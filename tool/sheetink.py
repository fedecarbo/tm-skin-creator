"""Ink on the body sheet: a drawing in the sheet's millimetres made into a weight per texel.

A drawing is rasterised once on the sheet (RES pixels per mm, a texel being about 0.9 mm), and
every texel reads the pixel under its own place on the sheet (tool/surface.sheet_cm), so a shape
drawn flat lands on the car with its true size, the right side mirrored. Drawings:

    Ink.svg(path_or_text)         an SVG in the sheet's frame (car/sheet.svg's viewBox: 1 unit = 1 mm):
                                  rect, circle, ellipse, line, polyline, polygon, path (M L H V C Q Z,
                                  absolute or relative), g, transform (translate, scale, rotate, matrix);
                                  a filled shape is ink, a stroked one is a line of its stroke-width;
                                  a subpath inside another of the same path is a hole
    Ink.image(picture, box)       a picture's alpha (or, with no alpha, its lightness) laid over the box
                                  (x0, y0, x1, y1) in mm
    Ink.lines(polylines, width)   lines `width` mm wide along polylines ((n, 2) arrays in mm)
    Ink.where(fn)                 fn(x, y) over the sheet's mm grid -> weight 0..1 (or a boolean)
    ink.sample(uv_cm)             the weight under sheet points (n, 2) in cm; 0 off the drawing
"""

import re
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image, ImageDraw

RES = 2  # pixels per mm


class Ink:
    def __init__(self, size_mm):
        self.w, self.h = (int(np.ceil(v * RES)) + 1 for v in size_mm)
        self.im = Image.new("L", (self.w, self.h), 0)
        self.rgb = None  # a picture's colours (h, w, 3), Ink.image

    @classmethod
    def blank(cls):
        from tool import surface
        return cls([10 * v for v in surface.load().size])

    def sample(self, uv_cm, colour=False):
        """Bilinear weights 0..1 under sheet points (n, 2) in cm; 0 off the sheet or the raster.
        colour: the picture's colours (n, 3) instead (Ink.image), 0 off it."""
        uv = np.asarray(uv_cm, np.float64)
        arr = self.rgb if colour else np.asarray(self.im, np.float32)[:, :, None]
        out = np.zeros((len(uv), arr.shape[2]), np.float32)
        ok = np.isfinite(uv).all(1)
        x, y = uv[ok, 0] * 10 * RES - 0.5, uv[ok, 1] * 10 * RES - 0.5
        x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
        fx, fy = x - x0, y - y0
        val = np.zeros((ok.sum(), arr.shape[2]), np.float32)
        for dx, dy, wgt in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
            xi, yi = x0 + dx, y0 + dy
            inside = (xi >= 0) & (yi >= 0) & (xi < arr.shape[1]) & (yi < arr.shape[0])
            val[inside] += wgt[inside, None] * arr[yi[inside], xi[inside]]
        out[ok] = val / 255
        return out if colour else out[:, 0]

    # ---- the drawings ----

    @classmethod
    def lines(cls, polylines, width):
        ink = cls.blank()
        d = ImageDraw.Draw(ink.im)
        for line in polylines:
            pts = [(float(x) * RES, float(y) * RES) for x, y in np.asarray(line).reshape(-1, 2)]
            if len(pts) >= 2:
                d.line(pts, fill=255, width=max(1, int(round(width * RES))), joint="curve")
        return ink

    @classmethod
    def where(cls, fn):
        ink = cls.blank()
        arr = np.zeros((ink.h, ink.w), np.uint8)
        xs = (np.arange(ink.w) + 0.5) / RES
        for r0 in range(0, ink.h, 256):
            ys = (np.arange(r0, min(r0 + 256, ink.h)) + 0.5) / RES
            X, Y = np.meshgrid(xs, ys)
            arr[r0:r0 + len(ys)] = np.clip(np.asarray(fn(X, Y), np.float32) * 255, 0, 255).astype(np.uint8)
        ink.im = Image.fromarray(arr)
        return ink

    @classmethod
    def image(cls, picture, box):
        ink = cls.blank()
        if isinstance(picture, (str, bytes)) or hasattr(picture, "read") or hasattr(picture, "__fspath__"):
            picture = Image.open(picture)
        x0, y0, x1, y1 = box
        pic = picture.convert("RGBA") if picture.mode in ("RGBA", "LA", "P") else picture.convert("L")
        w, h = max(1, int(round((x1 - x0) * RES))), max(1, int(round((y1 - y0) * RES)))
        pic = pic.resize((w, h), Image.LANCZOS)
        weight = pic.getchannel("A") if pic.mode == "RGBA" else pic
        px, py = int(round(x0 * RES)), int(round(y0 * RES))
        ink.im.paste(weight, (px, py))
        rgb = Image.new("RGB", (ink.w, ink.h), 0)  # the picture's colours, for a decal
        rgb.paste(pic.convert("RGB"), (px, py))
        ink.rgb = np.asarray(rgb, np.float32)
        return ink

    @classmethod
    def svg(cls, source):
        text = source if isinstance(source, str) and source.lstrip().startswith("<") else open(source, encoding="utf-8").read()
        root = ET.fromstring(text)
        ink = cls.blank()
        d = ImageDraw.Draw(ink.im)
        _walk(root, np.eye(3), d, {})
        return ink


# ---- the SVG subset ----

_NUM = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")


def _floats(s):
    return [float(v) for v in _NUM.findall(s or "")]


def _transform(s, M):
    """M composed with an SVG transform attribute."""
    for name, args in re.findall(r"(\w+)\s*\(([^)]*)\)", s or ""):
        v = _floats(args)
        T = np.eye(3)
        if name == "translate":
            T[0, 2], T[1, 2] = v[0], v[1] if len(v) > 1 else 0.0
        elif name == "scale":
            T[0, 0], T[1, 1] = v[0], v[1] if len(v) > 1 else v[0]
        elif name == "rotate":
            a = np.radians(v[0])
            R = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1.0]])
            if len(v) >= 3:
                C = np.eye(3)
                C[0, 2], C[1, 2] = v[1], v[2]
                Ci = np.eye(3)
                Ci[0, 2], Ci[1, 2] = -v[1], -v[2]
                R = C @ R @ Ci
            T = R
        elif name == "matrix" and len(v) == 6:
            T = np.array([[v[0], v[2], v[4]], [v[1], v[3], v[5]], [0, 0, 1.0]])
        M = M @ T
    return M


def _style(el, inherited):
    st = dict(inherited)
    for k in ("fill", "stroke", "stroke-width", "fill-rule"):
        if el.get(k) is not None:
            st[k] = el.get(k)
    for part in (el.get("style") or "").split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            st[k.strip()] = v.strip()
    return st


def _tag(el):
    return el.tag.split("}")[-1]


def _bezier(p0, p1, p2, p3=None, n=16):
    t = np.linspace(0, 1, n + 1)[1:, None]
    if p3 is None:  # quadratic
        return ((1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2).tolist()
    return ((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3).tolist()


def _path(dstr):
    """Subpaths of an SVG path as lists of points (closed flag)."""
    tokens = re.findall(r"[MmLlHhVvCcQqZzSsTtAa]|" + _NUM.pattern, dstr or "")
    subs, cur, closed = [], [], False
    pos = np.zeros(2)
    start = np.zeros(2)
    last_ctrl = None
    i, cmd = 0, None
    while i < len(tokens):
        if tokens[i].isalpha():
            cmd = tokens[i]
            i += 1
            if cmd in "Zz":
                if cur:
                    subs.append((cur, True))
                cur, pos = [], start.copy()
                continue
        rel = cmd.islower()
        c = cmd.upper()
        need = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "Q": 4, "S": 4, "T": 2, "A": 7}[c]
        v = [float(t) for t in tokens[i:i + need]]
        i += need
        if len(v) < need:
            break
        base = pos if rel else np.zeros(2)
        if c == "M":
            if cur:
                subs.append((cur, False))
            pos = base + v
            start = pos.copy()
            cur = [tuple(pos)]
            cmd = "l" if rel else "L"
            last_ctrl = None
        elif c == "L":
            pos = base + v
            cur.append(tuple(pos))
            last_ctrl = None
        elif c == "H":
            pos = np.array([base[0] + v[0], pos[1]])
            cur.append(tuple(pos))
        elif c == "V":
            pos = np.array([pos[0], base[1] + v[0]])
            cur.append(tuple(pos))
        elif c in "CS":
            if c == "C":
                p1, p2, p3 = base + v[0:2], base + v[2:4], base + v[4:6]
            else:
                p1 = 2 * pos - last_ctrl if last_ctrl is not None else pos
                p2, p3 = base + v[0:2], base + v[2:4]
            cur += [tuple(p) for p in _bezier(pos, p1, p2, p3)]
            pos, last_ctrl = p3, p2
        elif c in "QT":
            if c == "Q":
                p1, p2 = base + v[0:2], base + v[2:4]
            else:
                p1 = 2 * pos - last_ctrl if last_ctrl is not None else pos
                p2 = base + v[0:2]
            cur += [tuple(p) for p in _bezier(pos, p1, p2)]
            pos, last_ctrl = p2, p1
        elif c == "A":  # an arc: taken as a straight line to its end
            pos = base + v[5:7]
            cur.append(tuple(pos))
    if cur:
        subs.append((cur, False))
    return subs


def _inside(pt, poly):
    """Whether a point lies inside a polygon (ray crossing)."""
    x, y = pt
    n = len(poly)
    inside = False
    for k in range(n):
        (x0, y0), (x1, y1) = poly[k], poly[(k + 1) % n]
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            inside = not inside
    return inside


def _walk(el, M, d, style):
    st = _style(el, style)
    M = _transform(el.get("transform"), M)
    tag = _tag(el)
    shapes = []  # (points, closed)
    g = lambda k, default=0.0: float(el.get(k, default))
    if tag == "rect":
        x, y, w, h = g("x"), g("y"), g("width"), g("height")
        shapes.append(([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], True))
    elif tag in ("circle", "ellipse"):
        rx = g("r") if tag == "circle" else g("rx")
        ry = g("r") if tag == "circle" else g("ry")
        t = np.linspace(0, 2 * np.pi, 64, endpoint=False)
        shapes.append(([(g("cx") + rx * np.cos(a), g("cy") + ry * np.sin(a)) for a in t], True))
    elif tag == "line":
        shapes.append(([(g("x1"), g("y1")), (g("x2"), g("y2"))], False))
    elif tag in ("polyline", "polygon"):
        v = _floats(el.get("points"))
        shapes.append(([(v[k], v[k + 1]) for k in range(0, len(v) - 1, 2)], tag == "polygon"))
    elif tag == "path":
        shapes = _path(el.get("d"))
    if shapes:
        fill = st.get("fill", "black")
        stroke = st.get("stroke", "none")
        width = float(_floats(st.get("stroke-width", "1"))[0] or 1)
        pts = [([tuple((M @ [x, y, 1])[:2]) for x, y in s], closed) for s, closed in shapes]
        pix = [([(x * RES, y * RES) for x, y in s], closed) for s, closed in pts]
        if fill != "none" and tag not in ("line", "polyline"):
            polys = [s for s, _ in pix if len(s) >= 3]
            for k, s in enumerate(polys):
                hole = sum(_inside(s[0], o) for j, o in enumerate(polys) if j != k) % 2 == 1
                d.polygon(s, fill=0 if hole else 255)
        if stroke != "none":
            wpx = max(1, int(round(width * RES)))
            for s, closed in pix:
                if len(s) >= 2:
                    d.line(s + ([s[0]] if closed else []), fill=255, width=wpx, joint="curve")
    for child in el:
        _walk(child, M, d, st)
