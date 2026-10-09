"""A receipt: what one call of the paint box did, in a line. Every verb of `paintbox.Skin` returns one, and `tool.skin
show` prints each as the paint goes, so a design is read back call by call: what it painted and how much, where a
mark landed, what it refused and any accident it found.

    r = s.paint("body", "gloss red")       str(r): "gloss red on body: 31 parts of the body, 58,900 cm²", then its notes
    badge = s.mark("rear flank", "gloss", marks.disc(), size=12)
    badge.centre, badge.size, badge.twin   where it landed (cm), its width as laid (0: nothing laid), its mirror image's
    s.decal("7", badge, ...)               a receipt is a place for the next graphic
"""

import numpy as np

MOST = 4  # parts named in a line before "and n more"
SAMPLE = 400_000  # texels a big paint's area is read from


class Receipt:
    def __init__(self, what, step):
        self.what, self.step = what, step
        self.painted = {}   # texture set -> {part name: cm²}
        self.notes = []     # what the call decided, in words
        self.findings = []  # what it found wrong (tool/judge.py's findings)
        # a mark's place (tool/marks.py): its centre (x, y, z in cm, on the car), size (its width in cm as laid; 0 when
        # nothing was), moved (cm from where it was wanted), right, up and facing (the frame it lies in at its centre),
        # stretch (how far the sticker is stretched under it, a share of its lengths), turn (degrees the surface turns
        # under it from its centre's facing), twin (the same for its mirror image on the other side, or None)
        self.centre, self.size, self.moved = (0.0, 0.0, 0.0), 0.0, 0.0
        self.right, self.up, self.facing = (0, 0, -1), (0, 1, 0), (1, 0, 0)
        self.stretch, self.turn, self.twin = 0.0, 0.0, None
        self.mark, self.said = False, ""
        self.empty = None  # what a verb that meant to paint and painted nothing says

    def landed(self, centre, size=0.0, moved=0.0, right=(0, 0, -1), up=(0, 1, 0), facing=(1, 0, 0), stretch=0.0, turn=0.0,
               said=""):
        """Where a mark landed; said: its size in words ("4.6 cm tall")."""
        self.mark, self.said = True, said
        self.centre = tuple(round(float(v), 2) for v in centre)
        self.size, self.moved = float(size), float(moved)
        self.right, self.up, self.facing = (tuple(float(v) for v in d) for d in (right, up, facing))
        self.stretch, self.turn = float(stretch), float(turn)
        return self

    def add(self, tset, names, area):
        """Paint laid on a texture set: each part's name reached and the cm² on it."""
        if not names:
            return
        mine = self.painted.setdefault(tset, {})
        for name, cm2 in zip(names, area):
            mine[name] = mine.get(name, 0.0) + float(cm2)

    def __bool__(self):
        return self.size > 0 if self.mark else bool(self.painted)

    def spot(self):
        """The place as Skin.decal takes one (it takes the receipt itself too)."""
        return dict(centre=self.centre, up=tuple(round(v, 4) for v in self.up))

    def __str__(self):
        said = []
        for tset, parts in self.painted.items():
            names = sorted(parts, key=lambda n: -parts[n])
            total = sum(parts.values())
            where = {"Skin": "body", "Details": "inner car", "Wheels": "tyres", "Glass": "glass"}.get(tset, tset)
            who = ", ".join(names[:MOST]) + (f" and {len(names) - MOST} more" if len(names) > MOST else "")
            said.append(f"{who} ({where}), {total:,.0f} cm²" if total >= 1 else f"{who} ({where})")
        if self.mark:
            said.append(f"laid at ({', '.join(f'{v:.0f}' for v in self.centre)}), {self.said or f'{self.size:.1f} cm wide'}"
                        + (", and its twin" if self.twin else "") if self.size > 0 else "nothing laid")
        if self.empty and not said:
            said.append(self.empty)
        line = f"{self.what}: {'; '.join(said)}" if said else self.what
        more = [f"    {n}" for n in self.notes] + [f"    {f['level'].upper() if f.get('level') == 'block' else 'found'}: {f['text']}"
                                                  for f in self.findings]
        return "\n".join([line, *more])

    __repr__ = __str__


def areas(canvas, parts, texels):
    """What texels hold on a canvas: (the part names reached, the cm² on each), by the part that covers each texel
    most and the texel's size on the car, from its flat piece's density (tool/uvmap.py). A big paint is read at every
    k-th texel (SAMPLE of them at least): within a per cent, for a tenth of the time."""
    if not len(texels):
        return [], []
    step = max(1, len(texels) // SAMPLE)
    if step > 1:
        texels = texels[::step]
    owner = canvas.owners[texels]
    on = owner >= 0
    if not on.any():
        return [], []
    cm2 = np.bincount(owner[on], weights=canvas.texel_area[texels[on]], minlength=len(parts.instances)) * step
    ids = np.flatnonzero(cm2 > 0)
    by_name = {}
    for i in ids:
        name = parts.instances[i]["name"]
        by_name[name] = by_name.get(name, 0.0) + float(cm2[i])
    return list(by_name), list(by_name.values())
