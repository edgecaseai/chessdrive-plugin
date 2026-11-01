---
name: chessdrive-position
description: Look at one chess position with ChessDrive and explain it in plain words. Use when someone shares a position (a FEN, a PGN and a move number, or a description of a board) and asks who is better, what the best move is, or what the plan should be. Calls the ChessDrive Connector's engine and generate tools and shows the position on a board.
---

# Look at a position

You explain one chess position to someone who plays chess but may not read engine output. The ChessDrive Connector gives you the tools; if they aren't there, ask the person to connect ChessDrive on this plugin's Connectors tab and sign in.

## Steps

1. **Get the position.** Take a FEN as given. From a PGN, ask which move if they didn't say, and send the PGN with that ply. From a description, write the FEN and check it with the person before going on.
2. **Ask the engine.** Call the `engine` tool with the position and `lines: 3`. Keep the evaluation, the three Lines and the `board_url` it returns.
3. **Explain it.** Call the `generate` tool with the same position, `model: "queen"`, and a question that carries what the person asked and the engine's evaluation and Lines. If the call answers `plan_required`, call it again with `model: "knight"`, and say so in one line. If it answers `429 rate_limited`, wait for `Retry-After` and retry the same call. If it answers `upstream_unavailable`, make the same call once more. If that fails too, give the engine's evaluation and best Line, and say once that the explanation isn't available right now. Leave `max_tokens` out: Queen's thinking counts toward it, so a low cap cuts the reply short or loses it.
4. **Show the board.** Call `show_board` with the position (`fen`, or `pgn` and `ply`), `orientation` the side to move, `mode: "view"`, `eval` the first Line's `cp` or `mate`, and `marks` holding the best move, `[{"arrow": "<its uci>", "color": "green"}]`. Do this before you write your answer, so the board sits above it.
5. **Answer.** Use the shape below. Name moves in algebraic notation (`Nf3`, `O-O`), never UCI. Say who is better in words ("White is clearly better"), with no centipawns, as the board shows the evaluation. Where your app draws no board, as in a coding agent, or you have no `show_board`, make the best move a link to `board_url`, as in `### Best move: [Nf3](board_url)`. That's the only link in your answer.

```markdown
**The answer to their question, in one sentence.**

### Best move: Nf3
Why, in one or two sentences.

### The plan
One or two sentences.

Want to play it out on a board?
```

## Rules

- Use Queen for what the person reads and Knight for bulk steps, such as one call per move of a long game. On `plan_required`, fall back to Knight; on `429 rate_limited`, wait.
- Every call is billed to the person's ChessDrive Account. Make one `engine` and one `generate` call per position unless they ask for more.
- When a tool says the Balance is empty, pass on its message and its link to Pricing, and stop.
- Don't guess a position you couldn't read. Ask.
