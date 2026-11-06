---
name: chessdrive-vectors
description: Embed chess positions and texts with ChessDrive into a vector file on the person's machine, then answer with code that reads the file. Use when someone asks which positions are closest to a position, wants to find an idea in plain English across their own PGN files ("find back rank mates in my games"), wants a set of positions grouped by what they have in common, or mentions embeddings or vectors of chess positions. Runs in an agent that runs code, such as Claude Code, Codex or Cursor, and in Claude's chat app on a paid plan.
---

# Work with vectors

You turn chess positions and texts into vectors with ChessDrive Embed, then answer the person's question with code that reads them. Vectors stay in the file: code reads them, and you read what the code prints, which is rows, counts and scores. Compare and group are not API features. They are the scripts in `scripts/` beside this file, for you to run or adapt. Below, `<this Skill's folder>` is the folder this file is in, which your app gave you, so don't search for it. Run them from the person's own folder, by that full path.

## What you need

- **Somewhere to run code:** the person's machine, or in Claude's chat app on a paid plan, Claude's sandbox. There, read "the person's machine" below as that sandbox. The ChessDrive Connector has no `embed` tool.
- **The `chessdrive` CLI at 0.6.0 or later, signed in, or its local MCP tool `embed`.** If you have neither, read `references/set-up.md` and do what it says: it walks the person through what's missing, one step at a time, with Claude's chat app's own steps.
- **Python 3.11 or later with NumPy.** Check with `python3 -c "import numpy"`. If it fails and `uv` is there, run the scripts with `uv run --with numpy python`; otherwise ask to run `python3 -m pip install numpy`.

If they have no PGN file, read `references/get-games.md` and do what it says: with a username, fetch their games with its script, and otherwise give them its steps for their site as they're written, never from memory.

If they ask what this does, or give too little to start, say what you need in a line or two: their PGN files or the positions, and what they want to find or group.

## Step 1: Make the file

Count first. Embed is 4 cents per 1K items, and every position of a game is an item. For a PGN file, this gives the exact count and cost, with no call and no charge:

```bash
python3 <this Skill's folder>/scripts/vectorfile.py games.pgn
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
python3 <this Skill's folder>/scripts/compare.py games.npy --game 3 --ply 24 --other-games --per-game 1
```

**Closest to a position from elsewhere, or to a text.** Embed the query to a file of its own, then compare. A new query needs a new file name, as a run won't overwrite other vectors.

```bash
chessdrive embed --pgn one-game.pgn --ply 24 --out queries/position-1.npy
chessdrive embed --text "a back rank mate" --out queries/back-rank.npy
python3 <this Skill's folder>/scripts/compare.py games.npy --query queries/back-rank.npy --per-game 1
```

Keep a text under about 300 characters, as a longer one answers `text_too_long`. Use `--per-game 1` when a file has many games, since neighbouring positions in a game look alike and would fill the list.

**Groups of similar items.** Group the positions the question is about, such as a player's mistakes, rather than every position of a file, where the groups would mostly be games.

```bash
python3 <this Skill's folder>/scripts/group.py mistakes.npy --examples 3
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
- **Knight checks the idea before you claim it,** as `references/calls.md` says, never your own reading of the board. The list holds the nearest items, whether or not any truly fits. Write the hits you'd show as lines of a file, `{"pgn": "<pgn>", "ply": <ply>}` or `{"fen": "<fen>"}`, and run `chessdrive engine --positions hits.jsonl --depth 10 --out hits-checked.jsonl`, which answers each with its `fen` and Lines, in the list's order. Then ask Knight about each, all at once with `ask.py`, with its position, its Line in the message and the question `Does this position show "<the idea>"? Answer yes or no first, then say where, in one sentence.` Keep a hit only on Knight's yes, with its sentence as its note, and say if none does.
- **Show the hits on boards.** Build a Study with the `chessdrive-study` Skill beside this one: a page in its frame (its `references/frame.md`), without `data-moves`, with one Board and, in its panel, a `.cd-list` of the hits. Clicking a hit puts it on the Board, at its `pgn` and `ply` or its `fen`, in `mode: "play-both"` with its way back (its `references/board.md`, Trying moves). It makes no ChessDrive calls. Run that Skill's `scripts/check.py <the page>` until it prints `ok`, then open the page for the person with `open`, `xdg-open` or `start`. If that Skill isn't there, make the hit's move a link to its position on the Board, as Board links in `references/calls.md` says.
- **To explain a hit,** ask Queen about the same position, as `references/calls.md` says.
- **Name only moves the game or a tool gave you.** The file holds no moves: the `pgn` and the tools do.

Answer in exactly this shape, with no table and no price. The second line is how to open the Study, if you built one:

```markdown
**The answer to their question, in one sentence.**

The Study's full path as a link, and how to use and share it, in one line.

### Rkido vs Megacount, 9...Qxa1
What the positions share, in one or two sentences.

### ...

The files, how many items they hold, and that later questions are free, in one line.
```

## When a call is refused

The CLI and the tool handle `429 rate_limited` themselves: they wait and carry on. For the rest, the same command carries on after you act:

- `daily_limit_reached` stops a run on Free. Tell the person, and run the command again after midnight UTC, or after they move to a paid Plan.
- **One bad game** stops the run, naming the row, the game and the ply. Ask to remove that game from the file, then run the command again: the rows before it still match.
- **Different items at the same `--out`** are refused, and the files are left alone. Use a new file name.
- `coming_soon`: Embed isn't open yet. Say so, and stop.

## Rules

- Name no price unless they ask, including what this run cost, apart from the stop in Step 1. The CLI prints the cost, so leave it out.
- Before you send, check your answer against the shape in Step 3: the bold first line, a heading for each hit, no table, and no price they didn't ask for.
- Every call is billed to the person's ChessDrive Account. Reuse the file for every question it can answer.
- The person's PGN files stay where this code runs, apart from what each Embed call sends.
- Open `.npy` files only through NumPy, in code that prints no array. If a vector does reach your output, leave it out of your answer and fix the code.
