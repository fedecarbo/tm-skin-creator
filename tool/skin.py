"""Run a skin's design script: show it in the viewer, or build and install it.

    python -m tool.skin show <name>            paint it, put it in the viewer, snapshot it
    python -m tool.skin show <name> --open     ... and open the viewer in the browser
    python -m tool.skin install <name>         write the DDS files and the zip, install it
    python -m tool.skin list                   every skin, newest first

Paints take turns: one at a time on a computer (TSC_PAINTS=<n> for more), since each needs a few
GB and the Mac's old container (7.7 GB) ran out of memory with three at once (2026-09-28). A show or install
that finds another painting waits for it, and says so.

A skin lives in skins/<name>/: design.py (a `design(s)` function that paints a paintbox.Skin),
notes.md (the user's words and each change they asked for), thumb.png (the latest picture),
versions/<n>.png (a picture of every round shown).
show() also refreshes the gallery page's list (tool/gallery.py).
"""

import argparse
import contextlib
import importlib.util
import os
import sys
import time

from PIL import Image

from tool import gallery, install, paintbox, paths, snap, view


def load_design(name):
    folder = paths.SKINS / name
    script = folder / "design.py"
    if not script.exists():
        raise FileNotFoundError(f"no design at {script}")
    spec = importlib.util.spec_from_file_location(f"skins.{name}.design", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.design


def _try_lock(f):
    try:
        if os.name == "nt":
            import msvcrt
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except OSError:
        return False


@contextlib.contextmanager
def paint_slot():
    """Wait for a free paint slot (TSC_PAINTS, 1 by default) and hold it. The lock is the operating
    system's on an open file, so a paint that dies (killed for memory) frees it with it."""
    slots = max(1, int(os.environ.get("TSC_PAINTS") or 1))
    paths.WORK.mkdir(parents=True, exist_ok=True)
    said = False
    while True:
        for k in range(slots):
            f = open(paths.WORK / f"paint{k}.lock", "a+")
            if _try_lock(f):
                try:
                    yield
                finally:
                    f.close()  # closing the file releases the lock, on both systems
                return
            f.close()
        if not said:
            print("waiting for another paint to finish (paints take turns on this computer)", flush=True)
            said = True
        time.sleep(1)


def paint(name, frames=False, follow=True):
    """frames: also draw the car at the end of each step, for the Lab's Studio (show does).
    follow=False: the Lab doesn't turn to this skin (the Mac repainting its stale skins at start)."""
    t0 = time.time()
    s = paintbox.Skin(name)
    if frames:
        view.start_steps(name, follow)
        s.frames = True
    load_design(name)(s)
    s.end_steps()
    print(f"painted in {time.time() - t0:.0f} s")
    print(s.summary())
    return s


def show(name, open_browser=False, snapshot=True, follow=True):
    with paint_slot():
        s = paint(name, frames=True, follow=follow)
        t0 = time.time()
        paintbox.export_to_viewer(s)
        paintbox.save_painted(s)
        print(f"exported in {time.time() - t0:.0f} s")
    if snapshot:
        # the front three-quarter view becomes the skin's picture in the gallery, and a numbered
        # copy in versions/ keeps every round the user has seen (checkpoint 7)
        thumb = paths.SKINS / name / "thumb.png"
        snap.snap(name, prepare=False, thumb=thumb)
        keep_version(name, thumb)
    gallery.refresh()
    if open_browser:
        import urllib.parse
        import webbrowser
        url = f"http://localhost:{view.PORT}/?skin={urllib.parse.quote(name)}"
        try:
            view.start_server(view.PORT)
        except OSError:
            pass
        webbrowser.open(url)
        print(f"viewer: {url}")
        import threading
        threading.Event().wait()
    return s


def keep_version(name, thumb):
    """Copy the skin's picture to skins/<name>/versions/<n>.png, unless it matches the last one."""
    import shutil
    folder = paths.SKINS / name / "versions"
    folder.mkdir(exist_ok=True)
    kept = sorted(folder.glob("*.png"), key=lambda p: int(p.stem))
    if kept and kept[-1].read_bytes() == thumb.read_bytes():
        return
    n = int(kept[-1].stem) + 1 if kept else 1
    shutil.copyfile(thumb, folder / f"{n}.png")
    print(f"version {n} kept")


def do_install(name):
    t0 = time.time()
    folder = paths.SKINS / name
    # a skin shown on the other computer, or changed since it was shown here, is painted first
    painted = paths.BUILD / name / "painted.json"
    icon = None
    thumb = folder / "thumb.png"
    if thumb.exists():
        im = Image.open(thumb).convert("RGB")
        side = min(im.size)
        icon = im.crop(((im.width - side) // 2, (im.height - side) // 2, (im.width + side) // 2, (im.height + side) // 2)).resize((256, 256), Image.LANCZOS)
    with paint_slot():
        if not painted.exists() or painted.stat().st_mtime < (folder / "design.py").stat().st_mtime:
            paintbox.save_painted(paint(name))
        zip_path = paintbox.build_zip(name, icon)
    print(f"{zip_path.name}: {zip_path.stat().st_size / 1e6:.2f} MB, built in {time.time() - t0:.0f} s")
    target = install.install(zip_path)
    print(f"installed {target.name}")
    gallery.refresh()
    return target


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["show", "install", "list", "paint"])
    ap.add_argument("name", nargs="?", help="the skin")
    ap.add_argument("--open", action="store_true")
    ap.add_argument("--no-snap", action="store_true")
    args = ap.parse_args()
    if args.command == "list":
        for entry in gallery.refresh():
            mark = " (in the game)" if entry["installed"] else ""
            print(f"{entry['name']:<24} {entry['when']}{mark}  {entry['words']}")
        return
    if not args.name:
        sys.exit("which skin?")
    name = args.name
    if args.command == "show":
        show(name, args.open, snapshot=not args.no_snap)
    elif args.command == "paint":
        with paint_slot():
            paint(name)
    else:
        do_install(name)


if __name__ == "__main__":
    main()
