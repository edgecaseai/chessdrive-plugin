#!/usr/bin/env python3
"""One line on each mistake, from Knight, for Embed to group them by: what the move allowed, as the engine's Lines
show it. Python 3.11 or later, with the `chessdrive` CLI signed in.

    python3 describe.py patterns --rating 1612

Reads mistakes.jsonl, which Step 2 wrote, and asks Knight about them BATCH at a time, every batch at once, with no
position: each mistake goes in as its move, the better move and what it allowed, and Knight answers one line a
mistake, in chess words rather than moves. A line that names a move it wasn't given, or a number, is asked again
once, then replaced by a line built from the engine's Lines alone. Answers are kept in described.json, so running it
again bills no mistake twice. Writes texts.json, the file `chessdrive embed --input` takes, one text a mistake in
mistakes.jsonl's order, and prints one JSON object: the totals.
"""

import argparse
import json
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.dont_write_bytecode = True  # keeps the Plugin's folder as it was installed

from study import NAMED, NUMBER, numbered, plain  # noqa: E402

BATCH = 8  # under Free's Knight calls a minute for 130 mistakes, so no call waits
EXIT_RATE_LIMITED = 5
RETRIES = 5
RETRY_SECONDS = 5
TRIES = 2  # Knight's answers, before a mistake falls back to the engine's Lines alone
WORDS = 25  # Embed takes a short text, and a description is for grouping, not reading

SYSTEM = (
    "You describe chess mistakes by a player{rating}, one line each, for a program that groups mistakes of one kind "
    "together. For each numbered mistake, write its number, a full stop, then at most {words} plain words on what the "
    "move gave the other side, as the engine's line shows it: a piece left hanging, a fork, a pin, a back-rank weakness, "
    "a pawn that promotes, a file or diagonal opened to the king, a piece shut out, and so on, named by the pieces and "
    "squares. Say the kind of mistake, not the moves: name a move only when it is one you were given, written as given. "
    "No numbers, scores or evaluations, and nothing else."
)


def described(m):
    other = "Black" if m["colour"] == "White" else "White"
    lines = [f"{m['colour']} played {m['move']}, a {m['verdict']}, from FEN {m['fen']}."]
    if m["best"]:
        lines.append(f"Better was {numbered(m['ply'], m['best'], 3)}.")
    if m["allowed"]:
        lines.append(f"After the move, the engine's best play for {other} is {numbered(m['ply'] + 1, m['allowed'], 3)}.")
    lines.append(f"Before: {m['before']}; after: {m['after']}.")
    return " ".join(lines)


def message(batch):
    return "The mistakes:\n" + "\n".join(f"{n}. {described(m)}" for n, m in enumerate(batch, 1)) + "\nOne line each."


def key(m):
    return f"{m['site'] or m['date']}:{m['ply']}:{m['move']}"


def from_lines(m):
    """A description with no Knight in it: the move, and what the engine's Lines show."""
    said = f"{m['colour']} played {plain(m['move'].split('.')[-1])}, a {m['verdict']}"
    if m["allowed"]:
        said += f", allowing {numbered(m['ply'] + 1, m['allowed'], 2)}"
    if m["best"]:
        said += f"; better was {numbered(m['ply'], m['best'], 1)}"
    return said + "."


def sourced(text, m):
    """The line as plain text, or None when it names a move it wasn't given, a number, or nothing."""
    text = " ".join(re.sub(r"\[([^\]]*)\]\(line:[^)]+\)", r"\1", text).replace("*", "").split())
    if not text or NUMBER.search(text):
        return None
    given = {plain(s) for s in [m["move"].split(".")[-1], *m["best"], *m["allowed"]]}
    if any(plain(found) not in given for found in NAMED.findall(text)):
        return None
    return " ".join(text.split()[:WORDS])


def parsed(content, count):
    """Knight's lines by number, from 1, in whatever shape it wrote them."""
    out = {}
    for found in re.finditer(r"(?m)^\s*(\d+)[.)]\s*(.+?)\s*$", content):
        n = int(found.group(1))
        if 1 <= n <= count and n not in out:
            out[n] = found.group(2)
    return out


def call_knight(cli, batch, system):
    """Knight's lines on a batch, as {key: (text, from Knight)}, with the cost, the calls made and their tokens. A mistake whose line
    didn't pass is asked again in a batch of its own, then falls back to the engine's Lines."""
    out, cost, calls, tokens = {}, 0.0, 0, [0, 0]
    todo, tries = list(batch), 0
    while todo and tries < TRIES:
        args = [cli, "generate", "--model", "knight", "--no-stream", "--json", "--system", system, message(todo)]
        reply = None
        for attempt in range(RETRIES):
            done = subprocess.run(args, stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf-8")
            if done.returncode == 0:
                reply = json.loads(done.stdout)
                break
            if done.returncode in (1, EXIT_RATE_LIMITED):
                time.sleep(min(60, RETRY_SECONDS * 2**attempt))
                continue
            sys.exit(done.stderr.strip() or f"{cli} stopped with code {done.returncode}.")
        if reply is None:
            break
        calls += 1
        cost += float(reply.get("cost_usd") or 0)
        tokens[0] += int((reply.get("usage") or {}).get("input_tokens") or 0)
        tokens[1] += int((reply.get("usage") or {}).get("output_tokens") or 0)
        lines = parsed(reply.get("content", ""), len(todo)) if reply.get("finish_reason") != "max_tokens" else {}
        left = []
        for n, m in enumerate(todo, 1):
            if text := sourced(lines.get(n, ""), m):
                out[key(m)] = (text, True)
            else:
                left.append(m)
        todo, tries = left, tries + 1
    for m in todo:
        out[key(m)] = (from_lines(m), False)
    return out, cost, calls, tokens


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("folder", help="the folder Step 2 of the Skill wrote")
    parser.add_argument("--rating", help="the player's rating, for Knight")
    parser.add_argument("--cli", default="chessdrive", help="the CLI to call")
    args = parser.parse_args()

    folder = Path(args.folder)
    mistakes = [json.loads(line) for line in (folder / "mistakes.jsonl").read_text(encoding="utf-8").splitlines()]
    cache_file = folder / "described.json"
    cache = json.loads(cache_file.read_text(encoding="utf-8")) if cache_file.exists() else {}
    todo = [m for m in mistakes if key(m) not in cache]
    batches = [todo[i : i + BATCH] for i in range(0, len(todo), BATCH)]
    system = SYSTEM.format(rating=f" of about {args.rating}" if args.rating else "", words=WORDS)

    cost, calls, tokens = 0.0, 0, [0, 0]
    with ThreadPoolExecutor(max(1, len(batches))) as pool:
        for found, spent, made, used in pool.map(lambda batch: call_knight(args.cli, batch, system), batches):
            cost, calls, tokens = cost + spent, calls + made, [tokens[0] + used[0], tokens[1] + used[1]]
            for k, (text, by_knight) in found.items():
                cache[k] = {"text": text, "knight": by_knight}
    cache_file.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")

    texts = [cache[key(m)]["text"] for m in mistakes]
    (folder / "texts.json").write_text(json.dumps([{"type": "text", "text": t} for t in texts], ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "described": len(mistakes), "from_knight": sum(cache[key(m)]["knight"] for m in mistakes),
        "from_lines": sum(not cache[key(m)]["knight"] for m in mistakes), "knight_calls": calls, "knight_cost_usd": round(cost, 4),
        "knight_tokens": {"input": tokens[0], "output": tokens[1]}, "texts": str(folder / "texts.json"),
    }), flush=True)


if __name__ == "__main__":
    main()
