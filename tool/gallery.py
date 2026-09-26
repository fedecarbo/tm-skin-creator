"""The page of all skins: one picture per skin, newest first, the installed ones marked.

    python -m tool.gallery          refresh the list, serve, open http://localhost:8765/gallery.html

The page (viewer/gallery.html) reads /data/gallery.json, written here from skins/*/ and
skins/installed.json, and shows each skin's thumb.png (copied to the work folder's viewer
data). Clicking a picture opens the skin in the 3D viewer. The viewer's list of skins reads the
same file.

A round of concepts (a loose idea's two or three takes, each a different reading) is recorded in
skins/rounds.json by `python -m tool.skin round "<title>" <skin> <skin> ...`: its title, the user's
words and its takes, lettered A, B, C in that order. Each take's entry in gallery.json carries its
round, so the Lab shows a switch between the takes (the user's pick, 2026-09-26: "A · Switch in
the title", CHECKLIST.md "The Lab").

Newest first means by when a skin was made: the commit that added its design.py, which every
copy of the repo agrees on (a fresh clone gives every file the same modified time, so file times
can't order skins on a second computer). A skin not committed yet is newer than all of those and
goes by its design.py's time. Without git, file times it is.
"""

import datetime
import json
import re
import shutil
import subprocess
import webbrowser

from tool import install, paths, view

DATA = view.DATA
ROUNDS = paths.SKINS / "rounds.json"


def words_of(folder):
    notes = folder / "notes.md"
    if not notes.exists():
        return ""
    for line in notes.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            return line.lstrip("-* ").strip('"“”')
    return ""


def title_of(name):
    """The name as the pages show it: "TSC_CMYK_Peel_More" -> "CMYK Peel More"."""
    name = name.removeprefix("TSC_").replace("_", " ")
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name)


def load_rounds():
    return json.loads(ROUNDS.read_text(encoding="utf-8")) if ROUNDS.exists() else []


def twist(name, names):
    """A take's title: what its name adds to the round's shared start. TSC_ChaosElegance_Thrown
    among TSC_ChaosElegance_* -> "Thrown"; a take that adds nothing is its name's last word."""
    parts = [n.split("_") for n in names]
    shared = 0
    while all(len(p) > shared + 1 and p[shared] == parts[0][shared] for p in parts):
        shared += 1
    rest = name.split("_")[shared:] or name.split("_")[-1:]
    return title_of("_".join(rest))


def record_round(title, names, words=""):
    """Record a round of concepts (replacing one with the same title): its takes are the skins,
    lettered A, B, C in this order. A name may carry its own title: "TSC_X_Y=Worn flag"."""
    takes = []
    for item in names:
        name, _, own = item.partition("=")
        if not (paths.SKINS / name / "design.py").exists():
            raise FileNotFoundError(f"no skin called {name}")
        takes.append({"name": name, "title": own})
    plain = [t["name"] for t in takes]
    for t in takes:
        t["title"] = t["title"] or twist(t["name"], plain)
    rounds = [r for r in load_rounds() if r["title"].lower() != title.lower()]
    rounds.append({"title": title, "words": words, "made": datetime.date.today().isoformat(), "takes": takes})
    ROUNDS.write_text(json.dumps(rounds, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return rounds[-1]


def rounds_by_skin():
    """{skin name: its round, as the Lab shows it}: the title, the words, and every take with its
    letter. A skin in two rounds is in the newer one."""
    out = {}
    for r in load_rounds():
        takes = [{"key": chr(65 + k), "name": t["name"], "title": t["title"]} for k, t in enumerate(r["takes"])]
        for t in takes:
            out[t["name"]] = {"title": r["title"], "words": r.get("words", ""), "key": t["key"], "takes": takes}
    return out


def first_commits():
    """{skin name: unix time of the commit that added its design.py}. {} without git."""
    try:
        # safe.directory: in the container the repo belongs to another user, which git refuses.
        out = subprocess.run(["git", "-c", "safe.directory=*", "log", "--diff-filter=A", "--format=%ct", "--name-only",
                              "--", "skins/*/design.py"], cwd=paths.REPO, capture_output=True, text=True, timeout=30, check=True).stdout
    except (OSError, subprocess.SubprocessError):
        return {}
    times, when = {}, None
    for line in out.splitlines():  # newest commit first, so an older add of the same file wins
        if line.isdigit():
            when = int(line)
        elif line.startswith("skins/") and when is not None:
            times[line.split("/")[1]] = when
    return times


def refresh():
    manifest = install.load_manifest()
    committed = first_commits()
    rounds = rounds_by_skin()
    entries = []
    for folder in paths.SKINS.iterdir():
        if not folder.is_dir() or not (folder / "design.py").exists():
            continue
        thumb = folder / "thumb.png"
        stamp = thumb.stat().st_mtime if thumb.exists() else (folder / "design.py").stat().st_mtime
        made = committed.get(folder.name) or (folder / "design.py").stat().st_mtime
        target = DATA / "skins" / folder.name
        target.mkdir(parents=True, exist_ok=True)
        if thumb.exists():
            shutil.copyfile(thumb, target / "thumb.png")
        entries.append({
            "name": folder.name,
            "title": title_of(folder.name),
            "words": words_of(folder),
            "thumb": f"skins/{folder.name}/thumb.png" if thumb.exists() else None,
            "installed": f"{folder.name}.zip" in manifest,
            "installed_at": manifest.get(f"{folder.name}.zip", {}).get("installed"),  # when the skin was last put in the game
            "viewable": (target / "skin.json").exists(),
            "stamp": stamp,  # the picture's time, so pages reload it when it changes
            "made": made,
            "when": datetime.datetime.fromtimestamp(made).strftime("%Y-%m-%d %H:%M"),
            "round": rounds.get(folder.name),  # the round of concepts it's a take in, or None
        })
    entries.sort(key=lambda e: (-e["made"], e["title"]))
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "gallery.json").write_text(json.dumps(entries, indent=1), encoding="utf-8")
    return entries


def main():
    refresh()
    url = f"http://localhost:{view.PORT}/gallery.html"
    try:
        server = view.start_server(view.PORT)
    except OSError:
        server = None
    print(f"gallery: {url}", flush=True)
    webbrowser.open(url)
    if server:
        import threading
        threading.Event().wait()


if __name__ == "__main__":
    main()
