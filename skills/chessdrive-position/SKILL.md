---
name: chessdrive-position
description: Look at one chess position with ChessDrive and explain it in plain words. Use when someone shares a position (a FEN, a PGN and a move number, or a description of a board) and asks who is better, what the best move is, or what the plan should be. Calls the ChessDrive Connector's engine and generate tools and shows the position on a board.
---

# Look at a position

You explain one chess position to someone who plays chess but may not read engine output. The ChessDrive Connector gives you the tools. If they aren't there, read Connect in `<this Skill's folder>/../chessdrive-vectors/references/set-up.md`, where `<this Skill's folder>` is the folder this file is in, which your app gave you, so don't search for it, and walk the person through it one step at a time. Give no chess reading of your own in the meantime, and go on when the tools are there.

If they ask what this does, or give no position, say this and wait: "Send me a position as a FEN, a PGN and a move number, or describe the board, and I'll tell you who's better, the best move and the plan."

## Steps

1. **Get the position.** Take a FEN as given. From a PGN, ask which move if they didn't say, and send the PGN with that ply. From a description, write the FEN and check it with the person before going on.
2. **Ask the engine.** Call the `engine` tool with the position and `lines: 3`. Keep the evaluation, the three Lines and the `board_url` it returns.
3. **Explain it.** Call the `generate` tool with the same position, `model: "queen"`, and a question that carries what the person asked and the engine's evaluation and Lines. If the call answers `plan_required`, call it again with `model: "knight"`, and say so in one line. If it answers `429 rate_limited`, wait for `Retry-After` and retry the same call. If it answers `upstream_unavailable`, make the same call once more. If that fails too, give the engine's evaluation and best Line, and say once that the explanation isn't available right now. Leave `max_tokens` out: Queen's thinking counts toward it, so a low cap cuts the reply short or loses it.
4. **Show the board.** Call `show_board` with the position (`fen`, or `pgn` and `ply`), `orientation` the side to move, `mode: "play-both"`, so they can try moves on it, `eval` the first Line's `cp` or `mate`, and `marks` holding the best move, `[{"arrow": "<best_move.san>", "color": "green"}]`. Do this before you write your answer, so the board sits above it.
5. **Answer.** Use the shape below. Name moves in algebraic notation (`Nf3`, `O-O`), never UCI. Say who is better in words ("White is clearly better"), with no centipawns or score such as `+0.2`, as the board shows the evaluation. Where your app draws no board, as in a coding agent, or you have no `show_board`, make the best move a link to `board_url`, as in `### Best move: [Nf3](board_url)`. That's the only link in your answer.

```markdown
**The answer to their question, in one sentence.**

### Best move: Nf3
Why, in one or two sentences.

### The plan
One or two sentences.
```

## Follow-ups

Every ChessDrive Skill that shows a position sends its follow-up questions here: "why was 17...Bd7 a blunder?", "what does the knight on f7 threaten?", "what should Black play here?". Answer each with these steps, even when the answer looks plain from the board. Reading a board yourself is where answers go wrong: a piece on the wrong square, a threat that isn't there.

1. **Find the position.** Use one the tools gave you: an `engine` answer's `fen`, or a game's `pgn` and `ply`. For a position a Line reaches, such as the one after the move a mistake allowed, send a `pgn` of the game's moves up to the Line and then the Line's moves, with `ply` their number of half-moves. Never write a FEN yourself.
2. **Reuse the engine's answer, or make one small call.** If this chat already has an `engine` answer for that exact position, use it and make no call: a whole game's `moves` entry is one, with its `best_line`. Otherwise call `engine` on that one position only, with `depth` and `lines` left out, for one Line, not the three of Ask the engine above: a question about a threat, a square or one move needs no more. Only a question that weighs moves against each other, such as "what else could I play?", takes `lines: 3`. Send no position the question isn't about.
3. **Ask Queen.** Call `generate` as Explain it above says, with its fallbacks, on that position, with a `user` message holding the person's question, the evaluation in words and each Line in algebraic notation.
4. **Answer from those two,** in two to four sentences, at the person's level. Name only moves from the engine's Lines or the reply's `lines`: a move the reply names that isn't in `lines` was illegal, so drop that sentence. Where the reply and the engine disagree, the engine is right. Leave out what you drop, with no note about it or about how you checked. Show the position as Show the board says only if it isn't on a board they can see already.

**Make no chess claim the tools didn't make.** Every threat, attacked square, piece on a square and plan in your answer is one the engine's Lines or the reply state. A threat, an attack or a tactic goes in only if a Line plays it against a piece already on that square: 19.Nxe5 in a Line shows the knight on f7 hits the bishop on e5, and a reply that says the knight hits a square no Line goes to is wrong, however sure it sounds. A piece that moves to a square first and is taken there, as in 18...Rad8 19.Nxd8, was given up, not threatened: say it as the Line's moves, and never call an empty square threatened. If the tools don't show it, leave it out, and that includes a reason of your own for why a move mattered. If they don't answer the question, say what they do show and that they don't settle the rest. Before you send, find for each sentence the move of a Line or the sentence of the reply it comes from, and cut any you can't.

With no Connector, the CLI makes the same two calls: `chessdrive engine --fen "<fen>" --no-stream --json`, then `chessdrive generate --model queen --fen "<fen>" --no-stream "<message>"`. For a `pgn`, pipe it in with `--pgn - --ply <ply>` instead of `--fen`.

## Rules

- Every call is billed to the person's ChessDrive Account. Make one `engine` and one `generate` call per position unless they ask for more.
- When a tool says the Balance is empty, pass on its message and its link to Pricing, and stop.
- Don't guess a position you couldn't read. Ask.
