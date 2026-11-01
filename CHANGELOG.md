# Changelog

Each release of the `chessdrive` Plugin bumps `version` in `.claude-plugin/plugin.json` and adds a line here, newest first. People who added the marketplace get it from Check for updates, or `claude plugin marketplace update` and `claude plugin update` in Claude Code. A zip doesn't update: people download it again and upload it.

- **0.8.1** (2026-11-01): The Plugin is on a public repository, `edgecaseai/chessdrive-cli`, as a marketplace, under the MIT license. The README installs from there.
- **0.8.0** (2026-11-01): The Skills show boards in the answer, on `show_board` or in a Study, and link a move only where neither works. Answers read as one list: the answer in bold, then a headline and a sentence or two for each item. The cost comes up only if you ask, or before a run over $1.
- **0.7.4** (2026-11-01): The Skills check many positions in one Engine call instead of one call each, so there's no burst of calls. `chessdrive-game-search` checks up to about 500 positions a question with `chessdrive engine --positions`, which needs CLI 0.3.0, and never runs an engine on your machine.
- **0.7.3** (2026-11-01): The Skills leave `max_tokens` out, so a reply isn't cut short, and carry on without a note when Generate can't answer.
- **0.7.2** (2026-11-01): `chessdrive-patterns`, `chessdrive-game-search` and `chessdrive-vectors` check the CLI's version first, and ask you to update an old one instead of failing partway.
- **0.7.1** (2026-10-31): The author address is now `contact@edgecaselabs.dev`.
- **0.7.0** (2026-10-31): `chessdrive-game-review` opens a Lichess or chess.com link with the Connector's new `get_game` tool, so a pasted link works in Claude Chat. A chess.com link asks for your username once.
- **0.6.1** (2026-10-31): `chessdrive-patterns` quotes about 45 cents when the games come from a Handle.
- **0.6.0** (2026-10-31): `chessdrive-study`: your agent builds you a Study, an interactive page of your own on the Board: a game review, a mistake drill, an opening drill or a worksheet. `chessdrive-game-review` now ends by building one from its answers, with no new calls.
- **0.5.0** (2026-10-31): `chessdrive-game-search`: find examples of an idea across your own PGN files in plain English, check them with the engine, and get a PGN that opens as a Lichess study. Needs an agent that runs code, such as Claude Code, Codex or Cursor.
- **0.4.0** (2026-10-31): `chessdrive-patterns`: find the mistakes you keep making across your last 30 games, grouped on your machine and named in plain words. Needs an agent that runs code, such as Claude Code, Codex or Cursor.
- **0.3.0** (2026-10-30): `chessdrive-vectors`: embed positions and texts to a file on your machine, then find the closest ones or group them with code your agent runs. Needs an agent that runs code, such as Claude Code, Codex or Cursor.
- **0.2.0** (2026-10-30): `chessdrive-game-review`: review a game from a PGN, a Lichess or chess.com link or a Handle, or annotate it for a video or article.
- **0.1.1** (2026-10-30): `chessdrive-position` falls back to Knight on `plan_required` and waits on `429 rate_limited`.
- **0.1.0** (2026-10-29): First release. The Connector, and `chessdrive-position`.
