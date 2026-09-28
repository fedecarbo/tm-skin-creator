"""The build sheet of a car made in the design studio (CHECKLIST.md, "The design studio", W1): its
steps from the brief to the release, where each one stands, what was decided, and the options
waiting for the user. skins/<car>/sheet.json, written only by these commands, so the Lab's wizard
(W3) shows it and keeps no list of its own.

    python -m tool.sheet                                     every car with a sheet, and its step
    python -m tool.sheet <car>                               the car's sheet
    python -m tool.sheet new <car> --words "..."             start one, for a new car
    python -m tool.sheet on <car> <step>                     Claude is on the step
    python -m tool.sheet option <car> <step> "<title>" [--skin <name> | --file <path>]
                                                             an option for the step: A, B, C...
    python -m tool.sheet ask <car> <step>                    its options are shown: the user's turn
    python -m tool.sheet pick <car> <step> <letter|none> "<decision>"
    python -m tool.sheet decide <car> <step> ["<decision>"]  decided without options
    python -m tool.sheet skip <car> <step> "<why>"           nothing to decide there on this car
    python -m tool.sheet back <car> <step> "<why>" [--affects <step> ...]

The steps: brief, mood, concepts, shapes, colours, wheels, details, lettering, review, road,
release. Each is to do, Claude on it, waiting for you, decided, needs a look, or skipped.

Only a car begun in the studio has a sheet (the user, 2026-09-28: "I don't want you to get
influenced by previous builds, so if a build is done the old way, I would just have a standard
view how we have it for notes", then "lets focus on first time building, we can later figure
the already built"). A car made the old way keeps the Lab's stand and its notes, and `new` refuses
a car that has a design: taking a built car further is for later.

Options. An option is a skin, a whole design beside the car (skins/<car>_<Title>/), or a file in
the car's folder (a mood board). `option` without --skin or --file makes the skin: a copy of the
car's design.py and art/ to change, or an empty folder while the car has no design yet. A pick is
final (the user, 2026-09-28): the picked skin's design.py, art/ and thumb.png become the car's,
and every other option goes, its folder or file deleted (git's history keeps it), and out of its
round in skins/rounds.json. `pick none` keeps no option: the car's design as it is (a mix Claude
wrote into it). An option's design must stand on its own: one that loads the car's design or
another option's would break once they're gone, so the pick refuses it. An option that's in the
game (skins/installed.json) is kept, and the pick says so.

Going back. `back` reopens a decided step; what it decided moves to its history (`was`), and for a
step that paints the car, the car as it is becomes option A, so the change is tried beside it.
The later steps it affects (Claude decides which, and says why) need a look, the others stay
decided, and review, road test and release need a look after any change. A step never reopens
the steps before it.

Standard library only, and runnable with the Mac's own python3 (3.9), like tool/notes.py.
TSC_SKINS_HOME puts the skins elsewhere, for tests."""

import argparse
import datetime
import json
import os
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKINS = Path(os.environ.get("TSC_SKINS_HOME") or REPO / "skins")
NAME = re.compile(r"[A-Za-z0-9_\-]+")

STEPS = [
    ("brief", "Brief"),
    ("mood", "Mood"),
    ("concepts", "Concepts"),
    ("shapes", "Shapes"),
    ("colours", "Colours and materials"),
    ("wheels", "Wheels"),
    ("details", "Details"),
    ("lettering", "Lettering"),
    ("review", "Review"),
    ("road", "Road test"),
    ("release", "Release"),
]
KEYS = [k for k, _ in STEPS]
PAINTS = {"concepts", "shapes", "colours", "wheels", "details", "lettering"}  # their options are cars
CHECKS = ["review", "road", "release"]  # the whole car again, after any change
STATES = {"todo": "to do", "claude": "Claude on it", "waiting": "waiting for you", "decided": "decided",
          "look": "needs a look", "skipped": "skipped"}


class SheetError(Exception):
    pass


def today():
    return datetime.date.today().isoformat()


def title_of(name):
    """"TSC_PressRun" -> "Press Run", as the gallery says it."""
    name = name[4:] if name.startswith("TSC_") else name
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name.replace("_", " "))


def path(car):
    if not NAME.fullmatch(car or ""):
        raise SheetError(f"not a skin's name: {car!r}")
    return SKINS / car / "sheet.json"


def load(car):
    p = path(car)
    if not p.exists():
        raise SheetError(f"{car} has no sheet: start one with `new`")
    return json.loads(p.read_text("utf-8"))


def save(sheet):
    """The whole file or nothing (the Lab reads it), retrying while Windows holds it open."""
    p = path(sheet["car"])
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=p.parent, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(sheet, f, indent=1, ensure_ascii=False)
        f.write("\n")
    for k in range(20):
        try:
            os.replace(tmp, p)
            return
        except PermissionError:
            if k == 19:
                Path(tmp).unlink(missing_ok=True)
                raise
            time.sleep(0.05)


def step_of(sheet, key):
    if key not in KEYS:
        raise SheetError(f"no step {key!r}: " + ", ".join(KEYS))
    return sheet["steps"][KEYS.index(key)]


def blank(key, name):
    return {"key": key, "name": name, "state": "todo", "decision": "", "date": "", "options": [], "pick": None,
            "why": "", "was": []}


def new(car, words):
    if path(car).exists():
        raise SheetError(f"{car} has a sheet already")
    if (SKINS / car / "design.py").exists():
        raise SheetError(f"{car} was made the old way: it stays on the stand with its notes. A studio car starts "
                         "afresh, under a new name")
    sheet = {"car": car, "title": title_of(car), "words": words, "started": today(),
             "steps": [blank(k, n) for k, n in STEPS]}
    save(sheet)
    return sheet


def on(car, key):
    sheet = load(car)
    st = step_of(sheet, key)
    if st["state"] in ("decided", "skipped"):
        raise SheetError(f"{st['name']} is {st['state']}: go back to it to change it")
    st["state"] = "claude"
    save(sheet)
    return sheet


def camel(title):
    words = re.findall(r"[A-Za-z0-9]+", title)
    return "".join(w[:1].upper() + w[1:] for w in words)


def option(car, key, title, skin=None, file=None):
    """Add an option under the next letter. Without skin or file, make the skin beside the car."""
    sheet = load(car)
    st = step_of(sheet, key)
    if st["state"] in ("decided", "skipped"):
        raise SheetError(f"{st['name']} is {st['state']}: go back to it first")
    letter = chr(65 + len(st["options"]))
    opt = {"key": letter, "title": title}
    if file:
        if not (SKINS / car / file).is_file():
            raise SheetError(f"no file {file} in {car}'s folder")
        opt["file"] = Path(file).as_posix()
    else:
        if not skin:
            skin = f"{car}_{camel(title)}"
            folder = SKINS / skin
            if folder.exists():
                raise SheetError(f"{skin} exists already: name the option another way, or pass --skin {skin}")
            folder.mkdir()
            own = SKINS / car
            if (own / "design.py").exists():
                shutil.copyfile(own / "design.py", folder / "design.py")
            if (own / "art").is_dir():
                shutil.copytree(own / "art", folder / "art")
            (folder / "notes.md").write_text(
                f"Option {letter} of {car}'s {st['name']} step, {today()}: {title}. Made as a copy of the car's "
                "design to change; if it's picked, its design becomes the car's (tool/sheet.py).\n", encoding="utf-8")
        elif not (SKINS / skin).is_dir():
            raise SheetError(f"no skin called {skin}")
        if any(o.get("skin") == skin for o in st["options"]):
            raise SheetError(f"{skin} is an option already")
        opt["skin"] = skin
    st["options"].append(opt)
    st["state"] = "claude"
    save(sheet)
    return sheet, opt


def ask(car, key):
    sheet = load(car)
    st = step_of(sheet, key)
    if len(st["options"]) < 2:
        raise SheetError(f"{st['name']} has {len(st['options'])} option(s): with only one direction, decide it")
    for o in st["options"]:
        if "skin" in o and not (SKINS / o["skin"] / "design.py").exists():
            raise SheetError(f"option {o['key']} ({o['skin']}) has no design yet")
    st["state"] = "waiting"
    save(sheet)
    return sheet


def installed():
    p = SKINS / "installed.json"
    return json.loads(p.read_text("utf-8")) if p.exists() else {}


def borrows(text, names):
    """The names among `names` whose folder this design loads (paths.SKINS / "<name>" / ...)."""
    return [n for n in names if re.search(r"[\"'/\\]" + re.escape(n) + r"[\"'/\\]", text)]


def forget_rounds(gone):
    """Take deleted skins out of their rounds; a round left with fewer than two takes goes."""
    p = SKINS / "rounds.json"
    if not gone or not p.exists():
        return
    rounds = json.loads(p.read_text("utf-8"))
    kept = []
    for r in rounds:
        r["takes"] = [t for t in r["takes"] if t["name"] not in gone]
        if len(r["takes"]) >= 2:
            kept.append(r)
    if kept != rounds:
        p.write_text(json.dumps(kept, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def pick(car, key, letter, decision):
    """The user's pick. Returns what was done, in lines for Claude."""
    sheet = load(car)
    st = step_of(sheet, key)
    if not st["options"]:
        raise SheetError(f"{st['name']} has no options: decide it")
    letter = letter.upper() if letter.lower() != "none" else None
    chosen = next((o for o in st["options"] if o["key"] == letter), None)
    if letter and not chosen:
        raise SheetError(f"{st['name']} has no option {letter}: " + ", ".join(o["key"] for o in st["options"]))
    if not decision.strip():
        raise SheetError("say what was decided, in a few words")
    others = [o for o in st["options"] if o is not chosen]
    skins_gone = [o["skin"] for o in others if o.get("skin") and o["skin"] != car]
    moves = chosen is not None and chosen.get("skin") not in (None, car)
    final = SKINS / (chosen["skin"] if moves else car) / "design.py"
    if final.exists():
        leans = borrows(final.read_text("utf-8"), skins_gone + ([car] if moves else []))
        if leans:
            raise SheetError(f"{final.parent.name}'s design loads {', '.join(leans)}'s, which the pick replaces or "
                             "deletes: write it out whole first")
    said = []
    game = installed()
    if moves:
        src = SKINS / chosen["skin"]
        own = SKINS / car
        own.mkdir(exist_ok=True)
        shutil.copyfile(src / "design.py", own / "design.py")
        if (src / "art").is_dir():
            shutil.copytree(src / "art", own / "art", dirs_exist_ok=True)
        if (src / "thumb.png").exists():
            shutil.copyfile(src / "thumb.png", own / "thumb.png")
        said.append(f"{chosen['skin']}'s design, pictures and thumb are now {car}'s: show {car} to paint it under "
                    "its own name")
        if f"{chosen['skin']}.zip" in game:
            said.append(f"kept {chosen['skin']}'s folder: it's in the game")
        else:
            shutil.rmtree(src)
    gone = []
    for name in skins_gone:
        if f"{name}.zip" in game:
            said.append(f"kept {name}: it's in the game")
            continue
        if (SKINS / name).is_dir():
            shutil.rmtree(SKINS / name)
        gone.append(name)
    for o in others:
        if o.get("file") and (SKINS / car / o["file"]).exists():
            (SKINS / car / o["file"]).unlink()
            gone.append(o["file"])
    forget_rounds(set(gone) | ({chosen["skin"]} if moves else set()))
    if gone:
        said.append("deleted the others: " + ", ".join(gone))
    st.update(state="decided", decision=decision.strip(), date=today(), pick=letter, why="")
    save(sheet)
    return sheet, said


def decide(car, key, decision=""):
    sheet = load(car)
    st = step_of(sheet, key)
    if not st["pick"] and any(o.get("skin") != car for o in st["options"]):
        raise SheetError(f"{st['name']} has options: pick one, or pick none")
    if not st["pick"]:
        st["options"] = []  # only the car as it was, changed in place
    decision = decision.strip()
    if not decision and not st["decision"]:
        raise SheetError("say what was decided, in a few words")
    if decision and st["decision"] and decision != st["decision"]:
        st["was"].append({k: st[k] for k in ("decision", "date", "pick", "options")})
        st["options"], st["pick"] = [], None
    st.update(state="decided", decision=decision or st["decision"], date=today(), why="")
    save(sheet)
    return sheet


def skip(car, key, why):
    sheet = load(car)
    st = step_of(sheet, key)
    if st["options"] and not st["pick"]:
        raise SheetError(f"{st['name']} has options: pick one, or pick none")
    st.update(state="skipped", why=why.strip(), date=today())
    save(sheet)
    return sheet


def back(car, key, why, affects=()):
    sheet = load(car)
    st = step_of(sheet, key)
    if st["state"] not in ("decided", "skipped", "look"):
        raise SheetError(f"{st['name']} is {STATES[st['state']]}, not decided: nothing to go back to")
    at = KEYS.index(key)
    for a in affects:
        if a not in KEYS or KEYS.index(a) <= at:
            raise SheetError(f"{a!r} isn't a step after {st['name']}")
    st["was"].append({k: st[k] for k in ("decision", "date", "pick", "options")})
    st.update(state="claude", decision="", date=today(), options=[], pick=None, why=why.strip())
    if key in PAINTS and (SKINS / car / "design.py").exists():
        st["options"].append({"key": "A", "title": "as it is", "skin": car})
    for a in list(affects) + [c for c in CHECKS if KEYS.index(c) > at]:
        later = step_of(sheet, a)
        if later["state"] in ("decided", "skipped"):
            later.update(state="look", why=why.strip() if a in affects else "the car changed")
    save(sheet)
    return sheet


def here(sheet):
    """The step the car is at: the first one not decided or skipped."""
    return next((st for st in sheet["steps"] if st["state"] not in ("decided", "skipped")), None)


def describe(sheet):
    at = here(sheet)
    lines = [f"{sheet['title']} ({sheet['car']}), in the studio since {sheet['started']}: \"{sheet['words']}\""]
    for n, st in enumerate(sheet["steps"], 1):
        state = STATES[st["state"]] + (" (changed)" if st["was"] and st["state"] == "decided" else "")
        if st["state"] in ("decided", "skipped") and st["date"]:
            state += " " + st["date"][5:]
        what = ""
        if st["state"] == "decided":
            chosen = next((o for o in st["options"] if o["key"] == st["pick"]), None)
            what = (f"{chosen['key']} {chosen['title']}: " if chosen and chosen["title"] != "as it is" else "") + st["decision"]
        elif st["state"] in ("skipped", "look"):
            what = st["why"]
        if st["state"] in ("claude", "waiting") and st["options"]:
            what = ", ".join(f"{o['key']} {o['title']} ({o.get('skin') or o.get('file')})" for o in st["options"])
            if st["why"]:
                what = f"{st['why']}; {what}"
        elif st["state"] == "claude" and st["why"]:
            what = st["why"]
        mark = ">" if st is at else " "
        lines.append(f" {mark}{n:>2} {st['name']:<22} {state:<24} {what}".rstrip())
    return "\n".join(lines)


def cars():
    return [json.loads(p.read_text("utf-8")) for p in sorted(SKINS.glob("*/sheet.json"))]


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        for sheet in cars():
            at = here(sheet)
            print(f"{sheet['car']:<28} " + (f"{at['name']}, {STATES[at['state']]}" if at else "released"))
        return
    if argv[0] not in ("new", "on", "option", "ask", "pick", "decide", "skip", "back"):
        print(describe(load(argv[0])))
        return
    ap = argparse.ArgumentParser(prog="python -m tool.sheet")
    ap.add_argument("command")
    ap.add_argument("car")
    ap.add_argument("rest", nargs="*")
    ap.add_argument("--words", default="")
    ap.add_argument("--skin")
    ap.add_argument("--file")
    ap.add_argument("--affects", nargs="*", default=[])
    a = ap.parse_args(argv)
    need = {"new": 0, "on": 1, "option": 2, "ask": 1, "pick": 3, "decide": (1, 2), "skip": 2, "back": 2}[a.command]
    lo, hi = need if isinstance(need, tuple) else (need, need)
    if not lo <= len(a.rest) <= hi:
        ap.error(f"{a.command}: see the usage at the top of tool/sheet.py")
    said = []
    if a.command == "new":
        sheet = new(a.car, a.words)
    elif a.command == "on":
        sheet = on(a.car, a.rest[0])
    elif a.command == "option":
        sheet, opt = option(a.car, a.rest[0], a.rest[1], a.skin, a.file)
        said.append(f"option {opt['key']}: " + (opt.get("file") or opt["skin"]))
    elif a.command == "ask":
        sheet = ask(a.car, a.rest[0])
    elif a.command == "pick":
        sheet, said = pick(a.car, *a.rest)
    elif a.command == "decide":
        sheet = decide(a.car, *a.rest)
    elif a.command == "skip":
        sheet = skip(a.car, *a.rest)
    else:
        sheet = back(a.car, a.rest[0], a.rest[1], a.affects)
    for line in said:
        print(line)
    print(describe(sheet))


if __name__ == "__main__":
    try:
        main()
    except SheetError as e:
        sys.exit(str(e))
