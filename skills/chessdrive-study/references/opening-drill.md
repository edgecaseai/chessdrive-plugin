# Opening drill

A page where the Board plays the other side of the person's repertoire and the person plays theirs, from memory.

**Input:** the lines, as a PGN with variations, a list of lines or a study they pasted, and the side they play. The lines are theirs: build only from what they gave. If they give only an opening's name, ask for the moves, and never fill them in from memory.

## Calls

None. Optional, only when they ask whether the lines are any good: one `engine` call with `positions` holding the last position of each line, so the page can show where it leaves them.

## The page

In the frame ([frame.md](frame.md)), without `data-moves`. The header: "Your lines as {White}", and "Play your moves from memory; the board answers with the line's."

- `DATA.lines` holds each line as a list of SAN moves from the start, which you write out from what they gave. Keep them as given, and don't add a move.
- **Check the lines on load:** play each on a hidden Board. `play` returning `false` means a typo: name the line and its move at the top of the page, and leave the line out.
- Compare with the Board's `san`, with `+#!?` removed from both, in page code. No chess library is needed.
- **The Board:** `orientation` the person's side, `mode` their colour. To start or restart a line, `set({fen: START, lastMove: null, marks: []})`. If they play Black, then `play` the line's White first move.
- On the person's `move`: the line's next move gets a green square, then `play` the opponent's next move from a line that shares these moves, least practised first. Anything else gets a red square, the position back, then the expected move as a green arrow, and they try again (board.md, Right or wrong). Keep the position's FEN from `board.state.fen` after each of your own moves, for going back.
- A line ends at its last move: "Line done", then the next line. Count clean runs per line, and bring back lines with misses sooner within the session. The counts last only as long as the page stays open.
- **The panel:** a card with the line on view and how the last move went, then a card with a `.cd-list` of the lines and their clean runs, each under the person's own name for it or "Line 1", never its moves: this is a drill from memory. Clicking one starts it.
