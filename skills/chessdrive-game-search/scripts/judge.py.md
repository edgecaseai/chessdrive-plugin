# judge.py

The whole text of `judge.py`, a script of the `chessdrive-game-search` Skill. Claude's plugin directory takes no script files, so it's held here as text. Don't run or copy it from here: `unpack.md`, in `chessdrive-vectors/references`, writes it out as the file it is.

```python
#!/usr/bin/env python3
"""Knight's verdict on each hit: does the move show the idea? Through the `chessdrive` CLI, Python 3.11 or later.

    python3 judge.py hits.jsonl --idea "back rank mate" --checks checks/back-rank-mate.txt --out checks/back-rank-mate-judged.jsonl

Each line of hits.jsonl is a hit, `{"game": 29, "ply": 55, "pgn": "<its game>"}`, the same lines the engine's list
takes. --engine adds the engine's first Line from each hit's results line, the same line of its file. --checks is the
idea's checks, numbered, one a line, as `../references/ideas.md` gives them.

Knight reads, for each hit, the moves around it, the board after the move in words (`board.py`, so it names no piece
that isn't there), and the checks, and goes through them before its verdict. A hit Knight says yes to is asked once
more, and kept only when both answers say yes, so one slip doesn't put a wrong example in front of the person. A kept hit's note is
Knight's own sentence, word for word, and one that names a piece on a square where the board has none isn't kept.

It writes one line a hit to --out, in the file's order:

    {"game": 29, "ply": 55, "move": "28.Rc8#", "kept": true, "note": "...", "verdicts": ["yes", "yes"]}

with "kept": false and its "why" otherwise, and "error" for a hit Knight didn't answer after ask.py's retries. The
last line printed is the totals, with every unanswered hit and its error. Run it again and it bills no call already
answered.
"""

import argparse
import hashlib
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.dont_write_bytecode = True  # keeps the Plugin's folder as it was installed
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "chessdrive-vectors" / "scripts"))

from ask import AT_ONCE, Asker  # noqa: E402
from board import NAMES, replay, window, words  # noqa: E402

VOTES = 2
SYSTEM = (
    "You check whether a moment of a chess game shows an idea, as a coach would before using it in a lesson. The board "
    "after the move is listed square by square: read every piece from that list, and never name a piece on a square the "
    "list doesn't give it. Go through the idea's checks in order, one line each: first quote the words of the board list "
    "that settle it, then say \"so it holds\" or \"so it fails\". A moment shows the idea only if every check holds. Then "
    "write one line, \"Verdict: yes\" or \"Verdict: no\". On yes, add a last line \"Note:\" and one sentence for a player: "
    "the move, the piece that moves and what it does."
)
VERDICT = re.compile(r"verdict:\W*(yes|no)\b", re.I)
NOTE = re.compile(r"note:\W*(.+?)\s*$", re.I | re.S)
PIECE_ON = re.compile(r"\b(king|queen|rook|bishop|knight|pawn)\b(?:\s+\w+){0,2}?\s+on\s+([a-h][1-8])\b", re.I)


def engine_line(result):
    """The engine's first Line from a results line, numbered from its position, or "" when it has none."""
    lines = (result or {}).get("lines") or []
    if (result or {}).get("status") != "ok" or not lines:
        return ""
    fen = (result.get("fen") or "").split()
    ply = 2 * (int(fen[5]) - 1) + (fen[1] == "b") if len(fen) > 5 else 0
    out = []
    for i, move in enumerate(lines[0].get("moves") or []):
        n = (ply + i) // 2 + 1
        out.append(f"{n}.{move['san']}" if (ply + i) % 2 == 0 else (f"{n}...{move['san']}" if i == 0 else move["san"]))
    return " ".join(out)


def message(hit, idea, checks, line=""):
    moves, move = window(hit["pgn"], hit["ply"])
    parts = [f"Moves: {moves}\nThe move: {move}", words(hit["pgn"], hit["ply"])]
    if line:
        parts.append(f"The engine's best Line after it: {line}")
    parts.append(f'Does {move} show "{idea}"? Its checks:\n{checks}')
    return move, "\n\n".join(parts)


def absent(note, hit):
    """The first "<piece> on <square>" of a note that names a piece the board has on neither side of the move there."""
    board, before, _ = replay(hit["pgn"], hit["ply"])
    for found in PIECE_ON.finditer(note):
        kind, sq = found.group(1).lower(), found.group(2)
        at = "abcdefgh".index(sq[0]) + 8 * (int(sq[1]) - 1)
        if not any(b.squares[at] and NAMES[b.squares[at].lower()] == kind for b in (board, before)):
            return found.group(0)
    return None


def verdict_of(text):
    found = VERDICT.findall(text or "")
    return found[-1].lower() if found else None


def judged(hit, answers, move):
    out = {"game": hit.get("game"), "ply": hit["ply"], "move": move}
    if "source" in hit:
        out["source"] = hit["source"]
    missing = [a for a in answers if not a.get("text")]
    if missing:
        return {**out, "kept": False, "error": missing[0].get("error") or "no_reply", "why": "Knight didn't answer"}
    verdicts = [verdict_of(a["text"]) for a in answers]
    out["verdicts"] = verdicts
    if verdicts != ["yes"] * VOTES:
        why = "Knight said no" if "no" in verdicts else "Knight's reply gave no verdict"
        return {**out, "kept": False, "why": why}
    note = NOTE.search(answers[0]["text"])
    if not note:
        return {**out, "kept": False, "why": "Knight's yes came with no note"}
    note = note.group(1).strip()
    if wrong := absent(note, hit):
        return {**out, "kept": False, "why": f"Knight's note names a piece that isn't there: {wrong}"}
    return {**out, "kept": True, "note": note}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("hits", type=Path)
    parser.add_argument("--idea", required=True, help="the idea in the person's words")
    parser.add_argument("--checks", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--engine", type=Path, help="the engine's results for the same list")
    parser.add_argument("--cli", default="chessdrive")
    args = parser.parse_args()

    hits = [json.loads(line) for line in args.hits.read_text(encoding="utf-8").splitlines() if line.strip()]
    results = []
    if args.engine:
        results = [json.loads(line) for line in args.engine.read_text(encoding="utf-8").splitlines() if line.strip()]
    checks = args.checks.read_text(encoding="utf-8").strip()

    # Each answer is kept beside --out, so a second run bills no call already answered.
    replies_path = args.out.with_name(args.out.name + ".replies")
    replies = {}
    if replies_path.exists():
        for line in replies_path.read_text(encoding="utf-8").splitlines():
            if line.strip() and (a := json.loads(line)).get("text"):
                replies[a["id"]] = a

    texts, moves, ids = [], [], []
    for i, hit in enumerate(hits):
        move, text = message(hit, args.idea, checks, engine_line(results[i] if i < len(results) else None))
        moves.append(move)
        texts.append(text)
        # The id carries the question's own hash, so a changed question is asked again, never read from an old reply.
        ids.append(hashlib.sha256((text + hit["pgn"] + str(hit["ply"])).encode("utf-8", "surrogateescape")).hexdigest()[:12])

    def question(i, vote):
        return {"id": f"{ids[i]}#{vote}", "model": "knight", "system": SYSTEM, "message": texts[i],
                "pgn": hits[i]["pgn"], "ply": hits[i]["ply"]}

    # Every hit is asked once; a hit is asked again only while each answer so far says yes, as most hits are a no.
    asker, spent, calls, answers = Asker(args.cli), 0.0, 0, [[] for _ in hits]
    with open(replies_path, "w", encoding="utf-8") as out, ThreadPoolExecutor(AT_ONCE) as pool:
        for vote in range(1, VOTES + 1):
            asking = [i for i in range(len(hits)) if len(answers[i]) == vote - 1
                      and all(verdict_of(a.get("text")) == "yes" for a in answers[i])]
            todo = [question(i, vote) for i in asking if f"{ids[i]}#{vote}" not in replies]
            for q, a in zip(todo, pool.map(asker.ask, todo)):
                out.write(json.dumps(a, ensure_ascii=False) + "\n")
                out.flush()
                replies[q["id"]], spent = a, spent + a["cost_usd"]
            for i in asking:
                a = replies[f"{ids[i]}#{vote}"]
                if f"{ids[i]}#{vote}" not in {q["id"] for q in todo}:
                    out.write(json.dumps(a, ensure_ascii=False) + "\n")
                answers[i].append(a)
                calls += 1

    rows = [judged(hit, answers[i], moves[i]) for i, hit in enumerate(hits)]
    args.out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    print(json.dumps({
        "hits": len(rows), "kept": sum(r["kept"] for r in rows), "calls": calls,
        "unanswered": [{"game": r["game"], "ply": r["ply"], "error": r["error"]} for r in rows if r.get("error")],
        "cost_usd": round(spent, 6), "out": str(args.out),
    }))


if __name__ == "__main__":
    main()
```
