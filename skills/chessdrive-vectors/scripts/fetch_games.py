#!/usr/bin/env python3
"""Download a player's public games to a PGN file, newest first, from Lichess or chess.com, on the machine this runs on
and with no ChessDrive call. The Python standard library only, on Python 3.11 or later.

    python3 fetch_games.py lichess cemoss17 --how-long
    python3 fetch_games.py lichess cemoss17 --out games.pgn
    python3 fetch_games.py chesscom cemoss17 --out games.pgn --max 30
    python3 fetch_games.py lichess cemoss17 --speed rapid --since 2026-09-01 --out games.pgn
    python3 fetch_games.py --url https://lichess.org/abcdefgh --out game.pgn
    python3 fetch_games.py --url https://www.chess.com/game/live/123456789 --username cemoss17 --out game.pgn

It takes every game, or their newest `--max`, of the time controls `--speed` names and played from `--since` to
`--until`. Lichess sends only those games, and chess.com, which serves whole months, has only the months in that range
read and keeps that month's games of those speeds. `--url` takes the one game a link names, in any form the sites give: a
chess.com link needs either player's username, as chess.com finds a game only among a player's months. `--how-long` asks how many games that is and how long it takes, with no download. Lichess sends
about 20 games a second, and a program may run one such download at a time. chess.com serves a month at a time, one
request after another. Both sites ask a program to say what it is, and refuse a plain one.

Prints one JSON object: the site, the player, the games and the file, or for a link the game's players, date, result,
the side the link or the username played, and the file. On a site it can't reach, it stops and says so,
and the person downloads the file in their browser.
"""

import argparse
import datetime
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

AGENT = "ChessDrive-skills/0.1 (contact@edgecaselabs.dev)"
LICHESS_PLAYER = "https://lichess.org/api/user/{name}"
LICHESS_SPEED = "https://lichess.org/api/user/{name}/perf/{speed}"
LICHESS_GAMES = "https://lichess.org/api/games/user/{name}?clocks=false&evals=false&opening=true"
CHESSCOM = "https://api.chess.com/pub/player/{name}/games/archives"
CHESSCOM_STATS = "https://api.chess.com/pub/player/{name}/stats"
LICHESS_GAME = "https://lichess.org/game/export/{id}?clocks=false&evals=false&opening=true"
CHESSCOM_MONTHS = 6  # how far back a link's game is looked for, as the Connector's get_game does
LICHESS_GAMES_A_SECOND = 20
CHESSCOM_SECONDS_A_MONTH = 3
BUSY_SECONDS = int(os.environ.get("CHESSDRIVE_RETRY_SECONDS", 60))  # Lichess asks for a full minute after a 429
CHUNK = 65_536
EXPORT = "Ask the person to download the file in their browser instead."
PASTE = "Ask the person to paste the game's PGN instead."
LICHESS_ID = re.compile(r"^[a-zA-Z0-9]{8}(?:[a-zA-Z0-9]{4})?$")
CHESSCOM_ID = re.compile(r"^[0-9]{1,20}$")
LANGUAGE = re.compile(r"^[a-z]{2}(?:-[a-zA-Z]{2})?$")
TAG = re.compile(r'^\[(\w+) "((?:[^"\\]|\\.)*)"\]', re.M)
SPEEDS = ("bullet", "blitz", "rapid", "classical", "correspondence")
# chess.com's time classes. It has no classical, so classical is its rapid games of 25 minutes or more, by Lichess's line:
# the base time and 40 increments.
TIME_CLASS = {"bullet": "bullet", "blitz": "blitz", "rapid": "rapid", "classical": "rapid", "correspondence": "daily"}
CLASSICAL_SECONDS = 1500
DAY = datetime.timedelta(days=1)


class Scope:
    """Which games to take: the speeds, none for all, and the first and last day, as UTC dates."""

    def __init__(self, speeds=(), since=None, until=None):
        self.speeds, self.since, self.until = tuple(speeds), since, until

    def __bool__(self):
        return bool(self.speeds or self.since or self.until)

    def lichess_query(self):
        """Lichess's own filter, so it sends only these games. Its until is exclusive, so it's the day after."""
        query = {"perfType": ",".join(self.speeds)} if self.speeds else {}
        for key, day in (("since", self.since), ("until", self.until and self.until + DAY)):
            if day:
                query[key] = int(datetime.datetime.combine(day, datetime.time(), datetime.UTC).timestamp() * 1000)
        return "&" + urllib.parse.urlencode(query) if query else ""

    def months(self, addresses):
        """chess.com's monthly addresses inside the dates, which end in /YYYY/MM."""
        first = self.since and (self.since.year, self.since.month)
        last = self.until and (self.until.year, self.until.month)
        return [a for a in addresses if (not first or month_of(a) >= first) and (not last or month_of(a) <= last)]

    def takes(self, game):
        """Whether a game from chess.com's month JSON is in scope: its speed, standard chess for a speed, and its day."""
        if self.speeds:
            if game.get("rules") != "chess" or not any(self.of_speed(game, speed) for speed in self.speeds):
                return False
        day = datetime.datetime.fromtimestamp(game.get("end_time", 0), datetime.UTC).date()
        return (not self.since or day >= self.since) and (not self.until or day <= self.until)

    @staticmethod
    def of_speed(game, speed):
        if game.get("time_class") != TIME_CLASS[speed]:
            return False
        if speed != "classical":
            return True
        base, _, increment = game.get("time_control", "").partition("+")
        return base.isdigit() and int(base) + 40 * int(increment or 0) >= CLASSICAL_SECONDS


def month_of(address):
    year, month = address.rstrip("/").split("/")[-2:]
    return int(year), int(month)


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


def lichess(name, most, out, scope):
    url = LICHESS_GAMES.format(name=name) + (f"&max={most}" if most else "") + scope.lichess_query()
    answer = opened(url, "application/x-chess-pgn")
    while answer and (chunk := answer.read(CHUNK)):
        out.write(chunk)


def months_of(name):
    """The addresses of the months with games, newest first, or None if the player isn't there."""
    answer = opened(CHESSCOM.format(name=name.lower()), "application/json")
    return list(reversed(json.load(answer)["archives"])) if answer else None


def newest_first(month, scope):
    """A chess.com month's PGNs in scope, newest first, from its JSON, whose games come oldest first."""
    games = [g for g in json.load(month)["games"] if g.get("pgn") and scope.takes(g)]
    return [g["pgn"].encode() for g in sorted(games, key=lambda g: g.get("end_time", 0), reverse=True)]


def chesscom(name, most, out, scope):
    left = most
    for month in scope.months(months_of(name) or []):
        time.sleep(1)  # one at a time, as chess.com asks
        answer = opened(month, "application/json")
        if answer is None:
            continue
        games = newest_first(answer, scope)
        out.writelines(game.rstrip() + b"\n\n" for game in games[: left or None])
        if most:
            left -= min(left, len(games))
            if not left:
                break


def link_of(url):
    """The site, game id and the side a link shows, from every form of game link the two sites give, or None."""
    url = url.strip()
    parts = urllib.parse.urlsplit(url if "://" in url else "https://" + url)
    path = [p for p in parts.path.split("/") if p]
    host = (parts.hostname or "").lower().removeprefix("www.")
    if parts.scheme not in ("http", "https") or parts.username or parts.port:
        return None
    if host == "lichess.org":
        for start in (["game", "export"], ["embed", "game"], ["game"]):
            if path[: len(start)] == start and len(path) > len(start):
                path = path[len(start) :]
                break
        if not path or len(path) > 2 or not LICHESS_ID.match(path[0]) or path[1:] not in ([], ["white"], ["black"]):
            return None
        return "lichess", path[0][:8], path[1] if len(path) == 2 else None
    if host == "chess.com":
        path = path[1:] if path and LANGUAGE.match(path[0]) else path
        path = path[1:] if path[:1] == ["analysis"] else path
        if path[:2] in (["game", "live"], ["game", "daily"], ["live", "game"], ["daily", "game"]):
            path = path[2:]
        elif path[:1] == ["game"]:
            path = path[1:]
        else:
            return None
        if path[:1] == ["computer"]:
            sys.exit(f"chess.com doesn't publish games against its computer. {PASTE}")
        return ("chesscom", path[0], None) if path and CHESSCOM_ID.match(path[0]) else None
    return None


def chesscom_game(game_id, name):
    """The PGN of a chess.com game, from the player's newest months."""
    for month in (months_of(name) or sys.exit(f"chess.com has no player {name}. Check the spelling with the person."))[:CHESSCOM_MONTHS]:
        time.sleep(1)  # one at a time, as chess.com asks
        answer = opened(month, "application/json")
        for game in json.load(answer)["games"] if answer else []:
            if game.get("url", "").endswith("/" + game_id):
                if game.get("rules") != "chess":
                    sys.exit("That game isn't standard chess, which is all the engine reviews.")
                return game["pgn"].encode()
    sys.exit(f"That game isn't in {name}'s last {CHESSCOM_MONTHS} months on chess.com. It may be older, or another player's. {PASTE}")


def one_game(url, name, path):
    """Writes the game a link names to path, and says what it is."""
    link = link_of(url) or sys.exit(f"That isn't a Lichess or chess.com game link. Ask for the game's link or its PGN.")
    site, game_id, colour = link
    if site == "chesscom":
        name = (name or "").strip().removeprefix("@")
        if not name:
            sys.exit("A chess.com link needs the chess.com username of either player. Ask the person for theirs, then run it again with --username.")
        text = chesscom_game(game_id, name.lower())
    else:
        answer = opened(LICHESS_GAME.format(id=game_id), "application/x-chess-pgn")
        text = answer.read() if answer else sys.exit(f"That game wasn't found. Check the link with the person, or ask them to paste its PGN.")
    tags = {k: v for k, v in TAG.findall(text.decode("utf-8", "replace"))}
    if tags.get("Variant", "Standard") not in ("Standard", "From Position"):
        sys.exit("That game isn't standard chess, which is all the engine reviews.")
    if tags.get("Result") not in ("1-0", "0-1", "1/2-1/2"):
        sys.exit("That game isn't finished. A review needs a finished game.")
    if not colour and name:
        colour = next((c.lower() for c in ("White", "Black") if tags.get(c, "").casefold() == name.casefold()), None)
    path.write_bytes(text.rstrip() + b"\n")
    return {"site": site, "game": game_id, "white": tags.get("White"), "black": tags.get("Black"),
            "date": tags.get("UTCDate") or tags.get("Date"), "result": tags["Result"], "color": colour, "file": str(path)}


def lichess_count(name, scope):
    """Lichess's count of a player's games, of the speeds in scope, from its player API, or None if it has no player."""
    if not scope.speeds:
        answer = opened(LICHESS_PLAYER.format(name=name), "application/json")
        return json.load(answer)["count"]["all"] if answer else None
    counts = [opened(LICHESS_SPEED.format(name=name, speed=speed), "application/json") for speed in scope.speeds]
    return sum(json.load(a)["stat"]["count"]["all"] for a in counts if a) if any(counts) else None


def chesscom_count(name, scope):
    """chess.com's count of a player's rated games, of the speeds in scope: its stats count no others."""
    answer = opened(CHESSCOM_STATS.format(name=name.lower()), "application/json")
    stats = json.load(answer) if answer else {}
    classes = {TIME_CLASS[s] for s in scope.speeds} or set(TIME_CLASS.values())
    return sum(sum(stats.get(f"chess_{c}", {}).get("record", {}).get(k, 0) for k in ("win", "loss", "draw")) for c in classes)


def how_long(site, name, most, scope):
    """How many games, and the seconds to download them. A count is exact only for Lichess with no dates: Lichess
    counts by speed but not by date, so with dates it's the most there can be, and chess.com counts only rated games."""
    exact = site == "lichess" and not (scope.since or scope.until)
    if site == "lichess":
        games = lichess_count(name, scope)
        if games is None:
            return None
        games = min(games, most) if most else games
        return {"games": games, "exact": exact, "seconds": max(1, games // LICHESS_GAMES_A_SECOND)}
    months = months_of(name)
    if not months:
        return None
    months = scope.months(months)
    return {"games": chesscom_count(name, scope), "exact": exact, "months": len(months),
            "seconds": CHESSCOM_SECONDS_A_MONTH * len(months)}


def speeds(text):
    named = [s.strip().lower() for s in text.split(",") if s.strip()]
    if not named or any(s not in SPEEDS for s in named):
        raise argparse.ArgumentTypeError(f"name one or more of {', '.join(SPEEDS)}, comma-separated")
    return tuple(dict.fromkeys(named))


def day(text):
    try:
        return datetime.date.fromisoformat(text)
    except ValueError:
        raise argparse.ArgumentTypeError("give a date as YYYY-MM-DD")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("site", nargs="?", choices=("lichess", "chesscom"))
    parser.add_argument("player", nargs="?", help="their username on that site")
    parser.add_argument("--url", help="one game's link on Lichess or chess.com, instead of a player's games")
    parser.add_argument("--username", help="with a chess.com --url, either player's username")
    parser.add_argument("--out", help="the PGN file to write")
    parser.add_argument("--max", type=int, default=0, help="only their newest games, this many")
    parser.add_argument("--speed", type=speeds, default=(), help=f"only these time controls, comma-separated: {', '.join(SPEEDS)}")
    parser.add_argument("--since", type=day, help="only games played on this day or later, as YYYY-MM-DD")
    parser.add_argument("--until", type=day, help="only games played on this day or earlier, as YYYY-MM-DD")
    parser.add_argument("--how-long", action="store_true", help="say how many games and how long it takes, and download nothing")
    args = parser.parse_args()
    if args.url:
        if not args.out:
            parser.error("say where to write the game with --out")
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        print(json.dumps(one_game(args.url, args.username, Path(args.out))))
        return
    if not args.site or not args.player:
        parser.error("give a site and a username, or a game's --url")
    scope = Scope(args.speed, args.since, args.until)
    if scope.since and scope.until and scope.since > scope.until:
        parser.error("--since is after --until")
    asked = {k: v for k, v in (("speed", ",".join(scope.speeds)), ("since", str(scope.since or "")), ("until", str(scope.until or ""))) if v}
    missing = f"{args.site} has no games for {args.player}. Check the spelling with the person."
    if scope:
        missing = f"{args.site} has no games for {args.player} of {', '.join(f'{k} {v}' for k, v in asked.items())}. Check the spelling, or ask the person for a wider scope."
    if args.how_long:
        print(json.dumps({"site": args.site, "player": args.player, **asked, **(how_long(args.site, args.player, args.max, scope) or sys.exit(missing))}))
        return
    if not args.out:
        parser.error("say where to write the games with --out")
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as out:
        (lichess if args.site == "lichess" else chesscom)(args.player, args.max, out, scope)
    games = games_in(path.read_bytes())
    if not games:
        path.unlink()
        sys.exit(missing)
    print(json.dumps({"site": args.site, "player": args.player, **asked, "games": games, "file": str(path)}))


if __name__ == "__main__":
    main()
