"""Run a skin's design script: show it in the viewer, or build and install it.

    python -m tool.skin show <name>            paint it, put it in the viewer, snapshot it
    python -m tool.skin show <name> --open     ... and open the viewer in the browser
    python -m tool.skin install <name>         write the DDS files and the zip, install it
    python -m tool.skin list                   every skin, newest first

A skin lives in skins/<name>/: design.py (a `design(s)` function that paints a paintbox.Skin),
notes.md (the user's words and each change they asked for), thumb.png (the latest picture).
show() also refreshes the gallery page's list (tool/gallery.py).
"""

import argparse
import importlib.util
import sys
import time

from PIL import Image

from tool import gallery, install, paintbox, paths, snap


def load_design(name):
    folder = paths.SKINS / name
    script = folder / "design.py"
    if not script.exists():
        raise FileNotFoundError(f"no design at {script}")
    spec = importlib.util.spec_from_file_location(f"skins.{name}.design", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.design


def paint(name):
    t0 = time.time()
    s = paintbox.Skin(name)
    load_design(name)(s)
    print(f"painted in {time.time() - t0:.0f} s")
    print(s.summary())
    return s


def show(name, open_browser=False, snapshot=True):
    s = paint(name)
    t0 = time.time()
    paintbox.export_to_viewer(s)
    paintbox.save_painted(s)
    print(f"exported in {time.time() - t0:.0f} s")
    if snapshot:
        # the front three-quarter view becomes the skin's picture in the gallery
        snap.snap(name, prepare=False, thumb=paths.SKINS / name / "thumb.png")
    gallery.refresh()
    if open_browser:
        from tool import view
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


def do_install(name):
    t0 = time.time()
    folder = paths.SKINS / name
    icon = None
    thumb = folder / "thumb.png"
    if thumb.exists():
        im = Image.open(thumb).convert("RGB")
        side = min(im.size)
        icon = im.crop(((im.width - side) // 2, (im.height - side) // 2, (im.width + side) // 2, (im.height + side) // 2)).resize((256, 256), Image.LANCZOS)
    zip_path = paintbox.build_zip(name, icon)
    print(f"{zip_path.name}: {zip_path.stat().st_size / 1e6:.2f} MB, built in {time.time() - t0:.0f} s")
    target = install.install(zip_path)
    print(f"installed {target.name}")
    gallery.refresh()
    return target


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["show", "install", "list", "paint"])
    ap.add_argument("name", nargs="?")
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
    if args.command == "show":
        show(args.name, args.open, snapshot=not args.no_snap)
    elif args.command == "paint":
        paint(args.name)
    else:
        do_install(args.name)


if __name__ == "__main__":
    main()
