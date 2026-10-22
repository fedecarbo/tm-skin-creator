"""atlas: the car drawn flat with its lines and panels named, from the mesh. A throwaway sample (2026-10-22), not the tool.

    PY atlas.py            -> see/out/atlas_side.png, atlas_top.png, atlas_front.png (numbered tags, a legend beside),
                              cards_1.png, cards_2.png (one card per line: the line alone, its ends named)

"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from tool import meshlines, surface

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
FONT = "/System/Library/Fonts/Helvetica.ttc"
LEAST_LINE, LEAST_AREA = 80.0, 500.0
SKIP = ("wheel cover ring", "wheel cover disc", "wheel cover hub")


def font(size):
    try:
        return ImageFont.truetype(FONT, size)
    except OSError:
        return ImageFont.load_default()


class View:
    """An orthographic view: name, the camera's direction (what faces it is seen), and how a point maps to (u, v) cm."""

    def __init__(self, name, cam, u, v, note):
        self.name, self.cam, self.note = name, np.asarray(cam, float), note
        self.u, self.v = u, v  # functions pts(n,3) -> cm

    def uv(self, pts):
        pts = np.asarray(pts, float).reshape(-1, 3)
        return np.stack([self.u(pts), self.v(pts)], 1)


VIEWS = {
    "side": View("left side", (1, 0, 0), lambda p: p[:, 2], lambda p: -p[:, 1], "seen from the car's left; the nose points right"),
    "top": View("top", (0, 1, 0), lambda p: p[:, 2], lambda p: -p[:, 0], "seen from above; the nose points right, the car's left is at the top"),
    "front": View("front", (0, 0, 1), lambda p: p[:, 0], lambda p: -p[:, 1], "seen from the front; the car's left is on your right"),
}


class Sheet:
    def __init__(self, view, scale, pad=40, legend=0):
        self.view, self.scale, self.pad = view, scale, pad
        S = surface.load()
        uv = view.uv(S.V)
        self.lo, self.hi = uv.min(0), uv.max(0)
        w = int((self.hi[0] - self.lo[0]) * scale) + 2 * pad
        h = int((self.hi[1] - self.lo[1]) * scale) + 2 * pad
        self.w, self.h, self.legend = w, h, legend
        tall = max(h, 1180) if legend else h  # room for the legend's rows beside a short view
        self.im = Image.new("RGB", (w + legend, tall), (250, 250, 250))
        self.d = ImageDraw.Draw(self.im)
        self.S = S

    def px(self, pts):
        uv = self.view.uv(pts)
        return (uv - self.lo) * self.scale + self.pad

    def body(self, shade=True):
        """The body's triangles facing the camera, far ones first, shaded by their facing."""
        S, v = self.S, self.view
        face = S.fn @ v.cam
        on = np.flatnonzero(face > 0.02)
        C = S.V[S.F[on]].mean(1)
        depth = C @ v.cam
        order = on[np.argsort(depth)]
        light = np.array([0.3, 0.8, 0.5])
        light /= np.linalg.norm(light)
        for t in order:
            n = S.fn[t]
            g = int(170 + 70 * max(0.0, n @ light)) if shade else 220
            poly = [tuple(p) for p in self.px(S.V[S.F[t]])]
            self.d.polygon(poly, fill=(g, g, g), outline=(g - 12, g - 12, g - 12))

    def visible(self, pts, nrm):
        return (np.asarray(nrm) @ self.view.cam) > -0.15

    def line(self, pts, nrm, colour, width=3, seen_only=True):
        q = self.px(pts)
        vis = self.visible(pts, nrm) if seen_only else np.ones(len(q), bool)
        run = []
        for k in range(len(q)):
            if vis[k]:
                run.append(tuple(q[k]))
            if (not vis[k] or k == len(q) - 1) and len(run) > 1:
                self.d.line(run, fill=colour, width=width)
                run = []
        return q, vis

    def arrow(self, p, q, colour, size=9):
        """An arrow head at p pointing from q to p."""
        p, q = np.asarray(p), np.asarray(q)
        d = p - q
        n = np.linalg.norm(d)
        if n < 1e-6:
            return
        d /= n
        s = np.array([-d[1], d[0]])
        a, b = p - d * size + s * size * 0.6, p - d * size - s * size * 0.6
        self.d.polygon([tuple(p), tuple(a), tuple(b)], fill=colour)

    def tag(self, xy, text, fill, size=15, ring=None):
        f = font(size)
        tw = self.d.textlength(text, font=f)
        r = max(tw / 2 + 5, size * 0.75)
        x, y = xy
        self.d.ellipse([x - r, y - r, x + r, y + r], fill=fill, outline=ring or (20, 20, 20), width=2)
        self.d.text((x - tw / 2, y - size * 0.6), text, font=f, fill=(255, 255, 255) if sum(fill) < 400 else (0, 0, 0))

    def text(self, xy, text, size=14, fill=(20, 20, 20)):
        self.d.text(xy, text, font=font(size), fill=fill)


COLOURS = {"crease": (200, 40, 40), "opening": (20, 90, 200), "seam": (20, 140, 60), "rounded": (190, 110, 0)}
KIND = {"crease": "crisp line", "opening": "edge where the body ends", "seam": "seam", "rounded": "rounded edge's line"}


def atlas_items():
    """The lines (one per name, a roll's longest) and panels drawn: [(tag, name, record, kind)]."""
    lines, panels = [], []
    for n, rec in meshlines.named().items():
        k = n.rsplit(" ", 2)[-2]
        if n.startswith(SKIP):
            continue
        if k == "panel":
            if rec["area"] >= LEAST_AREA:
                panels.append((n, rec))
        else:
            L = max(rec, key=lambda x: x["length"]) if isinstance(rec, list) else rec
            if L["length"] >= LEAST_LINE:
                lines.append((n, L))
    lines.sort(key=lambda t: -t[1]["length"])
    panels.sort(key=lambda t: -t[1]["area"])
    items = [(f"{i + 1}", n, L, "line") for i, (n, L) in enumerate(lines)]
    items += [(chr(65 + i) if i < 26 else f"P{i}", n, r, "panel") for i, (n, r) in enumerate(panels)]
    return items


def ends_words(L):
    p = L["pts"]
    if L["closed"]:
        return "a loop"
    a, b = p[0], p[-1]
    if abs(a[2] - b[2]) < 5:
        return f"runs across the car, start ({a[0]:.0f}, {a[1]:.0f}, {a[2]:.0f})"
    first = "NOSE" if a[2] > b[2] else "TAIL"
    return f"course runs {first} first: start z {a[2]:.0f}, end z {b[2]:.0f}"


def draw_atlas(key, scale, legend_w=760):
    v = VIEWS[key]
    sh = Sheet(v, scale, legend=legend_w)
    sh.body()
    items = atlas_items()
    legend = []
    for tag, name, rec, kind in items:
        if kind == "panel":
            at = np.asarray(rec["at"])
            e, lab = meshlines._edges("Skin"), meshlines._panels("Skin")
            t = meshlines._triangle_at(at)
            if (e["N"][e["T"][t]].mean(0) @ v.cam) < 0.1:
                legend.append((tag, f"{name}  ({rec['area']:.0f} cm2)  not seen in this view", (120, 120, 120)))
                continue
            q = sh.px(at)[0]
            sh.tag(tuple(q), tag, (255, 230, 90), size=16)
            legend.append((tag, f"{name}  ({rec['area']:.0f} cm2; parts: {', '.join(rec['parts'][:2])})", (120, 100, 0)))
            continue
        col = COLOURS[rec["kind"]]
        q, vis = sh.line(rec["pts"], rec["nrm"], col, width=3)
        if not vis.any():
            legend.append((tag, f"{name}  ({KIND[rec['kind']]}, {rec['length']:.0f} cm)  not seen in this view", (120, 120, 120)))
            continue
        k = np.flatnonzero(vis)
        mid = k[len(k) // 2]
        sh.tag(tuple(q[mid]), tag, col, size=14)
        if not rec["closed"]:
            if vis[0] and len(q) > 4:
                sh.arrow(q[0], q[4], col, size=11)  # the course's start: an arrow head pointing out of it
                sh.d.ellipse([q[0][0] - 5, q[0][1] - 5, q[0][0] + 5, q[0][1] + 5], fill=(255, 255, 255), outline=col, width=2)
            if vis[-1]:
                sh.d.rectangle([q[-1][0] - 5, q[-1][1] - 5, q[-1][0] + 5, q[-1][1] + 5], fill=col)
        legend.append((tag, f"{name}  ({KIND[rec['kind']]}, {rec['length']:.0f} cm; {ends_words(rec)})", col))
    # the legend
    x0, y = sh.w + 10, 10
    sh.text((x0, y), f"The car's lines and panels, {v.name} view: {v.note}.", 16)
    y += 24
    sh.text((x0, y), "Lines: red crisp lines, blue edges where the body ends, green seams, orange rounded edges. A white dot with an", 13)
    y += 17
    sh.text((x0, y), "arrow head is a course's START (where meshlines.line(name) begins), a square its END. Yellow letters: panels.", 13)
    y += 17
    sh.text((x0, y), f"x out to the car's left, y up, z forward: nose tip z 215, tail z -162. Scale {scale:.0f} px per cm.", 13)
    y += 24
    for tag, words, col in legend:
        sh.d.rectangle([x0, y + 2, x0 + 22, y + 16], fill=col)
        sh.text((x0 + 28, y), f"{tag}: {words}", 13)
        y += 17
    OUT.mkdir(exist_ok=True)
    f = OUT / f"atlas_{key}.png"
    sh.im.save(f)
    return f, items


def draw_cards(per_row=3, scale=1.6):
    """One card per line: side and top views, the line alone in red, its ends named."""
    items = [it for it in atlas_items() if it[3] == "line"]
    side, top = Sheet(VIEWS["side"], scale, pad=14), Sheet(VIEWS["top"], scale, pad=14)
    side.body(shade=False)
    top.body(shade=False)
    base_side, base_top = side.im.copy(), top.im.copy()
    cw, ch = side.w + 8, side.h + top.h + 70
    files, cards = [], []
    for tag, name, L, _ in items:
        card = Image.new("RGB", (cw, ch), (255, 255, 255))
        d = ImageDraw.Draw(card)
        y = 0
        for base, sh, dy in ((base_side, side, 0), (base_top, top, side.h)):
            im = base.copy()
            sh.im, sh.d = im, ImageDraw.Draw(im)
            q, vis = sh.line(L["pts"], L["nrm"], (210, 30, 30), width=4, seen_only=False)
            if not L["closed"]:
                sh.arrow(q[0], q[min(4, len(q) - 1)], (210, 30, 30), 12)
                sh.d.ellipse([q[0][0] - 6, q[0][1] - 6, q[0][0] + 6, q[0][1] + 6], fill=(255, 255, 255), outline=(210, 30, 30), width=3)
                sh.d.rectangle([q[-1][0] - 6, q[-1][1] - 6, q[-1][0] + 6, q[-1][1] + 6], fill=(210, 30, 30))
                sh.text((q[0][0] + 8, q[0][1] - 18), "START", 13, (210, 30, 30))
                sh.text((q[-1][0] + 8, q[-1][1] + 4), "END", 13, (210, 30, 30))
            card.paste(im, (4, dy))
        p = L["pts"]
        d.text((6, side.h + top.h + 4), f"{tag}. {name}: {KIND[L['kind']]}, {L['length']:.0f} cm, along the {', '.join(L['parts'][:2])}", font=font(15), fill=(0, 0, 0))
        if L["closed"]:
            words = f"a closed loop: z {p[:, 2].max():.0f} to {p[:, 2].min():.0f}, y {p[:, 1].min():.0f} to {p[:, 1].max():.0f}"
        else:
            a, b = p[0], p[-1]
            words = (f"START ({a[0]:.0f}, {a[1]:.0f}, {a[2]:.0f}) is the {'NOSE' if a[2] > b[2] + 5 else 'TAIL' if b[2] > a[2] + 5 else ''} end; "
                     f"END ({b[0]:.0f}, {b[1]:.0f}, {b[2]:.0f}) is the {'TAIL' if a[2] > b[2] + 5 else 'NOSE' if b[2] > a[2] + 5 else ''} end. "
                     f"{ends_words(L)}")
        d.text((6, side.h + top.h + 26), words, font=font(13), fill=(60, 60, 60))
        d.text((6, side.h + top.h + 46), f"meshlines.line({name!r}{', tilt=' + str(round(L['tilt'])) if 'tilt' in L else ''})", font=font(13), fill=(60, 60, 60))
        d.rectangle([0, 0, cw - 1, ch - 1], outline=(180, 180, 180))
        cards.append(card)
    rows_per_sheet = 7
    for s in range(0, len(cards), per_row * rows_per_sheet):
        chunk = cards[s:s + per_row * rows_per_sheet]
        rows = (len(chunk) + per_row - 1) // per_row
        sheet = Image.new("RGB", (cw * per_row, ch * rows), (255, 255, 255))
        for i, c in enumerate(chunk):
            sheet.paste(c, ((i % per_row) * cw, (i // per_row) * ch))
        f = OUT / f"cards_{s // (per_row * rows_per_sheet) + 1}.png"
        sheet.save(f)
        files.append(f)
    return files


if __name__ == "__main__":
    for key, scale in (("side", 5.5), ("top", 5.5), ("front", 7.0)):
        f, items = draw_atlas(key, scale)
        print(f, f"{len(items)} items")
    for f in draw_cards():
        print(f)
