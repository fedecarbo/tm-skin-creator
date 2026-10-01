"""Notes on the car, and the Lab's timeline with Claude. In the Lab the user clicks the car where they
mean and writes what they want there (their pick of the mockups, 2026-09-27: CHECKLIST.md, "The
Lab", steps 7 and 9), or says something in the box under the timeline (the Lab's timeline, A, the
user's pick, 2026-09-28: CHECKLIST.md, "The Lab's timeline"). Each note keeps the skin (the one on
the car: the car, or one of its options), the part under the click, the point (for its pin), the
view and the user's words, in .notes/notes.json, and a picture of what the user was looking at with
the pin drawn on, beside it. The page saves them through the viewer's server (tool/view.py,
/api/notes). Claude answers in the Lab with lines of its own (`say`, or `done ... --say`): the
timeline shows the user's notes and words on one side, Claude's lines on the other.

.notes/ is git-ignored: the notes are a working queue on the computer where the user writes them,
and the repo is public (2026-09-27; until then the file was skins/notes.json). A skin's own record
of what the user asked for is its notes.md.

They reach Claude with the user's next message: a UserPromptSubmit hook (.claude/settings.json) runs
this file with --hook, which prints the new ones and marks them sent. Claude marks a note done once
it's handled: its pin leaves the car, and the note stays in the timeline, picture and all:

    python -m tool.notes                                    the notes not done yet, every skin
    python -m tool.notes done <skin> [N ...] [--say "..."]  mark notes done (all of the skin's, without
                                                            numbers), and say in the Lab what changed
    python -m tool.notes say <skin> "..."                   a line from Claude in the Lab's timeline
    python -m tool.notes wait [minutes]                     end as soon as a note comes, printing it
                                                            (default 120)

The Lab's sets of options (tool/sets.py) send the user's picks the same way: a note on the car with
`answer`, the set and the option picked, and no point. While Claude waits for an answer, it runs
`wait` in the background, which wakes it the moment one comes, with no message in the chat needed.

The server (on threads), the hook and the command line all write the file. Each write takes a lock,
a folder made with mkdir, which is atomic on Windows and macOS; then it replaces the file whole, retrying while Windows
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
    """A skin with a design, or a car with sets (a new car's concepts come before it has one)."""
    if not isinstance(skin, str) or not NAME.fullmatch(skin) or not any(
            (REPO / "skins" / skin / f).is_file() for f in ("design.py", "sets.json")):
        raise ValueError(f"no skin called {skin!r}")
    return skin


def of(skin):
    """The skin's notes not done yet, in the order they were written."""
    if not isinstance(skin, str) or not NAME.fullmatch(skin):
        return []
    return [n for n in load() if n["skin"] == skin and n["state"] != "done"]


def next_n(skin, notes=None):
    return max((x.get("n", 0) for x in (load() if notes is None else notes) if x["skin"] == skin), default=0) + 1


def timeline(skins):
    """Everything said in the Lab about these skins (a car and its options), in the order it was said:
    the user's notes, done or not, each with its picture's address (/notes/<file>) while the picture
    is on this computer, and Claude's lines (`by`: "claude")."""
    out = []
    for x in load():
        if x["skin"] in skins:
            x = dict(x)
            pic = picture_path(x)
            x["picture"] = f"notes/{pic.name}" if pic and pic.exists() else None
            out.append(x)
    return out


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


def _answer(v):
    """A pick in the Lab's sets of options ({"set", "name", "pick", "title"}: the set's number and title,
    the option picked and its title), checked; None when it isn't one."""
    if not isinstance(v, dict) or not isinstance(v.get("set"), int) or isinstance(v.get("set"), bool) or not 0 < v["set"] < 10000:
        return None
    pick = v.get("pick")
    if not isinstance(pick, str) or not re.fullmatch(r"[A-Z]", pick):
        return None
    return {"set": v["set"], "name": str(v.get("name") or "")[:80], "pick": pick, "title": str(v.get("title") or "")[:80]}


def _drop_picture(note):
    pic = picture_path(note)
    if pic:
        _retry(lambda: pic.unlink(missing_ok=True))
    note.pop("picture", None)


def add(skin, text, part=None, at=None, normal=None, picture=None, view=None, answer=None):
    """A new note from the Lab. part: {"id", "label", "token"}; at and normal: the clicked point and
    the surface's facing, in the viewer's metres; picture: the car as the user saw it, its dot drawn
    on (a JPEG data: URL); view: where the camera was (the Lab turns the car back to it); answer: the
    user's pick in a set of options (a pick needs no words). No point and no answer: words in the
    timeline's box. Returns the note."""
    text = str(text or "").strip()[:LONGEST]
    answer = _answer(answer)
    if not text and not answer:
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
            "part": {"id": part.get("id") if isinstance(part.get("id"), int) else None,
                     "label": str(part.get("label") or "")[:80], "token": str(part.get("token") or "")[:80]},
            "at": vec(at),
            "normal": vec(normal),
            "view": _view(view),
            "answer": answer,
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
            if x["skin"] == skin and x.get("n") == n:
                _drop_picture(x)
        save([x for x in notes if not (x["skin"] == skin and x.get("n") == n)])


def done(skin, numbers=(), said=""):
    """Mark notes done, their pictures kept for the timeline, and `said`, when there's one, as
    Claude's line about them. The skin may be gone: a pick deletes the options it doesn't keep
    (TSC_Ladybird's concepts, 2026-09-28), and their notes still need closing."""
    if not isinstance(skin, str) or not NAME.fullmatch(skin):
        raise ValueError(f"not a skin's name: {skin!r}")
    numbers = {int(k) for k in numbers}
    with _locked():
        notes = load()
        hit = [x for x in notes if x["skin"] == skin and x["state"] != "done" and (not numbers or x["n"] in numbers)]
        for x in hit:
            x["state"] = "done"
        if said.strip():
            notes.append(_line(skin, said, [x["n"] for x in hit]))
        save(notes)
    return hit


def _line(skin, text, about=()):
    text = str(text or "").strip()[:LONGEST]
    if not text:
        raise ValueError("nothing to say")
    return {"skin": skin, "by": "claude", "text": text, "about": sorted(about),
            "made": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "state": "done"}


def say(skin, text):
    """A line from Claude in the Lab's timeline (a car's, or one of its options')."""
    _skin(skin)
    with _locked():
        notes = load()
        notes.append(_line(skin, text))
        save(notes)


def line(x):
    a = x.get("answer")
    if a:  # a pick in a set of options, not a point on the car
        words = f": \"{x['text']}\"" if x["text"] else ""
        return f"- {x['skin']}, note {x['n']}, in the Lab's timeline, set {a['set']} ({a['name']}), picked {a['pick']} ({a['title']}){words}"
    if not x.get("at"):  # words in the timeline's box
        return f"- {x['skin']}, note {x['n']}, in the Lab's box: \"{x['text']}\""
    where = f"on {x['part']['token']} ({x['part']['label']})" if x["part"]["token"] else "on the car"
    pic = picture_path(x)
    seen = f" (what they saw, the pin drawn on: {pic})" if pic and pic.exists() else ""
    return f"- {x['skin']}, note {x['n']}, {where}: \"{x['text']}\"{seen}"


def deliver(since):
    """Print the notes Claude hasn't seen and mark them sent; True if there were any."""
    if not any(x["state"] == "new" for x in load()):  # most messages: no lock needed
        return False
    with _locked():
        notes = load()
        new = [x for x in notes if x["state"] == "new"]
        if not new:
            return False
        print(f"Notes the user left in the Lab {since} (their words: on the car, each pinned to the part they "
              "clicked, so look at its picture; in the box under the timeline; or a pick in a set of options. "
              "Once one is handled, `python -m tool.notes done <skin> <n> --say \"<what changed, a line>\"`):")
        for x in new:
            print(line(x))
            x["state"] = "sent"
        save(notes)
    return True


def hook():
    """For the UserPromptSubmit hook: the notes Claude hasn't seen, with the user's message."""
    try:
        deliver("since their last message")
    except TimeoutError:  # the page was saving one just then: they stay new for the next message
        print("(The Lab's notes were being saved just then; any new ones come with the next message.)")


def wait(minutes=120.0):
    """For Claude waiting on the user's answer in the Lab (a Bash command in the background, which
    wakes Claude when it ends): ends as soon as a note comes, printing it, so a pick in the Lab's
    timeline reaches Claude without a message in the chat; or after `minutes` with nothing."""
    end = time.monotonic() + minutes * 60
    while time.monotonic() < end:
        try:
            if deliver("while Claude waited"):
                return True
        except (TimeoutError, OSError, ValueError):  # busy, or caught mid-write: look again
            pass
        time.sleep(1)
    print(f"(No notes from the Lab in {minutes:g} minutes: stopped waiting.)")
    return False


def main(args):
    if args[:1] == ["--hook"]:
        try:
            hook()
        except Exception as e:  # never block the user's message over a note
            print(f"(The Lab's notes couldn't be read: {e})")
        return
    if args[:1] == ["wait"] and len(args) <= 2:
        wait(float(args[1]) if len(args) == 2 else 120.0)
        return
    if args[:1] == ["done"] and len(args) >= 2:
        rest, said = args[2:], ""
        if "--say" in rest:
            k = rest.index("--say")
            if k + 1 >= len(rest):
                sys.exit("--say what?")
            said, rest = rest[k + 1], rest[:k] + rest[k + 2:]
        hit = done(args[1], rest, said)
        print((f"{len(hit)} note(s) done" if hit else "no open notes matched") + (", and said in the Lab" if said else ""))
        return
    if args[:1] == ["say"] and len(args) == 3:
        say(args[1], args[2])
        print("said in the Lab")
        return
    if args:
        sys.exit(__doc__)
    for x in (n for n in load() if n["state"] != "done"):
        print(f"{line(x)} [{x['state']}]")


if __name__ == "__main__":
    main(sys.argv[1:])
