---
name: chessdrive-patterns
description: Find the mistakes a chess player keeps making across their last 30 games with ChessDrive. Use when someone asks "what do I keep getting wrong", "find the mistakes I keep making" or "what are my bad habits", or when a coach asks what a student should work on. The engine marks the player's mistakes in every game, Embed groups them with code, the top groups are named in plain words, and each name that fits shows three examples from different games, each explained, on a Study. Runs in an agent that runs code, such as Claude Code, Codex or Cursor, and in Claude's chat app on a paid plan.
---

# Patterns

You find what a player keeps getting wrong. The engine marks their mistakes, code groups them, Queen names the groups, and Knight checks each name against its examples and explains them, so nothing rests on your own reading of the board. It needs somewhere to run code, and is built on the `chessdrive-vectors` Skill beside this one. Read its `references/calls.md` before your first call: it has who judges what, how to make calls at once and what to do when one is refused.

Three limits hold in everything you write:

- **Judge positions in words.** Never write centipawns, a score such as `+1.3`, a win percentage or a closeness score.
- **Name only moves the tools gave you:** a move of the game, a `best`, an `allowed`, or a `generate` answer's `lines`. Copy them exactly.
- **A group is a lead, not a proof.** A group holds mistakes that look alike on the board and in what the engine's lines say they allowed, and a name is the chess model's reading of five of them. Say how many of the five Knight found show it, and never say every mistake in a group is that kind.

## If they ask what this does, or give too little

Say this, and wait: "Give me a PGN file of your last 30 games and your username on the site, and I'll find the kinds of mistake you make most, each with three examples on a board. It takes about 5 minutes, or 8 on Free. No file? Tell me your site and username, and I'll fetch them."

## What you need

This builds on `<this Skill's folder>/../chessdrive-vectors/`, where `<this Skill's folder>` is the folder this file is in, which your app gave you, so don't search for it. Run every command from the person's own folder, by the scripts' full paths. If that folder isn't there, only part of the Plugin was installed: ask them to add the whole Plugin from https://platform.chessdrive.io/skills, and stop.

Before anything else, read `<this Skill's folder>/../chessdrive-vectors/references/set-up.md` and do what it says. It checks each of these and walks the person through whatever is missing, one step at a time. This Skill needs somewhere to run code, the CLI at 0.6.0 or later, signed in, and Python with NumPy. Every call goes through the CLI, so it needs no Connector.

## Step 1: Get the games

You need about 30 of the player's games in a PGN file, and their name as the file writes it, which is in the `White` and `Black` tags.

**No file?** Read `<this Skill's folder>/../chessdrive-vectors/references/get-games.md` and do what it says: with a username, fetch their games with its script, and otherwise give the person its steps for their site as they're written, never from memory. It covers Lichess, chess.com and ChessBase. Never call `search`, and don't bring it up: it can't find a player's games.

Fewer than 30 games works, with fewer mistakes to group. Tell them 30 games take about 5 minutes, on Free too. Name the cost only if they ask: about 45 cents.

## Step 2: Mark the mistakes

```bash
python3 <this Skill's folder>/../chessdrive-vectors/scripts/pgn.py games.pgn --player "<their name>" --newest 30 --out patterns/games.pgn
chessdrive engine --games patterns/games.pgn --out patterns/answers.jsonl
```

The first keeps their newest 30 games; if the name isn't in the file, it says which names are. The second reviews each game whole, about 10 seconds a game, as many at once as the Plan allows, so never run games one by one yourself. Give it a 10-minute timeout, or run it in the background and wait to be told it has finished, rather than checking on it. Stopped, the same command carries on and bills no game twice. It ends with how many games it analysed and refused. Name any refused game in your answer.

Then mark their mistakes with code. Write this example to `patterns/mark.py` and run `python3 patterns/mark.py "<their name>"`:

```python
import json, sys
player = sys.argv[1].casefold()  # their name as the PGN's White and Black tags write it
MARK = {"blunder": "??", "mistake": "?", "inaccuracy": "?!"}
def words(e):  # an evaluation from White's side, in words
    if e.get("mate") is not None:
        return "the game is over" if e["mate"] == 0 else ("White" if e["mate"] > 0 else "Black") + " is mating"
    cp = e.get("cp") or 0
    side = "White" if cp > 0 else "Black"
    return "about equal" if abs(cp) < 50 else side + " is " + ("a little better" if abs(cp) < 150 else "clearly better" if abs(cp) < 300 else "winning")
rows = [json.loads(line) for line in open("patterns/answers.jsonl", encoding="utf-8")]
played = lambda t: (t.get("UTCDate") or t.get("Date") or "", t.get("UTCTime") or t.get("Time") or "")
side = lambda t: next((c for c in ("White", "Black") if t.get(c, "").casefold() == player), None)
games = sorted((r for r in rows if r["status"] == "ok" and side(r["tags"])), key=lambda r: played(r["tags"]))  # oldest first, so the groups stay as they are
found = []
for n, g in enumerate(games):
    colour = side(g["tags"])
    for at, m in enumerate(g["moves"]):
        keep = m["verdict"] in ("mistake", "blunder")
        if keep and m["color"] == colour.lower():
            after = g["moves"][at + 1] if at + 1 < len(g["moves"]) else {}  # the reply's best Line: what the mistake allowed
            found.append({"game": n, "ply": m["ply"], "move": f"{m['move_number']}{'.' if colour == 'White' else '...'}{m['move']['san']}{MARK[m['verdict']]}",
                "verdict": m["verdict"], "colour": colour, "opponent": g["tags"].get("Black" if colour == "White" else "White", ""), "date": played(g["tags"])[0],
                "site": g["tags"].get("Site", ""), "best": [x["san"] for x in m.get("best_line") or []], "allowed": [x["san"] for x in after.get("best_line") or []],
                "before": words(m["eval_before"]), "after": words(m["eval_after"]), "lost": m["win_chance_lost"], "fen": m["fen"], "pgn": g["pgn"]})
json.dump([{"type": "position", "pgn": f["pgn"], "ply": f["ply"] + 1} for f in found], open("patterns/items.json", "w", encoding="utf-8"))
open("patterns/mistakes.jsonl", "w", encoding="utf-8").writelines(json.dumps(f, ensure_ascii=False) + "\n" for f in found)
newest = games[-1]["tags"] if games else {}
print(json.dumps({"games": len(games), "rating": newest.get(f"{side(newest)}Elo"),
    "refused": [r["game"] for r in rows if r["status"] != "ok"], "positions": len(found), "blunders": sum(f["verdict"] == "blunder" for f in found)}))
```

It's an example: change it to fit what they ask, and say in your answer what you changed. For "count my inaccuracies too", make the `keep` line `keep = m["verdict"] in ("inaccuracy", "mistake", "blunder")`. For "only endgames", add `and sum(p in "QRBNqrbn" for p in m["fen"].split()[0]) <= 4` to it. Leave the rest as it is: Steps 3 and 5 read every field, and the sort keeps the groups the same from run to run.

It prints `games`, `rating`, `refused`, `positions` and `blunders`. If `positions` is under 6, there's too little to group: say so, and offer a review of their worst game instead.

## Step 3: Group them

```bash
python3 <this Skill's folder>/scripts/describe.py patterns --rating <their rating>
chessdrive embed --input patterns/items.json --out patterns/boards.npy
chessdrive embed --input patterns/texts.json --out patterns/texts.npy
python3 <this Skill's folder>/scripts/groups.py patterns
```

The first asks Knight for one line on each mistake, what the move gave the other side as the engine's Lines show it, eight mistakes a call and every call at once: about a minute. A line that names a move it wasn't given, or a number, is asked again, then built from the Lines alone, and the lines are kept, so running it again bills nothing. It prints `described`, `from_knight`, `from_lines` and `knight_calls`. Then Embed takes the position after each mistake, and each line, and `groups.py` joins the two, so a group holds mistakes that look alike on the board and in what they allowed. Give it a 5-minute timeout, or run it in the background.

`groups.py` prints the top three groups, largest first, then `positions`, `games` and `repeated_groups`. Each group has its `size`, the `games` it spans and five `examples` from different games, with `move`, written with its mark, `verdict`, `colour`, `opponent`, `date`, `site`, `best`, `allowed`, `before`, `after`, `fen`, `pgn`, `ply` and `text`, Knight's line on it. `allowed` is the engine's best play for the other side after the move. `ply` is the position the move was played from.

A group holds at least 3 mistakes from at least 3 games. A player with few mistakes gets fewer groups, or none: say so plainly, and never pad the list. The groups also go to `patterns/groups.json`, for Step 5.

## Step 4: Name the groups

Ask Queen once per group, all at once with `ask.py` as `calls.md` says, each with the first example's `pgn` and `ply`, `"id"` the group's number, and this `system`, filling in the player's rating.

```text
You help a chess player of about {rating} see what their mistakes have in common. You get a few of their mistakes.
In a phrase of at most eight plain words, name what links at least two of them, as concretely as the moves allow, such as "Taking first and miscounting the exchange", "Moving the piece that guarded another" or "Slow pawn moves while your opponent attacks". Never answer with only "forcing moves", "tactics" or "threats", which fit every mistake.
Then say in one sentence what to check before moving. Use only the moves you are given, and no numbers. If nothing links even two of them, say "No clear idea".
```

Its `message`, with a line for each example:

```text
These mistakes were grouped as alike:
1. FEN {fen}. {colour} played {move}, a {verdict}. Better was {best, its first 4 moves}. It allowed {allowed, its first 3 moves}. Before: {before}; after: {after}. In short: {text}
What do they have in common?
```

A group with no answer, `null`, is named "No clear idea". Two groups with the same name are one idea: keep the larger, and count the other as left out. Then write `patterns/names.json`, one object for each group, "No clear idea" included, with the reply's name and its sentence on what to check before moving, word for word:

```json
[{"group": 1, "name": "Moving the piece that guarded another", "check": "Before you move a piece, ask what it was guarding."}]
```

## Step 5: Explain them, and build the Study

```bash
python3 <this Skill's folder>/scripts/study.py patterns --rating <their rating>
```

It asks Knight whether each of a group's five examples shows its name, keeps the group if at least **3 of the 5** do, takes the first 3 that do, each from a different game, and asks Knight what each move allowed, from the engine's Lines, and how that shows the group's name where the Lines do, 6 calls at once. A reply that names a move it wasn't given, or a number, is asked again, then labelled and given the engine's Line. It then builds the Study, `patterns/your-mistakes.html`, in the `chessdrive-study` Skill's frame: the "Ask about this position" card, the Board, and beside it the groups by name with their examples, which put each mistake on the Board, facing their side, with its move in red and the better one in green, to try moves from and come back. Stopped, the same command bills no call twice.

It prints a line for each group kept, with `name`, `check`, `size`, `games`, `fit`, `checked` and its 3 `examples`, each with `move`, `opponent`, `date`, `site`, `better`, `allowed` and `why`, Knight's line. Then the totals: `kept`, `left_out` and `study`, the page's full path. Open it for the person with `open`, `xdg-open` or `start`. Don't build or change the page by hand.

If `kept` is 0, no name held and there's no page: say so plainly, with how many groups were left out, name no habit, and offer a review of their worst game instead. An example whose `from_knight` is false says the chess model didn't explain it: say how many. Otherwise, if `study` is `null`, the `chessdrive-study` Skill isn't there: make each example's move a link to its position on the Board, as Board links in `<this Skill's folder>/../chessdrive-vectors/references/calls.md` says, with no new call.

## Step 6: Answer

```markdown
**Your most common mistake is moving a piece that was guarding another.** The engine marked 96 mistakes across your last 30 games, and these kinds came up most.

The Study's full path as a link, and how to use and share it, in one line.

### 1. Moving the piece that guarded another
24 mistakes in 14 games, and 4 of the 5 I checked show this. What to check before you move, in one sentence.

- 18.Qe1?? against <opponent>: <its why>. 18.Qe2 was better.
- <the second example, the same way>
- <the third example, the same way>

### 2. ...

One more group was left out, as fewer than three of its five examples showed one idea.

**How far to trust this:** a group holds mistakes that look alike on the board and in what the engine's lines say they allowed, and each name comes from five of them, so not every mistake in a group is that kind.

Want a drill of group 1?
```

Start with the bold answer, with nothing before it. Give each group its three examples, as `study.py` printed them, with `why` as it stands, and say how many groups were left out when any were. Write each `move` as the scripts give it, with its mark, and write other moves with no mark. Number a move of `allowed` as the one after `move`, and name only the first few, as they are the engine's play and not the game's. Name the files, by name and never by a sandbox path, and say later questions about them are free, just above the last line. In Claude's chat app, say that lasts as long as this chat. That line offers one follow-up: a drill PGN of a group's mistakes for a Lichess study.

## Follow-ups

- **A question about a position** they saw: as `calls.md` says. Every mistake the engine marked is a line of `patterns/mistakes.jsonl`, with its `pgn`, `ply`, `best` and `allowed`, not only the examples you showed: look a move up there by `opponent` and `move` before you say it wasn't marked. `best` and `allowed` are the engine's Lines from a mistake's `fen` and from the position after its `move`, so a question about either needs no `engine` call.
- **"Turn group 1 into a drill":** run `python3 <this Skill's folder>/scripts/groups.py patterns --examples 10`, which shows more of the same groups, and make one game per mistake, in one PGN block, each with `[SetUp "1"]`, `[FEN "<fen>"]` and `[Result "*"]`. Its moves are `best`, after a first comment such as `{ You played 14...Qd7 here. Find better. }`.

## Rules

- Name no price unless they ask, including what this run cost.
- Every call is billed to the person's ChessDrive Account. Reuse `patterns/`: a new question about the same games costs nothing more than the `engine` and `generate` calls it needs. A fresh run over the same games can mark a few different mistakes, as the engine's search varies, so the groups can shift; reusing the folder keeps them.
- The person's PGN files and `patterns/` stay where this code runs, apart from what each Engine and Embed call sends. That's their machine, or in Claude's chat app Claude's sandbox, which resets with each new chat.
- Never print or read vectors, and open `.npy` files only through the scripts. Knight's lines in `patterns/texts.json` are for grouping: quote `text` in an answer only as a group's examples, never as a list. If a vector does reach your output, leave it out of your answer and fix the code.
- Low closeness or a small group doesn't show a player never makes a mistake of some kind. Only say what the groups show, and never say something is absent.
- `daily_limit_reached` stops a run on Free: tell the person, and run the same command after midnight UTC or after they move to a paid Plan.
- Before you send, read your answer once for a number judging a position, a closeness score, a mark that isn't the move's `verdict`, a group without its three examples, a name that fits fewer than three of five, a price they didn't ask for, and anything the tools didn't say. Fix what you find.
