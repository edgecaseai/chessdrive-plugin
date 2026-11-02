#!/usr/bin/env python3
"""What a player plays, counted from a PGN file of their games, with no call and no charge. The Python standard library
only, on Python 3.11 or later.

    python3 openings.py games.pgn --player cemoss17 --against white

`--against` is the colour the person preparing will have, so this example reads cemoss17's games with Black. Add
`--after "1. e4"` for what they do after the moves the person plays, `--speed` to choose speeds, `--lost` for only the
games they lost, and `--tree tree.json` to write the whole tree for a Study.

It reads their newest 200 games of that colour, leaves out bullet when 30 slower games remain, and prints one JSON
object: what it read and left out, their first moves, the top lines each as far as the games still agree, the line they
score worst in, their form, and `positions`, the end of each line, ready for Engine. Every move printed is in the file.
"""

import argparse
import json
import math
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

sys.dont_write_bytecode = True  # keeps the Plugin's folder as it was installed
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "chessdrive-vectors" / "scripts"))

from pgn import TAG, is_move, is_result, read_pgn, scan, split_games

NEWEST = 200  # games of the colour: what they play now, not what they played ten thousand games ago
ENOUGH_SLOWER = 30  # games, to read only the slower ones: a fast account's bullet says little about a long game
TOP_LINES = 3
MAX_PLIES = 16
LINE_SHARE = 0.05  # of the games read: a line needs this many, or MIN_LINE_GAMES, to be a line at all
MIN_LINE_GAMES = 3
FEW_GAMES = 20
RECENT = 30  # games: how much of a line is what they play now
FORM_GAMES = 12
WEAK_SCORE = 45  # percent
FAST = ("ultrabullet", "bullet")
SPEEDS = ((30, "ultrabullet"), (180, "bullet"), (480, "blitz"), (1500, "rapid"), (math.inf, "classical"))  # Lichess's


@dataclass
class Played:
    """One game, as the player saw it."""

    tags: dict
    colour: str
    moves: list
    result: str  # won, drawn or lost, for the player
    when: tuple
    speed: str

    def date(self):
        return self.when[0]


def tags_of(game):
    return dict(TAG.findall(game.text))


def moves_of(game):
    """The main line's moves, with their + and # and without their ! and ?, as the file writes them."""
    words = (word for _, _, word in scan(game.text) if word and is_move(word) and not is_result(word))
    return [word[word.rfind(".") + 1 :].rstrip("!?") for word in words]


def speed_of(tags):
    """The speed by the Lichess sum of base time and 40 increments, which reads a chess.com file too."""
    control = tags.get("TimeControl", "")
    if "/" in control:
        return "correspondence"
    base, _, increment = control.partition("+")
    if not base.isdigit() or (increment and not increment.isdigit()):
        return "unknown"
    seconds = int(base) + 40 * int(increment or 0)
    return next(name for limit, name in SPEEDS if seconds < limit)


def result_of(tags, colour):
    white, black = ("won", "lost") if colour == "White" else ("lost", "won")
    return {"1-0": white, "0-1": black, "1/2-1/2": "drawn"}.get(tags.get("Result"))


def played_at(tags):
    date = tags.get("UTCDate") or tags.get("Date") or ""
    return (date if date[:1].isdigit() else "", tags.get("UTCTime") or tags.get("Time") or "")


def theirs(games, player):
    """Their standard games, newest first, and how many of each kind it left out."""
    wanted, kept, left_out = player.casefold(), [], Counter()
    for game in games:
        tags = tags_of(game)
        colour = next((c for c in ("White", "Black") if tags.get(c, "").casefold() == wanted), None)
        if colour is None:
            continue
        moves = moves_of(game)
        result = result_of(tags, colour)
        if tags.get("Variant", "Standard").casefold() != "standard" and "FEN" not in tags:
            left_out["other_variants"] += 1
        elif "FEN" in tags:
            left_out["set_up_positions"] += 1
        elif not moves:
            left_out["no_moves"] += 1
        elif result is None:
            left_out["unfinished"] += 1
        else:
            kept.append(Played(tags, colour, moves, result, played_at(tags), speed_of(tags)))
    kept.sort(key=lambda g: g.when, reverse=True)
    return kept, left_out


def names_in(games):
    seen = Counter(tags[c] for tags in map(tags_of, games) for c in ("White", "Black") if tags.get(c))
    return [name for name, _ in seen.most_common(5)]


def chosen_speeds(games, asked):
    """Which speeds to read: the ones asked for, or all of them but bullet if enough slower games remain."""
    if asked == ["all"]:
        return sorted({g.speed for g in games})
    if asked:
        return asked
    slower = sorted({g.speed for g in games if g.speed not in FAST})
    enough = sum(g.speed in slower for g in games) >= ENOUGH_SLOWER
    return slower if enough else sorted({g.speed for g in games})


def numbered(moves, first_ply=0):
    """Moves as a line writes them: 1. e4 c5 2. Nf3, or 2...d6 when it opens on Black's move."""
    out = []
    for ply, move in enumerate(moves, first_ply):
        if ply % 2 == 0:
            out.append(f"{ply // 2 + 1}. {move}")
        else:
            out.append(f"{ply // 2 + 1}...{move}" if ply == first_ply else move)
    return " ".join(out)


def tally(games):
    done = Counter(g.result for g in games)
    played = len(games)
    return {
        "games": played,
        "won": done["won"],
        "drawn": done["drawn"],
        "lost": done["lost"],
        "score_percent": round(100 * (done["won"] + done["drawn"] / 2) / played),
        "last_played": max(g.date() for g in games),
    }


def branches(games, ply):
    """The moves played at a ply, most played first, each with its games."""
    found = {}
    for game in games:
        if ply < len(game.moves):
            found.setdefault(game.moves[ply], []).append(game)
    return sorted(found.items(), key=lambda item: -len(item[1]))


def leaves(games, moves, floor):
    """Every line at least `floor` games share, each as far as that many still agree."""
    deeper = [(move, branch) for move, branch in branches(games, len(moves)) if len(branch) >= floor]
    if not deeper or len(moves) >= MAX_PLIES:
        yield moves, games
        return
    for move, branch in deeper:
        yield from leaves(branch, moves + [move], floor)


def opening_of(games):
    """The opening most of these games name, up to the variation, as a game's tag names where it ended up. The file's
    own words, so a file with no `Opening` tag names none."""
    names = Counter(g.tags["Opening"].split(":")[0] for g in games if g.tags.get("Opening"))
    return names.most_common(1)[0][0] if names else None


def line_of(moves, games, recent):
    newest = {id(g) for g in recent}
    return {
        "line": numbered(moves),
        **tally(games),
        "of_their_last_30": sum(id(g) in newest for g in games),
        "opening": opening_of(games),
        "next": [{"move": numbered([move], len(moves)), "games": len(branch)} for move, branch in branches(games, len(moves))[:3]],
        "position": {"pgn": numbered(moves), "ply": len(moves)},
    }


def first_moves(games, start):
    """The moves from where the reading starts, and the replies to each."""
    return [
        {
            "move": numbered([move], start),
            **tally(branch),
            "replies": [{"move": numbered([reply], start + 1), **tally(after)} for reply, after in branches(branch, start + 1)[:4]],
        }
        for move, branch in branches(games, start)[:4]
    ]


def form_of(games):
    """The newest games at these speeds, of either colour, and their rating over them."""
    last = games[:FORM_GAMES]
    elo = [g.tags.get(f"{g.colour}Elo", "") for g in last]
    elo = [int(e) for e in elo if e.isdigit()]
    return {
        **{k: v for k, v in tally(last).items() if k != "last_played"},
        "from": last[-1].date(),
        "to": last[0].date(),
        "rating_then": elo[-1] if elo else None,
        "rating_now": elo[0] if elo else None,
        "games_newest_first": [
            {"date": g.date(), "colour": g.colour, "opponent": g.tags.get("Black" if g.colour == "White" else "White", ""), "result": g.result, "speed": g.speed}
            for g in last
        ],
    }


def tree_of(games, ply):
    """Everything the games played, for a Study, down to a move played once."""
    if ply >= MAX_PLIES:
        return []
    return [{"move": move, **tally(branch), "then": tree_of(branch, ply + 1)} for move, branch in branches(games, ply)]


def report(text, player, against, after, speed, lost=False):
    games = split_games(text)
    played, left_out = theirs(games, player)
    if not played:
        names = ", ".join(names_in(games))
        sys.exit(f"{player} isn't a player in this file." + (f" Its names include: {names}." if names else " It holds no games."))
    colour = "Black" if against == "white" else "White"
    speeds = chosen_speeds([g for g in played if g.colour == colour], speed)
    at_speed = [g for g in played if g.speed in speeds]
    of_colour = [g for g in played if g.colour == colour]
    other_speeds = Counter(g.speed for g in of_colour if g.speed not in speeds)
    from_speed = [g for g in of_colour if g.speed in speeds]
    wanted = after.replace(".", ". ").split()
    wanted = [w for w in wanted if is_move(w)]
    reached = [g for g in from_speed if g.moves[: len(wanted)] == wanted and (g.result == "lost" or not lost)]
    used = reached[:NEWEST]
    summary = {
        "player": player,
        "their_colour": colour,
        "read": {
            "games_in_file": len(games),
            "their_games": len(played) + sum(left_out.values()),
            "with_this_colour": len(of_colour),
            "used": len(used),
            "from": min((g.date() for g in used), default=None),
            "to": max((g.date() for g in used), default=None),
            "speeds": dict(Counter(g.speed for g in used).most_common()),
            "after": after or None,
            "only_games_they_lost": lost,
        },
        "left_out": {
            **left_out,
            "other_speeds": dict(other_speeds.most_common()),
            "older_than_newest_200": len(reached) - len(used),
            "other_first_moves": len(from_speed) - len(reached),
        },
        "few_games": len(used) < FEW_GAMES,
        "first_moves": [],
        "lines": [],
        "weak_spot": None,
        "form": form_of(at_speed) if at_speed else None,
        "positions": [],
    }
    if not used:
        return summary, []
    floor = max(MIN_LINE_GAMES, math.ceil(len(used) * LINE_SHARE))
    recent = used[:RECENT]
    found = sorted(((m, g) for m, g in leaves(used, wanted, floor) if m), key=lambda line: -len(line[1]))
    lines = [line_of(m, g, recent) for m, g in found]
    top = lines[:TOP_LINES]
    weakest = min(lines, key=lambda line: line["score_percent"], default=None)
    weak_spot = weakest if weakest and weakest["score_percent"] < WEAK_SCORE and weakest not in top else None
    summary["first_moves"] = first_moves(used, len(wanted))
    summary["lines"] = top
    summary["weak_spot"] = weak_spot
    summary["positions"] = [line["position"] for line in top + ([weak_spot] if weak_spot else [])]
    return summary, tree_of(used, 0)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pgn", help="the PGN file of the player's games")
    parser.add_argument("--player", required=True, help="their name as the PGN writes it")
    parser.add_argument("--against", required=True, choices=("white", "black"), help="the colour the person preparing will have")
    parser.add_argument("--after", default="", help='read only games that open with these moves, such as "1. e4"')
    parser.add_argument("--speed", action="append", default=[], help="a speed to read, more than once if you like, or all")
    parser.add_argument("--lost", action="store_true", help="read only the games they lost")
    parser.add_argument("--tree", help="also write the whole tree of what they played to this file, for a Study")
    args = parser.parse_args()
    if not Path(args.pgn).is_file():
        sys.exit(f"There's no file at {args.pgn}.")
    summary, tree = report(read_pgn(args.pgn), args.player, args.against, args.after, args.speed, args.lost)
    if args.tree:
        Path(args.tree).parent.mkdir(parents=True, exist_ok=True)
        Path(args.tree).write_text(json.dumps(tree, ensure_ascii=False), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
