#!/usr/bin/env python3
"""The mistakes a player keeps making: `group.py` on their vector file, with each example read back as the mistake it
is. NumPy only, on Python 3.11 or later.

    python3 groups.py patterns
    python3 groups.py patterns --top 5

Reads vectors.npy and mistakes.jsonl in the folder and prints one JSON object a line: the top groups, largest first,
each with a few examples from different games, then the totals. Never prints a vector or a score. A group needs
MIN_SIZE mistakes from at least two games, as one game's mistakes aren't a habit, so few mistakes give fewer groups.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # keeps the Plugin's folder as it was installed

VECTORS = Path(__file__).resolve().parent.parent.parent / "chessdrive-vectors" / "scripts"
sys.path.insert(0, str(VECTORS))

from vectorfile import emit

MIN_SIZE = 3
SHOWN = ("move", "verdict", "colour", "opponent", "date", "site", "best", "allowed", "before", "after", "fen", "pgn", "ply")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("folder", help="the folder mistakes.py wrote")
    parser.add_argument("--top", type=int, default=3, help="how many groups to show (default 3)")
    parser.add_argument("--examples", type=int, default=5, help="examples per group, from different games (default 5)")
    parser.add_argument("--groups", type=int, help="how many groups to make (default: group.py's, from the number of rows)")
    parser.add_argument("--seed", type=int, default=0, help="a different seed can give different groups")
    args = parser.parse_args()

    folder = Path(args.folder)
    mistakes = [json.loads(line) for line in (folder / "mistakes.jsonl").read_text(encoding="utf-8").splitlines()]
    # Every member, most typical first: `chessdrive embed --input` rows name no game, so group.py can't pick by game.
    command = [sys.executable, "-B", str(VECTORS / "group.py"), str(folder / "vectors.npy"), "--examples", str(len(mistakes)), "--seed", str(args.seed)]
    if args.groups:
        command += ["--groups", str(args.groups)]
    done = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
    if done.returncode != 0:
        sys.exit(done.stderr.strip())

    kept = []
    for line in done.stdout.splitlines():
        group = json.loads(line)
        rows, seen = [], set()  # one from each game, most typical first
        for example in group["examples"]:
            row = mistakes[example["row"]]
            if row["game"] not in seen:
                seen.add(row["game"])
                rows.append(row)
        if group["size"] >= MIN_SIZE and len(rows) >= 2:
            kept.append({"size": group["size"], "games": len(rows), "examples": [{k: r[k] for k in SHOWN} for r in rows[: args.examples]]})

    for number, group in enumerate(kept[: args.top], start=1):
        emit({"group": number, **group})
    emit({"positions": len(mistakes), "games": len({m["game"] for m in mistakes}), "repeated_groups": len(kept)})


if __name__ == "__main__":
    main()
