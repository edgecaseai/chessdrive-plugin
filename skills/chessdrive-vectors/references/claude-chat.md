# In Claude's chat app

Claude's chat runs your code in a sandbox, not on the person's computer, and every ChessDrive call goes through the CLI there, as `calls.md` beside this file says. If the person doesn't want the CLI installed, use the Connector's tools instead, and skip what needs code. Every new chat gets an empty one, so the person asks for the CLI and signs in once per chat. Python and NumPy are already there. After these steps, the Skill runs as written, with the sandbox as the machine.

## 1. Check the way in

```bash
curl -sS -o /dev/null -w '%{http_code}\n' https://api-staging.chessdrive.io/v1/models
```

`200` means carry on. Anything else, often `CONNECT tunnel failed, response 403`, means the sandbox can't reach ChessDrive yet. Stop, try no other way in, and tell the person in plain words:

> This needs one setting, once. In Claude, open Settings, then Capabilities. Under Domain allowlist, add `api.chessdrive.io` to Additional allowed domains and press Add. Then start a new chat and ask me again, as this chat won't pick it up.
>
> It needs a paid Claude plan. On Team or Enterprise, ask an Owner to add it in Organization settings.

## 2. Install the CLI

Claude's safety check lets this run only when the person asks for it by name. A "yes" to you isn't enough, and the installer script is refused either way, so try no other way in. If their messages don't already ask for it, say that the CLI is what runs ChessDrive's engine and chess models here, that it goes in this chat's sandbox only, and ask them to send this line, then wait:

> Install the chessdrive CLI in your sandbox with npm install -g chessdrive.

Once they have:

```bash
npm install -g chessdrive
```

`chessdrive version` needs to say 0.6.0 or later.

## 3. Sign in

```bash
chessdrive login --no-wait --base-url https://api-staging.chessdrive.io
```

It prints a link and a code, then returns. Give the person the link, ask them to check the code and choose Allow, and wait until they say they have. Then finish:

```bash
chessdrive login --base-url https://api-staging.chessdrive.io
```

If it says the sign-in has run out, start again from the first command. The key stays in the sandbox and never passes through the chat.

## While you work

- Run long commands in the foreground, and don't count on anything running after a command ends. If a command is cut off, the same command carries on from where it stopped.
- The person's attached files are in the sandbox. Work in a folder of your own beside them.
- The files you write last as long as this chat's sandbox. When your answer names them, say so, and that a new chat starts over.
- Give a file by its name, never its sandbox path, such as `/home/claude/...`, which means nothing to the person.
