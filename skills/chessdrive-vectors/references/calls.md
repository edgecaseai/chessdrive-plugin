# Call ChessDrive

The Skills name their calls `engine` and `generate`, with the Connector's fields. **Wherever you can run code, make them with the `chessdrive` CLI**: on the person's machine, or in Claude's chat app's sandbox once `claude-chat.md` beside this file is done. Use the Connector's tools of the same name only where you can't run code, or when the person said no to installing the CLI. `set-up.md` beside this file checks for the CLI, at 0.6.0 or later, and signs it in. Every Skill reads this file before its first call.

**Read the CLI's text** for a call you answer from, such as one position. **Add `--json` only when code reads the answer**: write it to a file, and read the file with code, never by eye.

## Engine

**One position runs on the person's own Stockfish, free; deep and bulk work runs on the Engine API, billed.** The CLI picks: one position, from `--fen` or `--pgn` with `--ply`, below `--depth 20` runs on the Stockfish installed on their machine, at depth 18 when you give no depth. `--depth 20` and up, `--positions`, `--games` and a whole game go to the Engine API. Ask for depth 20 or more only when the person asks for a deep search, and never add `--api` yourself. If the CLI says there's no Stockfish, the answer still came, billed: pass on its install line once, such as `brew install stockfish` on macOS, and go on. The Connector's `engine` tool always runs on the Engine API.

| The Skill asks for | Run |
|---|---|
| One position, from a FEN | `chessdrive engine --fen "<fen>" --no-stream` |
| One position of a game | `printf '%s' "$pgn" \| chessdrive engine --pgn - --ply <ply> --no-stream`, or `--pgn game.pgn` for a file |
| `lines: 3`, `depth: 10` | add `--lines 3`, `--depth 10` |
| A whole game, no `ply` | `chessdrive engine --pgn game.pgn --json > review.json`, then read `moves` from it with code |
| `positions`, several at once | one position a line in a file, `{"fen": "<fen>"}` or `{"pgn": "<pgn>", "ply": <ply>}`, then `chessdrive engine --positions list.jsonl --out results.jsonl`: line 7 of the results answers line 7 of the list |
| Several whole games | `chessdrive engine --games games.pgn --out answers.jsonl`: a line a game, in the file's order, with its `game`, `status`, `tags`, `pgn` and `moves` |

One position prints a line per Line: its rank, its score from White's side in pawns (`+0.34`, or `#3` for a mate), then its moves, numbered. `Best move:` follows. `--positions` and `--games` send as many calls at once as the Plan allows, wait out `rate_limited` themselves, and carry on after a stop without billing anything twice, so never run positions or games one by one yourself.

## Generate

```bash
printf '%s' "$pgn" | chessdrive generate --model queen --pgn - --ply <ply> --no-stream --system "<system>" "<message>"
```

Use `--fen "<fen>"` for a FEN, and leave the position out for a question with none. For a conversation, `--messages chat.json` takes a JSON list of `{"role", "content"}`. Leave `--max-tokens` out: the Model's thinking counts toward it, so a low cap cuts the reply short or loses it.

The reply marks each Line it names, as in `14...Nf6 [L1]`, and lists the Lines after it, each with its moves, as `L1  14...Nf6 15.Qe2 O-O`. Those are the moves that passed as legal: where a Skill speaks of `lines` and of links such as `[text](line:L1)`, read these. A move the reply names that isn't in a listed Line was illegal, so drop that sentence.

**Two or more calls that don't use each other's answers go together, up to 6 at once,** the most whose engine notes ChessDrive keeps: more than 6 and the notes behind the replies are skipped. Start them as soon as the engine has answered, and build any page while they run. With the CLI, write one call a line and run `ask.py`, in the background when you have a page to build:

```bash
python3 <this Skill's folder>/../chessdrive-vectors/scripts/ask.py questions.jsonl --out answers.jsonl
```

A line is `{"id": "14...Qd7", "model": "queen", "system": "<system>", "message": "<message>", "pgn": "<pgn>", "ply": 27}`, with `"fen"` for a bare position. An answer has `id`, `model`, `text`, the reply with its moves as plain text and any sentence with an illegal move dropped, and `lines`. It retries as below, gives `"text": null` and the `error` for a call that failed twice, and bills nothing twice when run again. With the Connector, make up to 6 tool calls in one message.

## Our models judge

Every chess judgement you give, in your answer, a page or a note, comes from ChessDrive: whether a move is good or bad, what a position is about, whether a position shows an idea, and why. You plan, pick, combine and write. You never judge from your own reading of the board, and never fill a gap with your own words.

- **The engine** gives every evaluation, verdict and Line.
- **Queen** explains what the person reads as prose, and answers their questions.
- **Knight,** cheap and quick, does the bulk, many calls at once: a line on each of many moves, whether a position shows the idea asked for, a group's name, a short summary.
- Use a model's reply word for word, by code where it goes in a file. Never reword it or add to it. Name only moves the tools gave you, copied exactly. Where a reply and the engine disagree, the engine is right, so drop that sentence.
- A note no model gave, after its retry, says so where it would stand, as in `{ Mistake. No explanation: the chess model didn't answer. }`, and your answer says how many. Never fill one in.
- **A question about a position** they saw, such as "why was that a blunder?" or "what does the knight on f7 threaten?": answer it as Follow-ups in `<this Skill's folder>/../chessdrive-position/SKILL.md` says. Reuse an `engine` answer you have for that position.

## When a call is refused

The CLI prints the API's code and message, and exits with a code of its own. Do as the Skill says for `limit_too_high` and `daily_limit_reached`, and for the rest:

- `plan_required`: Queen's calls on Free are used up for now, so make that call and the rest with Knight (`ask.py` does), and say so in one line.
- `429 rate_limited`: wait for `Retry-After`, the `retry after` in seconds, then make the same call again.
- `upstream_unavailable`, or a reply cut short: make the same call once more, then label it as above.
- **The Balance is empty:** pass on its message and its link to Pricing, give what you already have, and stop.

## Only the Connector

- **`show_board`,** a board drawn in Claude's chat or desktop app. Where code runs, a Study, a page of the `chessdrive-study` Skill, does its work, so call `show_board` only where the Skill says no Study can show.
- **`get_game`,** in Claude's chat app, whose sandbox can't reach Lichess or chess.com. Everywhere else, `fetch_games.py --url` in this Skill's `scripts` folder gets the game.

## Board links

The CLI gives no `board_url`. Where a Skill links a position to the Board and no Study shows it, build the link from the position with code, as in `python3 -c 'import sys, urllib.parse as u; print("https://platform.chessdrive.io/board#fen=" + u.quote_plus(sys.argv[1]))' "<fen>"`, or for a game `#pgn=<pgn>&ply=<ply>`, each quoted the same way.
