"""Fresh eyes on a finished car (PLAN.md, step 3): a Claude that didn't design it is given only the
user's words, what each step was meant to paint, the measures and the car's pictures, and names in a
few lines what's cut, sunk, forgotten or off the user's words, and in which picture. The eyes are an
agent, .claude/agents/fresh-eyes.md (Read only); this prepares what they read and records what came
of it. They never see the design, the notes or the designer's reasons: a designer is an unreliable
judge of its own work.

    python -m tool.eyes <name>          the close looks and the game's cameras taken afresh (the six
                                        views too when older than the paint), each picture cut out
                                        whole into build/<name>_eyes/, the brief beside them
                                        (brief.md); prints the brief's path, for the agent
    python -m tool.eyes <name> --again  after a fix and a show: the pictures taken afresh, and each one
                                        that changed since the eyes saw it, before beside after, in
                                        build/<name>_eyes/again/, listed in again.md for the same agent
    python -m tool.eyes <name> --done [--fixed "<what>" ...] [--left "<what: why>" ...]
                                        what came of it, a line in the Lab's timeline: "Fresh eyes
                                        checked it: two things fixed (...)", or "nothing to fix"

Only where the close looks run (a car shown alone, a pick), never on a set's takes. The pictures
take about fifteen seconds; the eyes' looking, in Claude's own session, shows in the Lab's chat as
the same job, handed over (progress.hand_over) until --done or the car's next job.
"""

import argparse
import json
import re
import shutil

from PIL import Image

from tool import measure, notes, paths, progress, snap, view

# the game's cameras the eyes read: the player's view all race, by day and at night (the alts are
# the same cameras pressed twice; Cam 1 and Cam 2 alike from afar)
CAMS = ("Cam 1 day", "Cam 2 alt day", "Cam 1 night", "Cam 2 alt night")
QUOTE = re.compile(r'["“]([^"”]+)["”]')
COUNT = ("no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine")


def folder(name):
    return paths.BUILD / f"{name}_eyes"


def words(name):
    """The user's own words about the car, from its record (skins/<name>/notes.md): every quote in
    an entry the user said ("The user's words ...", "Change 3 (user ...)"), in order. The record's
    other words are the designer's."""
    path = paths.SKINS / name / "notes.md"
    entries, cur = [], []
    for line in path.read_text(encoding="utf-8").splitlines() if path.exists() else ():
        if not line.strip() or line.startswith(("- ", "#")):
            entries.append(" ".join(cur))
            cur = []
        if line.strip() and not line.startswith("#"):
            cur.append(line.strip().removeprefix("- "))
    entries.append(" ".join(cur))
    out = []
    for e in entries:
        first = QUOTE.search(e)
        if first and "user" in e[:first.start()].lower():
            out += [q.strip() for q in QUOTE.findall(e) if q.strip() not in out]
    return out


def _steps(name):
    path = view.DATA / "skins" / name / "steps.json"
    if not path.exists():
        raise SystemExit(f"{name} hasn't been shown on this computer: tool.skin show {name} first")
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc.get("painting"):
        raise SystemExit(f"{name} is still being painted: wait for its show to end")
    return path, doc


def take(name):
    """The sheets the eyes read, taken afresh: the close looks and the game's cameras, and the six
    views when they're older than the last paint."""
    steps, _ = _steps(name)
    views = paths.BUILD / f"{name}_views.png"
    if not views.exists() or views.stat().st_mtime < steps.stat().st_mtime:
        snap.snap(name, prepare=False)
    snap.snap(name, out=paths.BUILD / f"{name}_close.png", shots=snap.CLOSE, prepare=False)
    snap.snap(name, out=paths.BUILD / f"{name}_cams.png", size=(1280, 720), shots=snap.CAMS, prepare=False,
              query="lens=game")  # the game's wide lens, as tool.snap --cams


def tiles(name):
    """The pictures the eyes read, {file name: picture}, cut whole from the sheets (a sheet read
    whole is scaled down by a third)."""
    out = {}
    for kind in ("views", "close", "cams"):
        sheet = Image.open(paths.BUILD / f"{name}_{kind}.png").convert("RGB")
        shots = snap.KINDS[kind]
        w, h = sheet.width // 3, sheet.height // ((len(shots) + 2) // 3)
        for k, shot in enumerate(shots):
            if kind != "cams" or shot[0] in CAMS:
                out[f"{kind} {shot[0]}.png"] = sheet.crop(((k % 3) * w, (k // 3) * h, (k % 3 + 1) * w, (k // 3 + 1) * h))
    return out


def _measures(name):
    """The measures, each paint named by its step, what and where, without its zone's formula (in a
    paint's name or where the design ends it): that's the design, which the eyes never see."""
    path = paths.BUILD / name / "measured.json"
    lines = measure.words(json.loads(path.read_text(encoding="utf-8")), written=True) if path.exists() else []
    return [re.sub(r"; ends where .*", "", x) if x.startswith(" ") else re.sub(r", zone .*", "", x)
            for x in lines] or ["Nothing zoned on the body."]


def brief(name):
    """What the eyes are given, as build/<name>_eyes/brief.md, beside the pictures."""
    _, doc = _steps(name)
    out = folder(name)
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    pictures = tiles(name)
    for file, im in pictures.items():
        im.save(out / file)
    said = words(name)
    steps = [st for st in doc["steps"] if st["does"]]
    clay = list(dict.fromkeys(c["name"] for c in doc.get("clay") or []))
    text = [f"# {progress.title_of(name)}", "",
            "## The user's words", "", *([f'- "{w}"' for w in said] or ["- (none recorded)"]), "",
            "## What each step was meant to paint", "",
            "The designer's words, to check against the pictures, not to trust.", "",
            *[f"{k}. {st['name']}: {st['does']}" for k, st in enumerate(steps, 1)], "",
            "Parts no step paints, left in the clay: " + (", ".join(clay) if clay else "none") + ".", "",
            "## Measured on the car", "",
            "Where each paint zoned on the body runs, in cm along the car (z: +212 the nose's tip, -158 the "
            "tail's end), and where it stops short of the body or leaves a gap.", "",
            "```", *_measures(name), "```", "",
            "## The pictures", "", *[f"- {out / f}" for f in pictures]]
    path = out / "brief.md"
    path.write_text("\n".join(text) + "\n", encoding="utf-8")
    return path


def again(name):
    """Each picture that changed since the eyes saw it, before beside after, the change outlined,
    listed in build/<name>_eyes/again.md with the measures as they are now. The pictures replace the
    ones the eyes saw, so a further look compares with this one."""
    out = folder(name)
    if not (out / "brief.md").exists():
        raise SystemExit(f"the eyes haven't looked at {name}: tool.eyes {name} first")
    later = out / "again"
    shutil.rmtree(later, ignore_errors=True)
    later.mkdir()
    pairs = []
    for file, after in tiles(name).items():
        seen = out / file
        before = Image.open(seen).convert("RGB") if seen.exists() else None
        marked = after.copy()  # the outline goes on a copy: the picture kept as seen stays clean
        if before is not None and before.size == after.size and not snap.changed(before, marked):
            continue
        after.save(seen)
        if before is None or before.size != after.size:
            continue
        pair = Image.new("RGB", (2 * after.width + 16, after.height), (24, 24, 26))
        pair.paste(before, (0, 0))
        pair.paste(marked, (after.width + 16, 0))
        pair.save(later / file)
        pairs.append(later / file)
    text = [f"# {progress.title_of(name)}, looked at again", "",
            "The car was changed. Each picture below changed: before on the left, after on the right, the "
            "change outlined in both." if pairs else "No picture changed.", "",
            "## Measured on the car now", "", "```", *_measures(name), "```", "",
            *[f"- {p}" for p in pairs]]
    path = out / "again.md"
    path.write_text("\n".join(text) + "\n", encoding="utf-8")
    return path, len(pairs)


def line(fixed=(), left=()):
    """The line for the Lab's timeline."""
    if not fixed and not left:
        return "Fresh eyes: nothing to fix."
    def many(items, what):
        n = len(items)
        return f"{COUNT[n] if n < len(COUNT) else n} {what} ({'; '.join(items)})"
    parts = ([many(fixed, "thing fixed" if len(fixed) == 1 else "things fixed")] if fixed else []) + \
            ([many(left, "left as it is")] if left else [])
    return "Fresh eyes checked it: " + ", ".join(parts) + "."


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--again", action="store_true", help="after a fix: the pictures that changed, before beside after")
    ap.add_argument("--done", action="store_true", help="what came of it, a line in the Lab's timeline")
    ap.add_argument("--fixed", action="append", default=[], help="with --done: a thing the eyes named, fixed")
    ap.add_argument("--left", action="append", default=[], help="with --done: a thing the eyes named, left, and why")
    args = ap.parse_args()
    name = args.name
    if args.done:
        text = line(args.fixed, args.left)
        notes.say(name, text)
        progress.finish(name)
        print(text)
        return
    with progress.job(f"Fresh eyes on {progress.title_of(name)}" + (", again" if args.again else ""), skin=name,
                      done="Looked over"):
        take(name)
        progress.stage("Writing what the eyes are given")
        if args.again:
            path, n = again(name)
            print(f"{n} picture{'s' if n != 1 else ''} changed: {path}")
            progress.hand_over(f"Looking again at what changed ({n} picture{'s' if n != 1 else ''})")
        else:
            path = brief(name)
            print(f"brief: {path}")
            n = len(list(folder(name).glob("*.png")))
            progress.hand_over(f"Looking at the car, close up and from the game's cameras ({n} pictures)")


if __name__ == "__main__":
    main()
