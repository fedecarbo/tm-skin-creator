"""The close looks: along every line and over every decal of a painted car, square to the face the eye sees, PX_CM
pixels a centimetre (a 1 cm gap is 20 pixels, a whole-car view gives it 6), each taken twice by the viewer: shaded,
for Claude's eye, and as a texel pass (which texel of the body's map each pixel shows: viewer.uvs), from which every
graphic's flat mask is read and measured. Both sides seen alike: a graphic on both is looked at on the left, and on
the right from each camera's mirror image, the two side by side on the sheets.

    python -m tool.close <name>      after tool.skin show: the looks, their sheets, what they measure, what changed

It reads what show kept (tool/judge.py's save): build/<name>/graphics.json (each marking's stations along the line it
follows, each fill's edge, each mark, words and picture; each call's step and each step's hash), owner.npy (the call
that covered each texel last) and verdict.json (the spots the judge's eye names); a design changed since is refused.
The looks (`plan`):
  along a line   one every ALONG cm, centred on the line, the camera square to the surface there;
  over a mark    one, framed to it whole (fewer than PX_CM pixels a cm when it's too big for the frame);
  at a spot      one at each spot the judge's eye names that no look shows already.
What the masks measure, as findings added to the verdict (check "close", `measure` and `changes`):
  gap      a line's paint drawn under half its width over GAP_RUN cm or more where the judge read its texels whole:
           what the texels hold and what the viewer draws differ;
  hidden   a line's stretch of HIDDEN_RUN cm, or HIDDEN_SHARE of a mark, that another part hides even seen square;
  sides    a graphic's mask on the right against its mirror image on the left (of words and pictures, their areas),
           SIDES cm² apart or more;
  changed  a pixel diff against the run before at the same cameras (pixelmatch's colour distance, DIFF), each changed
           pixel set against the steps the edit changed (judge.step_hashes): OUTSIDE cm² or more changed on a paint
           whose step's code didn't change is outside the edit.
Out: build/<name>_close_<k>.png, the sheets (each look: its number, the side, the graphic, where along the car; a red
ring at each finding); build/<name>_close_changed.png, before beside after for each look changed outside the edit;
build/<name>/close/ (each look's picture, looks.json, the owner map it was read with: the next run's before).
"""

import argparse
import base64
import io
import json
import re
import shutil
import time

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.spatial import ConvexHull

from tool import bake, fonts, judge, paths, progress, server, view

PX_CM = 20.0       # pixels a centimetre on the face looked at
TILE = 480         # each look's picture, square: 24 cm across at PX_CM
FOV = 32.0         # degrees: the viewer's lens (viewer.js's FOV)
ALONG = 18.0       # cm between looks along a line (each frames 24: they overlap)
GAP_RUN = 1.0      # cm
HIDDEN_RUN = 2.0   # cm
HIDDEN_SHARE = 0.1  # of a mark
SEEN = 3           # pixels of a station's stretch of the body for it to be seen
END = 4            # stations at each end of a line's paint (or of a dash): the judge measures where it ends
EDGE_ON = 0.2      # a station facing the camera less than this is seen edge on: hidden from no one
FACING = 0.5       # a station facing the camera this much or more (60 degrees) is seen whole: its width measured
GROUND = 5.0       # cm: the camera's least height off the floor
SIDES = 1.0        # cm²
BITE_AREA = 0.25   # cm² out of a shape's outline (its convex hull) in one piece, three times any other: a bite
SPECK = 2          # pixels eroded off a difference before it counts (a mask's edge aliases by one)
DIFF = 0.1         # pixelmatch's threshold: the share of the largest colour distance
OUTSIDE = 0.5      # cm²
SPOT_APART = 10.0  # cm: a spot this near a look's middle is in it
TWIN = 6.0         # cm: a mark whose middle is this near another's mirror image is its twin on the other side
COLS, ROWS = 4, 4  # looks on a sheet
FLIP = np.array([-1.0, 1.0, 1.0])
LEVELS = {"gap": "block", "cut": "block", "hidden": "note", "sides": "warn", "changed": "warn"}


# ---- where to look ----

def _dist(px_cm):
    """The camera's distance (m) that shows the face looked at px_cm pixels a centimetre."""
    return TILE / (px_cm * 2 * np.tan(np.radians(FOV / 2)) * 100)


def _dir(n):
    """The camera's direction from its target: the face's, never straight up or down (its up is the car's)."""
    d = np.asarray(n, np.float64)
    d = d / max(np.linalg.norm(d), 1e-9)
    if abs(d[1]) > 0.97:
        h = d[[0, 2]] if np.linalg.norm(d[[0, 2]]) > 1e-6 else np.array([0.0, 1.0])
        h = h / np.linalg.norm(h) * np.sqrt(1 - 0.97 ** 2)
        d = np.array([h[0], np.sign(d[1]) * 0.97, h[1]])
    return d


def _view(target, d, px_cm, lift):
    """A camera square to the face (d), standing at least GROUND cm off the floor: a face turned to the ground is seen
    as someone crouching beside the car sees it."""
    t = np.asarray(target, np.float64) + [0, lift, 0]
    dist = _dist(px_cm)
    low = (GROUND - t[1]) / (100 * dist)
    if d[1] < low:
        h = d[[0, 2]] if np.linalg.norm(d[[0, 2]]) > 1e-6 else np.array([np.sign(t[0]) or 1.0, 0.0])
        h = h / np.linalg.norm(h) * np.sqrt(max(1 - low ** 2, 0.0))
        d = np.array([h[0], low, h[1]])
    return {"dir": d.round(4).tolist(), "dist": round(float(dist), 4), "target": (t / 100).round(4).tolist()}


def _mirror_view(v):
    return {"dir": (np.asarray(v["dir"]) * FLIP).tolist(), "dist": v["dist"],
            "target": (np.asarray(v["target"]) * FLIP).tolist()}


def _project(v, pts, lift):
    """Points (cm, the model's) to a look's pixels (x, y), and their depth along the camera (m)."""
    T, d = np.asarray(v["target"]), np.asarray(v["dir"])
    C = T + d / np.linalg.norm(d) * v["dist"]
    f = -d / np.linalg.norm(d)
    r = np.cross(f, [0.0, 1.0, 0.0])
    r /= np.linalg.norm(r)
    u = np.cross(r, f)
    p = (np.asarray(pts, np.float64).reshape(-1, 3) + [0, lift, 0]) / 100 - C
    z = p @ f
    k = np.tan(np.radians(FOV / 2)) * np.maximum(z, 1e-6)
    return np.stack([((p @ r) / k + 1) / 2 * TILE, (1 - (p @ u) / k) / 2 * TILE], -1), z


def _twin(g, h):
    """Whether graphic h is graphic g's mirror image on the other side (station for station, or a mark's middle)."""
    if g["kind"] != h["kind"] or g["what"] != h["what"]:
        return False
    if g["kind"] == "mark":
        return np.linalg.norm(np.asarray(g["at"]) * FLIP - h["at"]) < TWIN
    a, b = np.asarray(g["pos"]), np.asarray(h["pos"])
    return len(a) == len(b) and float(np.abs(a * FLIP - b).max()) < 1.0


def plan(gfx, verdict, lift):
    """The looks: [{n, g (the graphic's index), side, view, px_cm, stations (a line's, first and end), twin (the
    look on the other side it mirrors), label}]."""
    G = gfx["graphics"]
    twin_of, paired = {}, set()  # a graphic on the right -> its mirror image on the left
    for i, g in enumerate(G):
        for j in range(i + 1, len(G)):
            if i not in paired and j not in paired and _twin(g, G[j]):
                x = np.asarray(g["at"] if g["kind"] == "mark" else g["pos"])[..., 0].mean()
                left, right = (i, j) if x >= 0 else (j, i)
                twin_of[right] = left
                paired |= {i, j}
    first = [i for i in range(len(G)) if i not in twin_of]
    looks = []

    def add(i, v, px, stations=None, twin=None):
        g = G[i]
        pts = np.asarray(g["pos"])[stations[0]:stations[1]] if stations else np.asarray([g["at"]])
        where, z, side = judge._where(pts)
        looks.append({"n": len(looks) + 1, "g": i, "side": side, "view": v, "px_cm": px, "stations": stations,
                      "twin": twin, "where": where, "z": z, "label": g["what"]})

    for i in first:
        g = G[i]
        mates = [j for j, k in twin_of.items() if k == i]
        if g["kind"] == "mark":
            px = min(PX_CM, (TILE / 2 - 12) / (g["reach"] * 1.1 + 1.0))
            v = _view(g["at"], _dir(g["facing"]), px, lift)
            add(i, v, px)
            for j in mates:
                add(j, _mirror_view(v), px, twin=len(looks))
            continue
        pos, fac = np.asarray(g["pos"]), np.asarray(g["facing"])
        n = len(pos)
        k = max(1, int(round(ALONG / judge.STATION)))
        cuts = np.linspace(0, n, max(1, int(np.ceil(n / k))) + 1).round().astype(int)
        for a, b in zip(cuts[:-1], cuts[1:]):
            v = _view(pos[(a + b) // 2], _dir(fac[a:b].sum(0)), PX_CM, lift)
            add(i, v, PX_CM, (int(a), int(b)))
            for j in mates:
                add(j, _mirror_view(v), PX_CM, (int(a), int(b)), twin=len(looks))
    for f in sorted((f for f in verdict["findings"] if f.get("at")), key=lambda f: f["side"] != "left"):
        at = np.asarray(f["at"], np.float64)
        if any(min(np.linalg.norm(np.asarray(L["view"]["target"]) * 100 - [0, lift, 0] - p) for p in (at, at * FLIP))
               < SPOT_APART for L in looks):
            continue
        where, z, side = judge._where(at)
        looks.append({"n": len(looks) + 1, "g": None, "side": side, "view": _view(at, _dir(f["nrm"]), PX_CM, lift),
                      "px_cm": PX_CM, "stations": None, "twin": None, "where": where, "z": z,
                      "label": f"what the eye names: {f['text']}"})
    return looks


# ---- taking them ----

def take(name, looks, folder):
    """Each look shaded (folder/<n>.png) and its texel pass (look["texels"]: the flat index of the texel of the
    4096² map each pixel shows, -2 another part of the car, -1 nothing)."""
    from playwright.sync_api import sync_playwright
    httpd = server.start(0)
    try:
        with sync_playwright() as p:
            browser = paths.launch(p)
            page = browser.new_page(viewport={"width": TILE, "height": TILE})
            page.on("pageerror", lambda e: print(f"page error: {e}"))
            page.goto(f"http://127.0.0.1:{httpd.server_address[1]}/?skin={name}&snap=1")
            page.wait_for_function("window.viewer && (window.viewer.ready || window.viewer.error)", timeout=180_000)
            if page.evaluate("window.viewer.error"):
                raise RuntimeError(page.evaluate("window.viewer.error"))
            progress.stage("Looking close up", total=len(looks))
            for L in looks:
                page.evaluate("(v) => viewer.show(v, false, [])", L["view"])
                Image.open(io.BytesIO(page.screenshot())).convert("RGB").save(folder / f"{L['n']}.png")
                px = np.frombuffer(base64.b64decode(page.evaluate("viewer.uvs()")), np.uint8).reshape(TILE, TILE, 4)[::-1]
                px = px.astype(np.int32)
                col, row = px[..., 0] + 256 * (px[..., 2] & 15), px[..., 1] + 256 * (px[..., 2] >> 4)
                L["texels"] = np.where(px[..., 3] == 255, row * 4096 + col, np.where(px[..., 3] == 128, -2, -1))
                progress.tick()
            browser.close()
    finally:
        httpd.shutdown()


# ---- what the masks measure ----

class _Map:
    """The body's map, read through a look's texel pass: whose paint each pixel shows, and where on the car it is."""

    def __init__(self, owner):
        self.owner = owner.reshape(-1)
        h, w = owner.shape
        b = bake.bake("Skin", w, h)
        self.pos, self.tri, self.w = b["position"].reshape(-1, 3), b["tri"].reshape(-1), w

    def texels(self, L):
        """The flat index of the texel each pixel of a look shows (-1: none; -2: another part of the car)."""
        t = L["texels"]
        if self.w != 4096:  # a map painted at another size
            t = np.where(t >= 0, (t // 4096 * self.w // 4096) * self.w + t % 4096 * self.w // 4096, t)
        return np.where((t >= 0) & (self.tri[np.maximum(t, 0)] >= 0), t, np.minimum(t, -1))

    def mask(self, L, op):
        t = self.texels(L)
        return (t >= 0) & (self.owner[np.maximum(t, 0)] == op)


def _say(found, L, g, kind, pts, text):
    where, z, side = judge._where(pts)
    found.append({"check": "close", "kind": kind, "z": z, "side": side, "step": g["step"] if g else None,
                  "text": f"{text}, {where} (look {L['n']})", "look": L["n"], "rings": pts})


def _said(verdict, z, side):
    """Whether the judge already said a flaw there, of the line or of a paint over it."""
    return any(f["check"] != "close" and f["kind"] in ("gap", "short", "line", "cut", "over", "sits") and f.get("z")
               and f["z"][0] + judge.MERGE >= z[1] and z[0] + judge.MERGE >= f["z"][1] and f["side"] in (side, None)
               for f in verdict["findings"])


def _line(M, L, g, lift, verdict, found):
    """A line's stations in its look: its paint's width as drawn, where it's drawn under half, where it's hidden."""
    a, b = L["stations"]
    pos, fac = np.asarray(g["pos"], np.float64), np.asarray(g["facing"], np.float64)
    T = np.gradient(pos, axis=0) if len(pos) > 1 else np.array([[0.0, 0.0, 1.0]])
    T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-9)
    A = np.cross(fac, T)
    A /= np.maximum(np.linalg.norm(A, axis=1, keepdims=True), 1e-9)
    t = M.texels(L)
    on = t >= 0
    P = M.pos[t[on]].astype(np.float64)
    own = M.owner[t[on]] == g["op"]
    reach = max(abs(g["lo"]), abs(g["hi"])) + judge.TOL if g["kind"] == "line" else judge.TOL
    W = g["hi"] - g["lo"] if g["kind"] == "line" else 0.0
    box = (np.abs(P - pos[a:b].mean(0)) <= np.abs(pos[a:b] - pos[a:b].mean(0)).max(0) + reach + 1.0).all(1)
    P, own = P[box], own[box]
    xy, _ = _project(L["view"], pos[a:b], lift)
    d = np.asarray(L["view"]["dir"])
    width, seen, hidden = np.zeros(b - a), np.zeros(b - a, bool), np.zeros(b - a, bool)
    one_sided = g["kind"] == "line" and g["lo"] * g["hi"] >= 0
    lo, hi = (0.0, W) if one_sided else (g.get("lo", 0.0), g.get("hi", 0.0))
    body = np.zeros(b - a)  # how much of its designed width the body shows, whatever paint is on it

    def spread(x):
        x = np.sort(x)
        return x[int(round(0.97 * (len(x) - 1)))] - x[int(0.03 * (len(x) - 1))] if len(x) >= SEEN else 0.0

    for k, s in enumerate(range(a, b)):
        v = P - pos[s]
        al = v @ T[s]
        r = np.sqrt(np.maximum((v * v).sum(1) - al * al, 0))  # how far from the line, round any edge it's on
        near = (np.abs(al) <= judge.STATION / 2) & (r <= reach)
        x, y = xy[k]
        inside = 4 <= x < TILE - 4 and 4 <= y < TILE - 4
        seen[k] = near.sum() >= SEEN
        hidden[k] = inside and not seen[k] and fac[s] @ d >= EDGE_ON
        across = r if one_sided else r * np.sign(v @ A[s])  # a centred strip's two faces either side of its middle
        width[k] = spread(across[near & own])
        body[k] = spread(across[near & (across >= lo - 0.3) & (across <= hi + 0.3)])
    for c0, c1 in judge._runs(hidden):
        if (c1 - c0) * judge.STATION >= HIDDEN_RUN:
            _say(found, L, g, "hidden", pos[a + c0:a + c1], f"{g['what']}: hidden by another part for "
                 f"{(c1 - c0) * judge.STATION:.1f} cm, even seen from where its face looks")
    if g["kind"] != "line":
        return
    expected = ndimage.binary_erosion(np.asarray(g["expected"]), iterations=END)  # the stations at its ends straddle them
    gap = expected[a:b] & (fac[a:b] @ d >= FACING) & (body >= judge.NARROW * W) & (width < 0.5 * W)
    for c0, c1 in judge._runs(gap):
        if (c1 - c0) * judge.STATION < GAP_RUN:
            continue
        _, z, side = judge._where(pos[a + c0:a + c1])
        if not _said(verdict, z, side):
            _say(found, L, g, "gap", pos[a + c0:a + c1], f"{g['what']}: seen close up, {np.median(width[c0:c1]):.1f} of "
                 f"its {W:.1f} cm wide for {(c1 - c0) * judge.STATION:.1f} cm (another paint, or none, in its place)")


def _mark(M, L, g, lift, found):
    """A mark's places in its look: the share another part hides, seen square to it; a shape's bite, what the eye
    sees chipped out of its outline (its convex hull, the body there showing another paint)."""
    pts, nrm = np.asarray(g["pts"], np.float64), np.asarray(g["nrm"], np.float64)
    keep = nrm @ np.asarray(L["view"]["dir"]) >= EDGE_ON
    if keep.sum() < 10:
        return
    xy, _ = _project(L["view"], pts[keep], lift)
    i = np.clip(xy.astype(int), 0, TILE - 1)
    t = M.texels(L)[i[:, 1], i[:, 0]]
    shown = (t >= 0) & (np.linalg.norm(M.pos[np.maximum(t, 0)] - pts[keep], axis=1) <= 1.0)
    share = 1 - shown.mean()
    if share >= HIDDEN_SHARE:
        _say(found, L, g, "hidden", pts[keep][~shown], f"{g['what']}: {share:.0%} of it hidden by another part, even seen "
             f"from where it faces")
    if g["shape"] != "shape":
        return
    m = M.mask(L, g["op"])
    lab, n = ndimage.label(m)
    if not n:
        return
    c = np.clip(_project(L["view"], [g["at"]], lift)[0][0].astype(int), 0, TILE - 1)
    k = lab[c[1], c[0]] or int(np.argmax(ndimage.sum(m, lab, range(1, n + 1)))) + 1  # the mark: the piece under its middle
    one = ndimage.binary_fill_holes(lab == k)  # a ring's hole is its own
    ys, xs = np.nonzero(one)
    if len(ys) < 50:
        return
    hull = ConvexHull(np.c_[xs, ys]).equations
    gy, gx = np.mgrid[:TILE, :TILE]
    inside = (np.tensordot(hull[:, :2], np.stack([gx, gy]), 1) + hull[:, 2, None, None] <= 0.5).all(0)
    t = M.texels(L)
    missing = ndimage.binary_opening(inside & ~one & (t >= 0), iterations=SPECK)  # the edge's aliasing goes
    parts, n = ndimage.label(missing)
    if not n:
        return
    sizes = np.sort(ndimage.sum(missing, parts, range(1, n + 1)))[::-1]
    area = sizes[0] / L["px_cm"] ** 2
    if area >= BITE_AREA and (n == 1 or sizes[0] >= 3 * sizes[1]):  # one bite, not a star's points
        ys, xs = np.nonzero(parts == int(np.argmax(ndimage.sum(missing, parts, range(1, n + 1)))) + 1)
        _say(found, L, g, "cut", M.pos[t[ys, xs]][:: max(1, len(ys) // 20)], f"{g['what']}: chipped, seen close up: "
             f"{area:.1f} cm² bitten out of its outline")


def _sides(M, G, looks, found):
    """Each look on the right against its mirror image on the left: a shape's or a line's mask, words' and pictures'
    areas."""
    by_n = {L["n"]: L for L in looks}
    for R in looks:
        if not R["twin"]:
            continue
        Lf = by_n[R["twin"]]
        g, h = G[Lf["g"]], G[R["g"]]
        a, b = M.mask(Lf, g["op"]), M.mask(R, h["op"])[:, ::-1]
        if g["kind"] == "mark" and g["shape"] != "shape":
            apart = abs(int(a.sum()) - int(b.sum())) / R["px_cm"] ** 2
            if apart >= SIDES and apart >= 0.1 * max(a.sum(), b.sum()) / R["px_cm"] ** 2:
                _say(found, R, h, "sides", [h["at"]], f"{h['what']}: {apart:.1f} cm² more of it on the "
                     f"{'right' if b.sum() > a.sum() else 'left'} than on the other side (looks {Lf['n']} and {R['n']})")
            continue
        diff = ndimage.binary_erosion(a ^ b, iterations=SPECK)
        apart = diff.sum() / R["px_cm"] ** 2
        if apart < SIDES:
            continue
        ys, xs = np.nonzero(diff)
        t = M.texels(R)[ys, TILE - 1 - xs]  # where on the right the difference is
        pts = M.pos[t[t >= 0]] if (t >= 0).any() else np.asarray([np.asarray(R["view"]["target"]) * 100])
        _say(found, R, h, "sides", pts[:: max(1, len(pts) // 50)], f"{h['what']}: the right side's differs from the left's "
             f"mirror image by {apart:.1f} cm² (looks {Lf['n']} and {R['n']})")


def measure(M, gfx, looks, verdict, lift):
    found = []
    G = gfx["graphics"]
    for L in looks:
        if L["g"] is None:
            continue
        g = G[L["g"]]
        if g["kind"] == "mark":
            _mark(M, L, g, lift, found)
        else:
            _line(M, L, g, lift, verdict, found)
    _sides(M, G, looks, found)
    return found


# ---- what changed since the run before ----

def _yiq(rgb):
    r, g, b = (rgb[..., k].astype(np.float32) for k in range(3))
    return np.stack([0.29889531 * r + 0.58662247 * g + 0.11448223 * b,
                     0.59597799 * r - 0.27417610 * g - 0.32180189 * b,
                     0.21147017 * r - 0.52261711 * g + 0.31114694 * b], -1)


def again(looks, before):
    """The run before's cameras that this run's looks don't stand at (a graphic moved or went): taken again, for the
    diff alone."""
    if not (before / "looks.json").exists():
        return []
    now = {json.dumps(L["view"]) for L in looks}
    return [{"n": f"{o['n']}b", "g": None, "side": o["side"], "view": o["view"], "px_cm": o["px_cm"], "stations": None,
             "twin": None, "where": o["where"], "z": o["z"], "label": o["label"]}
            for o in json.loads((before / "looks.json").read_text())["looks"] if json.dumps(o["view"]) not in now]


def changes(M, gfx, looks, folder, before, found):
    """Each of the run before's looks against this run's at the same camera (taken again where none stands there):
    the changed pixels (pixelmatch's YIQ distance over DIFF of its largest, specks gone), on the paint of an edited
    step (its code's hash changed) or outside the edit. Returns [(look, before's picture, outside mask)] for the
    compare sheet, and what it says in a line."""
    old = json.loads((before / "looks.json").read_text())
    old_owner = np.load(before / "owner.npy").reshape(-1)
    if len(old_owner) != len(M.owner):
        return [], "the run before was at another size: nothing compared"
    steps0, steps1 = old["steps"], gfx["steps"]
    edited = {s for s in set(steps0) | set(steps1) if steps0.get(s) != steps1.get(s)}
    ops0, ops1 = old["ops"], gfx["ops"]
    meant0, meant1 = (np.array([o in edited for o in ops] + [False]) for ops in (ops0, ops1))

    def paint(paints, ops, o):
        return f"{paints[o]} ({ops[o]})" if 0 <= o < len(ops) else "the stock paint"

    now = {json.dumps(L["view"]): L for L in looks}
    inside, shown, moves = [], [], {}
    for o in old["looks"]:
        L = now.get(json.dumps(o["view"]))
        if L is None or not (before / f"{o['n']}.png").exists():
            continue
        a = np.asarray(Image.open(before / f"{o['n']}.png").convert("RGB"))
        b = np.asarray(Image.open(folder / f"{L['n']}.png").convert("RGB"))
        d = _yiq(a) - _yiq(b)
        delta = 0.5053 * d[..., 0] ** 2 + 0.299 * d[..., 1] ** 2 + 0.1957 * d[..., 2] ** 2
        moved = ndimage.binary_opening(delta > 35215 * DIFF ** 2, iterations=1)
        if not moved.any():
            continue
        t = M.texels(L)
        o0, o1 = old_owner[np.maximum(t, 0)], M.owner[np.maximum(t, 0)]  # -1, the stock, reads each list's last: False
        halo = ndimage.binary_dilation((o0 != o1) & (t >= 0), iterations=3) & (o0 == o1)  # the viewer blends an edge
        out = ndimage.binary_opening(moved & (t >= 0) & ~(meant0[o0] | meant1[o1]) & ~halo, iterations=1)  # into the next
        if out.sum() / L["px_cm"] ** 2 < OUTSIDE:
            inside.append(o["n"])
            continue
        shown.append((L, Image.fromarray(a), out))
        pairs, which, count = np.unique(np.stack([o0[out], o1[out]], 1), axis=0, return_inverse=True, return_counts=True)
        for j, (p0, p1) in enumerate(pairs):  # what showed there before, what shows now: said once, its largest look
            area = count[j] / L["px_cm"] ** 2
            if area >= OUTSIDE and area > moves.get((p0, p1, L["side"]), (0,))[0]:
                pts = M.pos[t[out][which.ravel() == j]]
                moves[(p0, p1, L["side"])] = (area, L, pts[:: max(1, len(pts) // 50)])
    for (p0, p1, _), (area, L, pts) in moves.items():
        _say(found, L, {"step": ops1[p1] if 0 <= p1 < len(ops1) else None}, "changed", pts,
             f"outside this edit, {area:.1f} cm² shows {paint(gfx['paints'], ops1, p1)} where "
             f"{paint(old['paints'], ops0, p0)} showed before")
    words = (f"{len(old['looks'])} looks before, each taken again; edited: {', '.join(sorted(edited)) or 'no step'}; "
             f"changed only as the edit meant: {len(inside)}; outside it: {len(shown)}")
    return shown, words


# ---- the sheets ----

def _short(label):
    """A graphic's name for a tile: its step and what it is (\"Lines: a band 3 cm wide\")."""
    m = re.match(r".*\((?P<step>[^)]*)\): (?P<what>.*)", label)
    if not m:
        return label
    return f"{m['step']}: {re.split(r' (?:on the|along|beside|between|of the|near) ', m['what'])[0]}"


def _ring(d, x, y, r=14):
    d.ellipse((x - r, y - r, x + r, y + r), outline=(230, 20, 30), width=3)


def sheets(name, looks, folder, found, lift):
    """The looks on sheets of COLS x ROWS, a look on the right beside its twin on the left; a red ring at each
    finding."""
    for old in paths.BUILD.glob(f"{name}_close_*.png"):
        if old.stem[len(name) + 7:].isdigit():
            old.unlink()
    order, placed = [], set()
    for L in looks:
        if L["n"] in placed or L["twin"]:
            continue
        order.append(L)
        placed.add(L["n"])
        for R in looks:
            if R["twin"] == L["n"]:
                order.append(R)
                placed.add(R["n"])
    font = fonts.font("arial bold", 15)
    rings = {}
    for f in found:
        rings.setdefault(f["look"], []).append(f["rings"])
    per = COLS * ROWS
    out = []
    for s in range(0, len(order), per):
        part = order[s:s + per]
        rows = (len(part) + COLS - 1) // COLS
        sheet = Image.new("RGB", (COLS * TILE, rows * TILE), (24, 24, 26))
        for k, L in enumerate(part):
            tile = Image.open(folder / f"{L['n']}.png").convert("RGB")
            d = ImageDraw.Draw(tile)
            for pts in rings.get(L["n"], []):
                xy, z = _project(L["view"], pts, lift)
                for x, y in xy[(z > 0)][:: max(1, len(xy) // 6)]:
                    _ring(d, x, y)
            label = f"{L['n']} {L['side'] or ''}  {_short(L['label'])}"
            d.text((8, 6), label[:60], fill=(255, 255, 255), font=font, stroke_width=3, stroke_fill=(0, 0, 0))
            d.text((8, 26), L["where"][:70], fill=(255, 255, 255), font=font, stroke_width=3, stroke_fill=(0, 0, 0))
            sheet.paste(tile, ((k % COLS) * TILE, (k // COLS) * TILE))
        path = paths.BUILD / f"{name}_close_{len(out) + 1}.png"
        sheet.save(path)
        out.append((path, part))
    return out


def compare_sheet(name, shown, folder):
    path = paths.BUILD / f"{name}_close_changed.png"
    path.unlink(missing_ok=True)
    if not shown:
        return None
    band = 30
    out = Image.new("RGB", (2 * TILE, len(shown) * (TILE + band)), (24, 24, 26))
    font = fonts.font("arial bold", 16)
    for k, (L, before, moved) in enumerate(shown):
        y = k * (TILE + band)
        ImageDraw.Draw(out).text((8, y + 6), f"look {L['n']}: before, and after (outside the edit outlined)",
                                 fill=(235, 235, 235), font=font)
        a = np.asarray(Image.open(folder / f"{L['n']}.png").convert("RGB")).copy()
        a[ndimage.binary_dilation(moved, iterations=3) & ~ndimage.binary_dilation(moved, iterations=1)] = (232, 255, 71)
        out.paste(before, (0, y + band))
        out.paste(Image.fromarray(a), (TILE, y + band))
    out.save(path)
    return path


# ---- the run ----

def run(name):
    build = paths.BUILD / name
    if not (build / "graphics.json").exists():
        raise SystemExit(f"{name} has no graphics kept: tool.skin show {name} first")
    gfx = json.loads((build / "graphics.json").read_text())
    if gfx["design"] != judge.design_hash(name):
        raise SystemExit(f"{name}'s design changed since its last show: tool.skin show {name} first")
    verdict = json.loads((build / "verdict.json").read_text())
    lift = json.loads((view.DATA / "car.json").read_text())["lift_cm"]
    t0 = time.time()
    looks = plan(gfx, verdict, lift)
    before, folder = build / "close", build / "close_new"  # the run before stays until this one is done
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir(parents=True)
    shutil.copyfile(build / "owner.npy", folder / "owner.npy")
    once = again(looks, before)
    with progress.job(f"Looking close up at {progress.title_of(name)}", skin=name, done="Looked close up"):
        take(name, looks + once, folder)
        M = _Map(np.load(folder / "owner.npy"))
        found = measure(M, gfx, looks, verdict, lift)
        shown, said = changes(M, gfx, looks + once, folder, before, found) if (before / "looks.json").exists() else ([], "")
        made = sheets(name, looks, folder, found, lift)
        changed = compare_sheet(name, shown, folder)
    for L in looks:
        L.pop("texels", None)
    paths.write(folder / "looks.json", json.dumps({"design": gfx["design"], "steps": gfx["steps"], "ops": gfx["ops"],
                                                   "paints": gfx["paints"], "looks": looks}))
    shutil.rmtree(before, ignore_errors=True)
    folder.rename(before)
    for f in found:
        f.pop("rings")
        f["level"] = LEVELS[f["kind"]]
    rank = {"block": 0, "warn": 1, "note": 2}
    verdict["findings"] = sorted([f for f in verdict["findings"] if f["check"] != "close"] + found,
                                 key=lambda f: (rank[f["level"]], -(f["z"][0] if f["z"] else -1e9), f["text"]))
    verdict["close"] = {"design": gfx["design"], "looks": len(looks), "seconds": round(time.time() - t0, 1)}
    judge.save(name, verdict)
    print(f"{len(looks)} close looks in {verdict['close']['seconds']} s")
    for path, part in made:
        print(f"  {path}: {', '.join(dict.fromkeys(L['label'] for L in part))}")
    if said:
        print(said + (f"\n  {changed}" if changed else ""))
    for f in found:
        print(f"  {f['level'].upper() if f['level'] == 'block' else f['level']}: {f['kind']}: {f['text']}")
    if not found:
        print("the close looks find nothing to name")
    return verdict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    run(ap.parse_args().name)


if __name__ == "__main__":
    main()
