---
name: chessdrive-vectors
description: Embed chess positions and texts with ChessDrive into a vector file on the person's machine, then answer with code that reads the file. Use when someone asks which positions are closest to a position, wants to find an idea in plain English across their own PGN files ("find back rank mates in my games"), wants a set of positions grouped by what they have in common, or mentions embeddings or vectors of chess positions. Needs an agent that runs code on the person's machine, such as Claude Code, Codex or Cursor.
---

# Work with vectors

You turn chess positions and texts into vectors with ChessDrive Embed, then answer the person's question with code that reads them. Vectors stay in the file: code reads them, and you read what the code prints, which is rows, counts and scores. Compare and group are not API features. They are the scripts in `scripts/` beside this file, for you to run or adapt.

## What you need

- **Code running on the person's machine.** If you can't run code there, as in Claude's chat app, tell the person this needs an agent that can, such as Claude Code (the terminal or the desktop app's Code tab), Codex or Cursor, and stop. The ChessDrive Connector has no `embed` tool.
- **The `chessdrive` CLI, signed in, or its local MCP tool `embed`.** If you have neither, ask the person to follow https://platform.chessdrive.io/docs/cli to install it and run `chessdrive login`. Signing in is theirs to do, so a key never passes through the chat. Check `chessdrive version` too: this needs 0.2.0 or later. If it's older, ask the person to run `chessdrive update`, or to install it again from that page if their CLI doesn't have `update`, and wait until they have.
- **Python 3.11 or later with NumPy.** Check with `python3 -c "import numpy"`. If it fails and `uv` is there, run the scripts with `uv run --with numpy python`; otherwise ask to run `python3 -m pip install numpy`.

## Step 1: Make the file

Count first. Embed is 4 cents per 1K items, and every position of a game is an item. For a PGN file, this gives the exact count and cost, with no call and no charge:

```bash
python3 scripts/vectorfile.py games.pgn
```

Over 25,000 items that run costs over a dollar, so stop first: tell the person the items, the cost and the time, and wait for their yes. Below that, say how long it will take and go ahead, giving the cost only if they ask. Time is about 300 items a minute on Free, 1,000 on Hobby and 2,000 on Pro.

Then write the vectors, always with `--out`, as a call without it prints them:

```bash
chessdrive embed --pgn games.pgn --out games.npy
```

- **Every position of a PGN file:** as above, from `--pgn` with no `--ply`. Give `--pgn` again for each further file.
- **Items you chose:** `--fen`, `--text`, `--pgn one-game.pgn --ply 24`, or `--input items.json`, a JSON list of items such as `{"type": "position", "pgn": "<the game>", "ply": 24}`.
- **With the local MCP tool instead:** `embed` from `chessdrive mcp` takes `model` (its ID from `list_models`), `out`, and `pgn_file` or `input`. Paths are absolute. It answers with the same summary.

It writes `games.npy`, the vectors, and `games.jsonl` beside it, one line per row saying what that row is. Keep them: every later question reads them, free and in seconds.

**A long run outlasts a tool call.** For more than a few thousand items, start it in the background. A stopped run costs nothing: the same command, from the same folder, carries on from the rows written and is never billed twice, and a file with the rows so far already loads. A command that finishes prints the items, the files and the cost; you're done with this step when it reports every item written.

## Step 2: Ask the file

**Closest to a position in the file.** Game counts from 0 in the file, so a game's number is how many `[Event ` lines come before it. Ply is half-moves from the start: after White's move `n` it is `2n - 1`, after Black's it is `2n`.

```bash
python3 scripts/compare.py games.npy --game 3 --ply 24 --other-games --per-game 1
```

**Closest to a position from elsewhere, or to a text.** Embed the query to a file of its own, then compare. A new query needs a new file name, as a run won't overwrite other vectors.

```bash
chessdrive embed --pgn one-game.pgn --ply 24 --out queries/position-1.npy
chessdrive embed --text "a back rank mate" --out queries/back-rank.npy
python3 scripts/compare.py games.npy --query queries/back-rank.npy --per-game 1
```

Keep a text under about 300 characters, as a longer one answers `text_too_long`. Use `--per-game 1` when a file has many games, since neighbouring positions in a game look alike and would fill the list.

**Groups of similar items.** Group the positions the question is about, such as a player's mistakes, rather than every position of a file, where the groups would mostly be games.

```bash
python3 scripts/group.py mistakes.npy --examples 3
```

Pass `--groups` if the person names a number. Asking again with more `--examples` shows more of the same groups.

**Anything else** is a short script of yours. Keep the printing to rows, counts and scores:

```python
import sys
sys.path.insert(0, "<this Skill's folder>/scripts")
from vectorfile import load, cosine, unit, show, Games
file = load("games.npy")  # .vectors, memory-mapped; .rows, what each one is; .model
```

### Rules for comparing

- **Vectors compare only within one Model version.** `compare.py` refuses two files of different Models: embed the query again with the file's Model.
- **Send positions the same way when comparing them.** A position with its game carries its earlier boards and a bare FEN doesn't, so the same board gives different vectors. A file made from PGN needs a query with its game, as in `--pgn one-game.pgn --ply 24`. If the person has only a FEN, embed it with `--fen`, pass `--mixed`, and tell them the matches are rougher for it.

## Step 3: Answer

Each hit is one line of JSON. A hit from a game has `source`, `game`, `ply`, and, when the PGN file is still there and unchanged, `white`, `black`, `date`, `result`, `move`, such as `14...Qd7`, and `pgn`. A `warning` means the game has changed or moved; say so rather than guess the moves.

- **Answer in chess terms:** the game, the move, and what the positions share. A `score` ranks hits within one run, closer being higher. It isn't a percentage, so give the order and leave the numbers out.
- **Check the idea before you claim it.** The list holds the nearest items, whether or not any truly fits. To look at a hit, call the Connector's `engine` tool with `engine: "stockfish"`, `position: {"pgn": "<pgn>", "ply": <ply>}` or `{"fen": "<fen>"}`, and `depth: 10`. Without the Connector, pipe the `pgn` to `chessdrive engine --pgn - --ply <ply> --depth 10 --json`: its last event gives the `fen` and the Lines. Engine is billed, so do this for the few hits you show.
- **Show the hits on boards.** Build a Study with the `chessdrive-study` Skill beside this one: a page with a Board for each hit, at its `pgn` and `ply` or its `fen`, in `mode: "view"`, with no ChessDrive calls. If that Skill isn't there, make the hit's move a link to the `board_url` from the `engine` answer. With neither, point to the hit by its game and move. Drop a hit that doesn't show what was asked, and say if none does.
- **To explain a hit,** call `generate` with `model: "queen"` on the same position. If it answers `plan_required`, fall back to Knight and say so in one line. If it answers `upstream_unavailable`, make the same call once more. If that fails too, give the engine's Line with no explanation, and add no note about it. Leave `max_tokens` out: Queen's thinking counts toward it, so a low cap cuts the reply short or loses it.
- **Name only moves the game or a tool gave you.** The file holds no moves: the `pgn` and the tools do.

Answer in exactly this shape, with no table and no price. The second line is how to open the Study, if you built one:

```markdown
**The answer to their question, in one sentence.**

How to open the Study, in one line.

### Rkido vs Megacount, 9...Qxa1
What the positions share, in one or two sentences.

### ...

The files, how many items they hold, and that later questions are free, in one line.
```

## When a call is refused

The CLI and the tool handle `429 rate_limited` themselves: they wait and carry on. For the rest, the same command carries on after you act:

- `daily_limit_reached` stops a run on Free. Tell the person, and run the command again after midnight UTC, or after they move to a paid Plan.
- **The Balance is empty:** pass on the message and its link to Pricing, and stop.
- **One bad game** stops the run, naming the row, the game and the ply. Ask to remove that game from the file, then run the command again: the rows before it still match.
- **Different items at the same `--out`** are refused, and the files are left alone. Use a new file name.
- `coming_soon`: Embed isn't open yet. Say so, and stop.

## Rules

- Name no price unless they ask, including what this run cost, apart from the stop in Step 1. The CLI prints the cost, so leave it out.
- Before you send, check your answer against the shape in Step 3: the bold first line, a heading for each hit, no table, and no price they didn't ask for.
- Every call is billed to the person's ChessDrive Account. Reuse the file for every question it can answer.
- The person's PGN files stay on their machine, apart from what each Embed call sends.
- Open `.npy` files only through NumPy, in code that prints no array. If a vector does reach your output, leave it out of your answer and fix the code.
