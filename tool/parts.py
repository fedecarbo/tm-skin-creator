"""The named parts of the car: which triangle belongs to which part, and texel masks for painting.

    python -m tool.parts            resolve the names, write car/parts.json, print the tree
    python -m tool.parts --review   also render build/parts_review.png, the car coloured by part

Names come from tool/naming.py. Pieces and groups come from tool/segment.py. Every triangle
ends up in exactly one part instance: a name plus a side (left, right, centre) and, for the
wheel-related assemblies, an end (front, rear). Pieces nobody named join the nearest named
piece of their mesh. Each part sits in an assembly ("sidepod") and in a group, the map it's
painted on (body, details, tyres, glass): a group's name picks all its parts too, unless a part
or an assembly has that name.

    p = parts.load()
    p.mask(bake, "Details", "brake caliper")                  every caliper's texels
    p.mask(bake, "Details", "brake caliper", side="left", end="rear")
    p.mask(bake, "Skin", "sidepod")                            a whole assembly
    p.select("details")                                        a whole group (a map)
"""

import argparse
import json

import numpy as np
from scipy.spatial import cKDTree

from tool import naming, paths, segment
from tool.shapes import WHEEL_Y, WHEEL_Z  # the wheel centres, fitted to the tyres and covers

PARTS_JSON = paths.REPO / "car" / "parts.json"
CACHE = paths.CACHE / "parts.npz"
ENDED = {"rims and brakes", "tyre", "wheel cover", "front suspension", "rear suspension"}  # assemblies split front/rear
MESH_NAME = {"Skin": "Skin_01", "Details": "Details_01", "Wheels": "Wheels_01", "Glass": "Glass_01"}
MESH_TRIS = {"Skin": 27184, "Details": 65246, "Wheels": 4896, "Glass": 2239}


# ---- Rules: geometry that picks triangles a name can't ----


def _cover_radius(seg):
    """For Skin triangles over the wheels (|x| > 88): distance from the nearest wheel axle."""
    c = seg["centroid"]
    zc = np.where(c[:, 2] > 0, WHEEL_Z[0], WHEEL_Z[1])
    return np.hypot(c[:, 1] - WHEEL_Y, c[:, 2] - zc)


def _cover_pieces(seg, lo, hi):
    """Skin pieces over the wheels whose mean radius from the axle is in [lo, hi)."""
    r = _cover_radius(seg)
    cover = (seg["mesh"] == 0) & (np.abs(seg["centroid"][:, 0]) > 88)
    n = len(seg["piece_tris"])
    mean_r = np.bincount(seg["piece"][cover], weights=r[cover], minlength=n) / np.maximum(np.bincount(seg["piece"][cover], minlength=n), 1)
    ok = np.zeros(n, bool)
    ok[np.unique(seg["piece"][cover])] = True
    ok &= (mean_r >= lo) & (mean_r < hi)
    return ok[seg["piece"]] & cover


def _tub(seg):
    return seg["piece"] == 21


def _floor_piece_z(seg):
    return seg["piece_centroid"][seg["piece"], 2]


def _floor(seg):
    return seg["group"] == 55


def _floor_width(seg):
    box = seg["piece_hi"] - seg["piece_lo"]
    return box[seg["piece"], 0]


# Cuts: a smooth surface split by a distance field. base picks the triangles; field(position,
# normal) is positive inside the cut, in cm, so the border can be anti-aliased over one texel
# (coverage 0..1). Triangles are cut by their centroid, for the viewer. Only for surfaces with
# no fold of their own: a border that a fold gives is always cleaner than one a field gives.
def _tyre_radius(p):
    zc = np.where(p[:, 2] > 30, WHEEL_Z[0], WHEEL_Z[1])
    return np.hypot(p[:, 1] - WHEEL_Y, p[:, 2] - zc)


TREAD_RADIUS = 34.5  # cm from the axle: the tyre's crown starts here, the sidewalls are inside
CUTS = {
    "chassis_nose": ("chassis", lambda p, n: p[:, 2] - 95),
    "chassis_cockpit": ("chassis", lambda p, n: np.minimum(95 - p[:, 2], p[:, 2] + 45)),
    "chassis_engine": ("chassis", lambda p, n: -45 - p[:, 2]),
    "tyre_sidewall": ("tyre", lambda p, n: TREAD_RADIUS - _tyre_radius(p)),
    "tyre_tread": ("tyre", lambda p, n: _tyre_radius(p) - TREAD_RADIUS),
}
BASES = {"chassis": lambda s: s["group"] == 134, "tyre": lambda s: s["mesh"] == 2}


def _cut(name):
    base, field = CUTS[name]
    return lambda s: BASES[base](s) & (field(s["centroid"], s["normal"]) > 0)


RULES = {
    **{name: _cut(name) for name in CUTS},
    "cover_ring": lambda s: _cover_pieces(s, 19, 99),
    "cover_disc": lambda s: _cover_pieces(s, 10, 19),
    "cover_hub": lambda s: _cover_pieces(s, 0, 10),
    "floor_wing": lambda s: _floor(s) & (_floor_piece_z(s) > 120),
    "floor_diffuser": lambda s: _floor(s) & (_floor_piece_z(s) < -100),
    "floor_plank": lambda s: _floor(s) & (_floor_piece_z(s) >= -100) & (_floor_piece_z(s) <= 120) & (_floor_width(s) < 50),
    "floor_main": lambda s: _floor(s) & (_floor_piece_z(s) >= -100) & (_floor_piece_z(s) <= 120) & (_floor_width(s) >= 50),
    "glass_digits": lambda s: (s["mesh"] == 3) & (s["piece_tris"][s["piece"]] < 15) & (s["centroid"][:, 1] > 80),
}


# ---- Resolving names to triangles ----


def _side_of(x):
    return np.where(x > 1, "left", np.where(x < -1, "right", "centre"))


def resolve(seg):
    """Returns (tri_part, instances): the instance id of every triangle, and the instance table."""
    T = len(seg["mesh"])
    name_of = np.full(T, -1)  # index into naming.PARTS
    twin = seg["piece_twin"]
    for k, part in enumerate(naming.PARTS):
        sel = np.zeros(T, bool)
        pieces = list(part.get("piece", []))
        for g in part.get("group", []):
            pieces += list(np.unique(seg["piece"][seg["group"] == g]))
        pieces += [twin[p] for p in pieces if twin[p] >= 0]
        if pieces:
            sel |= np.isin(seg["piece"], pieces)
        if "rule" in part:
            sel |= RULES[part["rule"]](seg)
        taken = sel & (name_of >= 0)
        if taken.any():  # the first name wins; say so, it usually means a twin was guessed wrong
            other = naming.PARTS[name_of[taken][0]]["name"]
            print(f"note: {part['name']}: {taken.sum()} triangles were already {other}, left as {other}")
        name_of[sel & (name_of < 0)] = k
    # unnamed pieces join the nearest named piece of the same mesh
    for mesh in range(4):
        named = (name_of >= 0) & (seg["mesh"] == mesh)
        lost = (name_of < 0) & (seg["mesh"] == mesh)
        if not lost.any():
            continue
        tree = cKDTree(seg["centroid"][named])
        named_idx = np.flatnonzero(named)
        for p in np.unique(seg["piece"][lost]):
            tris = np.flatnonzero(seg["piece"] == p)
            _, nearest = tree.query(seg["centroid"][tris])
            # the named triangle most often nearest to this piece's triangles
            k = np.bincount(name_of[named_idx[nearest]]).argmax()
            name_of[tris] = k
    # sides and ends: per triangle for rule parts; per piece otherwise, and a piece only has a
    # side when it has a mirrored twin (a piece across the middle is "centre")
    c = seg["centroid"]
    pc = seg["piece_centroid"][seg["piece"]]
    is_rule = np.array(["rule" in p for p in naming.PARTS])[name_of]
    has_twin = twin[seg["piece"]] >= 0
    x = np.where(is_rule, c[:, 0], np.where(has_twin, pc[:, 0], 0))
    z = np.where(is_rule, c[:, 2], pc[:, 2])
    side = _side_of(x)
    parent = np.array([p["parent"] for p in naming.PARTS])[name_of]
    end = np.where(np.isin(parent, list(ENDED)), np.where(z > 30, "front", np.where(z < -30, "rear", "middle")), "")
    keys = np.stack([name_of.astype(str), side, end], 1)
    uniq, inv = np.unique(keys, axis=0, return_inverse=True)
    instances = []
    for u in uniq:
        p = naming.PARTS[int(u[0])]
        inst = {"name": p["name"], "parent": p["parent"], "side": u[1], "end": u[2]}
        if p.get("rule") in CUTS:
            inst["cut"] = p["rule"]
        instances.append(inst)
    tri_part = inv.reshape(-1).astype(np.int32)
    for i, inst in enumerate(instances):
        sel = tri_part == i
        inst["mesh"] = segment.SETS[int(seg["mesh"][sel][0])]
        inst["group"] = naming.GROUP_OF_SET[inst["mesh"]]
        inst["tris"] = int(sel.sum())
        inst["area_cm2"] = round(float(seg["area"][sel].sum()), 1)
        inst["pieces"] = [int(v) for v in np.unique(seg["piece"][sel])]
    # order: by assembly, then name, then side, then end
    order_of = {a: i for i, (a, _) in enumerate(naming.ASSEMBLIES)}
    order = sorted(range(len(instances)), key=lambda i: (order_of[instances[i]["parent"]], instances[i]["name"],
                                                          instances[i]["end"], instances[i]["side"]))
    remap = np.empty(len(order), np.int32)
    remap[order] = np.arange(len(order))
    return remap[tri_part], [instances[i] for i in order]


BAKE_SIZE = {"Skin": (2048, 2048), "Details": (2048, 2048), "Wheels": (512, 1024), "Glass": (1024, 1024)}


STATS_CACHE = paths.CACHE / "parts_stats.json"


def _texel_stats(tri_part, instances, mesh_offset):
    """Per instance: how many texels it owns, and how many of them other triangles also cover
    (its mirror twin, or repeats such as the four wheel covers): a colour there lands on all.
    Slow (a rasterisation per part), so results are cached by the instance's pieces."""
    from tool import bake
    cache = json.loads(STATS_CACHE.read_text()) if STATS_CACHE.exists() else {}
    p = Parts(tri_part, instances, mesh_offset)
    for tset, (w, h) in BAKE_SIZE.items():
        b = None
        for i, inst in enumerate(instances):
            if inst["mesh"] != tset:
                continue
            key = f"{tset}|{inst['name']}|{inst['side']}|{inst['end']}|{inst['tris']}|{hash(tuple(inst['pieces']))}"
            if key not in cache:
                b = b or bake.bake(tset, w, h)
                m = p.mask(b, tset, ids=[i])
                n = int(m.sum())
                cache[key] = [n, round(float((b["count"][m] > 1).mean()), 2) if n else 0.0]
            inst["texels"], inst["shared"] = cache[key]
    STATS_CACHE.parent.mkdir(parents=True, exist_ok=True)
    STATS_CACHE.write_text(json.dumps(cache))
    return instances


def build(write=True):
    seg = segment.segments()
    tri_part, instances = resolve(seg)
    mesh_offset = {name: int(np.flatnonzero(seg["mesh"] == i)[0]) for i, name in enumerate(segment.SETS)}
    instances = _texel_stats(tri_part, instances, mesh_offset)
    if write:
        PARTS_JSON.parent.mkdir(exist_ok=True)
        doc = {
            "about": "Every part of the CarSport, named by eye from the model (tool/naming.py). "
                     "Sides: left is +x, the driver's left. Ids are piece ids from tool/segment.py. "
                     "texels: the part's texels at 2048 (Wheels 512x1024, Glass 1024); shared: the share "
                     "of them that other parts (the mirror twin, repeats) also use: a colour there lands on all of them. "
                     "The tree: group > assembly (parent) > part.",
            "groups": [{"name": g, "about": d} for g, d in naming.GROUPS],
            "assemblies": [{"name": a, "about": d} for a, d in naming.ASSEMBLIES],
            "parts": [{"id": i, **inst} for i, inst in enumerate(instances)],
        }
        PARTS_JSON.write_text(json.dumps(doc, indent=1))
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(CACHE, tri_part=tri_part, mesh=seg["mesh"], **{f"offset_{k}": v for k, v in mesh_offset.items()})
    return tri_part, instances, mesh_offset


class Parts:
    def __init__(self, tri_part, instances, mesh_offset):
        self.tri_part, self.instances, self.mesh_offset = tri_part, instances, mesh_offset
        self.by_name = {}
        by_part = {n for inst in instances for n in (inst["name"], inst["parent"])}
        for i, inst in enumerate(instances):
            self.by_name.setdefault(inst["name"], []).append(i)
            self.by_name.setdefault(inst["parent"], []).append(i)
        for i, inst in enumerate(instances):  # a group by its name, where no part or assembly has it
            if inst["group"] not in by_part:
                self.by_name.setdefault(inst["group"], []).append(i)

    def names(self):
        return sorted(set(i["name"] for i in self.instances))

    def select(self, name, side=None, end=None, exact=False):
        """Instance ids matching a part, assembly or group name, narrowed by side ('left'/'right'/
        'centre') and end ('front'/'rear'). exact: only parts called that, not the assembly of the
        same name ("floor", "front wing" and "engine cover" are both)."""
        if name not in self.by_name:
            raise KeyError(f"no part called {name!r}; see car/parts.json")
        ids = sorted(set(self.by_name[name]))
        if exact:
            ids = [i for i in ids if self.instances[i]["name"] == name]
        if side:
            ids = [i for i in ids if self.instances[i]["side"] == side]
        if end:
            ids = [i for i in ids if self.instances[i]["end"] == end]
        return ids

    # ---- a part in words: the Lab's rooms show these, and copies line() for Claude ----

    def tag(self, i):
        """"front left", "right", or "" for a part on the centre line."""
        inst = self.instances[i]
        return " ".join(b for b in (inst["end"], inst["side"] if inst["side"] != "centre" else "") if b)

    def label(self, i):
        """"brake caliper (front left)", as the viewer names a part."""
        tag = self.tag(i)
        return f"{self.instances[i]['name']} ({tag})" if tag else self.instances[i]["name"]

    def token(self, i):
        """The shortest phrase that picks exactly this part in the paint box: "sidepod top|left",
        "brake caliper|left|front", "floor|left|part" (|part: the part, not its assembly)."""
        inst = self.instances[i]
        bits = [inst["name"]]
        exact = inst["name"] in {o[k] for o in self.instances for k in ("parent", "group")}
        if len(self.select(inst["name"], exact=exact)) > 1:
            bits.append(inst["side"])
            if len(self.select(inst["name"], side=inst["side"], exact=exact)) > 1:
                bits.append(inst["end"])
        if exact and len(self.select(inst["name"])) > len(self.select(inst["name"], exact=True)):
            bits.append("part")
        return "|".join(bits)

    def share_words(self, i, twins):
        """Whose paint part i shares, from coverage.twins(): "its own paint", or "paint shared
        with sidepod frame (right)", with the share when it's partial ("78% of its paint ...")."""
        texels, shared, others = twins.get(i, (0, 0, {}))
        if not others or shared < 0.01 * texels:
            return "its own paint"
        groups = {}
        for j in sorted(others, key=lambda j: (-others[j], j)):  # the biggest sharers first
            groups.setdefault(self.instances[j]["name"], []).append(self.tag(j))
        who = [name + (f" ({', '.join(t for t in tags if t)})" if any(tags) else "") for name, tags in groups.items()]
        if len(who) > 4:
            who = who[:3] + [f"{len(who) - 3} more parts"]
        who = ", ".join(who[:-1]) + " and " + who[-1] if len(who) > 1 else who[0]
        share = shared / max(texels, 1)
        return ("paint shared with " if share >= 0.95 else f"{round(share * 100)}% of its paint shared with ") + who

    def line(self, i, twins):
        """The line the Lab copies for Claude: "sidepod top|left (Skin map, its own paint)"."""
        return f"{self.token(i)} ({self.instances[i]['mesh']} map, {self.share_words(i, twins)})"

    def tri_mask(self, texture_set, name, side=None, end=None, ids=None):
        """Boolean over the local triangles of one mesh."""
        ids = self.select(name, side, end) if ids is None else ids
        off = self.mesh_offset[texture_set]
        n = MESH_TRIS[texture_set]
        return np.isin(self.tri_part[off:off + n], ids)

    def _rasterise(self, bake, texture_set, tri_mask, samples=1):
        """The texels the triangles cover. samples=2 takes 2x2 samples per texel and returns
        the covered share 0..1, so a seam between two parts that share a texel is mixed by
        area instead of decided by the texel's centre."""
        from tool import fbx, raster
        h, w = bake["tri"].shape
        if not hasattr(self, "_meshes"):
            self._meshes = fbx.meshes()
        uv = self._meshes[MESH_NAME[texture_set]]["tri_uv"][tri_mask].astype(np.float64)
        xy = np.stack([uv[..., 0] * w, (1 - uv[..., 1]) * h], -1)
        if samples == 1:
            return raster.rasterise(xy, w, h)[0] >= 0
        offsets = (np.arange(samples) + 0.5) / samples - 0.5
        cov = np.zeros((h, w), np.float32)
        for dx in offsets:
            for dy in offsets:
                cov += raster.rasterise(xy - [dx, dy], w, h)[0] >= 0
        return cov / (samples * samples)

    def _cut_coverage(self, bake, texture_set, cut):
        """Coverage 0..1 of a cut (both sides, both ends): the field's sign, anti-aliased over
        one texel using the field's change between neighbouring texels."""
        base, field = CUTS[cut]
        if not hasattr(self, "_seg"):
            self._seg = segment.segments()
        self._cuts = getattr(self, "_cuts", {})
        key = (texture_set, cut, bake["tri"].shape)
        if key in self._cuts:
            return self._cuts[key]
        base_key = (texture_set, base, bake["tri"].shape)
        if base_key not in self._cuts:
            off = self.mesh_offset[texture_set]
            base_tris = BASES[base](self._seg)[off:off + MESH_TRIS[texture_set]]
            self._cuts[base_key] = self._rasterise(bake, texture_set, base_tris)
        on = self._cuts[base_key]
        f = np.zeros(on.shape, np.float32)
        f[on] = field(bake["position"][on], bake["normal"][on])
        # how much the field changes per texel: the larger of the two neighbour differences,
        # where both neighbours are on the surface; elsewhere a typical value
        gx = np.abs(np.diff(f, axis=1, append=0))
        gy = np.abs(np.diff(f, axis=0, append=0))
        g = np.maximum(gx, gy)
        valid = on & np.roll(on, -1, 1) & np.roll(on, -1, 0)
        typical = float(np.median(g[valid & (g > 0)])) if (valid & (g > 0)).any() else 1e-3
        g = np.where(valid, np.maximum(g, 1e-6), typical)
        cov = np.clip(0.5 + f / g, 0, 1).astype(np.float32)
        cov[~on] = 0
        self._cuts[key] = cov
        return cov

    def coverage(self, bake, texture_set, name=None, side=None, end=None, ids=None):
        """Float texel coverage (h, w) 0..1 of a part: 1 inside, 0 outside, in between along a
        cut's border (anti-aliased). Parts bounded by mesh edges are 0 or 1; the padding
        between UV islands takes care of their edges."""
        ids = self.select(name, side, end) if ids is None else ids
        plain = [i for i in ids if "cut" not in self.instances[i]]
        out = self._rasterise(bake, texture_set, self.tri_mask(texture_set, None, ids=plain), samples=2) \
            if plain else np.zeros(bake["tri"].shape, np.float32)
        for i in ids:
            inst = self.instances[i]
            if "cut" not in inst or inst["mesh"] != texture_set:
                continue
            cov = self._cut_coverage(bake, texture_set, inst["cut"])
            m = cov > 0
            # narrow to this side and end, except on texels several triangles share (the four
            # tyres, say): those belong to every instance, and one colour lands on all of them
            pos, own = bake["position"][m], bake["count"][m] <= 1
            ok = np.ones(int(m.sum()), bool)
            if inst["side"] == "left":
                ok &= pos[:, 0] > 1
            elif inst["side"] == "right":
                ok &= pos[:, 0] < -1
            elif inst["side"] == "centre" and any(self.instances[j].get("cut") == inst["cut"] and
                                                  self.instances[j]["side"] != "centre" for j in range(len(self.instances))):
                ok &= np.abs(pos[:, 0]) <= 1
            if inst["end"] == "front":
                ok &= pos[:, 2] > 30
            elif inst["end"] == "rear":
                ok &= pos[:, 2] < -30
            keep = np.zeros(m.shape, bool)
            keep[m] = ok | ~own
            out = np.maximum(out, np.where(keep, cov, 0))
        return out

    def local_bake(self, texture_set, width, height, name=None, side=None, end=None, ids=None):
        """A bake (tri, position, normal) of one part's own triangles only. The main bake's
        position on a shared texel may come from any part that covers it; here it always comes
        from this part (its mirror twin at worst, so |x| and the rest agree)."""
        from tool import fbx, raster
        ids = self.select(name, side, end) if ids is None else ids
        if not hasattr(self, "_meshes"):
            self._meshes = fbx.meshes()
        m = self._meshes[MESH_NAME[texture_set]]
        tris = self.tri_mask(texture_set, None, ids=ids)
        uv = m["tri_uv"][tris].astype(np.float64)
        xy = np.stack([uv[..., 0] * width, (1 - uv[..., 1]) * height], -1)
        tri, bary = raster.rasterise(xy, width, height)
        position = raster.interpolate(tri, bary, m["positions"][m["tri_vertex"][tris]])
        normal = raster.interpolate(tri, bary, m["tri_normal"][tris])
        normal /= np.maximum(np.linalg.norm(normal, axis=-1, keepdims=True), 1e-9)
        return {"tri": tri, "position": position, "normal": normal.astype(np.float32)}

    def mask(self, bake, texture_set, name=None, side=None, end=None, ids=None):
        """Boolean texel mask (h, w): every texel the part covers by at least half. Shared texels
        (bake["count"] > 1) count for every part on them. See coverage() for soft edges."""
        return self.coverage(bake, texture_set, name, side, end, ids) >= 0.5


def load():
    if not CACHE.exists() or CACHE.stat().st_mtime < max(p.stat().st_mtime for p in (
            paths.REPO / "tool" / "naming.py", paths.REPO / "tool" / "parts.py", segment.CACHE)):
        tri_part, instances, mesh_offset = build()
    else:
        d = np.load(CACHE)
        tri_part = d["tri_part"]
        mesh_offset = {k[len("offset_"):]: int(d[k]) for k in d.files if k.startswith("offset_")}
        instances = json.loads(PARTS_JSON.read_text())["parts"]
    return Parts(tri_part, instances, mesh_offset)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--review", action="store_true")
    args = ap.parse_args()
    tri_part, instances, _ = build()
    for group, _ in naming.GROUPS:
        print(f"\n{group.upper()}")
        current = None
        for inst in (i for i in instances if i["group"] == group):
            if inst["parent"] != current:
                current = inst["parent"]
                print(f"  {current}")
            tag = " ".join(v for v in (inst["end"], inst["side"]) if v and v != "centre")
            print(f"    {inst['name']:<22} {tag:<12} {inst['mesh']:<8} {inst['tris']:>6} tris  {inst['area_cm2']:>7.0f} cm2  "
                  f"{inst['texels']:>7} texels  {int(inst['shared'] * 100):>3}% shared")
    print(f"\n{len(instances)} part instances, {len(set(i['name'] for i in instances))} names")
    if args.review:
        from tool import preview
        out = paths.BUILD / "parts_review.png"
        preview.render_parts_sheet(tri_part, instances, out)
        print(f"review: {out}")


if __name__ == "__main__":
    main()
