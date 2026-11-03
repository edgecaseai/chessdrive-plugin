# Mistake drill

A page that puts the person back in the positions where they went wrong and asks them to find a better move.

**Input:** one or more of the person's games as PGNs, at most ten, and their side in each. Send each game to `engine` on its own: it reads only the first game of a PGN.

**From Game review:** when the `chessdrive-game-review` Skill has just reviewed the game, its `engine` answer is step 1.

## Calls

1. `engine` with `{"engine": "stockfish", "position": {"pgn": PGN}}` on each whole game. Engine takes parallel requests, so call them together, up to the Plan's limit: 2 on Free, 6 on Hobby and 18 on Pro, and `balance` says which Plan. A call over the limit waits up to 5 seconds, then answers `429 rate_limited`: wait for `Retry-After` and retry it.
2. **Pick the positions:** the person's moves from move 5 on with `verdict` `mistake` or `blunder`, highest `win_chance_lost` first, at most twelve across all the games. With fewer than three, add their moves with the highest `win_chance_lost`, at least 0.1, up to three, and head the page "The moves that cost you most" instead of "Your mistakes". With none at all, tell them the engine found nothing to drill, and build nothing.
3. One `engine` call for all of them: `{"engine": "stockfish", "positions": [{"fen": <the move's fen>}], "lines": 3, "depth": 18}`, one entry per position. The **accepted answers** are the first moves of each result's Lines within 0.5 pawns of the first, judged from the mover's side (board.md, Numbers). With a mate Line, only the mating Lines. **Drop the position** if the move they played is an accepted answer. Keep the accepted answers' `san`, and the first Line's `moves`, in `DATA`.
4. Optional: one `generate` with `model: "knight"`, no `position`, all the positions as FENs with their best Lines in one question, asking for one hint each as a JSON list of strings. A hint names the idea or the target ("the queen on d8 is short of squares"), never the piece that moves or its square. Drop a hint that holds an accepted answer's destination square.

## The page

- One position at a time: `fen` the move's `fen`, `lastMove` the move before it, as `squares(<its fen>, <its move.san>)` (board.md, Moves in SAN), `orientation` the person's side, `mode` `play-white` or `play-black`. Caption: "Move 23 from your game against …: find a better move than {the move played}."
- On the person's `move`, compare its `san` with the accepted answers (board.md, Right or wrong). A hit gets a green square, "Show the line" and "Next". "Show the line" sets the position back and animates the first Line. A miss gets a red square, "Not one of the engine's top choices", and the position back. After two misses offer "Hint", when there are hints, and "Show": a green arrow for the best move, with its `eval`.
- A progress strip of the positions, solved ones ticked. Any can be tried again.
