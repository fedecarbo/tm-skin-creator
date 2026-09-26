"""The page online: the skins in the game, in 3D, for the user's phone and their friends.

    python -m tool.publish          build the page and put it online (the address it prints)
    python -m tool.publish --here   build it and open it on this computer only

What's on it: the 3D viewer (viewer/) with the skins in the game (skins/installed.json) that have
a design in skins/, test cars left out. It opens on the newest one. viewer/public.css hides the
workbench: the parts list, part names on click, copying a camera, the Lab.

Lighter for phones: every texture is at most 2048² (a set of 4096² paint runs a phone out of
graphics memory) and a JPEG at quality 90 with full-resolution colour (4:4:4), except where
values must stay exact or keep an alpha: the glow codes, the glass tint, AO, the shared texels
(PNG). The mesh and the lighting are the viewer's own.

Where it lives: GitHub Pages serves this repo's gh-pages branch (Settings, Pages, Branch:
gh-pages, / (root)). The branch is one commit that each publish replaces with a force-push, so
GitHub never keeps old textures. It's built in the work folder's site/, a git repo of that
branch alone, so the OneDrive repo never holds it, and clones leave it out of their fetches (the
SessionStart hook in .claude/settings.json).
"""

import argparse
import datetime
import http.server
import json
import re
import shutil
import subprocess
import threading
import webbrowser
from pathlib import Path

from PIL import Image

from tool import gallery, install, paths, view

SITE = paths.WORK / "site"
BRANCH = "gh-pages"
PAGE = ("index.html", "gallery.html", "viewer.js", "public.css")
MAX = 2048
JPEG = {"quality": 90, "subsampling": 0, "optimize": True}
PORT = 8766


def _fresh(target, source):
    """True when target exists and is newer than source and this file."""
    return target.exists() and target.stat().st_mtime >= max(source.stat().st_mtime, Path(__file__).stat().st_mtime)


def _ext(slot):
    return ".png" if slot.endswith(("_Code", "_AO")) or slot == "Glass_T" else ".jpg"


def _texture(source, target, slot):
    """One of the viewer's texture slots, made lighter (see the top)."""
    if _fresh(target, source):
        return
    im = Image.open(source)
    if max(im.size) > MAX:
        scale = MAX / max(im.size)
        # Codes stay exact; colour keeps its edges; data (roughness, normals) averages, as a mip does.
        how = Image.NEAREST if slot.endswith("_Code") else Image.LANCZOS if slot.endswith(("_B", "_I")) else Image.BOX
        im = im.resize((round(im.width * scale), round(im.height * scale)), how)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.suffix == ".jpg":
        if slot == "Skin_Coat":
            im = im.getchannel("R")  # the viewer reads the varnish from R alone
        im.save(target, "JPEG", **JPEG)
    else:
        im.save(target, optimize=True)


def _copy(source, target):
    if not _fresh(target, source):
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def chosen():
    """The skins on the page, newest first: gallery.refresh()'s entries for the skins in the game
    that have a design, without test cars."""
    installed = {n.removesuffix(".zip") for n in install.load_manifest()}
    return [e for e in gallery.refresh() if e["name"] in installed and "Test" not in e["name"].split("_")]


def build():
    """Write the page into SITE. Returns the gallery entries on it."""
    view.export_mesh()
    view.ensure_hdri()
    view.ensure_stock()
    skins = chosen()
    if not skins:
        raise SystemExit("No skins in the game yet, so nothing to put online.")
    out = SITE / "data"
    kept = {SITE / ".nojekyll"}  # served as is: no Jekyll, which would drop files starting with _
    SITE.mkdir(parents=True, exist_ok=True)
    (SITE / ".nojekyll").touch()

    newest = skins[0]["name"]
    head = ('<link rel="stylesheet" href="public.css">\n'
            '<script>/* tool/publish.py: a link that names no skin opens the newest */\n'
            'const q = new URLSearchParams(location.search);\n'
            f'if (!q.has("skin")) {{ q.set("skin", "{newest}"); history.replaceState(null, "", "?" + q); }}\n'
            '</script>\n')
    for name in PAGE:
        source, target = paths.REPO / "viewer" / name, SITE / name
        if name.endswith(".html"):
            html = source.read_text(encoding="utf-8")
            if "</head>" not in html:
                raise ValueError(f"{source}: no </head> to add the page's style to")
            extra = head if name == "index.html" else '<link rel="stylesheet" href="public.css">\n'
            target.write_text(html.replace("</head>", extra + "</head>", 1), encoding="utf-8")
        else:
            _copy(source, target)
        kept.add(target)
    for source in (paths.REPO / "viewer" / "lib").rglob("*"):
        if source.is_file():
            target = SITE / source.relative_to(paths.REPO / "viewer")
            _copy(source, target)
            kept.add(target)

    for name in ("car.json", "car.bin", "parts.json", *(f"{h}.hdr" for h in view.HDRIS),
                 *(p.name for p in view.DATA.glob("*_Shared.png"))):
        _copy(view.DATA / name, out / name)
        kept.add(out / name)

    entries = []
    for e in skins:
        name = e["name"]
        folder = view.DATA / "skins" / name
        if not (folder / "skin.json").exists():
            view.skin_from_build(name)
        skin = json.loads((folder / "skin.json").read_text())
        urls = {}
        for slot, url in skin["textures"].items():
            if url is None:
                urls[slot] = None
                continue
            where = "stock" if url.startswith("stock/") else f"skins/{name}"
            urls[slot] = f"{where}/{slot}{_ext(slot)}"
            _texture(view.DATA / url, out / urls[slot], slot)
            kept.add(out / urls[slot])
        target = out / "skins" / name
        target.mkdir(parents=True, exist_ok=True)
        (target / "skin.json").write_text(json.dumps({"name": name, "textures": urls}, indent=1))
        kept.add(target / "skin.json")
        thumb = paths.SKINS / name / "thumb.png"
        if thumb.exists() and not _fresh(target / "thumb.jpg", thumb):
            Image.open(thumb).convert("RGB").save(target / "thumb.jpg", "JPEG", **JPEG)
        if thumb.exists():
            kept.add(target / "thumb.jpg")
        # All of them are in the game, so no badge; the words in notes.md are Claude's, not for friends.
        entries.append({**e, "words": "", "installed": False, "viewable": True,
                        "thumb": f"skins/{name}/thumb.jpg" if thumb.exists() else None})
    (out / "gallery.json").write_text(json.dumps(entries, indent=1))
    kept.add(out / "gallery.json")

    for f in sorted(SITE.rglob("*"), reverse=True):  # what's no longer on the page
        if ".git" in f.relative_to(SITE).parts:
            continue
        if f.is_file() and f not in kept:
            f.unlink()
        elif f.is_dir() and not any(f.iterdir()):
            f.rmdir()
    return entries


def _repo_git(*args):
    return subprocess.run(["git", "-C", str(paths.REPO), *args], capture_output=True, text=True, check=True).stdout.strip()


def address():
    """The page's address, from this repo's GitHub remote."""
    m = re.search(r"github\.com[:/]([^/]+)/(.+?)(?:\.git)?$", _repo_git("remote", "get-url", "origin"))
    return f"https://{m.group(1).lower()}.github.io/{m.group(2)}/"


def push(entries):
    """Replace the gh-pages branch on GitHub with SITE, as one commit."""
    def git(*args, check=True):
        return subprocess.run(["git", "-C", str(SITE), *args], capture_output=True, text=True, check=check)

    if not (SITE / ".git").exists():
        git("init", "-q", "-b", BRANCH)
        git("remote", "add", "origin", _repo_git("remote", "get-url", "origin"))
    git("add", "-A")
    first = git("rev-parse", "-q", "--verify", "HEAD", check=False).returncode != 0
    if first or git("status", "--porcelain").stdout.strip():
        who = ("-c", f"user.name={_repo_git('config', 'user.name')}", "-c", f"user.email={_repo_git('config', 'user.email')}")
        message = f"The skins page, {datetime.date.today()}: " + ", ".join(e["title"] for e in entries)
        git(*who, "commit", "-q", *([] if first else ["--amend"]), "-m", message)
    pushed = git("push", "-q", "--force", "origin", BRANCH, check=False)
    if pushed.returncode:
        raise SystemExit(f"The push to GitHub failed:\n{pushed.stderr}")
    git("reflog", "expire", "--expire=now", "--all")  # keep only what's online
    git("gc", "-q", "--prune=now")


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**view.Handler.extensions_map, ".jpg": "image/jpeg", ".css": "text/css"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(SITE), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *args):
        pass


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--here", action="store_true", help="build it and open it on this computer, without putting it online")
    a = ap.parse_args()
    entries = build()
    size = sum(f.stat().st_size for f in SITE.rglob("*") if f.is_file() and ".git" not in f.relative_to(SITE).parts)
    print(f"page: {len(entries)} skins ({', '.join(e['title'] for e in entries)}), {size / 1e6:.0f} MB", flush=True)
    if a.here:
        server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        url = f"http://localhost:{PORT}/"
        print(f"here: {url}", flush=True)
        webbrowser.open(url)
        threading.Event().wait()
    push(entries)
    print(f"online: {address()} (GitHub takes a minute or two to update it)")


if __name__ == "__main__":
    main()
