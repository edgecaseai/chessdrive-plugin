---
name: chessdrive-prep
description: Prepare someone for a game against one opponent with ChessDrive, from a PGN file of that opponent's games, or their public Lichess and chess.com games. Use when someone says "prep me for my game tomorrow against X", "what does this player play against 1.e4", "help me prepare for my next opponent", or a coach or parent prepares a student. A local script counts what the opponent plays by colour, the engine checks where their top lines end, and the chess model writes a game plan. Gives what they play against this colour, their recent form, a plan, and how many games it read and what the file leaves out, then builds a Study, a page to explore their lines. Runs in an agent that runs code, such as Claude Code, Codex or Cursor, and in Claude's chat app on a paid plan. Calls the ChessDrive Connector's engine, generate and show_board tools.
---

# Opponent prep

You prepare someone for a game against one opponent. A script counts what the opponent plays from a file of their games, the engine checks where their lines end, and the chess model writes the plan, so nothing rests on what you remember about any player or opening.

Four limits hold in everything you write:

- **Judge positions in words.** Never write centipawns, a score such as `+1.3`, or a win percentage for a position. A player's score over their games, such as "6 wins in 10", is a count and is fine.
- **Name only moves the tools gave you:** a move in the script's output, a move of an `engine` Line, or a move you sent to `generate`. Copy them exactly. Never add a move or a fact about the player from memory, even for a famous player.
- **Name an opening only where `opening` gives its name.** A chess.com file gives none, so write the moves, such as 1...c6, and not the name you know, even a loose one such as "Caro-Kann structure".
- **Games show tendencies, not a person.** Say "in the 143 games I read", and never "they always" or "their style". Never guess at their mood or why they lost. Say what the games leave out.

## If they ask what this does, or give too little

Say this, and wait: "Tell me your opponent's username and site, or give me a PGN file of their games, and the colour you'll have. I'll count what they play against that colour, check their main lines with the engine, and give you their form and a plan, on a page to explore. It takes a few minutes, plus the download for a big account."

## What you need

- **Somewhere to run code.** That's the person's machine in a coding agent, or Claude's sandbox in Claude's chat app. The scripts need Python 3.11 or later and nothing else, make no ChessDrive call and cost nothing. If you can't run code at all, tell the person this needs Claude's chat app on a paid plan, or an agent that runs code, such as Claude Code, Codex or Cursor, and stop.
- **The ChessDrive Connector,** for `engine` and `generate`. If its tools aren't there, read `<this Skill's folder>/../chessdrive-vectors/references/set-up.md` and do what its Connect section says.

## Step 1: Get what you need

Ask only for what's missing, once, in one message:

- **The opponent's games:** a PGN file, or their username on Lichess or chess.com. Their games are public, so no permission is needed. Use the path they gave, or the file attached to the chat. With only a real name, ask for their username.
- **The opponent's name as the PGN writes it,** with a file: their username on that site. If the name isn't in the file, the script says which names are, so ask which is theirs.
- **The person's colour.** If they don't know yet, run Steps 2 to 4 for both colours, with the top two lines of each.
- **The moves they usually open with,** if they'd like the prep to fit them. "Not sure" is a fine answer: carry on without.

**With a username, fetch their games yourself.** The script is in the `chessdrive-vectors` Skill beside this one. This Skill's folder is the one this file is in, which your app gave you, so don't search for it. If they didn't say which site, try both. First ask how long it takes, with no download:

```bash
python3 <this Skill's folder>/../chessdrive-vectors/scripts/fetch_games.py lichess <name> --how-long
```

Tell the person how long, in minutes, then start without waiting. If it's over 8 minutes, add `--max 8000` to the Lichess download, which keeps it to about 7, and say you read their newest 8,000:

```bash
python3 <this Skill's folder>/../chessdrive-vectors/scripts/fetch_games.py lichess <name> --out prep/lichess.pgn
python3 <this Skill's folder>/../chessdrive-vectors/scripts/fetch_games.py chesscom <name> --out prep/chesscom.pgn
```

Give each a timeout of 10 minutes, or run it in the background and wait to be told it has finished. Run one at a time, and reuse a file you already have. Don't fetch with your own tools, as both sites refuse a plain request. With games from both sites, join them with `cat prep/lichess.pgn prep/chesscom.pgn > prep/games.pgn` and run Step 2 once, on that file.

If the script can't reach the site or is refused, as in Claude's chat app, stop trying: no browser, Claude in Chrome or script in a page. Read `<this Skill's folder>/../chessdrive-vectors/references/get-games.md` and give the person its steps under Or the person exports them, with the opponent's username in the links and `?max=1000` for Lichess, on words such as "their last 1,000 games". Wait for the file.

## Step 2: Count what they play

```bash
python3 <this Skill's folder>/scripts/openings.py <file> --player "<name>" --against <the person's colour> --tree prep/tree.json
```

Run every command here from the person's own folder, with the script's full path, so `prep/` lands there and never in the Skill's folder.

Add `--after "1. e4"` with the moves the person opens with, when they said. Add `--speed rapid` when they said what speed the game is and the file has it (`bullet`, `blitz`, `rapid`, `classical`, `correspondence`, or `all`). Without it the script leaves out bullet if at least 30 slower games remain.

It prints:

- `read`: the games in the file, theirs, with this colour, and `used`, what the rest stands on, from the date `from` to `to`, by `speeds`.
- `left_out`: what it didn't read, and why.
- `first_moves`: from where the reading starts, each move with its `games`, `won`, `drawn`, `lost` and `score_percent`, always from the opponent's side, and the `replies` to it.
- `lines`: the top three, each `line` as far as enough games still agree, with the same counts, `of_their_last_30`, `next`, the moves played after it, and `opening`, the file's own name for it, or null. A null name stays unnamed: write the moves.
- `weak_spot`: another line they score badly in, if there is one.
- `form`: their last 12 games at these speeds, of either colour, and `rating_then` and `rating_now`.
- `positions`: the end of each line, ready for Step 3.

`next` is a move of whichever side is to move after the line. When that's the person's colour, it's what the opponent's opponents played, not the opponent: write "After it, White played 5. f3", never "they played". In the same way, when the opponent has Black, `first_moves` are White's and only their `replies` are the opponent's: "they mostly face 1.e4".

If `few_games` is true, say the picture rests on few games. If `used` is 0, say so, and run it again without `--after`.

## Step 3: Check where their lines end

Call `engine` once: `{"engine": "stockfish", "positions": <positions as printed>, "lines": 3}`, with every entry of `positions`, `weak_spot`'s too. Each result has `lines`, `fen` and `board_url`. Each Line's score is from White's side, in `cp` or `mate`: under 50 either way is about equal, under 150 a little better, under 300 clearly better, more is winning, and a `mate` is mating. Turn them into those words, and use the words everywhere.

If a result is `game_over`, skip that line. If it's `not_run`, send those positions again, once. Copy each Line's first moves as they are, and write them after the line's last move: a Line is the engine's play, not the opponent's, so never say they played it.

## Step 4: Write the plan

Call `generate` once, with `model: "queen"`, no `position`, and this `system`. Without a position it talks only about what you send, rather than bringing in lines of its own:

```text
You prepare a chess player for a game against one opponent. You know only what you are given: the counts from their games and the engine's lines.
In at most five sentences, in plain words, say which line to aim for, why it suits this opponent, and what to watch for.
Name only moves from what you are given. Name no opening. Say nothing about the opponent that you weren't told.
Judge positions in words, such as "Black stands a little better", never in numbers.
```

Send `messages` with one `user` message:

```text
I have {colour} against {name}. In {used} of their games from {from} to {to}:
Line 1: {line}. {games} games: {won} wins, {drawn} draws, {lost} losses for them. After it, {they, or White or Black when `next` is the person's colour} played {next}. The engine says {who stands better}, and its best moves from there are {the first Line's first 4 moves, numbered}.
Line 2: ...
They score worst in: {weak_spot's line and its counts}.
Their last 12 games: {won} wins, {drawn} draws, {lost} losses.
Which line should I aim for, and what should I watch for?
```

Leave `max_tokens` out: Queen's thinking counts toward it, so a low cap cuts the reply short or loses it. If the call answers `plan_required`, make it on `model: "knight"`, and say so in one line of your answer. If it answers `429 rate_limited`, wait for `Retry-After` and retry the same call. If it answers `upstream_unavailable`, make the same call once more. If that fails too, give the lines and the engine's words with no plan, and say once that the plan isn't available right now.

**Check the reply before you use it.** Go through every move it names: if a move isn't in what you sent, with the same number, drop that sentence. Drop a sentence too if it names an opening, or says something about the opponent that you didn't send.

## Step 5: Build a Study

Before you write your answer, build the person a Study with the `chessdrive-study` Skill beside this one: read `frame.md`, `board.md` and `opponent-prep.md` in `<this Skill's folder>/../chessdrive-study/references/`, and fill the page from what you already have. Hand it over as that Skill's Step 6 says: in a coding agent, open it and give its full path as a link. Do this in every run. Don't offer it or ask first, and make no new ChessDrive calls.

A coding agent always builds the Study, as the page is a file it opens: `show_board` isn't a way round it. If your app can't show a page, as in a chat with no artifacts, or that Skill isn't there, call `show_board` instead, once, before your answer, with `pgn` the first line's `line`, its `ply`, `orientation` the person's colour, `moves: true` and `mode: "play-both"`, so they can try their own moves. With no `show_board`, make the moves of each line's heading a link to its `board_url`.

## Step 6: Answer

```markdown
**Against White they mostly answer 1.e4 with 1...c5, in 96 of the 143 games I read, and they score worst after 1...e6.** One more sentence with the plan's main idea.

How to use the Study or the board, in one line.

### Line 1: 1. e4 c5 2. Nf3 d6 3. d4 cxd4
41 games: 20 wins, 8 draws, 13 losses for them, and 12 of their last 30. Where it leaves you, in the engine's words, with its best moves.

### Line 2: ...

### Their form
Their last 12: 7 wins, 1 draw, 4 losses, from 2026.10.02 to 2026.10.28. Their rating went from 1910 to 1944.

### Your plan
The plan from Step 4.

**What this rests on:** {used} of their {their_games} games, from {from} to {to}, at {speeds}. Left out: {left_out, in words}. Games on other accounts, and over the board, aren't in it.

Want to drill their main line?
```

Start with the bold answer, with nothing before it. Start a line's heading with "Line 1:", never with its first move, which would render as a list item. Write every line's counts as "21 games: 10 wins, 4 draws, 7 losses for them", never as 10W 4D 7L. Copy each line as the script writes it, numbers and all, and never renumber a move. An engine Line carries on from the move after its line's last: after `4. e4 d6` its first move is 5, as in 5. Be2 e5. If `weak_spot` isn't null, give it a heading after the top lines. The last line offers one follow-up.

## Follow-ups

- **A question about a position** they saw, such as "why was that a blunder?" or "what does the knight on f7 threaten?": never answer from your own reading of the board. Call `engine` on that one position, with `depth` left out and `lines` too, for one Line, or `lines: 3` if they ask what else to play, unless you have its answer already. Step 3's result for a line's last position is the engine's answer there, so a question about it needs no `engine` call. Then call `generate` with Queen, with the question and the Line in the message. Answer in two to four sentences from those two alone. A threat, an attack or a tactic goes in only if a Line plays it against a piece that stands on that square now: a piece that moves there first in the Line and is taken was given up, so give that as the Line's moves. Add no reason of your own, and no note on what you left out. Follow-ups in `<this Skill's folder>/../chessdrive-position/SKILL.md` has the rest.

These read the same file, so the script costs nothing:

- **"Drill their main line":** build an Opening drill with the `chessdrive-study` Skill, from `lines`, with the person's side as the side to drill.
- **"What did they play in the games they lost?":** run Step 2 again with `--lost`, and answer from its `lines` and counts.
- **"After 1.d4, what do they do?":** run Step 2 again with `--after`, and answer from `first_moves` and `lines`. Call `engine` only if they ask where it leaves them.

## Rules

- Name moves in algebraic notation (`Nf3`, `O-O`), never UCI, with their number.
- When you read games from both sites, end What this rests on with: "One username on two sites may be two people, so check these games are all theirs."
- Name no price unless they ask, and then add up `cost_usd` and never guess.
- Every call is billed to the person's ChessDrive Account: one `engine` call and one `generate` call a run, and none for the script.
- The PGN file and `prep/` stay where this code runs. What goes out is the positions and counts you send to `engine` and `generate`.
- When a tool says the Balance is empty, pass on its message and its link to Pricing, give what you already have, and stop.
- Before you send, read your answer once for a number judging a position, a move that isn't in the script's output or an `engine` Line, an opening's name where `opening` is null, such as Sicilian or Caro-Kann for a line that has none, even in a passing phrase, a Line, or a `next` of the person's colour, given as the opponent's own moves, a price they didn't ask for, and anything the tools didn't say. Fix what you find.
