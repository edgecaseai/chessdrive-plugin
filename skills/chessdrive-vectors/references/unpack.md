# Unpack the scripts

Claude's plugin directory takes no script files, so this plugin holds each of its Python scripts as text, in a `.py.md` file in its Skill's `scripts` folder. This step copies the plugin's Skills to `~/.cache/chessdrive/skills` on the machine your code runs on, and writes each script there as the `.py` file it is. It does nothing else: it makes no network call, installs nothing and runs none of the scripts. It's safe to run again, and a session needs it once.

Run it with the folder this plugin's Skills sit in, which is the parent of the folder your app gave you for the Skill you're in:

```bash
python3 - "<the folder of the Skill you're in>/.." <<'EOF'
import pathlib, re, shutil, sys
skills = pathlib.Path(sys.argv[1]).resolve()
out = pathlib.Path.home() / ".cache" / "chessdrive" / "skills"
for src in sorted(skills.glob("chessdrive-*/**/*")):
    if not src.is_file():
        continue
    to = out / src.relative_to(skills)
    to.parent.mkdir(parents=True, exist_ok=True)
    if src.name.endswith(".py.md"):
        text = src.read_text(encoding="utf-8")
        fence = re.search(r"^(`{3,})python\n", text, re.M)
        end = text.index("\n" + fence.group(1) + "\n", fence.end())
        to.with_name(src.name[:-3]).write_text(text[fence.end():end + 1], encoding="utf-8")
    else:
        shutil.copyfile(src, to)
print(out)
EOF
```

It prints the folder. From then on a Skill's `<this Skill's folder>` is its folder inside the printed one, such as `<the printed folder>/chessdrive-prep`. The scripts find each other, and the Skills' reference files, by their place in that folder, so read and run everything from there, never from a copy of your own, and never by typing a script out again.

If `python3` isn't found, the Skills' scripts can't run either: do as step 4 of `set-up.md` beside this file says, then come back here.
