---
name: chessdrive-study
description: Build someone a Study with ChessDrive, an interactive chess page of their own on the ChessDrive Board. Use when someone says "turn this game into a page I can step through", "make me a drill of my mistakes", "make a worksheet from these positions for my students" or "build me a trainer for my opening lines", or asks for any chess app, viewer, board, trainer, quiz or printable sheet, even if they don't name ChessDrive. In Claude it's an artifact, in a coding agent a local HTML file. Calls the ChessDrive Connector's engine and generate tools only as the Study needs.
---

# Build a Study

You build a **Study**: one page for one person, around their game, their lines or their students. It shows the **Board**, ChessDrive's free chess board, which owns the rules, the position and the person's moves, so your page code only feeds it and listens to it. Paid answers come from the ChessDrive Connector's tools, which you call yourself while you build. If they aren't there, read Connect in `<this Skill's folder>/../chessdrive-vectors/references/set-up.md`, where `<this Skill's folder>` is the folder this file is in, which your app gave you, so don't search for it, and walk the person through it one step at a time. Give no chess reading of your own in the meantime, and go on when the tools are there. The page never calls them: the answers go into it at build time.

Every move on the page is **sourced**: from a PGN or FEN the person gave, from `engine`, or played by the person on the Board. Every verdict ("a mistake", "the best move") comes from `engine`, in its words. `generate` writes the explanation around them, and may name only moves it was given. Never work out a move yourself.

## Step 1: Pick the kind

Build without asking whether they want a page. Match the request to one kind, then read [board.md](references/board.md) and the kind's reference before anything else:

| They want | Kind | Reference | Calls |
|---|---|---|---|
| to go through a game and see where it turned | Game review | [review.md](references/review.md) | `engine` 1, `generate` up to 3 |
| to practise the moments they went wrong | Mistake drill | [mistake-drill.md](references/mistake-drill.md) | `engine` 1 a game and 1 a position, `generate` 0 or 1 |
| to learn or test a line of their repertoire | Opening drill | [opening-drill.md](references/opening-drill.md) | None |
| sheets of positions to print or hand out | Worksheet | [worksheet.md](references/worksheet.md) | None with the coach's answers, else `engine` 1 a position |
| to prepare against an opponent, from a PGN file of their games | Opponent prep | [opponent-prep.md](references/opponent-prep.md) | `engine` 1, `generate` 0 or 1 |

- **One position or one game to look at or play** needs no page: where the Connector has `show_board`, call it and stop. It takes the Board's State. Add `opponent: {"engine": "stockfish", "level": 5}` to play the person with the engine.
- **Something else,** such as a table of their games: build it from the closest kind and keep every rule here.
- **Preparing against an opponent with no file of their games:** run the `chessdrive-prep` Skill first, and build nothing from memory of their games.

Ask one question only when the request lacks the one input the kind needs: which game, which side, which lines. If they ask what this does, or give no position, game or lines to work from, say in a line or two what you need, such as a PGN, a Lichess or chess.com link, or their opening lines, and build nothing. Take the person's word for the side they played, whatever the PGN's names say.

## Step 2: Gather

Make the calls the kind's reference lists, and no more. **When another ChessDrive Skill has just gathered these answers, use them and make no new calls.**

- `generate` takes `model`, `system`, `messages` and `position`. Put everything it may talk about in the message: the moves, the evaluations and the engine's Lines.
- Use `model: "queen"` for what the person reads as prose, such as a turning point explained, and `model: "knight"` for bulk, such as a hint for each position. If a call answers `plan_required`, make it and the rest on `model: "knight"`, and say so in one line. If it answers `429 rate_limited`, wait for `Retry-After` and retry the same call. If it answers `upstream_unavailable`, make the same call once more. If that fails too, leave that note out of the page, with no word about it.
- Leave `max_tokens` out: the Model's thinking counts toward it, so a low cap cuts the reply short or loses it.
- A reply links each move as `[text](line:L1)`, and its `lines` holds the moves that passed as legal. Write the moves as plain text in the page. A link with no match in `lines` named an illegal move, so drop that sentence. Drop a sentence too if it names a move that isn't in what you gave it.
- A long game's `engine` answer can be too big for your app to show you at once. If it saves the answer to a file, read `moves` from there; don't call `engine` again.
- When a tool says the Balance is empty, pass on its message and its link to Pricing, and stop.
- Keep the `cost_usd` of every answer, in case they ask what the page cost.

## Step 3: Build the page

One self-contained HTML file, following [board.md](references/board.md):

- the Board, from its pinned script tag;
- the fields of each tool answer your page reads, inline as one `const DATA = {…}`, leaving out `board_url` and what you don't use. If you can run code, write `DATA` from the answers with code. Never retype a move from memory: one wrong letter in a Line is an illegal move on the page;
- page code that sets the Board's State and listens to its events, as the kind's reference says, all inside `(() => { … })();`. At the top level of a script, a name the browser already uses, such as `top`, stops the whole script.

In Claude it's an artifact, in ChatGPT a canvas, and in a coding agent a `.html` file the person opens.

**If your app can't show a page,** fall back: `show_board` with the game and its verdicts (see [review.md](references/review.md)), or the position, where the Connector has it. Without `show_board`, give the `board_url` links from the tool answers.

## Step 4: Link back

Every page carries this line, on screen and on every printed page, whatever else it shows:

```html
<footer class="cd-made">Made with <a href="https://platform-staging.chessdrive.io/?utm_source=study&utm_campaign=KIND" target="_blank" rel="noopener">ChessDrive</a></footer>
```

`KIND` is `review` for a Game review, `drill` for a Mistake drill, `opening` for an Opening drill, `worksheet` for a Worksheet, `prep` for Opponent prep and `other` for anything else. Add `@media print { .cd-made { position: fixed; bottom: 0; } }`, which repeats it on every sheet. The Board's own "Board by ChessDrive" link stays as it is.

## Step 5: Check it

It's done when every line holds:

- the Board's column has a width of its own (board.md, Load it), or the Board draws nothing;
- the Board faces the person's side, or the side to move for a position with no owner;
- a Board that shows a game or a position takes moves and has its way back (board.md, Trying moves);
- every move and verdict on the page traces to the person's input or to an answer in `DATA`;
- evaluations read from White's side (`+1.2`, `−0.4`, `M3`, `−M3`);
- text from a PGN or a tool goes in with `textContent`, never `innerHTML`: a PGN header can hold anything;
- the page holds no API key, token or Connection secret, and makes no `fetch`;
- the page code sits inside a function, not at the top level of its script;
- the footer is there.

A coding agent that can open the page in a browser does so, and looks at the console.

## Step 6: Hand it over

Up to two short lines:

- the answer to what they asked, when the page has one ("Engine found no mistakes by you; 7...h6 cost you the most");
- how to use the page ("Click a move or use ← →"), and where it is, for a file.

Name no price unless they ask. If they ask what it cost, add up `cost_usd` and never guess ("2 ChessDrive calls, 4 cents").

## Follow-ups

- **A question about a position** they saw, such as "why was that a blunder?" or "what does the knight on f7 threaten?": never answer from your own reading of the board. Call `engine` on that one position, with `depth` left out and `lines` too, for one Line, or `lines: 3` if they ask what else to play, unless you have its answer already. An `engine` answer the page was built from is reused, so a question about its position needs no new `engine` call. Then call `generate` with Queen, with the question and the Line in the message. Answer in two to four sentences from those two alone. A threat, an attack or a tactic goes in only if a Line plays it against a piece that stands on that square now: a piece that moves there first in the Line and is taken was given up, so give that as the Line's moves. Add no reason of your own, and no note on what you left out. Follow-ups in `<this Skill's folder>/../chessdrive-position/SKILL.md` has the rest.

## Rules

- Load the Board only from the pinned URL in [board.md](references/board.md). Its rules and moves are the ones the person can trust.
- Keep the person's data in their page: a game they pasted stays in `DATA`.
- Every call is billed to the person's ChessDrive Account. Spend only on what the page shows, and rebuild a page from the answers you have.
- Name verdicts as `engine` does. A move it didn't call a mistake is a "costly move" at most.
