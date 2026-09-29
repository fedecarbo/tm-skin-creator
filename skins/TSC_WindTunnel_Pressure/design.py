"""TSC_WindTunnel_Pressure, concept C of TSC_WindTunnel: the car straight out of an airflow
simulation, every surface coloured by how hard the air presses on it.

The pressure field is this design's own shape (no other car uses it). Each leading edge the air
hits head-on (the nose's tip, the sidepods' front lips round the inlets, the cockpit's front rim,
the front of the engine cover, the tail's lip) is a source; the heat falls off with the distance
from it, a little further along the car than across, blurred in 3D so the bands run as clean
curves over folds. The field is cut into five hard steps of a hot ramp, with a thin dark contour
line on each step, and everything else sinks to the black-violet of low pressure.
"""

import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree

from tool import fbx, parts, shapes

DARK = "#0d0a12"  # low pressure: most of the car, the wheels and the inner car
# the hot ramp, coolest first, and where each step starts on the field (0..1)
RAMP = ["#6e0f1f", "#c62a1c", "#f07a12", "#ffc234", "#fff4c2"]
LEVELS = [0.17, 0.27, 0.40, 0.56, 0.80]
LINE = 0.3  # the contour lines, cm

# where the air hits head-on: a box (cm), the surfaces in it facing forward at least `nz`, how hot
# the source is where it faces the air most squarely (1 = the hottest point; `even`: all of it;
# `centre`: this much cooler at x ±50 than in the middle, so its bands close as lenses rather than
# run as stripes across the car) and how far its heat reaches (cm); `ahead` shortens the reach
# forward of the source, per cm (the tail's lip: its heat runs back over the tail and stops short
# of the name panel). The sidepods stay low on the ramp: bright rims round their dark inlets read as eyes
# from straight on (concept round 1, paint 1).
SOURCES = [
    dict(name="nose tip", lo=(-30, 36, 195), hi=(30, 45, 230), nz=0.7, s=1.0, L=28, parts=("nose tip",), even=True),
    dict(name="cockpit's front rim", lo=(-40, 60, 78), hi=(40, 90, 100), nz=0.15, s=0.62, L=16, parts=("cockpit surround",)),
    dict(name="sidepods' front lips", lo=(-90, 18, -20), hi=(90, 65, 60), nz=0.5, s=0.38, L=21,
         parts=("body shell", "sidepod top", "sidepod inlet")),
    dict(name="engine cover's front", lo=(-34, 76, -60), hi=(34, 90, -40), nz=0.3, s=0.54, L=11, even=True),
    dict(name="tail's lip", lo=(-55, 58, -136), hi=(55, 70, -127), nz=-1, s=0.54, L=12, parts=("tail panel", "tail corner"),
         even=True, centre=0.45, ahead=0.7),
]
ALONG = 1.4  # the heat reaches this much further along the car than across it
BLUR = 2.5  # cm: smooths the bands into clean curves
GRID = 1.0  # cm
# the game writes the player's number and name here (x, z): the field is held down over them
PANELS = [((-19, -78), (19, -62)), ((-19, -120), (19, -82))]

# the body parts the field is painted on: all but the wheel covers, the sidepod inlets (dark
# inside, the lips round them are hot), the side skirt (its ledge forward of the sidepods shows
# from above as a strip at the car's waist) and the wing's pylons under the nose (struts, dark
# as the inner car: hot, they hung under the nose like fangs from straight on)
FIELD_PARTS = ["body shell", "cockpit surround", "fuel cap", "mirror mount", "nose fin", "nose panel", "nose tip",
               "rear flank", "rear quarter panel", "sidepod top", "engine cover|part",
               "engine cover panel", "number panel", "diffuser", "diffuser strake", "tail corner", "tail panel"]

_FIELD = {}


def _samples(density=0.08):
    """Points spread evenly over the body (not the wheel covers), with their smooth normals and
    part names."""
    P = parts.load()
    m = fbx.meshes()["Skin_01"]
    tv, pos = m["tri_vertex"], m["positions"].astype(np.float64)
    names = np.array([inst["name"] for inst in P.instances])
    pn = names[P.tri_part[P.mesh_offset["Skin"]:P.mesh_offset["Skin"] + len(tv)]]
    p = pos[tv]
    area = np.linalg.norm(np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]), axis=1) / 2
    ti = np.repeat(np.arange(len(p)), np.maximum(1, np.round(area / density)).astype(int))
    rng = np.random.default_rng(7)
    r1, r2 = rng.random(len(ti)), rng.random(len(ti))
    s = np.sqrt(r1)
    bary = np.stack([1 - s, s * (1 - r2), s * r2], 1)
    nrm = (m["tri_normal"][ti] * bary[:, :, None]).sum(1)
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
    keep = ~np.isin(pn[ti], ("wheel cover disc", "wheel cover hub", "wheel cover ring"))
    return (p[ti] * bary[:, :, None]).sum(1)[keep], nrm[keep], pn[ti][keep]


def _field():
    """The pressure field on a 3D grid round the body, and its gradient, built once."""
    if _FIELD:
        return _FIELD
    pts, nrm, pn = _samples()
    lo = np.array([-112.0, -8.0, -178.0])
    shape = tuple(np.ceil((np.array([112.0, 100.0, 228.0]) - lo) / GRID).astype(int) + 1)
    axes = [lo[k] + GRID * np.arange(shape[k]) for k in range(3)]
    vox = np.stack(np.meshgrid(*axes, indexing="ij"), -1).reshape(-1, 3)
    near = np.isfinite(cKDTree(pts[::4]).query(vox, workers=-1, distance_upper_bound=5.0)[0])
    at = vox[near]
    squash = np.array([1.0, 1.0, 1.0 / ALONG])
    heat = np.zeros(len(at))
    for src in SOURCES:
        inside = np.all((pts >= src["lo"]) & (pts <= src["hi"]), 1) & (nrm[:, 2] > src["nz"])
        if "parts" in src:
            inside &= np.isin(pn, src["parts"])
        # the more squarely a source faces the air, the hotter: in steps, one search per step
        face = np.ones(inside.sum()) if src.get("even") else nrm[inside, 2] / nrm[inside, 2].max()
        face = face * (1 - src.get("centre", 0) * (pts[inside, 0] / 50) ** 2)
        hot = np.round(src["s"] * face / 0.02) * 0.02
        for h in np.unique(hot[hot > 0]):
            these = pts[inside][hot == h]
            d, k = cKDTree(these * squash).query(at * squash, workers=-1, distance_upper_bound=src["L"] * 5)
            if src.get("ahead"):
                found = np.isfinite(d)
                d[found] += src["ahead"] * np.maximum(at[found, 2] - these[k[found], 2], 0)
            heat = np.maximum(heat, np.where(np.isfinite(d), h * np.exp(-d / src["L"]), 0.0))
    for (x0, z0), (x1, z1) in PANELS:  # held down over the number and name panels, softly
        out = np.maximum.reduce([x0 - at[:, 0], at[:, 0] - x1, z0 - at[:, 2], at[:, 2] - z1])
        heat *= np.clip(out / 5.0, 0, 1) ** 2
    F = np.zeros(len(vox), np.float32)
    F[near] = heat
    F = F.reshape(shape)
    Mk = near.reshape(shape).astype(np.float32)
    sig = BLUR / GRID
    F = ndimage.gaussian_filter(F * Mk, sig) / np.maximum(ndimage.gaussian_filter(Mk, sig), 1e-6)
    _FIELD.update(F=F.astype(np.float32), grad=[g.astype(np.float32) / GRID for g in np.gradient(F)], lo=lo)
    return _FIELD


_AT = {}


def _at(pos, nrm):
    """The field at points on the car and its slope along the surface (per cm), remembered for
    the last set of points (every step's paint asks for the same texels)."""
    key = (len(pos), hash(pos[::997].tobytes()))
    if _AT.get("key") != key:
        fd = _field()
        c = ((pos.astype(np.float64) - fd["lo"]) / GRID).T
        f = ndimage.map_coordinates(fd["F"], c, order=1)
        g = np.stack([ndimage.map_coordinates(gk, c, order=1) for gk in fd["grad"]], 1)
        g -= (g * nrm).sum(1, keepdims=True) * nrm  # along the surface only
        _AT.update(key=key, f=f, slope=np.maximum(np.linalg.norm(g, axis=1), 1e-5))
    return _AT["f"], _AT["slope"]


def step_of(level):
    """Where the field is at `level` or more, with a crisp edge (the signed distance in cm)."""
    def dist(p, n):
        f, slope = _at(p, n)
        return (f - level) / slope
    return shapes.field(dist)


def contours(width=LINE):
    """A thin line along every step's edge."""
    def dist(p, n):
        f, slope = _at(p, n)
        return width / 2 - np.min([np.abs(f - lv) for lv in LEVELS], 0) / slope
    return shapes.field(dist)


def design(s):
    s.clay()
    s.step("Low pressure", "The whole car in satin black-violet, the colour of the air sliding along and away: "
           "the body, the wheels and the inner car.",
           words="I want you to come up with a concept to build a car")
    s.paint("body", "satin", colour=DARK)
    s.paint("wheels", "satin", colour=DARK)
    s.paint("inner", "satin", colour=DARK)

    s.step("The pressure field", "Where the air hits head-on the paint heats up in five hard steps, crimson, red, "
           "orange, amber and a pale yellow-white at the nose's tip, spreading back from each leading edge in "
           "smooth curves.",
           words="I like the kind of concepts that are like CMYK ends in K kind of")
    for level, colour in zip(LEVELS, RAMP):
        s.paint(FIELD_PARTS, "satin", colour=colour, zone=step_of(level))

    s.step("Contour lines", "A thin black-violet line along the edge of every step, as on an engineer's plot.",
           words="I like the kind of concepts that are like CMYK ends in K kind of")
    s.paint(FIELD_PARTS, "satin", colour=DARK, zone=contours())
