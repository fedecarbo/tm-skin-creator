"""The page of all skins: one picture per skin, newest first, the installed ones marked.

    python -m tool.gallery          refresh the list, serve, open http://localhost:8765/gallery.html

The page (viewer/gallery.html) reads /data/gallery.json, written here from skins/*/ and
skins/installed.json, and shows each skin's thumb.png (copied to the work folder's viewer
data). Clicking a picture opens the skin in the 3D viewer. The viewer's list of skins reads the
same file.

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
            "installed_at": manifest.get(f"{folder.name}.zip", {}).get("installed"),  # the Lab's UV map room paints the latest
            "viewable": (target / "skin.json").exists(),
            "stamp": stamp,  # the picture's time, so pages reload it when it changes
            "made": made,
            "when": datetime.datetime.fromtimestamp(made).strftime("%Y-%m-%d %H:%M"),
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
