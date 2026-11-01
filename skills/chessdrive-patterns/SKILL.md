---
name: chessdrive-patterns
description: Find the mistakes a chess player keeps making across their last 30 games with ChessDrive. Use when someone asks "what do I keep getting wrong", "find the mistakes I keep making" or "what are my bad habits", or when a coach asks what a student should work on. The engine marks the player's mistakes in every game, Embed groups them on the person's machine, and the top three groups are named in plain words, each with a board. Needs an agent that runs code on the person's machine, such as Claude Code, Codex or Cursor.
---

# Patterns

You find what a player keeps getting wrong. The engine marks their mistakes, code groups them, and the chess model names the groups, so nothing rests on your own reading of the board. It needs code running on the person's machine and is built on the `chessdrive-vectors` Skill beside this one, whose scripts it calls from `../chessdrive-vectors/scripts/`.

Three limits hold in everything you write:

- **Judge positions in words.** Never write centipawns, a score such as `+1.3`, a win percentage or a closeness score.
- **Name only moves the tools gave you:** a move of the game, a `best`, an `allowed`, or a `generate` answer's `lines`. Copy them exactly.
- **A group is a lead, not a proof.** A group holds positions that look alike, and a name is the chess model's reading of five of them. Say how many of the five show it, and never say every mistake in a group is that kind.

## What you need

- **Code running on the person's machine.** If you can't run code there, as in Claude's chat app, tell the person this needs an agent that can, such as Claude Code (the terminal or the desktop app's Code tab), Codex or Cursor, and stop.
- **The `chessdrive` CLI, signed in.** If it's missing, ask the person to follow https://platform.chessdrive.io/docs/cli to install it and run `chessdrive login`. Signing in is theirs to do, so a key never passes through the chat. Check `chessdrive version` too: this needs 0.2.0 or later. If it's older, ask the person to run `chessdrive update`, or to install it again from that page if their CLI doesn't have `update`, and wait until they have.
- **Python 3.11 or later with NumPy.** Check with `python3 -c "import numpy"`. If it fails and `uv` is there, run the scripts with `uv run --with numpy python`; otherwise ask to run `python3 -m pip install numpy`.
- **The ChessDrive Connector,** for `generate`. If its tools aren't there, ask the person to connect ChessDrive on this plugin's Connectors tab. Without it, use the CLI as Step 4 says.

## Step 1: Get the games

You need about 30 of the player's games and their name as the PGN writes it.

- **A PGN file:** use it. Their name is in the `White` and `Black` tags.
- **A Handle:** ask which site if they didn't say, then call `search` with `{"player": {"handles": [{"platform": "lichess", "username": "<handle>"}]}, "limit": 30, "pgn": true}` and write each `game.pgn` to `games.pgn`, one after another. If `search` says it's coming soon, say finding games by Handle isn't open yet, and ask them to export their games to a PGN file from their site.

Fewer than 30 games works, with fewer mistakes to group. Tell them 30 games take about 10 minutes. If they ask what it costs: about 30 cents from a PGN file, or about 45 cents when the games come from a Handle.

## Step 2: Mark the mistakes

```bash
python3 scripts/mistakes.py games.pgn --player "<their name>" --folder patterns
```

It takes their newest 30 games and calls Engine once per game, about 10 seconds each. Give the call a 10-minute timeout, or run it in the background and wait to be told it has finished, rather than checking on it. Stopped, the same command carries on and bills no game twice. It prints a line per game, then the totals: `games`, `rating`, `refused`, `positions`, `blunders` and the costs so far. Name any `refused` game in your answer.

If the name isn't in the file, it says which names are. If `positions` is under 6, there's too little to group: say so, and offer a review of their worst game instead.

## Step 3: Group them

```bash
chessdrive embed --input patterns/items.json --out patterns/vectors.npy
python3 scripts/groups.py patterns
```

It prints the top three groups, largest first, then `positions`, `games` and `repeated_groups`. Each group has its `size`, the `games` it spans and five `examples` from different games, with `move`, written with its mark, `verdict`, `colour`, `opponent`, `date`, `site`, `best`, `allowed`, `before`, `after`, `fen`, `pgn` and `ply`. `allowed` is the engine's best play for the other side after the move. `ply` is the position the move was played from.

A group holds at least 3 mistakes from at least 2 games. A player with few mistakes gets fewer groups, or none: say so plainly, and never pad the list.

## Step 4: Name the groups

Call `generate` once per group, on the first example, with `model: "queen"`, `position: {"pgn": "<its pgn>", "ply": <its ply>}`, and this `system`, filling in the player's rating:

```text
You help a chess player of about {rating} see what their mistakes have in common. You get a few of their mistakes.
In a phrase of at most eight plain words, name what links at least two of them, as concretely as the moves allow, such as "Taking first and miscounting the exchange", "Moving the piece that guarded another" or "Slow pawn moves while your opponent attacks". Never answer with only "forcing moves", "tactics" or "threats", which fit every mistake.
Then say in one sentence what to check before moving. Use only the moves you are given, and no numbers. If nothing links even two of them, say "No clear idea".
```

Send one `user` message, with a line for each example:

```text
These mistakes were grouped as alike:
1. FEN {fen}. {colour} played {move}, a {verdict}. Better was {best, its first 4 moves}. It allowed {allowed, its first 3 moves}. Before: {before}; after: {after}.
What do they have in common?
```

Leave `max_tokens` out: Queen's thinking counts toward it, so a low cap cuts the reply short or loses it. If a call answers `plan_required`, make it and the rest on Knight, with `model: "knight"`, and say so in one line of your answer. If it answers `429 rate_limited`, wait for `Retry-After` and retry the same call. If it answers `upstream_unavailable`, make the same call once more. If that fails too, name the group from its examples alone, and add no note about it. With no Connector, pipe the `pgn` to `chessdrive generate --model queen --pgn - --ply <ply> --no-stream --system "<system>" "<message>"`.

**Check each name against its five examples.** Go through them one at a time: read `move`, `best` and `allowed`, and decide whether that example's moves show the name. The count is what you found for that group, and groups differ. Keep a name that fits at least two, and leave out the rest, saying how many you left out. Add no tactic of your own. Two groups with the same name are one idea, so say so rather than listing it twice.

## Step 5: Show a board

Build the person a Study with the `chessdrive-study` Skill beside this one: a page in `patterns/` with a heading for each group you kept and, under it, the example its name fits best on a Board, at its `pgn` and `ply`, facing their `colour`, in `mode: "view"`. Read its `references/board.md`, and take the moves from the scripts' output. It makes no ChessDrive calls and needs no Connector.

If that Skill isn't there, make one call to the Connector's `engine` tool with `{"engine": "stockfish", "positions": [{"fen": "<its fen>"}], "depth": 10}`, one entry per example, and make each example's move a link to its `board_url`. With no Connector either, point to the example by its game and move.

## Step 6: Answer

```markdown
**Your most common mistake is moving a piece that was guarding another.** The engine marked 96 mistakes across your last 30 games, and three kinds came up most.

How to open the Study, in one line.

### 1. Moving the piece that guarded another
24 mistakes in 14 games, and {the number that fit} of the five I checked show this. What to check before you move, in one sentence.

18.Qe1?? against <opponent> allowed 18...Rxd3, and 18.Qe2 was better.

### 2. ...

**How far to trust this:** a group holds mistakes that look alike, and each name comes from five of them, so not every mistake in a group is that kind.

Want a drill of group 1?
```

Give each group one example, the one on its board. Write each `move` as the scripts give it, with its mark, and write other moves with no mark. Number a move of `allowed` as the one after `move`, and name only the first few, as they are the engine's play and not the game's. Name the files and say later questions about them are free, just above the last line. That line offers one follow-up: a drill PGN of a group's mistakes for a Lichess study.

## A follow-up

**"Turn group 1 into a drill":** run `python3 scripts/groups.py patterns --examples 10`, which shows more of the same groups, and make one game per mistake, in one PGN block, each with `[SetUp "1"]`, `[FEN "<fen>"]` and `[Result "*"]`. Its moves are `best`, after a first comment such as `{ You played 14...Qd7 here. Find better. }`.

## Rules

- Name no price unless they ask, including what this run cost.
- Every call is billed to the person's ChessDrive Account. Reuse `patterns/`: a new question about the same games costs nothing more than any `generate` it needs. A fresh run over the same games can mark a few different mistakes, as the engine's search varies, so the groups can shift; reusing the folder keeps them.
- The person's PGN files stay on their machine, apart from what each Engine and Embed call sends.
- Never print or read vectors, and open `.npy` files only through the scripts. If a vector does reach your output, leave it out of your answer and fix the code.
- Low closeness or a small group doesn't show a player never makes a mistake of some kind. Only say what the groups show, and never say something is absent.
- `daily_limit_reached` stops a run on Free: tell the person, and run the same command after midnight UTC or after they move to a paid Plan.
- When a tool says the Balance is empty, pass on its message and its link to Pricing, give what you already have, and stop.
- Before you send, read your answer once for a number judging a position, a closeness score, a mark that isn't the move's `verdict`, a group with more than one example, a price they didn't ask for, and anything the tools didn't say. Fix what you find.
