"""Notes on the car: in the Lab's Studio the user clicks the car where they mean and writes what they
want there (their pick of the mockups, 2026-09-27: CHECKLIST.md, "The Lab", step 7). Each note keeps
the skin, the step it was written at, the part under the click, the point (for its pin), and the
user's words, in skins/notes.json. The page saves them through the viewer's server (tool/view.py,
/api/notes).

They reach Claude with the user's next message: a UserPromptSubmit hook (.claude/settings.json) runs
this file with --hook, which prints the new ones and marks them sent. Claude marks a note done once
it's handled, and its pin leaves the car:

    python -m tool.notes                        the notes not done yet, every skin
    python -m tool.notes done <skin> [N ...]    mark notes done (all of the skin's, without numbers)

Standard library only, and runnable as a file: the hook runs it with whatever Python the computer
has (the Mac's own python3 has no numpy)."""

import json
import os
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FILE = REPO / "skins" / "notes.json"
LONGEST = 2000  # characters in a note


def load():
    return json.loads(FILE.read_text("utf-8")) if FILE.exists() else []


def save(notes):
    fd, tmp = tempfile.mkstemp(dir=FILE.parent, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(notes, f, indent=1, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, FILE)  # whole or not at all: the page and the hook both read it


def of(skin):
    """The skin's notes not done yet, in the order they were written."""
    return [n for n in load() if n["skin"] == skin and n["state"] != "done"]


def next_n(skin):
    return max((x["n"] for x in load() if x["skin"] == skin), default=0) + 1


def add(skin, text, step=None, step_name="", part=None, at=None, normal=None):
    """A new note from the Studio. part: {"id", "label", "token"}; at and normal: the clicked point
    and the surface's facing, in the viewer's metres. Returns the note."""
    text = str(text or "").strip()[:LONGEST]
    if not text:
        raise ValueError("an empty note")
    if not isinstance(skin, str) or not (REPO / "skins" / skin / "design.py").is_file():
        raise ValueError(f"no skin called {skin!r}")
    vec = lambda v: [round(float(x), 4) for x in v][:3] if isinstance(v, list) and len(v) == 3 else None
    part = part if isinstance(part, dict) else {}
    notes = load()
    note = {
        "skin": skin,
        "n": next_n(skin),
        "text": text,
        "step": step if isinstance(step, int) else None,
        "step_name": str(step_name or "")[:80],
        "part": {"id": part.get("id") if isinstance(part.get("id"), int) else None,
                 "label": str(part.get("label") or "")[:80], "token": str(part.get("token") or "")[:80]},
        "at": vec(at),
        "normal": vec(normal),
        "made": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "state": "new",  # new -> sent (Claude has read it) -> done (handled)
    }
    notes.append(note)
    save(notes)
    return note


def remove(skin, n):
    """The user takes a note back (its × in the Studio)."""
    save([x for x in load() if not (x["skin"] == skin and x["n"] == n)])


def done(skin, numbers=()):
    notes = load()
    hit = [x for x in notes if x["skin"] == skin and x["state"] != "done" and (not numbers or x["n"] in numbers)]
    for x in hit:
        x["state"] = "done"
    save(notes)
    return hit


def line(x):
    where = f"on {x['part']['token']} ({x['part']['label']})" if x["part"]["token"] else "on the car"
    step = f"at step {x['step']} ({x['step_name']})" if x["step"] is not None else ""
    return f"- {x['skin']}, note {x['n']}, {step + ', ' if step else ''}{where}: \"{x['text']}\""


def hook():
    """For the UserPromptSubmit hook: print the notes Claude hasn't seen, and mark them sent."""
    notes = load()
    new = [x for x in notes if x["state"] == "new"]
    if not new:
        return
    print("Notes the user left on the car in the Lab's Studio since their last message (their words, "
          "each pinned to the part they clicked; `python -m tool.notes done <skin> <n>` once one is handled):")
    for x in new:
        print(line(x))
        x["state"] = "sent"
    save(notes)


def main(args):
    if args[:1] == ["--hook"]:
        try:
            hook()
        except Exception as e:  # never block the user's message over a note
            print(f"(The Lab's notes couldn't be read: {e})")
        return
    if args[:1] == ["done"] and len(args) >= 2:
        hit = done(args[1], {int(a) for a in args[2:]})
        print(f"{len(hit)} note(s) done" if hit else "no open notes matched")
        return
    if args:
        sys.exit(__doc__)
    for x in (n for n in load() if n["state"] != "done"):
        print(f"{line(x)} [{x['state']}]")


if __name__ == "__main__":
    main(sys.argv[1:])
