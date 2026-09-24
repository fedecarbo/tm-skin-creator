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
    dict(name="body shell", parent="body", piece=[21]),
    dict(name="nose tip", parent="body", piece=[23]),
    dict(name="nose panel", parent="body", piece=[51]),
    dict(name="nose fin", parent="body", piece=[5, 9, 26], group=[260]),
    dict(name="cockpit surround", parent="body", piece=[122]),
    dict(name="mirror mount", parent="body", piece=[13, 18]),
    dict(name="side skirt", parent="body", piece=[19]),
    dict(name="sidepod top", parent="sidepod", piece=[55]),
    dict(name="sidepod inlet", parent="sidepod", piece=[15]),
    dict(name="rear flank", parent="body", piece=[29]),
    dict(name="rear quarter panel", parent="body", piece=[58]),
    dict(name="fuel cap", parent="body", piece=[33]),
    dict(name="engine cover", parent="engine cover", piece=[22]),
    dict(name="engine cover panel", parent="engine cover", piece=[1, 3]),
    dict(name="number panel", parent="engine cover", piece=[0, 2, 4]),
    dict(name="tail panel", parent="tail", piece=[6]),
    dict(name="tail corner", parent="tail", piece=[7]),
    dict(name="diffuser", parent="tail", piece=[52]),
    dict(name="diffuser strake", parent="tail", piece=[53, 129, 131]),
    dict(name="wing pylon", parent="front wing", piece=[24, 25, 27, 28]),
    dict(name="wheel cover ring", parent="wheel cover", rule="cover_ring"),
    dict(name="wheel cover disc", parent="wheel cover", rule="cover_disc"),
    dict(name="wheel cover hub", parent="wheel cover", rule="cover_hub"),
    # ---- Details: the inner car ----
    dict(name="front wing", parent="front wing", rule="floor_wing"),
    dict(name="front wing endplate", parent="front wing", group=[359]),
    dict(name="wing bracket", parent="front wing", group=[253, 269, 270, 206, 265, 204]),
    dict(name="floor", parent="floor", rule="floor_main"),
    dict(name="floor plank", parent="floor", rule="floor_plank"),
    dict(name="rear diffuser", parent="floor", rule="floor_diffuser"),
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
    dict(name="sidepod frame", parent="sidepod", group=[411]),
    dict(name="sidepod grille", parent="sidepod", group=[439]),
    dict(name="sidepod boss", parent="sidepod", group=[412]),
    dict(name="sidepod strut", parent="sidepod", group=[441]),
    dict(name="airbox", parent="engine cover", group=[340, 370]),
    dict(name="exhaust", parent="tail", group=[322, 323]),
    dict(name="side vent", parent="tail", group=[366, 367, 413, 414]),
    dict(name="rear bumper", parent="tail", group=[88, 339, 354, 266, 232]),
    dict(name="rear bumper corner", parent="tail", group=[360]),
    dict(name="rear undertray", parent="tail", group=[90]),
    dict(name="rear strake", parent="tail", group=[374]),
    dict(name="digit display", parent="tail", group=[312, 305, 311, 240, 234, 239]),
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
    dict(name="hub", parent="wheel", group=[421, 434]),
    dict(name="rim", parent="wheel", group=[442, 443, 440, 444]),
    dict(name="brake caliper", parent="wheel", group=[445, 446, 450, 451]),
    dict(name="wheel ring", parent="wheel", group=[447, 448, 449, 452, 453, 454]),
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
    # ---- Glass ----
    dict(name="canopy", parent="glass", piece=[2070]),
    dict(name="gear display", parent="glass", rule="glass_digits"),
    dict(name="nose lens", parent="glass", group=[465, 466, 468, 470, 471, 469]),
    dict(name="rear light lens", parent="glass", group=[472, 473]),
    dict(name="side lens", parent="glass", group=[475, 476]),
    dict(name="wing lens", parent="glass", group=[474]),
    dict(name="mirror glass", parent="glass", group=[477]),
]

# Assemblies, in the order the viewer lists them, with a plain description.
ASSEMBLIES = [
    ("body", "the painted outer shell"),
    ("sidepod", "the boxes either side of the cockpit"),
    ("engine cover", "the deck behind the cockpit"),
    ("tail", "the back of the car"),
    ("wheel cover", "the discs over the wheels"),
    ("front wing", "the wing under the nose"),
    ("floor", "the flat underside"),
    ("chassis", "the inner shell under the body"),
    ("cockpit", "where the driver sits"),
    ("front suspension", "the arms holding the front wheels"),
    ("rear suspension", "the arms holding the rear wheels"),
    ("wheel", "hubs, rims and brakes"),
    ("tyre", "the rubber"),
    ("glass", "the see-through parts"),
]
