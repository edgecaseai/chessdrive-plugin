# Mistake drill

A page that puts the person back in the positions where they went wrong and asks them to find a better move.

**Input:** one or more of the person's games as PGNs, at most ten, and their side in each. Send each game to `engine` on its own: it reads only the first game of a PGN. For a link, get the PGN as the `chessdrive-game-review` Skill's Step 1 does.

**From Game review:** when the `chessdrive-game-review` Skill has just reviewed the game, its `engine` answer is step 1.

## Calls

1. `engine` on each whole game. With the CLI, put the games in one PGN file and run `chessdrive engine --games games.pgn --out drill/answers.jsonl`, a line a game, which sends as many as the Plan allows and waits out `rate_limited` itself; read it with code. With the Connector, call `{"engine": "stockfish", "position": {"pgn": PGN}}` for each, together, as many at once as the Plan allows. A call over the limit waits up to 5 seconds, then answers `429 rate_limited`: wait for `Retry-After` and retry it.
2. **Pick the positions:** the person's moves from move 5 on with `verdict` `mistake` or `blunder`, highest `win_chance_lost` first, at most twelve across all the games. With fewer than three, add their other moves from move 5 on with the highest `win_chance_lost`, at least 0.1, until there are three in all, and head the page "The moves that cost you most" instead of "Your mistakes". With none at all, tell them the engine found nothing to drill, and build nothing.
3. One `engine` call for all of them: `{"engine": "stockfish", "positions": [{"fen": <the move's fen>}], "lines": 3, "depth": 18}`, one entry per position. The **accepted answers** are the first moves of each result's Lines within 0.5 pawns of the first, judged from the mover's side (board.md, Numbers). With a mate Line, only the mating Lines. **Drop the position** if the move they played is an accepted answer. Keep the accepted answers' `san`, and the first Line's `moves` and its `cp` or `mate`, in `DATA`.
4. Optional: one `generate` with `model: "knight"`, no `position`, each position's FEN, the move played and its first Line in one question, asking for one hint each as a JSON list of strings, and saying what a hint is. A hint names the idea or the target ("the queen on d8 is short of squares"), never the piece that moves or its square. Drop a hint that holds an accepted answer's destination square, that names the piece the first Line's first move moves, or that says an accepted answer's move in words, such as "castle" where an answer is `O-O` or "take the knight" where one is `Bxf6`.

## The page

In the frame ([frame.md](frame.md)), without `data-moves`. The header: "Your mistakes" or "The moves that cost you most", and "Find a better move than the one you played."

- One position at a time: `fen` the move's `fen`, `lastMove` the move before it, as `squares(<its fen>, <its move.san>)` (board.md, Moves in SAN), `orientation` the person's side, `mode` `play-white` or `play-black`. The drill sets the position back itself, so it takes no `tryMoves` and no "Back to the position": leave the frame's `#back` button out.
- **The panel:** a card with the caption, "Move 23 from your game against …: find a better move than {the move played}.", what the last try got, and the buttons; then the "Ask about this position" card; then a card with the progress strip. The engine's Line on that card is the answer, so put the card in a wrapper of your own, `<div id="ask" hidden>`: show it after a hit or Show, and when the next position comes up hide it again. Hide the card's `.cd-live-line` and `.cd-live-answer` whenever your code sets the Board, as for "Show the line" or the next position: the card clears them only on the person's own moves.
- On the person's `move`, compare its `san` with the accepted answers (board.md, Right or wrong). A hit gets a green square, "One of the engine's top choices.", "Show the line" and "Next". "Show the line" sets the position back and animates the first Line. A miss gets a red square, "Not one of the engine's top choices.", and the position back. After two misses offer "Hint", when there are hints, and "Show": a green arrow for the best move, "The engine's best move is {its san}.", the Board's `eval` set to the first Line's score, and "Next".
- The progress strip is a row of numbered `.cd-btn`s, solved ones ticked and the one on view `aria-current`. Any can be tried again.
