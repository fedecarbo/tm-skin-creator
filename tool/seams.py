"""The car's seams: where its pieces meet along the side, traced from the mesh. The user, 2026-10-04:
"there are seams between pieces, like the one between body shell and side skirt".

A seam is one piece's edge, where it meets the piece beside it (or stands a step proud of it): its
path on the car, a point every cm along it (the left side; the right mirrors it).

    seams.traced()                   {name: {"path": [[x, y, z], ...]}}
    seams.line("side skirt", 0.6)    a zone (tool/shapes.py): a line along the seam, 0.6 cm wide, both sides
    seams.near("rear wing", 3)       a zone: within 3 cm of it
    course.seam("side skirt")        the seam as a course (tool/course.py), for markings along it

    python -m tool.seams             trace them and print where each runs
"""

import json

import numpy as np

from tool import fbx, parts, paths

# name: the piece whose edge it is, the stretch along the car (z, cm), the band of height the edge
# runs in, and which of its edges ("lower": its lowest at each length, "upper": its highest). Picked
# from the side view (the pieces' edges every cm, 2026-10-04); the side skirt's top edge steps up
# 3.5 cm at the inlet's front corner, so it is two seams.
SEAMS = {
    "rear wing": ("tail corner", -152, -126, 45, 60, "lower"),           # its lower edge, over the rear flank
    "strake": ("rear flank", -141.5, -110.5, 20, 29.5, "lower"),        # the rear flank's edge over the diffuser strake
    "side skirt": ("side skirt", -26, 40, 24, 28, "upper"),              # its top edge, under the inlet
    "side skirt ahead": ("side skirt", 44, 72, 27, 32, "upper"),         # its top edge against the body shell
}
CACHE = paths.CACHE / "seam_paths.json"


def _edges(piece):
    """The piece's open edges on the left side: their midpoints (n, 3)."""
    P = parts.load()
    m = fbx.meshes()["Skin_01"]
    names = np.array([i["name"] for i in P.instances])
    tv = m["tri_vertex"]
    part = names[P.tri_part[P.mesh_offset["Skin"]:P.mesh_offset["Skin"] + len(tv)]]
    pos = m["positions"].astype(np.float64)
    _, wid = np.unique(np.round(pos, 1), axis=0, return_inverse=True)
    T = wid.ravel()[tv[part == piece]]
    V = np.zeros((wid.max() + 1, 3))
    V[wid.ravel()] = pos
    e = np.sort(np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), axis=1)
    u, n = np.unique(e, axis=0, return_counts=True)
    u = u[n == 1]
    a, b = V[u[:, 0]], V[u[:, 1]]
    out = []
    for t in np.linspace(0, 1, 9):  # along each edge, every cm or so
        out.append(a + t * (b - a))
    p = np.concatenate(out)
    return p[p[:, 0] > 2]


def _trace(piece, z0, z1, y0, y1, which):
    p = _edges(piece)
    p = p[(p[:, 2] >= z0 - 0.5) & (p[:, 2] <= z1 + 0.5) & (p[:, 1] >= y0) & (p[:, 1] <= y1)]
    path = []
    for z in np.arange(z0, z1 + 1e-9, 1.0):
        q = p[np.abs(p[:, 2] - z) < 0.5]
        if len(q):
            path.append(q[np.argmin(q[:, 1])] if which == "lower" else q[np.argmax(q[:, 1])])
    return {"path": np.array(path).round(2).tolist()}


def traced():
    """Every seam, traced once and cached (again when the mesh changes)."""
    mesh_t = fbx.CACHE.stat().st_mtime if fbx.CACHE.exists() else 0
    if CACHE.exists():
        doc = json.loads(CACHE.read_text())
        if doc.get("mesh") == mesh_t and doc.get("seams_def") == json.dumps(SEAMS):
            return doc["seams"]
    seams = {name: _trace(*spec) for name, spec in SEAMS.items()}
    paths.write(CACHE, json.dumps({"mesh": mesh_t, "seams_def": json.dumps(SEAMS), "seams": seams}))
    return seams


def _distance(name):
    """(pos, nrm) -> cm from the seam's path, either side of the car."""
    from scipy.spatial import cKDTree
    path = np.array(traced()[name]["path"])
    dense = []
    for a, b in zip(path, path[1:]):
        for t in np.linspace(0, 1, 11)[:-1]:
            dense.append(a + t * (b - a))
    dense.append(path[-1])
    dense = np.array(dense)
    tree = cKDTree(np.concatenate([dense, dense * [-1, 1, 1]]))
    return lambda p, n: tree.query(p.astype(np.float64))[0]


def line(name, width=0.6):
    """A line along the seam, `width` cm wide."""
    from tool import shapes
    from tool.noise import smoothstep
    d = _distance(name)
    return shapes.Zone(lambda p, n: smoothstep(-0.1, 0.1, width / 2 - d(p, n)).astype(np.float32))


def near(name, reach):
    """Within `reach` cm of the seam."""
    from tool import shapes
    from tool.noise import smoothstep
    d = _distance(name)
    return shapes.Zone(lambda p, n: smoothstep(-0.1, 0.1, reach - d(p, n)).astype(np.float32))


def main():
    for name, s in traced().items():
        z = [p[2] for p in s["path"]]
        print(f"{name:18s} z {z[0]:7.1f} to {z[-1]:7.1f}, {len(z)} points")


if __name__ == "__main__":
    main()
