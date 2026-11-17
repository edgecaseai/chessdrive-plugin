#!/usr/bin/env python3
"""The Game review Study, built from what the review saved. Python 3.11 or later; the `chessdrive` CLI makes the
page's Study key.

    python3 study.py review --colour black

Reads, from the folder the Skill's Steps 1 to 4 wrote: engine.json, the engine's answer for the whole game;
answers.jsonl, which ask.py wrote, a note a marked move, its `id` the move as in `14...Qd7`; and game.pgn. It makes no
call to the engine or the chess models.

Writes the Study in the frame of the chessdrive-study Skill beside this one, named after the game, beside the folder
it read, which is the person's own folder: the Board with the game and a verdict on every marked move; the card On the
board, with the verdict and the note of the move on view, word for word, or a label where no model gave one; that
Skill's "Ask about this position" card; the turning points; and a graph of White's chance to win. The turning points
are the moves the Skill's Step 3 heads an answer with: the worst three mistakes and blunders of the person's, or of
both sides without --colour, and up to three after which a different side stood better or a level game stopped being
level, five at most. With no mistake of theirs, their worst inaccuracy leads, or else their costliest move that wasn't
the engine's best.

It checks the page with that Skill's check.py and prints one JSON object: `study`, the page's full path, or null when
that Skill isn't there; `check`, "ok" or what check.py printed; `turning_points`; `missing`, the marked moves no model
explained; and `unmatched`, the answers whose `id` is no marked move.
"""

import argparse
import html
import json
import re
import subprocess
import sys
import textwrap
import unicodedata
from pathlib import Path

sys.dont_write_bytecode = True  # keeps the Plugin's folder as it was installed

STUDY = Path(__file__).resolve().parent.parent.parent / "chessdrive-study"
REFERENCES = STUDY / "references"

MARKED = ("inaccuracy", "mistake", "blunder")
WORST = 3  # the person's worst moves that head an answer
TURNS = 3  # the turning points beside them
LISTED = 5
START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
TAG = re.compile(r'^\[(\w+)\s+"((?:[^"\\]|\\.)*)"\]', re.M)


def san(move):
    """A move as the CLI gives it, {san, uci}, or as the Connector does, its SAN alone."""
    return move["san"] if isinstance(move, dict) else move


def label(move):
    return f"{move['move_number']}{'.' if move['color'] == 'white' else '...'}{san(move['move'])}"


def same(text):
    """A move's label as two writers of it agree: no spaces, marks or checks."""
    return re.sub(r"[\s?!+#]", "", str(text).replace("…", "..."))


def lines_of(path):
    """A JSON Lines file's objects. Split at the line feed alone: a reply can hold a separator that splitlines() breaks at."""
    return [json.loads(line) for line in path.read_text(encoding="utf-8").split("\n") if line.strip()] if path.exists() else []


def notes(folder, moves):
    """Each marked move's note by its place in `moves`, as ask.py wrote it, None where no model gave one; and the ids
    of the answers that are no marked move's. An answer is its move's by its id, else by the ply it was asked at."""
    marked = {same(label(m)): i for i, m in enumerate(moves) if m["verdict"] in MARKED}
    asked = {q["id"]: q["ply"] for q in lines_of(folder / "questions.jsonl") if "id" in q and "ply" in q}
    by_ply = {m["ply"]: i for i, m in enumerate(moves) if m["verdict"] in MARKED}
    found, unmatched = {}, []
    for answer in lines_of(folder / "answers.jsonl"):
        at = marked.get(same(answer.get("id", "")), by_ply.get(asked.get(answer.get("id"))))
        if at is None:
            unmatched.append(answer.get("id"))
        elif answer.get("text") or at not in found:
            found[at] = answer.get("text") or None
    return found, unmatched


def side(evaluation, mover):
    """Who stands better, by the Skill's bands: 1 for White, -1 for Black, 0 when it's about equal."""
    if evaluation.get("mate") is not None:
        return (1 if evaluation["mate"] > 0 else -1) if evaluation["mate"] else mover
    return 0 if abs(evaluation["cp"]) < 50 else 1 if evaluation["cp"] > 0 else -1


def turning_points(moves, colour):
    """The moves the page lists, by their place in `moves`, in game order."""
    cost = lambda i: -moves[i]["win_chance_lost"]
    bad = [i for i, m in enumerate(moves) if m["verdict"] in ("mistake", "blunder")]
    theirs = [i for i in bad if not colour or moves[i]["color"] == colour]
    turned = []
    for i in bad:
        mover = 1 if moves[i]["color"] == "white" else -1
        after = side(moves[i]["eval_after"], mover)
        if after and after != side(moves[i]["eval_before"], mover):
            turned.append(i)
    listed = sorted(theirs, key=cost)[:WORST] + sorted(turned, key=cost)[:TURNS]
    if colour and not theirs:
        own = [i for i, m in enumerate(moves) if m["color"] == colour and m["verdict"] != "best" and m["win_chance_lost"] > 0]
        listed = sorted([i for i in own if moves[i]["verdict"] == "inaccuracy"] or own, key=cost)[:1] + listed
    return sorted(list(dict.fromkeys(listed))[:LISTED])


def game(folder, moves):
    """The game's PGN and its headers. With no game.pgn, the engine's moves make one."""
    path = folder / "game.pgn"
    if path.exists():
        pgn = path.read_text(encoding="utf-8").strip()
    else:
        text = [] if moves[0]["fen"] == START else [f'[SetUp "1"]\n[FEN "{moves[0]["fen"]}"]\n\n']
        for i, m in enumerate(moves):
            text.append(label(m) if m["color"] == "white" or i == 0 else san(m["move"]))
        pgn = " ".join(text) + " *"
    tags = {name: re.sub(r"\\(.)", r"\1", value).strip() for name, value in TAG.findall(pgn)}
    return pgn, {name: value for name, value in tags.items() if value and set(value) != {"?"}}


def players(tags):
    out = {}
    for colour in ("White", "Black"):
        player = {"name": tags.get(colour), "rating": int(tags[colour + "Elo"]) if tags.get(colour + "Elo", "").isdigit() else None}
        if any(player.values()):
            out[colour.lower()] = {k: v for k, v in player.items() if v}
    return out


def title_of(tags, colour):
    white, black = tags.get("White"), tags.get("Black")
    if colour:
        opponent = black if colour == "white" else white
        return f"Your game against {opponent}" if opponent else "Your game"
    return f"{white} against {black}" if white and black else "A game to step through"


def file_name(title):
    plain = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    return (re.sub(r"[^a-z0-9]+", "-", plain.lower()).strip("-") or "game-review") + ".html"


def study_key(cli, study, title):
    """The page's API and Study key: those of the page built before, else a new key (live.md, Make the key), else none."""
    if study.exists():
        old = study.read_text(encoding="utf-8")
        key, api = (re.search(rf'<meta name="chessdrive-{m}" content="([^"]+)">', old) for m in ("key", "api"))
        if key and api:
            return html.unescape(api[1]), html.unescape(key[1])
    try:
        done = subprocess.run([cli, "study-key", title, "--json"], capture_output=True, text=True, encoding="utf-8")
        made = json.loads(done.stdout) if done.returncode == 0 else {}
        return made.get("api_url"), made.get("key")
    except (OSError, ValueError):
        return None, None


def code_blocks(path):
    """Each fenced block of a reference, by its language, in order, as it stands."""
    found = re.findall(r"^( *)```(\w+)\n(.*?)^\1```", path.read_text(encoding="utf-8"), re.M | re.S)
    return [(lang, textwrap.dedent(body)) for _, lang, body in found]


def put(page, old, new):
    if old not in page:
        sys.exit(f"study.py: frame.md has changed, and no longer has {old!r}. Build the Study by hand, as review.md says.")
    return page.replace(old, new, 1)


ON_THE_BOARD = """<section class="cd-card"><h2>On the board</h2>
      <p class="cd-now"><span class="cd-num" id="now-move"></span> <span class="cd-tag" id="now-verdict" hidden></span></p>
      <p id="now-note" hidden></p>
      <p class="cd-meta" id="now-eval"></p>
      <p class="cd-meta" id="now-line" hidden></p>
      <button class="cd-btn" id="now-best" hidden>Show the best move</button>
    </section>"""

LISTS = """<section class="cd-card"><h2>Turning points</h2><ul class="cd-list" id="turning"></ul></section>
    <section class="cd-card"><h2>White’s chance to win</h2>
      <svg class="cd-graph" id="graph" viewBox="0 0 300 80" preserveAspectRatio="none" role="img" aria-label="White’s chance to win, move by move"></svg>
    </section>"""

STYLE = """
.cd-meta { color: var(--ink-2); font-size: 13.5px; }
.cd-now { font-size: 16px; font-weight: 600; }
.cd-tag[hidden] { display: none; }
.cd-list .cd-num { font-weight: 600; }
.cd-graph { display: block; width: 100%; height: 80px; border-radius: var(--radius); background: var(--paper-2); cursor: pointer; }
.cd-graph * { fill: none; stroke: var(--ink-2); stroke-width: 1.5; stroke-linecap: round; vector-effect: non-scaling-stroke; }
.cd-graph .cd-level { stroke: var(--line-strong); stroke-width: 1; }
.cd-graph .cd-dot { stroke: var(--brand); stroke-width: 7; }
.cd-graph .cd-dot.cd-inaccuracy { stroke: var(--inaccuracy); }
.cd-graph .cd-dot.cd-mistake { stroke: var(--mistake); }
.cd-graph .cd-dot.cd-blunder { stroke: var(--blunder); }
.cd-graph .cd-on { stroke: var(--brand); stroke-width: 10; }
"""

PAGE_CODE = """
const board = document.getElementById('board');
const back = document.getElementById('back');
const el = (id) => document.getElementById(id);
const M = DATA.moves;
const GLYPH = { inaccuracy: '?!', mistake: '?', blunder: '??' };
const WORD = { inaccuracy: 'Inaccuracy', mistake: 'Mistake', blunder: 'Blunder' };
const NO_NOTE = 'No explanation: the chess model didn’t answer.';
// A move's verdict and its note, word for word as the chess model wrote it, or the label where none did.
const noteOf = (m) => m.note ?? NO_NOTE;
// A Line's moves numbered on from the move m, as "14...Nf6 15.Qe2 O-O".
const numbered = (m, sans) => {
  let n = parseInt(m.move, 10), black = m.color === 'black';
  return sans.map((s, k) => {
    const text = (black ? (k === 0 ? n + '...' : '') : n + '.') + s;
    if (black) n++;
    black = !black;
    return text;
  }).join(' ');
};
// An evaluation in words, from White's side, by the engine's bands.
const words = (e) => {
  if (e.mate != null) return e.mate === 0 ? 'checkmate' : (e.mate > 0 ? 'White' : 'Black') + ' mates in ' + Math.abs(e.mate);
  const side = e.cp > 0 ? 'White' : 'Black', a = Math.abs(e.cp);
  return a < 50 ? 'about equal' : side + (a < 150 ? ' a little better' : a < 300 ? ' clearly better' : ' winning');
};
// With `ply` half-moves played: the evaluation, the Board's bar, and White's chance to win.
const evalAt = (ply) => (ply === 0 ? M[0].eval_before : M[ply - 1].eval_after);
const bar = (e) => (e.mate === 0 ? null : e);
const chance = (ply) => {
  const e = evalAt(ply);
  if (e.mate == null) return 1 / (1 + Math.exp(-0.00368208 * e.cp));
  return (e.mate === 0 ? M[ply - 1].color === 'white' : e.mate > 0) ? 1 : 0;
};

const annotations = {};
M.forEach((m, i) => {
  if (GLYPH[m.verdict]) annotations[i + 1] = { glyph: GLYPH[m.verdict], comment: WORD[m.verdict] + '. ' + noteOf(m) };
});
board.set({ pgn: DATA.pgn, ply: 0, orientation: DATA.orientation, moves: true, mode: 'play-both', players: DATA.players,
  annotations, eval: bar(M[0].eval_before) });
live(board);

// The graph: one point for each ply, the turning points as dots, and the ply on view.
const graph = el('graph'), W = 300, H = 80;
const x = (ply) => 6 + (ply / M.length) * (W - 12), y = (ply) => 6 + (1 - chance(ply)) * (H - 12);
const draw = (name, cls, attrs) => {
  const node = document.createElementNS(graph.namespaceURI, name);
  node.setAttribute('class', cls);
  for (const k in attrs) node.setAttribute(k, attrs[k]);
  graph.append(node);
  return node;
};
// A dot is a line too short to see with a round end, so it stays round however wide the graph is.
const dot = (cls, ply) => draw('line', cls, { x1: x(ply), y1: y(ply), x2: x(ply) + 0.01, y2: y(ply) });
draw('line', 'cd-level', { x1: 0, x2: W, y1: H / 2, y2: H / 2 });
draw('polyline', 'cd-curve', { points: [...M.keys(), M.length].map((ply) => x(ply) + ',' + y(ply)).join(' ') });
for (const i of DATA.turning) dot('cd-dot cd-' + M[i].verdict, i + 1);
const here = dot('cd-on', 0);

const tagOf = (m, tag = document.createElement('span')) => {
  tag.className = 'cd-tag' + (GLYPH[m.verdict] ? ' cd-' + m.verdict : '');
  tag.textContent = WORD[m.verdict] || 'Costliest move';
  return tag;
};
const turning = DATA.turning.map((i) => {
  const item = document.createElement('li'), button = document.createElement('button');
  const move = Object.assign(document.createElement('span'), { className: 'cd-num', textContent: M[i].move + (GLYPH[M[i].verdict] || '') });
  const what = Object.assign(document.createElement('span'), { textContent: words(M[i].eval_before) + ' → ' + words(M[i].eval_after) });
  button.append(tagOf(M[i]), move, what);
  button.onclick = () => { if (trying()) back.click(); show(i + 1); };
  item.append(button);
  el('turning').append(item);
  return [i + 1, button];
});
if (!turning.length) el('turning').closest('section').hidden = true;

let on = 0, best = false;
// Keeps the page in step with the Board, at `ply` half-moves played. With `showBest`, the Board goes to the position
// before the move, with the engine's move in green and the move played in red.
function show(ply, showBest = false) {
  const m = M[ply - 1];
  const marked = !!(m && GLYPH[m.verdict]);
  on = ply;
  best = showBest && marked;
  if (best) {
    const good = squares(m.fen, m.best_line[0]), played = squares(m.fen, m.san);
    board.set({ ply: ply - 1, eval: bar(m.eval_before),
      marks: [good && { arrow: good, color: 'green' }, played && { arrow: played, color: 'red' }].filter(Boolean) });
  } else {
    board.set({ ply, eval: bar(evalAt(ply)), marks: [] });
  }
  el('now-move').textContent = m ? m.move + (GLYPH[m.verdict] || '') : 'The start of the game';
  el('now-move').className = m ? 'cd-num' : '';
  el('now-verdict').hidden = el('now-note').hidden = el('now-best').hidden = !marked;
  el('now-line').hidden = !best;
  if (marked) {
    tagOf(m, el('now-verdict'));
    el('now-note').textContent = noteOf(m);
    el('now-line').textContent = 'The engine’s Line: ' + numbered(m, m.best_line.slice(0, 6)) + '. Green is its move, red the move played.';
    el('now-best').textContent = best ? 'Back to the move played' : 'Show the best move';
  }
  const before = m ? words(m.eval_before) : '', after = words(evalAt(ply));
  el('now-eval').textContent = m ? 'Before: ' + before + '. After: ' + after + '.' : after[0].toUpperCase() + after.slice(1) + '.';
  for (const at of ['x1', 'x2']) here.setAttribute(at, x(ply) + (at === 'x2' ? 0.01 : 0));
  for (const at of ['y1', 'y2']) here.setAttribute(at, y(ply));
  for (const [at, button] of turning) button.setAttribute('aria-current', String(at === ply));
}

const trying = tryMoves(board, back, { pgn: DATA.pgn, annotations }, (ply) => show(ply));
board.on('ply', ({ ply }) => { if (!trying()) show(ply); });
el('now-best').onclick = () => { if (trying()) back.click(); show(on, !best); };
graph.addEventListener('click', (e) => {
  const box = graph.getBoundingClientRect();
  const ply = Math.round((((e.clientX - box.left) / box.width) * W - 6) / (W - 12) * M.length);
  if (trying()) back.click();
  show(Math.max(0, Math.min(M.length, ply)));
});
// ← → step the game from anywhere on the page; the Board steps itself when it has the focus.
document.addEventListener('keydown', (e) => {
  if (e.target === board || e.target.closest?.('input, textarea') || trying()) return;
  if (e.key === 'ArrowLeft' && on > 0) show(on - 1);
  else if (e.key === 'ArrowRight' && (best || on < M.length)) show(best ? on : on + 1);
  else return;
  e.preventDefault();
});
show(0);
"""


def page(data, title, api=None, key=None):
    """The Study: frame.md's page, style and keeping script as they stand, with board.md's tryMoves and squares, and
    live.md's card, which asks about the position on view with the page's Study key."""
    frame = code_blocks(REFERENCES / "frame.md")
    live = code_blocks(REFERENCES / "live.md")
    card = [body for lang, body in live if lang == "html"][1]
    live_style = next(body for lang, body in live if lang == "css")
    live_code = next(body for lang, body in live if lang == "js")
    skeleton = next(body for lang, body in frame if lang == "html")
    style = next(body for lang, body in frame if lang == "css")
    keeping = next(body for lang, body in frame if lang == "js")
    board_code = [body for lang, body in code_blocks(REFERENCES / "board.md") if lang == "js"]
    try_moves = next(body for body in board_code if "function tryMoves" in body)
    squares = next(body for body in board_code if "const squares" in body)

    # As JSON that is also safe inside a <script>: no "<" for the browser to read as a tag or a comment, and no line
    # separator, which would end the line inside a note.
    data_js = json.dumps(data, ensure_ascii=False)
    for unsafe in "<\x85\u2028\u2029":
        data_js = data_js.replace(unsafe, f"\\u{ord(unsafe):04x}")
    script = "\n".join([keeping, live_code, try_moves, squares, f"const DATA = {data_js};", PAGE_CODE])

    out = skeleton
    out = put(out, "<title>Your game against Ana</title>", f"<title>{html.escape(title)}</title>")
    out = put(out, "<h1>Your game against Ana</h1>", f"<h1>{html.escape(title)}</h1>")
    out = put(out, '<section class="cd-card"><h2>Turning points</h2>…</section>', ON_THE_BOARD + "\n    " + card.strip() + "\n    " + LISTS)
    if api:
        metas = f'<meta name="chessdrive-api" content="{html.escape(api)}">' + (f'\n<meta name="chessdrive-key" content="{html.escape(key)}">' if key else "")
        out = put(out, '<meta name="chessdrive-api" content="https://api.chessdrive.io">', metas)
    out = put(out, '  <section class="cd-more">…</section>\n', "")
    out = put(out, "utm_campaign=KIND", "utm_campaign=review")
    out = put(out, "<style>/* The style, below */</style>", "<style>\n" + style + live_style + STYLE + "</style>")
    out = put(out, "  /* The keeping script, below, first; then the kind's page code. */",
              "\n".join("  " + line if line else line for line in script.strip().split("\n")))
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("folder", help="the folder with engine.json, answers.jsonl and game.pgn")
    parser.add_argument("--colour", choices=["white", "black"], help="the person's colour: the Board faces it. Leave it out if you don't know it")
    parser.add_argument("--out", help="where the Study goes (default: named after the game, in the folder that holds `folder`)")
    parser.add_argument("--no-key", action="store_true", help="make no Study key: only in Claude's chat app, where the page is an artifact")
    parser.add_argument("--cli", default="chessdrive", help="the CLI to call")
    args = parser.parse_args()

    folder = Path(args.folder)
    if not (folder / "engine.json").exists():
        sys.exit(f"study.py: {folder / 'engine.json'} isn't there. Save the engine's answer for the whole game to it first.")
    moves = json.loads((folder / "engine.json").read_text(encoding="utf-8")).get("moves") or []
    if not moves:
        sys.exit(f"study.py: {folder / 'engine.json'} has no `moves`. It needs the engine's answer for a whole game.")
    found, unmatched = notes(folder, moves)
    listed = turning_points(moves, args.colour)
    pgn, tags = game(folder, moves)
    title = title_of(tags, args.colour)
    evaluation = lambda e: {"cp": e.get("cp"), "mate": e.get("mate")}
    data = {"pgn": pgn, "orientation": args.colour or "white", "players": players(tags), "turning": listed, "moves": [{
        "ply": m["ply"], "move": label(m), "san": san(m["move"]), "color": m["color"], "verdict": m["verdict"], "fen": m["fen"],
        "eval_before": evaluation(m["eval_before"]), "eval_after": evaluation(m["eval_after"]),
        "best_line": [san(move) for move in m["best_line"]], "note": found.get(i),
    } for i, m in enumerate(moves)]}

    study, check = None, None
    if (REFERENCES / "frame.md").exists() and (REFERENCES / "board.md").exists() and (REFERENCES / "live.md").exists():
        study = Path(args.out) if args.out else folder.resolve().parent / file_name(title)
        api, key = (None, None) if args.no_key else study_key(args.cli, study, title)
        study.write_text(page(data, title, api, key), encoding="utf-8")
        done = subprocess.run([sys.executable, "-B", str(STUDY / "scripts" / "check.py"), str(study)], capture_output=True, text=True, encoding="utf-8")
        check = "ok" if done.returncode == 0 else done.stdout.strip() or done.stderr.strip()

    print(json.dumps({
        "study": str(study.resolve()) if study else None, "check": check, "title": title,
        "turning_points": [label(moves[i]) for i in listed],
        "missing": [label(m) for i, m in enumerate(moves) if m["verdict"] in MARKED and not found.get(i)],
        "unmatched": unmatched,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
