# ChessDrive for Claude

Chess Skills for your agent, and the ChessDrive Connector they call. Ask about a position, a game or a player in plain words; the Skills use ChessDrive's engine, chess models and game corpus to answer, and show you a board.

## Install

- **Claude:** Customize → Plugins → Add → Add marketplace → Add from a repository. Enter `edgecaseai/chessdrive-plugin`, press Sync and install ChessDrive. Then, in a Chat, open the plugin's Connectors tab, connect ChessDrive and sign in.
- **Claude Code:** install the CLI and sign in once, then add the Plugin. Its Connector uses the key `chessdrive login` saves, so there's no second sign-in.

  ```bash
  npm install -g chessdrive
  chessdrive login
  claude plugin marketplace add edgecaseai/chessdrive-plugin
  claude plugin install chessdrive@chessdrive
  ```

- **Cursor, Codex and other agents:** paste the setup prompt from [Add ChessDrive to your AI](https://platform-staging.chessdrive.io/cookbook/add-to-your-ai).

Signing in connects your ChessDrive Account. Calls are billed to its Balance, as API calls are.

## The CLI

The Skills that run code use the `chessdrive` CLI. On Windows, follow [the CLI docs](https://platform-staging.chessdrive.io/docs/cli).

```bash
npm install -g chessdrive
chessdrive login
```

Without npm, `curl -fsSL https://platform-staging.chessdrive.io/install.sh | sh`.

## Skills

- `chessdrive-position`: look at one position and explain it.
- `chessdrive-game-review`: review a finished game, or annotate it for a video or article.
- `chessdrive-vectors`: embed positions and texts to a file on your machine, then find the closest ones or group them. It needs an agent that runs code there, such as Claude Code (the terminal or the desktop app's Code tab), Codex or Cursor, with the `chessdrive` CLI; it doesn't work in Claude's chat app.
- `chessdrive-patterns`: find the mistakes you keep making across your last 30 games. It runs in an agent that runs code, with the `chessdrive` CLI, or in Claude's chat app on a paid plan, once you've added `api.chessdrive.io` under Settings, Capabilities, Domain allowlist.
- `chessdrive-game-search`: find examples of an idea across your own PGN files, in plain English, checked with the engine and returned as a PGN. It runs where `chessdrive-patterns` does.
- `chessdrive-study`: have your agent build you a Study, an interactive page of your own on the Board: a game to step through, a drill of your mistakes, an opening line to practise or a worksheet to print. It's an artifact in Claude and a local file in a coding agent.

## Updates

What changed in each version is in [CHANGELOG.md](CHANGELOG.md). In Claude, use Check for updates. In Claude Code:

```bash
claude plugin marketplace update chessdrive
claude plugin update chessdrive@chessdrive
```

## License

MIT, in [LICENSE](LICENSE). Each release replaces this repository's files, so a pull request here wouldn't last. Write to contact@edgecaselabs.dev instead.
