# Game review

A page to step through one game and see where it turned: the Board with the move list and its verdicts, an evaluation graph, and the turning points explained.

**Input:** the game as a PGN, and which side the person played. Take a pasted PGN as given. For a link, fetch the PGN as the `chessdrive-game-review` Skill does; if you can't, ask for it. Never rebuild the moves from a page or from memory. `engine` reads only the first game of a PGN, so if a paste holds several, ask which one. Ask for the side only if neither the person nor the PGN's names say.

**From Game review:** the `chessdrive-game-review` Skill hands you the `engine` answer and a note for every marked move. Skip the calls below: its turning points are the ones it heads, and each note is its move's explanation.

## Calls

1. `engine` with `{"engine": "stockfish", "position": {"pgn": PGN}}`, no `ply`: one answer for the whole game. Each of `moves` has `ply`, `move_number`, `color`, `move.san`, `fen`, `eval_before`, `eval_after`, `win_chance_lost`, `verdict` (`best`, `good`, `inaccuracy`, `mistake`, `blunder`) and `best_line`. If it says the PGN doesn't parse, say a move in its main line is illegal or the text isn't a game, and ask them to copy it again. On `limit_too_high`, call again with `depth: 10` and say so in one line.
2. **Turning points:** the person's moves with `verdict` `mistake` or `blunder`, highest `win_chance_lost` first, at most three. With none, take their one move with the highest `win_chance_lost`, call it "the costliest move", and say in the hand-over that the engine found no mistakes by them.
3. **A note for every marked move,** all at once with `ask.py` as `calls.md` says, while you write the page: one `generate` each, `model: "queen"` for a mistake or blunder, up to 12, and `model: "knight"` for an inaccuracy, with `position: {"pgn": PGN, "ply": <the move's ply>}` and this `system`, filling in the rating from the PGN's `WhiteElo` or `BlackElo`, or "a club player" without one. For Knight, "In one plain sentence of at most 20 words" replaces "In at most three sentences, in plain words".

   ```text
   You review a chess game for a player rated about {rating}, who had {Black}. The move they ask about was a {verdict}.
   In at most three sentences, in plain words, say what the move allowed and why the engine's best move is better.
   Use the engine's Line you are given, and name only moves from that Line or from the game.
   Judge positions in words, such as "Black is losing", never in numbers.
   ```

   and one `user` message:

   ```text
   {Black} played {14...Qd7}, a {blunder}. Instead of it, the engine's best Line was {14...Nf6 15.Qe2 O-O}. The game went on {15.Rd1 Qe7 16.Nd5}. What went wrong?
   ```

## The page

In the frame ([frame.md](frame.md)), with `data-moves`. The header: "Your game against {opponent}", and "Step through with ← → or the moves, and play your own to try an idea."

- **The Board:** `pgn`, `ply: 0`, `orientation` the person's side, `moves: true`, `mode: "play-both"`, `players` from the PGN's headers, and `annotations` for every `inaccuracy`, `mistake` and `blunder` (board.md, Verdicts), with its note as the comment. The person tries their own moves and comes back with "Back to the game" under it (board.md, Trying moves).
- **The panel,** three cards, in step with `ply`:
  - **On the board,** first, where the person looks: the move just played, its verdict's `.cd-tag` and its note when it has one, and the evaluation before and after, with `eval` on the Board, from `ply: 0`: there, the first move's `eval_before`, so its bar is there from the start. On a marked move, "Show the best move", which goes to the ply before the move with the two arrows from board.md.
  - **Turning points,** a `.cd-list`, each with its verdict's `.cd-tag`: clicking one goes to the ply after the move, where the Board shows its verdict and explanation.
  - **White's chance to win:** a plain SVG graph, 80 px tall and the card's width, one point per ply, with the turning points as dots in their verdict's colour (`--mistake`, `--blunder`, and `--brand` for the costliest move) and the ply on view as a `--brand` dot. Clicking the graph sets `ply`.
- **Keys:** ← → step, from your own listener (board.md, Keys).

## Where the app can't show a page

Call `show_board` with `pgn`, `ply: 0`, `orientation`, `moves: true`, `mode: "play-both"`, so the person can try their own moves, `players` and the same `annotations`. They can be 40 KB at most, so cut the comments on inaccuracies first.
