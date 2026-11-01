#!/usr/bin/env python3
"""Groups of similar items in a vector file, largest first, each with its most typical items. NumPy only, on Python
3.11 or later.

    python3 group.py vectors.npy
    python3 group.py vectors.npy --groups 5 --examples 3

Prints one JSON object a line, and never a vector. The same file and --seed give the same groups, so a second run with
more --examples shows more of the same group. Duplicates, or too few items, give fewer groups than asked for.
"""

import argparse
import math
import sys

sys.dont_write_bytecode = True  # keeps the Plugin's folder as it was installed

import numpy as np
from vectorfile import CHUNK, Games, emit, load, same_way, show, unit

# Groups are found on a sample at most this large, then every row joins its nearest.
MAX_SAMPLE = 50_000
MAX_ROUNDS = 50


def first_centres(points, count, rng):
    """k-means++ on cosine distance: each new centre is likely to be far from those so far."""
    centres = [points[rng.integers(len(points))]]
    nearest = points @ centres[0]
    while len(centres) < count:
        gaps = np.asarray(1 - nearest, "f8")
        gaps[gaps < 1e-6] = 0
        if gaps.sum() == 0:
            break  # no distinct point is left
        centres.append(points[rng.choice(len(points), p=gaps / gaps.sum())])
        nearest = np.maximum(nearest, points @ centres[-1])
    return np.stack(centres)


def find_centres(points, count, rng):
    """k-means on the unit sphere. A centre that loses every point goes, so a tight sample gives fewer groups."""
    centres = first_centres(points, count, rng)
    labels = None
    for _ in range(MAX_ROUNDS):
        moved = (points @ centres.T).argmax(axis=1)
        if labels is not None and np.array_equal(moved, labels):
            break
        used = np.unique(moved)
        labels = moved if len(used) == len(centres) else None  # a centre going renumbers the rest
        centres = unit(np.stack([points[moved == j].sum(axis=0) for j in used]))
    return centres


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("vectors", help="the vector file to group")
    parser.add_argument("--groups", type=int, help="how many groups (default: from the number of rows, at most 20)")
    parser.add_argument("--examples", type=int, default=1, help="items per group, from different games (default 1)")
    parser.add_argument("--seed", type=int, default=0, help="a different seed can give different groups")
    parser.add_argument("--mixed", action="store_true", help="group positions sent in two ways anyway")
    args = parser.parse_args()

    file = load(args.vectors)
    same_way(file.rows, args.mixed)
    count = len(file.rows)
    wanted = args.groups or min(20, max(2, round(math.sqrt(count / 2))))

    rng = np.random.default_rng(args.seed)
    sample = np.sort(rng.choice(count, min(count, MAX_SAMPLE), replace=False))
    centres = find_centres(unit(np.asarray(file.vectors[sample])), min(wanted, count), rng)

    labels, scores = np.empty(count, "i4"), np.empty(count, "f4")
    for start in range(0, count, CHUNK):
        similar = unit(np.asarray(file.vectors[start : start + CHUNK])) @ centres.T
        labels[start : start + CHUNK] = similar.argmax(axis=1)
        scores[start : start + CHUNK] = similar.max(axis=1)

    games = Games(file)
    sizes = np.bincount(labels, minlength=len(centres))
    for number, label in enumerate(np.argsort(-sizes, kind="stable").tolist(), start=1):
        if sizes[label] == 0:
            continue
        members = np.flatnonzero(labels == label)
        examples, seen = [], set()
        for i in members[np.argsort(-scores[members], kind="stable")].tolist():
            game = (file.rows[i].get("source"), file.rows[i].get("game"))
            if game[1] is not None and game in seen:
                continue
            seen.add(game)
            examples.append({"row": i, **show(file.rows[i], games)})
            if len(examples) == args.examples:
                break
        emit({
            "group": number,
            "size": int(sizes[label]),
            "tightness": round(float(scores[members].mean()), 4),
            "examples": examples,
        })


if __name__ == "__main__":
    main()
