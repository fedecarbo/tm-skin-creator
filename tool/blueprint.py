"""The blueprints: the body drawn flat from the left, the right, above, the front and the rear at
a known scale (1 pixel = 1 mm), where every pixel knows the spot on the body it shows. Claude
draws on them the way a livery designer draws on a side view (2026-09-29, the user: "it paints
blindly ... wobbly lines"; the plan: draw on blueprints), and a curve drawn on a view lands on the
body point by point along the line of sight, exact by construction: no guessing between points,
no spline through the air. shapes.view_line, view_shape and view_point are the paint box's side.

    python -m tool.blueprint                 build car/blueprints/<view>.png for every view (+ .json)
    python -m tool.blueprint --view left     one view
    python -m tool.blueprint --pins left     the user's pins (tool/lines.py) in that view's mm
    python -m tool.blueprint --probe left "M 1850,330 C ..."   what a path lands on, every 25 mm: read it before painting

A view's coordinates are the car's own, in millimetres, along the two axes the view shows
(VIEWS): the left and right views (z, y): z forward from the car's origin, y up from the ground;
the top view (x, z): x to the car's left; the front and rear views (x, y). So a point is the same
numbers whichever view shows it, and the grid on the picture is labelled with them. On the
picture the left view has the nose to the left, the right view to the right, the top view the
nose up the page with the car's left on the page's left, the front view the car's left on the
page's right (as you'd see it), the rear view the car's left on the page's left.

The picture: the body (the Skin mesh only, less the wheels' faces and the blades, which are an
outline: the wheels, the wing and the inner car are left off, so the body shows whole), shaded
flat, the body turning away from the view (facing it under FACING: the top faces from the side,
the undersides' slopes, the flanks from above) tinted blue and hatched, because a line drawn
there from this view doesn't land: it's drawn from the view that faces it, its creases (edges where the surface turns more than
FOLD degrees) and panel edges drawn dark, a 100 mm grid, and the user's pins from the Lab's lines
room as numbered marks (hollow where the view doesn't see them). What every pixel shows is cached
in the work folder (blueprint_<view>.npz: the triangle and its weights), rebuilt when the mesh or
this file changes; the picture and its .json (the size, the origin, the pins) live in
car/blueprints/, committed, for Claude to read before drawing.

A path on a view is an SVG path in those mm (M, L, H, V, C, S, Q, T, Z; absolute or relative; no
arcs: use C), e.g. "M -1600,620 C -800,700 400,760 1400,720" for a sweep along the left side."""

import argparse
import json
import re
import sys

import numpy as np

from tool import fbx, paths, raster

SCALE = 1.0    # pixels per mm
MARGIN = 100   # mm round the body
FOLD = 35.0    # degrees: an edge where the surface turns more than this is drawn as a crease
FOLDER = paths.REPO / "car" / "blueprints"
AXIS = {"x": 0, "y": 1, "z": 2}
# toward: the unit vector from the car to the eye; h, v: the axis along the picture's width and
# height, and its sign on the page (+1: right or up)
VIEWS = {
    "left": {"toward": (1, 0, 0), "h": ("z", -1), "v": ("y", 1), "about": "the car's left side, nose to the left"},
    "right": {"toward": (-1, 0, 0), "h": ("z", 1), "v": ("y", 1), "about": "the car's right side, nose to the right"},
    "top": {"toward": (0, 1, 0), "h": ("x", -1), "v": ("z", 1), "about": "from above, nose up the page, the car's left on the left"},
    "front": {"toward": (0, 0, 1), "h": ("x", -1), "v": ("y", 1), "about": "from the front, the car's left on the right"},
    "rear": {"toward": (0, 0, -1), "h": ("x", 1), "v": ("y", 1), "about": "from behind, the car's left on the left"},
}


OFF_PARTS = ("wheel cover", "nose fin", "mirror mount", "wing pylon")  # parents or names left out of what a view lands on
FACING = 0.6  # how squarely the body must face a view for a line drawn on it to land there (about 53 degrees)


def _mesh():
    """The body's mesh, and which of its triangles a view mustn't land on: the wheels' faces and
    the blades (the nose fin, the mirror mounts, the wing's pylons). A line drawn across a wheel
    must not paint its face, and a line that starts under the nose must not paint the pylon
    behind it (the first proof did both). They're drawn as outlines on the picture."""
    from tool import parts
    m = fbx.meshes()["Skin_01"]
    T = m["tri_vertex"]
    p = parts.load()
    inst = p.tri_part[p.mesh_offset["Skin"]:p.mesh_offset["Skin"] + len(T)]
    off = np.array([x.get("parent") in OFF_PARTS or x["name"] in OFF_PARTS for x in p.instances])[inst]
    return m["positions"].astype(np.float64), T, m["tri_uv"].astype(np.float64), m["tri_normal"].astype(np.float64), off


class Blueprint:
    """One view: its frame (mm to pixels and back) and what every pixel shows."""

    def __init__(self, view):
        if view not in VIEWS:
            raise KeyError(f"no view called {view!r}: {', '.join(VIEWS)}")
        self.view = view
        spec = VIEWS[view]
        self.toward = np.asarray(spec["toward"], np.float64)
        self.h_axis, self.h_sign = AXIS[spec["h"][0]], spec["h"][1]
        self.v_axis, self.v_sign = AXIS[spec["v"][0]], spec["v"][1]
        self.axes = (spec["h"][0], spec["v"][0])
        P, T, UV, N, off = _mesh()
        self.P, self.T, self.UV, self.N, self.off = P, T, UV, N, off
        self.part = None  # each triangle's part name, on demand (part_of)
        h = P[:, self.h_axis] * 10 * self.h_sign
        v = P[:, self.v_axis] * 10 * self.v_sign
        self.W = int(np.ceil((h.max() - h.min() + 2 * MARGIN) * SCALE))
        self.H = int(np.ceil((v.max() - v.min() + 2 * MARGIN) * SCALE))
        self.ox = (MARGIN - h.min()) * SCALE  # pixel x of h = 0
        self.oy = (MARGIN + v.max()) * SCALE  # pixel y of v = 0
        self._hits = None
        self._depth = None

    # ---- the frame ----

    def to_pixel(self, h, v):
        """View mm -> pixel (x, y), floats; the pixel's centre is at (col + 0.5, row + 0.5)."""
        h, v = np.asarray(h, np.float64), np.asarray(v, np.float64)
        return self.ox + self.h_sign * h * SCALE, self.oy - self.v_sign * v * SCALE

    def to_view(self, pos):
        """Body cm (n, 3) -> (h mm, v mm, depth cm: smaller nearer the eye)."""
        pos = np.asarray(pos, np.float64)
        return pos[:, self.h_axis] * 10, pos[:, self.v_axis] * 10, -(pos @ self.toward)

    # ---- what every pixel shows ----

    def _cache(self):
        return paths.CACHE / f"blueprint_{self.view}_{SCALE:g}.npz"

    def hits(self):
        """(tri (H, W) int32 or -1, bary (H, W, 3) float32): the body triangle each pixel shows."""
        if self._hits is None:
            c = self._cache()
            if c.exists() and c.stat().st_mtime > max(fbx.CACHE.stat().st_mtime, paths.Path(__file__).stat().st_mtime):
                d = np.load(c)
                self._hits = (d["tri"], d["bary"].astype(np.float32))
            else:
                tri, bary = self._rasterise(~self.off)
                c.parent.mkdir(parents=True, exist_ok=True)
                np.savez_compressed(c, tri=tri, bary=bary.astype(np.float16))
                self._hits = (tri, bary)
        return self._hits

    def _rasterise(self, which):
        """The chosen triangles (a mask over the mesh's) rasterised into the view: (tri, bary), tri
        the mesh's own triangle ids."""
        ids = np.flatnonzero(which)
        corners = self.P[self.T[ids]]  # (n, 3, 3)
        px, py = self.to_pixel(corners[..., self.h_axis] * 10, corners[..., self.v_axis] * 10)
        depth = -(corners @ self.toward)
        tri, bary = raster.rasterise(np.stack([px, py], -1), self.W, self.H, depth=depth)
        return np.where(tri >= 0, ids[np.maximum(tri, 0)], -1).astype(np.int32), bary

    def depth(self):
        """(H, W) depth in cm of what each pixel shows (inf where nothing)."""
        if self._depth is None:
            tri, bary = self.hits()
            d = raster.interpolate(tri, bary, -(self.P[self.T] @ self.toward)[..., None])[..., 0]
            self._depth = np.where(tri >= 0, d, np.inf).astype(np.float32)
        return self._depth

    def _at(self, h, v):
        """The pixel under view mm points: (col, row, inside)."""
        px, py = self.to_pixel(h, v)
        col, row = np.floor(px).astype(int), np.floor(py).astype(int)
        inside = (col >= 0) & (col < self.W) & (row >= 0) & (row < self.H)
        return np.clip(col, 0, self.W - 1), np.clip(row, 0, self.H - 1), inside

    def hit(self, h, v):
        """The body under view mm points: (positions (n, 3) cm, normals (n, 3), ok (n,)): ok is
        False where the point is off the body."""
        tri, bary = self.hits()
        col, row, inside = self._at(h, v)
        t, b = tri[row, col], bary[row, col].astype(np.float64)
        ok = inside & (t >= 0)
        t = np.maximum(t, 0)
        pos = (self.P[self.T[t]] * b[:, :, None]).sum(1)
        nrm = (self.N[t] * b[:, :, None]).sum(1)
        nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-9)
        return pos, nrm, ok

    def depth_at(self, h, v):
        """The depth (cm) of what the view shows under view mm points; inf off the body."""
        col, row, inside = self._at(h, v)
        return np.where(inside, self.depth()[row, col], np.inf)

    def texel(self, h, v, size=4096):
        """The Skin texel (col, row) under view mm points (-1 where off the body)."""
        tri, bary = self.hits()
        col, row, inside = self._at(h, v)
        t, b = tri[row, col], bary[row, col].astype(np.float64)
        ok = inside & (t >= 0)
        uv = (self.UV[np.maximum(t, 0)] * b[:, :, None]).sum(1)
        tx = np.clip((uv[:, 0] % 1.0) * size, 0, size - 1).astype(int)
        ty = np.clip((1 - uv[:, 1] % 1.0) * size, 0, size - 1).astype(int)
        return np.where(ok, tx, -1), np.where(ok, ty, -1)

    # ---- the picture ----

    def creases(self):
        """The mesh's edges the eye sees as lines: where two triangles meet at more than FOLD
        degrees, and the edges with one triangle only (panel edges, openings). (n, 2, 3) cm."""
        T = self.T
        e = np.sort(np.stack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]], 1).reshape(-1, 2), axis=1)
        fn = np.cross(self.P[T[:, 1]] - self.P[T[:, 0]], self.P[T[:, 2]] - self.P[T[:, 0]])
        fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-9)
        face = np.repeat(np.arange(len(T)), 3)
        key = e[:, 0].astype(np.int64) * len(self.P) + e[:, 1]
        order = np.argsort(key, kind="stable")
        key, face, e = key[order], face[order], e[order]
        first = np.r_[True, key[1:] != key[:-1]]
        starts = np.flatnonzero(first)
        counts = np.diff(np.r_[starts, len(key)])
        one = starts[counts == 1]
        two = starts[counts == 2]
        cos = (fn[face[two]] * fn[face[two + 1]]).sum(1)
        fold = two[cos < np.cos(np.radians(FOLD))]
        keep = np.r_[one, fold]
        return self.P[e[keep]]

    def picture(self, pins=True):
        """The blueprint as a PIL image, and the pins drawn on it as {line: [(n, h, v, seen)]}."""
        from PIL import Image, ImageDraw, ImageFont
        tri, bary = self.hits()
        n = raster.interpolate(tri, bary, self.N)
        n /= np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-9)
        light = self.toward + np.array([0.25, 0.6, 0.15])
        light /= np.linalg.norm(light)
        shade = 0.55 + 0.45 * np.abs(n @ light)
        img = np.full((self.H, self.W, 3), 248, np.uint8)
        body = tri >= 0
        grey = np.clip(shade * 205, 0, 255).astype(np.uint8)
        img[body] = grey[body][:, None]
        # the body turning away from the view (under FACING): a line drawn there from this view
        # doesn't land; tinted and hatched so it reads as "not from here"
        away = body & ((n @ self.toward) < FACING)
        hatch = ((np.arange(self.H)[:, None] + np.arange(self.W)[None, :]) % 8) < 2
        img[away] = (img[away] * np.array([0.78, 0.86, 1.0])).astype(np.uint8)
        img[away & hatch] = (img[away & hatch] * 0.75).astype(np.uint8)
        im = Image.fromarray(img)
        d = ImageDraw.Draw(im)
        # the grid: every 100 mm faint, every 500 mm darker and labelled
        hn, vn = self.axes
        h0, h1 = sorted(((0 - self.ox) / SCALE * self.h_sign, (self.W - self.ox) / SCALE * self.h_sign))
        v0, v1 = sorted(((self.oy - 0) / SCALE * self.v_sign, (self.oy - self.H) / SCALE * self.v_sign))
        font = ImageFont.truetype(_font(), 22)
        small = ImageFont.truetype(_font(), 16)
        for h in np.arange(np.ceil(h0 / 100) * 100, h1, 100):
            x = self.to_pixel(h, 0)[0]
            major = h % 500 == 0
            d.line([(x, 0), (x, self.H)], fill=(150, 175, 215) if major else (205, 218, 238), width=1)
            if major:
                d.text((x + 3, self.H - 24), f"{hn} {h:.0f}", fill=(60, 80, 120), font=small)
        for v in np.arange(np.ceil(v0 / 100) * 100, v1, 100):
            y = self.to_pixel(0, v)[1]
            major = v % 500 == 0
            d.line([(0, y), (self.W, y)], fill=(150, 175, 215) if major else (205, 218, 238), width=1)
            if major:
                d.text((4, y - 20), f"{vn} {v:.0f}", fill=(60, 80, 120), font=small)
        # the body over the grid, then its creases where the view sees them
        im2 = Image.fromarray(img)
        im.paste(im2, mask=Image.fromarray((body * 255).astype(np.uint8)))
        d = ImageDraw.Draw(im)
        segs = self.creases()
        mid = segs.mean(1)
        hm, vm, dm = self.to_view(mid)
        seen = dm <= self.depth_at(hm, vm) + 0.6
        for (a, b), ok in zip(segs, seen):
            if not ok:
                continue
            ha, va, _ = self.to_view(a[None])
            hb, vb, _ = self.to_view(b[None])
            xa, ya = self.to_pixel(ha[0], va[0])
            xb, yb = self.to_pixel(hb[0], vb[0])
            d.line([(xa, ya), (xb, yb)], fill=(55, 58, 64), width=2)
        # the wheel covers and the blades, an outline only: landmarks, not surfaces to draw on
        wheels = self._rasterise(self.off)[0] >= 0
        edge = wheels & ~np.roll(wheels, 1, 0) | wheels & ~np.roll(wheels, 1, 1) | wheels & ~np.roll(wheels, -1, 0) | wheels & ~np.roll(wheels, -1, 1)
        ys, xs = np.nonzero(edge)
        d.point(list(zip(xs.tolist(), ys.tolist())), fill=(120, 120, 130))
        # the user's pins
        marks = {}
        if pins:
            from tool import lines
            for L in lines.load()["lines"]:
                marks[L["name"]] = []
                pts = np.asarray(L["points"], np.float64)
                if not len(pts):
                    continue
                for flip in ((1.0, 1.0, 1.0),) + (((-1.0, 1.0, 1.0),) if L["mirror"] else ()):
                    q = pts * np.array(flip)
                    h, v, dep = self.to_view(q)
                    ok = dep <= self.depth_at(h, v) + 1.0
                    for k, (hh, vv, o) in enumerate(zip(h, v, ok)):
                        x, y = self.to_pixel(hh, vv)
                        r = 9
                        d.ellipse([x - r, y - r, x + r, y + r], fill=(232, 60, 160) if o else None, outline=(232, 60, 160), width=2)
                        d.text((x + r + 2, y - 11), str(k + 1), fill=(160, 20, 100), font=small)
                        if flip[0] > 0:
                            marks[L["name"]].append((k + 1, round(float(hh), 1), round(float(vv), 1), bool(o)))
                    if flip[0] > 0 and ok.any():
                        k0 = int(np.flatnonzero(ok)[0])
                        x, y = self.to_pixel(h[k0], v[k0])
                        d.text((x + 14, y + 4), L["name"], fill=(160, 20, 100), font=font)
        d.text((10, 6), f"{self.view}: {VIEWS[self.view]['about']}; ({hn}, {vn}) in mm, 1 px = 1 mm. "
               "Blue hatching: the body turns away from this view (draw that from another). Outlines: wheels, fins.", fill=(0, 0, 0), font=font)
        return im, marks


    def part_of(self, tri_ids):
        """The part's name of each triangle id (-1: none)."""
        if self.part is None:
            from tool import parts
            p = parts.load()
            inst = p.tri_part[p.mesh_offset["Skin"]:p.mesh_offset["Skin"] + len(self.T)]
            self.part = np.array([x["name"] for x in p.instances])[inst]
        t = np.asarray(tri_ids)
        return np.where(t >= 0, self.part[np.maximum(t, 0)], "-")

    def probe(self, path, step=25.0):
        """What a path lands on, every `step` mm: rows of (h, v, part or "off", facing the view,
        x y z cm), for reading before painting."""
        tri, _ = self.hits()
        rows = []
        for sub in sample_path(path, step):
            pos, nrm, ok = self.hit(sub[:, 0], sub[:, 1])
            col, row, _ = self._at(sub[:, 0], sub[:, 1])
            part = self.part_of(np.where(ok, tri[row, col], -1))
            facing = nrm @ self.toward
            for k in range(len(sub)):
                rows.append((float(sub[k, 0]), float(sub[k, 1]), str(part[k]) if ok[k] else "off", float(facing[k]) if ok[k] else 0.0,
                             tuple(float(v) for v in pos[k]) if ok[k] else None))
        return rows


def _font():
    from tool import fonts
    return fonts.path("arial bold")


_loaded = {}


def load(view):
    if view not in _loaded:
        _loaded[view] = Blueprint(view)
    return _loaded[view]


# ---- SVG paths on a view ----

_TOKEN = re.compile(r"[MmLlHhVvCcSsQqTtZzAa]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")


def parse_path(d):
    """An SVG path -> list of subpaths, each a list of segments: ("L", p0, p1), ("Q", p0, c, p1),
    ("C", p0, c1, c2, p1); closed subpaths end with an L back to their start."""
    toks = _TOKEN.findall(d)
    i, cmd, cur, start, prev_c, prev_cmd = 0, None, None, None, None, None
    subs, seg = [], []

    def num():
        nonlocal i
        v = float(toks[i])
        i += 1
        return v

    def pt(rel):
        x, y = num(), num()
        return (cur[0] + x, cur[1] + y) if rel and cur else (x, y)

    while i < len(toks):
        if toks[i].isalpha():
            cmd = toks[i]
            i += 1
            if cmd in "Zz":
                if seg and cur != start:
                    seg.append(("L", cur, start))
                if seg:
                    subs.append(seg)
                seg, cur, prev_c, prev_cmd = [], start, None, "Z"
                continue
        if cmd is None:
            raise ValueError("a path must start with M")
        rel = cmd.islower()
        c = cmd.upper()
        if c == "A":
            raise ValueError("arcs (A) aren't supported: draw the curve with C")
        if c == "M":
            if seg:
                subs.append(seg)
                seg = []
            cur = start = pt(rel)
            prev_c, prev_cmd = None, "M"
            cmd = "l" if rel else "L"  # further pairs after M are lines
            continue
        if c == "L":
            p = pt(rel)
            seg.append(("L", cur, p))
        elif c == "H":
            x = num()
            p = (cur[0] + x if rel else x, cur[1])
            seg.append(("L", cur, p))
        elif c == "V":
            y = num()
            p = (cur[0], cur[1] + y if rel else y)
            seg.append(("L", cur, p))
        elif c == "C":
            c1, c2, p = pt(rel), pt(rel), pt(rel)
            seg.append(("C", cur, c1, c2, p))
            prev_c = c2
        elif c == "S":
            c1 = (2 * cur[0] - prev_c[0], 2 * cur[1] - prev_c[1]) if prev_cmd == "C" and prev_c else cur
            c2, p = pt(rel), pt(rel)
            seg.append(("C", cur, c1, c2, p))
            prev_c = c2
        elif c == "Q":
            cq, p = pt(rel), pt(rel)
            seg.append(("Q", cur, cq, p))
            prev_c = cq
        elif c == "T":
            cq = (2 * cur[0] - prev_c[0], 2 * cur[1] - prev_c[1]) if prev_cmd == "Q" and prev_c else cur
            p = pt(rel)
            seg.append(("Q", cur, cq, p))
            prev_c = cq
        prev_cmd = c
        cur = p
    if seg:
        subs.append(seg)
    return subs


def _bezier(seg, n):
    t = np.linspace(0, 1, n)[:, None]
    if seg[0] == "L":
        a, b = np.asarray(seg[1]), np.asarray(seg[2])
        return a + (b - a) * t
    if seg[0] == "Q":
        a, c, b = (np.asarray(p) for p in seg[1:])
        return (1 - t) ** 2 * a + 2 * (1 - t) * t * c + t ** 2 * b
    a, c1, c2, b = (np.asarray(p) for p in seg[1:])
    return (1 - t) ** 3 * a + 3 * (1 - t) ** 2 * t * c1 + 3 * (1 - t) * t ** 2 * c2 + t ** 3 * b


def sample_path(d, step=1.0):
    """The path's subpaths as points every `step` mm along them: a list of (n, 2) arrays."""
    out = []
    for sub in parse_path(d):
        pts = []
        for seg in sub:
            rough = _bezier(seg, 33)
            length = np.linalg.norm(np.diff(rough, axis=0), axis=1).sum()
            n = max(2, int(np.ceil(length / step)) + 1)
            dense = _bezier(seg, 4 * n)
            s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(dense, axis=0), axis=1))]
            want = np.linspace(0, s[-1], n)
            p = np.stack([np.interp(want, s, dense[:, k]) for k in range(2)], 1)
            pts.append(p if not pts else p[1:])
        if pts:
            out.append(np.concatenate(pts))
    return out


def build(view=None, quiet=False):
    """The pictures and their .json, into car/blueprints/."""
    FOLDER.mkdir(parents=True, exist_ok=True)
    meta = {}
    for name in ([view] if view else list(VIEWS)):
        bp = load(name)
        im, marks = bp.picture()
        im.save(FOLDER / f"{name}.png", optimize=True)
        meta[name] = {"about": VIEWS[name]["about"], "axes": bp.axes, "size": [bp.W, bp.H], "px_per_mm": SCALE,
                      "origin_px": [round(bp.ox, 1), round(bp.oy, 1)], "pins": marks}
        if not quiet:
            print(f"{name}: {bp.W} x {bp.H} px, ({bp.axes[0]}, {bp.axes[1]}) mm; pins: "
                  + (", ".join(f"{k} ({sum(1 for m in v if m[3])} seen of {len(v)})" for k, v in marks.items()) or "none"))
    old = json.loads((FOLDER / "blueprints.json").read_text()) if (FOLDER / "blueprints.json").exists() else {}
    old.update(meta)
    (FOLDER / "blueprints.json").write_text(json.dumps(old, indent=1))
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--view", choices=list(VIEWS))
    ap.add_argument("--pins", metavar="VIEW", choices=list(VIEWS), help="the user's pins in that view's mm")
    ap.add_argument("--probe", nargs=2, metavar=("VIEW", "PATH"), help="what an SVG path lands on, every 25 mm, before painting it")
    args = ap.parse_args()
    if args.probe:
        bp = load(args.probe[0])
        print(f"  {bp.axes[0]:>6}  {bp.axes[1]:>5}  {'lands on':16s} facing   x     y     z (cm)")
        for h, v, part, facing, pos in bp.probe(args.probe[1]):
            flag = "" if part == "off" else ("  <- turns away: won't land from this view" if facing < FACING else "")
            xyz = f"{pos[0]:6.1f} {pos[1]:5.1f} {pos[2]:6.1f}" if pos else ""
            print(f"  {h:6.0f}  {v:5.0f}  {part:16s} {facing:5.2f}  {xyz}{flag}")
        return
    if args.pins:
        from tool import lines
        bp = load(args.pins)
        for L in lines.load()["lines"]:
            pts = np.asarray(L["points"], np.float64)
            if not len(pts):
                continue
            h, v, dep = bp.to_view(pts)
            seen = dep <= bp.depth_at(h, v) + 1.0
            print(f"{L['name']} ({bp.axes[0]}, {bp.axes[1]} mm): " + "  ".join(f"{k + 1}: ({hh:.0f}, {vv:.0f}){'' if s else ' hidden'}" for k, (hh, vv, s) in enumerate(zip(h, v, seen))))
        return
    build(args.view)


if __name__ == "__main__":
    main()
