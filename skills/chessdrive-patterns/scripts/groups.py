#!/usr/bin/env python3
"""The mistakes a player keeps making: `group.py` on their vector file, with each example read back as the mistake it
is. NumPy only, on Python 3.11 or later.

    python3 groups.py patterns
    python3 groups.py patterns --top 5

Reads mistakes.jsonl in the folder and its vectors: boards.npy, the positions after each mistake, and texts.npy,
describe.py's line on each, joined as one unit vector each so a group holds mistakes that look alike on the board and
in what they allowed; or vectors.npy alone, as an older run left it. Prints one JSON object a line: the top groups,
largest first, each with a few examples from different games, each with its description, then the totals. Never prints
a vector or a score. A group needs MIN_SIZE mistakes from at least MIN_GAMES games, as one game's mistakes aren't a
habit and a group shows three examples from different games, so few mistakes give fewer groups. The groups it prints
go to groups.json too, for study.py.
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # keeps the Plugin's folder as it was installed

VECTORS = Path(__file__).resolve().parent.parent.parent / "chessdrive-vectors" / "scripts"
sys.path.insert(0, str(VECTORS))

import numpy as np  # noqa: E402

from vectorfile import emit, unit  # noqa: E402

MIN_SIZE = 3
MIN_GAMES = 3
SHOWN = ("move", "verdict", "colour", "opponent", "date", "site", "best", "allowed", "before", "after", "fen", "pgn", "ply")


def joined(folder, count):
    """vectors.npy from boards.npy and texts.npy, each row's two unit vectors end to end, with the texts' rows beside
    it; or vectors.npy as it stands when only it is there."""
    boards, texts, out = folder / "boards.npy", folder / "texts.npy", folder / "vectors.npy"
    if not boards.exists() and not texts.exists():
        return
    for file in (boards, texts):
        if not file.exists() or not file.with_suffix(".jsonl").exists():
            sys.exit(f"groups.py: {file} is missing. Step 3 of the Skill makes boards.npy and texts.npy with `chessdrive embed --out`.")
    a, b = np.load(boards, mmap_mode="r"), np.load(texts, mmap_mode="r")
    if len(a) != count or len(b) != count:
        sys.exit(f"groups.py: mistakes.jsonl has {count} mistakes, boards.npy {len(a)} rows and texts.npy {len(b)}: they should match, so run Step 3 again.")
    np.save(out, np.concatenate([unit(np.asarray(a)), unit(np.asarray(b))], axis=1).astype("<f4"))
    shutil.copyfile(texts.with_suffix(".jsonl"), out.with_suffix(".jsonl"))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("folder", help="the folder Step 2 of the Skill wrote")
    parser.add_argument("--top", type=int, default=3, help="how many groups to show (default 3)")
    parser.add_argument("--examples", type=int, default=5, help="examples per group, from different games (default 5)")
    parser.add_argument("--groups", type=int, help="how many groups to make (default: group.py's, from the number of rows)")
    parser.add_argument("--seed", type=int, default=0, help="a different seed can give different groups")
    args = parser.parse_args()

    folder = Path(args.folder)
    mistakes = [json.loads(line) for line in (folder / "mistakes.jsonl").read_text(encoding="utf-8").splitlines()]
    described = json.loads((folder / "described.json").read_text(encoding="utf-8")) if (folder / "described.json").exists() else {}
    for m in mistakes:
        m["text"] = (described.get(f"{m['site'] or m['date']}:{m['ply']}:{m['move']}") or {}).get("text", "")
    joined(folder, len(mistakes))
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
        if group["size"] >= MIN_SIZE and len(rows) >= MIN_GAMES:
            kept.append({"size": group["size"], "games": len(rows), "examples": [{k: r[k] for k in (*SHOWN, "text")} for r in rows[: args.examples]]})

    shown = [{"group": number, **group} for number, group in enumerate(kept[: args.top], start=1)]
    for group in shown:
        emit(group)
    (folder / "groups.json").write_text(json.dumps(shown, ensure_ascii=False), encoding="utf-8")
    emit({"positions": len(mistakes), "games": len({m["game"] for m in mistakes}), "repeated_groups": len(kept)})


if __name__ == "__main__":
    main()
