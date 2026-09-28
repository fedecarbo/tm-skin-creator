"""Notes on the car: in the Lab the user clicks the car where they mean and writes what they want
there (their pick of the mockups, 2026-09-27: CHECKLIST.md, "The Lab", steps 7 and 9). Each note keeps
the skin, the step it was written at, the part under the click, the point (for its pin), and the
user's words, in .notes/notes.json, and a picture of what the user was looking at with the pin drawn
on, beside it. The page saves them through the viewer's server (tool/view.py, /api/notes).

.notes/ is git-ignored: the notes are a working queue on the computer where the user writes them,
and the repo is public (2026-09-27; until then the file was skins/notes.json). A skin's own record
of what the user asked for is its notes.md.

They reach Claude with the user's next message: a UserPromptSubmit hook (.claude/settings.json) runs
this file with --hook, which prints the new ones and marks them sent. Claude marks a note done once
it's handled, and its pin leaves the car:

    python -m tool.notes                        the notes not done yet, every skin
    python -m tool.notes done <skin> [N ...]    mark notes done (all of the skin's, without numbers)

The server (on threads), the hook and the command line all write the file. Each write takes a lock,
a folder made with mkdir, which is atomic on Windows and macOS and holds across the Mac's container
and host, where file locks don't reach; then it replaces the file whole, retrying while Windows
refuses (another program has it open: the page's poll, OneDrive). TSC_NOTES_HOME puts the folder
elsewhere, for tests.

Standard library only, and runnable as a file: the hook runs it with whatever Python the computer
has (the Mac's own python3 has no numpy)."""

import base64
import contextlib
import json
import math
import os
import re
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HOME = Path(os.environ.get("TSC_NOTES_HOME") or REPO / ".notes")
FILE = HOME / "notes.json"
LOCK = HOME / "lock"
NAME = re.compile(r"[A-Za-z0-9_\-]+")  # a skin's name, as the paint box allows it
LONGEST = 2000  # characters in a note
BIGGEST = 6 << 20  # bytes in a note's picture
TRIES = 20  # Windows refusing a replace or a read: that many tries, 50 ms apart


def _retry(fn):
    for k in range(TRIES):
        try:
            return fn()
        except PermissionError:
            if k == TRIES - 1:
                raise
            time.sleep(0.05)


@contextlib.contextmanager
def _locked(wait=3.0, stale=10.0):
    """One writer at a time. A lock older than `stale` seconds was left by a writer that died."""
    HOME.mkdir(parents=True, exist_ok=True)
    end = time.monotonic() + wait
    while True:
        try:
            os.mkdir(LOCK)
            break
        except (FileExistsError, PermissionError):
            with contextlib.suppress(OSError):
                if time.time() - LOCK.stat().st_mtime > stale:
                    os.rmdir(LOCK)
                    continue
            if time.monotonic() > end:
                raise TimeoutError("the notes are being saved by something else")
            time.sleep(0.02)
    try:
        yield
    finally:
        for _ in range(TRIES):
            try:
                os.rmdir(LOCK)
                break
            except FileNotFoundError:
                break
            except OSError:
                time.sleep(0.05)


def load():
    return json.loads(_retry(lambda: FILE.read_text("utf-8"))) if FILE.exists() else []


def save(notes):
    """Under the lock only: the whole file or nothing, as the page and the hook both read it."""
    fd, tmp = tempfile.mkstemp(dir=HOME, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(notes, f, indent=1, ensure_ascii=False)
        f.write("\n")
    try:
        _retry(lambda: os.replace(tmp, FILE))
    except OSError:
        Path(tmp).unlink(missing_ok=True)
        raise


def _skin(skin):
    if not isinstance(skin, str) or not NAME.fullmatch(skin) or not (REPO / "skins" / skin / "design.py").is_file():
        raise ValueError(f"no skin called {skin!r}")
    return skin


def of(skin):
    """The skin's notes not done yet, in the order they were written."""
    if not isinstance(skin, str) or not NAME.fullmatch(skin):
        return []
    return [n for n in load() if n["skin"] == skin and n["state"] != "done"]


def next_n(skin, notes=None):
    return max((x["n"] for x in (load() if notes is None else notes) if x["skin"] == skin), default=0) + 1


def picture_path(note):
    """The note's picture on this computer (older notes kept it as ".notes/<name>"), or None."""
    return HOME / Path(note["picture"]).name if note.get("picture") else None


def _picture(data_url):
    """A JPEG from the page (a data: URL), checked, as bytes; None when there's none."""
    head = "data:image/jpeg;base64,"
    if not isinstance(data_url, str) or not data_url.startswith(head):
        return None
    data = base64.b64decode(data_url[len(head):], validate=True)
    if len(data) > BIGGEST or not data.startswith(b"\xff\xd8"):
        raise ValueError("not a picture the Lab took")
    return data


def _view(v):
    """The camera the user saw the car from (the viewer's camera(): dir, dist, target, fov, mood and
    the framing), checked; None when it isn't one, and the note is kept without it."""
    if not isinstance(v, dict):
        return None
    try:
        def num(x):
            x = float(x)
            if not math.isfinite(x):
                raise ValueError("not a number")
            return x
        vec = lambda k: [round(num(x), 4) for x in v[k]] if isinstance(v[k], list) and len(v[k]) == 3 else None
        out = {"dir": vec("dir"), "dist": round(num(v["dist"]), 4), "target": vec("target"), "fov": round(num(v["fov"]), 3)}
        if None in (out["dir"], out["target"]) or not 0.05 < out["dist"] < 100 or not 1 < out["fov"] < 170:
            return None
        out["mood"] = v.get("mood") if v.get("mood") in ("day", "night", "sunrise", "sunset") else "day"
        f = v.get("framing")
        if isinstance(f, dict):
            out["framing"] = {k: round(num(f[k]), 4) for k in ("x", "y", "zoom")}
        return out
    except (KeyError, TypeError, ValueError):
        return None


def _station(v):
    """The stand's station the user was looking at ({"key", "name", "try", "latest"}: its try, and
    whether that was the newest), checked; None when it isn't one."""
    if not isinstance(v, dict) or not isinstance(v.get("key"), str) or not re.fullmatch(r"[a-z]{1,20}", v["key"]):
        return None
    n = v.get("try")
    if not isinstance(n, int) or isinstance(n, bool) or not 0 < n < 1000:
        n = None
    return {"key": v["key"], "name": str(v.get("name") or v["key"])[:40], "try": n, "latest": v.get("latest") is not False}


def _drop_picture(note):
    pic = picture_path(note)
    if pic:
        _retry(lambda: pic.unlink(missing_ok=True))
    note.pop("picture", None)


def add(skin, text, step=None, step_name="", part=None, at=None, normal=None, picture=None, view=None, station=None):
    """A new note from the Lab. part: {"id", "label", "token"}; at and normal: the clicked point and
    the surface's facing, in the viewer's metres; picture: the car as the user saw it, its dot drawn
    on (a JPEG data: URL); view: where the camera was (the Lab turns the car back to it); station:
    the stand's station and try the user was looking at (step and step_name: the Studio's step,
    before the stations). Returns the note."""
    text = str(text or "").strip()[:LONGEST]
    if not text:
        raise ValueError("an empty note")
    _skin(skin)
    vec = lambda v: [round(float(x), 4) for x in v][:3] if isinstance(v, list) and len(v) == 3 else None
    part = part if isinstance(part, dict) else {}
    jpeg = _picture(picture)
    with _locked():
        notes = load()
        note = {
            "skin": skin,
            "n": next_n(skin, notes),
            "text": text,
            "step": step if isinstance(step, int) and not isinstance(step, bool) else None,
            "step_name": str(step_name or "")[:80],
            "part": {"id": part.get("id") if isinstance(part.get("id"), int) else None,
                     "label": str(part.get("label") or "")[:80], "token": str(part.get("token") or "")[:80]},
            "at": vec(at),
            "normal": vec(normal),
            "view": _view(view),
            "station": _station(station),
            "made": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "state": "new",  # new -> sent (Claude has read it) -> done (handled)
        }
        if jpeg:
            name = f"{skin}-{note['n']}.jpg"
            (HOME / name).write_bytes(jpeg)
            note["picture"] = name
        notes.append(note)
        save(notes)
    return note


def remove(skin, n):
    """The user takes a note back (its × in the Lab)."""
    _skin(skin)
    n = int(n)
    with _locked():
        notes = load()
        for x in notes:
            if x["skin"] == skin and x["n"] == n:
                _drop_picture(x)
        save([x for x in notes if not (x["skin"] == skin and x["n"] == n)])


def done(skin, numbers=()):
    """Mark notes done. The skin may be gone: a studio pick deletes the options it doesn't keep,
    notes and all (TSC_Ladybird's concepts, 2026-09-28), and their notes still need closing."""
    if not isinstance(skin, str) or not NAME.fullmatch(skin):
        raise ValueError(f"not a skin's name: {skin!r}")
    numbers = {int(k) for k in numbers}
    with _locked():
        notes = load()
        hit = [x for x in notes if x["skin"] == skin and x["state"] != "done" and (not numbers or x["n"] in numbers)]
        for x in hit:
            x["state"] = "done"
            _drop_picture(x)
        save(notes)
    return hit


def line(x):
    where = f"on {x['part']['token']} ({x['part']['label']})" if x["part"]["token"] else "on the car"
    step = f"at step {x['step']} ({x['step_name']})" if x["step"] is not None else ""
    st = x.get("station")
    if st:
        step = f"looking at the {st['name']} station" + (f", try {st['try']}" if st["try"] else "") + ("" if st["latest"] else " (an earlier try than the newest)")
    pic = picture_path(x)
    seen = f" (what they saw, the pin drawn on: {pic})" if pic and pic.exists() else ""
    return f"- {x['skin']}, note {x['n']}, {step + ', ' if step else ''}{where}: \"{x['text']}\"{seen}"


def hook():
    """For the UserPromptSubmit hook: print the notes Claude hasn't seen, and mark them sent."""
    if not any(x["state"] == "new" for x in load()):  # most messages: no lock needed
        return
    try:
        with _locked():
            notes = load()
            new = [x for x in notes if x["state"] == "new"]
            if not new:
                return
            print("Notes the user left on the car in the Lab since their last message (their words, "
                  "each pinned to the part they clicked; look at each one's picture; "
                  "`python -m tool.notes done <skin> <n>` once one is handled):")
            for x in new:
                print(line(x))
                x["state"] = "sent"
            save(notes)
    except TimeoutError:  # the page was saving one just then: they stay new for the next message
        print("(The Lab's notes were being saved just then; any new ones come with the next message.)")


def main(args):
    if args[:1] == ["--hook"]:
        try:
            hook()
        except Exception as e:  # never block the user's message over a note
            print(f"(The Lab's notes couldn't be read: {e})")
        return
    if args[:1] == ["done"] and len(args) >= 2:
        hit = done(args[1], args[2:])
        print(f"{len(hit)} note(s) done" if hit else "no open notes matched")
        return
    if args:
        sys.exit(__doc__)
    for x in (n for n in load() if n["state"] != "done"):
        print(f"{line(x)} [{x['state']}]")


if __name__ == "__main__":
    main(sys.argv[1:])
