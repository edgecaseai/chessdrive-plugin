---
name: chessdrive-position-filter
description: Find chess positions by what stands on the board, across over two million games by strong players, with ChessDrive's Search. Use when someone asks for positions or examples such as "rook endings with White to move", "a knight on the rim", "opposite-coloured bishops", "a passed pawn on the seventh" or "kings castled on opposite sides", from master games rather than their own. Writes a Position filter from their words, runs it with Search's `where` mode, and links each position to a board. Calls ChessDrive with the ChessDrive Connector's `search` tool in a chat app, Claude's or ChatGPT, and through the `chessdrive` CLI in a coding agent.
---

# Find positions by a filter

You turn what someone describes on a board into a **Position filter**, run it with Search, and show them the positions it finds, each with a game that reached it. Read `<this Skill's folder>/../chessdrive-vectors/references/calls.md` before your first call: it says how to call ChessDrive and what to do when a call is refused. `<this Skill's folder>` is the folder this file is in, which your app gave you, so don't search for it. If what you need isn't there, read `<this Skill's folder>/../chessdrive-vectors/references/set-up.md` and walk the person through it one step at a time.

Search looks at games up to October 2025, mostly by titled and master-level players. It can't yet look only at one player's games, some years or some ratings. For an idea across the person's **own** games, use the `chessdrive-game-search` Skill instead.

If they ask what this does, or give too little, say this and wait: "Describe a kind of position, such as rook endings with White to move or a knight on the rim, and I'll find examples from master games, each with a board."

## Step 1: Write the filter

A filter is a JSON tree, true or false for each position. Each node is an object with one key.

- **Board expressions** give squares: `{"piece": "wN"}` (`w` or `b`, then `P N B R Q K`); `{"attacks": "wB"}` or `{"attacks": "white"}`, where a side's own pieces count as attacked, so it also means defended; `{"occupied": "white" | "black" | "any"}`; `{"squares": ["g8", "h7"]}`; `{"rank": 7}`; `{"file": "a"}`; `{"and": [..]}`, `{"or": [..]}`, `{"not": X}`; `{"shift": [X, "N"]}`, one step N S E W NE NW SE SW; `{"fill": [X, "N"]}`, 1 to 7 steps without X; `{"flip": X}`, colours swapped and ranks mirrored.
- **Tests** give true or false: `{"any": X}`, `{"none": X}`, `{"count": X, "gte": 3}` (or `lte`, `eq`), `{"to_move": "white"}`, `{"castling": "K"}`, `{"en_passant": true}`, `{"all": [..]}`, `{"some": [..]}`, `{"not": T}`, `{"flip": T}`.
- **The root is a test.** Squares go inside `any`, `none` or `count`: `{"piece": "wN"}` alone is refused.
- **"Either side"** is `{"some": [T, {"flip": T}]}`: write T from White's side.
- **Named parts** go in `define` and are used as `{"ref": "name"}`.

Start from `<this Skill's folder>/references/parts.json`: ready parts for a rook ending, White's passed pawns, light squares, opposite-coloured bishops, a piece on the rim and kings castled on opposite wings. Copy into `define` only the parts you use and the parts they use: `opposite_bishops` needs `light_squares`. `<this Skill's folder>/references/examples.json` has five requests worked through, from words to `where` and `define`. `<this Skill's folder>/references/position-filter.schema.json` is the full schema, if a node's exact form is in doubt.

Read their words as a chess player would. "A knight on the rim" is on the a- or h-file. "Rook ending" allows pawns and kings. "White has" means White's pieces; "either side" needs `flip`. If the words could mean two filters, take the plainer one and say which you took.

## Step 2: Run it

A call costs half a cent a position returned, at least one a call: 20 positions are 10 cents. Go ahead without asking.

- **CLI:** write the filter to `where.json` and the parts to `define.json`, then run `chessdrive search --where @where.json --define @define.json --limit 20 --json`. Leave out `--define` when there are no parts.
- **Connector:** call `search` with `where`, `define` and `limit: 20`.

The answer's `positions` each have a `fen`, `occurrences` (how many times games reached it), `quiet`, and in `examples` one game with its players, date and the `ply` it reached the position. `next_cursor`, when it isn't null, gets more: send it as `cursor` with the same `where` and `define`, only if they ask for more.

## Step 3: When it's refused

- **`invalid_filter`:** `param` names the node at fault, such as `where.all[1].ref`. Mend that node alone and send once more. If it's refused again, tell them in plain words what you tried to find, and stop.
- **`upstream_unavailable` saying the filter took too long:** narrow it once, for example with `to_move` or a piece count, say what you added, and send again.
- **Anything else:** as `calls.md` says.

## Step 4: Answer

- **None found:** say so, and offer one way to loosen it, such as either side to move.
- **Otherwise:** one line on what the filter looks for, in words. Then up to 5 positions, most played first by `occurrences`: each a link to its position on the Board, its `board_url` from the Connector or, with the CLI, the link Board links in `calls.md` builds from its `fen`, labelled with the game, as in `[Carlsen–Caruana, 2019, move 29](link)`. Its move number is `ply / 2 + 1`, rounded down. Say how many positions came back and what the call cost.
- **Never** name where the games came from, and never paste a filter's JSON unless they ask for it.
