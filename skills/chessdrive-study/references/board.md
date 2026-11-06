# The Board in a page

## Load it

The frame's `<head>` loads it ([frame.md](frame.md)), from `https://cdn.jsdelivr.net/npm/@chessdrive/board@0.1.2/dist/board.umd.js`. Keep that exact URL: jsDelivr's `/npm/` path and an exact version. It's the script host every Claude artifact allows. The Board needs nothing else, as its pieces, squares and rules are inside it.

**Keep it in `.cd-board`,** which gives it its width. The Board fills its box and has no width of its own, so in a box that sizes to its content it collapses to a sliver: never `flex: 0 0 auto`, `width: fit-content` or `display: inline-block` around it. A second Board, as in a grid of diagrams, needs `display: block` and a width of its own too.

## The State

One object describes the whole Board. `board.set(patch)` merges a partial State and `board.state` returns the current one. Unknown fields are ignored. Call `set` straight after the tag, in the same script: don't wait for `ready`. An `addEventListener('ready', …)` in a later script never fires, as the Board is ready by then.

| Field | Value |
|---|---|
| `fen` | a position; or instead: |
| `pgn`, `ply` | a game, and how many half-moves have been played (0 = the start; leave `ply` out for the end) |
| `orientation` | `"white"` or `"black"`: the side at the bottom |
| `lastMove` | `"e2e4"`: tinted. A game supplies its own; setting `fen` clears it unless you pass it too |
| `marks` | a list of `{arrow: "e2e4", color}`, `{circle: "f7", color}`, `{square: "d5", color}`; colours `green`, `red`, `blue`, `yellow`, `orange`. Yours stay until you set `marks` again, which leaves the person's alone |
| `annotations` | verdicts on a game's moves, a map from Board `ply` to `{glyph, comment}`: see Verdicts |
| `eval` | an answer's `eval_before`, `eval_after` or Line as it comes, from White's side; `null` hides the bar, which keeps its place once shown |
| `mode` | `view` (no moves), `play-white`, `play-black`, `play-both` (the default, so set it; see Trying moves) |
| `moves` | `true` shows the game's move list inside the Board: beside it at `full` on a wide page, below at `phone` |
| `players` | `{white: {name, rating}, black: {name, rating}}`, with captures and material |
| `size` | `full` (squares up to 560 px, 520 beside the eval bar), `phone` (360, moves below), `embed` (240, buttons and link), `thumb` (160, the board alone) |

The Board follows the viewer's light or dark setting, whatever your page does, and dims in dark. A page with only a light look adds the `data-light` attribute to the element.

## Verdicts

The Board draws verdicts itself: in the move list, on the move's square, and the comment under the list while that ply is on view. Use `annotations` for them, not a list of your own.

- The key is the Board `ply` after the move: `moves[i].ply + 1`.
- Build them in page code from `DATA.moves`, so none goes missing, not by hand.
- The glyph comes only from `verdict`: `?!` for `inaccuracy`, `?` for `mistake`, `??` for `blunder`. A `best` or `good` move gets none: the Board's `!` and `!!` would read as praise the engine didn't give.
- The comment starts with the verdict's word: "Mistake. …", then the move's note. Where no model gave one, it says so, as in "Inaccuracy. No explanation: the chess model didn't answer.", never a note of your own.
- Set them with the `pgn`, in the same `set`. A new game clears them, and a move played from an earlier ply drops those on the moves it replaced.

## Commands and events

- `board.set(patch)` returns `false` and fires `error` for a bad value, which stays as it was.
- `board.play("Nf3")` or `board.play("g1f3")` plays one legal move from the position on view. An illegal one fires `error` and returns `false`.
- `await board.animate(["e4", "e5", "Nf3"])` plays a line, at a pace a person can follow, so use it rather than a timer of your own. `board.clear()` removes your Marks.
- `board.on(name, fn)` listens. Events report **the person's actions only**, never your own commands:
  - `move` `{uci, san, fen, ply}`: the person moved;
  - `ply` `{ply, fen}`: the person stepped through the game;
  - `marks` `{marks}`, `flip` `{orientation}`, `error` `{code, message}`.
- A click anywhere on a Board reaches your page as a `click` on the element, its buttons and link included: give a card its own button rather than listening on the Board.

## Trying moves

A Board that shows a game or a position to look at takes the person's moves, so they can try their own ideas and come back. Set `mode: "play-both"`, and give each such Board a button of yours under it, `hidden` at first: "Back to the game", or "Back to the position" for a `fen`. Copy this function as it stands:

```js
// `shown` is what to come back to: {pgn, annotations} or {fen, lastMove}, with any `marks` and `eval` you set.
// Returns a function that says whether the person is on their own moves.
function tryMoves(board, button, shown, onBack) {
  let left = null; // The ply of the game they left it at.
  board.on('move', ({ ply }) => {
    if (left === null) board.set({ marks: [], eval: null }); // Your answers are about what you showed.
    left = Math.min(left ?? ply - 1, ply - 1);
    button.hidden = false;
  });
  button.onclick = () => {
    const ply = left;
    left = null;
    button.hidden = true;
    board.set(shown.pgn === undefined ? shown : { ...shown, ply });
    onBack?.(ply);
  };
  return () => left !== null;
}
```

- A Board on its own: `tryMoves(board, back, {pgn, annotations})`, once for each Board on the page.
- With a page `show(ply)`: `const trying = tryMoves(board, back, {pgn, annotations}, show)`. Call `show` on the `ply` event only `if (!trying())`, as the plies then count the person's moves, not the game's. Your own clicks, on a graph or a turning point, start with `if (trying()) back.click()`.

## Numbers

- **Plies.** Each of a whole-game answer's `moves` has `ply`, the half-moves played *before* it: 0 for White's first move. The Board's `ply` counts half-moves played. So `moves[i]` is played from Board `ply: i` and shown done at `ply: i + 1`, and on a `ply` event the move just played is `moves[ply - 1]`. `generate`'s `position: {pgn, ply}` names the position at Board `ply`.
- **Evaluations** are from White's side, and exactly one of `cp` and `mate` is set. For the side to move, better is higher for White and lower for Black: compare `cp × (white ? 1 : −1)`. Print pawns with one decimal (`+1.3`) and a mate as `M3` (White mates) or `−M3`. `mate: 0` is checkmate on the board: print "Checkmate", and pass `eval: null`.
- **Moves in SAN.** Engine's answers through the Connector give each move in SAN alone: `best_line` and a Line's `moves` are lists such as `["Nf3", "d5"]`, and `move` and `best_move` are `{san}`. The CLI's `--json` gives `{san, uci}` in those lists instead, so read a move as `m.san ?? m`. An arrow and `lastMove` take a move's squares: get them from a Board you never put on the page, with this function as it stands:

  ```js
  // A move's squares, such as squares(fen, 'Nf3') → 'g1f3', or null when it isn't legal in that position.
  const probe = document.createElement('chessdrive-board');
  const squares = (fen, san) => (probe.set({ fen }) && probe.play(san) ? probe.state.lastMove : null);
  ```

- **Win chance** for a graph: `1 / (1 + Math.exp(-0.00368208 * cp))`; a mate is 1 if White mates and 0 if Black does, and for `mate: 0` the side that just moved has won.

## Patterns

- **Keep the page in step with the Board.** The Board holds the position. Your page holds `DATA` and one `show(ply)` function, which sets the Board's `ply`, `eval` and `marks` (`[]` if none) and updates your panel. Call it on the `ply` event and from your own clicks. Keep no chess position of your own.
- **Show a verdict:** go to the ply after the move, where the Board shows its glyph and comment.
- **Show the best move instead:** go to the ply before the move, with a green arrow for the engine's best move (`squares(fen, best_line[0])`), a red arrow for the move played (`squares(fen, move.san)`) and `eval_before`.
- **Right or wrong:** in `play-*` mode, on the person's `move`, compare its `san` with the sourced answers, leaving out `+` and `#`, then a `green` or `red` square on its `uci`'s third and fourth letters. For a miss, wait a beat and `set({fen, lastMove, marks: []})` back to the position. Go back with `fen`, not `ply`: a `play-*` Board takes moves only at the end of its game.
- **The other side replies:** on the person's correct `move`, `board.play(nextMove)`.
- **A line without losing the game:** show it as text, or `set({fen})` the position and `animate` the line, then `set({pgn, ply})` to come back. Set the annotations again with that `pgn`.
- **Keys:** with a game in `view` mode, ← → step it while the Board has focus, and arrive as `ply` events. In `play-both` the squares keep those keys for their cursor, and the Board's buttons and move list step it. A page that steps from anywhere listens on `document`, and ignores a keydown whose `target` is the Board, or it steps twice.
- **Print:** the frame's Save as PDF prints the page as it is, in light, without your buttons. A grid of diagrams goes to `mode: "view"`, and `size: "thumb"` from a `beforeprint` listener, back to `embed` on `afterprint`: `embed` prints its buttons and link, and is too tall for a grid. The squares print without the browser's background graphics. Write "White to play" beside each diagram yourself.
