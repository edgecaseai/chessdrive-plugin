# Call ChessDrive

The Skills name their calls `engine` and `generate`, with the Connector's fields. **Wherever you can run code, make them with the `chessdrive` CLI**: on the person's machine, or in Claude's chat app's sandbox once `claude-chat.md` beside this file is done. Use the Connector's tools of the same name only where you can't run code, or when the person said no to installing the CLI. `set-up.md` beside this file checks for the CLI, at 0.6.0 or later, and signs it in.

**Read the CLI's text** for a call you answer from, such as one position. **Add `--json` only when code reads the answer**: write it to a file, and read the file with code, never by eye.

## Engine

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

## When a call is refused

The CLI prints the API's code and message, and exits with a code of its own. Do what the Skill says for that code: `plan_required`, `rate_limited`, which gives a `retry after` in seconds, `upstream_unavailable`, `limit_too_high`, `daily_limit_reached`, or the Balance being empty, whose message has the link to Pricing.

## Only the Connector

- **`show_board`,** a board drawn in Claude's chat or desktop app. Where code runs, a Study, a page of the `chessdrive-study` Skill, does its work, so call `show_board` only where the Skill says no Study can show.
- **`get_game`,** in Claude's chat app, whose sandbox can't reach Lichess or chess.com. Everywhere else, `fetch_games.py --url` in this Skill's `scripts` folder gets the game.

## Board links

The CLI gives no `board_url`. Where a Skill links a position to the Board and no Study shows it, build the link from the position with code, as in `python3 -c 'import sys, urllib.parse as u; print("https://platform-staging.chessdrive.io/board#fen=" + u.quote_plus(sys.argv[1]))' "<fen>"`, or for a game `#pgn=<pgn>&ply=<ply>`, each quoted the same way.
