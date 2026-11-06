#!/usr/bin/env python3
"""Checks a Study before you hand it over, with no browser. Python 3.8 or later; Node, when it's there, checks the
scripts' syntax too.

    python3 check.py review.html

It checks what a page can get wrong without anyone seeing it: `DATA` parses, every script of the page's own runs
inside a function, no text goes in with `innerHTML`, the Board loads only from its pinned URL, the page holds no key
but its own Study key, and the footer is there. It prints one line a problem, with its line in the file, and exits 1;
or prints `ok` and exits 0. What a check can't see, such as an error once the page runs, the frame shows on the page.
"""

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True  # keeps the Plugin's folder as it was installed

BOARD = "https://cdn.jsdelivr.net/npm/@chessdrive/board@0.1.2/dist/board.umd.js"
SCRIPT = re.compile(r"<script(?P<attrs>[^>]*)>(?P<code>.*?)</script>", re.S)
WRAPPED = re.compile(r"^\(\s*(?:\(\s*\)\s*=>|(?:async\s+)?function\b[^(]*\(\s*\))\s*\{.*\}\s*\)\s*\(\s*\)\s*;?$", re.S)
UNSAFE = re.compile(r"\.(?:innerHTML|outerHTML)\s*[+]?=|insertAdjacentHTML|document\.write")
KEY = re.compile(r"\b(?:ck|sk|cd)_[A-Za-z0-9]{20,}")
STUDY_KEY = re.compile(r'<meta name="chessdrive-key" content="[^"]*">')
SITE = "https://platform.chessdrive.io/"
FOOTER = re.compile(re.escape(f'<footer class="cd-made">Made with <a href="{SITE}?utm_source=study&') + r'(?:amp;)?utm_campaign=[a-z]+"')


def line_of(page, at):
    return page.count("\n", 0, at) + 1


def problems(page):
    found = []
    scripts = list(SCRIPT.finditer(page))
    sources = [re.search(r'\bsrc="([^"]*)"', s["attrs"]) for s in scripts]
    if [src[1] for src in sources if src] != [BOARD]:
        found.append((1, f"the page loads the Board once, from {BOARD}, and no other script"))
    for script, src in zip(scripts, sources):
        if src or "json" in script["attrs"]:
            continue
        code, at = script["code"], script.start("code")
        if not WRAPPED.match(code.strip()):
            found.append((line_of(page, at), "a script's code isn't all inside `(() => { … })();`"))
        for unsafe in UNSAFE.finditer(code):
            found.append((line_of(page, at + unsafe.start()), "text goes in with `textContent`, never `innerHTML`"))
        data = re.search(r"\bconst DATA\s*=\s*", code)
        if data:
            try:
                json.JSONDecoder().raw_decode(code, data.end())
            except ValueError as e:
                found.append((line_of(page, at + data.end()), f"DATA isn't JSON, as code writes it: {e.msg}"))
    if not any(re.search(r"\bconst DATA\s*=", s["code"]) for s in scripts) and "<chessdrive-board" in page:
        found.append((1, "the page has no `const DATA = {…}`"))
    for key in KEY.finditer(STUDY_KEY.sub("", page)):
        found.append((line_of(page, key.start()), "a key outside the page's own `chessdrive-key` <meta>"))
    if not FOOTER.search(page):
        found.append((1, f'the frame\'s footer, `<footer class="cd-made">Made with <a href="{SITE}?utm_source=study&utm_campaign=KIND"`, is missing'))
    return found + syntax(page, scripts, sources)


def syntax(page, scripts, sources):
    """Each script of the page's own through `node --check`, where Node is installed."""
    node, found = shutil.which("node"), []
    if not node:
        return found
    for script, src in zip(scripts, sources):
        if src or "json" in script["attrs"] or not script["code"].strip():
            continue
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
            f.write("\n" * (line_of(page, script.start("code")) - 1) + script["code"])
        done = subprocess.run([node, "--check", f.name], capture_output=True, text=True)
        Path(f.name).unlink()
        if done.returncode:
            where = re.search(r":(\d+)\n", done.stderr)
            error = next((l for l in done.stderr.splitlines() if "Error" in l), done.stderr.strip()[-200:])
            found.append((int(where[1]) if where else line_of(page, script.start("code")), error))
    return found


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    found = problems(Path(sys.argv[1]).read_text(encoding="utf-8"))
    for at, problem in sorted(found):
        print(f"line {at}: {problem}")
    print("ok" if not found else f"{len(found)} to fix")
    sys.exit(1 if found else 0)


if __name__ == "__main__":
    main()
