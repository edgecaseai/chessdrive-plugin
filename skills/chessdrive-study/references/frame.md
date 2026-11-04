# The frame

Every Study is the same page: ChessDrive's colours and type, a header that says what the page is, the Board, and a panel beside it on a wide screen and under it on a narrow one. The kind's reference says what goes in each part. Copy the three blocks below as they stand, then fill them in.

## The page

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Your game against Ana</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:wght@600&family=Geist+Mono:wght@400;500&family=Inter:wght@400;500;600&display=swap">
<script src="https://cdn.jsdelivr.net/npm/@chessdrive/board@0.1.2/dist/board.umd.js"></script>
<meta name="chessdrive-api" content="https://api-staging.chessdrive.io">
<style>/* The style, below */</style>
</head>
<body>
<div class="cd-page" data-moves>
  <header class="cd-head">
    <h1>Your game against Ana</h1>
    <p>Step through with ← → or the moves, and play your own to try an idea.</p>
  </header>
  <div class="cd-board">
    <chessdrive-board id="board"></chessdrive-board>
    <button class="cd-btn" id="back" hidden>Back to the game</button>
  </div>
  <aside class="cd-panel">
    <section class="cd-card"><h2>Turning points</h2>…</section>
  </aside>
  <p class="cd-keep" hidden><button class="cd-btn" data-keep="download">Download</button> <button class="cd-btn" data-keep="pdf">Save as PDF</button></p>
  <section class="cd-more">…</section>
  <footer class="cd-made">Made with <a href="https://platform-staging.chessdrive.io/?utm_source=study&utm_campaign=KIND" target="_blank" rel="noopener">ChessDrive</a></footer>
</div>
<script>
(() => {
  /* The keeping script, below, first; then the kind's page code. */
})();
</script>
</body>
</html>
```

- **`<title>` and `<h1>`** say what the page is, in the person's words: "Your game against Ana", "Your mistakes", "Ana's openings against 1.e4". The `<p>` under it says how to use the page in one line.
- **`data-moves`** on `.cd-page` leaves room for the Board's move list: keep it when the Board in `.cd-board` has `moves: true`, and drop it when it hasn't.
- **`.cd-board`** holds the Board and its "Back to the game" button. A page with several Boards, such as a Worksheet, puts the one to play in `.cd-board` and the rest in `.cd-more`.
- **`.cd-panel`** holds the kind's panel, in `.cd-card`s, each with an `<h2>`. Put what the person needs while on the Board here, first things first. A Board the person moves on gets the "Ask about this position" card first, and the page's `chessdrive-api` and `chessdrive-key` `<meta>`s, as [live.md](live.md) says.
- **`.cd-more`** holds what can wait below, across the page: a grid of diagrams, what the page rests on. Leave it out if there's nothing.
- **Buttons** are `.cd-btn`, and `.cd-btn.cd-main` for the one to press next. A list the person clicks through is `.cd-list` of `<button>`s; mark the one on view with `aria-current="true"`. A small label is `.cd-tag`, with `.cd-inaccuracy`, `.cd-mistake` or `.cd-blunder` for a verdict.
- **Numbers and moves** go in `.cd-num`, which sets them in the mono face.

Load nothing else: no other script, font or stylesheet. The page calls nothing but the keeping script's fetch and live.md's card.

## The style

The site's tokens, light and dark, then the frame. It keeps the Board and its buttons in view on any screen: on a wide one the Board's size follows the window's height, and on a narrow one the page is one column with the Board first.

```css
:root {
  color-scheme: light dark;
  --font-display: 'Fraunces', Georgia, serif;
  --font-body: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
  --font-mono: 'Geist Mono', ui-monospace, Menlo, monospace;
  --paper: oklch(0.972 0.025 85);
  --paper-2: oklch(0.942 0.0375 85);
  --surface: oklch(0.993 0.01125 85);
  --line: oklch(0.885 0.0325 85);
  --line-strong: oklch(0.8 0.035 85);
  --ink: oklch(0.21 0.012 52);
  --ink-2: oklch(0.4 0.012 52);
  --ink-3: oklch(0.52 0.012 52);
  --brand: oklch(0.68 0.17 52);
  --brand-strong: oklch(0.52 0.1445 52);
  --brand-soft: oklch(0.94 0.0476 52);
  --ok: oklch(0.5 0.1 150);
  --ok-soft: oklch(0.94 0.035 150);
  --danger: oklch(0.53 0.19 27);
  --danger-soft: oklch(0.94 0.04 27);
  --focus: var(--brand-strong);
  --inaccuracy: #a16207;
  --mistake: #c2410c;
  --blunder: #b91c1c;
  --radius: 4px;
  --radius-card: 6px;
  --cd-gap: 16px;
  --cd-panel: 340px;
  --cd-side: 40px;
  --cd-room: 316px;
}
@media screen and (prefers-color-scheme: dark) {
  :root {
    --paper: oklch(0.165 0.01 52);
    --paper-2: oklch(0.2 0.011 52);
    --surface: oklch(0.192 0.011 52);
    --line: oklch(0.275 0.012 52);
    --line-strong: oklch(0.36 0.013 52);
    --ink: oklch(0.935 0.0225 85);
    --ink-2: oklch(0.78 0.015 85);
    --ink-3: oklch(0.62 0.012 52);
    --brand: oklch(0.745 0.1598 52);
    --brand-strong: oklch(0.81 0.1326 52);
    --brand-soft: oklch(0.29 0.0544 52);
    --ok: oklch(0.74 0.11 150);
    --ok-soft: oklch(0.27 0.04 150);
    --danger: oklch(0.7 0.16 27);
    --danger-soft: oklch(0.28 0.06 27);
    --focus: var(--brand);
  }
}
@media print { :root { color-scheme: light; } }

*, *::before, *::after { box-sizing: border-box; }
body { margin: 0; background: var(--paper); color: var(--ink); font: 15px/1.5 var(--font-body); -webkit-font-smoothing: antialiased; }
:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; }
h1 { margin: 0; font: 600 clamp(20px, 3.2vw, 26px)/1.15 var(--font-display); letter-spacing: -0.02em; text-wrap: balance; }
h2 { margin: 0 0 8px; font-size: 13px; font-weight: 600; color: var(--ink-2); }
p { margin: 0 0 8px; }
.cd-num { font-family: var(--font-mono); font-variant-numeric: tabular-nums; }

.cd-page { --cd-board: calc(clamp(200px, 100svh - var(--cd-room), 560px) + var(--cd-side));
  display: grid; grid-template-columns: minmax(0, 1fr); gap: var(--cd-gap); max-width: 1220px; margin: 0 auto; padding: var(--cd-gap); }
.cd-page[data-moves] { --cd-room: 430px; }
.cd-head p { margin: 4px 0 0; color: var(--ink-2); font-size: 14px; }
.cd-keep { display: flex; flex-wrap: wrap; gap: 8px; margin: 0; }
.cd-keep[hidden] { display: none; }
.cd-board { display: grid; gap: 10px; justify-items: start; width: 100%; max-width: var(--cd-board); min-width: 0; margin-inline: auto; }
chessdrive-board { display: block; width: 100%; --board-font: var(--font-body); --board-mono: var(--font-mono); --board-display: var(--font-display); }
.cd-panel { display: grid; gap: 12px; align-content: start; min-width: 0; }
.cd-more { min-width: 0; }
@media (min-width: 960px) {
  .cd-page, .cd-page[data-moves] { --cd-room: 180px; grid-template-columns: minmax(0, var(--cd-board)) var(--cd-panel); grid-template-rows: auto auto 1fr;
    justify-content: center; gap: 12px 28px; grid-template-areas: "board head" "board keep" "board panel" "more more" "made made"; }
  .cd-page[data-moves] { --cd-side: 248px; }
  .cd-head { grid-area: head; }
  .cd-board { grid-area: board; margin: 0; }
  .cd-keep { grid-area: keep; }
  .cd-panel { grid-area: panel; }
  .cd-more { grid-area: more; }
  .cd-made { grid-area: made; }
}

.cd-card { background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius-card); padding: 12px 14px; }
.cd-btn { display: inline-flex; align-items: center; justify-content: center; gap: 6px; height: 32px; padding: 0 12px; border: 1px solid var(--line-strong);
  border-radius: var(--radius); background: var(--surface); color: var(--ink); font: 500 13.5px var(--font-body); cursor: pointer; white-space: nowrap; }
.cd-btn:hover:not(:disabled) { background: var(--paper-2); }
.cd-btn:active:not(:disabled) { transform: scale(0.96); }
.cd-btn:disabled { opacity: 0.45; cursor: not-allowed; }
.cd-btn[hidden] { display: none; }
.cd-btn.cd-main { background: var(--ink); border-color: var(--ink); color: var(--paper); }
.cd-btn.cd-main:hover:not(:disabled) { background: color-mix(in oklch, var(--ink), var(--paper) 16%); }
.cd-list { list-style: none; margin: 0; padding: 0; display: grid; gap: 2px; }
.cd-list button { display: flex; gap: 8px; align-items: baseline; width: 100%; padding: 6px 8px; border: 0; border-radius: var(--radius);
  background: none; color: inherit; font: inherit; font-size: 14px; text-align: left; cursor: pointer; }
.cd-list button:hover { background: var(--paper-2); }
.cd-list button[aria-current="true"] { background: var(--brand-soft); box-shadow: inset 2px 0 var(--brand); }
.cd-tag { display: inline-flex; align-items: center; height: 20px; padding: 0 6px; border-radius: 2px; background: var(--paper-2); color: var(--ink-2); font-size: 12px; font-weight: 500; white-space: nowrap; }
.cd-tag.cd-inaccuracy, .cd-tag.cd-mistake, .cd-tag.cd-blunder { color: #fff; }
.cd-inaccuracy { background: var(--inaccuracy); }
.cd-mistake { background: var(--mistake); }
.cd-blunder { background: var(--blunder); }
.cd-made { color: var(--ink-3); font-size: 13px; }
.cd-made a { color: var(--ink); text-decoration: none; background: linear-gradient(var(--brand), var(--brand)) 0 100% / 100% 2px no-repeat; padding-bottom: 1px; }

@media print {
  .cd-page { display: block; max-width: none; padding: 0; }
  .cd-page > * + * { margin-top: 12px; }
  .cd-keep, .cd-btn { display: none !important; }
  .cd-board { max-width: 15cm; margin: 0; }
  .cd-card, .cd-more > * { break-inside: avoid; }
  .cd-tag { background: none !important; color: var(--ink) !important; border: 1px solid var(--line-strong); }
  .cd-made { position: fixed; bottom: 0; }
}
@media (prefers-reduced-motion: reduce) { .cd-btn:active:not(:disabled) { transform: none; } }
```

Write the kind's own styles after it, from these tokens only: no colour, font or radius of your own. A graph is drawn in `--ink-2` on `--paper-2`, with verdicts in their own colours and the ply on view in `--brand`.

## The keeping script

First in the page's one script, before the kind's code. In a coding agent's file it shows Download, which saves a copy with the Board's script inside it, so the copy opens with no internet, and Save as PDF. In Claude and other apps the page isn't a file of the person's, the host blocks both, and the buttons stay hidden: the app has its own download and share.

```js
// The page as it was built, before the page code changes it, for Download: never with its Study key.
const built = '<!doctype html>\n' + document.documentElement.outerHTML.replace(/<meta name="chessdrive-key"[^>]*>\n?/, '');
const keep = document.querySelector('.cd-keep');
if (keep && location.protocol === 'file:') {
  keep.hidden = false;
  keep.querySelector('[data-keep="pdf"]').onclick = () => window.print();
  keep.querySelector('[data-keep="download"]').onclick = async ({ currentTarget: button }) => {
    let html = built;
    const tag = html.match(/<script src="(https:\/\/cdn\.jsdelivr\.net\/npm\/@chessdrive\/board@[^"]+)"><\/script>/);
    if (tag) {
      try {
        const code = await (await fetch(tag[1])).text();
        html = html.replace(tag[0], () => '<script>' + code.replaceAll('</' + 'script', '<\\/' + 'script') + '</' + 'script>');
      } catch {
        button.textContent = 'Download (the copy needs the internet)';
      }
    }
    const link = document.createElement('a');
    link.href = URL.createObjectURL(new Blob([html], { type: 'text/html' }));
    link.download = (document.title.replace(/[\\/:*?"<>|]+/g, ' ').trim() || 'Study') + '.html';
    link.click();
  };
}
// The Board prints light, whatever the screen's setting.
const boards = () => document.querySelectorAll('chessdrive-board:not([data-light])');
let printing = [];
addEventListener('beforeprint', () => { printing = [...boards()]; printing.forEach((b) => b.setAttribute('data-light', '')); });
addEventListener('afterprint', () => printing.forEach((b) => b.removeAttribute('data-light')));
```
