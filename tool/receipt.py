"""A receipt: what one call of the paint box did, in a line, and where it landed. Every verb of `paintbox.Skin` returns
one, and `tool.skin show` and `read` print each as the paint goes, so a design is read back call by call: what it
painted and how much; its landing on the body (the stretch of the car it lies on, z nose to tail with the car's
stations named, y, x and which side, and the way it faces), read off its texels' places; where a mark landed; what
it refused and any accident it found.

    r = s.paint("body", "gloss red")       str(r): "gloss red on body: 31 parts of the body, 58,900 cm²", then its
                                           landing ("on the body: z 215 to -162, ..., facing up"), then its notes
    badge = s.mark("rear flank", "gloss", marks.disc(), size=12)
    badge.centre, badge.size, badge.twin   where it landed (cm), its width as laid (0: nothing laid), its mirror image's
    s.decal("7", badge, ...)               a receipt is a place for the next graphic
"""

import numpy as np

MOST = 4  # parts named in a line before "and n more"
SAMPLE = 400_000  # texels a big paint's area and landing are read from
STATION = 12.0  # cm: the car's station this near a z names it
FACE = 0.5      # a texel's normal along an axis this much faces that way ...
FACING = 0.3    # ... and a landing faces a way when this share of its texels do
FACES = ("up", "down", "left", "right", "forward", "back")
AXES = ((1, 1), (1, -1), (0, 1), (0, -1), (2, 1), (2, -1))


def _n(v):
    return f"{round(float(v)) + 0.0:.0f}"  # never "-0"


def station(z):
    """The car's station nearest a z along it (carmap.STATIONS: "the nose", "the deck, the engine cover panel"), within
    STATION cm; else None."""
    from tool import carmap
    stations = np.array([s for s, _ in carmap.STATIONS], float)
    k = int(np.argmin(np.abs(stations - z)))
    return carmap.STATIONS[k][1] if abs(stations[k] - z) <= STATION else None


class Landing:
    """Where a call's paint lies on the body, from its texels' places: the box it fills and the ways it faces."""

    def __init__(self):
        self.lo = self.hi = None
        self.faces = np.zeros(len(FACES))  # texels facing each of FACES
        self.n = 0

    def add(self, pos, nrm):
        lo, hi = pos.min(0), pos.max(0)
        self.lo = lo if self.lo is None else np.minimum(self.lo, lo)
        self.hi = hi if self.hi is None else np.maximum(self.hi, hi)
        n = nrm / np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-9)
        for k, (axis, sign) in enumerate(AXES):
            self.faces[k] += int((n[:, axis] * sign > FACE).sum())
        self.n += len(pos)

    def side(self):
        lo, hi = self.lo, self.hi
        return ("the left side" if lo[0] > 1 else "the right side" if hi[0] < -1
                else "both sides" if lo[0] < -1 and hi[0] > 1 else "the middle")

    def facing(self):
        return [w for k, w in enumerate(FACES) if self.faces[k] >= FACING * self.n]

    def __str__(self):
        lo, hi, faces = self.lo, self.hi, self.facing()
        a, b = station(round(float(hi[2]))), station(round(float(lo[2])))
        where = f" ({a} to {b})" if a and b and a != b else f" ({a or b})" if a or b else ""
        return (f"z {_n(hi[2])} to {_n(lo[2])}{where}, y {_n(lo[1])} to {_n(hi[1])}, x {_n(lo[0])} to {_n(hi[0])} ({self.side()})"
                + (f", facing {', '.join(faces)}" if faces else ""))

    def doc(self):
        """As a concept's page reads it (tool/view.py's steps.json): the box in cm, z nose to tail, the car's stations
        at its two ends (a name each, or None), the side, the ways it faces, and all of it in words."""
        def span(a, b):
            return [round(float(a), 1), round(float(b), 1)]
        lo, hi = self.lo, self.hi
        return {"z": span(hi[2], lo[2]), "y": span(lo[1], hi[1]), "x": span(lo[0], hi[0]), "side": self.side(),
                "stations": [station(round(float(z))) for z in (hi[2], lo[2])], "faces": self.facing(), "words": str(self)}


class Receipt:
    def __init__(self, what, step):
        self.what, self.step = what, step
        self.k = -1  # the step it lies in (Skin.steps), once it ends: a step a call opens itself (the clay's) is its own
        self.across = False  # the design says it crosses the car's parts on purpose (across=True): meant, not an accident
        self.painted = {}   # texture set -> {part name: cm²}
        self.landing = None  # where it lies on the body (Landing), once paint lands there
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

    def land(self, pos, nrm):
        """Paint laid on the body at these places, facing these ways: its landing."""
        if self.landing is None:
            self.landing = Landing()
        self.landing.add(pos, nrm)

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
        more = [f"    on the body: {self.landing}"] if self.landing else []
        more += [f"    {n}" for n in self.notes] + [f"    {f['level'].upper() if f.get('level') == 'block' else 'found'}: {f['text']}"
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
