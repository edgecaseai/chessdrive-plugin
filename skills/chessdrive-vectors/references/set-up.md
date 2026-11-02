# Set up ChessDrive

A person may meet ChessDrive here first, so get them through this in their own agent, in plain words. Don't send them to read the Docs, and don't show them an error. Say which thing is missing and give one step. **Only one:** end your message there, and name the next only once that's done.

## Check, in this order

Stop at the first that's missing, walk them through it, then carry on down the list. Run a check alone, so you stop before the next, and skip those the Skill doesn't need.

1. **Somewhere to run code.** If you can't run a command at all, say what's needed in one line: Claude's chat app on a paid plan, or an agent that runs code, such as Claude Code (the terminal or the desktop app's Code tab), Codex or Cursor. Then stop. In Claude's chat app, follow `claude-chat.md` beside this file instead of steps 2 and 3, which covers the domain step, the CLI and the sign-in.
2. **The CLI.** Run `chessdrive version`. If the command isn't found, see [Install the CLI](#install-the-cli). If it's older than the Skill needs, see [Update the CLI](#update-the-cli).
3. **The sign-in.** Run `chessdrive balance`, which costs nothing. If it says there's no API key, or that the key was refused, see [Sign in](#sign-in).
4. **Python 3.11 or later with NumPy.** Run `python3 -c "import sys, numpy; assert sys.version_info >= (3, 11)"`. If it fails and `uv` is there, run the scripts with `uv run --python 3.11 --with numpy python`. If Python is older than 3.11, ask them to install the latest from https://www.python.org/downloads/ and tell you when it's done. Otherwise ask whether you can run `python3 -m pip install numpy`, and wait for their yes.
5. **The Connector,** if the Skill needs it: the tools `engine` and `generate`. If they aren't there, see [Connect](#connect).

## Install the CLI

Say that the CLI is a small program that lets you call ChessDrive from here, and ask if you can install it. On their yes, run:

```bash
curl -fsSL https://platform-staging.chessdrive.io/install.sh | sh
```

On Windows, run `npm install -g chessdrive` if `npm` is there. Otherwise give them https://platform-staging.chessdrive.io/docs/cli, which has the download.

If it says its folder isn't on the `PATH`, run the `export` line it prints, and use the same line in each later command.

## Update the CLI

Ask to run `chessdrive update`. If the CLI doesn't have `update`, install it again as above.

## Sign in

Signing in is the person's to do, in their browser, so a key never passes through the chat. It's free, and it makes a ChessDrive account if they have none.

```bash
chessdrive login --no-wait --base-url https://api-staging.chessdrive.io
```

It prints a link and a code, then returns. Give them the link, ask them to check the code and choose Allow, and wait until they say they have. Then finish:

```bash
chessdrive login --base-url https://api-staging.chessdrive.io
```

If it says the sign-in has run out, start again from the first command. If `--no-wait` is an unknown flag, the CLI is too old: update it first. Never ask for a key, or for a password.

## Connect

Say that ChessDrive isn't connected to your app yet, and give them the steps for their app, one at a time. They only do this once.

- **Claude's chat or desktop app:** in a chat, open Customize, then Plugins, then ChessDrive. On its Connectors tab, press Connect, sign in to ChessDrive and pick a daily limit.
- **Claude Code:** type `/mcp`, choose `chessdrive` and sign in. If it isn't listed, ask to run `claude mcp add --transport http --scope user chessdrive https://api-staging.chessdrive.io/mcp`, then restart Claude Code and try again.
- **Any other agent:** add `https://api-staging.chessdrive.io/mcp` as a remote MCP server named `chessdrive`, then sign in when it asks.

Then ask them to start a new chat if the tools still don't appear, as some apps load them only at the start.
