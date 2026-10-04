"""The car's levels: lines the user draws from the side, in the Lab's levels room (viewer/lab-levels.js).
The user, 2026-10-04: "a tool I can define from the side how the line goes"; the car's line is its
curved top and bottom seen from the side, and the levels follow it, never a flat cut.

A level is a height along the car: a handful of points (z, y) in cm, one smooth curve through them
(a natural cubic spline, held level past the end points), and on the car the line runs wherever
the outer body is at that height, all round: along both sides, across the front of the sidepods,
round the nose tip and across the tail. Seen from the side, the line on the car is the curve
itself. The room draws the same curve (lab-levels.js's spline is this one), so what is dragged
there is what is painted.

The side's levels: the user draws two, the top (role "top") and the bottom (role "bottom"), and
`between` more are shared out between them, smooth because they are. The bottom's shape fades out
towards the top: the level s of the way down (s = k / (between + 1)) sits s times the typical gap
(the median along the bottom's stretch) below the top, plus s² times how much the gap at that length
differs from it. So the levels near the top run parallel to it, as the rear wing's seam does (the
user, 2026-10-04: "I do expect that the lines follow the same curvature"), and those near the
bottom follow the bottom (shared evenly, the bottom's climb at the tail tilted every level). The bottom
and the levels between run only between the bottom's first and last points: ahead of the sidepods
the body has no side below the top (the nose's own lower edge is the top there), and held level
they would run on along the floor's blade and round the front wing.

car/levels.json (committed, written by the room through the viewer's server, /api/levels):
    {"levels": [{"name": "top edge", "role": "top", "points": [[z, y], ...]}, ...], "between": 5}

    python -m tool.levels            paint every level on the clay car, for the viewer and the room (LOOK)
    python -m tool.levels --side     the side view the room draws on, into the work folder (also made
                                     by the first paint, and again when the mesh changes)

    levels.line("top edge", 0.8)     a zone (tool/shapes.py): the level's line, 0.8 cm wide on the surface
                                     ("between 1" is the highest of the levels between, and so on down)
    levels.above("top edge")         a zone: the body above it
"""

import argparse
import json
import time

import numpy as np

from tool import paths, progress

FILE = paths.REPO / "car" / "levels.json"
LOOK = "Look_Levels"  # the clay car with the levels on it, in the viewer's data (never a skin of the user's)
SIDE = 0.25  # cm per pixel of the side view
WHEELS = ("wheel cover disc", "wheel cover hub", "wheel cover ring")
# the outer body's parts a level isn't painted on: the struts under the nose and the inlets' insides
# (a level at their height ran along an inlet's roof)
OFF = ("wing pylon", "sidepod inlet")
# where to start, for the user to move: the top's edge as Claude found it (the middle of the roll from
# top to side, smoothed) and the bottom along the body's lower edge (where the side turns under), from
# the tail's end to the sidepods' front (2026-10-04)
START = {"levels": [{"name": "top edge", "role": "top",
                     "points": [[-158, 61.0], [-120, 60.6], [-80, 58.6], [-40, 57.0], [0, 57.6],
                                [40, 59.8], [90, 56.0], [140, 50.6], [180, 45.7], [210, 41.0]]},
                    {"name": "bottom edge", "role": "bottom",
                     "points": [[-162, 38], [-145, 29], [-128, 23], [-105, 19.5], [-60, 20.5], [-10, 22],
                                [40, 20.5], [82, 18.5]]}],
         "between": 5}
MOST = 12  # levels between, at most


def load():
    if FILE.exists():
        return json.loads(FILE.read_text())
    return json.loads(json.dumps(START))


def save(doc):
    """Check a document from the room and keep it."""
    out, roles = [], set()
    for L in doc.get("levels", []):
        name = str(L.get("name", "")).strip()[:40]
        pts = sorted(([round(float(z), 2), round(float(y), 2)] for z, y in L.get("points", [])), key=lambda p: p[0])
        if not name or len(pts) < 2:
            raise ValueError("a level needs a name and two points or more")
        if any(b[0] - a[0] < 0.5 for a, b in zip(pts, pts[1:])):
            raise ValueError(f"{name}: two points at the same place along the car")
        level = {"name": name, "points": pts}
        if L.get("role") in ("top", "bottom") and L["role"] not in roles:
            level = {"name": name, "role": L["role"], "points": pts}
            roles.add(L["role"])
        out.append(level)
    if len({L["name"].lower() for L in out}) != len(out):
        raise ValueError("two levels share a name")
    kept = {"levels": out, "between": min(max(int(doc.get("between", 0)), 0), MOST)}
    paths.write(FILE, json.dumps(kept, indent=1) + "\n")
    return kept


def spline(points):
    """The level's height along the car, Y(z), and its slope: a natural cubic spline through the points,
    held level past the ends (lab-levels.js draws the same)."""
    from scipy.interpolate import CubicSpline
    p = np.asarray(points, np.float64)
    if len(p) == 2:
        p = np.vstack([p[0], p.mean(0), p[1]])
    s = CubicSpline(p[:, 0], p[:, 1], bc_type="natural")
    z0, z1 = p[0, 0], p[-1, 0]

    def Y(z):
        return s(np.clip(z, z0, z1))

    def dY(z):
        z = np.asarray(z, np.float64)
        return np.where((z > z0) & (z < z1), s(np.clip(z, z0, z1), 1), 0.0)
    return Y, dY


def curves(doc=None):
    """Every line the levels make: (name, Y, dY, span), span the stretch (z0, z1) it runs along, or None
    all along the car. The levels drawn, then the levels between the top and the bottom, highest first."""
    doc = doc or load()
    out = []
    for L in doc["levels"]:
        Y, dY = spline(L["points"])
        span = (L["points"][0][0], L["points"][-1][0]) if L.get("role") == "bottom" else None
        out.append((L["name"], Y, dY, span))
    role = {L["role"]: L for L in doc["levels"] if L.get("role")}
    n = int(doc.get("between", 0))
    if "top" in role and "bottom" in role and n:
        (T, dT), (B, dB) = spline(role["top"]["points"]), spline(role["bottom"]["points"])
        span = (role["bottom"]["points"][0][0], role["bottom"]["points"][-1][0])
        zs = np.arange(span[0], span[1] + 1e-9, 1.0)
        gap = float(np.median(T(zs) - B(zs)))  # the typical gap between the top and the bottom
        for k in range(1, n + 1):
            s = k / (n + 1)  # how far down: 0 at the top, 1 at the bottom
            out.append((f"between {k}", lambda z, s=s: T(z) - s * gap - s * s * (T(z) - B(z) - gap),
                        lambda z, s=s: dT(z) - s * s * (dT(z) - dB(z)), span))
    return out


def _find(name):
    for c in curves():
        if c[0].lower() == name.lower():
            return c
    raise ValueError(f"no level called {name!r} in {FILE.name}: the levels room draws them")


def _above_cm(Y, dY):
    """(pos, nrm) -> how far above the level each point is, in cm along the surface."""
    def f(p, n):
        z = p[:, 2].astype(np.float64)
        h = p[:, 1] - Y(z)
        g = np.stack([np.zeros(len(h)), np.ones(len(h)), -dY(z)], 1)
        nn = n.astype(np.float64)
        gs = np.linalg.norm(g - (g * nn).sum(1, keepdims=True) * nn, axis=1)
        return h / np.maximum(gs, 0.05)
    return f


def line(name, width=0.8):
    """The level's line on the outer body, `width` cm wide on the surface."""
    from tool import shapes
    from tool.noise import smoothstep
    _, Y, dY, span = _find(name)
    f = _above_cm(Y, dY)
    z = shapes.Zone(lambda p, n: smoothstep(-0.1, 0.1, width / 2 - np.abs(f(p, n))).astype(np.float32))
    # the outer body (the flanks behind the wheels see little of the open air), and not its undersides;
    # the side tucks under along the sidepods, facing 15 to 40 degrees down from 34 cm to its foot, and
    # is still the side the room draws on: only what faces more than 50 degrees down is under the car
    z = z & shapes.outside(0.1) & shapes.Zone(lambda p, n: smoothstep(-0.85, -0.75, n[:, 1]).astype(np.float32))
    return z & shapes.band(*span) if span else z


def above(name):
    """The body above the level."""
    from tool import shapes
    from tool.noise import smoothstep
    f = _above_cm(*_find(name)[1:3])
    return shapes.Zone(lambda p, n: smoothstep(-0.05, 0.05, f(p, n)).astype(np.float32))


# ---- the side view the room draws on ----

def side_view():
    """The car seen square from its right side (the nose to the right), the wheels off, shaded like
    clay, one pixel every SIDE cm: written to the work folder (levels/side.png and side.json, the
    picture's place in cm), and again whenever the mesh changes."""
    from PIL import Image
    from tool import fbx, parts, raster, view
    out = view.DATA / "levels"
    stamp = out / "side.json"
    mesh_t = fbx.CACHE.stat().st_mtime if fbx.CACHE.exists() else 0
    if stamp.exists() and json.loads(stamp.read_text()).get("mesh") == mesh_t:
        return stamp
    P = parts.load()
    names = np.array([i["name"] for i in P.instances])
    parent = np.array([i.get("parent") or "" for i in P.instances])
    corners, shade_n, inner = [], [], []
    for mesh in ("Skin_01", "Details_01"):
        m = fbx.meshes()[mesh]
        tset = mesh.split("_")[0]
        off = P.mesh_offset[tset]
        part = P.tri_part[off:off + len(m["tri_vertex"])]
        keep = ~np.isin(names[part], WHEELS) & (parent[part] != "rims and brakes")
        corners.append(m["positions"][m["tri_vertex"]][keep])
        shade_n.append(m["tri_normal"][keep])
        inner.append(np.full(keep.sum(), tset == "Details"))
    C = np.concatenate(corners).astype(np.float64)
    N = np.concatenate(shade_n).astype(np.float64)
    inner = np.concatenate(inner)
    z0, z1, y0, y1 = -168.0, 220.0, -2.0, 92.0
    w, h = int((z1 - z0) / SIDE), int((y1 - y0) / SIDE)
    xy = np.stack([(C[..., 2] - z0) / SIDE, (y1 - C[..., 1]) / SIDE], -1)
    tri, bary = raster.rasterise(xy, w, h, depth=C[..., 0])  # seen from the right (-x): the nearest is the lowest x
    hit = tri >= 0
    n = (N[tri[hit]] * bary[hit][..., None]).sum(1)
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
    light = np.array([-0.75, 0.55, 0.35]); light /= np.linalg.norm(light)
    lit = 0.38 + 0.62 * np.clip(n @ light, 0, 1)
    base = np.where(inner[tri[hit]], 0.55, 0.92)
    img = np.zeros((h, w, 4), np.uint8)
    img[hit, :3] = (np.clip(base * lit, 0, 1) * 255).astype(np.uint8)[:, None]
    img[hit, 3] = 255
    out.mkdir(parents=True, exist_ok=True)
    Image.fromarray(img, "RGBA").save(out / "side.png", optimize=True)
    stamp.write_text(json.dumps({"z0": z0, "z1": z1, "y0": y0, "y1": y1, "px": SIDE, "w": w, "h": h, "mesh": mesh_t}))
    return stamp


def sections():
    """The body's outline every cm along the car (the car map's, the left half, its open surface), for
    the room's live line on the 3D car: levels/sections.json, [[z, [x, y, x, y, ...]], ...] in cm."""
    from tool import carmap, view
    out = view.DATA / "levels" / "sections.json"
    d = np.load(carmap.CACHE)
    if out.exists() and out.stat().st_mtime > carmap.CACHE.stat().st_mtime:
        return out
    Z, st, q = d["sec_Z"], d["sec_starts"], d["sec_q"]
    rows = []
    for k, z in enumerate(Z):
        p = q[st[k]:st[k + 1]][::4]  # a point every cm round the outline
        rows.append([round(float(z), 2), [round(float(v), 1) for v in p.ravel()]])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, separators=(",", ":")))
    return out


# ---- the levels on the clay car ----

def paint():
    """Every level as a line on the clay car (LOOK), for the viewer and the room: the levels drawn in
    black, the levels between in blue."""
    from tool import build, paintbox, view
    doc = load()
    with progress.job("Drawing your levels on the car"):
        side_view()
        sections()
        lines = curves(doc)
        progress.stage("Painting", total=len(lines))
        s = paintbox.Skin(LOOK)
        s.clay()
        body = sorted({i["name"] for i in s.parts.instances if i["mesh"] == "Skin"} - set(WHEELS) - set(OFF))
        drawn = {L["name"] for L in doc["levels"]}
        for name, *_ in lines:
            s.paint([f"{b}|part" for b in body], "matte", colour="#0a0a0a" if name in drawn else "#1d4ed8", zone=line(name))
            progress.tick()
        s.end_steps()
        progress.stage("Putting it on the car")
        build.export_to_viewer(s)
        (view.DATA / "levels").mkdir(parents=True, exist_ok=True)
        paths.write(view.DATA / "levels" / "painted.json", json.dumps({"stamp": time.time(), "levels": doc["levels"], "between": doc.get("between", 0)}))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--side", action="store_true", help="only the side view and the outlines the room draws on")
    args = ap.parse_args()
    if args.side:
        print(side_view())
        print(sections())
        return
    t = time.time()
    paint()
    doc = load()
    print(f"painted {', '.join(L['name'] for L in doc['levels'])} and {len(curves(doc)) - len(doc['levels'])} levels between"
          f" on {LOOK} in {time.time() - t:.0f} s")


if __name__ == "__main__":
    main()
