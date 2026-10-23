"""The ledger: every car's verdict kept side by side, so a flaw that comes back in one place, car after car, is known
as the tool's and queued for a session of its own (the user, 2026-10-22: "if it finds something that is happening in
various cars, something that has a root cause, then I guess it should be automatically just logged to queue a fix in
another session").

    python -m tool.ledger      each place a flaw was found on two cars or more: its cars, and its item when queued

`keep(name, verdict)` (tool/judge.py's save, tool/gate.py's despite) keeps the car's latest verdict in the work folder
(ledger.json): its blocks and warnings, each by its signature: its kind and check, the model's line a marking was read
against (its `ruler`), its place (`mid`) within NEAR cm, the car's two sides one. The takes of one car
(skins/<name>/take.json) are one car, and a car deleted keeps its last verdict here. A signature on CARS cars, or let go
on LET_GO, is the tool's, not the design's: written into the queue's own section (SECTION in IMPROVEMENTS.md), one
item K<n> for the flaws of a kind one stroke shows on the cars (their places, the day last seen, the cars, one finding
as it reads), and taken out when no car shows it any more. A verdict's findings on a queued signature carry `known` (K<n>): the judge says it, and the gate lets it
pass. An item deleted from the queue is done (fixed, or found not the tool's): only verdicts kept after count again.
Milliseconds a verdict. Standard library only, as tool/gate.py is.
"""

import json
import math
import re
import textwrap
import time

from tool import gate, paths

CARS = 3     # cars a flaw in one place is found on to be the tool's ...
LET_GO = 2   # ... or that let it go
NEAR = 3.0   # cm between two findings' places that are one place
LEVELS = ("block", "warn")  # a note names, never forbids
FILE = paths.WORK / "ledger.json"
QUEUE = paths.REPO / "IMPROVEMENTS.md"
SECTION = "## Found on several cars"
ITEM = re.compile(r"^- \*\*K(\d+):", re.M)
RULER = re.compile(r", [\d.]+ cm from the design's course|, mirrored to the right")
KEYS = ("kind", "check", "ruler", "mid")


def _sig(f):
    """A finding's signature: its kind, check and ruler (the lines it names, not how far the design's course lay from
    them), and its place on the car's left."""
    x, y, z = f["mid"]
    return {"kind": f["kind"], "check": f["check"], "ruler": RULER.sub("", f.get("ruler") or ""), "mid": [abs(x), y, z]}


def _same(a, b):
    return ((a["kind"], a["check"], a["ruler"]) == (b["kind"], b["check"], b["ruler"])
            and math.dist(a["mid"], b["mid"]) <= NEAR)


def _load():
    return gate._read(FILE) or {"cars": {}, "queued": [], "done": [], "next": 1}


def _section(text):
    """The queue's own section, from its heading to the next: its text and where it is (start, end; None, none)."""
    i = text.find(SECTION)
    if i < 0:
        return "", None
    j = text.find("\n## ", i + len(SECTION))
    j = j + 1 if j >= 0 else len(text)
    return text[i:j], (i, j)


def _split(section):
    """The section's words before its items, and its items, each whole: (head, {K: item})."""
    parts = re.split(r"(?m)^(?=- \*\*)", section)
    return parts[0], {int(m.group(1)): p for p in parts[1:] if (m := ITEM.match(p))}


def unkept(text):
    """A file's text without the items the ledger keeps (they come and go by themselves): the self-test's word count."""
    s, at = _section(text)
    return text[:at[0]] + _split(s)[0] + text[at[1]:] if at else text


def _groups(led):
    """Every signature on the cars' latest verdicts, the queued ones first: {sig, q, rows: (car, when, row, name), cars,
    let_go: the cars that let it go, pairs: (name, call) it was found on}. A row of a verdict kept before its signature
    was done doesn't count."""
    groups = [{"sig": q, "q": q, "rows": []} for q in led["queued"]]
    rows = [(c["of"], c["when"], r, n) for n, c in led["cars"].items() for r in c["rows"]
            if not any(d["when"] > c["when"] and _same(r, d) for d in led["done"])]
    for s in sorted(rows, key=lambda s: s[1]):
        g = next((g for g in groups if _same(s[2], g["sig"])), None)
        if g is None:
            groups.append(g := {"sig": s[2], "q": None, "rows": []})
        g["rows"].append(s)
    for g in groups:
        g["cars"] = sorted({s[0] for s in g["rows"]})
        g["let_go"] = sorted({s[0] for s in g["rows"] if s[2]["let_go"]})
        g["pairs"] = {(s[3], s[2]["op"]) for s in g["rows"]}
    return groups


def _at(mid):
    """A signature's place in words, either side when it isn't in the middle."""
    x, y, z = mid
    return f"({'±' if x >= 2 else ''}{x:.0f}, {y:.0f}, {z:.0f})"


def _item(qs):
    """One item: the signatures sharing a K, their places nose first, the finding last seen."""
    q = max(qs, key=lambda q: q["seen"])
    cars, let = (sorted({c for q_ in qs for c in q_[k]}) for k in ("cars", "let_go"))
    places = ", ".join(_at(q_["mid"]) for q_ in sorted(qs, key=lambda q_: -q_["mid"][2]))
    text = (f"- **K{q['k']}: {q['kind']}, on {len(cars)} car{'s' * (len(cars) > 1)}** ({q['seen']}, last seen; "
            f"{', '.join(cars)}" + (f", let go on {len(let)}" if let else "") + f"; at {places}): "
            f"{q['text'].replace('`', chr(39))}")
    return textwrap.fill(text, 120, subsequent_indent="  ", break_long_words=False, break_on_hyphens=False) + "\n"


def keep(name, verdict):
    """Keep the car's verdict, queue what's on enough cars (or out, what's on none), and mark the verdict's findings
    on a queued signature (`known`)."""
    led, now = _load(), time.strftime("%Y-%m-%dT%H:%M:%S")
    gone = gate.let_go(name, verdict)[0]
    take = gate._read(paths.SKINS / name / "take.json") or {}
    led["cars"][name] = {"when": now, "of": take.get("of") or name,
                         "rows": [{**_sig(f), "op": f.get("op"), "text": f["text"], "let_go": f["text"] in gone}
                                  for f in verdict["findings"] if f.get("level") in LEVELS and f.get("mid")]}
    text = QUEUE.read_text(encoding="utf-8")
    old, at = _section(text)
    head, items = _split(old)
    for q in [q for q in led["queued"] if q["k"] not in items]:  # deleted from the queue: done
        led["queued"].remove(q)
        led["done"].append({**{k: q[k] for k in KEYS}, "when": now})
    mine, queued, strokes = {q["k"] for q in led["queued"]}, [], {}  # strokes: K -> the (car, call) its flaws are on
    for g in _groups(led):
        q = g["q"]
        if q is None and (len(g["cars"]) >= CARS or len(g["let_go"]) >= LET_GO):
            q = {k: g["sig"][k] for k in KEYS}
            q["k"] = next((p["k"] for p in queued if (p["kind"], p["check"]) == (q["kind"], q["check"])
                           and strokes[p["k"]] & g["pairs"]), None)  # the same stroke's flaw of that kind: one item
            if q["k"] is None:
                q["k"] = led["next"] = max([led["next"], *(k + 1 for k in items)])  # never another's number
                led["next"] += 1
        if q is None or not g["cars"]:
            continue  # not on enough cars yet; or no car shows it any more
        strokes.setdefault(q["k"], set()).update(g["pairs"])
        last = g["rows"][-1]
        queued.append({**q, "cars": g["cars"], "let_go": g["let_go"], "seen": last[1][:10], "text": last[2]["text"]})
    led["queued"] = queued
    for f in verdict["findings"]:
        f.pop("known", None)
        q = next((q for q in queued if f.get("level") in LEVELS and f.get("mid") and _same(_sig(f), q)), None)
        if q:
            f["known"] = f"K{q['k']}"
    others = [p for k, p in items.items() if k not in mine]  # another computer's
    by = {}
    for q in queued:
        by.setdefault(q["k"], []).append(q)
    listed = sorted(others + [_item(qs) for qs in by.values()], key=lambda p: int(ITEM.match(p).group(1)))
    new = (head or SECTION).rstrip("\n") + "\n" + "".join(("\n" if i == 0 else "") + p.rstrip("\n") + "\n"
                                                         for i, p in enumerate(listed))
    if at is None and listed:
        paths.write(QUEUE, text.rstrip("\n") + "\n\n" + new)
    elif at is not None and new.rstrip("\n") != old.rstrip("\n"):
        paths.write(QUEUE, text[:at[0]] + new + ("\n" + text[at[1]:] if at[1] < len(text) else ""))
    paths.write(FILE, json.dumps(led, ensure_ascii=False))


def main():
    groups = [g for g in _groups(_load()) if g["q"] or len(g["cars"]) > 1]
    for g in groups:
        print(f"{'K' + str(g['q']['k']) if g['q'] else 'not queued'}: {g['sig']['kind']} at {_at(g['sig']['mid'])}, "
              f"on {', '.join(g['cars'])}" + (f", let go on {len(g['let_go'])}" if g["let_go"] else ""))
        print(f"  {g['rows'][-1][2]['text']}")
    if not groups:
        print("no flaw found in one place on two cars")


if __name__ == "__main__":
    main()
