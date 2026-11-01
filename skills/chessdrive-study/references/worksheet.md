# Worksheet

A printable sheet of positions for students, with an answer key, and an on-screen twin they can try.

**Input:** the positions as FENs, or games with move numbers, from the coach, and the answers if they have them. Every diagram is a position the coach gave, or reached in a game they gave.

**From a game:** send `engine` the `{pgn, ply}` of every position in one call, as `positions`, to get their `fen`s, with `depth: 1` if that's all you need. Don't work out a FEN yourself. A position with no moves left comes back as `game_over` with no analysis: use the position before it.

**Never change a position.** If the Board or the engine refuses one, name it at the top of the page, leave it out, and say so in the hand-over: the coach decides what they meant.

## Calls

None when the coach gives the answers. When they don't, `engine` with `lines: 1` on each position: the answer is the first Line's first move, in SAN, and a mate shows as "mate in N".

## The task line under each diagram

"White to play" or "Black to play", then the task, matched to where the answer came from:

- the move played in a game: "Find the move that was played."
- the coach's own solution: the coach's words, or "Find the best move."
- the engine: "Find the best move." or, for a mate Line, "Mate in N."

## The page

- A heading the coach can type into (`contenteditable`): class, date and title. Edits aren't saved, so say so in the hand-over.
- A grid of numbered diagrams, three across in print and on wide screens: each a Board with `fen`, `size: "embed"` (`"thumb"` in print), `mode: "view"`, `orientation` the side to move, the task line under it, and a print-only "Your move: ____". Each is a print block (`break-inside: avoid`).
- **Answer key** on its own printed page (`break-before: page`): number, answer in SAN, and where it came from (the game, the coach or the engine). On screen it stays hidden behind "Show answers", so students on a tablet don't see it.
- **Try it** on screen only: a "Try it" button on each diagram opens it large in `play-*` mode. The student's move is checked against the answer as in board.md, with "Not the game move, try again" or "Not the engine's move" for a miss, and "Show the answer" after two misses.
- **Check the answers on load:** play each answer on its position on a hidden Board. `play` returning `false` means a typo, shown to the coach at the top of the page.
- **Printing:** see board.md. In Claude there's no Print button.
