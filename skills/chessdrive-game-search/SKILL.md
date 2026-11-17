---
name: chessdrive-game-search
description: Find examples of a chess idea across someone's own PGN files, in plain English, with ChessDrive. Use when someone wants every back rank mate in their games, positions for a lesson on a tactic, examples for an article or video, or moments like a position they show you, from a game collection they have as PGN. Embeds every position to a file once, finds the closest moments with code, checks them with the engine, and returns a page of boards and a PGN of examples. Later questions read the same file. Runs in an agent that runs code, such as Claude Code, Codex or Cursor, and in Claude's chat app on a paid plan.
---

# Game search

**Unpack the scripts first.** This plugin holds its Python scripts as text, one `.py.md` file each. Wherever you can run code, before anything else read `chessdrive-vectors/references/unpack.md`, in the folder beside the one this file is in, and run its one command, which prints a folder. From then on `<this Skill's folder>` is this Skill's folder inside the printed one, `<the printed folder>/chessdrive-game-search`: read every file and run every script from there. Where you can't run code, skip this, and `<this Skill's folder>` is the folder this file is in.

You find moments that show an idea across a person's PGN files, check them with the engine, and hand back a PGN of examples. You work from the `chessdrive-vectors` Skill beside this one: its rules hold here, and Your app gave you the folder this file is in, so don't search for it. In the commands below `<vectors>` is `<this Skill's folder>/../chessdrive-vectors/scripts`, and `<here>` is `<this Skill's folder>/scripts`. Vectors stay in the file. You read rows, counts and moves.

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
| Free | about 9,000 | 2 min | 9 min | over 4 days, at 128K a day |
| Hobby | about 18,000 | 1 min | 5 min | 22 min |
| Pro | about 35,000 | under a minute | 3 min | 12 min |

Hobby and Pro get their figures from the CLI at 0.7.0 or later, which sends several calls at once; `chessdrive version` shows it. With an older CLI they run about 10,000 a minute: 2 min for 200 games, 8 for 1,000, 40 for 5,000.

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

**The number they ask for is the most to show, not a target.** Go down the list in order until you have it, 10 examples if they named no number. A small file may hold fewer: if the list runs out, answer with what you have, as in "I found 2", and never go through the games to reach the number. Take the next hits of the list in batches of up to 100, with `--top` raised, and stop at about 300 positions for one question, or at the end of the list, then say what you have, even if it's fewer than they asked for. That takes a few minutes, as Knight goes through each hit's checks.

**First, the idea's checks.** Read `<this Skill's folder>/references/ideas.md`. If the idea is there, copy its checks as written to a file, such as `checks/back-rank-mate.txt`. If not, write its checks as that file says, and give them to the person in your answer. A hit is the moment after the move at its `ply`: a mate's ply is the move with `#`.

For each batch:

1. **The engine, in one command.** Write a line per hit to a file, `{"game": <game>, "ply": <ply>, "pgn": "<pgn>"}`, and run:

   ```bash
   chessdrive engine --positions checks/back-rank-mate.jsonl --depth 10 --out checks/back-rank-mate-results.jsonl
   ```

   Line 7 of the results answers line 7 of the list, with `status`, `fen`, `best_move` and `lines`. A mate comes back as `game_over`, which is right: it has no Line to show. A question with a new list gets a new pair of files. Never call the engine once per position, and never run one on this machine: every engine answer comes from ChessDrive.
2. **Knight, all at once, with one command:**

   ```bash
   python3 <here>/judge.py checks/back-rank-mate.jsonl --idea "<the idea in the person's words>" --checks checks/back-rank-mate.txt --engine checks/back-rank-mate-results.jsonl --out checks/back-rank-mate-judged.jsonl
   ```

   For each hit, Knight reads the moves around it, the board after the move in words and the checks, and goes through them before its verdict. Each hit is asked twice, and kept only when both answers say yes. Line 7 of `--out` answers line 7 of the list, with `kept`, Knight's `note` on a kept hit, and `why` and any `error` on the rest. Its last printed line is the totals, with every hit Knight didn't answer and the error. Run the same command again after a stop: it bills no call already answered.
3. **Keep a hit when `kept` is true, and only then,** with no second reading of your own, at its `move`, with its `note` as the hit's note, word for word. Say how many hits Knight didn't answer and why, from the totals' `unanswered`, as in "Knight didn't answer 2 of the hits (`upstream_unavailable`), so they aren't in the list."

Judge positions in words, never with an evaluation number, and name only moves from the game or from a tool. Count the hits you read and the ones Knight kept, and report those counts as they are.

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
**I found 4 back rank mates in your games.** I read 20 hits, and Knight kept 4 of them.

The checks, in one line, only if you wrote them yourself. Any hits Knight didn't answer, how many and why, in one line.

The Study's full path as a link, and how to use and share it, in one line.

### Carlsen vs Anand, 28.Rc8#
Your note on it, in one or two sentences.

### ...

The PGN file and the vector file, with its size in positions: paths in a coding agent, names alone in Claude's chat app.
```

Later questions read that file, so finish by saying so in one short line: the search takes seconds, and the checks take as long as you do. If they ask what one costs: a new phrase is one Embed item, a position already in the file is no Embed call at all, 100 engine checks are about a fifth of a cent, and Knight's checks are about a tenth of a cent a hit, a little more for each hit it says yes to, so a question of 100 hits costs about 15 cents.

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
