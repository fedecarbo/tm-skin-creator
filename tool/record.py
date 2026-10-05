"""The tool measured against the record (the plan's step 7, PLAN.md): of the flaws the user pointed
out on a car they were shown, how many do the tool's own checks name on that car before they would?
For a change to a check: the score before and after it says whether cars get better before the user
sees them. On demand only.

    python -m tool.record          paint every flaw's car again with this code and score the checks
    python -m tool.record new      what the user said in the records that the test set hasn't sorted

The test set, tool/record.json, is everything the user said about a car in quotes, as the records
keep it (skins/*/notes.md in every version in git's history, deleted skins too: `gather`), sorted
once by Claude: a flaw (something wrong on the car they were shown) or other (a wish, taste, an
answer, a name). A flaw has its kind (KINDS), where it was along the car (z, front to back, in cm,
or null), what was wrong, and either `before`, the commit whose design is the car they saw (`paint`:
its skin, when it isn't the record's), or `why` it can't be painted again (the tool fixed it in
itself, the car was never committed).

Each flaw with a `before` is painted again: that commit's skins with this code (the working tree's
tool, car and viewer, copied into the work folder), in a fresh process, and its checks run: the
measures (tool/measure.py: STOPS SHORT, GAP) and the paint box's notes on pictures (FOLD, CUT). A
check catches a flaw when it names the same kind where the flaw was (their stretches along the car
within SLACK cm), or anywhere on the car for a flaw with no place. What else the checks name on those
cars is said too: warnings the user never raised. The last run's score is kept in the work folder,
so the next says what it was.
"""

import io
import json
import re
import shutil
import subprocess
import sys
import tarfile
import time
from datetime import datetime
from pathlib import Path

from tool import paths, progress

TESTS = paths.REPO / "tool" / "record.json"
HOME = paths.WORK / "record"
SLACK = 5.0  # cm along the car

KINDS = {
    "short": "a paint stops before the surface it was meant to cover ends",
    "gap": "a hole inside a paint's run",
    "fold": "a picture or words over a fold or a sharp curve",
    "cut": "a shape cut off by an edge, an opening or a join",
    "spill": "a shape running off its panel onto the next piece",
    "over": "a paint laid over, or touching, another that should stay clear",
    "clear": "paint on or round the game's own number and name panels",
    "upside down": "words upside down or mirrored",
    "line": "a line that isn't smooth or doesn't sit where it should",
    "edge": "an edge soft, pixelated or outlined",
    "spread": "a pattern spread unevenly",
}
CHECKS = {"measure": "the measure", "picture": "the pictures' check"}

# What runs in the fresh process, from the copied tree: the car painted, its checks as findings.
CHILD = r'''
import json, re, sys
from tool import measure, paintbox, skin
name, out = sys.argv[1], sys.argv[2]
with skin.paint_slot():
    s = paintbox.Skin(name)
    s.measure = True
    skin.load_design(name)(s)
    s.end_steps()
found = []
for m in measure.measure(s):
    for side, r in m["sides"].items():
        if not r:
            continue
        for end, e in r["ends"].items():
            x = e.get("across")
            if x and not x["as_written"]:
                found.append({"check": "measure", "kind": "short", "z": [x["from"], x["to"]], "side": side,
                              "text": f"{m['step']}: {m['what']}, {end} end, bare past an opening"})
            if e["short"] >= measure.SHORT and not e["as_written"]:
                found.append({"check": "measure", "kind": "short", "z": [r[end], e["body"]], "side": side,
                              "text": f"{m['step']}: {m['what']}, {end} end {e['short']:.0f} cm short"})
        for g in r["gaps"]:
            if not g["as_written"]:
                found.append({"check": "measure", "kind": "gap", "z": [g["from"], g["to"]], "side": side,
                              "text": f"{m['step']}: {m['what']}, a gap of {g['from'] - g['to']:.0f} cm"})
for note in s.notes:
    for pattern, kind in ((r"decal at (.+?): the surface under the picture has a fold", "fold"),
                          (r"decal at (.+?): \d+% of the picture landed", "cut")):
        hit = re.match(pattern, note)
        spot = paintbox.SPOTS.get(hit.group(1).strip().lower()) if hit else None
        if hit:
            z = [spot["centre"][2] + spot["width"] / 2, spot["centre"][2] - spot["width"] / 2] if spot else None
            found.append({"check": "picture", "kind": kind, "z": z, "text": note})
json.dump(found, open(out, "w"))
'''


def git(*args, text=True):
    return subprocess.run(["git", "-C", str(paths.REPO), *args], capture_output=True, text=text, check=True).stdout


def key(said):
    return re.sub(r"\W+", " ", said[:60].lower()).strip()[:40]


def load():
    return json.loads(TESTS.read_text(encoding="utf-8"))


def gather():
    """Everything the user said in quotes in the records, every version of every one: [{skin, commit,
    said}], each the first time a record has it. A record's lines and paragraphs that name the user."""
    def blocks(text):
        out, cur = [], None
        for line in text.splitlines():
            if not line.strip() or line.startswith("#"):
                cur = None
            elif line.startswith("- ") or cur is None:
                cur = [line[2:] if line.startswith("- ") else line]
                out.append(cur)
            else:
                cur.append(line.strip())
        return [" ".join(b) for b in out]

    seen, found = set(), []
    for f in sorted(set(git("log", "--all", "--format=", "--name-only", "--", "skins/*/notes.md").split())):
        for commit in git("log", "--reverse", "--format=%H", "--", f).split():
            try:
                text = git("show", f"{commit}:{f}")
            except subprocess.CalledProcessError:
                continue  # the commit that deleted it
            for b in blocks(text):
                if not re.search(r"\buser\b", b, re.I):
                    continue
                for said in re.findall(r'["“]([^"”]{4,})["”]', b):
                    k = key(said)
                    if len(k) >= 8 and k not in seen:
                        seen.add(k)
                        found.append({"skin": f.split("/")[1], "commit": commit[:10], "said": said})
    return found


def unsorted(tests):
    known = {key(f["said"]) for f in tests["flaws"]} | {key(o.split(": ", 1)[1]) for o in tests["other"]}
    return [g for g in gather() if key(g["said"]) not in known]


def version(commit, skin):
    """The picture of the round the user saw: the newest skins/<skin>/versions/<n>.png at the commit."""
    names = git("ls-tree", "--name-only", commit, f"skins/{skin}/versions/").split()
    ns = [int(Path(n).stem) for n in names if Path(n).stem.isdigit()]
    return max(ns) if ns else None


def paint(flaw, tree):
    """The checks' findings on the car the user saw, painted with this code: a list, or {"error": ...}."""
    skin = flaw.get("paint", flaw["skin"])
    shutil.rmtree(tree / "skins", ignore_errors=True)
    blob = git("archive", flaw["before"], "--", "skins", ":(exclude)skins/*/versions", ":(exclude)skins/*/sets", text=False)
    with tarfile.open(fileobj=io.BytesIO(blob)) as t:
        t.extractall(tree, filter="data")
    out, log = HOME / "found.json", HOME / "paint.log"
    out.unlink(missing_ok=True)
    with open(log, "w") as f:
        r = subprocess.run([sys.executable, "-B", "-c", CHILD, skin, str(out)], cwd=tree, stdout=f, stderr=subprocess.STDOUT)
    if r.returncode:
        return {"error": (log.read_text(errors="replace").strip().splitlines() or ["(no output)"])[-1]}
    return list({(x["check"], x["text"]): x for x in json.loads(out.read_text())}.values())  # a side's twin once


def meets(flaw, finding):
    if finding["kind"] != flaw["kind"]:
        return False
    if flaw["where"] is None or finding["z"] is None:
        return True
    (a0, a1), (b0, b1) = sorted(flaw["where"]), sorted(finding["z"])
    return a0 - SLACK <= b1 and b0 <= a1 + SLACK


def ident(flaw):
    return f"{flaw['skin']}/{flaw['kind']}/{flaw['where']}"


def score():
    tests = load()
    flaws = tests["flaws"]
    paintable = [f for f in flaws if f.get("before")]
    said = len({key(f["said"]) for f in flaws}) + len(tests["other"])
    print(f"The record: {said} things the user said about cars; {len(flaws)} flaws on the car they were shown, "
          f"{len(paintable)} of them on a car that can be painted again as they saw it.")
    tree = HOME / "tree"
    shutil.rmtree(tree, ignore_errors=True)
    for d in ("tool", "car", "viewer"):
        shutil.copytree(paths.REPO / d, tree / d, copy_function=shutil.copy2, ignore=shutil.ignore_patterns("__pycache__"))
    cars, rows = {}, []
    with progress.job("Checking the tool against your record", done="Checked against your record"):
        progress.stage("Painting the cars you saw again", total=len({(f["before"], f.get("paint", f["skin"])) for f in paintable}))
        for f in paintable:
            car = (f["before"], f.get("paint", f["skin"]))
            if car not in cars:
                progress.detail(progress.title_of(car[1]))
                t0 = time.time()
                cars[car] = paint(f, tree)
                print(f"  painted {car[1]} as at {car[0]} in {time.time() - t0:.0f} s", flush=True)
                progress.tick()
            found = cars[car]
            hits = [] if isinstance(found, dict) else [x for x in found if meets(f, x)]
            rows.append((f, car, found, hits))
    caught = [f for f, _, found, hits in rows if hits]
    lines = []
    for f, car, found, hits in rows:
        v = version(car[0], car[1])
        seen = f"{car[1]}" + (f", version {v}" if v else "") + f" ({car[0][:7]})"
        if isinstance(found, dict):
            lines.append(f"  NOT PAINTED  {seen}: {found['error']}")
            continue
        by = ", ".join(sorted({CHECKS[h['check']] for h in hits}))
        lines.append(f"  {'caught' if hits else 'missed'} {f['kind']:<6} {seen}: {f['what']}" + (f" ({by})" if hits else ""))
        for h in hits:
            lines.append(f"      {h['text']}")
    others = [(car, x) for car, found in cars.items() if not isinstance(found, dict)
              for x in found if not any(meets(f, x) for f in paintable if (f["before"], f.get("paint", f["skin"])) == car)]
    last = HOME / "last.json"
    was = json.loads(last.read_text()) if last.exists() else None
    head = git("rev-parse", "--short=10", "HEAD").strip() + ("+changes" if git("status", "--porcelain", "--", "tool", "car").strip() else "")
    print(f"\nThis code ({head}) names {len(caught)} of the {len(paintable)} before the user did"
          + (f" (was {len(was['caught'])} of {was['of']}, {was['when']}, at {was['at']})." if was else "."))
    by_check = {c: sum(1 for _, _, _, hits in rows if any(h["check"] == c for h in hits)) for c in CHECKS}
    print("  by check: " + ", ".join(f"{CHECKS[c]} {n}" for c, n in by_check.items()))
    print("\n".join(lines))
    print(f"\n{len(others)} other warnings on those cars, which the user never raised:")
    for car, x in others:
        print(f"  {car[1]} ({car[0][:7]}): {x['text']}")
    rest = [f for f in flaws if not f.get("before")]
    whys = {}
    for f in rest:
        whys.setdefault(f["why"], []).append(f)
    print(f"\n{len(rest)} flaws can't be painted again:")
    for why, fs in whys.items():
        print(f"  {len(fs)}: {why} ({', '.join(sorted({x['kind'] for x in fs}))})")
    new = unsorted(tests)
    if new:
        print(f"\n{len(new)} things said in the records aren't in the test set yet: python -m tool.record new")
    paths.write(last, json.dumps({"at": head, "when": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                  "caught": [ident(f) for f in caught], "of": len(paintable)}))
    progress.result(f"The tool names {len(caught)} of the {len(paintable)} flaws you pointed out")


def main():
    if sys.argv[1:] == ["new"]:
        new = unsorted(load())
        for g in new:
            print(f"{g['skin']} (first in {g['commit']}): \"{g['said']}\"")
        print(f"{len(new)} not in {TESTS.relative_to(paths.REPO)}: each goes in its flaws (KINDS, with where, what "
              "and before or why) or its other" if new else "Everything said in the records is in the test set.")
        return
    bad = [f for f in load()["flaws"] if f["kind"] not in KINDS]
    if bad:
        sys.exit(f"unknown kinds in {TESTS.name}: {', '.join(sorted({f['kind'] for f in bad}))}")
    score()


if __name__ == "__main__":
    main()
