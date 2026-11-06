# Stockfish and Generate in the page

A Study with a Board the person moves on gets a card that asks about the position on view, only when they ask: the engine's evaluation and best Line, and one question to Generate with that Line passed in. **The engine's Line runs on Stockfish in the person's browser, free,** with no key and no call to ChessDrive. A question to Generate works with a **Study key**, a key made for this page alone, which calls only Engine and Generate, up to a dollar a day, for 7 days; the Engine API is there only for a browser that can't run Stockfish. A Worksheet's grid and a Board in `view` mode with nothing to try get none.

The browser's Stockfish is [stockfish.js](https://github.com/nmrugg/stockfish.js)' build of Stockfish 18, GPL-3.0, loaded unchanged from its npm package on unpkg the first time the person asks, about 7 MB, and kept by the browser after that. The card credits it. Keep its pinned URL in `live()` as it stands.

## Make the key

- **In a coding agent,** make one Study key per page while you build it: `chessdrive study-key "<title>"`, with the page's `<title>`, which prints the key alone, or with no CLI the Connector's `study_key` tool with `name`. It's free. Make one, never more for the same page, and none when you rebuild a page that has one: keep its key.
- **In Claude, ChatGPT or any app that shows the page itself,** make none. The page can't reach the API there, so the card shows the engine's Line where the browser can run Stockfish, and no questions; a copy the person downloads and opens shows the quiet "Add your key" line for them.

Never print the key in the chat, and never write it anywhere but the page's `<meta>`.

## The page

In the frame's `<head>`, after the Board's script, the API's address from the key's answer (`api_url`), and the key itself when you made one:

```html
<meta name="chessdrive-api" content="https://api.chessdrive.io">
<meta name="chessdrive-key" content="ck_…">
```

Without a key, leave out the second line and keep the first: the page then shows "Add your key" for questions. The keeping script's Download leaves the key out of every copy, and the page takes it out of its own copy once it has read it.

First in `.cd-panel`, this card as it stands:

```html
<section class="cd-card cd-live" hidden>
  <h2>Ask about this position</h2>
  <p class="cd-live-add" hidden><span></span> <button class="cd-link" type="button">Add your key</button></p>
  <form class="cd-live-key" hidden><input type="password" autocomplete="off" placeholder="ck_…" aria-label="Your ChessDrive key"> <button class="cd-btn">Save</button></form>
  <div class="cd-live-tools" hidden><button class="cd-btn" type="button" data-live="engine">Engine's line</button></div>
  <p class="cd-live-credit" hidden>Runs <a href="https://github.com/nmrugg/stockfish.js" target="_blank" rel="noopener">Stockfish</a> (GPL-3.0) in your browser, free.</p>
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
.cd-live-add, .cd-live-credit { color: var(--ink-3); font-size: 13px; margin: 8px 0 0; }
.cd-live-credit a { color: inherit; }
.cd-link { padding: 0; border: 0; background: none; color: var(--ink); font: inherit; cursor: pointer; text-decoration: underline; text-decoration-color: var(--brand); }
.cd-live-line, .cd-live-answer { margin: 8px 0 0; font-size: 14px; }
@media print { .cd-live { display: none; } }
```

And this function, after the keeping script and before the kind's code, called once with the Board in `.cd-board`: `live(board)`. Copy it as it stands:

```js
// The card that asks about the position on view, only when the person asks: the engine's Line from Stockfish in this
// browser, free, and a question to Generate with the page's Study key. It shows where either can run.
function live(board) {
  const card = document.querySelector('.cd-live');
  const api = document.querySelector('meta[name="chessdrive-api"]')?.content;
  const meta = document.querySelector('meta[name="chessdrive-key"]');
  let key = meta?.content || '';
  meta?.remove();
  try { key ||= localStorage.getItem('chessdrive-key') || ''; } catch {}
  if (!card) return;
  const $ = (s) => card.querySelector(s);
  const [add, keyForm, tools, credit, lineOut, ask, answer] =
    ['.cd-live-add', '.cd-live-key', '.cd-live-tools', '.cd-live-credit', '.cd-live-line', '.cd-live-ask', '.cd-live-answer'].map($);
  // Where each part can run: Stockfish in this browser, and the API with or without a key.
  const sf = stockfish();
  let local = typeof Worker === 'function' && typeof WebAssembly === 'object', online = false;
  const show = () => {
    card.hidden = !(local || online);
    tools.hidden = !(local || (online && key));
    credit.hidden = !local;
    ask.hidden = !(online && key);
    add.hidden = !(online && !key);
  };
  const needKey = (why) => {
    add.querySelector('span').textContent = why;
    key = '';
    show();
  };
  show();
  if (api) {
    fetch(api + '/v1/models').then((r) => {
      if (!r.ok) return;
      online = true;
      if (!key) needKey('Questions here need a ChessDrive key.');
      show();
    }).catch(() => {});
  }
  add.querySelector('button').onclick = () => { keyForm.hidden = false; keyForm.querySelector('input').focus(); };
  keyForm.onsubmit = (e) => {
    e.preventDefault();
    const input = keyForm.querySelector('input');
    if (!/^[a-z]+_[0-9A-Za-z]{20,}$/.test(input.value.trim())) return;
    key = input.value.trim();
    input.value = '';
    try { localStorage.setItem('chessdrive-key', key); } catch {}
    keyForm.hidden = true;
    show();
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
        try { localStorage.removeItem('chessdrive-key'); } catch {}
        needKey(code === 'expired_api_key' ? 'This page’s key has expired.' : 'This page’s key no longer works.');
      }
      if (code === 'key_limit_reached') throw new Error('This page’s key has spent its dollar for today. It works again tomorrow.');
      throw Object.assign(new Error(data.error?.message || 'ChessDrive didn’t answer. Try again.'), { code });
    }
  }

  // The engine's answer for each position asked about, so a question reuses it: Stockfish in this browser, or the
  // Engine API with the key where the browser can't run it.
  const answers = new Map();
  const engine = (fen) => {
    if (!answers.has(fen)) {
      const asked = sf().then((s) => {
        if (s) return s(fen);
        if (!online || !key) throw new Error('The engine can’t run in this browser.');
        return call('/v1/engine', { engine: 'stockfish', position: { fen } });
      });
      answers.set(fen, asked.catch((e) => {
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

// Stockfish 18 in this browser (stockfish.js, GPL-3.0). The function it returns starts it the first time it's called,
// and resolves to a function from a FEN to the engine's answer as Engine gives it, scores from White's side and moves
// as {san, uci}, or to null where the browser can't run it. A Worker can't start from another site, so it starts from a Blob that loads the engine; the engine
// finds its .wasm from the address after the Worker's #.
function stockfish(depth = 18) {
  const url = 'https://unpkg.com/stockfish@18.0.8/bin/stockfish-18-lite-single';
  const probe = document.createElement('chessdrive-board');
  // A Line's UCI moves in SAN too, from the Board, which plays them and writes them in its PGN.
  const moves = (fen, uci) => {
    probe.set({ fen });
    const played = [];
    for (const u of uci.slice(0, 12)) {
      if (!probe.play(u)) break;
      played.push(u);
    }
    const san = (probe.state.pgn || '').split('\n\n').pop().split(/\s+/)
      .filter((t) => t && !/^\d+\.+$/.test(t) && !/^(\*|1-0|0-1|1\/2-1\/2)$/.test(t));
    return played.map((u, i) => ({ san: san[i], uci: u }));
  };
  let started = null;
  return () => (started ||= new Promise((resolve) => {
    let worker;
    try {
      const src = URL.createObjectURL(new Blob(['importScripts(' + JSON.stringify(url + '.js') + ');'], { type: 'text/javascript' }));
      worker = new Worker(src + '#' + encodeURIComponent(url + '.wasm'));
    } catch {
      return resolve(null);
    }
    const fail = () => { worker.terminate(); resolve(null); };
    const late = setTimeout(fail, 30000);
    worker.onerror = () => { clearTimeout(late); fail(); };
    let listen = null, queue = Promise.resolve();
    worker.onmessage = ({ data }) => {
      const line = String(data);
      if (line === 'uciok') {
        clearTimeout(late);
        resolve(search);
      }
      listen?.(line);
    };
    // One search at a time, each after the last, whether or not it found a move.
    const search = (fen) => {
      const run = queue.then(() => new Promise((done, failed) => {
        let last = '';
        listen = (line) => {
          if (/^info .* multipv 1 .* pv /.test(line) && !/ (lower|upper)bound /.test(line)) last = line;
          if (!line.startsWith('bestmove')) return;
          listen = null;
          const score = last.match(/ score (cp|mate) (-?\d+)/), pv = last.split(' pv ')[1]?.split(' ') || [];
          const line1 = { cp: null, mate: null, moves: moves(fen, pv) };
          if (!score || !line1.moves.length) return failed(new Error('The engine found no move here.'));
          const sign = fen.split(' ')[1] === 'b' ? -1 : 1;
          line1[score[1]] = sign * Number(score[2]);
          done({ lines: [line1], best_move: line1.moves[0] });
        };
        worker.postMessage('position fen ' + fen);
        worker.postMessage('go depth ' + depth);
      }));
      queue = run.catch(() => {});
      return run;
    };
    worker.postMessage('uci');
  }));
}
```

- The card never runs a paid call on its own: Stockfish starts on "Engine's line" or a question, in the browser, and Generate runs on a question. A question reuses the engine's answer for that position. The Engine API runs only where the browser can't run Stockfish, with the key.
- The answers go in with `textContent`, and stay on screen only while their position is on view.
- In the kind's code, set the Board's `marks` and `eval` as before: the card sets them only when the person asks, and a move or step clears its text.
