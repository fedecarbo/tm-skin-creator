"""The names of the car's parts, by eye, from labelled renders (Claude, 2026-09-24).

Each entry names a part and says which pieces or groups make it (ids from tool/segment.py) or
which rule picks its triangles (rules live in tool/parts.py). Only one side of each mirrored
pair is listed: the twin gets the same name. Every piece left unnamed joins the nearest named
piece of its mesh (bolts, brackets, ends of rods), so the list needn't be complete.

  name     what the user calls it, plain words, singular
  parent   the assembly it belongs to, for the list in the viewer
  group    ids of touching-piece groups (Details, Glass)
  piece    piece ids (Skin, Details)
  rule     a rule in tool/parts.RULES that picks pieces by geometry, or a cut (tool/parts.CUTS)
           that splits a smooth surface by a distance field, with anti-aliased edges

Sides: the car's left is +x. Front is +z. A part's side and end (front/rear) are worked out
from where its pieces sit, so "brake caliper" covers all four and can be narrowed later.
"""

PARTS = [
    # ---- Body (the Skin mesh) ----
    # The big panel from the nose to the cockpit and over the sidepods is one smooth piece with
    # no fold in it (measured: no crease over 10 degrees except its centre seam). Splitting it by
    # slope or by a line gave ragged borders in the game (2026-09-24), so it stays one part;
    # zones on it (nose, bonnet, sides) are the paint box's job, with soft edges in 3D.
    dict(name="body shell", parent="shell", piece=[21]),
    dict(name="nose tip", parent="shell", piece=[23]),
    dict(name="nose panel", parent="shell", piece=[51]),
    dict(name="nose fin", parent="shell", piece=[5, 9, 26], group=[260]),
    dict(name="cockpit surround", parent="shell", piece=[122]),
    dict(name="mirror mount", parent="shell", piece=[13, 18]),
    dict(name="side skirt", parent="shell", piece=[19]),
    dict(name="sidepod top", parent="sidepod", piece=[55]),
    dict(name="sidepod inlet", parent="sidepod", piece=[15]),
    dict(name="rear flank", parent="shell", piece=[29]),
    dict(name="rear quarter panel", parent="shell", piece=[58]),
    dict(name="fuel cap", parent="shell", piece=[33]),
    dict(name="engine cover", parent="engine cover", piece=[22]),
    dict(name="engine cover panel", parent="engine cover", piece=[1, 3]),
    dict(name="number panel", parent="engine cover", piece=[0, 2, 4]),
    dict(name="tail panel", parent="tail", piece=[6]),
    dict(name="tail corner", parent="tail", piece=[7]),
    dict(name="diffuser", parent="tail", piece=[52]),
    dict(name="diffuser strake", parent="tail", piece=[53, 129, 131]),
    dict(name="wing pylon", parent="wing mounts", piece=[24, 25, 27, 28]),
    dict(name="wheel cover ring", parent="wheel cover", rule="cover_ring"),
    dict(name="wheel cover disc", parent="wheel cover", rule="cover_disc"),
    dict(name="wheel cover hub", parent="wheel cover", rule="cover_hub"),
    # ---- Details: the inner car ----
    dict(name="front wing", parent="front wing", rule="floor_wing"),
    dict(name="front wing endplate", parent="front wing", group=[359]),
    dict(name="wing bracket", parent="wing mounts", group=[253, 269, 270, 206, 265, 204]),
    dict(name="floor", parent="floor", rule="floor_main"),
    dict(name="floor plank", parent="floor", rule="floor_plank"),
    # the frame the tail hangs on: the face round the speed numbers, the channels under it and the two
    # arms reaching forward. Cut from the floor's piece by its rule, it was "rear diffuser" in the
    # floor until the user saw it (2026-09-26: "you are including a big portion of the rear.
    # That's not the floor")
    dict(name="tail frame", parent="tail", rule="floor_diffuser"),
    dict(name="floor rail", parent="floor", group=[254]),
    dict(name="nose inner", parent="chassis", rule="chassis_nose"),
    dict(name="cockpit tub", parent="chassis", rule="chassis_cockpit"),
    dict(name="engine bay", parent="chassis", rule="chassis_engine"),
    dict(name="nose plate", parent="chassis", group=[185]),
    dict(name="front bulkhead", parent="chassis", group=[231]),
    dict(name="nose sensor", parent="chassis", group=[235]),
    dict(name="antenna", parent="chassis", group=[256, 258]),
    dict(name="side vane", parent="chassis", group=[328]),
    dict(name="sidepod panel", parent="sidepod", group=[419]),
    # the plate the grille sits in: its own crease-bounded piece inside the frame's group (the
    # user wanted it painted apart, 2026-09-24); it must come before the frame, first name wins
    dict(name="sidepod grille plate", parent="sidepod", piece=[1898]),
    dict(name="sidepod frame", parent="sidepod", group=[411]),
    dict(name="sidepod grille", parent="sidepod", group=[439]),
    dict(name="sidepod boss", parent="sidepod", group=[412]),
    dict(name="sidepod strut", parent="sidepod", group=[441]),
    dict(name="airbox", parent="engine cover", group=[340, 370]),
    dict(name="exhaust", parent="tail", group=[322, 323]),
    dict(name="side vent", parent="tail", group=[366, 367, 413, 414]),
    # the lights under the tail's lenses, behind the "rear light lens" glass: the stock glow there is
    # white, yet the game shows them red, and Nadeo's post says a skin can't change them
    dict(name="rear light", parent="tail", piece=[241, 231]),
    dict(name="rear bumper", parent="tail", group=[88, 339, 354, 266, 232]),
    dict(name="rear bumper corner", parent="tail", group=[360]),
    dict(name="rear undertray", parent="tail", group=[90]),
    dict(name="rear strake", parent="tail", group=[374]),
    # piece 139 (the right digit's bottom bar face) has no mirror match, so it's named here
    dict(name="digit display", parent="tail", group=[312, 305, 311, 240, 234, 239], piece=[139]),
    # cockpit
    dict(name="seat", parent="cockpit", group=[152]),
    dict(name="seat belt", parent="cockpit", group=[169, 278, 274, 200, 307, 154]),
    dict(name="belt buckle", parent="cockpit", group=[233, 267, 198]),
    dict(name="cockpit rim", parent="cockpit", group=[165, 142, 140, 338, 358]),
    dict(name="steering wheel", parent="cockpit", group=[192, 262]),
    dict(name="steering column", parent="cockpit", group=[251]),
    dict(name="dashboard", parent="cockpit", group=[252, 272, 237]),
    dict(name="mirror", parent="cockpit", group=[353]),
    dict(name="mirror arm", parent="cockpit", group=[410]),
    # front suspension (left; the right is the twin)
    dict(name="lower wishbone", parent="front suspension", group=[301]),
    dict(name="upper wishbone", parent="front suspension", group=[302]),
    dict(name="tie rod", parent="front suspension", group=[277, 329]),
    dict(name="damper", parent="front suspension", group=[280, 275]),
    dict(name="pushrod", parent="front suspension", group=[282, 276]),
    dict(name="brake line", parent="front suspension", group=[279]),
    dict(name="upright", parent="front suspension", group=[415, 416]),
    # the slotted crescent inside each front wheel that the stock Details_I marks as brake lights
    # (code 0): dim all the time, flaring when braking (checkpoint 1). Part of the hub's group.
    dict(name="brake light", parent="rims and brakes", piece=[461, 462]),
    dict(name="hub", parent="rims and brakes", group=[421, 434]),
    dict(name="rim", parent="rims and brakes", group=[442, 443, 440, 444]),
    dict(name="brake caliper", parent="rims and brakes", group=[445, 446, 450, 451]),
    dict(name="wheel ring", parent="rims and brakes", group=[447, 448, 449, 452, 453, 454]),
    # rear suspension
    dict(name="hub bracket", parent="rear suspension", group=[408, 409]),
    dict(name="upright cover", parent="rear suspension", group=[376]),
    dict(name="driveshaft", parent="rear suspension", group=[395]),
    dict(name="rear damper", parent="rear suspension", group=[344]),
    dict(name="rear arm", parent="rear suspension", group=[377, 378, 373, 379, 382, 385, 386, 388, 390, 391, 392,
                                                          398, 399, 402, 404, 405, 406, 422, 423, 420, 350]),
    # ---- Tyres (the Wheels mesh) ----
    dict(name="tread", parent="tyre", rule="tyre_tread"),
    dict(name="sidewall", parent="tyre", rule="tyre_sidewall"),
    # ---- Glass: each piece in the assembly it sits in (placed by its nearest parts, 2026-09-26) ----
    dict(name="canopy", parent="shell", piece=[2070]),
    dict(name="gear display", parent="cockpit", rule="glass_digits"),
    dict(name="nose lens", parent="shell", group=[465, 466, 468, 470, 471, 469]),
    dict(name="rear light lens", parent="tail", group=[472, 473]),
    dict(name="side lens", parent="tail", group=[475, 476]),
    dict(name="wing lens", parent="front wing", group=[474]),
    dict(name="mirror glass", parent="cockpit", group=[477]),
]

# The groups, the top of the parts list (the user, 2026-09-26: "Wheel cover, Tyre, etc. should be
# in a parent category called Wheels. Same with body ... the parent of sidepod, engine cover, tail
# ... At least the external bits. Then there's Mechanicals ... cables, suspensions etc."). The
# floor is a group of its own (the user, 2026-09-26: "we could separate the bottom floor"), with the
# front wing, whose panels wear the floor's paint ("I still see the front wing objects in body ... All
# should be floor I would assume. Except for wing pylon. And wing bracket": those hold the wing under
# the nose, in Body's "wing mounts"). A group
# is a name for the list and for picking parts; the paint box's own words "body" and "wheels"
# keep their meanings (tool/paintbox.py).
GROUPS = [
    ("body", "the outside of the car"),
    ("floor", "the underside and the front wing"),
    ("wheels", "tyres, covers, rims and brakes"),
    ("mechanicals", "the frame and the suspension"),
    ("cockpit", "where the driver sits"),
]

# Assemblies, in the order the viewer lists them: (name, group, a plain description). The user
# may split them further (2026-09-26); a group keeps its assemblies' order.
ASSEMBLIES = [
    ("shell", "body", "the nose, the sides and the canopy"),
    ("wing mounts", "body", "the struts holding the front wing under the nose"),
    ("sidepod", "body", "the boxes either side of the cockpit"),
    ("engine cover", "body", "the deck behind the cockpit"),
    ("tail", "body", "the back of the car"),
    ("floor", "floor", "the flat underside and its planks"),
    ("front wing", "floor", "the wing under the nose, in the floor's paint"),
    ("wheel cover", "wheels", "the discs over the wheels"),
    ("tyre", "wheels", "the rubber"),
    ("rims and brakes", "wheels", "rims, hubs and brakes"),
    ("chassis", "mechanicals", "the inner shell under the body"),
    ("front suspension", "mechanicals", "the arms holding the front wheels"),
    ("rear suspension", "mechanicals", "the arms holding the rear wheels"),
    ("cockpit", "cockpit", "seat, belts, steering wheel, dashboard and mirrors"),
]
