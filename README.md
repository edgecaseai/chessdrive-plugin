# ChessDrive

Chess Skills for your agent. Where your agent runs code, they call ChessDrive through its CLI; in a chat that runs none, through the ChessDrive Connector. Ask about a position, a game or a player in plain words; the Skills use ChessDrive's engine, chess models and game corpus to answer, and show you a board.

This is the edition of the ChessDrive plugin for Claude's plugin directory. It has every Skill. The directory takes no script files and no sign-in helper, so it differs from the plugin on [our own repository](https://github.com/edgecaseai/chessdrive-plugin) in two ways, both set out under [What it runs and sends](#what-it-runs-and-sends): its Python scripts are held as text and written out before they run, and the Connector signs in through your browser.

## Connect

After you add ChessDrive, connect it and sign in. In Claude's chat or desktop app, open the plugin's Connectors tab and connect ChessDrive. In Claude Code, run `/mcp` and choose ChessDrive. Signing in connects your ChessDrive Account, or makes one. Calls are billed to its Balance, as API calls are.

## The CLI

The Skills that run code use the `chessdrive` CLI, which you install and sign in to yourself. Your agent asks before it installs anything. On Windows, follow [the CLI docs](https://platform.chessdrive.io/docs/cli).

```bash
npm install -g chessdrive
chessdrive login
```

Without npm, `curl -fsSL https://platform.chessdrive.io/install.sh | sh`. In Claude Code the CLI's sign-in and the Connector's are two sign-ins, to the same Account.

## Skills

- `chessdrive-position`: look at one position and explain it.
- `chessdrive-game-review`: review a finished game, or annotate it for a video or article.
- `chessdrive-prep`: prepare for a game against one opponent, from a PGN file of their games or their public Lichess and chess.com games: what they play against your colour, their recent form and a plan. It runs where your agent runs code.
- `chessdrive-vectors`: embed positions and texts to a file on your machine, then find the closest ones or group them. It needs an agent that runs code there, such as Claude Code (the terminal or the desktop app's Code tab), with the `chessdrive` CLI.
- `chessdrive-patterns`: find the mistakes you keep making across your last 30 games. It runs in an agent that runs code, with the `chessdrive` CLI, or in Claude's chat app on a paid plan, once you've added `api.chessdrive.io` under Settings, Capabilities, Domain allowlist.
- `chessdrive-game-search`: find examples of an idea across your own PGN files, in plain English, checked with the engine and returned as a PGN. It runs where `chessdrive-patterns` does.
- `chessdrive-study`: have your agent build you a Study, an interactive page of your own on the Board: a game to step through, a drill of your mistakes, an opening line to practise or a worksheet to print. It's an artifact in Claude and a local file in a coding agent.

## What it runs and sends

- **Scripts, held as text:** the Skills that run code use Python scripts. Each one is in this plugin as a Markdown file, `<name>.py.md` in its Skill's `scripts` folder, holding the script's whole text, which you can read here. Before a Skill runs one, your agent runs one command, in `skills/chessdrive-vectors/references/unpack.md`, that copies the Skills to `~/.cache/chessdrive/skills` and writes each script there as a `.py` file. Your agent then runs them with `python3`, as the Skill says. Nothing runs when you install the plugin, and nothing runs without your agent's usual permission to run a command.
- **What the scripts do:** they read your PGN files and write files in your working folder: counts of an opponent's openings, vector files, groups, PGNs of examples and Study pages. `fetch_games.py` downloads a player's public games from lichess.org and chess.com when you give a username or a game link. The scripts that need the engine, the chess models or Embed call ChessDrive through the `chessdrive` CLI, and `check.py` runs `node --check` on a Study page where Node is installed. None of them reaches any other host.
- **ChessDrive calls:** the Skills send positions, games and questions to `api.chessdrive.io`, through the CLI or the Connector, signed in as your ChessDrive Account. Nothing else leaves your machine for ChessDrive: your PGN files and the files the Skills write stay where the code runs.
- **Sign-in:** the Connector signs in with OAuth in your browser. The plugin holds no key and reads none from your machine.
- **Study pages:** a Study loads the ChessDrive Board from cdn.jsdelivr.net, its fonts from fonts.googleapis.com and, when you turn its engine on, Stockfish from unpkg.com.

Privacy: [platform.chessdrive.io/legal/privacy](https://platform.chessdrive.io/legal/privacy).

## Updates

What changed in each version is in [CHANGELOG.md](CHANGELOG.md).

## License

MIT, in [LICENSE](LICENSE). This edition is built from the ChessDrive plugin, and its version follows the plugin's. Write to contact@edgecaselabs.dev.
