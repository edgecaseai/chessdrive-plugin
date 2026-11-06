---
name: chessdrive-study
description: Build someone a Study with ChessDrive, an interactive chess page of their own on the ChessDrive Board. Use when someone says "turn this game into a page I can step through", "make me a drill of my mistakes", "make a worksheet from these positions for my students" or "build me a trainer for my opening lines", or asks for any chess app, viewer, board, trainer, quiz or printable sheet, even if they don't name ChessDrive. In Claude it's an artifact, in a coding agent a local HTML file, whose engine and questions run on a Study key. Calls ChessDrive's engine and chess models only as the Study needs, through the `chessdrive` CLI wherever code runs, or the ChessDrive Connector where none does.
---

# Build a Study

You build a **Study**: one page for one person, around their game, their lines or their students. It shows the **Board**, ChessDrive's free chess board, which owns the rules, the position and the person's moves, so your page code only feeds it and listens to it. Paid answers come from `engine` and `generate`, which you call yourself while you build: with the `chessdrive` CLI wherever you can run code, and with the ChessDrive Connector's tools where you can't. Read `<this Skill's folder>/../chessdrive-vectors/references/calls.md` before your first call: it has who judges what, how to make calls at once and what to do when one is refused. `<this Skill's folder>` is the folder this file is in, which your app gave you, so don't search for it. If what you need isn't there, read `<this Skill's folder>/../chessdrive-vectors/references/set-up.md` and walk the person through it one step at a time. Give no chess reading of your own in the meantime, and go on when it's there. The answers you gather go into the page at build time. The page answers about a position the person plays or steps to, only when they ask: the engine's Line from Stockfish in their browser, free, and a question to Generate with a **Study key** made for that page ([live.md](references/live.md)).

Every move on the page is **sourced**: from a PGN or FEN the person gave, from `engine`, or played by the person on the Board. Every verdict ("a mistake", "the best move") comes from `engine`, in its words, and every explanation from a chess model, as `calls.md` says. Never work out a move yourself.

## Step 1: Pick the kind

Build without asking whether they want a page. Match the request to one kind, then read [frame.md](references/frame.md), [board.md](references/board.md), [live.md](references/live.md) and the kind's reference before anything else:

| They want | Kind | Reference | Calls |
|---|---|---|---|
| to go through a game and see where it turned | Game review | [review.md](references/review.md) | `engine` 1, `generate` 1 a marked move |
| to practise the moments they went wrong | Mistake drill | [mistake-drill.md](references/mistake-drill.md) | `engine` 1 a game and 1 a position, `generate` 0 or 1 |
| to learn or test a line of their repertoire | Opening drill | [opening-drill.md](references/opening-drill.md) | None |
| sheets of positions to print or hand out | Worksheet | [worksheet.md](references/worksheet.md) | None with the coach's answers, else `engine` 1 a position |
| to prepare against an opponent, from a PGN file of their games | Opponent prep | [opponent-prep.md](references/opponent-prep.md) | `engine` 1, `generate` 0 or 1 |

- **One position or one game to look at or play** needs no page where your app draws boards: in Claude's chat or desktop app, where the Connector has `show_board`, call it and stop. A coding agent builds the page. It takes the Board's State. Add `opponent: {"engine": "stockfish", "level": 5}` to play the person with the engine.
- **Something else,** such as a table of their games: build it from the closest kind and keep every rule here.
- **Preparing against an opponent with no file of their games:** run the `chessdrive-prep` Skill first, and build nothing from memory of their games.

Ask one question only when the request lacks the one input the kind needs: which game, which side, which lines. If they ask what this does, or give no position, game or lines to work from, say in a line or two what you need, such as a PGN, a Lichess or chess.com link, or their opening lines, and build nothing. Take the person's word for the side they played, whatever the PGN's names say.

## Step 2: Gather

Make the calls the kind's reference lists, and no more. **When another ChessDrive Skill has just gathered these answers, use them and make no new calls.**

- `generate` takes `model`, `system`, `messages` and `position`. Put everything it may talk about in the message: the moves, the evaluations and the engine's Lines. Make the calls at once with `ask.py`, Queen for what the person reads as prose and Knight for bulk, as `calls.md` says, and write the page while they run.
- A long game's `engine` answer can be too big for your app to show you at once. If it saves the answer to a file, read `moves` from there; don't call `engine` again.
- When a tool says the Balance is empty, pass on its message and its link to Pricing, and stop.
- Keep the `cost_usd` of every answer, in case they ask what the page cost.

## Step 3: Build the page

One self-contained HTML file in the frame, [frame.md](references/frame.md), so every Study looks like ChessDrive, has the same layout and fits any screen, with the Board as [board.md](references/board.md) says:

- the frame's page, style and keeping script, copied as they stand, with the kind's parts in its header, `.cd-board`, `.cd-panel` and `.cd-more`;
- for a Board the person moves on, live.md's card, styles and `live(board)`, with the Study key you made in a coding agent in the page's `chessdrive-key` `<meta>`, and none in an app that shows the page itself;
- the fields of each tool answer your page reads, inline as one `const DATA = {…}` of JSON, leaving out `board_url` and what you don't use. If you can run code, write `DATA` from the answers with code. Never retype a move from memory: one wrong letter in a Line is an illegal move on the page;
- page code after the keeping script that sets the Board's State and listens to its events, as the kind's reference says, all inside `(() => { … })();`. At the top level of a script, a name the browser already uses, such as `top`, stops the whole script.

In Claude it's an artifact, in ChatGPT a canvas, and in a coding agent a `.html` file in the person's working folder, never a scratch or temporary folder, so they can find and keep it.

**If your app can't show a page,** fall back, though a coding agent always can, as the page is a file it opens: `show_board` with the game and its verdicts (see [review.md](references/review.md)), or the position, where the Connector has it. Without `show_board`, give the `board_url` links from the tool answers.

## Step 4: Link back

Every page carries the frame's footer, on screen and on every printed page, whatever else it shows:

```html
<footer class="cd-made">Made with <a href="https://platform-staging.chessdrive.io/?utm_source=study&utm_campaign=KIND" target="_blank" rel="noopener">ChessDrive</a></footer>
```

`KIND` is `review` for a Game review, `drill` for a Mistake drill, `opening` for an Opening drill, `worksheet` for a Worksheet, `prep` for Opponent prep and `other` for anything else. The frame's print rules repeat it on every sheet. The Board's own "Board by ChessDrive" link stays as it is.

## Step 5: Check it

Run `python3 <this Skill's folder>/scripts/check.py <file>` and fix each line it prints until it prints `ok`. It checks `DATA`, the scripts, `innerHTML`, the Board's URL, keys and the footer, with `node --check` where Node is. Never open the page in a browser to check it, yours or the person's: an error once it runs shows on the page, as a line they can paste back to you. It's done when every line holds:

- the page is the frame: its tokens and no colour or font of your own, the header's two lines, the Board in `.cd-board`, the panel in `.cd-panel`, and `data-moves` on `.cd-page` only when the Board shows its moves;
- the Board faces the person's side, or the side to move for a position with no owner, and one that shows a game or a position takes moves and has its way back (board.md, Trying moves);
- every move and verdict on the page traces to the person's input or to an answer in `DATA`, and evaluations read from White's side (`+1.2`, `−0.4`, `M3`, `−M3`);
- text from a PGN or a tool goes in with `textContent`, as a PGN header can hold anything, and the page makes no `fetch` but the keeping script's and live.md's card's, and loads Stockfish only as live.md's `stockfish()` does.

## Step 6: Hand it over

In a coding agent, open the file for them first: `open <file>` on macOS, `xdg-open <file>` on Linux, `start "" <file>` on Windows.

Then up to three short lines:

- the answer to what they asked, when the page has one ("Engine found no mistakes by you; 7...h6 cost you the most"), and where on the page to look: a Game review's verdicts and notes are in its top card, On the board;
- how to use the page ("Click a move or use ← →"), and, for a file, where it is: its full path as a link, as in `[/Users/ana/chess/review.html](file:///Users/ana/chess/review.html)`;
- how to keep and share it: for a file, "Download saves a copy that opens anywhere, without your key; send it, or Save as PDF"; in Claude, "Download or share it from the artifact's menu". For a page with a Study key, add that the engine's Line runs in their browser, free, that its questions work for 7 days, up to a dollar a day, and that the key is listed on the Dashboard under Study keys.

Say nothing about how you checked the page. Name no price unless they ask. If they ask what it cost, add up `cost_usd` and never guess ("2 ChessDrive calls, 4 cents").

## Follow-ups

- **A question about a position** they saw: as `calls.md` says. An `engine` answer the page was built from is reused, so a question about its position needs no new `engine` call.

## Rules

- Load the Board only from the pinned URL in [frame.md](references/frame.md). Its rules and moves are the ones the person can trust.
- Keep the person's data in their page: a game they pasted stays in `DATA`.
- Every call is billed to the person's ChessDrive Account, the page's own too, up to its Study key's dollar a day. Spend only on what the page shows, and rebuild a page from the answers you have.
- Name verdicts as `engine` does. A move it didn't call a mistake is a "costly move" at most.
