---
name: chessdrive-game-search
description: Find examples of a chess idea across someone's own PGN files, in plain English, with ChessDrive. Use when someone wants every back rank mate in their games, positions for a lesson on a tactic, examples for an article or video, or moments like a position they show you, from a game collection they have as PGN. Embeds every position to a file once, finds the closest moments with code, checks them with the engine, and returns a page of boards and a PGN of examples. Later questions read the same file. Runs in an agent that runs code, such as Claude Code, Codex or Cursor, and in Claude's chat app on a paid plan.
---

# Game search

You find moments that show an idea across a person's PGN files, check them with the engine, and hand back a PGN of examples. You work from the `chessdrive-vectors` Skill beside this one: its rules hold here, and `<this Skill's folder>` is the folder this file is in, which your app gave you, so don't search for it. In the commands below `<vectors>` is `<this Skill's folder>/../chessdrive-vectors/scripts`, and `<here>` is `<this Skill's folder>/scripts`. Vectors stay in the file. You read rows, counts and moves.

## If they ask what this does, or give too little

Say this, and wait: "Give me your PGN files and an idea in a few words, such as knight forks, and I'll find examples, check them with the engine, and give you a page of boards and a PGN. The first run reads every position once, and later questions are quick. No file? Tell me your site and username, and I'll fetch your games."

## What you need

This builds on `<this Skill's folder>/../chessdrive-vectors/`. If that folder isn't there, only part of the Plugin was installed: ask them to add the whole Plugin from https://platform.chessdrive.io/skills, and stop.

Before anything else, read `<this Skill's folder>/../chessdrive-vectors/references/set-up.md` and do what it says. It checks each of these and walks the person through whatever is missing, one step at a time. This Skill needs somewhere to run code, the CLI at 0.6.0 or later, signed in, and Python with NumPy. In Claude's chat app, read "the person's machine" in `chessdrive-vectors` as Claude's sandbox.

Every call here goes through the CLI, as `<this Skill's folder>/../chessdrive-vectors/references/calls.md` says, so it needs no Connector.

## Step 1: Count the positions

Ask which PGN files to search. If a `.npy` of them is already there, go to Step 3: the person has paid for it. **No file?** Read `<this Skill's folder>/../chessdrive-vectors/references/get-games.md` and do what it says: with a username, fetch their games with its script, using `--max 300` as a start, and otherwise give the person its steps for their site as they're written, never from memory. It covers Lichess, chess.com and ChessBase.

This counts the positions and the cost exactly, with no call and no charge:

```bash
python3 <vectors>/vectorfile.py games.pgn more-games.pgn
```

Every position of every game is one item, at 4 cents per 1K. Tell the person the games and the time, then go ahead. **Over 25,000 positions, about 300 games, stop first:** that run costs over a dollar, so tell them the games, the positions, the cost and the time, and wait for their yes. Below that, give the cost only if they ask.

The time depends on their Plan, which `chessdrive balance` shows:

| Plan | Positions a minute | 200 games | 1,000 games | 5,000 games |
|---|---|---|---|---|
| Free | 300 | 53 min | 4.4 h | 22 h, over 4 days |
| Hobby | 1,000 | 16 min | 80 min | 6.7 h |
| Pro | about 2,000 | 8 min | 40 min | 3.3 h |

A game is about 80 positions. Free stops at 500 calls a day, about 128K positions, so the rest waits for the next day, and its Trial credits cover about 3,000 games.

## Step 2: Embed once

Run this in the background, from the folder that holds the PGN files, and keep that folder:

```bash
chessdrive embed --pgn games.pgn --pgn more-games.pgn --out games.npy
```

Tell the person they can leave it running. A stopped run costs nothing: the same command, from the same folder, carries on from the rows written and bills only the rest. You're done when it reports every item written.

To add a file later, give the same command with the new `--pgn` last. It keeps the rows it has and embeds only the new games. A file given in another order is refused, as the rows no longer match.

Everything after this reads `games.npy`, so never embed the collection again.

## Step 3: Find the moments

**Search with the name of the idea, in two to five words.** A long sentence ranks the same examples far lower, so when the person writes a paragraph, take the idea's chess name out of it. Tactical ideas work best: mates, forks, pins, sacrifices. If the first wording finds little, try another name for the idea.

**Some ideas are in the notation itself,** so don't search for them by meaning. A promotion is `=` in a move, an underpromotion `=N`, `=B` or `=R`, a mate `#` and a check `+`. Read those from the PGN text with a short script: it's free, exact and complete. Use vectors for what the notation doesn't say.

Embed the words to a file of their own, named for them, and reuse that file if the idea comes back:

```bash
chessdrive embed --text "back rank mate" --out queries/back-rank-mate.npy
python3 <vectors>/compare.py games.npy --query queries/back-rank-mate.npy --per-game 1 --top 20
```

**From a position in the file,** no Embed call is needed. Game counts from 0 and ply is half-moves from the start, as in `chessdrive-vectors`:

```bash
python3 <vectors>/compare.py games.npy --game 3 --ply 24 --other-games --per-game 1 --top 20
```

Use this to ask for more once you have a good example: the moment you confirmed is a better question than the words were.

**From a position elsewhere,** embed it to `queries/` as `chessdrive-vectors` shows, with its game if you have the game. A bare FEN needs `--mixed` and gives rougher matches, so tell the person.

## Step 4: Check every hit you keep

The list holds the closest moments, whether or not they show the idea. Knight says which do, never your own reading of the board, as `<this Skill's folder>/../chessdrive-vectors/references/calls.md` says.

**The number they ask for is the most to show, not a target.** Go down the list in order until you have it, 10 examples if they named no number. A small file may hold fewer: if the list runs out, answer with what you have, as in "I found 2", and never go through the games to reach the number. Take the next hits of the list in batches of up to 100, with `--top` raised, and stop at about 500 positions for one question, or at the end of the list, then say what you have, even if it's fewer than they asked for. That is about a cent and under a minute.

For each batch:

1. **The engine, in one command.** Write a line per hit to a file, `{"pgn": "<pgn>", "ply": <ply>}`, and run:

   ```bash
   chessdrive engine --positions checks/back-rank-mate.jsonl --depth 10 --out checks/back-rank-mate-results.jsonl
   ```

   Line 7 of the results answers line 7 of the list, with `status`, `fen`, `best_move` and `lines`. A position with no legal moves comes back as `game_over`, so for a mate send the ply before it. A question with a new list gets a new pair of files. Never call the engine once per position, and never run one on this machine: every engine answer comes from ChessDrive.
2. **Knight, all at once.** One Knight call a hit with `ask.py`, `"id"` its game and ply, on its `pgn` and `ply`, with this `system`, and a `message` of the game's moves from four before `ply` to four after it, numbered, the engine's first Line, and `Does this show "<the idea in the person's words>"?`:

   ```text
   You check whether a moment of a chess game shows an idea. Answer "yes" or "no" first. On yes, name the move where it happens, and say in one sentence what happens there: the piece that moves, what it hits and what it wins. If only the engine's Line has it, say the player missed it. Use only the moves you are given.
   ```

3. **Keep a hit on Knight's yes, and only then,** with no second reading of your own, at the move it names, found in the `pgn` with code, with its sentence as the hit's note.

Judge positions in words, never with an evaluation number, and name only moves from the game or from a tool. Count the hits you read, the ones the engine checked and the ones Knight kept, and report those counts as they are.

**Few hits never prove an idea is absent.** The list is nearest neighbours: it can miss real examples, and scores say nothing about whether one exists. Say "I found 4", never "there are only 4" or "your games have no pins". If the person needs every example, tell them this finds good ones, not all of them. A `score` only orders the hits of one search, and for words it's about 0.3 to 0.5 even for the best. Leave it out of your answer.

## Step 5: Hand back the examples

Write the examples you kept to `picks.json`, in the list's order, each with its moment and Knight's sentence as its note. Add `"source"` as well if the run had several PGN files:

```json
[{"game": 29, "ply": 55, "note": "28.Rc8# mates on the back rank: the pawns on f7, g7 and h7 box in the king."}]
```

```bash
python3 <here>/examples.py games.npy picks.json --out back-rank-mates.pgn --title "Back rank mate"
```

Each example is its whole game with your note at the moment. The file opens as a Lichess study: in a study, New chapter, PGN, paste the file. Each game becomes a chapter, up to 64 in a study. Lichess's single-game import isn't the place for it, as it reads only the first game of a paste.

Then build the person a Study with the `chessdrive-study` Skill beside this one: a page in the frame without `data-moves`, with one Board and, in its panel, a `.cd-list` of the examples with their notes. Clicking an example puts it on the Board, at its `pgn` and `ply`, in `mode: "play-both"` with its way back. Read `frame.md` and `board.md`, Trying moves included, in `<this Skill's folder>/../chessdrive-study/references/`, and run its `../scripts/check.py <the page>` until it prints `ok`. Open the page for the person with `open`, `xdg-open` or `start`. It makes no ChessDrive calls and needs no Connector. If that Skill isn't there, call the Connector's `engine` tool once with `positions` holding your best three as `{"fen": "<its fen>"}` and `depth: 10`, and make each one's move a link to its `board_url`, using its `show_board` tool for a mate. With no Connector either, point to each by its game and move.

Then answer in exactly this shape, with no table:

```markdown
**I found 4 back rank mates in your games.** I read 20 hits, and the engine checked 7.

The Study's full path as a link, and how to use and share it, in one line.

### Carlsen vs Anand, 28.Rc8#
Your note on it, in one or two sentences.

### ...

The PGN file and the vector file, with its size in positions: paths in a coding agent, names alone in Claude's chat app.
```

Later questions read that file, so finish by saying so in one short line: the search takes seconds, and the checks take as long as you do. If they ask what one costs: a new phrase is one Embed item, a position already in the file is no Embed call at all, and 100 engine checks are about a fifth of a cent, so a question costs about a cent at most.

**To explain an example,** ask Queen on the same `{pgn, ply}`, as `calls.md` says.

## Follow-ups

- **A question about a position** they saw: as `calls.md` says. A hit's row in the results file is the engine's answer for its position, so a question about it needs no `engine` call.

## When a call is refused

`chessdrive embed`, `chessdrive engine --positions` and `--games` handle `429 rate_limited` themselves: they wait and carry on. The rest is in `chessdrive-vectors`, and after you act the same command carries on from the rows written:

- `daily_limit_reached` stops a run on Free. Run the command again after midnight UTC, or after the person moves to a paid Plan.
- **One bad game** stops the run, naming the row, the game and the ply. Ask to remove that game from the file, then run the command again.

## Rules

- Name no price unless they ask, including what this run cost or what a later question costs, apart from the stop in Step 1.
- Before you send, check your answer against the shape in Step 5: the bold first line, a heading for each example, no table, and no price they didn't ask for.
- Every call is billed to the person's ChessDrive Account. Reuse the file for every question.
- The person's PGN files and `games.npy` stay where this code runs, apart from what each Embed and Engine call sends. That's their machine, or in Claude's chat app Claude's sandbox, which resets with each new chat, so a new chat embeds the games again.
- Open `.npy` files only through NumPy, in code that prints no array. If a vector does reach your output, leave it out of your answer and fix the code.
