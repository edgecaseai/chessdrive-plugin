# ChessDrive

Chess Skills for your agent. Where your agent runs code, they call ChessDrive through its CLI; in a chat that runs none, through the ChessDrive Connector. Ask about a position, a game or a player in plain words; the Skills use ChessDrive's engine, chess models and game corpus to answer, and show you a board.

## Install

- **Claude:** Customize → Plugins → Add → Add marketplace → Add from a repository. Enter `edgecaseai/chessdrive-plugin`, press Sync and install ChessDrive. Then, in a Chat, open the plugin's Connectors tab, connect ChessDrive and sign in.
- **Claude Code:** install the CLI and sign in once, then add the Plugin. Its Connector uses the key `chessdrive login` saves, so there's no second sign-in.

  ```bash
  npm install -g chessdrive
  chessdrive login
  claude plugin marketplace add edgecaseai/chessdrive-plugin
  claude plugin install chessdrive@chessdrive
  ```

- **ChatGPT:** once ChessDrive is in ChatGPT's plugin directory, open Plugins, find ChessDrive, add it and sign in. Until then, add `https://api.chessdrive.io/mcp` as a custom MCP server, which brings the Connector's tools without the Skills.
- **Cursor, Codex and other agents:** paste the setup prompt from [Add ChessDrive to your AI](https://platform.chessdrive.io/cookbook/add-to-your-ai).

Signing in connects your ChessDrive Account. Calls are billed to its Balance, as API calls are.

## The CLI

The Skills that run code use the `chessdrive` CLI. On Windows, follow [the CLI docs](https://platform.chessdrive.io/docs/cli).

```bash
npm install -g chessdrive
chessdrive login
```

Without npm, `curl -fsSL https://platform.chessdrive.io/install.sh | sh`.

## Skills

- `chessdrive-position`: look at one position and explain it.
- `chessdrive-game-review`: review a finished game, or annotate it for a video or article.
- `chessdrive-prep`: prepare for a game against one opponent, from a PGN file of their games or their public Lichess and chess.com games: what they play against your colour, their recent form and a plan. It runs where your agent runs code.
- `chessdrive-vectors`: embed positions and texts to a file on your machine, then find the closest ones or group them. It needs an agent that runs code there, such as Claude Code (the terminal or the desktop app's Code tab), Codex or Cursor, with the `chessdrive` CLI; it doesn't work in Claude's chat app.
- `chessdrive-patterns`: find the mistakes you keep making across your last 30 games. It runs in an agent that runs code, with the `chessdrive` CLI, or in Claude's chat app on a paid plan, once you've added `api.chessdrive.io` under Settings, Capabilities, Domain allowlist.
- `chessdrive-game-search`: find examples of an idea across your own PGN files, in plain English, checked with the engine and returned as a PGN. It runs where `chessdrive-patterns` does.
- `chessdrive-study`: have your agent build you a Study, an interactive page of your own on the Board: a game to step through, a drill of your mistakes, an opening line to practise or a worksheet to print. It's an artifact in Claude and a local file in a coding agent.

## What it runs and sends

- **ChessDrive calls:** the Skills send positions, games and questions to `api.chessdrive.io`, through the CLI or the Connector, signed in as your ChessDrive Account. Nothing else leaves your machine for ChessDrive: your PGN files and the files the Skills write stay where the code runs.
- **Scripts:** the Skills that run code use the Python scripts in their `scripts` folders, which you can read here. They read and write files in your working folder. `fetch_games.py` downloads a player's public games from lichess.org and chess.com when you give a username or a game link, and the others make no network calls of their own.
- **Study pages:** a Study loads the ChessDrive Board from cdn.jsdelivr.net, its fonts from fonts.googleapis.com and, when you turn its engine on, Stockfish from unpkg.com.
- **Claude Code:** the Plugin's Connector reads the key `chessdrive login` saved on your machine and sends it only to `api.chessdrive.io`, so you sign in once.

## Updates

What changed in each version is in [CHANGELOG.md](CHANGELOG.md). In Claude, use Check for updates. In Claude Code:

```bash
claude plugin marketplace update chessdrive
claude plugin update chessdrive@chessdrive
```

## License

MIT, in [LICENSE](LICENSE). Each release replaces this repository's files, so a pull request here wouldn't last. Write to contact@edgecaselabs.dev instead.
