# Engine and Generate in the page

A Study with a Board the person moves on gets a card that asks about the position on view, only when they ask: Engine's evaluation and best Line, and one question to Generate with that Line passed in. It works with a **Study key**, a key made for this page alone, which calls only Engine and Generate, up to a dollar a day, for 7 days. A Worksheet's grid and a Board in `view` mode with nothing to try get none.

## Make the key

- **In a coding agent,** make one Study key per page while you build it: `chessdrive study-key "<title>"`, with the page's `<title>`, which prints the key alone, or with no CLI the Connector's `study_key` tool with `name`. It's free. Make one, never more for the same page, and none when you rebuild a page that has one: keep its key.
- **In Claude, ChatGPT or any app that shows the page itself,** make none. The page can't reach the API there, so the card stays hidden and says nothing; a copy the person downloads and opens shows the quiet "Add your key" line instead.

Never print the key in the chat, and never write it anywhere but the page's `<meta>`.

## The page

In the frame's `<head>`, after the Board's script, the API's address from the key's answer (`api_url`), and the key itself when you made one:

```html
<meta name="chessdrive-api" content="https://api-staging.chessdrive.io">
<meta name="chessdrive-key" content="ck_…">
```

Without a key, leave out the second line and keep the first: the page then shows "Add your key". The keeping script's Download leaves the key out of every copy, and the page takes it out of its own copy once it has read it.

First in `.cd-panel`, this card as it stands:

```html
<section class="cd-card cd-live" hidden>
  <h2>Ask about this position</h2>
  <p class="cd-live-add" hidden><span></span> <button class="cd-link" type="button">Add your key</button></p>
  <form class="cd-live-key" hidden><input type="password" autocomplete="off" placeholder="ck_…" aria-label="Your ChessDrive key"> <button class="cd-btn">Save</button></form>
  <div class="cd-live-tools" hidden><button class="cd-btn" type="button" data-live="engine">Engine's line</button></div>
  <p class="cd-live-line cd-num" hidden></p>
  <form class="cd-live-ask" hidden><input placeholder="Why not take on f7?" aria-label="Ask about this position" maxlength="300"> <button class="cd-btn">Ask</button></form>
  <p class="cd-live-answer" aria-live="polite" hidden></p>
</section>
```

Its styles, after the frame's:

```css
.cd-live form { display: flex; gap: 8px; margin: 8px 0 0; }
.cd-live [hidden] { display: none; }
.cd-live input { flex: 1; min-width: 0; height: 32px; padding: 0 10px; border: 1px solid var(--line-strong); border-radius: var(--radius); background: var(--paper); color: var(--ink); font: inherit; font-size: 14px; }
.cd-live-add { color: var(--ink-3); font-size: 13px; margin: 0; }
.cd-link { padding: 0; border: 0; background: none; color: var(--ink); font: inherit; cursor: pointer; text-decoration: underline; text-decoration-color: var(--brand); }
.cd-live-line, .cd-live-answer { margin: 8px 0 0; font-size: 14px; }
@media print { .cd-live { display: none; } }
```

And this function, after the keeping script and before the kind's code, called once with the Board in `.cd-board`: `live(board)`. Copy it as it stands:

```js
// The card that asks Engine and Generate about the position on view, with the page's Study key, only when the person
// asks. It shows only where the page can reach the API, which a free call with no key finds out.
function live(board) {
  const card = document.querySelector('.cd-live');
  const api = document.querySelector('meta[name="chessdrive-api"]')?.content;
  const meta = document.querySelector('meta[name="chessdrive-key"]');
  let key = meta?.content || '';
  meta?.remove();
  try { key ||= localStorage.getItem('chessdrive-key') || ''; } catch {}
  if (!card || !api) return;
  const $ = (s) => card.querySelector(s);
  const [add, keyForm, tools, lineOut, ask, answer] =
    ['.cd-live-add', '.cd-live-key', '.cd-live-tools', '.cd-live-line', '.cd-live-ask', '.cd-live-answer'].map($);
  const needKey = (why) => {
    add.querySelector('span').textContent = why;
    add.hidden = false;
    tools.hidden = ask.hidden = true;
  };
  const ready = () => { add.hidden = keyForm.hidden = true; tools.hidden = ask.hidden = false; };
  fetch(api + '/v1/models').then((r) => {
    if (!r.ok) return;
    card.hidden = false;
    key ? ready() : needKey('The engine and questions here need a ChessDrive key.');
  }).catch(() => {});
  add.querySelector('button').onclick = () => { keyForm.hidden = false; keyForm.querySelector('input').focus(); };
  keyForm.onsubmit = (e) => {
    e.preventDefault();
    const input = keyForm.querySelector('input');
    if (!/^[a-z]+_[0-9A-Za-z]{20,}$/.test(input.value.trim())) return;
    key = input.value.trim();
    input.value = '';
    try { localStorage.setItem('chessdrive-key', key); } catch {}
    ready();
  };

  async function call(path, body) {
    for (let tries = 0; ; tries++) {
      const r = await fetch(api + path, {
        method: 'POST',
        headers: { Authorization: 'Bearer ' + key, 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await r.json().catch(() => ({}));
      if (r.ok) return data;
      const code = data.error?.code;
      if ((r.status === 429 && tries < 2) || (code === 'upstream_unavailable' && tries < 1)) {
        await new Promise((go) => setTimeout(go, 1000 * (Number(r.headers.get('Retry-After')) || 2)));
        continue;
      }
      if (r.status === 401) {
        key = '';
        try { localStorage.removeItem('chessdrive-key'); } catch {}
        needKey(code === 'expired_api_key' ? 'This page’s key has expired.' : 'This page’s key no longer works.');
      }
      if (code === 'key_limit_reached') throw new Error('This page’s key has spent its dollar for today. It works again tomorrow.');
      throw Object.assign(new Error(data.error?.message || 'ChessDrive didn’t answer. Try again.'), { code });
    }
  }

  // Engine's answer for each position asked about, so a question reuses it.
  const answers = new Map();
  const engine = (fen) => {
    if (!answers.has(fen)) {
      answers.set(fen, call('/v1/engine', { engine: 'stockfish', position: { fen } }).catch((e) => {
        answers.delete(fen);
        throw e;
      }));
    }
    return answers.get(fen);
  };
  const score = (l) => (l.mate != null ? (l.mate > 0 ? 'M' : '−M') + Math.abs(l.mate)
    : (l.cp >= 0 ? '+' : '−') + (Math.abs(l.cp) / 100).toFixed(1));
  // A Line's moves numbered from its position, as "14...Nf6 15.Qe2 O-O": its first 8 are enough to read.
  const numbered = (fen, moves) => {
    const [, side, , , , full] = fen.split(' ');
    let n = Number(full) || 1, black = side === 'b';
    return moves.map((m, i) => {
      const text = (black ? (i === 0 ? n + '...' : '') : n + '.') + m.san;
      if (black) n++;
      black = !black;
      return text;
    }).join(' ');
  };
  const lineOf = (fen, a) => score(a.lines[0]) + '  ' + numbered(fen, a.lines[0].moves.slice(0, 8));
  const over = () => board.state.outcome ? 'The game is over in this position.' : '';

  const clear = () => { lineOut.hidden = answer.hidden = true; };
  board.on('ply', clear);
  board.on('move', clear);

  $('[data-live="engine"]').onclick = async ({ currentTarget: button }) => {
    const fen = board.state.fen;
    lineOut.hidden = false;
    if (over()) { lineOut.textContent = over(); return; }
    lineOut.textContent = 'The engine is thinking…';
    button.disabled = true;
    try {
      const a = await engine(fen);
      if (board.state.fen !== fen) return;
      lineOut.textContent = lineOf(fen, a);
      board.set({ eval: a.lines[0], marks: [{ arrow: a.best_move.uci, color: 'green' }] });
    } catch (e) {
      lineOut.textContent = e.message;
    } finally {
      button.disabled = false;
    }
  };

  ask.onsubmit = async (e) => {
    e.preventDefault();
    const input = ask.querySelector('input'), button = ask.querySelector('button');
    const question = input.value.trim(), fen = board.state.fen;
    if (!question) return;
    answer.hidden = false;
    if (over()) { answer.textContent = over(); return; }
    answer.textContent = 'Thinking…';
    button.disabled = true;
    try {
      const a = await engine(fen);
      const line = lineOf(fen, a);
      const body = (model) => ({
        model,
        position: { fen },
        system: 'You answer one question about a chess position for a club player, in two to four plain sentences. ' +
          'Use the engine\'s Line you are given, and name only moves from that Line. Judge positions in words, never in numbers. ' +
          'A threat or tactic goes in only if the Line plays it.',
        messages: [{ role: 'user', content: question + '\n\nThe engine\'s best Line here: ' + line }],
      });
      let reply;
      try {
        reply = await call('/v1/generate', body('queen'));
      } catch (err) {
        if (err.code !== 'plan_required') throw err;
        reply = await call('/v1/generate', body('knight'));
      }
      if (board.state.fen !== fen) return;
      // Moves come as [text](line:L1); a sentence whose move isn't one of the reply's legal Lines goes.
      const legal = new Set((reply.lines || []).map((l) => l.id));
      const text = reply.content.split(/(?<=[.!?])\s+/)
        .filter((s) => [...s.matchAll(/\]\(line:([^)]+)\)/g)].every((m) => legal.has(m[1])))
        .join(' ')
        .replace(/\[([^\]]+)\]\(line:[^)]+\)/g, (_, text) => text);
      answer.textContent = text || 'No answer this time. Try asking another way.';
      lineOut.hidden = false;
      lineOut.textContent = line;
      board.set({ eval: a.lines[0] });
    } catch (err) {
      answer.textContent = err.message;
    } finally {
      button.disabled = false;
    }
  };
}
```

- The card never runs a paid call on its own: Engine runs on "Engine's line" or a question, and Generate on a question. A question reuses Engine's answer for that position.
- The answers go in with `textContent`, and stay on screen only while their position is on view.
- In the kind's code, set the Board's `marks` and `eval` as before: the card sets them only when the person asks, and a move or step clears its text.
