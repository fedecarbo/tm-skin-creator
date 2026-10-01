"""A car's sets of options (the user's pick, 2026-09-28: LEARNED.md, Decisions): whenever the user
asks for a few ideas on anything, in any order ("can we try 3 different materials for X", "a few
concepts for the wheels", or a new car's first concepts), Claude paints each option as a whole car
and they wait in the Lab's list, "For you to pick", until the user picks one there or in the chat.
skins/<car>/sets.json, written only by these commands, so the Lab shows it and keeps no list of its
own.

    python -m tool.sets                                      every car with sets, and what's open
    python -m tool.sets <car>                                the car's sets
    python -m tool.sets new <car> "<title>" [--words "..."]  a new set, being painted: prints its number
    python -m tool.sets option <car> <n> "<Title>" [--skin <name>]
                                                             an option in it: A, B, C...
    python -m tool.sets open <car> <n>                       all painted: the user's turn
    python -m tool.sets pick <car> <n> <letter|none> "<what was picked, a few words>"
    python -m tool.sets drop <car> <n> "<why>"               not wanted any more

A set is painting (Claude on it), open (the user's turn), picked, or dropped. Its title says what
it's about ("Wheels · 3 ideas", "3 concepts"); its words are the user's, when they asked.

Options. An option is a skin beside the car, skins/<car>_<Title>/: `option` makes it as a copy of the
car's design.py and art/ to change, or an empty folder while the car has no design yet (a new car's
concepts); --skin takes one that exists. `open` wants two or more, each with a design. A pick is final
(the user, 2026-09-28: "I dont think we can keep on maintaining options that I don't like"): the
picked option's design.py, art/ and thumb.png become the car's, each option's picture is kept for the
Lab's "Earlier picks" (skins/<car>/sets/<n>/<letter>.png), and every option's folder goes (git's
history keeps them). `pick none` keeps no option: the car's design as it is (a mix Claude wrote into
it). An option's design must stand on its own: one that loads the car's or another option's would
break once they're gone, so the pick refuses it. An option that's in the game (skins/installed.json)
is kept, and the pick says so. `drop` deletes the options the same way, keeping their pictures.

Any car can have sets: a new one starts with its concepts as its first set (`new` makes its folder),
and one made before can have them too.

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
STATES = {"painting": "Claude is painting them", "open": "for you to pick", "picked": "picked", "dropped": "dropped"}


class SetsError(Exception):
    pass


def now():
    return datetime.datetime.now().replace(microsecond=0).isoformat()


def title_of(name):
    """"TSC_PressRun" -> "Press Run", as the gallery says it."""
    name = name[4:] if name.startswith("TSC_") else name
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name.replace("_", " "))


def camel(title):
    words = re.findall(r"[A-Za-z0-9]+", title)
    return "".join(w[:1].upper() + w[1:] for w in words)


def path(car):
    if not NAME.fullmatch(car or ""):
        raise SetsError(f"not a skin's name: {car!r}")
    return SKINS / car / "sets.json"


def load(car):
    p = path(car)
    return json.loads(p.read_text("utf-8")) if p.exists() else {"car": car, "sets": []}


def save(doc):
    """The whole file or nothing (the Lab reads it), retrying while Windows holds it open."""
    p = path(doc["car"])
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=p.parent, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
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


def set_of(doc, n):
    for s in doc["sets"]:
        if s["n"] == int(n):
            return s
    raise SetsError(f"{doc['car']} has no set {n}")


def new(car, title, words=""):
    """A new set, being painted. A car with no folder yet gets one: a new car's first concepts."""
    if not title.strip():
        raise SetsError("say what the set is about")
    doc = load(car)
    (SKINS / car).mkdir(parents=True, exist_ok=True)
    s = {"n": max((x["n"] for x in doc["sets"]), default=0) + 1, "title": title.strip(), "words": words.strip(),
         "made": now(), "state": "painting", "options": [], "pick": None, "decision": "", "done": ""}
    doc["sets"].append(s)
    save(doc)
    return doc, s


def option(car, n, title, skin=None):
    """An option under the next letter: a copy of the car's design to change (or an empty folder while
    it has none), or --skin, a skin that exists."""
    doc = load(car)
    s = set_of(doc, n)
    if s["state"] in ("picked", "dropped"):
        raise SetsError(f"set {n} is {s['state']}")
    letter = chr(65 + len(s["options"]))
    if not skin:
        skin = f"{car}_{camel(title)}"
        folder = SKINS / skin
        if folder.exists():
            raise SetsError(f"{skin} exists already: name the option another way, or pass --skin {skin}")
        folder.mkdir()
        own = SKINS / car
        if (own / "design.py").exists():
            shutil.copyfile(own / "design.py", folder / "design.py")
        if (own / "art").is_dir():
            shutil.copytree(own / "art", folder / "art")
        (folder / "notes.md").write_text(
            f"Option {letter} of {car}'s set {n} ({s['title']}), {now()[:10]}: {title}. Made as a copy of the car's "
            "design to change; if it's picked, its design becomes the car's (tool/sets.py).\n", encoding="utf-8")
    elif not (SKINS / skin).is_dir():
        raise SetsError(f"no skin called {skin}")
    if skin == car or any(o["skin"] == skin for o in s["options"]):
        raise SetsError(f"{skin} can't be an option here")
    s["options"].append({"key": letter, "title": title, "skin": skin})
    s["state"] = "painting"
    save(doc)
    return doc, s["options"][-1]


def open_(car, n):
    doc = load(car)
    s = set_of(doc, n)
    if s["state"] in ("picked", "dropped"):
        raise SetsError(f"set {n} is {s['state']}")
    if len(s["options"]) < 2:
        raise SetsError(f"set {n} has {len(s['options'])} option(s): with one, just make it on the car")
    for o in s["options"]:
        if not (SKINS / o["skin"] / "design.py").exists():
            raise SetsError(f"option {o['key']} ({o['skin']}) has no design yet")
    s["state"] = "open"
    save(doc)
    return doc


def installed():
    p = SKINS / "installed.json"
    return json.loads(p.read_text("utf-8")) if p.exists() else {}


def borrows(text, names):
    """The names among `names` whose design this one loads (`borrow("<name>")`, tool/skin.py)."""
    return [n for n in names if re.search(r"[\"'/\\]" + re.escape(n) + r"[\"'/\\]", text)]


def keep_pictures(car, s):
    """Each option's picture (its gallery thumb) into skins/<car>/sets/<n>/<letter>.png, for the Lab's
    earlier picks, before its folder goes."""
    folder = SKINS / car / "sets" / str(s["n"])
    for o in s["options"]:
        thumb = SKINS / o["skin"] / "thumb.png"
        if thumb.exists():
            folder.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(thumb, folder / f"{o['key']}.png")
            o["picture"] = f"sets/{s['n']}/{o['key']}.png"


def clear(car, s):
    """Delete the set's options, unless one is in the game. Returns lines for Claude."""
    said, gone, game = [], [], installed()
    for o in s["options"]:
        name = o["skin"]
        if name == car:
            continue
        if f"{name}.zip" in game:
            said.append(f"kept {name}: it's in the game")
            continue
        if (SKINS / name).is_dir():
            shutil.rmtree(SKINS / name)
        gone.append(name)
    if gone:
        said.append("deleted: " + ", ".join(gone))
    return said


def pick(car, n, letter, decision):
    """The user's pick: its design becomes the car's; the others go. `none`: the car as it is."""
    doc = load(car)
    s = set_of(doc, n)
    if s["state"] in ("picked", "dropped"):
        raise SetsError(f"set {n} is {s['state']} already")
    if not decision.strip():
        raise SetsError("say what was picked, in a few words")
    chosen = None
    if letter.lower() != "none":
        chosen = next((o for o in s["options"] if o["key"] == letter.upper()), None)
        if not chosen:
            raise SetsError(f"set {n} has options " + ", ".join(o["key"] for o in s["options"]) + f", not {letter}")
    others = [o["skin"] for o in s["options"] if o is not chosen]
    final = SKINS / (chosen["skin"] if chosen else car) / "design.py"
    if final.exists():
        leans = borrows(final.read_text("utf-8"), others + ([car] if chosen else []))
        if leans:
            raise SetsError(f"{final.parent.name}'s design loads {', '.join(leans)}'s, which the pick replaces or "
                            "deletes: write it out whole first")
    elif chosen:
        raise SetsError(f"{chosen['skin']} has no design")
    keep_pictures(car, s)
    said = []
    if chosen:
        src, own = SKINS / chosen["skin"], SKINS / car
        shutil.copyfile(src / "design.py", own / "design.py")
        if (src / "art").is_dir():
            shutil.copytree(src / "art", own / "art", dirs_exist_ok=True)
        if (src / "thumb.png").exists():
            shutil.copyfile(src / "thumb.png", own / "thumb.png")
        said.append(f"{chosen['skin']}'s design, pictures and thumb are now {car}'s: show {car} to paint it under "
                    "its own name")
    said += clear(car, s)
    s.update(state="picked", pick=chosen["key"] if chosen else None, decision=decision.strip(), done=now())
    save(doc)
    return doc, said


def drop(car, n, why):
    doc = load(car)
    s = set_of(doc, n)
    if s["state"] in ("picked", "dropped"):
        raise SetsError(f"set {n} is {s['state']} already")
    keep_pictures(car, s)
    said = clear(car, s)
    s.update(state="dropped", decision=why.strip(), done=now())
    save(doc)
    return doc, said


# ---- For the Lab (viewer/lab-car.js, through tool/view.py's /api/sets) ----


def cars():
    return [json.loads(p.read_text("utf-8")) for p in sorted(SKINS.glob("*/sets.json"))]


def find(skin):
    """The car `skin` is, or is an option of (the Lab follows whichever skin Claude painted last, often
    an option); the skin itself when it's in no set."""
    if not NAME.fullmatch(skin or ""):
        return None
    for doc in cars():
        if doc["car"] != skin and any(o["skin"] == skin for s in doc["sets"] for o in s["options"]):
            return doc["car"]
    return skin


def lab(skin):
    """What the Lab shows for `skin`: its car's sets, newest first."""
    car = find(skin)
    if not car:
        return None
    doc = load(car)
    return {"car": car, "title": title_of(car), "skin": skin, "sets": sorted(doc["sets"], key=lambda s: s["n"], reverse=True)}


def describe(doc):
    lines = [f"{title_of(doc['car'])} ({doc['car']}): {len(doc['sets'])} set(s)"]
    for s in doc["sets"]:
        opts = ", ".join(f"{o['key']} {o['title']}" + (f" ({o['skin']})" if s["state"] in ("painting", "open") else "")
                         for o in s["options"])
        what = f"picked {s['pick'] or 'none'}: {s['decision']}" if s["state"] == "picked" else (
            f"dropped: {s['decision']}" if s["state"] == "dropped" else STATES[s["state"]])
        lines.append(f"  {s['n']:>2}. {s['title']} [{what}] {opts}".rstrip())
    return "\n".join(lines)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        for doc in cars():
            waiting = [s for s in doc["sets"] if s["state"] in ("painting", "open")]
            print(f"{doc['car']:<28} " + (", ".join(f"{s['n']}. {s['title']} ({STATES[s['state']]})" for s in waiting)
                                         or "nothing open"))
        return
    if argv[0] not in ("new", "option", "open", "pick", "drop"):
        print(describe(load(argv[0])))
        return
    ap = argparse.ArgumentParser(prog="python -m tool.sets")
    ap.add_argument("command")
    ap.add_argument("car")
    ap.add_argument("rest", nargs="*")
    ap.add_argument("--words", default="")
    ap.add_argument("--skin")
    a = ap.parse_args(argv)
    need = {"new": 1, "option": 2, "open": 1, "pick": 3, "drop": 2}[a.command]
    if len(a.rest) != need:
        ap.error(f"{a.command}: see the usage at the top of tool/sets.py")
    said = []
    if a.command == "new":
        doc, s = new(a.car, a.rest[0], a.words)
        said.append(f"set {s['n']}: {s['title']}")
    elif a.command == "option":
        doc, o = option(a.car, a.rest[0], a.rest[1], a.skin)
        said.append(f"option {o['key']}: {o['skin']}")
    elif a.command == "open":
        doc = open_(a.car, a.rest[0])
    elif a.command == "pick":
        doc, said = pick(a.car, *a.rest)
    else:
        doc, said = drop(a.car, *a.rest)
    for line in said:
        print(line)
    print(describe(doc))


if __name__ == "__main__":
    try:
        main()
    except SetsError as e:
        sys.exit(str(e))
