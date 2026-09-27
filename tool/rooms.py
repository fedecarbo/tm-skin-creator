"""The Lab's UV map room (viewer/lab-rooms.js): the game's four maps, Skin, Details, Wheels and
Glass, as flat maps where surfaces are picked (tool/view.py), and the whole car as a second tab,
where a picked surface lights up. It has a day and night picker (the viewer lights both;
Trackmania has sunrise and sunset too).

The rooms before it were one per map, Body, Details, Tyres and Glass, each with a camera on its
area (and before that Body, Wheels, Details and Lights: CHECKLIST.md, "The Lab"). The user,
2026-09-27: "I'm starting to not find the views (body, details, etc) so helpful." They had said the
UV map's surfaces would be useful ("for the uv map separating surfaces, that's going to be
useful"), so the maps stay as one room. A room is an entry in ROOMS: its parts are the ones painted
on its maps. rooms() raises if a part is in no room, because a part the Lab can't place is a gap in
the tool."""

# The camera: the viewer's view (viewer/viewer.js, setView). dir: the direction from the car to the
# camera (the car faces +z, its left is +x). frame: what the camera frames, from FRAMES: the viewer
# sets the distance and aim so those parts fill the room's picture with margin to spare at the
# nearest edge, whatever its size (a phone too). Or a fixed view: dist and target, in metres. hides:
# a room whose parts this one takes off. sets: the maps the room shows, its parts those painted on
# them.
ROOMS = [
    {"key": "uv", "name": "UV map", "sets": ["Skin", "Details", "Wheels", "Glass"],
     "about": "the game's four maps: point at a surface to see where its paint goes",
     "view": {"dir": [0.5, 0.62, 0.6], "frame": "car", "margin": 0.06}},
]
FRAMES = {
    "car": lambda inst: True,
}


def rooms(p):
    """ROOMS with each room's part ids and its maps, for the Lab (view.export_uvmap). A framed view
    carries the ids it frames (fit), and hides the ids of the parts the room takes off."""
    ids = {r["key"]: [i for i, inst in enumerate(p.instances) if inst["mesh"] in r["sets"]] for r in ROOMS}
    placed = set().union(*ids.values())
    missing = [p.label(i) for i in range(len(p.instances)) if i not in placed]
    if missing:
        raise ValueError(f"parts in no room of the Lab: {', '.join(missing)} (tool/rooms.py)")
    out = []
    for r in ROOMS:
        view = {k: v for k, v in r["view"].items() if k != "frame"}
        if "frame" in r["view"]:
            view["fit"] = [i for i, inst in enumerate(p.instances) if FRAMES[r["view"]["frame"]](inst)]
        own = set(ids[r["key"]])
        hides = [i for i in ids[r["hides"]] if i not in own] if "hides" in r else []
        out.append({**{k: v for k, v in r.items() if k != "sets"}, "maps": [{"set": s} for s in r["sets"]],
                    "view": view, "ids": ids[r["key"]], "hides": hides})
    return out
