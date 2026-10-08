"""The gates: a car is said to be done only once the judge has passed it as it is (the user, 2026-10-07: "If rules
don't work, then let's find another approach ... it cannot randomly make mistakes").

    python -m tool.gate <name>                    what the gates say of the car now
    python -m tool.gate <name> --despite "<why>"  let what blocks go, said to the user in the Lab: what it is and why

A car passes when this computer's verdict (tool/judge.py: build/<name>/verdict.json) is of its design as it is
(`design_hash`: design.py, the designs it borrows, its art), nothing in it blocks but what was let go, and, with `looks`,
the close looks (tool/close.py) have seen that design: a car shown alone wants them, an option in a set doesn't. Where
it bites:
  tool.notes done      a note handled: with the close looks
  tool.sets open       a set's takes: each judged
  tool.skin install    judged in the paint it puts in the game
  a pass               an agent whose brief names a car with a language (language.md): with the close looks, refused
                       before it starts (tool/guard.py, PreToolUse)
  the end of a turn    each car whose design, verdict or what was let go changed in the turn: held once for each thing
                       wrong (tool/guard.py, Stop)
What blocks and is meant, or is still there after about three rounds of fixing, is let go with --despite, never
quietly: the Lab's timeline says what it is and why, and skins/<name>/despite.json keeps it let go while the design
is the same. A car never judged, judged before its last change or not looked at close can't be let go: showing it
again is cheap.

Standard library only: tool/notes.py, tool/sets.py and tool/guard.py run it, the last with whatever Python the
computer has.
"""

import hashlib
import json
import re
import sys
import time

from tool import paths

TOP = 3  # blocking findings a refusal names


def design_hash(name):
    """The design's hash: design.py, the designs it borrows (borrow("...")), its art."""
    h, seen = hashlib.sha256(), set()

    def add(n):
        if n in seen:
            return
        seen.add(n)
        p = paths.SKINS / n / "design.py"
        if not p.exists():
            return
        src = p.read_bytes()
        h.update(src)
        for m in re.findall(rb'borrow\("([^"]+)"\)', src):
            add(m.decode())
        for f in sorted((paths.SKINS / n / "art").glob("*")):
            if f.is_file():
                h.update(f.name.encode())
                h.update(f.read_bytes())
    add(name)
    return h.hexdigest()[:16] if seen and (paths.SKINS / name / "design.py").exists() else ""


def _read(p):
    try:
        return json.loads(p.read_text("utf-8"))
    except (OSError, ValueError):
        return None


def verdict(name):
    return _read(paths.BUILD / name / "verdict.json")


def blocks(name, v):
    """The verdict's blocking findings, but those let go for this design."""
    let = _read(paths.SKINS / name / "despite.json") or {}
    gone = set(let.get("blocks", ())) if let.get("design") == v.get("design") else set()
    return [f for f in v.get("findings", ()) if f.get("level") == "block" and f.get("text") not in gone]


def alone(name):
    """The car shown alone, not an option in one of a car's sets (tool/sets.py)."""
    from tool import sets
    return sets.find(name) == name


def wrong(name, looks=True):
    """What keeps the car from passing: (what, a line) each, what one of unjudged, changed, unlooked and blocks;
    nothing when it passes or has no design. looks: the close looks wanted too, when it's shown alone."""
    if not (paths.SKINS / name / "design.py").exists():
        return []
    v = verdict(name)
    show = f"`PY -m tool.skin show {name}`" + (f", then `PY -m tool.close {name}`" if looks and alone(name) else "")
    if v is None:
        return [("unjudged", f"{name} hasn't been judged on this computer: {show}")]
    if v.get("design") != design_hash(name):
        return [("changed", f"{name}'s design changed since it was judged: {show}")]
    out = []
    if looks and (v.get("close") or {}).get("design") != v["design"] and alone(name):
        out.append(("unlooked", f"{name} hasn't been looked at close as it is: `PY -m tool.close {name}`"))
    b = blocks(name, v)
    if b:
        out.append(("blocks", f"{name}: the judge blocks {len(b)}: " + "; ".join(f["text"] for f in b[:TOP])
                    + (f"; and {len(b) - TOP} more (`PY -m tool.gate {name}`)" if len(b) > TOP else "")))
    return out


def refusal(names, what, looks=True):
    """Why `what` can't go on, or None when every car named passes."""
    found = [w for n in names for w in wrong(n, looks)]
    if not found:
        return None
    text = (f"Refused: {what} waits for the judge to pass {'the car' if len(names) == 1 else 'each car'}.\n"
            + "\n".join(f"  {line}" for _, line in found))
    if any(k == "blocks" for k, _ in found):
        text += ("\nFix what blocks and show it again (about three rounds). What's meant, or still there after that: "
                 "`PY -m tool.gate <name> --despite \"<why, in plain words>\"` tells the user in the Lab; then again.")
    return text


def _place(text):
    """The place a finding names last, in plain words: "(the front flank)"."""
    m = re.search(r"\(([^()]*)\)\s*$", text)
    return f" ({m.group(1)})" if m else ""


def despite(name, why):
    """Let the car's blocks go, for this design: said in the Lab's timeline, what they are and why."""
    from tool import judge, notes
    why = " ".join(str(why or "").split())
    if not why:
        raise SystemExit("--despite needs the why, in plain words")
    stale = [line for k, line in wrong(name, looks=False) if k != "blocks"]
    if stale:
        raise SystemExit("\n".join(stale))
    v = verdict(name)
    b = blocks(name, v)
    if not b:
        raise SystemExit(f"nothing blocks on {name}: nothing to let go")
    p = paths.SKINS / name / "despite.json"
    let = _read(p) or {}
    kept = let.get("blocks", []) if let.get("design") == v["design"] else []
    paths.write(p, json.dumps({"design": v["design"], "why": why, "blocks": kept + [f["text"] for f in b],
                               "when": time.strftime("%Y-%m-%d %H:%M")}, indent=1, ensure_ascii=False) + "\n")
    what = "; ".join(judge.KINDS.get(f["kind"], f["kind"]) + _place(f["text"]) for f in b)
    notes.say(name, f"{why} Still there, as the tool measures it: {what}.")
    return f"{len(b)} let go on {name}, and said in the Lab"


def main(args):
    if len(args) == 3 and args[1] == "--despite":
        print(despite(args[0], args[2]))
        return
    if len(args) != 1 or args[0].startswith("-"):
        sys.exit(__doc__)
    name = args[0]
    if not (paths.SKINS / name / "design.py").exists():
        sys.exit(f"{name} has no design: nothing to judge")
    v, found = verdict(name), wrong(name)
    for _, line in found:
        print(line)
    let = {}
    if v and v.get("design") == design_hash(name):
        for f in blocks(name, v)[TOP:]:
            print(f"  BLOCK: {f['kind']}: {f['text']}")
        let = _read(paths.SKINS / name / "despite.json") or {}
        if let.get("design") == v["design"]:
            print(f"let go ({let['when']}): {let['why']}")
    if not found:
        print(f"{name} passes: judged as it is" + (", looked at close" if alone(name) else "") + ", nothing blocks"
              + (" but what was let go" if let.get("design") == v["design"] else ""))


if __name__ == "__main__":
    main(sys.argv[1:])
