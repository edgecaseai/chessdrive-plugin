#!/usr/bin/env python3
"""Read a PGN file's games and tags. The Python standard library only, on Python 3.11 or later, so a script that only
reads games needs no NumPy. It splits a file as `chessdrive embed` splits it.

Run, it writes one player's newest games to a file of their own, before `chessdrive engine --games` bills each game:

    python3 pgn.py games.pgn --player MyHandle --newest 30 --out patterns/games.pgn

It prints one JSON object: the games written, the player's games in the file, and the file. A name not in the file
stops it, naming the ones that are.
"""

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Game:
    text: str  # the tags and the main line, as the API reads them
    plies: int

    def id(self):
        """The `game_id` of this game's rows, so a row can tell its game from one edited since."""
        return hashlib.sha256(self.text.encode("utf-8", "surrogateescape")).hexdigest()[:16]


SPECIAL = re.compile(r"[{;()\[]")
NOT_SPACE = re.compile(r"[^ \t\n\r]")
WORD = re.compile(r"[^ \t\n\r\[]+")
TAG = re.compile(r'\[(\w+)\s+"((?:[^"\\]|\\.)*)"')


def tag_end(pgn, start):
    """The index just past the `]` closing the tag that opens at pgn[start]."""
    quoted = False
    i = start + 1
    while i < len(pgn):
        c = pgn[i]
        if quoted and c == "\\":
            i += 1
        elif c == '"':
            quoted = not quoted
        elif not quoted and c == "]":
            return i + 1
        i += 1
    return len(pgn)


def main_line(pgn):
    """The PGN with its `{…}` and `;` comments and `(…)` variations blanked out, keeping the tags."""
    out, depth, i = [], 0, 0
    while i < len(pgn):
        found = SPECIAL.search(pgn, i)
        at = found.start() if found else len(pgn)
        if depth == 0:
            out.append(pgn[i:at])
        if not found:
            break
        c = pgn[at]
        if c in "{;":
            end = pgn.find("}" if c == "{" else "\n", at + 1)
            i = (end if end >= 0 else len(pgn)) + 1
            out.append(" ")
        elif c == "(":
            depth += 1
            i = at + 1
        elif c == ")":
            depth -= 1
            i = at + 1
            if depth == 0:
                out.append(" ")
        elif depth == 0:
            i = tag_end(pgn, at)
            out.append(pgn[at:i])
        else:
            i = at + 1
    return "".join(out)


def is_result(word):
    return word in ("*", "1-0", "0-1", "1/2-1/2")


def is_move(word):
    """Whether a word of a main line is a half-move, not a move number, a NAG or a glyph."""
    word = word[word.rfind(".") + 1 :]
    return len(word) >= 2 and word[0] in "abcdefghKQRBNOP0"


def scan(line):
    """Each tag and word of a main line, as (start, end, word), with word None for a tag."""
    i = 0
    while found := NOT_SPACE.search(line, i):
        at = found.start()
        if line[at] == "[":
            i = tag_end(line, at)
            yield at, i, None
        else:
            i = WORD.match(line, at).end()
            yield at, i, line[at:i]


def split_games(pgn):
    """Every game of a PGN file, split as `chessdrive embed` splits it, so a row's `game` is its place in this list."""
    line = main_line(pgn.removeprefix("\ufeff"))
    games, start, plies, moved = [], 0, 0, False

    def end(at):
        nonlocal start, plies, moved
        games.append(Game(line[start:at].strip(), plies))
        start, plies, moved = at, 0, False

    for at, after, word in scan(line):
        if word is None:
            if moved:
                end(at)
            continue
        moved = True
        if is_result(word):
            end(after)
        elif is_move(word):
            plies += 1
    if line[start:].strip():
        end(len(line))
    return games


def read_pgn(path):
    return Path(path).read_bytes().decode("utf-8", "surrogateescape")


def player_games(games, player, newest):
    """The player's newest games, oldest first, whatever order the file is in. Games with no date keep the file's."""
    def tags(game):
        return dict(TAG.findall(game.text))

    def played(game):
        t = tags(game)
        return t.get("UTCDate") or t.get("Date") or "", t.get("UTCTime") or t.get("Time") or ""

    wanted = player.casefold()
    theirs = [g for g in games if wanted in (tags(g).get("White", "").casefold(), tags(g).get("Black", "").casefold())]
    return sorted(theirs, key=played)[-newest:], theirs


def names_in(games):
    seen = {}
    for game in games:
        for colour in ("White", "Black"):
            if name := dict(TAG.findall(game.text)).get(colour):
                seen[name] = seen.get(name, 0) + 1
    return sorted(seen, key=seen.get, reverse=True)[:5]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pgn", help="a PGN file holding the player's games")
    parser.add_argument("--player", required=True, help="the player's name as the PGN's White and Black tags write it")
    parser.add_argument("--newest", type=int, default=30, help="how many of their newest games (default 30)")
    parser.add_argument("--out", required=True, help="the PGN file to write")
    args = parser.parse_args()
    games = split_games(read_pgn(args.pgn))
    chosen, theirs = player_games(games, args.player, args.newest)
    if not chosen:
        sys.exit(f'No game in {args.pgn} has "{args.player}" as White or Black. The names there: {", ".join(names_in(games))}.')
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes("".join(g.text + "\n\n" for g in chosen).encode("utf-8", "surrogateescape"))
    print(json.dumps({"games": len(chosen), "theirs": len(theirs), "file": str(out)}))


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    main()
