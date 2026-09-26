"""The Lab's painting rooms (viewer/lab-rooms.js): the game's four maps, Body, Details, Tyres and
Glass, each with its parts and a camera that looks at them. Each room shows the car with its
camera, and its own flat map as a second tab, where surfaces are picked (tool/view.py). Every room
has a day and night picker (the viewer lights both; Trackmania has sunrise and sunset too).

The user, 2026-09-26: "just for now go back to the default, Body, Details, Tyres, Glass. I don't
think we need a tab for lights because for each we can just have a picker ... it's now getting
over engineered." Before that the rooms were Body, Wheels, Details and Lights (CHECKLIST.md, "The
Lab"). A room is an entry in ROOMS: its parts are the ones painted on its map. rooms() raises if
a part is in no room, because a part the Lab can't place is a gap in the tool.

The cameras are the user's picks of 2026-09-26, from real renders side by side
(https://claude.ai/artifact/1j5ftfuzYn6TiZz7F5uddd): Body from higher up, the whole car; Details
with the shell taken off (a camera alone saw mostly the body); Tyres the Wheels room's, one front
wheel close. Glass has Body's until the user picks one."""

# The camera: the viewer's view (viewer/viewer.js, setView). dir: the direction from the car to the
# camera (the car faces +z, its left is +x, the front wheels' axle at z 1.79, the rear's at -1.20).
# frame: what the camera frames, from FRAMES: the viewer sets the distance and aim so those parts
# fill the room's picture with margin to spare at the nearest edge, whatever its size (a phone
# too). Or a fixed view: dist and target, in metres. hides: a room whose parts this one takes off
# (the Details room the shell). set: the map the room is, its parts those painted on it.
ROOMS = [
    {"key": "body", "name": "Body", "set": "Skin", "about": "the painted shell and the wheel covers",
     "view": {"dir": [0.5, 0.62, 0.6], "frame": "car", "margin": 0.06}},
    {"key": "details", "name": "Details", "set": "Details", "about": "the inner car, the floor, the rims and brakes",
     "view": {"dir": [0.62, 0.35, 0.72], "frame": "car", "margin": 0.05}, "hides": "body"},
    {"key": "tyres", "name": "Tyres", "set": "Wheels", "about": "the rubber: all four tyres share one paint",
     "view": {"dir": [0.85, 0.15, 0.5], "frame": "front left tyre", "margin": 0.3}},
    {"key": "glass", "name": "Glass", "set": "Glass", "about": "the canopy, the lenses and the mirrors: tint only",
     "view": {"dir": [0.5, 0.62, 0.6], "frame": "car", "margin": 0.06}},
]
FRAMES = {
    "car": lambda inst: True,
    "front left tyre": lambda inst: inst["parent"] == "tyre" and inst["side"] == "left" and inst["end"] == "front",
}


def rooms(p):
    """ROOMS with each room's part ids and its map, for the Lab (view.export_uvmap). A framed view
    carries the ids it frames (fit), and hides the ids of the parts the room takes off."""
    ids = {r["key"]: [i for i, inst in enumerate(p.instances) if inst["mesh"] == r["set"]] for r in ROOMS}
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
        out.append({**{k: v for k, v in r.items() if k != "set"}, "maps": [{"set": r["set"]}], "view": view,
                    "ids": ids[r["key"]], "hides": hides})
    return out
