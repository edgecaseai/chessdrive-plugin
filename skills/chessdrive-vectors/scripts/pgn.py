"""Read a PGN file's games and tags. The Python standard library only, on Python 3.11 or later, so a script that only
reads games needs no NumPy. It splits a file as `chessdrive embed` splits it.
"""

import hashlib
import re
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
