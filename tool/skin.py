"""Run a skin's design script: show it in the viewer, or build and install it.

    python -m tool.skin show <name>            paint it, put it in the viewer, snapshot it
    python -m tool.skin show <name> --open     ... and open the viewer in the browser
    python -m tool.skin install <name>         paint it, build the zip, install it (the PC)
    python -m tool.skin list                   every skin, newest first

show also measures how far each zoned paint reaches on the body (tool/measure.py, kept in
build/<name>/measured.json) and names what's wrong on the car before anyone looks (tool/checks.py:
a paint that stops short, a graphic cut, spilled or over another, paint by the game's panels, a soft
edge), printed after the paint's notes and kept in build/<name>/found.json, and says how each graphic sits
against the lines the eye sees and the other graphics (tool/eye.py, kept in build/<name>/eye.json for
tool.snap --eye).

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

from tool import build, checks, course, eye, gallery, install, measure, paintbox, paths, progress, snap, view


def borrow(name):
    """Another skin's design, to build on: its module, with its design(), helpers and colours.
    Run afresh at each call, so two designs that borrow it never share its state. A design names
    the skin it borrows in quotes, `borrow("TSC_CMYK_EndsInK")`, which is how tool/sets.py sees it."""
    script = paths.SKINS / name / "design.py"
    if not script.exists():
        raise FileNotFoundError(f"no design at {script}")
    spec = importlib.util.spec_from_file_location(f"skins.{name}.design", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_design(name):
    return borrow(name).design


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
            progress.stage("Waiting for another paint to finish")
            said = True
        time.sleep(1)


def paint(name, frames=False):
    """frames: also draw the car at the end of each step, for the Lab (show does)."""
    t0 = time.time()
    progress.stage("Painting")
    s = paintbox.Skin(name)
    if frames:
        view.start_steps(name)
        s.frames = s.measure = True
    load_design(name)(s)
    s.end_steps()
    print(f"painted in {time.time() - t0:.0f} s")
    print(s.summary(found=not frames))  # show's checks say the paint's own findings with the rest
    return s


def show(name, open_browser=False, snapshot=True):
    with progress.job(f"Painting {progress.title_of(name)}", skin=name,
                      done="Painted and photographed" if snapshot else "Painted"):
        with paint_slot():
            s = paint(name, frames=True)
            t0 = time.time()
            progress.stage("Measuring where the paint reaches")
            found = measure.measure(s)
            measure.save(name, found)
            lines = measure.words(found)
            print(f"measured in {time.time() - t0:.1f} s" + (":" if lines else ": nothing zoned on the body"))
            print("\n".join(f"  {line}" for line in lines))
            for call in s.zoned:  # a marking along a course, read back off the body (tool/course.py)
                if getattr(call["zone"], "course", None) is not None:
                    for line in course.measure(call["zone"])[1]:
                        print(f"  {call['what']}: {line}")
            t0 = time.time()
            progress.stage("Checking the car")
            found = checks.run(s, found)
            checks.save(name, found)
            lines = checks.words(found)
            print(f"checked in {time.time() - t0:.1f} s: " + (f"the checks name {len(found)}" if found else "the checks name nothing"))
            print("\n".join(f"  {line}" for line in lines))
            if found:  # the Lab's chat says it under the job
                progress.result(f"{'Painted and photographed' if snapshot else 'Painted'}; the checks name {len(found)} "
                                f"thing{'s' if len(found) > 1 else ''} to look at")
            t0 = time.time()
            progress.stage("Looking at how each graphic sits")
            looks = eye.look(s)
            eye.save(name, looks)
            lines = eye.words(looks)
            print(f"looked in {time.time() - t0:.1f} s at how each graphic sits against the lines the eye sees and the "
                  "other graphics" + (":" if lines else ": no graphic near one"))
            print("\n".join(f"  {line}" for line in lines))
            t0 = time.time()
            progress.stage("Putting it on the car")
            build.export_to_viewer(s)
            build.save_painted(s)
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
        from tool import server
        server.serve(f"?skin={urllib.parse.quote(name)}", "viewer")
    return s


def keep_version(name, thumb):
    """Copy the skin's picture to skins/<name>/versions/<n>.png, unless it matches the last one."""
    import shutil
    folder = paths.SKINS / name / "versions"
    folder.mkdir(exist_ok=True)
    kept = sorted((p for p in folder.glob("*.png") if p.stem.isdigit()), key=lambda p: int(p.stem))
    if kept and kept[-1].read_bytes() == thumb.read_bytes():
        return
    n = int(kept[-1].stem) + 1 if kept else 1
    shutil.copyfile(thumb, folder / f"{n}.png")
    print(f"version {n} kept")


def do_install(name):
    """Paint the skin, build its zip, put it in the game.
    Always painted afresh: a paint kept from an earlier show can't know whether a design it
    borrows, its pictures or the tool changed since (and a skin shown on the other computer has
    none here)."""
    install.game_folder()  # before painting: only the PC has the game
    t0 = time.time()
    with progress.job(f"Putting {progress.title_of(name)} in the game", skin=name, done="In the game"):
        with paint_slot():
            s = paint(name)
            build.save_painted(s)
            build.export_to_viewer(s)  # this computer's viewer shows the car as installed
            zip_path = build.build_zip(name)
        print(f"{zip_path.name}: {zip_path.stat().st_size / 1e6:.2f} MB, built in {time.time() - t0:.0f} s")
        progress.stage("Copying it into the game")
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
        with progress.job(f"Painting {progress.title_of(name)}", skin=name, done="Painted"), paint_slot():
            paint(name)
    else:
        do_install(name)


if __name__ == "__main__":
    main()
