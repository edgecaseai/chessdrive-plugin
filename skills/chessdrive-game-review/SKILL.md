---
name: chessdrive-game-review
description: Review a finished chess game with ChessDrive, or annotate it for a video or article. Use when someone says "review my last game", "what did I do wrong in this game" or "annotate this game for my video", or shares a PGN, a Lichess or chess.com game link, or a username and asks where the game went wrong. The engine checks every move, then the worst ones are explained at the player's level. Gives the turning points, the worst three moves and one lesson, or an annotated PGN for a Lichess study with talking points, then builds a Study, a page to step through the game. Calls the ChessDrive Connector's get_game, engine, generate and show_board tools.
---

# Game review

You take a finished chess game through the engine, then explain the moves that mattered. The engine judges every move and the chess model helps you say why, so your answer never rests on your own reading of the board. The ChessDrive Connector gives you the tools. If they aren't there, read Connect in `<this Skill's folder>/../chessdrive-vectors/references/set-up.md`, where `<this Skill's folder>` is the folder this file is in, which your app gave you, so don't search for it, and walk the person through it one step at a time. Give no chess reading of your own in the meantime, and go on when the tools are there.

Pick the mode from what they ask:

- **For me**, the default: "review my last game", "what did I do wrong". You give the turning points, the worst three moves and one lesson.
- **For a video or article**: "annotate this game", or they mention a video, a stream or an article. You give an annotated PGN and 3 to 5 talking points.

Two limits hold in everything you write:

- **Judge positions and moves in words.** Never write centipawns, an evaluation in pawns such as "a third of a pawn", a score such as `+1.3`, a win percentage or a move's `win_chance_lost`, even for a level game or a move that cost almost nothing. Saying a side has mate in 3 is fine.
- **Name only moves the tools gave you:** a move of the game, a `best_line`, or a `generate` answer's `lines`. Copy them exactly, and never work out a line yourself.

## If they ask what this does, or give too little

Say this, and wait: "Paste a game's PGN or its Lichess or chess.com link, or tell me your username and site for your last game, and tell me roughly your rating. I'll check every move with the engine and show you the turning points and your three worst moves. For a video, say so and I'll annotate it."

## Step 1: Get the game

- **A pasted PGN:** use it as given; moves with no headers are fine. Engine reads only the first game of a PGN, so if the paste holds several, ask which one and send only that.
- **A Lichess or chess.com link:** call `get_game` with `{"url": "<the link>"}`, as they gave it: it reads every form of both sites' links, `/game/<id>` included, and fetches the game on ChessDrive's side. Use its `pgn`. Its `color`, when it has one, is the person's colour. On `username_needed`, ask for their chess.com username, which finds the game, then call again with `{"url": "<the link>", "username": "<username>"}`.

- **A username:** ask which site if they didn't say, then fetch their last game with `python3 <this Skill's folder>/../chessdrive-vectors/scripts/fetch_games.py lichess <username> --max 1 --out game.pgn`, or `chesscom`, and go on without offering first. Say which game you found, with the opponent and the date, so they can stop you if it's the wrong one. Never call `search`, and don't bring it up: it can't find a player's games. If the script can't reach the site, or you can't run code, ask which game instead, as below.

**When you can't get it:** if `get_game` refuses, pass on its message and ask for the PGN: on Lichess it's under Share & export below the board, and on chess.com press Share, open the PGN tab and press Download. Stop there: no fetch of your own, search, browser or Claude in Chrome, as the sites stop those. If `get_game` isn't among your tools, ask them to reconnect ChessDrive or paste the PGN. Never rebuild the moves from what a page shows or from memory.

**Ask only for what's missing, once, in one message:**

- *Which game*, if they gave no PGN, link or username. Ask for one of those, and if they can't fetch it from here, give the steps for their site, asking which site if they didn't say:
  - **Lichess:** open your profile, open the game in your list, and paste me the page's address.
  - **chess.com:** open https://www.chess.com/games/archive/USERNAME with your username, open the game, and paste me the page's address.
  - **ChessBase:** make a PGN file of that game, by the ChessBase steps in `<this Skill's folder>/../chessdrive-vectors/references/get-games.md`, with only that game selected, and paste me its text or attach it.
- *Their colour*, for me mode only: take it from the link, from `color`, or from their name in the PGN's `White` and `Black` headers. If none of those says, ask, and never guess it from their rating.
- *Roughly their rating*, for me mode only: take it from the PGN's `WhiteElo` or `BlackElo`. A coach asking about a student gives the student's colour and rating.

## Step 2: Ask the engine

Call `engine` once, on the whole game: `{"engine": "stockfish", "position": {"pgn": "<the PGN>"}}`, with no `ply`, `lines` or `depth`. Each entry in `moves` has `move_number`, `color`, `move.san`, and:

- `ply` and `fen`: the position the move was played from
- `verdict`: `best`, `good`, `inaccuracy`, `mistake` or `blunder`, and `win_chance_lost`, how much the move cost
- `eval_before` and `eval_after`, from White's side
- `best_line`, the engine's Line from before the move
- `board_url`, on inaccuracies, mistakes and blunders: that position, with the engine's move drawn on it

A long game's answer can be too big for your app to show you at once. If it saves the answer to a file, read `moves` from there with your own tools; don't call `engine` again.

If `engine` says the PGN doesn't parse, tell them a move in its main line is illegal or the text isn't a game, and ask them to copy it again. Don't try to repair it. On `limit_too_high` the game is too long for one call: call again with `depth: 10` and say so in one line.

Turn evaluations into words, and use them everywhere: under 50 `cp` either way is about equal, under 150 a little better, under 300 clearly better, more is winning, and a `mate` is mating.

## Step 3: Pick the moves

- **For me:** the person's three worst moves are their mistakes and blunders with the highest `win_chance_lost`. The turning points are up to three mistakes or blunders, by either side, after which a different side stood better or a level game stopped being level. The moves to explain are those two groups, the worst three first, at most 5.
- **For a video or article:** the 5 mistakes and blunders, by either side, with the highest `win_chance_lost`.

**No mistakes:** if the person made no mistake or blunder, say so plainly: "The engine found no mistakes or blunders by you in this game." Then explain their worst inaccuracy if they have one, and any mistake of their opponent's that decided the game. With fewer than three, give the ones there are. Never pad the list.

## Step 4: Explain them

Call `generate` once per move, with `model: "queen"`, `position: {"pgn": "<the PGN>", "ply": <the move's ply>}`, and this `system`, filling in the rating. For a video or article, start it with "You explain a chess game to an audience of club players." instead of the first sentence. Make these calls two at a time, two in one message: they don't use each other's answers, so they needn't run one by one. Never send more than two at once, as the engine's notes behind each reply are then skipped without a word, and the replies get worse.

```text
You review a chess game for a player rated about {rating}. The move they ask about was a {verdict}.
In at most three sentences, in plain words, say what the move allowed and why the engine's best move is better.
Use the engine's Line you are given, and name only moves from that Line or from the game.
Judge positions in words, such as "Black is losing", never in numbers.
```

Send one `user` message:

```text
{Black} played {14...Qd7}, a {blunder}. The engine's best Line was {Nf6 Qe2 O-O}. Before the move {Black was a little better}; after it {White is winning}. What went wrong?
```

Leave `max_tokens` out: Queen's thinking counts toward it, so a low cap cuts the reply short or loses it.

If a call answers `plan_required`, make it and the rest on `model: "knight"`, and say so in one line of your answer. If it answers `429 rate_limited`, wait for `Retry-After` and retry the same call. If it answers `upstream_unavailable`, make the same call once more. If that fails too, give that move's verdict and the engine's Line with no explanation, and add no note about it. If every call fails, say once that the explanations aren't available right now.

Replies link each move as `[text](line:L1)`, and `lines` holds the moves that passed as legal. Write the moves as plain text. A link with no match in `lines` named an illegal move, so drop that sentence. Where a reply and the engine disagree, the engine is right. Build your answer from the replies and the Lines, and add no tactics of your own: the lesson and every "what it allowed" must be something they show.

## Step 5: Build a Study

Before you write your answer, build the person a page of this game with the `chessdrive-study` Skill: the Board, the verdicts on the moves and your explanations, to step through. Do this in every run. Don't offer it or ask first, and make no new ChessDrive calls. Read `board.md` and `review.md` in `<this Skill's folder>/../chessdrive-study/references/`, and fill the page from the `engine` answer and the `generate` replies you already have. Its orientation is the person's colour, or White if you don't know it.

If your app can't show a page, or that Skill isn't there, call `show_board` instead, once, before your answer, with `pgn`, `ply: 0`, `orientation`, `moves: true`, `mode: "play-both"`, so the person can try their own moves, and `annotations`. Each key is a move's `ply + 1`, each glyph is the mark above, and each comment is `generate`'s explanation or empty. Where no board shows, or you have no `show_board`, make the move in its heading a link to its `board_url`, as in `### [14...Qd7??](board_url) The queen left f7`.

## Step 6: Answer

Put one line on how to use the Study or the board under your first line. Any link goes on words, as in `[Step through the game](link)`, never bare, as a game's link is very long.

### For me

```markdown
**You lost with Black in 34 moves, after one bad move in a level game.** One more sentence on who stood better and when, from the evaluations.

How to use the Study or the board, in one line.

### 12.Nxe5 White took the centre
What changed, and who stood better after it.

### 14...Qd7?? The queen left f7
What it allowed, and the move to play instead.

### 22...Rf8? The rook gave up the open file
What it allowed, and the move to play instead.

**The lesson:** one sentence to take into the next game.

Want a drill of your three worst moves?
```

List the moves from Step 3 once each, in game order, so a move that is both a turning point and one of the worst three gets one heading. A heading is the move with its mark and a few words on what it did. Under it, write one or two sentences at the player's level: a beginner gets plain ideas such as "the knight was undefended", a strong player gets the idea behind the Line. End with one short line offering a drill PGN of these mistakes for a Lichess study, or, for a coach, homework for the student.

### For a video or article

Give the annotated PGN in a code block, built from the game:

- Keep the headers, and write every move of `moves` in order as its `move.san`, leaving out clocks and evals.
- Mark every inaccuracy, mistake and blunder in `moves`, not only those you explained, straight after the move: `?!` for an inaccuracy, `?` for a mistake, `??` for a blunder, as in `14...Qd7??`.
- After a marked move add a `{ comment }`: the explanation in one or two sentences for those you explained, and "Better was 14...Nf6." for the rest. A comment holds no braces.
- After the comment add the `best_line` as a variation, its first 6 moves at most, as in `(14...Nf6 15.Qe2 O-O)`.
- End with the game's result.

Check it before you hand it over: call `engine` with `"position": {"pgn": "<your PGN>", "ply": <the last move's ply>}` and `depth: 1`. Its `fen` must equal that move's `fen`; if the call is refused or the two differ, fix the PGN and check again. Tell them to import it in a Lichess study: New chapter → PGN.

Then give 3 to 5 talking points, in game order:

```markdown
1. **"The pin on d7 is the whole game."**
   Show: 13.Rxd7 Rxd7 14.Rd1.
```

The quoted line is the one sentence to say on camera. Each point's Line comes from the game or a `best_line`, and they find it in the Study at that move. With no Study, make the Line a link to the position's `board_url`, as in `[13.Rxd7 Rxd7 14.Rd1](board_url)`. The positions with no `board_url` get theirs from one `engine` call, never one call each: `positions` holding each one as `{"fen": "<its fen>"}`, with `depth: 10`. A checkmate or stalemate has no move to find, so show the position before it.

## Follow-ups

These reuse what you already have, with no new calls.

- **"Turn my mistakes into a drill PGN":** one game per mistake, in one PGN block, each with `[SetUp "1"]`, `[FEN "<the move's fen>"]` and `[Result "*"]`. Its moves are the `best_line`, after a first comment such as `{ You played 14...Qd7 here. Find better. }`. Lichess makes each game a chapter of a study.
- **"Show me those moves on their own boards":** one `show_board` per move, at its `ply`, with `alongside: true` on every board after the first, so they all stay live.
- **"Turn it into homework for my student":** build a Worksheet with the `chessdrive-study` Skill, from these positions and your explanations, so the student has a page of boards. If that Skill isn't there, write one line per position, "White to move: find a better move than [14.Nf3](board_url)", with the `board_url` cut at `&marks=`, so the link doesn't draw the answer, and put the answers at the end, with why each is better.

## Rules

- Name moves in algebraic notation (`Nf3`, `O-O`), never UCI, with their number (`14...Qd7`).
- Marks come only from `verdict`: `?!`, `?` or `??`, and none on a `best` or `good` move.
- Use Queen for what the person reads and Knight for bulk steps, such as a note on every move if they ask for one.
- Every call is billed to the person's ChessDrive Account. Make one whole-game `engine` call and about 5 `generate` calls, and reuse them for follow-ups.
- When a tool says the Balance is empty, pass on its message and its link to Pricing, give what you already have, and stop.
- Before you send, read your answer once for a number judging a position or a move, a mark that isn't the move's `verdict`, a move with two headings, a price they didn't ask for, and anything the tools didn't say. Fix what you find.
