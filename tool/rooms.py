"""The Lab's painting rooms (viewer/lab-rooms.js): the areas of the car a design is worked on in,
each with its parts and a camera that looks at them (the user, 2026-09-26: "the views should
cover particular painting rooms. For example, the body, the wheels, the details ... each room
provides the necessary views that tackle the objective"). Each room shows the car with its camera,
and its own flat maps as a second tab.

A room is an entry in ROOMS and a rule in _member. A new room ("cables and mechanicals") takes its
parts from another. Every part is in at least one room: rooms() raises if one isn't, because a
part the Lab can't place is a gap in the tool. Rooms cut across the texture sets: Wheels holds the
tyres (Wheels), the wheel covers (Skin) and the rims, hubs and brakes (Details).

The Lights room is the parts that glow in Nadeo's light map (Details_I) and the glass lenses, seen
at night; its flat map is the light map, not the paint. Trackmania has four moods (sunrise, day,
sunset, night); the viewer lights day and night so far."""

import numpy as np

from tool import paintbox

# The camera: the viewer's view (viewer/viewer.js, setView): the direction from the target to the
# camera, the distance and the target, in metres (the car faces +z, its left is +x, the front
# wheels' axle at z 1.79, the rear's at -1.20). maps: the flat maps the room's UV map tab offers,
# and the texture it shows on each (the paint unless said).
ROOMS = [
    {"key": "body", "name": "Body", "about": "the painted shell, the canopy and the mirrors' glass",
     "view": {"dir": [0.62, 0.3, 0.72], "dist": 6.4}, "maps": [{"set": "Skin"}, {"set": "Glass"}]},
    {"key": "wheels", "name": "Wheels", "about": "the tyres, the wheel covers, the rims, hubs and brakes",
     "view": {"dir": [0.8, 0.22, 0.56], "dist": 3.4, "target": [0.74, 0.36, 1.05]},
     "maps": [{"set": "Skin"}, {"set": "Details"}, {"set": "Wheels"}]},
    {"key": "details", "name": "Details", "about": "the inner car: the frame, the suspension, the cockpit and the floor",
     "view": {"dir": [0.55, 0.18, 0.82], "dist": 4.6, "target": [0, 0.32, 0.8]}, "maps": [{"set": "Details"}]},
    {"key": "lights", "name": "Lights", "about": "everything that glows, and the lenses over it",
     "view": {"dir": [-0.62, 0.3, -0.72], "dist": 6.4}, "night": True,
     "maps": [{"set": "Details", "slot": "Details_I"}, {"set": "Glass"}]},
]
BODY_GLASS = ("canopy", "mirror glass")  # the rest of the glass covers lights
GLOW_MIN = 0.02  # a part glows when this share of its texels in the light map does


def _member(key, inst, lit):
    if key == "body":
        return (inst["mesh"] == "Skin" and inst["name"] not in paintbox.WHEEL_COVER_PARTS) or inst["name"] in BODY_GLASS
    if key == "wheels":
        return inst["parent"] in ("tyre", "wheel cover", "wheel")
    if key == "details":
        return inst["mesh"] == "Details" and inst["parent"] != "wheel"
    if key == "lights":
        return inst["name"] in lit or (inst["mesh"] == "Glass" and inst["name"] not in BODY_GLASS)
    raise KeyError(key)


def glowing(p, own):
    """The names of the parts that glow in Nadeo's light map. own: the part id of each texel of the
    Details map at some grid size (-1 for none), as the rooms' UV map data."""
    h, w = own.shape
    light = paintbox.stock("Details_I", (w, h))[..., :3].max(-1) > 0.08
    ids = own.reshape(-1)
    counted = ids >= 0
    total = np.bincount(ids[counted], minlength=len(p.instances))
    lit = np.bincount(ids[counted & light.reshape(-1)], minlength=len(p.instances))
    # a shared texel names the lowest id, so a mirror twin glows with its twin: by name
    return sorted({p.instances[i]["name"] for i in np.flatnonzero((lit >= 64) & (lit >= GLOW_MIN * np.maximum(total, 1)))})


def rooms(p, lit):
    """ROOMS with each room's part ids, for the Lab (view.export_uvmap)."""
    out = [{**r, "night": r.get("night", False), "ids": [i for i, inst in enumerate(p.instances) if _member(r["key"], inst, lit)]}
           for r in ROOMS]
    placed = set().union(*(r["ids"] for r in out))
    missing = [p.label(i) for i in range(len(p.instances)) if i not in placed]
    if missing:
        raise ValueError(f"parts in no room of the Lab: {', '.join(missing)} (tool/rooms.py)")
    return out
