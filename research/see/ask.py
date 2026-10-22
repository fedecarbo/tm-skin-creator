"""ask: the car answers questions in words, from its own mesh. A throwaway sample (2026-10-22), not the tool.

    PY ask.py line "side skirt crease 2"       a line: its ends, which is the nose end, how its course runs, what it meets
    PY ask.py line "rear flank roll 2"         a rounded edge: each of its lines by tilt, the same way
    PY ask.py panel "sidepod top panel 1"      a panel: its parts, extent, facing, the lines round it, where it's flat
    PY ask.py part "sidepod inlet"             a part: extent, its piece and gap, panels, lines, what paint on it covers
    PY ask.py at 39 19 70                      a point: the part and panel under it, lines near, facing, where along the car
    PY ask.py paint wheels                     what a where-word covers, per texture set
    PY ask.py flat "rear flank"                where words and badges read flat on a part
    PY ask.py stretch "body shell roll 2" nose 30   the exact call for a 30 cm stretch from the nose end (or tail)
    PY ask.py find skirt                       every name with a word in it
    PY ask.py list                             every line 40 cm and up, every panel 50 cm2 and up, with their ends
"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

from tool import meshlines, paintbox, paths, surface

HERE = Path(__file__).resolve().parent
NOSE_Z, TAIL_Z = 215.0, -162.0
PIECES = json.load(open(paths.REPO / "car" / "pieces.json"))["pieces"]
PARTS = json.load(open(paths.REPO / "car" / "parts.json"))["parts"]
KEEP_CLEAR = {"number panel": "the game letters the player's number on it", "engine cover panel": "the game letters the player's name on it",
              "nose fin": "its plate is the game's"}


def P(p):
    return f"({p[0]:.0f}, {p[1]:.0f}, {p[2]:.0f})"


def names():
    return meshlines.named()


def kind_of(name):
    return name.rsplit(" ", 2)[-2]


def height_words(y):
    if y < 26:
        return "low, near the ground"
    if y < 56:
        return "at mid height, on the flank"
    return "high, on the top"


def facing_words(n):
    n = np.asarray(n, float)
    n = n / max(np.linalg.norm(n), 1e-9)
    words = []
    for v, pos, neg in ((n[1], "up", "down"), (n[0], "out to the car's left", "out to the car's right"), (n[2], "forward", "back")):
        if v > 0.35:
            words.append(pos)
        elif v < -0.35:
            words.append(neg)
    return " and ".join(words) or "sideways"


def along_words(z):
    f = (NOSE_Z - z) / (NOSE_Z - TAIL_Z)
    return f"{f * 100:.0f} % of the way from the nose to the tail"


def side_words(x):
    if x > 1:
        return "the car's left side"
    if x < -1:
        return "the car's right side"
    return "the middle"


def extent_words(pts):
    pts = np.asarray(pts)
    lo, hi = pts.min(0), pts.max(0)
    return (f"z {hi[2]:.0f} (front) to {lo[2]:.0f} (back), y {lo[1]:.0f} to {hi[1]:.0f} up, x {lo[0]:.0f} to {hi[0]:.0f} "
            f"({side_words((lo[0] + hi[0]) / 2)})")


def corners(pts, least=20.0, chord=8.0):
    """Where a line turns by `least` degrees or more, over chords of `chord` cm: [(point, degrees)]."""
    pts = np.asarray(pts, float)
    s = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    if s[-1] < 3 * chord:
        return []
    out, k = [], np.arange(0, s[-1], chord / 2)
    q = np.stack([np.interp(k, s, pts[:, i]) for i in range(3)], 1)
    for i in range(2, len(q) - 2):
        a, b = q[i] - q[i - 2], q[i + 2] - q[i]
        c = np.degrees(np.arccos(np.clip(a @ b / max(np.linalg.norm(a) * np.linalg.norm(b), 1e-9), -1, 1)))
        if c >= least and (not out or np.linalg.norm(q[i] - out[-1][0]) > chord):
            out.append((q[i], c))
        elif c >= least and c > out[-1][1]:
            out[-1] = (q[i], c)
    return out


def _lines_pool():
    """Every named line (a roll's lines each), [(name, record)]."""
    pool = []
    for n, rec in names().items():
        if kind_of(n) == "panel":
            continue
        for L in (rec if isinstance(rec, list) else [rec]):
            pool.append((n, L))
    return pool


def meets(L, name, point, reach=2.5):
    found = []
    for n, K in _lines_pool():
        if n == name or K is L:
            continue
        d = float(np.linalg.norm(K["pts"] - point, axis=1).min())
        if d <= reach:
            found.append((d, n))
    found.sort()
    return [n for _, n in found[:4]]


def panel_names():
    return {rec["label"]: n for n, rec in names().items() if kind_of(n) == "panel"}


def panels_beside(L, reach=4.0):
    e, lab = meshlines._edges("Skin"), meshlines._panels("Skin")
    C = e["P"][e["T"]].mean(1)
    tree = cKDTree(L["pts"])
    d, _ = tree.query(C)
    close = lab[d <= reach]
    by = panel_names()
    counts = {}
    for p in close:
        if p in by:
            counts[by[p]] = counts.get(by[p], 0) + 1
    return [n for n, _ in sorted(counts.items(), key=lambda kv: -kv[1])[:3]]


def line_words(name, L, roll=False):
    pts = L["pts"]
    kind = meshlines.WORDS[L["kind"]]
    tilt = f", tilted {L['tilt']:.0f} degrees from facing up" if "tilt" in L else ""
    walls = f" (a groove: {L['walls']} lines close together, this the longest)" if L.get("walls", 1) > 1 else ""
    out = [f"{name}{' (one of its lines)' if roll else ''}: {kind}{tilt}, {L['length']:.0f} cm, along the "
           f"{', '.join(L['parts'][:3])}{walls}."]
    if L["closed"]:
        out.append(f"  A closed loop, no ends: it runs round {extent_words(pts)}.")
        out.append(f"  Its course, meshlines.line({name!r}{', tilt=' + str(round(L['tilt'])) if 'tilt' in L else ''}), starts at "
                   f"{P(pts[0])} and runs round; c.between(a, b) takes the way the loop runs from a to b.")
    else:
        p0, p1 = pts[0], pts[-1]
        dz = p0[2] - p1[2]
        if abs(dz) >= 5:
            nose_first = dz > 0
            nose, tail = (p0, p1) if nose_first else (p1, p0)
            out.append(f"  Nose end {P(nose)} (z {nose[2]:.0f}), tail end {P(tail)} (z {tail[2]:.0f}): it runs {extent_words(pts)}; "
                       f"{height_words(pts[:, 1].mean())}.")
            call = f"meshlines.line({name!r}{', tilt=' + str(round(L['tilt'])) if 'tilt' in L else ''})"
            if nose_first:
                out.append(f"  ITS COURSE RUNS NOSE FIRST: {call} has c.start at the nose end and c.end at the tail end.")
            else:
                out.append(f"  ITS COURSE RUNS TAIL FIRST: {call} has c.start at the TAIL end (z {p0[2]:.0f}) and c.end at the nose end "
                           f"(z {p1[2]:.0f}). For a nose-first course take {call}.reversed().")
            out.append(f"  A stretch by lengths along the car needs no direction: c.between({max(p0[2], p1[2]) - 10:.0f}, "
                       f"{max(p0[2], p1[2]) - 40:.0f}) is the 30 cm nearest the nose end whichever way it runs.")
        else:
            a, b = (p0, p1) if p0[0] >= p1[0] else (p1, p0)
            out.append(f"  It runs across the car, not along it: from {P(p0)} to {P(p1)}, {extent_words(pts)}; "
                       f"{height_words(pts[:, 1].mean())}. Its course starts at {P(p0)}.")
        for p, deg in corners(pts):
            out.append(f"  Turns {deg:.0f} degrees at {P(p)}.")
        m0, m1 = meets(L, name, p0), meets(L, name, p1)
        if m0:
            out.append(f"  At its course's start {P(p0)} it meets: {', '.join(m0)}.")
        if m1:
            out.append(f"  At its course's end {P(p1)} it meets: {', '.join(m1)}.")
    beside = panels_beside(L)
    if beside:
        out.append(f"  Panels along it: {', '.join(beside)}.")
    return out


def ask_line(name):
    key = " ".join(name.strip().lower().split())
    rec = meshlines._named(name, "line", "Skin")
    if isinstance(rec, list):
        if len(rec) == 1:
            return line_words(key, rec[0])
        out = [f"{key}: a rounded edge, {len(rec)} lines side by side across it, each facing its own way. "
               f"meshlines.line({key!r}, tilt=<degrees>) picks one:"]
        for L in sorted(rec, key=lambda x: x["tilt"]):
            out += line_words(key, L, roll=True)
        return out
    return line_words(key, rec)


def rooms_cache():
    f = HERE / "rooms.json"
    if f.exists():
        return json.load(open(f))
    from tool import marks
    body = sorted({p["name"] for p in PARTS if p["mesh"] == "Skin" and p["group"] == "body"})
    r = marks.rooms(body)
    data = {k: [(float(a), [float(v) for v in c], [float(v) for v in f_]) for a, c, f_ in v] for k, v in r.items()}
    json.dump(data, open(f, "w"))
    return data


def flat_words(part):
    rooms = rooms_cache().get(part)
    if not rooms:
        return [f"  Nowhere on the {part} is flat enough (12 cm across or more) for words to read flat."]
    return [f"  Flat room on the {part} (words and badges read flat, no stretch to speak of): " +
            "; ".join(f"{a:.0f} cm across, centred {P(c)}, facing {facing_words(n)}" for a, c, n in rooms) + "."]


def ask_panel(name):
    key = " ".join(name.strip().lower().split())
    rec = meshlines._named(name, "panel", "Skin")
    e, lab = meshlines._edges("Skin"), meshlines._panels("Skin")
    tris = np.flatnonzero(lab == rec["label"])
    X = e["P"][e["T"][tris]]
    V = X.reshape(-1, 3)
    nrm = np.cross(X[:, 1] - X[:, 0], X[:, 2] - X[:, 0])
    out = [f"{key}: a panel of {rec['area']:.0f} cm2 on the {', '.join(rec['parts'][:3])}, bounded by the model's crisp lines and edges; "
           f"a point on it: {P(rec['at'])}. meshlines.panel({key!r}) fills it right up to its lines (both=True: its mirror image too)."]
    out.append(f"  Extent: {extent_words(V)}; it faces {facing_words(nrm.sum(0))}.")
    tree = cKDTree(V)
    edges = []
    for n, L in _lines_pool():
        d, _ = tree.query(L["pts"])
        share = (d <= 1.0).mean()
        if share >= 0.3 and len(L["pts"]) > 3:
            edges.append((share * L["length"], n, L["length"]))
    edges.sort(reverse=True)
    if edges:
        out.append("  Its edges are the lines: " + ", ".join(f"{n} ({l:.0f} cm)" for _, n, l in edges[:6]) + ".")
    out += flat_words(rec["parts"][0])
    return out


def ask_part(name):
    key = name.strip().lower()
    mine = [p for p in PARTS if p["name"] == key]
    if not mine:
        import difflib
        close = difflib.get_close_matches(key, sorted({p["name"] for p in PARTS}), n=5, cutoff=0.5)
        raise SystemExit(f"no part called {name!r}; did you mean {', '.join(map(repr, close))}? (car/parts.json has every name)")
    S = surface.load("Skin" if mine[0]["mesh"] == "Skin" else "Details")
    left = [p for p in mine if p["side"] != "right"] or mine
    ids = [p["id"] for p in left]
    tris = np.isin(S.part, ids)
    out = [f"{key}: {len(mine)} part{'s' if len(mine) > 1 else ''} ({', '.join(f'{p['side']} {p['end']}'.strip() or 'centre' for p in mine)}), "
           f"in the {mine[0]['mesh']} texture set ({'the body' if mine[0]['mesh'] == 'Skin' else 'the inner car' if mine[0]['mesh'] == 'Details' else mine[0]['mesh']}), "
           f"group '{mine[0]['group']}', {sum(p['area_cm2'] for p in mine):.0f} cm2 in all."]
    if tris.any():
        V = S.V[S.F[tris]].reshape(-1, 3)
        out.append(f"  Extent{' (the left one; the right mirrors it)' if len(mine) > len(left) else ''}: {extent_words(V)}; "
                   f"mostly facing {facing_words((S.fn[tris] * 1).sum(0))}.")
    for pc in PIECES:
        if key in pc["parts"]:
            others = [p for p in pc["parts"] if p != key]
            if pc["gap_cm"] > 1.0:
                out.append(f"  A piece of its own{' with ' + ', '.join(others) if others else ''}: a gap of {pc['gap_cm']:.1f} cm to the "
                           f"{pc['nearest']}. A line or a band along it STOPS at the gap, as a wrap would; a graphic laid whole stays on it.")
            elif len(pc["parts"]) <= 3:
                out.append(f"  A piece sewn on{' with the ' + ', '.join(others) if others else ''}, {pc['gap_cm']:.2f} cm from the "
                           f"{pc['nearest']} (1 cm or less): a line may run on across the join.")
            else:
                out.append(f"  Part of the main skin with {len(others)} other parts ({', '.join(others[:6])}{'...' if len(others) > 6 else ''}): "
                           f"a band or a line runs on across the seams between them.")
            break
    if key in KEEP_CLEAR:
        out.append(f"  KEEP CLEAR: {KEEP_CLEAR[key]}; nothing on it or within 3 cm (the judge blocks it).")
    shared = max(p["shared"] for p in mine)
    if shared >= 0.05:
        out.append(f"  {shared * 100:.0f} % of its texels share their paint with another part: a colour on it lands there too (show names it).")
    pn = [n for n, r in names().items() if kind_of(n) == "panel" and key in r["parts"][:1] and r["area"] >= 50]
    if pn:
        out.append(f"  Its panels: {', '.join(pn[:6])}.")
    ln = [n for n, r in names().items() if kind_of(n) != "panel" and (r[0] if isinstance(r, list) else r)["parts"][0] == key
          and max(x["length"] for x in (r if isinstance(r, list) else [r])) >= 40]
    if ln:
        out.append(f"  Its lines (40 cm and up): {', '.join(ln[:10])}.")
    out += flat_words(key)
    out += ["  " + l.strip() for l in ask_paint(key)]
    return out


def ask_at(p):
    p = np.asarray(p, float)
    t, on = meshlines._closest(p)  # the model's triangle whose skin is nearest the point itself, not the nearest centre
    e = meshlines._edges("Skin")
    name = meshlines._parts_of("Skin")[t]
    d = float(np.linalg.norm(p - on))
    a, b, c = e["P"][e["T"][t]]
    n = np.cross(b - a, c - a)
    found, under = meshlines.near(p)
    out = [f"{P(p)}: on {side_words(p[0])}, {along_words(p[2])}, {height_words(p[1])}."]
    if d > 6:
        out.append(f"  It's {d:.0f} cm off the body: the nearest skin is the {name} at {P(on)}.")
    else:
        out.append(f"  The part under it: the {name}, facing {facing_words(n)}" + (f" ({d:.1f} cm from the skin)" if d > 0.5 else "") + ".")
    out.append(f"  The panel under it: {under or 'none'}.")
    if found:
        out.append("  Within 5 cm: " + "; ".join(f"{n} ({what}) {dd:.1f} cm away" for dd, n, what in found[:5]) + ".")
    else:
        out.append("  No model line within 5 cm: open panel.")
    return out


def ask_paint(where):
    sk = paintbox.Skin("TSC_Ask", size=1024)
    ids = sk._ids(where)
    sets = {"Skin": "the body set", "Details": "the inner car set", "Wheels": "the tyres set", "Glass": "the glass set"}
    out = [f"paint on {where!r} covers:"]
    for tset, v in ids.items():
        names_ = sorted({sk.parts.instances[i]["name"] for i in v})
        out.append(f"  {sets.get(tset, tset)}: {', '.join(names_)}.")
    if not ids:
        out.append("  nothing.")
    return out


def ask_stretch(name, end, cm):
    rec = meshlines._named(name, "line", "Skin")
    tilt = None
    if isinstance(rec, list):
        rec = max(rec, key=lambda x: x["length"])
        tilt = round(rec["tilt"])
    c = meshlines.line(name, tilt=tilt)
    call = f"meshlines.line({name!r}{', tilt=' + str(tilt) if tilt else ''})"
    nose_first = c.start[2] >= c.end[2]
    want_nose = end.lower().startswith("n")
    if want_nose != nose_first:
        c, call = c.reversed(), call + ".reversed()"
    st = c.between(c.start, c.at(s=float(cm)))
    return [f"{cm} cm of {name} from the {'nose' if want_nose else 'tail'} end:",
            f"  c = {call}        # c.start is now the {'nose' if want_nose else 'tail'} end, {P(c.start)}",
            f"  stretch = c.between(c.start, c.at(s={cm}))",
            f"  It runs from {P(st.start)} to {P(st.end)}, {st.length:.0f} cm; or by lengths along the car: "
            f"c.between({st.start[2]:.0f}, {st.end[2]:.0f}), which needs no direction."]


def ask_find(word):
    w = word.lower()
    out = [n for n in names() if w in n]
    parts_ = sorted({p["name"] for p in PARTS if w in p["name"]})
    return ([f"names of lines and panels with {word!r}: " + (", ".join(out[:40]) or "none")] +
            [f"parts with {word!r}: " + (", ".join(parts_) or "none")])


def ask_list():
    out = ["The body's lines, 40 cm and up (meshlines.line(name)), the longest first; each one's nose end and tail end, and which end "
           "its course starts at:"]
    for n, rec in names().items():
        k = kind_of(n)
        if k == "panel":
            continue
        Ls = rec if isinstance(rec, list) else [rec]
        L = max(Ls, key=lambda x: x["length"])
        if L["length"] < 40:
            continue
        p0, p1 = L["pts"][0], L["pts"][-1]
        if L["closed"]:
            ends = f"a loop round z {L['pts'][:, 2].max():.0f} to {L['pts'][:, 2].min():.0f}"
        elif abs(p0[2] - p1[2]) >= 5:
            ends = (f"nose end {P(p0 if p0[2] > p1[2] else p1)}, tail end {P(p1 if p0[2] > p1[2] else p0)}; course runs "
                    f"{'NOSE' if p0[2] > p1[2] else 'TAIL'} first")
        else:
            ends = f"across the car, {P(p0)} to {P(p1)}"
        tilt = f" ({len(Ls)} lines by tilt)" if isinstance(rec, list) else ""
        out.append(f"  {n:<28} {meshlines.WORDS[L['kind']]:<28} {L['length']:4.0f} cm  {', '.join(L['parts'][:2]):<28} {ends}{tilt}")
    out.append("Its panels, 50 cm2 and up (meshlines.panel(name)):")
    for n, rec in names().items():
        if kind_of(n) == "panel" and rec["area"] >= 50:
            out.append(f"  {n:<28} {rec['area']:6.0f} cm2  at {P(rec['at'])}  {', '.join(rec['parts'][:3])}")
    out.append("Parts (car/parts.json): " + ", ".join(sorted({p['name'] for p in PARTS})))
    return out


def main(argv):
    if not argv:
        print(__doc__)
        return
    what, rest = argv[0], argv[1:]
    try:
        if what == "line" or what == "roll":
            lines = ask_line(" ".join(rest))
        elif what == "panel":
            lines = ask_panel(" ".join(rest))
        elif what == "part":
            lines = ask_part(" ".join(rest))
        elif what == "at":
            lines = ask_at([float(v) for v in rest[:3]])
        elif what == "paint":
            lines = ask_paint(" ".join(rest))
        elif what == "flat":
            lines = flat_words(" ".join(rest))
        elif what == "stretch":
            lines = ask_stretch(rest[0], rest[1], rest[2])
        elif what == "find":
            lines = ask_find(" ".join(rest))
        elif what == "list":
            lines = ask_list()
        else:
            print(__doc__)
            return
    except ValueError as e:
        print(str(e))
        return
    print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv[1:])
