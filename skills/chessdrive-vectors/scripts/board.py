#!/usr/bin/env python3
"""A position of a game in words, for a chess model to read. The Python standard library only, on Python 3.11 or later.

    python3 board.py game.pgn --ply 66

prints the board after the game's 66th half-move: the move that led there, the piece it moved and the enemy pieces
that piece attacks, every piece of each side by square, and the squares in front of, beside and behind each king, from
that king's side. It states what stands where and nothing more: no move is judged. The model reads its pieces from
these lines instead of working them out from a FEN, so it names none that aren't there.

`words(pgn, ply)` is the same text, for a script that writes questions. A move the game can't play stops it, naming
the ply.
"""

import argparse
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # keeps the Plugin's folder as it was installed

from pgn import is_move, is_result, main_line, read_pgn, scan, split_games  # noqa: E402

FILES = "abcdefgh"
NAMES = {"k": "king", "q": "queen", "r": "rook", "b": "bishop", "n": "knight", "p": "pawn"}
VALUE = {"k": 100, "q": 9, "r": 5, "b": 3, "n": 3, "p": 1}
KNIGHT = [(1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)]
KING = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
ROOK = [(1, 0), (0, 1), (-1, 0), (0, -1)]
BISHOP = [(1, 1), (-1, 1), (-1, -1), (1, -1)]
SAN = re.compile(r"^([NBRQK])?([a-h])?([1-8])?(x)?([a-h][1-8])(?:=?([NBRQ]))?$")


def name(sq):
    return FILES[sq % 8] + str(sq // 8 + 1)


def square(text):
    return FILES.index(text[0]) + 8 * (int(text[1]) - 1)


def white(piece):
    return piece.isupper()


class Board:
    """A position: 64 squares from a1 to h8, each a piece letter (upper case for White) or "", and whose move it is."""

    def __init__(self):
        back = "rnbqkbnr"
        self.squares = [""] * 64
        for f in range(8):
            self.squares[f] = back[f].upper()
            self.squares[8 + f] = "P"
            self.squares[48 + f] = "p"
            self.squares[56 + f] = back[f]
        self.white_to_move, self.castling, self.en_passant = True, set("KQkq"), None

    def at(self, f, r):
        return self.squares[f + 8 * r] if 0 <= f < 8 and 0 <= r < 8 else None

    def attacks(self, sq):
        """The squares the piece on sq attacks, whatever stands on them, pins aside."""
        piece = self.squares[sq]
        kind, f, r, out = piece.lower(), sq % 8, sq // 8, []
        if kind == "p":
            step = 1 if white(piece) else -1
            return [x + 8 * (r + step) for x in (f - 1, f + 1) if 0 <= x < 8 and 0 <= r + step < 8]
        if kind in "nk":
            for df, dr in KNIGHT if kind == "n" else KING:
                if self.at(f + df, r + dr) is not None:
                    out.append(f + df + 8 * (r + dr))
            return out
        rays = (ROOK if kind == "r" else BISHOP if kind == "b" else ROOK + BISHOP)
        for df, dr in rays:
            x, y = f + df, r + dr
            while (here := self.at(x, y)) is not None:
                out.append(x + 8 * y)
                if here:
                    break
                x, y = x + df, y + dr
        return out

    def attacked(self, sq, by_white):
        return any(p and white(p) == by_white and sq in self.attacks(i) for i, p in enumerate(self.squares))

    def king(self, of_white):
        return self.squares.index("K" if of_white else "k")

    def apply(self, frm, to, promotion=None):
        """A copy of the board after the move, legal or not."""
        b = Board.__new__(Board)
        b.squares, b.castling = self.squares[:], set(self.castling)
        piece, b.en_passant = b.squares[frm], None
        if piece.lower() == "p" and to == self.en_passant and not b.squares[to]:
            b.squares[to + (-8 if white(piece) else 8)] = ""
        if piece.lower() == "p" and abs(to - frm) == 16:
            b.en_passant = (to + frm) // 2
        if piece.lower() == "k" and abs(to - frm) == 2:
            rook_from, rook_to = (frm + 3, frm + 1) if to > frm else (frm - 4, frm - 1)
            b.squares[rook_to], b.squares[rook_from] = b.squares[rook_from], ""
        b.squares[to], b.squares[frm] = (promotion.upper() if white(piece) else promotion.lower()) if promotion else piece, ""
        for sq, right in ((4, "KQ"), (60, "kq"), (0, "Q"), (7, "K"), (56, "q"), (63, "k")):
            if sq in (frm, to):
                b.castling -= set(right)
        b.white_to_move = not self.white_to_move
        return b

    def safe(self, after):
        """Whether the side that just moved left its own king out of check."""
        return not after.attacked(after.king(self.white_to_move), not self.white_to_move)

    def play(self, san):
        """The board after a move written in SAN, or None when it isn't legal here."""
        text = san.rstrip("+#!?").replace("0", "O")
        mover = self.white_to_move
        if text in ("O-O", "O-O-O"):
            king, side = self.king(mover), "K" if text == "O-O" else "Q"
            if (side if mover else side.lower()) not in self.castling:
                return None
            step = 1 if side == "K" else -1
            path = range(king + step, king + (3 if side == "K" else 4) * step, step)
            if any(self.squares[s] for s in path) or any(self.attacked(s, not mover) for s in (king, king + step, king + 2 * step)):
                return None
            return self.apply(king, king + 2 * step)
        found = SAN.match(text)
        if not found:
            return None
        kind, from_file, from_rank, _, dest, promotion = found.groups()
        kind, to = (kind or "P"), square(dest)
        letter = kind if mover else kind.lower()
        options = []
        for frm, piece in enumerate(self.squares):
            if piece != letter or (from_file and FILES[frm % 8] != from_file) or (from_rank and str(frm // 8 + 1) != from_rank):
                continue
            if self.squares[to] and white(self.squares[to]) == mover:
                continue
            if kind == "P":
                step = 8 if mover else -8
                if to % 8 == frm % 8:
                    start = frm // 8 == (1 if mover else 6)
                    if self.squares[to] or not (to == frm + step or (start and to == frm + 2 * step and not self.squares[frm + step])):
                        continue
                elif not (to in self.attacks(frm) and (self.squares[to] or to == self.en_passant)):
                    continue
                if (to // 8 in (0, 7)) != bool(promotion):
                    continue
            elif to not in self.attacks(frm):
                continue
            after = self.apply(frm, to, promotion)
            if self.safe(after):
                options.append(after)
        return options[0] if len(options) == 1 else None

    def placement(self):
        """The FEN's first field, for tests."""
        rows = []
        for r in range(7, -1, -1):
            row, empty = "", 0
            for f in range(8):
                if p := self.squares[f + 8 * r]:
                    row, empty = row + (str(empty) if empty else "") + p, 0
                else:
                    empty += 1
            rows.append(row + (str(empty) if empty else ""))
        return "/".join(rows)


def sans(pgn):
    """A game's main-line moves in SAN, read as `chessdrive embed` reads them, move numbers and glyphs left out."""
    return [word[word.rfind(".") + 1:] for _, _, word in scan(main_line(pgn)) if word is not None and is_move(word) and not is_result(word)]


def replay(pgn, ply):
    """The board after ply half-moves, the board before the last of them and that move's SAN."""
    moves = sans(pgn)
    if not 0 < ply <= len(moves):
        sys.exit(f"The game has {len(moves)} half-moves, so it has no ply {ply}.")
    board = before = Board()
    for i, san in enumerate(moves[:ply]):
        before, board = board, board.play(san)
        if board is None:
            sys.exit(f"The game's move {san} at ply {i + 1} isn't legal there, so the game can't be read.")
    return board, before, moves[ply - 1]


def between(a, b):
    """The squares strictly between two squares on one rank, file or diagonal, else none."""
    df, dr = (b % 8) - (a % 8), (b // 8) - (a // 8)
    if not (df == 0 or dr == 0 or abs(df) == abs(dr)):
        return []
    n = max(abs(df), abs(dr))
    step_f, step_r = (df > 0) - (df < 0), (dr > 0) - (dr < 0)
    return [a % 8 + step_f * i + 8 * (a // 8 + step_r * i) for i in range(1, n)]


def numbered(moves, first_ply):
    out = []
    for i, san in enumerate(moves):
        ply, n = first_ply + i, (first_ply + i) // 2 + 1
        out.append(f"{n}.{san}" if ply % 2 == 0 else (f"{n}...{san}" if i == 0 else san))
    return " ".join(out)


def side_of(of_white):
    return "White" if of_white else "Black"


def pieces(board, of_white):
    """One side's pieces as a FEN reader would list them: the king, then the others by value, then the pawns by file."""
    found = [(p.lower(), sq) for sq, p in enumerate(board.squares) if p and white(p) == of_white]
    order = "kqrbn"
    named = [p.upper() + name(sq) for p, sq in sorted((x for x in found if x[0] != "p"), key=lambda x: (order.index(x[0]), x[1] % 8, x[1]))]
    pawns = [name(sq) for p, sq in sorted((x for x in found if x[0] == "p"), key=lambda x: (x[1] % 8, x[1]))]
    if pawns:
        named.append(("pawns " if len(pawns) > 1 else "pawn ") + ", ".join(pawns))
    return f"{side_of(of_white)}: " + ", ".join(named) + "."


def around(board, of_white):
    """The squares next to a king, in front of, beside and behind it, each said from that king's side."""
    k = board.king(of_white)
    forward = 1 if of_white else -1

    def say(sq):
        p = board.squares[sq]
        if not p:
            return f"{name(sq)} empty"
        return f"{name(sq)} its own {NAMES[p.lower()]}" if white(p) == of_white else f"{name(sq)} an enemy {NAMES[p.lower()]}"

    near = sorted((sq for sq in board.attacks(k)), key=lambda sq: sq % 8)
    groups = [("in front of it", [s for s in near if s // 8 - k // 8 == forward]),
              ("beside it", [s for s in near if s // 8 == k // 8]),
              ("behind it", [s for s in near if s // 8 - k // 8 == -forward])]
    parts = [f"{label}: " + ", ".join(say(s) for s in squares) for label, squares in groups if squares]
    parts[0] = parts[0][0].upper() + parts[0][1:]
    # Said outright either way, as the model reads a stated fact far better than one it has to work out.
    shielding = [s for s in groups[0][1] if board.squares[s] and white(board.squares[s]) == of_white]
    shield = (f" Its own pieces in front of it: " + ", ".join(f"{NAMES[board.squares[s].lower()]} on {name(s)}" for s in shielding) + "."
              if shielding else " None of its own pieces stands in front of it.")
    return f"The {side_of(of_white).lower()} king is on {name(k)}, rank {k // 8 + 1}. " + "; ".join(parts) + "." + shield


def moved(board, before, san):
    """The move's piece, where it went and the enemy pieces it now attacks, most valuable first."""
    mover = before.white_to_move
    changed = [sq for sq in range(64) if before.squares[sq] != board.squares[sq]]
    to = next(sq for sq in changed if board.squares[sq] and white(board.squares[sq]) == mover
              and not (board.squares[sq].lower() == "r" and san.startswith("O")))
    frm = next(sq for sq in changed if before.squares[sq] and white(before.squares[sq]) == mover
               and not board.squares[sq] and (before.squares[sq].lower() == "k" or not san.startswith("O")))
    piece = board.squares[to]
    hit = sorted((sq for sq in board.attacks(to) if board.squares[sq] and white(board.squares[sq]) != mover),
                 key=lambda sq: (-VALUE[board.squares[sq].lower()], sq % 8, sq))
    def target(sq):
        said = f"the {NAMES[board.squares[sq].lower()]} on {name(sq)}"
        if board.squares[sq].lower() == "k" and piece.lower() in "rbq":
            said += (f" along rank {sq // 8 + 1}" if sq // 8 == to // 8 else f" along the {FILES[sq % 8]}-file"
                     if sq % 8 == to % 8 else " along a diagonal")
        return said

    hits = ", ".join(target(sq) for sq in hit) or "no enemy piece"
    text = (f"The move took {side_of(mover)}'s {NAMES[piece.lower()]} from {name(frm)} to {name(to)}. "
            f"From {name(to)} it attacks {hits}.")
    k = board.king(not mover)
    near = max(abs(k % 8 - to % 8), abs(k // 8 - to // 8)) == 1
    text += " It stands next to the enemy king." if near else " It isn't next to the enemy king."
    for sq, p in enumerate(board.squares):
        # A line piece of the same side that the move uncovered: it now attacks, through the square the piece left,
        # an enemy piece it didn't attack before.
        if not p or white(p) != mover or sq == to or p.lower() not in "rbq":
            continue
        opened = [t for t in board.attacks(sq) if t not in before.attacks(sq) and board.squares[t]
                  and white(board.squares[t]) != mover and frm in between(sq, t)]
        if opened:
            targets = ", ".join(f"the {NAMES[board.squares[t].lower()]} on {name(t)}" for t in opened)
            text += f" Moving it uncovered {side_of(mover)}'s {NAMES[p.lower()]} on {name(sq)}, which now attacks {targets}."
    return text


def words(pgn, ply):
    """The board after ply half-moves of the game, in words."""
    board, before, san = replay(pgn, ply)
    return "\n".join([moved(board, before, san), pieces(board, True), pieces(board, False), around(board, True), around(board, False)])


def window(pgn, ply, before=4, after=4):
    """The game's moves from `before` moves ahead of ply's to `after` past it, numbered, and ply's own move."""
    moves = sans(pgn)
    lo, hi = max(0, ply - 1 - before), min(len(moves), ply + after)
    return numbered(moves[lo:hi], lo), numbered([moves[ply - 1]], ply - 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pgn", type=Path, help="a PGN file; its first game is read unless --game says")
    parser.add_argument("--ply", type=int, required=True, help="half-moves from the start, as the vector rows count them")
    parser.add_argument("--game", type=int, default=0, help="which game of the file, from 0")
    args = parser.parse_args()
    found = split_games(read_pgn(args.pgn))
    if not 0 <= args.game < len(found):
        sys.exit(f"{args.pgn} has {len(found)} games, counted from 0.")
    print(words(found[args.game].text, args.ply))


if __name__ == "__main__":
    main()
