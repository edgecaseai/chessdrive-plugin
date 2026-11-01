#!/usr/bin/env python3
"""The items of a vector file closest to a text or a position. NumPy only, on Python 3.11 or later.

    python3 compare.py vectors.npy --query query.npy
    python3 compare.py vectors.npy --game 3 --ply 24 --other-games

--query is a vector file with one row: a text or a position embedded with `--out`, by the same Model. --game and --ply
pick a position already in the file. Prints one JSON object a line, closest first, and never a vector.
"""

import argparse
import sys
from collections import Counter

sys.dont_write_bytecode = True  # keeps the Plugin's folder as it was installed

import numpy as np
from vectorfile import Games, cosine, emit, load, same_model, same_way, show


def query_row(file, game, ply, source):
    """The row of a position in the file. Several PGN files in one run each count their games from 0."""
    found = [
        i
        for i, row in enumerate(file.rows)
        if row.get("game") == game and row.get("ply") == ply and source in (None, row.get("source"))
    ]
    if not found:
        sys.exit(f"{file.path} has no row for game {game}, ply {ply}. Games count from 0.")
    if len(found) > 1:
        sources = sorted({file.rows[i]["source"] for i in found})
        sys.exit(f"Game {game}, ply {ply} is in {len(found)} files: pick one with --source, from {sources}.")
    return found[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("vectors", help="the vector file to look through")
    parser.add_argument("--query", help="a vector file with one row: what to look for")
    parser.add_argument("--game", type=int, help="with --ply: a position in the file, its game from 0")
    parser.add_argument("--ply", type=int, help="half-moves into that game, 0 being its start")
    parser.add_argument("--source", help="the PGN file of --game, when the run had several")
    parser.add_argument("--top", type=int, default=10, help="how many hits to print (default 10)")
    parser.add_argument("--per-game", type=int, help="at most this many hits from one game")
    parser.add_argument("--other-games", action="store_true", help="with --game: skip the rest of that game")
    parser.add_argument("--mixed", action="store_true", help="compare positions sent in two ways anyway")
    args = parser.parse_args()
    if (args.query is None) == (args.game is None) or (args.game is None) != (args.ply is None):
        parser.error("give --query, or --game with --ply")
    if args.other_games and args.game is None:
        parser.error("--other-games goes with --game")

    file = load(args.vectors)
    own, own_game = None, None
    if args.query:
        query = load(args.query)
        if len(query.rows) != 1:
            sys.exit(f"{query.path} has {len(query.rows)} rows, and a query is one: embed that one item to its own file.")
        same_model(file, query)
        same_way(file.rows + query.rows, args.mixed)
        target = query.vectors[0]
    else:
        same_way(file.rows, args.mixed)
        own = query_row(file, args.game, args.ply, args.source)
        own_game = (file.rows[own].get("source"), args.game)
        target = file.vectors[own]

    scores = cosine(file.vectors, target)
    games, per_game, rank = Games(file), Counter(), 0
    for i in np.argsort(-scores, kind="stable").tolist():
        row = file.rows[i]
        game = (row.get("source"), row["game"]) if "game" in row else None
        if i == own or (args.other_games and game == own_game):
            continue
        if args.per_game and game is not None:
            if per_game[game] >= args.per_game:
                continue
            per_game[game] += 1
        rank += 1
        emit({"rank": rank, "score": round(float(scores[i]), 4), "row": i, **show(row, games)})
        if rank == args.top:
            break


if __name__ == "__main__":
    main()
