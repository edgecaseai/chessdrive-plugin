# Set up ChessDrive

A person may meet ChessDrive here first, so get them through this in their own agent, in plain words. Don't send them to read the Docs, and don't show them an error. Say which thing is missing and give one step. **Only one:** end your message there, and name the next only once that's done.

## Check, in this order

Stop at the first that's missing, walk them through it, then carry on down the list. Run a check alone, so you stop before the next, and skip those the Skill doesn't need.

1. **Where you are.** In a chat app, Claude's chat app or ChatGPT, the Connector makes every call, as `calls.md` beside this file says: skip steps 2 to 4, ask for no setting or install, and go to step 5. A sandbox there already has Python for the Skills' scripts. Only a Skill that embeds, Patterns, Game search or Vectors, needs more there. In Claude's chat app, follow `claude-chat.md` beside this file for it, instead of steps 2 and 3, which covers the domain step, the CLI and the sign-in. In ChatGPT it can't run, as the Connector has no `embed` tool: say it needs Codex, Claude Code, Cursor or Claude's chat app, and stop. Anywhere else, if the Skill runs code and you can't run a command at all, say what's needed in one line: Claude's chat app, ChatGPT, or an agent that runs code, such as Claude Code (the terminal or the desktop app's Code tab), Codex or Cursor. Then stop.
2. **The CLI,** which makes every ChessDrive call in a coding agent (`calls.md` beside this file). Run `chessdrive version`. If the command isn't found, see [Install the CLI](#install-the-cli). If it's older than 0.6.0, see [Update the CLI](#update-the-cli). If the person says no to installing it, skip to step 5 and use the Connector instead.
3. **The sign-in.** Run `chessdrive balance`, which costs nothing. If it says there's no API key, or that the key was refused, see [Sign in](#sign-in).
4. **Python 3.11 or later with NumPy.** Run `python3 -c "import sys, numpy; assert sys.version_info >= (3, 11)"`. If it fails and `uv` is there, run the scripts with `uv run --python 3.11 --with numpy python`. If Python is older than 3.11, ask them to install the latest from https://www.python.org/downloads/ and tell you when it's done. Otherwise ask whether you can run `python3 -m pip install numpy`, and wait for their yes.
5. **The Connector,** in a chat app, where you can't run code, or when the person said no to the CLI: the tools `engine` and `generate`. If they aren't there, see [Connect](#connect).

## Install the CLI

Say that the CLI is a small program that lets you call ChessDrive's engine and chess models from here, and ask if you can install it. On their yes, run:

```bash
npm install -g chessdrive
```

Without `npm`, run `curl -fsSL https://chessdrive.io/install.sh | sh`, or on Windows give them https://chessdrive.io/docs/cli, which has the download.

If it says its folder isn't on the `PATH`, run the `export` line it prints, and use the same line in each later command.

## Update the CLI

Ask to run `chessdrive update`. If the CLI doesn't have `update`, install it again as above.

## Sign in

Signing in is the person's to do, in their browser, so a key never passes through the chat. It's free, and it makes a ChessDrive account if they have none.

```bash
chessdrive login --no-wait --base-url https://api.chessdrive.io
```

It prints a link and a code, then returns. Give them the link, ask them to check the code and choose Allow, and wait until they say they have. Then finish:

```bash
chessdrive login --base-url https://api.chessdrive.io
```

If it says the sign-in has run out, start again from the first command. If `--no-wait` is an unknown flag, the CLI is too old: update it first. Never ask for a key, or for a password.

## Connect

Say that ChessDrive isn't connected to your app yet, and give them the steps for their app, one at a time. They only do this once.

- **Claude's chat or desktop app:** in a chat, open Customize, then Plugins, then ChessDrive. On its Connectors tab, press Connect, sign in to ChessDrive and pick a daily limit.
- **ChatGPT:** ask them to open Settings, then Plugins, press Add, then Add Custom MCP Server, name it ChessDrive, paste `https://api.chessdrive.io/mcp` and sign in to ChessDrive. If ChessDrive is already in their Plugins, they open it there, press Connect and sign in instead.
- **Claude Code:** the Plugin's Connector uses the key `chessdrive login` saved. Once the CLI is signed in, ask them to type `/mcp`, choose `chessdrive` and press Reconnect. If it isn't listed, ask to run `claude mcp add-json --scope user chessdrive '{"type":"http","url":"https://api.chessdrive.io/mcp","headersHelper":"chessdrive key --headers"}'`, then restart Claude Code.
- **Codex:** ask to add this to `~/.codex/config.toml`, with the full path `command -v chessdrive` gives, then restart Codex:

  ```toml
  [mcp_servers.chessdrive]
  url = "https://api.chessdrive.io/mcp"
  http_headers_helper = "/full/path/to/chessdrive key --headers"
  ```

- **Cursor:** ask to add a `chessdrive` server to `~/.cursor/mcp.json` with `"url": "https://api.chessdrive.io/mcp"` and `"headers": { "Authorization": "Bearer ${env:CHESSDRIVE_CONNECTOR_KEY}" }`, and `export CHESSDRIVE_CONNECTOR_KEY="$(chessdrive key 2>/dev/null)"` in their shell's startup file, then restart Cursor. On Windows, leave out the headers and sign in when Cursor asks.
- **Any other agent:** add `https://api.chessdrive.io/mcp` as a remote MCP server named `chessdrive`, sending `Authorization: Bearer` and the key `chessdrive key` prints, or sign in when it asks.

Then ask them to start a new chat if the tools still don't appear, as some apps load them only at the start.
