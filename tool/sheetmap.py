"""The body sheet as a design AI reads it: car/sheet.svg, car/sheet.png, car/sheet.json.

    python -m tool.carmap --sheet     writes the three (and car/sheet_body.png, the sheet shaded)

The sheet (tool/surface.py) in millimetres, 1 SVG unit = 1 mm, x from the nose's tip at the left
to the tail at the right, y down from the top centreline: the pieces' outlines, the areas (top,
sides, under) as filled regions, the map's lines (the shoulder, the lower edge, the real folds,
the openings, the joins), the darts (seams), a 10 cm grid, and the stations (where z = 150, 100 ...
runs on the sheet, with a tick on the top centreline). sheet.json has every one of them as
polylines in mm, each piece's bounds and distortion, and each area's, so a designer knows where a
big graphic sits cleanly. Colours as car/map/areas.jpg: the top white, the sides blue, under grey;
the shoulder green, the lower edge magenta, folds black, openings red, joins blue, seams orange.
"""

import json

import numpy as np
from PIL import Image, ImageDraw
from scipy.spatial import cKDTree

from tool import carmap, fonts, paths, surface

SVG, PNG, BODY_PNG, JSON = (paths.REPO / "car" / f"sheet{s}" for s in (".svg", ".png", "_body.png", ".json"))
AREA_FILL = {"top": "#f4f2ec", "sides": "#9fc3e6", "under": "#7d828a"}
LINE = {"shoulder": ("#1f8f3a", 1.6), "lower": ("#d0208e", 1.6), "fold": ("#111111", 0.8), "opening": ("#e02020", 0.8),
        "join": ("#2050e0", 0.6), "seam": ("#ff8c00", 1.2), "outline": ("#333333", 0.6),
        "design-shoulder": ("#9fdc9f", 0.8), "design-lower": ("#f0a0d0", 0.8), "blend": ("#ff8c00", 1.6)}
# the design lines (the map's named lines as one smooth curve per stretch, carmap.Map.design_lines) run under the
# measured ones in a paler shade; where they bridge a gap between two measured curves (the sidepod's rear corner)
# the blend is orange: a band offset from the line follows the blend there
STATIONS = [z for z, _ in carmap.STATIONS]
GRID = 10.0  # cm


def _area_labels(sheet):
    """Per sheet triangle: 0 top, 1 sides, 2 under (by the map's own cut, at the centroid)."""
    m = sheet.m
    cen = sheet.corners.mean(1)
    a1, a2 = m.across_level(cen, 1), m.across_level(cen, 2)
    return np.where(a1 < 0, 0, np.where(a2 < 0, 1, 2))


def _loops(sel_uv):
    """Closed boundary loops of a set of sheet triangles (n, 3, 2): a list of (k, 2) arrays."""
    key = np.round(sel_uv.reshape(-1, 2), 4)
    _, inv = np.unique(key, axis=0, return_inverse=True)
    Fl = inv.reshape(-1, 3)
    b = surface._boundary(Fl, inv.max() + 1)
    pos = {}
    for t in range(len(Fl)):
        for c in range(3):
            pos[int(Fl[t, c])] = sel_uv[t, c]
    nxt = {}
    for i, j in b:
        nxt.setdefault(int(i), []).append(int(j))
    seen, out = set(), []
    for i, _ in b:
        if int(i) in seen:
            continue
        loop, cur = [], int(i)
        while cur not in seen:
            seen.add(cur)
            loop.append(pos[cur])
            cand = [j for j in nxt.get(cur, []) if j not in seen]
            if not cand:
                break
            cur = cand[0]
        if len(loop) >= 3:
            out.append(np.array(loop + [loop[0]]))
    return out


def _stations(sheet):
    """Per station z: its iso-z polylines on the sheet (cm) and, on the main piece, the x where
    the top centreline crosses it."""
    m = sheet.m
    z = sheet.corners[:, :, 2]
    uv = sheet.corner_uv
    out = {}
    for z0 in STATIONS:
        segs = []
        for t in np.flatnonzero((z.min(1) < z0) & (z.max(1) > z0)):
            pts = []
            for k in range(3):
                a, b = z[t, k], z[t, (k + 1) % 3]
                if (a - z0) * (b - z0) < 0:
                    s = (z0 - a) / (b - a)
                    pts.append(uv[t, k] + s * (uv[t, (k + 1) % 3] - uv[t, k]))
            if len(pts) == 2:
                segs.append(pts)
        lines = _chain(np.array(segs)) if segs else []
        # the tick: where the station meets the main piece's upper edge (its highest point on the sheet)
        tops = [l[np.argmin(l[:, 1])] for l in lines]
        x_top = float(min(tops, key=lambda p: p[1])[0]) if tops else None
        out[z0] = dict(lines=lines, x_top=x_top)
    return out


def _chain(segs, tol=1e-3):
    """Segments (n, 2, 2) chained end to end into polylines."""
    key = np.round(segs.reshape(-1, 2) / tol).astype(np.int64)
    _, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.reshape(-1, 2)
    nxt = {}
    for k, (i, j) in enumerate(inv):
        nxt.setdefault(int(i), []).append((int(j), k))
        nxt.setdefault(int(j), []).append((int(i), k))
    used = np.zeros(len(segs), bool)
    pos = {int(inv[k, e]): segs[k, e] for k in range(len(segs)) for e in range(2)}
    out = []
    for k in range(len(segs)):
        if used[k]:
            continue
        used[k] = True
        chain = [int(inv[k, 0]), int(inv[k, 1])]
        for end in (1, 0):
            while True:
                cur = chain[-1] if end else chain[0]
                cand = [(j, s) for j, s in nxt.get(cur, []) if not used[s]]
                if not cand:
                    break
                j, s = cand[0]
                used[s] = True
                chain.append(j) if end else chain.insert(0, j)
        out.append(np.array([pos[v] for v in chain]))
    return out


def features(sheet=None):
    """Everything drawn, in cm: the lines by name, the pieces (name, outline loops, bounds,
    distortion), the areas per piece (loops, bounds, distortion), the stations."""
    sheet = sheet or surface.load()
    m = sheet.m
    labels = _area_labels(sheet)
    a, ang, st = surface.measures(sheet.s1, sheet.s2)
    V = sheet.corners
    area = 0.5 * np.linalg.norm(np.cross(V[:, 1] - V[:, 0], V[:, 2] - V[:, 0]), axis=1)

    def stats(sel):
        sel = sel & sheet.painted
        if not sel.any():
            return None
        return dict(cm2=round(float(area[sel].sum())), area_pct_95=round(surface.percentile(np.abs(a[sel]), area[sel]), 1),
                    angle_deg_95=round(surface.percentile(ang[sel], area[sel]), 1), stretch_pct_95=round(surface.percentile(st[sel], area[sel]), 1))

    def bounds(uv):
        return [round(float(v), 1) for v in (uv[..., 0].min(), uv[..., 1].min(), uv[..., 0].max(), uv[..., 1].max())]

    pieces, areas = [], []
    for k, name in enumerate(sheet.piece_names):
        sel = sheet.piece == k
        pieces.append(dict(name=name, index=k, loops=_loops(sheet.corner_uv[sel]), bounds=bounds(sheet.corner_uv[sel]), distortion=stats(sel)))
        for j, aname in enumerate(("top", "sides", "under")):
            s = sel & (labels == j)
            if area[s].sum() < 50:
                continue
            areas.append(dict(name=aname, piece=name, loops=_loops(sheet.corner_uv[s]), bounds=bounds(sheet.corner_uv[s]), distortion=stats(s)))
    return dict(lines=sheet.lines, pieces=pieces, areas=areas, stations=_stations(sheet), size=[float(v) for v in sheet.size])


def write(sheet=None):
    """car/sheet.svg, .png, _body.png and .json."""
    sheet = sheet or surface.load()
    f = features(sheet)
    _svg(f)
    _png(sheet, f)
    _json(sheet, f)
    return SVG, PNG, JSON


def _mm(pts):
    return " ".join(f"{10 * x:.1f},{10 * y:.1f}" for x, y in pts)


def _svg(f):
    W, H = (10 * v for v in f["size"])
    L = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" width="{W:.0f}mm" height="{H:.0f}mm">',
         "<!-- The body sheet (tool/surface.py, tool/sheetmap.py): the car's outer skin flattened, in mm. x runs from the nose's tip "
         "(left) to the tail, y down from the top centreline. Pieces: the body (the top and the flanks, one piece), then below it the "
         "sidepod's top, the skirt, the tail, the diffuser and the inlet's duct. Draw on it in mm; shapes.sheet() paints it on the car. -->",
         '<g id="grid" stroke="#d8d8d8" stroke-width="0.5" fill="none">']
    for x in np.arange(0, W + 1, 10 * GRID):
        L.append(f'<line x1="{x:.0f}" y1="0" x2="{x:.0f}" y2="{H:.0f}"/>')
    for y in np.arange(0, H + 1, 10 * GRID):
        L.append(f'<line x1="0" y1="{y:.0f}" x2="{W:.0f}" y2="{y:.0f}"/>')
    L.append("</g>")
    L.append('<g id="areas" stroke="none">')
    for a in f["areas"]:
        pid = a["piece"].replace("'", "").replace(" ", "-")
        for k, loop in enumerate(a["loops"]):
            L.append(f'<polygon id="{a["name"]}-{pid}-{k}" class="{a["name"]}" fill="{AREA_FILL[a["name"]]}" points="{_mm(loop)}"/>')
    L.append("</g>")
    L.append('<g id="pieces" fill="none">')
    for p in f["pieces"]:
        pid = p["name"].replace("'", "").replace(" ", "-")
        for k, loop in enumerate(p["loops"]):
            L.append(f'<polyline id="piece-{pid}-{k}" stroke="{LINE["outline"][0]}" stroke-width="{10 * LINE["outline"][1] / 2:.1f}" points="{_mm(loop)}"/>')
    L.append("</g>")
    L.append('<g id="stations" fill="none" stroke="#9a9a9a" stroke-width="2" stroke-dasharray="12 8">')
    for z0, s in f["stations"].items():
        for k, line in enumerate(s["lines"]):
            L.append(f'<polyline id="z{z0}-{k}" points="{_mm(line)}"/>')
        if s["x_top"] is not None:
            L.append(f'<text x="{10 * s["x_top"]:.0f}" y="-8" font-size="30" fill="#555" stroke="none" text-anchor="middle">z {z0}</text>')
    L.append("</g>")
    for name in ("join", "opening", "fold", "design-lower", "design-shoulder", "lower", "shoulder", "blend", "seam"):
        col, w = LINE[name]
        L.append(f'<g id="{name}" fill="none" stroke="{col}" stroke-width="{10 * w / 2:.1f}">')
        for k, line in enumerate(f["lines"][name]):
            L.append(f'<polyline id="{name}-{k}" points="{_mm(line)}"/>')
        L.append("</g>")
    L.append('<g id="names" font-size="40" fill="#333">')
    for p in f["pieces"]:
        x0, y0, x1, y1 = p["bounds"]
        L.append(f'<text x="{10 * (x0 + x1) / 2:.0f}" y="{10 * y1 + 45:.0f}" text-anchor="middle">{p["name"]}</text>')
    L.append("</g></svg>")
    SVG.write_text("\n".join(L))


def _png(sheet, f, scale=5):
    """car/sheet.png: the sheet drawn; car/sheet_body.png: the same shaded by how the body faces
    (up light, down dark) and what the chase cameras see, the lines faint over it."""
    W, H = int(f["size"][0] * scale) + 2 * 60, int(f["size"][1] * scale) + 2 * 60
    m = sheet.m
    font, small = fonts.font("arial bold", 22), fonts.font("arial bold", 16)
    labels = _area_labels(sheet)
    shade = m.layers["facing_y"][m.F[sheet.tri]].mean(1)
    chase = m.layers["chase"][m.F[sheet.tri]].mean(1)
    for shaded, path in ((False, PNG), (True, BODY_PNG)):
        im = Image.new("RGB", (W, H), (250, 250, 250) if not shaded else (40, 40, 44))
        d = ImageDraw.Draw(im)
        P = lambda pts: [(60 + scale * x, 60 + scale * y) for x, y in np.asarray(pts).reshape(-1, 2)]
        if not shaded:
            for x in np.arange(0, f["size"][0] + 1, GRID):
                d.line(P([(x, 0), (x, f["size"][1])]), fill=(225, 225, 225), width=1)
            for y in np.arange(0, f["size"][1] + 1, GRID):
                d.line(P([(0, y), (f["size"][0], y)]), fill=(225, 225, 225), width=1)
        for t in range(len(sheet.tri)):
            if shaded:
                v = 0.35 + 0.5 * (0.5 + 0.5 * shade[t]) + 0.15 * chase[t]
                col = tuple(int(255 * min(v, 1) * c) for c in ((0.98, 0.97, 0.94) if sheet.painted[t] else (0.6, 0.62, 0.7)))
            else:
                h = AREA_FILL[("top", "sides", "under")[labels[t]]].lstrip("#")
                col = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
                if not sheet.painted[t]:
                    col = tuple(int(c * 0.75) for c in col)
            d.polygon(P(sheet.corner_uv[t]), fill=col)
        for z0, s in f["stations"].items():
            for line in s["lines"]:
                d.line(P(line), fill=(150, 150, 150) if not shaded else (120, 120, 130), width=1)
            if s["x_top"] is not None:
                d.text((60 + scale * s["x_top"], 36), f"z {z0}", fill=(80, 80, 80) if not shaded else (200, 200, 200), font=small, anchor="mm")
        for name in ("outline", "join", "opening", "fold", "design-lower", "design-shoulder", "lower", "shoulder", "blend", "seam"):
            col, w = LINE[name]
            rgb = tuple(int(col.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
            for line in (f["lines"][name] if name != "outline" else [l for p in f["pieces"] for l in p["loops"]]):
                d.line(P(line), fill=rgb, width=max(1, int(w * scale / 2 + 0.5)))
        for p in f["pieces"]:
            x0, y0, x1, y1 = p["bounds"]
            d.text((60 + scale * (x0 + x1) / 2, 60 + scale * y1 + 14), p["name"], fill=(40, 40, 40) if not shaded else (230, 230, 230), font=font, anchor="mm")
        d.text((60, 12), "The body sheet: the car's outer skin flattened, 1 grid square = 10 cm on the paint; the nose's tip at the left, "
               "the top centreline along the top edge (tool/surface.py). The car's model: amogusstrikesback2, CC-BY-4.0.",
               fill=(60, 60, 60) if not shaded else (220, 220, 220), font=small)
        im.save(path)


def _json(sheet, f):
    mm = lambda arr: [[round(10 * float(x), 1), round(10 * float(y), 1)] for x, y in np.asarray(arr).reshape(-1, 2)]
    a, ang, st = surface.measures(sheet.s1, sheet.s2)
    doc = dict(
        about="The body sheet (tool/surface.py): the car's outer skin flattened, in mm. x from the nose's tip (left) to the tail, y down from "
              "the top centreline. Pieces: the body (the top and the flanks in one), the sidepod's top, the skirt, the tail, the diffuser, the "
              "inlet's duct, each with its outline, bounds [x0, y0, x1, y1] and distortion (95th percentile by area over the painted body: "
              "area %, angle degrees, stretch %). lines: the map's lines as polylines. stations: where each z of car/map.md runs on the sheet, "
              "and x_top, the top centreline's x there. lines.design-shoulder and lines.design-lower are the design lines: each "
              "named line as one smooth curve per stretch, blended (lines.blend, orange on the picture) across the gap between two "
              "measured curves at the sidepod's rear corner; a band or a pinstripe is measured in 3D from them (shapes.line, "
              "shapes.line_offset), never on the sheet. Draw lattices, logos and decals in mm here; shapes.sheet() paints the "
              "drawing on the car, the right side mirrored.",
        size_mm=[round(10 * v) for v in f["size"]],
        lines={name: [mm(l) for l in lines] for name, lines in f["lines"].items()},
        pieces=[dict(name=p["name"], bounds_mm=[round(10 * v) for v in p["bounds"]], outline=[mm(l) for l in p["loops"]], distortion=p["distortion"]) for p in f["pieces"]],
        areas=[dict(name=x["name"], piece=x["piece"], bounds_mm=[round(10 * v) for v in x["bounds"]], distortion=x["distortion"]) for x in f["areas"]],
        stations={str(z): dict(x_top_mm=None if s["x_top"] is None else round(10 * s["x_top"]), lines=[mm(l) for l in s["lines"]]) for z, s in f["stations"].items()},
        targets=dict(area_pct=surface.AREA_LIMIT, angle_deg=surface.ANGLE_LIMIT, at="95th percentile by area over the painted body"))
    JSON.write_text(json.dumps(doc, separators=(",", ":")))
