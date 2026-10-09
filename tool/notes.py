"""Notes on the car, and the Lab's timeline with Claude. In the Lab the user clicks the car where they
mean and writes what they want there (their pick of the mockups, 2026-09-27), draws on it with the
pen (a strip where they'd want one, a ring round something: their idea, 2026-10-05), or says
something in the box under the timeline (the Lab's timeline, A, the user's pick, 2026-09-28). Each
note keeps the skin (the one on the car: the car, or one of its options), the part under the click,
the point (for its pin), the lines drawn (`drawn`: in the paint box's cm, and the parts they cross),
the view and the user's words, in .notes/notes.json, and a picture of what the user was looking at
with the pin and the lines on it, beside it. The page saves them through the viewer's server (tool/view.py,
/api/notes). Claude answers in the Lab with lines of its own (`say`, or `done ... --say`): the
timeline shows the user's notes and words on one side, Claude's lines on the other.

.notes/ is git-ignored: the notes are a working queue on the computer where the user writes them,
and the repo is public (2026-09-27; until then the file was skins/notes.json). A skin's own record
of what the user asked for is its notes.md.

They reach Claude with the user's next message: a UserPromptSubmit hook (.claude/settings.json) runs
this file with --hook, which prints the new ones and marks them sent. Claude marks a note done once
it's handled and the judge passes the car (tool/gate.py): its pin leaves the car, and the note stays
in the timeline, picture and all:

    python -m tool.notes                                    the notes not done yet, every skin
    python -m tool.notes drawn <skin> <N>                   the lines a note drew, in cm, for a zone
    python -m tool.notes done <skin> [N ...] [--say "..."]  mark notes done (all of the skin's, without
                                                            numbers), and say in the Lab what changed
    python -m tool.notes say <skin> "..."                   a line from Claude in the Lab's timeline
    python -m tool.notes ask <skin> "<question>" --choice "<label>" [--colour "#rrggbb"]
                             [--picture <png or jpg>] --choice ... [--several]
    python -m tool.notes ask <skin> "<question>" --yes      a question as a widget in the timeline
    python -m tool.notes settle <skin> <K> "<what was decided>"
                                                            question K answered elsewhere (in the chat)
    python -m tool.notes wait [minutes]                     end as soon as a note comes, printing it
                                                            (default 120)

Whenever the user gets to pick something, it comes to the timeline as a widget (the user, 2026-10-02:
"keep the interactivity in the chat, whenever the user gets to pick something. Similar to A2UI"):
Claude describes it from a small fixed catalog, the Lab draws it, and the answer comes back as a note.
The catalog: a set of options (tool/sets.py: painted cars, Pick or "None of these"); a choice (two to
six labels, each with a colour swatch or a small picture if wanted; one, or several with --several);
yes or no. Each has a box for the user's own words. A question is one of Claude's lines with `ask`
({n, kind, choices [{key, label, colour, picture}], several, settled}); an answer is a note with
`answer` and no point: {set, name, pick (a letter, "none" or "" for words only), title} or {ask,
question, kind, pick [keys], labels, yes}, checked here against the question. While Claude waits for
an answer, it runs `wait` in the background, which wakes it the moment one comes, with no message in
the chat needed.

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
import subprocess
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
            except FileNotFoundError:  # freed already
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
    """A skin with a design, or a car with sets or a record (a new car is asked and shown things before
    it has a design)."""
    if not isinstance(skin, str) or not NAME.fullmatch(skin) or not any(
            (REPO / "skins" / skin / f).is_file() for f in ("design.py", "sets.json", "notes.md")):
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
            if x.get("ask"):  # a question's pictures, while they're on this computer
                x["ask"] = dict(x["ask"], choices=[dict(c, picture=f"notes/{c['picture']}" if c.get("picture") and
                                                        (HOME / c["picture"]).exists() else None)
                                                   for c in x["ask"]["choices"]])
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
    except (KeyError, TypeError, ValueError):  # a view that isn't one
        return None


STROKES = 24  # lines in a note
POINTS = 2000  # points in a line


def _drawn(v):
    """The lines the user drew on the car with the Lab's pen, checked: {"strokes": [[[x, y, z] cm]],
    "parts": [{"token", "label"}], "mesh": [...]}, the parts they cross in the order they cross them, and
    for each line picked on the model's mesh (Draw with Mesh on) {"set", "clicks": [[x, y, z] cm],
    "closed"}, None for one drawn by hand (no "mesh" when none was picked); None when there are none."""
    if not isinstance(v, dict) or not isinstance(v.get("strokes"), list):
        return None
    given = v.get("mesh") if isinstance(v.get("mesh"), list) else []
    strokes, mesh = [], []
    for k, line in enumerate(v["strokes"][:STROKES]):
        if not isinstance(line, list):
            raise ValueError("a drawn line is a list of points")
        pts = []
        for q in line[:POINTS]:
            if not isinstance(q, list) or len(q) != 3:
                raise ValueError("a drawn point is [x, y, z]")
            q = [round(float(c), 1) for c in q]
            if not all(math.isfinite(c) and abs(c) < 1000 for c in q):
                raise ValueError("a drawn point off the car")
            pts.append(q)
        if len(pts) >= 2:
            strokes.append(pts)
            m = given[k] if k < len(given) else None
            if isinstance(m, dict) and m.get("set") in ("Skin", "Details", "Wheels") and isinstance(m.get("clicks"), list):
                clicks = [[round(float(c), 2) for c in q] for q in m["clicks"][:200] if isinstance(q, list) and len(q) == 3]
                ok = all(math.isfinite(c) and abs(c) < 1000 for q in clicks for c in q)
                mesh.append({"set": m["set"], "clicks": clicks, "closed": bool(m.get("closed"))} if ok and clicks else None)
            else:
                mesh.append(None)
    if not strokes:
        return None
    parts = [{"token": str(p.get("token") or "")[:80], "label": str(p.get("label") or "")[:80]}
             for p in (v.get("parts") if isinstance(v.get("parts"), list) else []) if isinstance(p, dict)][:40]
    out = {"strokes": strokes, "parts": parts}
    if any(mesh):
        out["mesh"] = mesh
    return out


def _side(xs):
    return "the left" if min(xs) > 2 else "the right" if max(xs) < -2 else "both sides of the middle"


def drawn_words(d):
    """Each drawn line in a few words, in the paint box's cm (x the car's left, y up, z forward): a
    line from one end to the other, or a ring (its ends meet) and what it goes round."""
    out, mesh = [], d.get("mesh") or []
    for k, pts in enumerate(d["strokes"], 1):
        picked = mesh[k - 1] if k <= len(mesh) else None
        how = f"picked on the model's mesh ({picked['set']}, {len(picked['clicks'])} clicks), " if picked else ""
        length = sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))
        xs, ys, zs = zip(*pts)
        at = lambda q: f"(x {q[0]:+.0f}, y {q[1]:.0f}, z {q[2]:+.0f})"
        if length > 8 and math.dist(pts[0], pts[-1]) < max(4.0, 0.15 * length):
            out.append(f"line {k}: {how}a ring {length:.0f} cm round on {_side(xs)}, round x {min(xs):+.0f} to "
                       f"{max(xs):+.0f}, y {min(ys):.0f} to {max(ys):.0f}, z {min(zs):+.0f} to {max(zs):+.0f}")
        else:
            out.append(f"line {k}: {how}{length:.0f} cm long on {_side(xs)}, from {at(pts[0])} to {at(pts[-1])}")
    return out


def _number(v):
    return v if isinstance(v, int) and not isinstance(v, bool) and 0 < v < 10000 else None


def _asked(notes, skin, k):
    """Question k of Claude's to this skin."""
    return next((x for x in notes if x["skin"] == skin and x.get("ask") and x["ask"]["n"] == k), None)


def _answer(v, notes, skin):
    """The user's answer from the Lab's timeline, checked; None when it isn't one. In a set of options
    ({"set", "name", "pick", "title"}): the option picked (a letter), "none" of them, or "" when the
    words say it. To a question of Claude's ({"ask", "pick" or "yes"}): checked against the question,
    which lends the answer its words, so Claude reads it without looking the question up."""
    if not isinstance(v, dict):
        return None
    if _number(v.get("set")):
        pick = v.get("pick")
        if not isinstance(pick, str) or not re.fullmatch(r"[A-Z]|none|", pick):
            return None
        return {"set": v["set"], "name": str(v.get("name") or "")[:80], "pick": pick, "title": str(v.get("title") or "")[:80]}
    k = _number(v.get("ask"))
    if not k:
        return None
    q = _asked(notes, skin, k)
    if not q:
        raise ValueError(f"{skin} has no question {k}")
    a = q["ask"]
    out = {"ask": k, "question": q["text"][:200], "kind": a["kind"], "pick": [], "labels": [], "yes": None}
    if a["kind"] == "yes":
        if isinstance(v.get("yes"), bool):
            out["yes"] = v["yes"]
        return out
    keys = {c["key"]: c["label"] for c in a["choices"]}
    pick = v.get("pick") or []
    if not isinstance(pick, list) or any(p not in keys for p in pick) or len(set(pick)) != len(pick):
        raise ValueError("not one of the question's choices")
    if len(pick) > 1 and not a.get("several"):
        raise ValueError("the question takes one choice")
    out["pick"] = sorted(pick)
    out["labels"] = [keys[p] for p in out["pick"]]
    return out


def _answered(answer):
    """Whether an answer says something without words: a pick, none of them, or a yes or a no."""
    return bool(answer and (answer.get("pick") or answer.get("yes") is not None))


def _drop_picture(note):
    pic = picture_path(note)
    if pic:
        _retry(lambda: pic.unlink(missing_ok=True))
    note.pop("picture", None)


def add(skin, text, part=None, at=None, normal=None, picture=None, view=None, answer=None, drawn=None):
    """A new note from the Lab. part: {"id", "label", "token"}; at and normal: the clicked point and
    the surface's facing, in the viewer's metres; drawn: the lines drawn with the pen (_drawn);
    picture: the car as the user saw it, its dot and lines drawn on (a JPEG data: URL); view: where
    the camera was (the Lab turns the car back to it); answer: the
    user's answer to a set of options or a question of Claude's (a pick needs no words). No point and
    no answer: words in the timeline's box. Returns the note."""
    text = str(text or "").strip()[:LONGEST]
    _skin(skin)
    vec = lambda v: [round(float(x), 4) for x in v][:3] if isinstance(v, list) and len(v) == 3 else None
    part = part if isinstance(part, dict) else {}
    jpeg = _picture(picture)
    with _locked():
        notes = load()
        answer = _answer(answer, notes, skin)
        if not text and not _answered(answer):
            raise ValueError("an empty note")
        note = {
            "skin": skin,
            "n": next_n(skin, notes),
            "text": text,
            "part": {"id": part.get("id") if isinstance(part.get("id"), int) else None,
                     "label": str(part.get("label") or "")[:80], "token": str(part.get("token") or "")[:80]},
            "at": vec(at),
            "normal": vec(normal),
            "drawn": _drawn(drawn),
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
    Claude's line about them. The skin may be gone: a pick deletes the options it doesn't keep, and
    their notes still need closing."""
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


COLOUR = re.compile(r"#[0-9a-fA-F]{6}")
PICTURES = {".png": b"\x89PNG", ".jpg": b"\xff\xd8", ".jpeg": b"\xff\xd8"}


def ask(skin, question, choices=(), yes=False, several=False):
    """A question of Claude's as a widget in the Lab's timeline: yes or no, or two to six choices, each
    {"label", "colour" ("#rrggbb"), "picture" (a PNG or JPEG on this computer, copied beside the
    notes)}. Returns its number."""
    _skin(skin)
    question = str(question or "").strip()[:LONGEST]
    if not question:
        raise ValueError("ask what?")
    if yes == bool(choices):
        raise ValueError("either --yes or two to six --choice")
    if not yes and not 2 <= len(choices) <= 6:
        raise ValueError("two to six choices")
    made = []
    for key, c in zip("ABCDEF", choices):
        label = str(c.get("label") or "").strip()[:60]
        if not label:
            raise ValueError("a choice needs a label")
        colour = c.get("colour")
        if colour and not COLOUR.fullmatch(colour):
            raise ValueError(f"not a colour: {colour!r} (#rrggbb)")
        pic = Path(c["picture"]) if c.get("picture") else None
        if pic:
            data = pic.read_bytes()
            if pic.suffix.lower() not in PICTURES or not data.startswith(PICTURES[pic.suffix.lower()]) or len(data) > BIGGEST:
                raise ValueError(f"not a PNG or JPEG under {BIGGEST >> 20} MB: {pic}")
        made.append({"key": key, "label": label, "colour": colour.lower() if colour else None, "picture": pic})
    with _locked():
        notes = load()
        k = max((x["ask"]["n"] for x in notes if x["skin"] == skin and x.get("ask")), default=0) + 1
        for c in made:
            if c["picture"]:
                name = f"{skin}-ask{k}{c['key']}{c['picture'].suffix.lower().replace('.jpeg', '.jpg')}"
                (HOME / name).write_bytes(c["picture"].read_bytes())
                c["picture"] = name
        q = _line(skin, question)
        q["ask"] = {"n": k, "kind": "yes" if yes else "choice", "choices": made, "several": bool(several), "settled": ""}
        notes.append(q)
        save(notes)
    return k


def settle(skin, k, decided):
    """Question k answered elsewhere (in the chat): its widget closes, saying what was decided."""
    decided = str(decided or "").strip()[:200]
    if not decided:
        raise ValueError("say what was decided")
    with _locked():
        notes = load()
        q = _asked(notes, skin, int(k))
        if not q:
            raise ValueError(f"{skin} has no question {k}")
        q["ask"]["settled"] = decided
        save(notes)


def answer_words(a):
    """An answer as Claude reads it, without the user's own words."""
    if "set" in a:
        return (f"set {a['set']} ({a['name']}), " + (f"picked {a['pick']} ({a['title']})" if len(a["pick"]) == 1
                else "none of these" if a["pick"] == "none" else "in their own words"))
    said = ("yes" if a["yes"] else "no") if a["yes"] is not None else ", ".join(
        f"{k} ({t})" for k, t in zip(a["pick"], a["labels"])) or "in their own words"
    return f"question {a['ask']} (\"{a['question']}\"): {said}"


def line(x):
    a = x.get("answer")
    if a:  # an answer to a set of options or a question, not a point on the car
        words = f": \"{x['text']}\"" if x["text"] else ""
        return f"- {x['skin']}, note {x['n']}, in the Lab's timeline, {answer_words(a)}{words}"
    if not x.get("at"):  # words in the timeline's box
        return f"- {x['skin']}, note {x['n']}, in the Lab's box: \"{x['text']}\""
    pic = picture_path(x)
    d = x.get("drawn")
    if d:
        names = [p["token"] or p["label"] for p in d["parts"]]
        over = ", ".join(names[:12]) + (f" and {len(names) - 12} more" if len(names) > 12 else "") if names else "the car"
        seen = f" (what they saw, the lines on it: {pic})" if pic and pic.exists() else ""
        return (f"- {x['skin']}, note {x['n']}, drawn on the car over {over}: \"{x['text']}\"{seen}; "
                + "; ".join(drawn_words(d)) + f" (its points: `python -m tool.notes drawn {x['skin']} {x['n']}`)")
    where = f"on {x['part']['token']} ({x['part']['label']})" if x["part"]["token"] else "on the car"
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
              "clicked or drawn on it, so look at its picture; in the box under the timeline; or an answer to a set of options "
              "or a question. "
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


def show_drawn(skin, n):
    """A note's drawn lines, as a design takes them: each line's points in cm, ready for a zone."""
    x = next((x for x in load() if x["skin"] == skin and x.get("n") == int(n)), None)
    if not x or not x.get("drawn"):
        sys.exit(f"{skin} has no note {n} drawn on the car")
    print(f"{skin}, note {x['n']}: \"{x['text']}\"")
    mesh = x["drawn"].get("mesh") or []
    for k, (words, pts) in enumerate(zip(drawn_words(x["drawn"]), x["drawn"]["strokes"])):
        print(f"# {words}")
        m = mesh[k] if k < len(mesh) else None
        if m:  # exact: the same line again from the clicks, on the model
            clicks = ", ".join(f"({a:g}, {b:g}, {c:g})" for a, b, c in m["clicks"])
            print(f"meshlines.picked([{clicks}], tset={m['set']!r}" + (", closed=True)" if m["closed"] else ")"))
        else:
            print("[" + ", ".join(f"({a:g}, {b:g}, {c:g})" for a, b, c in pts) + "]")
    print("# shapes.polyline([line, ...], width=<cm>): a strip along the points; meshlines.picked(...) is a Course on "
          "the model (.strip(cm)); (-x, y, z): the same on the other side.")


def events(record):
    """A skin's record (notes.md) as its events: each bullet and the lines indented under it, one line each."""
    out, inside = [], False
    for raw in record.splitlines():
        if raw.startswith("- "):
            out.append(raw[2:].strip())
            inside = True
        elif inside and raw.startswith("  "):
            out[-1] += " " + raw.strip()
        elif raw.strip():
            inside = False
    return out


def short(text, most=220):
    text = " ".join(text.split())
    return text if len(text) <= most else text[:most].rsplit(" ", 1)[0] + " …"


def _changed(skins, name):
    """The day of the last commit that touched the skin's folder ("" without git)."""
    try:
        r = subprocess.run(["git", "-C", str(skins), "log", "-1", "--format=%cs", "--", name],
                           capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):  # no git here
        return ""


def standing():
    """Where every skin stands, for a session's start on either computer (tool/doctor.py prints it), newest first: the last event
    in its record, whether it's in the game, and what's open. Open is a record's events that start with
    `Open` (written when something is left to do, turned to `Closed` once it's done), a set waiting for
    the user or being painted, and on this computer the Lab's notes not done and questions unanswered.
    A note not read yet is marked read, as it's printed here in full."""
    skins = Path(os.environ.get("TSC_SKINS_HOME") or REPO / "skins")
    sets = [json.loads(p.read_text("utf-8")) for p in sorted(skins.glob("*/sets.json"))]
    waiting = {d["car"]: [s for s in d["sets"] if s["state"] in ("painting", "open")] for d in sets}
    options = {o["skin"] for ss in waiting.values() for s in ss for o in s["options"]}
    installed = json.loads((skins / "installed.json").read_text("utf-8")) if (skins / "installed.json").exists() else {}
    notes = load()
    answered = {(x["skin"], x["answer"]["ask"]) for x in notes if (x.get("answer") or {}).get("ask")}
    lab = {}
    for x in notes:
        if x["state"] != "done":
            lab.setdefault(x["skin"], []).append(line(x)[2:])
        elif x.get("ask") and not x["ask"]["settled"] and (x["skin"], x["ask"]["n"]) not in answered:
            lab.setdefault(x["skin"], []).append(f"question {x['ask']['n']} in the Lab, unanswered: \"{short(x['text'], 160)}\"")
    rows = []
    for record in skins.glob("*/notes.md"):
        name = record.parent.name
        if name in options:
            continue
        said = events(record.read_text("utf-8"))
        day = _changed(skins, name)
        zip_ = installed.get(f"{name}.zip")
        head = (f"{name}, {day or 'new'}, " + (f"in the game since {zip_['installed'][:10]}" if zip_ else "not in the game")
                + (f". Last: {short(said[-1])}" if said else ". No events yet"))
        todo = ([short(e, 400) for e in said if re.match(r"Open\b", e)]
                + [f"set {s['n']}, {s['title']}: " + ("for the user to pick" if s["state"] == "open" else "being painted")
                   + " (" + ", ".join(f"{o['key']} {o['skin']}" for o in s["options"]) + ")" for s in waiting.get(name, [])]
                + lab.pop(name, []))
        rows.append((day or "~", head, todo))  # a skin never committed sorts first
    rows.sort(key=lambda r: r[0], reverse=True)
    rows += [("", f"{name}, no record", todo) for name, todo in sorted(lab.items())]
    print("Where each skin stands, newest first (its record's last event; what's open):")
    for _, head, todo in rows:
        print(f"- {head}")
        for t in todo:
            print(f"  - {t}")
    if not any(todo for *_, todo in rows):
        print("Nothing open.")
    new = {(x["skin"], x["n"]) for x in notes if x["state"] == "new"}
    if new:
        with contextlib.suppress(TimeoutError), _locked():
            fresh = load()
            for x in fresh:
                if (x["skin"], x.get("n")) in new and x["state"] == "new":
                    x["state"] = "sent"
            save(fresh)


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
        if str(REPO) not in sys.path:  # runnable as a file
            sys.path.insert(0, str(REPO))
        from tool import gate  # standard library only, as this file
        refused = gate.refusal([args[1]], "marking a note done")
        if refused:
            sys.exit(refused)
        hit = done(args[1], rest, said)
        print((f"{len(hit)} note(s) done" if hit else "no open notes matched") + (", and said in the Lab" if said else ""))
        return
    if args[:1] == ["drawn"] and len(args) == 3:
        show_drawn(args[1], args[2])
        return
    if args[:1] == ["say"] and len(args) == 3:
        say(args[1], args[2])
        print("said in the Lab")
        return
    if args[:1] == ["ask"] and len(args) >= 4:
        choices, yes, several, rest = [], False, False, args[3:]
        while rest:
            flag, rest = rest[0], rest[1:]
            if flag in ("--yes", "--several"):
                yes, several = yes or flag == "--yes", several or flag == "--several"
                continue
            if flag not in ("--choice", "--colour", "--picture") or not rest:
                sys.exit(f"{flag}? " + __doc__)
            value, rest = rest[0], rest[1:]
            if flag == "--choice":
                choices.append({"label": value})
            elif not choices:
                sys.exit(f"{flag} goes after the --choice it belongs to")
            else:
                choices[-1][flag[2:]] = value
        k = ask(args[1], args[2], choices, yes, several)
        print(f"asked in the Lab: question {k} (`settle {args[1]} {k} \"...\"` if it's answered in the chat)")
        return
    if args[:1] == ["settle"] and len(args) == 4:
        settle(args[1], args[2], args[3])
        print("settled in the Lab")
        return
    if args:
        sys.exit(__doc__)
    for x in (n for n in load() if n["state"] != "done"):
        print(f"{line(x)} [{x['state']}]")


if __name__ == "__main__":
    main(sys.argv[1:])
