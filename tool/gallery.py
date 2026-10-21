"""The list of skins, newest first, the installed ones marked: "My skins" on the Lab's page, and the
lots they're parked in on the Lab's world (viewer/lab-garage.js), the user's own groups.

The page (viewer/index.html) reads /data/gallery.json, written here (refresh) from skins/*/ and
skins/installed.json, and shows each skin's thumb.png (copied to the work folder's viewer data). Each entry
says its lot; /data/lots.json lists the lots in the user's order. The Lab's server (tool/labserver.py) calls
`fresh` when a page asks for either: they're brought up to date from what the tools wrote (a thumb, a design,
a record, the game's list) and what the Lab wrote (sets, notes, lots), so no command refreshes them.

The lots, skins/lots.json (committed: both computers see the same world; a skin in no lot is in New):

    python -m tool.gallery lots                      the lots and their cars
    python -m tool.gallery lot new "<name>"          a new, empty lot
    python -m tool.gallery lot move <skin> "<name>"  a car to that lot (made if new; "New" takes it out of every lot)
    python -m tool.gallery lot rename "<old>" "<new>"
    python -m tool.gallery lot drop "<name>"         the lot goes, its cars to New

Newest first means by when a skin was made: the commit that added its design.py, which every
copy of the repo agrees on (a fresh clone gives every file the same modified time, so file times
can't order skins on a second computer). A skin not committed yet is newer than all of those and
goes by its design.py's time. Without git, file times it is.
"""

import argparse
import datetime
import json
import shutil
import subprocess
import sys

from tool import install, notes, paths, progress, view

DATA = view.DATA
LOTS = paths.SKINS / "lots.json"
NEW = "New"


def words_of(folder):
    record = folder / "notes.md"
    if not record.exists():
        return ""
    for line in record.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            return line.lstrip("-* ").strip('"“”')
    return ""


def first_commits():
    """{skin name: unix time of the commit that added its design.py}. {} without git."""
    try:
        # safe.directory: a repo owned by another user (the Mac's old container) is refused without it.
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


def fresh():
    """gallery.json brought up to date when anything it's made of is newer than it."""
    out = DATA / "gallery.json"
    if not out.exists():
        return refresh()
    sources = [*paths.SKINS.glob("*/thumb.png"), *paths.SKINS.glob("*/design.py"), *paths.SKINS.glob("*/notes.md"),
               *paths.SKINS.glob("*/sets.json"), *(DATA / "skins").glob("*/skin.json"),
               paths.INSTALLED_MANIFEST, LOTS, notes.HOME / "notes.json", paths.SKINS]
    newest = max((p.stat().st_mtime for p in sources if p.exists()), default=0)
    return refresh() if newest > out.stat().st_mtime else None


def refresh():
    manifest = install.load_manifest()
    committed = first_commits()
    stands = notes.stands()  # where each skin stands, for the world
    lots = load_lots()
    lot_of = {s: lot["name"] for lot in reversed(lots) for s in lot["skins"]}  # a skin named twice: in the first lot
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
            "title": progress.title_of(folder.name),
            "words": words_of(folder),
            "thumb": f"skins/{folder.name}/thumb.png" if thumb.exists() else None,
            "installed": f"{folder.name}.zip" in manifest,
            "installed_at": manifest.get(f"{folder.name}.zip", {}).get("installed"),  # when the skin was last put in the game
            "viewable": (target / "skin.json").exists(),
            "stamp": stamp,  # the picture's time, so pages reload it when it changes
            "made": made,
            "when": datetime.datetime.fromtimestamp(made).strftime("%Y-%m-%d %H:%M"),
            "stand": stands.get(folder.name),  # tool/notes.py stands: its last event, its day, what's open
            "lot": lot_of.get(folder.name),  # the user's group it's parked in, or None: New
        })
    entries.sort(key=lambda e: (-e["made"], e["title"]))
    DATA.mkdir(parents=True, exist_ok=True)
    paths.write(DATA / "gallery.json", json.dumps(entries, indent=1))
    paths.write(DATA / "lots.json", json.dumps({"lots": lots}, indent=1))
    return entries


# ---- the lots ----

def load_lots():
    """[{name, skins: [...]}] in the user's order; [] before any."""
    if not LOTS.exists():
        return []
    return json.loads(LOTS.read_text(encoding="utf-8")).get("lots", [])


def describe_lots(lots):
    if not lots:
        return "no lots yet: every car is in New"
    return "\n".join(f"{lot['name']}: " + (", ".join(lot["skins"]) or "empty") for lot in lots)


def lot(command, args):
    """One change to the lots, written to skins/lots.json, then the list refreshed so the world shows it."""
    lots = load_lots()
    by = {lot["name"]: lot for lot in lots}
    if command == "new":
        (name,) = args
        if name in by or name == NEW:
            raise SystemExit(f"{name}: a lot already")
        lots.append({"name": name, "skins": []})
    elif command == "move":
        skin, name = args
        if not (paths.SKINS / skin).is_dir():
            raise SystemExit(f"{skin}: no such skin")
        for lot in lots:
            lot["skins"] = [s for s in lot["skins"] if s != skin]
        if name != NEW:
            if name not in by:
                by[name] = {"name": name, "skins": []}
                lots.append(by[name])
            by[name]["skins"].append(skin)
    elif command == "rename":
        old, new = args
        if old not in by:
            raise SystemExit(f"{old}: no such lot")
        if new in by or new == NEW:
            raise SystemExit(f"{new}: a lot already")
        by[old]["name"] = new
    elif command == "drop":
        (name,) = args
        if name not in by:
            raise SystemExit(f"{name}: no such lot")
        lots.remove(by[name])
    paths.write(LOTS, json.dumps({"lots": lots}, indent=1) + "\n")
    refresh()
    print(describe_lots(lots))


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["lots"]:
        print(describe_lots(load_lots()))
        return
    if argv[:1] == ["lot"]:
        ap = argparse.ArgumentParser(prog="python -m tool.gallery lot")
        ap.add_argument("command", choices=["new", "move", "rename", "drop"])
        ap.add_argument("args", nargs="*")
        a = ap.parse_args(argv[1:])
        need = {"new": 1, "move": 2, "rename": 2, "drop": 1}[a.command]
        if len(a.args) != need:
            ap.error(f"{a.command}: see the usage at the top of tool/gallery.py")
        lot(a.command, a.args)
        return
    for e in refresh():
        print(f"{e['name']:<28} {e['lot'] or NEW:<16} {e['when']}" + ("  in the game" if e["installed"] else ""))


if __name__ == "__main__":
    main()
