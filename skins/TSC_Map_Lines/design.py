"""The car map's candidate lines (tool/carmap.py, the ridges of the body's curvature): every
traced ridge drawn on a clay car, each in its own colour (twelve colours round and round, so
neighbouring lines differ), to check each one close up against the car's own shading before any
is named. A test car for the map, not a skin to drive (2026-09-29)."""

from tool import carmap, shapes

BODY = "body"
COLOURS = ("#e6194b", "#3cb44b", "#4363d8", "#f58231", "#911eb4", "#42d4f4",
           "#f032e6", "#bfef45", "#469990", "#9a6324", "#800000", "#000075")


def design(s):
    s.clay()
    s.step("Ridges", "Every ridge of the body's curvature, each in its own colour.", words="the car map")
    m = carmap.load()
    for k, colour in enumerate(COLOURS):
        lines = [r for i, r in enumerate(m.ridges) if i % len(COLOURS) == k]
        if lines:
            s.paint(BODY, "satin", colour=colour, zone=shapes.polyline(lines, 1.2))
    s.paint(["inner", "wheel covers"], "satin", colour="#3a3d42")
