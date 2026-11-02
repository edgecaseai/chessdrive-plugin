"""Read the two files `chessdrive embed --out` writes. NumPy only, on Python 3.11 or later.

x.npy holds one vector per row, and x.jsonl says what each row is. compare.py and group.py are built on this, and a
script of your own can be too: `from vectorfile import load, cosine, unit, show`. Nothing here prints a vector.

Run it on PGN files to see what embedding them would cost, with no call and no charge:

    python3 vectorfile.py games.pgn
"""

import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from pgn import TAG, Game, is_move, is_result, main_line, read_pgn, scan, split_games  # noqa: F401, the other scripts import them from here

# Rows taken at a time, so a file larger than memory works.
CHUNK = 65_536
USD_PER_1K_ITEMS = 0.04


@dataclass
class VectorFile:
    path: Path
    vectors: np.ndarray  # memory-mapped, (rows, dimensions)
    rows: list[dict]  # rows[i] says what vectors[i] is
    model: str


def load(path):
    """A vector file's rows that both files hold: a stopped run's files load, with the rows so far."""
    npy = Path(str(path) if str(path).endswith(".npy") else f"{path}.npy")
    jsonl = npy.with_suffix(".jsonl")
    if not npy.exists() or not jsonl.exists():
        sys.exit(f"{npy} and {jsonl} go together, and this needs both: make them with `chessdrive embed --out {npy}`.")
    vectors = np.load(npy, mmap_mode="r")
    lines = jsonl.read_bytes().split(b"\n")[:-1]  # what follows the last newline: nothing, or a line cut short
    count = min(len(vectors), len(lines))
    if count == 0:
        sys.exit(f"{npy} has no rows yet.")
    rows = [json.loads(line) for line in lines[:count]]
    return VectorFile(npy, vectors[:count], rows, rows[0]["model"])


def same_model(a, b):
    """Stops unless two files can be compared."""
    if a.model != b.model:
        sys.exit(
            f"Vectors compare only within one Model version: {a.path} is {a.model} and {b.path} is {b.model}. "
            f"Embed the items of {b.path} again with {a.model}."
        )
    if a.vectors.shape[1] != b.vectors.shape[1]:
        sys.exit(f"{a.path} and {b.path} have vectors of different lengths, so they aren't one run's kind of file.")


def same_way(rows, mixed):
    """Stops if positions went in two ways, as a position with its game and a bare FEN give different vectors."""
    ways = {"bare FEN" if "fen" in r else "with its game" for r in rows if r["type"] == "position"}
    if len(ways) > 1 and not mixed:
        sys.exit(
            "These positions went in two ways, some with their game and some as a bare FEN, and the two give "
            "different vectors. Send them the same way, or pass --mixed for a rougher answer, and say that it is."
        )


def unit(vectors):
    """Vectors scaled to length 1, with a zero vector left at zero."""
    lengths = np.linalg.norm(vectors, axis=-1, keepdims=True)
    return vectors / np.where(lengths == 0, 1, lengths)


def cosine(vectors, query):
    """Each row's cosine with the query, from -1 to 1: the higher, the closer."""
    query = unit(np.asarray(query))
    scores = np.empty(len(vectors), "f4")
    for start in range(0, len(vectors), CHUNK):
        scores[start : start + CHUNK] = unit(np.asarray(vectors[start : start + CHUNK])) @ query
    return scores


class Games:
    """Finds the game behind a row, reading each PGN file once."""

    def __init__(self, file):
        self.folder = file.path.parent
        self.files = {}

    def find(self, row):
        """The row's game, or None if its file can't be found or the game has changed since it was embedded."""
        if "pgn" in row:
            return next(iter(split_games(row["pgn"])), None)
        if "source" not in row:
            return None
        source = row["source"]
        if source not in self.files:
            paths = [Path(source), self.folder / source]
            found = next((p for p in paths if p.is_file()), None)
            self.files[source] = split_games(read_pgn(found)) if found else []
        games = self.files[source]
        game = games[row["game"]] if row["game"] < len(games) else None
        return game if game and game.id() == row["game_id"] else None


def last_move(game, ply):
    """The move that reached a ply of a game, such as 14...Qd7, or None at its start."""
    moves = [w for _, _, w in scan(game.text) if w and is_move(w) and not is_result(w)]
    if ply == 0 or ply > len(moves):
        return None
    san = moves[ply - 1]
    san = san[san.rfind(".") + 1 :].rstrip("!?")
    if '[FEN "' in game.text:
        return san  # a set-up game may start at any move number
    return f"{(ply + 1) // 2}{'.' if ply % 2 else '...'}{san}"


def show(row, games):
    """What a row says, for an answer: an item that can go to another call, and the game it's from."""
    shown = {k: v for k, v in row.items() if k not in ("model", "game_id")}
    game = games.find(row)
    if game is None:
        if "source" in row:
            shown["warning"] = f"{row['source']} is missing or its game has changed, so this row shows no moves."
        return shown
    tags = dict(TAG.findall(game.text))
    shown.update({k.lower(): tags[k] for k in ("White", "Black", "Result") if k in tags})
    if date := tags.get("Date") or tags.get("UTCDate"):  # Lichess's exports have only the second
        shown["date"] = date
    if (move := last_move(game, row.get("ply", 0))) is not None:
        shown["move"] = move
    shown.pop("pgn", None)
    shown["pgn"] = game.text  # last, so output cut to length still shows the rest
    return shown


def emit(item):
    """Prints one JSON object on a line, whatever the terminal's encoding."""
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    print(json.dumps(item, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    games = [g for path in sys.argv[1:] for g in split_games(read_pgn(path))]
    items = sum(g.plies + 1 for g in games)
    emit({"games": len(games), "items": items, "cost_usd": round(items / 1000 * USD_PER_1K_ITEMS, 4)})
