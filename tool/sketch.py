"""The sketch: where every call of a design lands, drawn on the car's side and top views (`tool.skin read` and `show`
write build/<name>_landing.png, to look at before the car is shown). The body in grey from the model's own triangles,
each call's texels in a colour of its own, numbered where they lie, the tyres outlined over them (what a wheel hides
shows through), and a legend: each call's words and its area on the body. A coat over most of the body (COAT cm² or
more) is said in the legend and not drawn, so the graphics show.

    sk = sketch.Sketch()          paintbox.Skin keeps one while it paints (Skin.sketch)
    sk.land(op, pos, nrm)         a call's texels on the body, as they land (Canvas.took)
    sk.draw(skin, path)           the picture, once the design is done; returns the path
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from tool import fbx

SCALE = 4.0   # pixels per cm
PAD = 24      # pixels round a view
COAT = 12000  # cm² of the body: from this a paint is a coat, said and not drawn
SEEN = 0.05   # a texel facing the view this much is drawn
PALETTE = ((220, 40, 40), (30, 110, 220), (30, 160, 70), (230, 140, 0), (150, 50, 200), (0, 160, 170), (200, 30, 140),
           (120, 90, 30), (60, 60, 60), (240, 200, 0), (90, 170, 230), (170, 220, 60))
LIGHT = np.array([0.3, 0.8, 0.5]) / np.linalg.norm([0.3, 0.8, 0.5])


def _font(size):
    return ImageFont.load_default(size)


class _View:
    """An orthographic view of the car: its name, the camera (what faces it is seen), the car's axes along the picture
    (axis, sign) and the picture's size from the body's extent."""

    def __init__(self, name, cam, u, v, V):
        self.name, self.cam, self.u, self.v = name, np.asarray(cam, np.float64), u, v
        uv = self.uv(V)
        self.lo = uv.min(0)
        size = uv.max(0) - self.lo
        self.w, self.h = int(size[0] * SCALE) + 2 * PAD, int(size[1] * SCALE) + 2 * PAD

    def uv(self, pts):
        pts = np.asarray(pts, np.float64).reshape(-1, 3)
        return np.stack([pts[:, self.u[0]] * self.u[1], pts[:, self.v[0]] * self.v[1]], 1)

    def px(self, pts):
        return (self.uv(pts) - self.lo) * SCALE + PAD

    def pixels(self, pts):
        """Each point's flat pixel index."""
        q = np.floor(self.px(pts)).astype(np.int64)
        return np.clip(q[:, 1], 0, self.h - 1) * self.w + np.clip(q[:, 0], 0, self.w - 1)

    def triangles(self, mesh, shade=True):
        """The mesh's triangles facing this view as an image: far ones first, shaded by their facing (or flat)."""
        P, F = mesh["positions"].astype(np.float64), mesh["tri_vertex"]
        X = P[F]
        fn = np.cross(X[:, 1] - X[:, 0], X[:, 2] - X[:, 0])
        fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-9)
        on = np.flatnonzero(fn @ self.cam > 0.02)
        order = on[np.argsort(X[on].mean(1) @ self.cam)]
        im = Image.new("L", (self.w, self.h), 0)
        d = ImageDraw.Draw(im)
        for t in order:
            g = int(170 + 70 * max(0.0, fn[t] @ LIGHT)) if shade else 255
            d.polygon([tuple(p) for p in self.px(X[t])], fill=g, outline=max(g - 12, 1) if shade else 255)
        return np.asarray(im)


class Sketch:
    def __init__(self):
        meshes = fbx.meshes()
        self.body, self.tyres = meshes[fbx.MESH_OF["Skin"]], meshes[fbx.MESH_OF["Wheels"]]
        V = self.body["positions"]
        self.views = (_View("the left side", (1, 0, 0), (2, 1), (1, -1), V), _View("from above", (0, 1, 0), (2, 1), (0, -1), V))
        self.calls = {}  # op -> per view, the pixel indices its texels fall on, as they land

    def land(self, op, pos, nrm):
        """A call's texels on the body: kept per view, those facing it."""
        mine = self.calls.setdefault(op, [[] for _ in self.views])
        for k, v in enumerate(self.views):
            vis = (nrm @ v.cam) > SEEN
            if vis.any():
                mine[k].append(np.unique(v.pixels(pos[vis])))

    def draw(self, skin, path):
        """The picture: each view with every call's texels on it (a coat said, not drawn), the tyres outlined, a tag at
        each call's number, and the legend under them."""
        from scipy import ndimage
        rows = []  # the legend: (op, words, colour, drawn)
        for op, rec in enumerate(skin.receipts):
            if op not in self.calls:
                continue
            area = sum(rec.painted.get("Skin", {}).values())
            coat = area >= COAT
            rows.append((op, f"{rec.what}  ({area:,.0f} cm2{': a coat over the body, not drawn' if coat else ''})",
                         (200, 200, 200) if coat else PALETTE[len(rows) % len(PALETTE)], not coat))
        sheets = []
        for k, v in enumerate(self.views):
            g = v.triangles(self.body)
            im = np.where(g[..., None] > 0, np.repeat(g[..., None], 3, 2), 250).astype(np.uint8).reshape(-1, 3)
            tags = []
            for op, words, colour, drawn in rows:
                if not drawn or not self.calls[op][k]:
                    continue
                pix = np.unique(np.concatenate(self.calls[op][k]))
                im[pix] = colour
                mid = np.array([pix.mean() % v.w, pix.mean() // v.w])
                near = pix[np.argmin(np.abs(pix % v.w - mid[0]) + np.abs(pix // v.w - mid[1]))]
                tags.append(((near % v.w, near // v.w), str(op + 1), colour))
            tyre = v.triangles(self.tyres, shade=False) > 0
            im = im.reshape(v.h, v.w, 3)
            im[tyre] = (im[tyre] * 0.65 + 0.35 * 120).astype(np.uint8)
            im[tyre & ~ndimage.binary_erosion(tyre, iterations=2)] = (70, 70, 70)
            sheet = Image.fromarray(im)
            d = ImageDraw.Draw(sheet)
            for (x, y), text, colour in tags:
                f = _font(13)
                tw = d.textlength(text, font=f)
                r = max(tw / 2 + 5, 10)
                d.ellipse([x - r, y - r, x + r, y + r], fill=colour, outline=(20, 20, 20), width=2)
                d.text((x - tw / 2, y - 8), text, font=f, fill=(255, 255, 255) if sum(colour) < 400 else (0, 0, 0))
            d.text((8, 4), v.name, font=_font(14), fill=(40, 40, 40))
            sheets.append(sheet)
        w = max(s.width for s in sheets)
        h = sum(s.height for s in sheets) + 20 * (len(rows) + 2)
        out = Image.new("RGB", (w, h), (255, 255, 255))
        y = 0
        for s in sheets:
            out.paste(s, (0, y))
            y += s.height
        d = ImageDraw.Draw(out)
        d.text((8, y + 4), f"{skin.name}: where each call lands, before the car is shown (the nose points right; each call's "
                           "texels in its colour, numbered; the tyres outlined over what they hide)", font=_font(14), fill=(0, 0, 0))
        y += 24
        for op, words, colour, drawn in rows:
            d.rectangle([8, y + 3, 26, y + 15], fill=colour)
            d.text((32, y), f"{op + 1}: {words}", font=_font(13), fill=(20, 20, 20))
            y += 20
        path.parent.mkdir(parents=True, exist_ok=True)
        out.save(path)
        return path
