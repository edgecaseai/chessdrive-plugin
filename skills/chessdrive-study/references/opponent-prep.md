# Opponent prep

A page to explore what one opponent plays: their lines as a tree with results, and where the top lines leave the person.

**Input:** the opponent's PGN file, their name as the PGN writes it, and the colour the person will have. If the `chessdrive-prep` Skill has just run, build from its answers and make no new calls. If not, run it first, as this page needs what it gathers.

## Calls

1. `python3 ../chessdrive-prep/scripts/openings.py <file> --player "<name>" --against <colour> --tree prep/tree.json`, which makes no call and costs nothing. Its summary fills the page's top, and `prep/tree.json` holds every move they played: each entry has `move`, `games`, `won`, `drawn`, `lost`, `score_percent`, `last_played` and `then`, its next moves.
2. One `engine` call on the summary's `positions` with `lines: 3`, as the Prep Skill's Step 3 says.
3. The plan from the Prep Skill's Step 4, if you have it. It's one `generate` call.

## The page

- `DATA` holds the summary, the tree and the `engine` results, written by code. Never retype the tree.
- The Board: `orientation` the person's colour, `mode: "play-both"`, so the person walks the tree by moving.
- **The tree panel** beside it, kept in step with the Board's `move` and `ply`: for the current position, what they played, each with its games, wins, draws, losses and last date. Clicking a row plays it on the Board, with `play`. "Back" and "Start" buttons. A move the person plays that isn't in the tree shows "Not in their games".
- **Top lines** above it: each line with its counts, written as "1 draw" and "1 loss" where there's one, and where the engine says it leaves the person, in words. Clicking one plays it out on the Board. The engine's Line is shown as the engine's, never as their moves.
- **What this rests on,** under the panel: how many games, from when to when, at what speeds, and `left_out` in words.
- `KIND` is `prep`.
