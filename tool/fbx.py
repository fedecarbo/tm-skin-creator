"""A small reader for the binary FBX of the car (version 7300, from Maya 2018).

It returns the four meshes (Skin_01, Details_01, Glass_01, Wheels_01) as numpy arrays:
positions per vertex, and per triangle corner the vertex index, the UV and the normal.
Units are cm, Y is up. The parsed result is cached in the work folder.
"""

import struct
import zlib

import numpy as np

from tool import paths

CACHE = paths.CACHE / "mesh.npz"
ARRAY_TYPES = {"f": ("<f4", 4), "d": ("<f8", 8), "l": ("<i8", 8), "i": ("<i4", 4), "b": ("u1", 1)}


class Node:
    __slots__ = ("name", "props", "children")

    def __init__(self, name, props, children):
        self.name, self.props, self.children = name, props, children

    def find(self, name):
        return next((c for c in self.children if c.name == name), None)

    def all(self, name):
        return [c for c in self.children if c.name == name]


def _read_prop(buf, pos):
    t = chr(buf[pos])
    pos += 1
    if t in "YCIFDL":
        fmt = {"Y": "<h", "C": "<?", "I": "<i", "F": "<f", "D": "<d", "L": "<q"}[t]
        size = struct.calcsize(fmt)
        return struct.unpack_from(fmt, buf, pos)[0], pos + size
    if t in ARRAY_TYPES:
        length, encoding, clen = struct.unpack_from("<3I", buf, pos)
        pos += 12
        raw = buf[pos : pos + clen]
        if encoding == 1:
            raw = zlib.decompress(raw)
        dtype, _ = ARRAY_TYPES[t]
        return np.frombuffer(raw, dtype=dtype, count=length), pos + clen
    if t in "SR":
        (length,) = struct.unpack_from("<I", buf, pos)
        pos += 4
        data = bytes(buf[pos : pos + length])
        return (data.decode("utf-8", "replace") if t == "S" else data), pos + length
    raise ValueError(f"unknown FBX property type {t!r} at {pos - 1}")


def _read_node(buf, pos):
    end, nprops, _, name_len = struct.unpack_from("<3IB", buf, pos)
    if end == 0:
        return None, pos + 13
    pos += 13
    name = bytes(buf[pos : pos + name_len]).decode()
    pos += name_len
    props = []
    for _ in range(nprops):
        value, pos = _read_prop(buf, pos)
        props.append(value)
    children = []
    while pos < end:
        child, pos = _read_node(buf, pos)
        if child is None:
            break
        children.append(child)
    return Node(name, props, children), end


def parse(path):
    buf = memoryview(open(path, "rb").read())
    if bytes(buf[:20]) != b"Kaydara FBX Binary  ":
        raise ValueError(f"{path}: not a binary FBX")
    (version,) = struct.unpack_from("<I", buf, 23)
    if version >= 7500:
        raise ValueError(f"FBX {version}: 64-bit records are not supported")
    pos, top = 27, []
    while pos < len(buf) - 13:
        node, pos = _read_node(buf, pos)
        if node is None:
            break
        top.append(node)
    return Node("", [], top)


def _layer(geom, layer_name, data_name, index_name):
    """Per-corner values of a layer element (UVs or normals), expanded to one row per corner."""
    el = geom.find(layer_name)
    mapping = el.find("MappingInformationType").props[0]
    ref = el.find("ReferenceInformationType").props[0]
    width = 2 if layer_name == "LayerElementUV" else 3
    data = np.asarray(el.find(data_name).props[0], dtype=np.float64).reshape(-1, width)
    if ref == "IndexToDirect":
        data = data[np.asarray(el.find(index_name).props[0])]
    elif ref != "Direct":
        raise ValueError(f"{layer_name}: unsupported reference {ref}")
    return mapping, data


def load_meshes(path=paths.FBX):
    root = parse(path)
    objects = root.find("Objects")
    models = {m.props[0]: m.props[1].split("\x00")[0] for m in objects.all("Model")}
    parent = {c.props[1]: c.props[2] for c in root.find("Connections").all("C") if c.props[0] == "OO"}
    meshes = {}
    for geom in objects.all("Geometry"):
        name = models[parent[geom.props[0]]]
        positions = np.asarray(geom.find("Vertices").props[0], dtype=np.float64).reshape(-1, 3)
        pvi = np.asarray(geom.find("PolygonVertexIndex").props[0], dtype=np.int64)
        ends = pvi < 0
        corner_vertex = np.where(ends, ~pvi, pvi)
        uv_map, uvs = _layer(geom, "LayerElementUV", "UV", "UVIndex")
        n_map, normals = _layer(geom, "LayerElementNormal", "Normals", "NormalsIndex")
        if uv_map != "ByPolygonVertex" or n_map != "ByPolygonVertex":
            raise ValueError(f"{name}: expected per-corner UVs and normals")
        # Fan-triangulate each polygon (the car's meshes are already all triangles).
        tris = []
        start = 0
        for end in np.flatnonzero(ends):
            for k in range(start + 1, end):
                tris.append((start, k, k + 1))
            start = end + 1
        corners = np.asarray(tris, dtype=np.int64)  # (T, 3) corner indices
        meshes[name] = {
            "positions": positions.astype(np.float32),
            "tri_vertex": corner_vertex[corners].astype(np.int32),
            "tri_uv": uvs[corners].astype(np.float32),
            "tri_normal": normals[corners].astype(np.float32),
        }
    return meshes


def meshes():
    """The car's meshes, from the cache when it's newer than the FBX."""
    if CACHE.exists() and CACHE.stat().st_mtime > paths.FBX.stat().st_mtime:
        data = np.load(CACHE)
        out = {}
        for key in data.files:
            mesh, field = key.split("/")
            out.setdefault(mesh, {})[field] = data[key]
        return out
    result = load_meshes()
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(CACHE, **{f"{m}/{k}": v for m, d in result.items() for k, v in d.items()})
    return result


if __name__ == "__main__":
    for name, m in meshes().items():
        p = m["positions"]
        print(
            f"{name}: {len(p)} vertices, {len(m['tri_vertex'])} triangles, "
            f"x {p[:, 0].min():.1f}..{p[:, 0].max():.1f}, y {p[:, 1].min():.1f}..{p[:, 1].max():.1f}, "
            f"z {p[:, 2].min():.1f}..{p[:, 2].max():.1f}, "
            f"uv {m['tri_uv'].min():.3f}..{m['tri_uv'].max():.3f}"
        )
