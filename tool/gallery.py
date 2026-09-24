"""The page of all skins: one picture per skin, newest first, the installed ones marked.

    python -m tool.gallery          refresh the list, serve, open http://localhost:8765/gallery.html

The page (viewer/gallery.html) reads /data/gallery.json, written here from skins/*/ and
skins/installed.json, and shows each skin's thumb.png (copied to the work folder's viewer
data). Clicking a picture opens the skin in the 3D viewer.
"""

import datetime
import json
import shutil
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


def refresh():
    manifest = install.load_manifest()
    entries = []
    for folder in paths.SKINS.iterdir():
        if not folder.is_dir() or not (folder / "design.py").exists():
            continue
        thumb = folder / "thumb.png"
        stamp = thumb.stat().st_mtime if thumb.exists() else (folder / "design.py").stat().st_mtime
        target = DATA / "skins" / folder.name
        target.mkdir(parents=True, exist_ok=True)
        if thumb.exists():
            shutil.copyfile(thumb, target / "thumb.png")
        entries.append({
            "name": folder.name,
            "words": words_of(folder),
            "thumb": f"skins/{folder.name}/thumb.png" if thumb.exists() else None,
            "installed": f"{folder.name}.zip" in manifest,
            "viewable": (target / "skin.json").exists(),
            "stamp": stamp,
            "when": datetime.datetime.fromtimestamp(stamp).strftime("%Y-%m-%d %H:%M"),
        })
    entries.sort(key=lambda e: -e["stamp"])
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
