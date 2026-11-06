#!/usr/bin/env python3
"""Many questions to ChessDrive's chess models at once, through the `chessdrive` CLI. Python 3.11 or later.

    python3 ask.py questions.jsonl --out answers.jsonl

Each line of questions.jsonl is one call:

    {"id": "14...Qd7", "model": "queen", "system": "<system>", "message": "<message>", "pgn": "<the game>", "ply": 27}

with "fen" in place of "pgn" and "ply" for a bare position, and neither for a question with no position. It runs
AT_ONCE calls at a time, the most whose engine notes ChessDrive keeps, and writes one line a call to --out, as each
finishes:

    {"id": "14...Qd7", "model": "queen", "text": "...", "lines": {"L1": "14...Nf6 15.Qe2 O-O"}, "cost_usd": 0.004}

`text` is the reply with its moves as plain text, and `lines` the Lines it named, which passed as legal; a sentence
that named a move with no such Line is dropped. A call is retried as the Skills say: on rate_limited after its wait,
on upstream_unavailable or a reply cut short once more. One that still fails is written with "text": null and its
"error", for the Skill to label, never to fill in. On plan_required, Queen's call and every later one go to Knight,
and "model" says so. Run it again and it bills no call already answered. The last line printed is the totals.
"""

import argparse
import json
import re
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.dont_write_bytecode = True  # keeps the Plugin's folder as it was installed

AT_ONCE = 6
RATE_LIMIT_TRIES = 5
LINK = re.compile(r"\[([^\]]*)\]\(line:([^)\s]+)\)")
SENTENCE = re.compile(r"(?<=[.!?])\s+")
RETRY_AFTER = re.compile(r"retry after:? *(\d+)", re.I)


def numbered(line):
    """A Line's moves as an answer writes them, from its first move's number: 14...Nf6 15.Qe2 O-O."""
    fen = (line.get("from_fen") or "").split()
    black, number = len(fen) > 5 and fen[1] == "b", int(fen[5]) if len(fen) > 5 else 1
    out = []
    for i, move in enumerate(line.get("moves") or []):
        ply = i + black
        n = number + ply // 2
        out.append(f"{n}.{move['san']}" if ply % 2 == 0 else (f"{n}...{move['san']}" if i == 0 else move["san"]))
    return " ".join(out)


def plain(reply):
    """The reply with each linked move as its text, without the sentences whose link names no Line, and its Lines."""
    lines = {line["id"]: numbered(line) for line in reply.get("lines") or []}
    kept = [s for s in SENTENCE.split(reply.get("content") or "") if all(m.group(2) in lines for m in LINK.finditer(s))]
    return " ".join(LINK.sub(r"\1", " ".join(kept)).split()), lines


def code_of(done):
    """The API's error code from a failed run: its --json body, else the CLI's `code: message` line."""
    try:
        return json.loads(done.stdout)["error"]["code"]
    except (ValueError, KeyError, TypeError):
        found = re.search(r"\b([a-z]+(?:_[a-z]+)+)\b", done.stderr)
        return found.group(1) if found else f"exit_{done.returncode}"


class Asker:
    def __init__(self, cli):
        self.cli, self.knight_only, self.lock = cli, False, threading.Lock()

    def run(self, q, model):
        args = [self.cli, "generate", "--model", model, "--no-stream", "--json"]
        if q.get("system"):
            args += ["--system", q["system"]]
        if q.get("pgn"):
            args += ["--pgn", "-", "--ply", str(q["ply"])]
        elif q.get("fen"):
            args += ["--fen", q["fen"]]
        return subprocess.run(args + [q["message"]], input=q.get("pgn", ""), capture_output=True, text=True, encoding="utf-8")

    def ask(self, q):
        model, cost, second_try, waits = q.get("model", "queen"), 0.0, False, 0
        while True:
            if model == "queen" and self.knight_only:
                model = "knight"
            done = self.run(q, model)
            if done.returncode == 0:
                reply = json.loads(done.stdout)
                cost += float(reply.get("cost_usd") or 0)
                text, lines = plain(reply)
                if text and reply.get("finish_reason") != "max_tokens":
                    return {"id": q["id"], "model": model, "text": text, "lines": lines, "cost_usd": round(cost, 6)}
                error = "cut_short"
            else:
                error = code_of(done)
            if error == "plan_required" and model == "queen":
                with self.lock:
                    self.knight_only = True
                continue
            if error == "rate_limited" and waits < RATE_LIMIT_TRIES:
                waits += 1
                wait = RETRY_AFTER.search(done.stderr) if done.returncode else None
                time.sleep(int(wait.group(1)) if wait else 5 * waits)
                continue
            if error in ("upstream_unavailable", "cut_short", "overloaded_error", "exit_1") and not second_try:
                second_try = True
                continue
            if error not in ("upstream_unavailable", "cut_short", "overloaded_error", "rate_limited", "exit_1"):
                sys.exit(done.stderr.strip() or f"{self.cli} stopped: {error}.")
            return {"id": q["id"], "model": model, "text": None, "error": error, "cost_usd": round(cost, 6)}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("questions", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--at-once", type=int, default=AT_ONCE)
    parser.add_argument("--cli", default="chessdrive")
    args = parser.parse_args()

    questions = [json.loads(line) for line in args.questions.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len({q["id"] for q in questions}) != len(questions):
        sys.exit("Each question needs its own id.")
    answered = {}
    if args.out.exists():
        for line in args.out.read_text(encoding="utf-8").splitlines():
            if line.strip() and (a := json.loads(line)).get("text"):
                answered[a["id"]] = a
    todo = [q for q in questions if q["id"] not in answered]
    asker, spent = Asker(args.cli), 0.0
    with open(args.out, "w", encoding="utf-8") as out, ThreadPoolExecutor(max(1, min(args.at_once, AT_ONCE))) as pool:
        for a in answered.values():
            out.write(json.dumps(a, ensure_ascii=False) + "\n")
        for future in as_completed([pool.submit(asker.ask, q) for q in todo]):
            a = future.result()
            out.write(json.dumps(a, ensure_ascii=False) + "\n")
            out.flush()
            answered[a["id"]], spent = a, spent + a["cost_usd"]
    print(json.dumps({"calls": len(questions), "answered": sum(1 for a in answered.values() if a.get("text")),
                      "unanswered": [a["id"] for a in answered.values() if not a.get("text")],
                      "knight_for_queen": asker.knight_only, "cost_usd": round(spent, 6), "out": str(args.out)}))


if __name__ == "__main__":
    main()
