#!/usr/bin/env python3
"""A player's mistakes across their last games, from Engine's whole-game answers. NumPy only, on Python 3.11 or later,
with the `chessdrive` CLI signed in.

    python3 mistakes.py games.pgn --player MyHandle --folder patterns

Sends as many games at once as the Plan's requests in flight. Keeps each game's answer in the folder, so running it
again carries on and bills no game twice. Writes:

    items.json       the position after each mistake, where what it allowed is on the board, for `chessdrive embed --input`
    mistakes.jsonl   what each row of items.json is: the game, the move, its verdict, Engine's best Line from before
                     it, and what it allowed: Engine's best Line for the other side after it

Prints one JSON object a line: a line per game, then the totals. A game Engine refuses is skipped and named.
"""

import argparse
import json
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.dont_write_bytecode = True  # keeps the Plugin's folder as it was installed
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "chessdrive-vectors" / "scripts"))

from vectorfile import TAG, USD_PER_1K_ITEMS, emit, read_pgn, split_games

WENT_WRONG = ("mistake", "blunder")
EXIT_INVALID, EXIT_RATE_LIMITED = 2, 5
SHORTER_DEPTH = 10  # for a game too long for one call at the default depth
RETRIES = 5
RETRY_SECONDS = int(os.environ.get("CHESSDRIVE_RETRY_SECONDS", 5))
IN_FLIGHT = {"free": 1, "hobby": 2, "pro": 6}  # Stockfish's requests in flight on each Plan


class Slots:
    """The calls a run may have at Engine at once. Each 429 costs it one, as another run on the Account or a smaller
    engine can leave less than the Plan allows, and the calls it stops would only have waited 5 s to be refused."""

    def __init__(self, size):
        self.size = size
        self.free = threading.Semaphore(size)
        self.lock = threading.Lock()

    def __enter__(self):
        self.free.acquire()

    def __exit__(self, *_):
        self.free.release()

    def one_fewer(self):
        with self.lock:
            if self.size == 1:
                return
            self.size -= 1
        self.free.acquire()


def tags_of(game):
    return dict(TAG.findall(game.text))


def colour_of(tags, player):
    """Which side the player had, or None for a game they aren't in."""
    wanted = player.casefold()
    return next((c for c in ("White", "Black") if tags.get(c, "").casefold() == wanted), None)


def played_at(tags):
    return tags.get("UTCDate") or tags.get("Date") or "", tags.get("UTCTime") or tags.get("Time") or ""


def last_games(games, player, count):
    """The player's newest `count` games, oldest first, whatever order the file is in."""
    theirs = [g for g in games if colour_of(tags_of(g), player)]
    theirs.sort(key=lambda g: played_at(tags_of(g)))  # stable, so games with no date keep the file's order
    return theirs[-count:]


def names_in(games):
    seen = {}
    for game in games:
        tags = tags_of(game)
        for colour in ("White", "Black"):
            if name := tags.get(colour):
                seen[name] = seen.get(name, 0) + 1
    return sorted(seen, key=seen.get, reverse=True)[:5]


def in_flight(cli):
    """How many calls the Plan lets a run send at once, or 1 where the Plan can't be read, as on a Team member's key."""
    done = subprocess.run([cli, "balance", "--json"], capture_output=True, text=True, encoding="utf-8")
    try:
        return IN_FLIGHT.get(json.loads(done.stdout).get("plan"), 1)
    except ValueError:
        return 1


def call_engine(cli, game, slots):
    """A whole game's answer, retrying what can pass and stopping the run on what can't. None is a game refused."""
    args = [cli, "engine", "--pgn", "-", "--json"]
    for attempt in range(RETRIES):
        with slots:
            done = subprocess.run(args, input=game.text, capture_output=True, text=True, encoding="utf-8")
        if done.returncode == 0:
            return json.loads(done.stdout)
        if done.returncode == EXIT_RATE_LIMITED:
            slots.one_fewer()
        if done.returncode == EXIT_RATE_LIMITED or done.returncode == 1:
            time.sleep(min(60, RETRY_SECONDS * 2**attempt))
            continue
        if "limit_too_high" in done.stderr and "--depth" not in args:
            args += ["--depth", str(SHORTER_DEPTH)]
            continue
        if done.returncode == EXIT_INVALID:
            return None
        sys.exit(done.stderr.strip() or f"{cli} stopped with code {done.returncode}.")
    sys.exit(done.stderr.strip() or f"{cli} kept failing.")


def answers_of(cli, games, folder):
    """Each game's place in games and its answer, as they come: those saved, then the rest from Engine, up to the Plan's
    requests in flight. A game refused answers None. A stop lets the calls running end, as they're billed and saved."""
    calls = []
    for at, game in enumerate(games):
        saved = folder / f"{game.id()}.json"
        if saved.exists():
            yield at, json.loads(saved.read_text(encoding="utf-8"))
        else:
            calls.append((at, game, saved))
    if not calls:
        return

    slots = Slots(in_flight(cli))

    def answer(at, game, saved):
        found = call_engine(cli, game, slots)
        if found is not None:
            saved.write_text(json.dumps(found), encoding="utf-8")
        return at, found

    with ThreadPoolExecutor(slots.size) as pool:
        running = [pool.submit(answer, *call) for call in calls]
        try:
            for done in as_completed(running):
                yield done.result()
        finally:
            pool.shutdown(cancel_futures=True)


def in_words(score):
    """An evaluation from White's side, in the Game review Skill's words."""
    if score.get("mate") is not None:
        side = "White" if score["mate"] > 0 else "Black"
        return "the game is over" if score["mate"] == 0 else f"{side} is mating"
    cp = score.get("cp") or 0
    side = "White" if cp > 0 else "Black"
    if abs(cp) < 50:
        return "about equal"
    return f"{side} is {'a little better' if abs(cp) < 150 else 'clearly better' if abs(cp) < 300 else 'winning'}"


def written(move):
    """The move as an answer writes it, with its mark: 14...Qd7??"""
    mark = "??" if move["verdict"] == "blunder" else "?"
    return f"{move['move_number']}{'.' if move['color'] == 'white' else '...'}{move['move']['san']}{mark}"


def sans(move):
    return [m["san"] for m in move.get("best_line") or []]


def mistakes_of(answer, game, number_in_file, colour):
    tags = tags_of(game)
    opponent = tags.get("Black" if colour == "White" else "White", "")
    moves = answer["moves"]
    for at, move in enumerate(moves):
        if move["verdict"] in WENT_WRONG and move["color"] == colour.lower():
            after = moves[at + 1] if at + 1 < len(moves) else {}  # the reply's best Line: what the mistake allowed
            yield {
                "game": number_in_file,
                "ply": move["ply"],
                "move": written(move),
                "verdict": move["verdict"],
                "colour": colour,
                "opponent": opponent,
                "date": played_at(tags)[0],
                "site": tags.get("Site", ""),
                "best": sans(move),
                "allowed": sans(after),
                "before": in_words(move["eval_before"]),
                "after": in_words(move["eval_after"]),
                "lost": move["win_chance_lost"],
                "fen": move["fen"],
                "pgn": game.text,
            }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pgn", help="a PGN file holding the player's games")
    parser.add_argument("--player", required=True, help="the player's name as the PGN's White and Black tags write it")
    parser.add_argument("--folder", default="patterns", help="where the answers and the two files go")
    parser.add_argument("--games", type=int, default=30, help="how many of their newest games (default 30)")
    parser.add_argument("--cli", default="chessdrive", help="the CLI to call")
    args = parser.parse_args()

    games = split_games(read_pgn(args.pgn))
    chosen = last_games(games, args.player, args.games)
    if not chosen:
        sys.exit(f'No game in {args.pgn} has "{args.player}" as White or Black. The names there: {", ".join(names_in(games))}.')

    folder = Path(args.folder)
    answers = folder / "engine"
    answers.mkdir(parents=True, exist_ok=True)
    by_game, refused_by_game, cost = {}, {}, 0.0
    for at, answer in answers_of(args.cli, chosen, answers):
        game, tags = chosen[at], tags_of(chosen[at])
        if answer is None:
            refused_by_game[at] = {"game": at, "white": tags.get("White"), "black": tags.get("Black"), "date": played_at(tags)[0]}
            continue
        cost += float(answer.get("cost_usd") or 0)
        by_game[at] = list(mistakes_of(answer, game, at, colour_of(tags, args.player)))
        emit({"game": at, "of": len(chosen), "mistakes": len(by_game[at])})

    mistakes = [m for at in sorted(by_game) for m in by_game[at]]  # answers come in any order, and the files keep the games'
    refused = [refused_by_game[at] for at in sorted(refused_by_game)]
    (folder / "items.json").write_text(
        json.dumps([{"type": "position", "pgn": m["pgn"], "ply": m["ply"] + 1} for m in mistakes]), encoding="utf-8"
    )
    (folder / "mistakes.jsonl").write_text("".join(json.dumps(m, ensure_ascii=False) + "\n" for m in mistakes), encoding="utf-8")
    newest = tags_of(chosen[-1])
    emit({
        "games": len(chosen) - len(refused),
        "rating": newest.get(f"{colour_of(newest, args.player)}Elo"),
        "refused": refused,
        "positions": len(mistakes),
        "blunders": sum(m["verdict"] == "blunder" for m in mistakes),
        "engine_cost_usd": round(cost, 4),
        "embed_cost_usd": round(len(mistakes) * USD_PER_1K_ITEMS / 1000, 4),
    })


if __name__ == "__main__":
    main()
