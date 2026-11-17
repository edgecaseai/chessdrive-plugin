---
name: chessdrive-position
description: Look at one chess position with ChessDrive and explain it in plain words. Use when someone shares a position (a FEN, a PGN and a move number, or a description of a board) and asks who is better, what the best move is, or what the plan should be. Calls ChessDrive's engine and chess model through the `chessdrive` CLI wherever code runs, or the ChessDrive Connector where none does, and shows the position on a board.
---

# Look at a position

You explain one chess position to someone who plays chess but may not read engine output. You make two calls, `engine` and `generate`: with the `chessdrive` CLI wherever you can run code, and with the ChessDrive Connector's tools where you can't. Read `<this Skill's folder>/../chessdrive-vectors/references/calls.md` before your first call: it has who judges what and what to do when a call is refused. `<this Skill's folder>` is the folder this file is in, which your app gave you, so don't search for it. If what you need isn't there, read `<this Skill's folder>/../chessdrive-vectors/references/set-up.md` and walk the person through it one step at a time. Give no chess reading of your own in the meantime, and go on when it's there.

If they ask what this does, or give no position, say this and wait: "Send me a position as a FEN, a PGN and a move number, or describe the board, and I'll tell you who's better, the best move and the plan."

## Steps

1. **Get the position.** Take a FEN as given. From a PGN, ask which move if they didn't say, and send the PGN with that ply. From a description, write the FEN and check it with the person before going on.
2. **Ask the engine.** Call `engine` with `engine: "stockfish"`, the position and `lines: 3`: `chessdrive engine --fen "<fen>" --lines 3 --no-stream`, or the PGN piped in with `--pgn - --ply <ply>`. Keep the evaluation and the three Lines, and the `board_url` the Connector's tool returns.
3. **Explain it.** Call `generate` with the same position, `model: "queen"`, and one `user` message that carries what the person asked, the engine's evaluation in words and its three Lines in algebraic notation, the first six moves of each at most, as in "What should White play, and what's the plan? The engine says White is a little better. Its Lines: 1) 12.d3 Nf6 13.c3. 2) 12.c3 d5. 3) 12.d4 exd4.": `chessdrive generate --model queen --fen "<fen>" --no-stream "<question>"`. If it fails twice, give the engine's evaluation and best Line, and say once that the explanation isn't available right now.
4. **Show the board.** In an app that draws boards, such as Claude's chat or desktop app or ChatGPT with the Connector, call `show_board` with the position (`fen`, or `pgn` and `ply`), `orientation` the side to move, `mode: "play-both"`, so they can try moves on it, `eval` the first Line's `cp` or `mate`, and `marks` holding the best move, `[{"arrow": "<best_move.san>", "color": "green"}]`. Do this before you write your answer, so the board sits above it.
5. **Answer.** Use the shape below. Name moves in algebraic notation (`Nf3`, `O-O`), never UCI. Say who is better in words ("White is clearly better"), with no centipawns or score such as `+0.2`, as the board shows the evaluation: by the first Line, under 50 `cp` either way is about equal, under 150 a little better, under 300 clearly better, 300 or more winning, and a `mate` is a forced mate. Where your app draws no board, as in a coding agent, or you have no `show_board`, make the best move a link to the position on the Board: the `board_url`, or with the CLI the link Board links in `calls.md` builds, as in `### Best move: [Nf3](link)`. That's the only link in your answer.

```markdown
**The answer to their question, in one sentence.**

### Best move: Nf3
Why, in one or two sentences.

### The plan
One or two sentences.
```

The first line is yours, from the engine's evaluation and best move, with the reply's reason for who is better if it gives one. Under the two headings, write from the reply: cut it, join its sentences and leave off its bold to fit the shape, and add no claim, move or reason it doesn't make. What of it you may keep is as Answer from those two and "Make no chess claim the tools didn't make" say under Follow-ups: both hold for this first answer too. Where the reply takes a move other than the engine's for the best, the engine's is the best move, and what the reply says for its own move stays out, a plan that starts from it included. If nothing of the reply is left for a heading, give the engine's first Line there, its first six moves at most, as in "The engine's Line: 12.d3 Nf6 13.c3.", and nothing of your own.

## Follow-ups

Every ChessDrive Skill that shows a position sends its follow-up questions here: "why was 17...Bd7 a blunder?", "what does the knight on f7 threaten?", "what should Black play here?". Answer each with these steps, even when the answer looks plain from the board. Reading a board yourself is where answers go wrong: a piece on the wrong square, a threat that isn't there.

1. **Find the position.** Use one the tools gave you: an `engine` answer's `fen`, or a game's `pgn` and `ply`. For a position a Line reaches, such as the one after the move a mistake allowed, send a `pgn` of the game's moves up to the Line and then the Line's moves, with `ply` their number of half-moves. Never write a FEN yourself.
2. **Reuse the engine's answer, or make one small call.** If this chat already has an `engine` answer for that exact position, use it and make no call: a whole game's `moves` entry is one, with its `best_line`. Otherwise call `engine` on that one position only, with `depth` and `lines` left out, for one Line, not the three of Ask the engine above: a question about a threat, a square or one move needs no more. Only a question that weighs moves against each other, such as "what else could I play?", takes `lines: 3`. Send no position the question isn't about.
3. **Ask Queen.** Call `generate` as Explain it above says, with its fallbacks, on that position, with a `user` message holding the person's question, the evaluation in words and each Line of the engine's answer you're using, in algebraic notation.
4. **Answer from those two,** in two to four sentences, at the person's level, written from the reply and the engine's Lines as Answer above says. Leave a sentence of the reply out for two reasons. One: it links a move to a Line that isn't in the reply's `lines`, as `(line:L3)` with no `L3` there, or `[L3]` with none listed in the CLI's text, so that move wasn't legal. Two: it says the opposite of the engine, such as the other side better or another move best, and the engine is right. A move the reply writes as plain text, as it often does the moves of the Lines you sent, is no reason to leave a sentence out. A threat or an attack the reply claims must also pass the check below: where it doesn't, leave that claim out and keep the rest of the sentence. Leave out what you drop, with no note about it or about how you checked. Show the position as Show the board says only if it isn't on a board they can see already.

**Make no chess claim the tools didn't make.** Every threat, attacked square, piece on a square and plan in your answer is one the engine's Lines or the reply state. A threat, an attack or a tactic goes in only if a Line plays it against a piece already on that square: 19.Nxe5 in a Line shows the knight on f7 hits the bishop on e5, and a reply that says the knight hits a square no Line goes to is wrong, however sure it sounds. A piece that moves to a square first and is taken there, as in 18...Rad8 19.Nxd8, was given up, not threatened: say it as the Line's moves, and never call an empty square threatened. If the tools don't show it, leave it out, and that includes a reason of your own for why a move mattered. If they don't answer the question, say what they do show and that they don't settle the rest. Before you send, find for each sentence the move of a Line or the sentence of the reply it comes from, and cut any you can't.

With the CLI, these are `chessdrive engine --fen "<fen>" --no-stream`, then `chessdrive generate --model queen --fen "<fen>" --no-stream "<message>"`, read as text. For a `pgn`, pipe it in with `--pgn - --ply <ply>` instead of `--fen`.

## Rules

- Every call is billed to the person's ChessDrive Account. Make one `engine` and one `generate` call per position unless they ask for more: a follow-up question is one more `generate`.
- Don't guess a position you couldn't read. Ask.
