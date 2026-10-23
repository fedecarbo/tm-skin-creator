"""TSC_RingsAcross_Before: TSC_RingsAcross painted by the tool as it was (4e59d71), a throwaway test car for the road's step 19 (2026-10-22): navy rings pressed across the car's panel
lines' grooves, a hairline between pieces, a rolled edge and two plain crisp lines, both sides, on a white body, for
the eye to find any ring chipped, jogged or cut where it crosses one. The shoulder ring is K2's own (the ring that came
out chipped on three cars)."""
from tool import marks, meshlines

RINGS = "deep navy satin"


def design(s):
    s.clay()
    s.step("Base", "The body white gloss, the inner car dark grey.", words="a white car")
    s.paint("body", "gloss white")
    s.paint("inner", "dark grey satin")
    s.step("Shoulder ring", "A 16 cm navy ring pressed over the rear flank's rolled shoulder at z -68, across the "
           "panel line between the rear flank and the body shell, both sides.", words="a ring over the shoulder")
    s.mark("body", RINGS, marks.ring(0.82), size=16, at=meshlines.line("rear flank roll 2", tilt=47).at(z=-68), across=True)
    s.step("Groove rings", "Navy rings 12 to 14 cm pressed across four panel lines' grooves: where the sidepod top meets "
           "the body (its own piece, a hairline apart), round the fuel cap, beside the cockpit, on the rear quarter "
           "panel; both sides.", words="rings across the panel lines")
    s.mark("body", RINGS, marks.ring(0.8), size=14, at=(56, None, -15), across=True)
    s.mark("body", RINGS, marks.ring(0.6), size=12, at=(51, None, -72), across=True)
    s.mark("body", RINGS, marks.ring(0.8), size=14, at=(23, None, 33), across=True)
    s.mark("body", RINGS, marks.ring(0.8), size=12, at=meshlines.line("rear quarter panel crease 1").at(z=-65), across=True)
    s.step("Edge rings", "Navy rings 12 cm pressed over the body shell's rolled side at z 70 and over two plain crisp "
           "lines beside the nose at z 112, both sides.", words="rings over a rolled edge and crisp lines")
    s.mark("body", RINGS, marks.ring(0.8), size=12, at=meshlines.line("body shell roll 4").at(z=70), across=True)
    s.mark("body", RINGS, marks.ring(0.8), size=12, at=meshlines.line("body shell crease 3").at(z=112), across=True)
    s.step("Wheels", "Dark grey wheels.", words="dark wheels")
    s.paint("wheels", "dark grey satin")
