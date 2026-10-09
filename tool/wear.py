"""Paint that has aged: the top coat faded, chipped, scraped, its clear coat gone, grime in its corners.

    under = s.keep()                       # what shows through: primer, bare metal
    s.paint("body", ...)                   # the top coat (a flag, a livery), any number of colours
    s.wear(under, fade=0.3, chips=0.3, scrapes=0.5, clearcoat=0.2, grime=0.3)

The looks in tool/looks.py ("faded", "chipped") wear one colour as it's painted; this wears the
whole coat as it stands, so a flag of several colours ages as one paint job. Drawn in 3D on the
baked positions, as the tears are (tool/peel.py), so nothing breaks at a seam, and every worn
edge is a hard one-texel cut, as the tears' are (soft edges read as blurred: the user,
2026-09-24).

Where it wears is read off the car's own shape, as real paint wears: the wear maps (maps), baked once per car on its
repaired surface (tool/surface.py) and cached in the work folder, nothing from which way a spot faces or how high it is.

- fade: how far the coat has washed out towards a pale, warm grey version of itself, in soft
  blotches about a third of a metre across, as much as the spot sees of the open sky.
- chips: 0..1, how chipped, in small flakes down to `under`, with a thin dark rim where the paint breaks: the share
  of the paint lost along the body's outward edges, corners and tight shoulders and round the lips where it ends (up
  to 90 %), more on thin blades and fins, none down in a crevice; on the open panels a sixtieth of it (FLAT).
- scrapes: long scuffs along the car, down to `under`, on the body's outline seen from above (its wheels left out),
  where a wall or another car touches it. 0..1, how many.
- clearcoat: the share of the paint where the clear coat has failed under the open sky: ragged
  patches, chalky and matte, paler than the paint around them.
- grime: 0..1, how dirty its corners are: a stain of road grime, streaked along the car, in what the open air
  doesn't reach and down the grooves and inner corners. A stain of its own colour, never a shadow (the game's
  shaders shade the corners themselves).

Bare metal in the chips mirrors the dark room and reads as black specks: keep `under` a light
primer.

The maps, per texel of a set's map (maps(tset, size), each (size * size,) float16, flat as the paint box's canvas):
    convex   how sharply the body bends round the texel, per cm, within REACH: + outward (an edge, a corner, a bolt
             head, a lip where the body ends: a right angle reads about 1.6 at it), - inward (a panel line's groove,
             an inner corner); a rounded edge of radius r reads 1/(2r) across it, a flat panel 0. From the bend of
             every edge of the model's triangles (tool/meshlines.py), each spread over REACH round it
    rounded  the same within ROUND: a rounded shoulder, the nose's front (a shoulder of radius 3 cm reads 0.17)
    open     the share of the open air the spot sees, 0..1, with the car, its wheels and the road in the way: 1 on
             top, about half on a side, 0 under the floor and inside an inlet (SKY rays from each point of the
             surface)
    thick    cm through the part behind the spot, inwards (a fin, a wing's blade: 1 to 3; up to THICK)
    outline  cm in from the body's outline seen from above, its wheels left out (up to THICK): 0 where a wall or
             another car touches it
Baked in about 20 s for the body at 4096, once (`python -m tool.wear` builds them and says what they hold).
"""

import time

import numpy as np

from tool import noise, paths, peel
from tool.noise import smoothstep

VERSION = 2      # the maps' cache: a change to how they're made changes it
REACH = 0.5      # cm round a texel the body's bends are read in, for `convex`; every STEP cm along each edge
STEP = 0.04
ROUND = 2.0      # the same for `rounded`, every ROUND_STEP cm, at the points of the fine surface
ROUND_STEP = 0.25
SKY = 512        # rays from each point of the surface for the open air
THICK = 50.0     # cm: the thickness and the outline are read up to this
WHEELS = ("wheel cover disc", "wheel cover hub", "wheel cover ring", "rim", "hub", "brake light", "wheel ring",
          "brake caliper")
FLAT = 1 / 60    # an open panel loses this share of what an edge loses to chips
GRIME = np.array([0.24, 0.21, 0.17], np.float32)  # road grime: a dark, warm grey


# ---- the maps ----

def maps(tset, size):
    """The set's wear maps at a size (the module's docstring), mapped from the disk: built once, again when the car's
    surface is."""
    from tool import bake, surface
    folder = paths.CACHE / f"wear{VERSION}_{tset}_{size}"
    surface.load(tset)
    if not (folder / "open.npy").exists() or (folder / "open.npy").stat().st_mtime < surface.cache_file(tset).stat().st_mtime:
        b = bake.bake(tset, size, size)
        lin = np.flatnonzero(b["tri"].reshape(-1) >= 0)
        layers = {"convex": _convex(tset, b["position"].reshape(-1, 3)[lin], b["normal"].reshape(-1, 3)[lin], REACH, STEP)}
        S = surface.load(tset)
        layers.update(zip(("rounded", "open", "thick", "outline"), S.sample(_shape(tset).astype(np.float32), size, lin).T))
        out = {}
        for k, v in layers.items():
            full = np.zeros(size * size, np.float32)
            full[lin] = v
            out[k] = full[b["near"]].astype(np.float16)  # a texel off every triangle takes its nearest one's
        bake.save(folder, out)
    return bake.load(folder)


def _convex(tset, P, N, reach, step):
    """How sharply the body bends round points P with normals N, per cm: every edge's bend, read every `step` cm along
    it, spread over `reach` with a smooth kernel that holds a rounded edge's 1/(2r); an edge facing away from the point
    (the far side of a thin panel) left out. A lip where the body ends bends outward a right angle."""
    from scipy.spatial import cKDTree
    from tool import fbx, meshlines
    e = meshlines._edges(tset)
    fn = fbx.meshes()[fbx.MESH_OF[tset]]["tri_normal"].astype(np.float64).mean(1)
    fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
    tri, sewn = e["tri"], e["sewn"]
    seg = np.concatenate([e["s1"], e["sb"]])
    bend = np.concatenate([np.radians(e["bend"]), np.where(sewn, 0.0, np.pi / 2)])
    facing = np.concatenate([fn[tri[e["h1"]]] + fn[tri[e["h2"]]], fn[tri[e["hb"]]]])
    keep = np.abs(bend) > np.radians(0.5)
    seg, bend, facing = seg[keep], bend[keep], facing[keep]
    length = np.linalg.norm(seg[:, 1] - seg[:, 0], axis=1)
    n = np.maximum(1, np.ceil(length / step).astype(np.int64))
    of = np.repeat(np.arange(len(seg)), n)
    t = (np.arange(len(of)) - np.repeat(np.cumsum(n) - n, n) + 0.5) / n[of]
    at = seg[of, 0] + (seg[of, 1] - seg[of, 0]) * t[:, None]
    weight = 0.5 * bend[of] * (length / n)[of] * 3 / (np.pi * reach ** 2)
    out = np.zeros(len(P))
    texels = cKDTree(P.astype(np.float64))
    for a in range(0, len(at), 40000):
        near = cKDTree(at[a:a + 40000]).sparse_distance_matrix(texels, reach, output_type="coo_matrix")
        i, j = near.row + a, near.col
        ok = (facing[of[i]] * N[j]).sum(1) > -0.3
        np.add.at(out, j[ok], (weight[i] * (1 - (near.data / reach) ** 2) ** 2)[ok])
    return out


def _shape(tset):
    """`rounded`, `open`, `thick` and `outline` at the points of the set's fine surface: (n, 4)."""
    import igl.embree
    from scipy.spatial import ConvexHull
    from tool import fbx, parts, surface
    S = surface.load(tset)
    V, F = S.FV.astype(np.float64), S.FF.astype(np.int64)
    area = np.linalg.norm(np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]), axis=1)
    N = np.zeros_like(V)
    for k in range(3):
        np.add.at(N, F[:, k], S.fine_facing() * area[:, None])
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    ms = fbx.meshes()
    soup = lambda keys: np.concatenate([ms[k]["positions"][ms[k]["tri_vertex"]].reshape(-1, 3) for k in keys]).astype(np.float64)
    car = soup([k for k in ms if not k.startswith("Glass")])
    ground = float(car[:, 1].min())  # the tyres stand on the road
    road = np.array([[-1e3, ground, -1e3], [1e3, ground, -1e3], [1e3, ground, 1e3], [-1e3, ground, 1e3]])
    Vs = np.vstack([car, road])
    Fs = np.vstack([np.arange(len(car)).reshape(-1, 3), len(car) + np.array([[0, 2, 1], [0, 3, 2]])])
    open_ = 1 - igl.embree.ambient_occlusion(Vs, Fs, V + 0.02 * N, N, SKY)
    own = soup([fbx.MESH_OF[tset]])
    thick = np.fmin(igl.embree.shape_diameter_function(own, np.arange(len(own)).reshape(-1, 3), V - 0.02 * N, N, 64), THICK)  # nan: nothing behind
    names = np.array([inst["name"] for inst in parts.load().instances])
    body = np.concatenate([(lambda s: s.V[s.F[~np.isin(names[s.part], WHEELS)]].reshape(-1, 3))(surface.load(k))
                           for k in ("Skin", "Details")])[:, [0, 2]]
    hull = ConvexHull(body).equations  # seen from above: x and z
    outline = np.minimum(-(V[:, [0, 2]] @ hull[:, :2].T + hull[:, 2]).max(1), THICK)
    return np.stack([_convex(tset, V, N, ROUND, ROUND_STEP), open_, thick, np.maximum(outline, 0)], 1)


# ---- the wear ----

def _cut(H, idx, c):
    """Where a field H (> 0 inside) cuts through: 0..1 with a one-texel edge, and cm from the edge."""
    g, pitch = peel.gradient(H, idx, c.pos, c.w, c.w * c.h)
    sd = H / np.maximum(g, 1e-6)
    return np.clip(0.5 + sd / pitch, 0, 1), sd, pitch


def _show(c, idx, under, hole, rim=None):
    """Let `under` through where hole is 1; rim darkens it along the break."""
    for k in ("colour", "rough", "metal", "coat"):
        layer = getattr(c, k)
        if layer is None:
            continue
        u = under[k][idx]
        if k == "colour":
            if rim is not None:
                u = u * (1 - 0.45 * rim)[:, None]
            layer[idx] = layer[idx] * (1 - hole[:, None]) + u * hole[:, None]
        else:
            layer[idx] = layer[idx] * (1 - hole) + u * hole


def wear(skin, under, where="body", fade=0.3, chips=0.3, scrapes=0.0, clearcoat=0.0, grime=0.0, chip_size=1.6, seed=0):
    t0 = time.time()
    tset = under.get("set", "Skin")
    c = skin.canvas(tset)
    idx, m = skin._mask(tset, skin._ids(where).get(tset, []), None, c)
    pos = c.pos[idx]
    M = {k: v[idx].astype(np.float32) for k, v in maps(tset, c.w).items()}
    sky = M["open"]
    said = [f"faded up to {fade:.0%}"]
    share = lambda w: float((w * m).sum() / max(m.sum(), 1))

    def pale(col, t):
        grey = col.mean(1, keepdims=True)
        target = 0.55 * (0.6 * col + 0.4 * grey) + 0.45 * np.array([0.88, 0.85, 0.8], np.float32)
        return col * (1 - t[:, None]) + target * t[:, None]

    if fade > 0:
        blotch = noise.fbm(pos / 60.0, 3, seed + 31)
        t = np.clip(fade * (0.35 + 0.9 * blotch) * (0.2 + 0.8 * sky), 0, 0.85)
        c.colour[idx] = pale(c.colour[idx], t)
        c.rough[idx] = np.clip(c.rough[idx] + 0.25 * t, 0, 1)
    if clearcoat > 0:  # a few big ragged patches where the sky beats on it, chalky and matte
        # (at a fifth of the faces, 20 cm across, they read as camouflage: 2026-09-26)
        f = noise.fbm(pos / 34.0, 3, seed + 41) + 0.12 * (peel.facets(pos / 5.0, seed + 43, 2) - 0.5) \
            + 0.45 * (smoothstep(0.55, 0.9, sky) - 1)
        hole, sd, pitch = _cut(f - float(np.quantile(f, 1 - clearcoat)), idx, c)
        lift = np.clip(0.5 + (0.12 - sd) / pitch, 0, 1) * hole  # the lifting edge, 1.2 mm, lighter
        chalk = 0.35 + 0.25 * noise.fbm(pos / 0.9, 2, seed + 45)  # mottled, not flat
        col = pale(c.colour[idx], chalk * hole)
        c.colour[idx] = np.clip(col + 0.2 * lift[:, None], 0, 1)
        c.rough[idx] = c.rough[idx] * (1 - hole) + 0.95 * hole
        if c.coat is not None:
            c.coat[idx] = c.coat[idx] * (1 - hole) + hole  # no varnish left
        said.append(f"{share(hole):.0%} clear coat gone")
    if scrapes > 0:  # long scuffs along the car where walls and other cars touch it
        touch = smoothstep(2.5, 0.5, M["outline"]) * smoothstep(0.1, 0.3, sky)
        where_hit = smoothstep(0.62 - 0.25 * scrapes, 0.7 - 0.25 * scrapes, noise.fbm(pos / 50.0, 2, seed + 51))
        streak = noise.fbm(pos * np.array([0.0, 1.1, 0.03], np.float32), 3, seed + 53)
        gate = smoothstep(0.3, 0.6, touch * where_hit)
        hole, sd, pitch = _cut(streak - (0.63 - 0.08 * scrapes) - 0.6 * (1 - gate), idx, c)
        _show(c, idx, under, hole)
        said.append(f"{share(hole):.1%} scraped")
    if chips > 0:  # along the outward edges and lips, most on thin blades, never down in a crevice; a few anywhere
        edge = np.maximum(smoothstep(0.25, 1.2, M["convex"]), smoothstep(0.06, 0.3, M["rounded"]))
        edge *= 1 + 0.6 * smoothstep(4.0, 1.0, M["thick"])
        e = np.clip(edge, 0, 1) * smoothstep(0.05, 0.3, sky)
        f = noise.fbm(pos / chip_size, 3, seed + 7) + 0.12 * (peel.facets(pos / (chip_size * 0.6), seed + 9, 2) - 0.5)
        worn = np.clip(chips * (FLAT + (1 - FLAT) * e), 0, 0.9)  # the share each spot loses, by how it bends
        levels = np.linspace(0, 1, 257)
        hole, sd, pitch = _cut(f - np.interp(1 - worn, levels, np.quantile(f[::7], levels)), idx, c)
        rim = np.clip(0.5 + (0.06 - sd) / pitch, 0, 1) * hole  # the broken paint's edge, 0.6 mm
        _show(c, idx, under, hole, rim)
        lost = lambda on: float((hole * m)[on].sum() / max(m[on].sum(), 1))
        said.append(f"chipped: {lost(e > 0.5):.0%} of the edges, {lost(e < 0.05):.1%} of the open panels")
    if grime > 0:  # a stain where the air doesn't reach and down the grooves, streaked along the car
        corner = np.maximum(smoothstep(0.35, 0.05, sky), smoothstep(-0.15, -0.8, M["convex"]))
        streak = noise.fbm(pos * np.array([1 / 6, 1 / 8, 1 / 40], np.float32), 4, seed + 61)
        w = np.clip(grime * 1.4 * corner * smoothstep(0.35, 0.65, 0.6 * streak + 0.4 * noise.fbm(pos / 12, 3, seed + 63)), 0, 0.9)
        c.colour[idx] = c.colour[idx] * (1 - w[:, None]) + GRIME * w[:, None]
        c.rough[idx] = np.clip(c.rough[idx] + 0.5 * w, 0, 1)
        if c.coat is not None:
            c.coat[idx] = np.maximum(c.coat[idx], w)  # dull under the dirt
        said.append(f"grime on {share(w > 0.1):.0%}")
    c.touched[idx] = True
    skin.notes.append(f"wear on {where}: {', '.join(said)} ({time.time() - t0:.0f} s)")


def main():
    from tool import bake
    for tset in ("Skin", "Details"):
        t = time.time()
        M = maps(tset, 4096)
        on = bake.bake(tset, 4096, 4096)["tri"].reshape(-1) >= 0
        said = ", ".join(f"{k} {np.quantile(v[on], 0.05):.2f} to {np.quantile(v[on], 0.95):.2f}" for k, v in M.items())
        print(f"{tset} at 4096 ({time.time() - t:.0f} s), from the 5th to the 95th percentile: {said}")


if __name__ == "__main__":
    main()
