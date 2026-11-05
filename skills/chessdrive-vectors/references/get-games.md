# Get games into a PGN file

A PGN file is a text file of chess games. Every site can give one, and games on Lichess and chess.com are public.

## Fetch them yourself

When someone asks you to get the games, or gives you a username, go ahead without offering first. It needs the site, so ask for that if they didn't say. It works for any player, so someone preparing for an opponent can name theirs. `fetch_games.py` is in the `scripts` folder beside this file's folder:

```bash
python3 <the scripts folder>/fetch_games.py lichess USERNAME --max 30 --out games.pgn
python3 <the scripts folder>/fetch_games.py chesscom USERNAME --max 30 --out games.pgn
```

It takes their newest games and prints how many it wrote. Use only this script, as it tells the sites what it is. If it says the site has no games for that name, check the spelling with the person.

### Only the games they want

Give the script what the request says, so it downloads only those games:

- **`--speed`** with one or more of `bullet`, `blitz`, `rapid`, `classical` and `correspondence`, comma-separated: "my rapid games" is `--speed rapid`. chess.com has no classical, so there it's the rapid games of 25 minutes or more, and correspondence is its daily games.
- **`--since YYYY-MM-DD`** and **`--until YYYY-MM-DD`,** each day included: "the last two months" is `--since` two months before today.

**Ask for the scope only when it matters.** Unless `--max` keeps it to 500 games or fewer, run the command first with `--how-long` in place of `--out`. It downloads nothing and prints `games` and `seconds`. If `games` is over 500 and the request didn't say which time controls or how far back, ask both in one question, with the count and the time, and fetch with their answer:

> You have 14,530 games on Lichess, about 12 minutes to download. Which time controls should I take, and from how far back?

Don't ask when it's 500 or fewer, or when the request already says, as in "my rapid games from the last two months": go ahead. With `exact: false`, `games` is a guide: with dates, Lichess gives the most there can be, and chess.com counts only rated games.

**If it can't reach the site or is refused, or you can't run code, stop and give the person the link below.** That's how it goes in Claude's chat app, whose sandbox can't reach the sites. Don't go around it: no fetch of your own, no browser, no Claude in Chrome, no script in a page, and never pose as a browser. The link gets them the file in one click. Games in ChessBase need the steps below too.

## Or the person exports them

Ask which site if they didn't say, then give only that site's steps, as they're written here, with the username in the links. Sites change, so never give steps from memory. Wait until they say the file is there. A person never needs to give you a password.

### Lichess

Give them the link on words that say whose games and how many, with the bracket after it:

```markdown
[Your last 30 games](https://lichess.org/api/games/user/USERNAME?max=30) (it downloads by itself)
```

It needs no sign-in, works for any player's username, and a file called `lichess_USERNAME_<date>.pgn` lands in their Downloads folder. Change 30 for more or fewer games, or leave `?max=30` off for all of them. For one time control, add `&perfType=rapid`, or `bullet`, `blitz`, `classical` or `correspondence`, and say so on the words.

To choose the games by date, colour or opponent, sign in to Lichess and open `https://lichess.org/@/USERNAME/download`. Fill in what you want, put the number in Maximum number, and press Download.

### chess.com

1. Sign in to chess.com in your browser. The download doesn't work signed out.
2. Open `https://www.chess.com/games/archive/USERNAME`, your Game History. It also opens for any other player's username.
3. Press the Select All box at the top right of the list. It picks the 50 games on that page.
4. Press the Download button beside it. The file lands in your Downloads folder.

**With no sign-in,** give them one month's games on words, with the username in lowercase and the month as `2026/10`:

```markdown
[Your October games](https://api.chess.com/pub/player/username/games/YYYY/MM/pgn) (it downloads by itself)
```

It's the whole month, and a month that has just started may hold few games. For more, give another month too.

### ChessBase

1. In the Application Menu (the File menu in older versions), choose New, then Database.
2. At the bottom of the dialog, pick PGN as the file type. Name it `my-games.pgn`, and save it somewhere you'll find it.
3. Open the database that holds your games, click a game in the list, and press Ctrl+A to select them all.
4. Drag them onto the new database's icon, or press Ctrl+C, open the new database and press Ctrl+V. ChessBase turns them into PGN as they're copied.

### When they have it

- **A coding agent:** ask where it is. It's usually their Downloads folder. Ask before you look there, then copy it into the folder you're working in.
- **Claude's chat app:** ask them to attach the file to this chat.

Check a file they exported before you spend anything. A PGN file starts with `[Event `, and this counts its games:

```bash
grep -c '^\[Event ' games.pgn
```

If it says 0, or the file starts with `<`, it's an error page and not a PGN: say so, and go through the steps again. Several files can be joined with `cat one.pgn two.pgn > games.pgn`. The person's name in the file is their username on that site, in the `White` and `Black` tags.
