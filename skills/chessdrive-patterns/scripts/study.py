#!/usr/bin/env python3
"""The groups whose names hold, three examples each with a Knight line, and the Study that shows them. Python 3.11 or
later, with the `chessdrive` CLI signed in.

    python3 study.py patterns --rating 1612

Reads groups.json, which groups.py wrote, and names.json, Queen's name for each group, which you write, a group to an
object:

    [{"group": 1, "name": "Moving the piece that guarded another", "check": "Before you move a piece, ask what it guarded."}]

Knight checks each name against its group's examples, one call an example, and a group stays only if at least MIN_FIT
of them show it. It shows the first SHOWN that do, each from a different game, each with one more Knight call saying
what the move allowed, from the engine's Lines. The calls run AT_ONCE at a time. Answers are kept in explained.json, so
running it again bills no call twice. Writes the Study, your-mistakes.html, in the frame of the chessdrive-study Skill
beside this one, with its "Ask about this position" card, unless no group is kept, and prints one JSON object a line:
each group kept, then the totals.
"""

import argparse
import html
import json
import re
import subprocess
import sys
import textwrap
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.dont_write_bytecode = True  # keeps the Plugin's folder as it was installed

STUDY = Path(__file__).resolve().parent.parent.parent / "chessdrive-study" / "references"

MIN_FIT = 3
SHOWN = 3
CHECKED = 5  # the examples a name is checked against; a drill's groups.py --examples 10 keeps them first
EXIT_RATE_LIMITED = 5
RETRIES = 5
RETRY_SECONDS = 5
TRIES = 2  # Knight's answers, before an example shows the engine's Line, labelled
AT_ONCE = 6  # the most calls whose engine notes ChessDrive keeps

SYSTEM = (
    "You explain one chess mistake to a player{rating}. In one plain sentence of at most 25 words, say what the move "
    "allowed, as the engine's line shows it: what the other side wins or threatens, and how. The mistake was grouped "
    "under a name you are given: where the line shows that idea, let the sentence show it through the moves, and "
    "never quote the name, say the mistake fits it, or mention the group. Name a piece as won only if a move of the "
    "line takes it. Use only the moves you are given, written as given, and no numbers, scores or evaluations."
)
FIT_SYSTEM = (
    "You check whether one chess mistake shows the idea a group of mistakes was named for. Answer \"yes\" or \"no\" "
    "first, then say why in one sentence, from the moves and the engine's lines you are given."
)
LINK = re.compile(r"\[([^\]]*)\]\(line:([^)\s]+)\)")
# A move a reply names: a piece's move or any capture, or castling. A bare square such as "e4" may be a square.
NAMED = re.compile(r"(?<![\w.])(?:[KQRBN][a-h]?[1-8]?x?[a-h][1-8]|[a-h]x[a-h][1-8](?:=[QRBN])?|O-O(?:-O)?)")
NUMBER = re.compile(r"[+−-]\s?\d|\d\s?(?:%|centipawn|pawns? up)|\bcp\b", re.I)


def plain(san):
    return san.rstrip("+#?!")


def numbered(ply, sans, count):
    """Moves of a Line from the position `ply` half-moves in, as an answer writes them: 18...Rxd3 19.Qe2 Rxe2."""
    out = []
    for i, san in enumerate(sans[:count]):
        at = ply + i
        if at % 2 == 0:
            out.append(f"{at // 2 + 1}.{san}")
        else:
            out.append(f"{at // 2 + 1}...{san}" if i == 0 else san)
    return " ".join(out)


def message(example, name="", question=None):
    ply, other = example["ply"], "Black" if example["colour"] == "White" else "White"
    lines = [f"{example['colour']} played {example['move']}, a {example['verdict']}."]
    if name:
        lines.append(f"It was grouped under: {name}.")
    if example["allowed"]:
        lines.append(f"After it, the engine's best play for {other} is {numbered(ply + 1, example['allowed'], 3)}.")
    if question:
        lines.append(f"The engine's best move instead was {numbered(ply, example['best'], 3)}.")
    lines.append(f"Before the move: {example['before']}; after it: {example['after']}.")
    lines.append(question or f"What did {example['move']} allow?")
    return "\n".join(lines)


def sourced(reply, example):
    """The reply as plain text, or None when it links a Line that didn't pass, names a move it wasn't given, or a number."""
    ids = {line["id"] for line in reply.get("lines") or []}
    if any(found.group(2) not in ids for found in LINK.finditer(reply.get("content", ""))):
        return None
    text = " ".join(LINK.sub(r"\1", reply.get("content", "")).split())
    given = {plain(s) for s in [example["move"].split(".")[-1], *example["best"], *example["allowed"]]}
    if not text or reply.get("finish_reason") == "max_tokens" or NUMBER.search(text):
        return None
    if any(plain(m) not in given for m in NAMED.findall(text)):
        return None
    return text


def ask_knight(cli, example, system, text):
    """One Knight reply on the position after the example's move, where the Line it allowed is legal, so the Lines it
    names pass; None if Knight couldn't answer. Waits out a rate limit, and stops on anything else."""
    args = [cli, "generate", "--model", "knight", "--pgn", "-", "--ply", str(example["ply"] + 1), "--no-stream", "--json",
            "--system", system, text]
    for attempt in range(RETRIES):
        done = subprocess.run(args, input=example["pgn"], capture_output=True, text=True, encoding="utf-8")
        if done.returncode == 0:
            return json.loads(done.stdout)
        if done.returncode in (1, EXIT_RATE_LIMITED):
            time.sleep(min(60, RETRY_SECONDS * 2**attempt))
            continue
        sys.exit(done.stderr.strip() or f"{cli} stopped with code {done.returncode}.")
    return None


def call_knight(cli, example, system, name=""):
    """Knight's line on what the example's move allowed, its cost, the calls made, and whether it came from Knight. It
    gets the group's name, to say how the example shows it where the Line does. A move Knight can't explain, asked
    twice, says so, with the engine's Line."""
    cost, tries = 0.0, 0
    while tries < TRIES:
        reply, tries = ask_knight(cli, example, system, message(example, name)), tries + 1
        cost += float((reply or {}).get("cost_usd") or 0)
        if reply and (text := sourced(reply, example)):
            return text, cost, tries, True
    allowed = numbered(example["ply"] + 1, example["allowed"], 2)
    said = f"It allowed {allowed}." if allowed else f"Better was {numbered(example['ply'], example['best'], 1)}."
    return f"The chess model didn't explain this one. {said}", cost, tries, False


def fits(cli, name, example):
    """Whether Knight says the example shows the name, and the call's cost. No answer is a no."""
    reply = ask_knight(cli, example, FIT_SYSTEM, message(example, question=f'Does this mistake show "{name}"?'))
    return bool(reply) and (reply.get("content") or "").strip().lower().startswith("yes"), float((reply or {}).get("cost_usd") or 0)


def study_key(cli, study):
    """The page's API and Study key: those of the page built before, else a new key (live.md, Make the key), else none."""
    if study.exists():
        old = study.read_text(encoding="utf-8")
        key, api = (re.search(rf'<meta name="chessdrive-{m}" content="([^"]+)">', old) for m in ("key", "api"))
        if key and api:
            return api[1], key[1]
    done = subprocess.run([cli, "study-key", "Your mistakes", "--json"], capture_output=True, text=True, encoding="utf-8")
    try:
        made = json.loads(done.stdout) if done.returncode == 0 else {}
        return made.get("api_url"), made.get("key")
    except ValueError:
        return None, None


def code_blocks(path):
    """Each fenced block of a reference, by its language, in order, as it stands."""
    found = re.findall(r"^( *)```(\w+)\n(.*?)^\1```", path.read_text(encoding="utf-8"), re.M | re.S)
    return [(lang, textwrap.dedent(body)) for _, lang, body in found]


def put(page, old, new):
    if old not in page:
        sys.exit(f"study.py: frame.md has changed, and no longer has {old!r}. Build the Study by hand, as frame.md says.")
    return page.replace(old, new, 1)


PANEL = """<section class="cd-card"><h2>On the board</h2>
      <p><span class="cd-num" id="ex-move"></span> <span class="cd-tag" id="ex-verdict"></span></p>
      <p class="cd-meta" id="ex-game"></p>
      <p id="ex-why"></p>
      <p class="cd-meta" id="ex-better"></p>
    </section>
    <section class="cd-card"><h2>The kinds of mistake you make most</h2><div id="groups"></div></section>"""

MORE = """<section class="cd-more"><section class="cd-card"><h2>How far to trust this</h2>
    <p>A group holds mistakes that look alike on the board and in what the engine's lines say they allowed. Its name comes from five of them, and a name stays only when at least three of the five show it, so not every mistake in a group is that kind.</p>
    <p id="left-out" hidden></p></section></section>"""

STYLE = """
.cd-meta { color: var(--ink-2); font-size: 13.5px; }
.cd-group + .cd-group { margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--line); }
.cd-group h3 { margin: 0 0 2px; font-size: 15px; font-weight: 600; }
.cd-group p { margin: 0 0 6px; }
"""

PAGE_CODE = """
const board = document.getElementById('board');
live(board);
const back = document.getElementById('back');
const groupsBox = document.getElementById('groups');
const text = (id, value) => { document.getElementById(id).textContent = value; };
let onView = null;
let marks = [];
const trying = tryMoves(board, back, {}, () => show(onView));

function show(ex) {
  onView = ex;
  marks = [squares(ex.fen, ex.san) && { arrow: squares(ex.fen, ex.san), color: 'red' },
    ex.best[0] && squares(ex.fen, ex.best[0]) && { arrow: squares(ex.fen, ex.best[0]), color: 'green' }].filter(Boolean);
  const word = ex.verdict === 'blunder' ? 'Blunder' : 'Mistake';
  board.set({ pgn: ex.pgn, ply: ex.ply, orientation: ex.colour.toLowerCase(), mode: 'play-both', marks,
    annotations: { [ex.ply + 1]: { glyph: ex.verdict === 'blunder' ? '??' : '?', comment: word + '. ' + ex.why } } });
  text('ex-move', ex.move);
  const tag = document.getElementById('ex-verdict');
  tag.textContent = word;
  tag.className = 'cd-tag cd-' + ex.verdict;
  text('ex-game', ['against ' + (ex.opponent || 'your opponent'), ex.date].filter(Boolean).join(', '));
  text('ex-why', ex.why);
  text('ex-better', ex.better ? 'Better was ' + ex.better + '. Red is your move, green the better one.' : '');
  for (const b of groupsBox.querySelectorAll('button')) b.setAttribute('aria-current', String(b.ex === ex));
}

board.on('ply', ({ ply }) => {
  if (!trying() && onView) board.set({ marks: ply === onView.ply ? marks : [] });
});

for (const group of DATA.groups) {
  const box = document.createElement('div');
  box.className = 'cd-group';
  const title = document.createElement('h3');
  title.textContent = group.group + '. ' + group.name;
  const count = document.createElement('p');
  count.className = 'cd-meta';
  count.textContent = group.size + ' mistakes in ' + group.games + ' games; ' + group.fit + ' of the ' + group.checked + ' checked show this.';
  const check = document.createElement('p');
  check.textContent = group.check;
  const list = document.createElement('ul');
  list.className = 'cd-list';
  for (const ex of group.examples) {
    const item = document.createElement('li');
    const button = document.createElement('button');
    button.ex = ex;
    const move = document.createElement('span');
    move.className = 'cd-num';
    move.textContent = ex.move;
    const against = document.createElement('span');
    against.textContent = 'against ' + (ex.opponent || 'your opponent');
    button.append(move, against);
    button.onclick = () => { if (trying()) back.click(); show(ex); };
    item.append(button);
    list.append(item);
  }
  box.append(title, count);
  if (group.check) box.append(check);
  box.append(list);
  groupsBox.append(box);
}
if (DATA.left_out) {
  const left = document.getElementById('left-out');
  left.hidden = false;
  left.textContent = DATA.left_out + (DATA.left_out === 1 ? ' more group was' : ' more groups were') + ' left out, as fewer than three of five examples showed one idea.';
}
if (DATA.groups.length) show(DATA.groups[0].examples[0]);
"""


def page(data, api=None, key=None):
    """The Study: frame.md's page, style and keeping script as they stand, with board.md's tryMoves and squares, and
    live.md's card, which asks about the position on view with the page's Study key."""
    frame = code_blocks(STUDY / "frame.md")
    live = code_blocks(STUDY / "live.md")
    card = [body for lang, body in live if lang == "html"][1]
    live_style = next(body for lang, body in live if lang == "css")
    live_code = next(body for lang, body in live if lang == "js")
    skeleton = next(body for lang, body in frame if lang == "html")
    style = next(body for lang, body in frame if lang == "css")
    keeping = next(body for lang, body in frame if lang == "js")
    board_code = [body for lang, body in code_blocks(STUDY / "board.md") if lang == "js"]
    try_moves = next(body for body in board_code if "function tryMoves" in body)
    squares = next(body for body in board_code if "const squares" in body)

    data_js = json.dumps(data, ensure_ascii=False).replace("</", "<\\/").replace("<!--", "<\\!--")
    script = "\n".join([keeping, live_code, try_moves, squares, f"const DATA = {data_js};", PAGE_CODE])
    title = "Your mistakes"

    out = skeleton
    out = put(out, "<title>Your game against Ana</title>", f"<title>{html.escape(title)}</title>")
    out = put(out, "<h1>Your game against Ana</h1>", f"<h1>{html.escape(title)}</h1>")
    out = put(out, "<p>Step through with ← → or the moves, and play your own to try an idea.</p>",
              "<p>Click a mistake to put it on the board, then play your own moves to try an idea.</p>")
    out = put(out, '<div class="cd-page" data-moves>', '<div class="cd-page">')
    out = put(out, ">Back to the game</button>", ">Back to the position</button>")
    out = put(out, '<section class="cd-card"><h2>Turning points</h2>…</section>', card.strip() + "\n    " + PANEL)
    if api:
        metas = f'<meta name="chessdrive-api" content="{html.escape(api)}">' + (f'\n<meta name="chessdrive-key" content="{html.escape(key)}">' if key else "")
        out = put(out, '<meta name="chessdrive-api" content="https://api-staging.chessdrive.io">', metas)
    out = put(out, '<section class="cd-more">…</section>', MORE)
    out = put(out, "utm_campaign=KIND", "utm_campaign=other")
    out = put(out, "<style>/* The style, below */</style>", "<style>\n" + style + live_style + STYLE + "</style>")
    out = put(out, "  /* The keeping script, below, first; then the kind's page code. */",
              textwrap.indent(script.strip(), "  "))
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("folder", help="the folder Step 2 of the Skill and groups.py wrote, with your names.json")
    parser.add_argument("--rating", help="the player's rating, for Knight")
    parser.add_argument("--out", help="where the Study goes (default: your-mistakes.html in the folder)")
    parser.add_argument("--cli", default="chessdrive", help="the CLI to call")
    args = parser.parse_args()

    folder = Path(args.folder)
    groups = {g["group"]: {**g, "examples": g["examples"][:CHECKED]} for g in json.loads((folder / "groups.json").read_text(encoding="utf-8"))}
    names = json.loads((folder / "names.json").read_text(encoding="utf-8"))

    for named in names:
        if named["group"] not in groups:
            sys.exit(f"study.py: names.json names group {named['group']}, which groups.json doesn't have.")
    named_ones = [n for n in names if n.get("name") and n["name"] != "No clear idea"]
    key = lambda ex: f"{ex['site'] or ex['date']}:{ex['ply']}:{ex['move']}"
    cache_file = folder / "explained.json"
    cache = json.loads(cache_file.read_text(encoding="utf-8")) if cache_file.exists() else {}
    cost, calls = 0.0, 0

    checks = [(n["name"], ex) for n in named_ones for ex in groups[n["group"]]["examples"] if f"fit:{n['name']}:{key(ex)}" not in cache]
    with ThreadPoolExecutor(AT_ONCE) as pool:
        for (name, ex), (shows, spent) in zip(checks, pool.map(lambda c: fits(args.cli, *c), checks)):
            cost, calls = cost + spent, calls + 1
            cache[f"fit:{name}:{key(ex)}"] = shows
    kept, left_out = [], len(names) - len(named_ones)
    for named in named_ones:
        group = groups[named["group"]]
        fit = [n for n, ex in enumerate(group["examples"], start=1) if cache[f"fit:{named['name']}:{key(ex)}"]]
        if len(fit) < MIN_FIT:
            left_out += 1
            continue
        kept.append((named, group, fit))

    shown = [(group["examples"][n - 1], named["name"]) for named, group, fit in kept for n in fit[:SHOWN]]
    todo = [(ex, name) for ex, name in shown if key(ex) not in cache]
    system = SYSTEM.format(rating=f" of about {args.rating}" if args.rating else "")
    with ThreadPoolExecutor(AT_ONCE) as pool:
        for (ex, _), (why, spent, made, by_knight) in zip(todo, pool.map(lambda job: call_knight(args.cli, job[0], system, job[1]), todo)):
            cost, calls = cost + spent, calls + made
            cache[key(ex)] = {"why": why, "knight": by_knight}
    cache_file.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")

    data, printed = {"groups": [], "left_out": left_out}, []
    for number, (named, group, fit) in enumerate(kept, start=1):
        examples = []
        for n in fit[:SHOWN]:
            ex = group["examples"][n - 1]
            said = cache[key(ex)]
            examples.append({
                "move": ex["move"], "san": plain(ex["move"].split(".")[-1]), "verdict": ex["verdict"], "colour": ex["colour"],
                "opponent": ex["opponent"], "date": ex["date"], "site": ex["site"], "fen": ex["fen"], "pgn": ex["pgn"],
                "ply": ex["ply"], "best": ex["best"], "better": numbered(ex["ply"], ex["best"], 1),
                "allowed": numbered(ex["ply"] + 1, ex["allowed"], 3), "why": said["why"], "from_knight": said["knight"],
            })
        entry = {"group": number, "name": named["name"], "check": named.get("check", ""), "size": group["size"],
                 "games": group["games"], "fit": len(fit), "checked": len(group["examples"]), "examples": examples}
        data["groups"].append({**entry, "examples": [{k: v for k, v in e.items() if k != "from_knight"} for e in examples]})
        printed.append({**entry, "examples": [{k: e[k] for k in ("move", "opponent", "date", "site", "better", "allowed", "why", "from_knight")} for e in examples]})

    study = None
    if kept and (STUDY / "frame.md").exists() and (STUDY / "board.md").exists():
        study = Path(args.out) if args.out else folder / "your-mistakes.html"
        study.write_text(page(data, *study_key(args.cli, study)), encoding="utf-8")

    for entry in printed:
        print(json.dumps(entry, ensure_ascii=False), flush=True)
    print(json.dumps({
        "named": len(names), "kept": len(kept), "left_out": left_out, "knight_calls": calls,
        "knight_cost_usd": round(cost, 4), "study": str(study.resolve()) if study else None,
    }), flush=True)


if __name__ == "__main__":
    main()
