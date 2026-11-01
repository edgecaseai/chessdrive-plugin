#!/usr/bin/env python3
"""A PGN of examples: each picked moment as its whole game, with a note at that move. NumPy only, on Python 3.11 or later.

    python3 examples.py games.npy picks.json --out examples.pgn --title "Back rank mates"

picks.json is a list of {"game", "ply", "note"}, best first, with "source" as well when the run had several PGN files.
Games come from the PGN files behind games.npy, so their moves are the ones Embed checked. The result opens as a Lichess
study, one chapter a game. Prints one JSON object, and never a vector.
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # keeps the Plugin's folder as it was installed

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "chessdrive-vectors/scripts"))
from vectorfile import Games, emit, is_move, is_result, load, scan

# A Lichess study holds 64 chapters and quietly drops the rest.
MAX_EXAMPLES = 64


def rows_by_game(file):
    return {(row.get("source"), row["game"]): row for row in file.rows if "game" in row}


def find_row(rows, pick):
    """The row of the picked game, which says which game of which PGN file it is."""
    game = pick["game"]
    if "source" in pick:
        row = rows.get((pick["source"], game))
    else:
        found = [row for (_, g), row in rows.items() if g == game]
        if len(found) > 1:
            sources = sorted(row["source"] for row in found)
            sys.exit(f"Game {game} is in {len(found)} files: say which with \"source\", from {sources}.")
        row = found[0] if found else None
    if row is None:
        sys.exit(f"The file has no row for game {game}. Games count from 0.")
    return row


def annotate(game, ply, note):
    """The game's tags and moves, cleaned of its blanks, with the note after the move that reached the ply."""
    tags, moves, played = [], [], 0
    if ply == 0:
        moves.append("{" + note + "}")
    for start, end, word in scan(game.text):
        if word is None:
            tags.append(game.text[start:end])
            continue
        moves.append(word)
        if is_move(word) and not is_result(word):
            played += 1
            if played == ply:
                moves.append("{" + note + "}")
    if ply > played:
        sys.exit(f"That game has {played} half-moves, so it has no moment at ply {ply}.")
    return tags, moves


def tag(name, value):
    return '[%s "%s"]' % (name, value.replace("\\", "\\\\").replace('"', '\\"'))


def written(tags, moves, chapter):
    head = "\n".join(([tag("ChapterName", chapter)] if chapter else []) + tags)
    return f"{head}\n\n{' '.join(moves)}\n"


def clean(note):
    """A note as one comment on one line: `}` would end it, and Lichess cuts a file at a blank line before a `[`."""
    return re.sub(r"\s+", " ", note.replace("}", ")")).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("vectors", help="the vector file the picks came from")
    parser.add_argument("picks", help='a JSON list of {"game", "ply", "note"}, best first')
    parser.add_argument("--out", required=True, help="the PGN file to write")
    parser.add_argument("--title", help="names each chapter of a Lichess study: Title 1, Title 2 and so on")
    args = parser.parse_args()

    picks = json.loads(Path(args.picks).read_text(encoding="utf-8"))
    if len(picks) > MAX_EXAMPLES:
        sys.exit(f"That's {len(picks)} examples, and a Lichess study holds {MAX_EXAMPLES} chapters: pick fewer.")

    file = load(args.vectors)
    rows, games, out = rows_by_game(file), Games(file), []
    for number, pick in enumerate(picks, 1):
        row = find_row(rows, pick)
        game = games.find(row)
        if game is None:
            sys.exit(f"{row['source']} is missing, or game {row['game']} has changed since it was embedded.")
        tags, moves = annotate(game, pick["ply"], clean(pick["note"]))
        out.append(written(tags, moves, f"{args.title} {number}" if args.title else None))

    Path(args.out).write_text("\n".join(out), encoding="utf-8", errors="surrogateescape")
    emit({"examples": len(out), "file": args.out})


if __name__ == "__main__":
    main()
