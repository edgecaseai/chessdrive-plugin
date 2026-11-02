#!/usr/bin/env python3
"""Download a player's public games to a PGN file, newest first, from Lichess or chess.com, on the machine this runs on
and with no ChessDrive call. The Python standard library only, on Python 3.11 or later.

    python3 fetch_games.py lichess cemoss17 --how-long
    python3 fetch_games.py lichess cemoss17 --out games.pgn
    python3 fetch_games.py chesscom cemoss17 --out games.pgn --max 30

It takes every game, or their newest `--max`. `--how-long` asks how long that takes, with no download. Lichess sends
about 20 games a second, and a program may run one such download at a time. chess.com serves a month at a time, one
request after another. Both sites ask a program to say what it is, and refuse a plain one.

Prints one JSON object: the site, the player, the games and the file. On a site it can't reach, it stops and says so,
and the person downloads the file in their browser.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

AGENT = "ChessDrive-skills/0.1 (contact@edgecaselabs.dev)"
LICHESS_PLAYER = "https://lichess.org/api/user/{name}"
LICHESS_GAMES = "https://lichess.org/api/games/user/{name}?clocks=false&evals=false&opening=true"
CHESSCOM = "https://api.chess.com/pub/player/{name}/games/archives"
LICHESS_GAMES_A_SECOND = 20
CHESSCOM_SECONDS_A_MONTH = 3
BUSY_SECONDS = int(os.environ.get("CHESSDRIVE_RETRY_SECONDS", 60))  # Lichess asks for a full minute after a 429
CHUNK = 65_536
GAME_START = re.compile(rb'^(?=\[Event ")', re.M)
PLAYED = re.compile(rb'^\[UTC(?:Date|Time) "([^"]*)"', re.M)
EXPORT = "Ask the person to download the file in their browser instead."


def opened(url, accept):
    """The answer to one request, waiting once if the site says it's busy. None if the player isn't there."""
    request = urllib.request.Request(url, headers={"User-Agent": AGENT, "Accept": accept})
    for attempt in (1, 2):
        try:
            return urllib.request.urlopen(request, timeout=60)
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return None
            if error.code != 429 or attempt == 2:
                sys.exit(f"The site answered {error.code} for {url}. {EXPORT}")
            time.sleep(BUSY_SECONDS)
        except urllib.error.URLError as error:
            sys.exit(f"Can't reach the site from here ({error.reason}). {EXPORT}")


def games_in(text):
    return text.count(b'[Event "')


def lichess(name, most, out):
    url = LICHESS_GAMES.format(name=name) + (f"&max={most}" if most else "")
    answer = opened(url, "application/x-chess-pgn")
    while answer and (chunk := answer.read(CHUNK)):
        out.write(chunk)


def months_of(name):
    """The addresses of the months with games, newest first, or None if the player isn't there."""
    answer = opened(CHESSCOM.format(name=name.lower()), "application/json")
    return list(reversed(json.load(answer)["archives"])) if answer else None


def newest_first(month):
    """A chess.com month's games, which come oldest first."""
    return sorted((g for g in GAME_START.split(month) if g.strip()), key=PLAYED.findall, reverse=True)


def chesscom(name, most, out):
    left = most
    for month in months_of(name) or []:
        time.sleep(1)  # one at a time, as chess.com asks
        answer = opened(f"{month}/pgn", "application/x-chess-pgn")
        if answer is None:
            continue
        games = newest_first(answer.read())
        out.writelines(game.rstrip() + b"\n\n" for game in games[: left or None])
        if most:
            left -= min(left, len(games))
            if not left:
                break


def how_long(site, name, most):
    if site == "lichess":
        answer = opened(LICHESS_PLAYER.format(name=name), "application/json")
        games = json.load(answer)["count"]["all"] if answer else 0
        games = min(games, most) if most else games
        return {"games": games, "seconds": max(1, games // LICHESS_GAMES_A_SECOND)} if games else None
    months = months_of(name)
    return {"months": len(months), "seconds": CHESSCOM_SECONDS_A_MONTH * len(months)} if months else None


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("site", choices=("lichess", "chesscom"))
    parser.add_argument("player", help="their username on that site")
    parser.add_argument("--out", help="the PGN file to write")
    parser.add_argument("--max", type=int, default=0, help="only their newest games, this many")
    parser.add_argument("--how-long", action="store_true", help="say how long it takes, and download nothing")
    args = parser.parse_args()
    missing = f"{args.site} has no games for {args.player}. Check the spelling with the person."
    if args.how_long:
        print(json.dumps({"site": args.site, "player": args.player, **(how_long(args.site, args.player, args.max) or sys.exit(missing))}))
        return
    if not args.out:
        parser.error("say where to write the games with --out")
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as out:
        (lichess if args.site == "lichess" else chesscom)(args.player, args.max, out)
    games = games_in(path.read_bytes())
    if not games:
        path.unlink()
        sys.exit(missing)
    print(json.dumps({"site": args.site, "player": args.player, "games": games, "file": str(path)}))


if __name__ == "__main__":
    main()
