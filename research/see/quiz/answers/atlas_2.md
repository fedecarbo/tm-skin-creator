# Answers (atlas_2)

1. The nose end is (24, 18, 149); the tail end is (77, 22, 17) (the line runs (24, 18, 149) → (39, 19, 70) → (77, 22, 17)).
   The course starts at the NOSE end (z 149) and ends at the tail end (z 17).
   From: car/anatomy.md (the ends); cards_1.png card 18 and atlas legend 18 ("course runs NOSE first: start z 149, end z 17").

2. body shell roll 2 runs TAIL first: start (40, 66, -82), end (40, 58, 38). `deck.between(deck.start, deck.at(z=-60))`
   is z -82 to -60: the BACK (tail) part of the roll, a 3 cm band centred on its line (it wraps the edge).
   From: cards_1.png card 20 / atlas legend 20 ("course runs TAIL first: start z -82, end z 38"); car/anatomy.md (the roll's ends); SKILL.md (`.band(cm)` centred).

3. sidepod top panel 1, on the sidepod top (the flat room there, 28 cm across, faces up).
   From: `PY -m tool.meshlines at 70 61 -26` ("The panel under it: sidepod top panel 1"); car/anatomy.md (Where it's calm).

4. Centre (64, 36, -80): the rear flank's biggest flat room, 37 cm across, facing out and back; a 25 cm badge fits inside it.
   (The other flat room, (81, 31, -51), is only 28 cm across.)
   From: car/anatomy.md (Where it's calm); `PY -m tool.meshlines at 64 36 -80` (rear flank panel 1, no line within 5 cm).

5. It stops at the sidepod inlet's edge. The sidepod inlet is a piece of its own, with a gap of 1.4 cm round it;
   a line (or band) stops there, as a wrap would, instead of running on across onto the sidepod top or the body shell.
   From: car/anatomy.md (Where a graphic stops: "Pieces of their own ... the sidepod inlet (each side), 1.4 cm. A line stops there, as a wrap would.").

6. Yes: the number panel (z -78 to -62), where the game letters the player's number; engine cover seam 2 is its boundary,
   so a placard on z -74 to -62 lies on or within 3 cm of it. The keep-clear rule says nothing on it or within 3 cm:
   `show` names what's there, and a shape/decal is moved or shrunk until it's clear.
   From: car/anatomy.md (Keep clear; engine cover seam 2 "along the engine cover and number panel, z -62 to -78"); SKILL.md (Keep clear; shapes "clear of the game's panels, moved or shrunk until they are").

7. Two sets of parts, all four wheels alike: the body's wheel covers (with their own hub, ring and disc) and the inner
   car's rims, hubs and wheel rings. Not the tyres (their own paint) and not "body".
   From: .claude/skills/paint/SKILL.md (What the car allows: "Wheels and tyres are their own paint").

8. side skirt crease 2, a crisp line, 146 cm ((24, 18, 149) → (39, 19, 70) → (77, 22, 17)).
   From: car/anatomy.md; `PY -m tool.meshlines` (146 cm at (39, 19, 70), side skirt); atlas legend 18.

9. In front of it (nearer the nose). The inlet's opening faces forward at the front of the sidepod (its edge loop starts at
   z 19, its crease at z 14; model.jpg's front view shows the openings on the flanks), and the flat room on the sidepod top
   at z -26 lies behind it, above the duct.
   From: car/anatomy.md (sidepod inlet edge 1 z 19 to -51; sidepod inlet crease 1; flat rooms); car/map/model.jpg (front straight on); atlas_front.png (panel I with line 9 round it, seen from the front); `PY -m tool.meshlines at 70 50 15` (sidepod inlet panel 1).

10. The tail corner and tail panel, 1.7 cm; the sidepod inlet (each side), 1.4 cm.
    (Sewn on, 1 cm or less, so a line may run on: the diffuser strake and diffuser 0.05 cm, the sidepod top 0.41 cm, the nose fin 0.35 cm.)
    From: car/anatomy.md (Where a graphic stops).

## Commands run

- `PY -m tool.meshlines` (about 5 s)
- `PY -m tool.meshlines at 70 61 -26`
- `PY -m tool.meshlines at 70 50 15`
- `PY -m tool.meshlines at 64 36 -80`

Also read: SKILL.md, car/anatomy.md, car/map/model.jpg, atlas_side.png, atlas_top.png, atlas_front.png, cards_1.png, cards_2.png (cards_3.png not needed).

Time for the whole quiz: roughly 5 to 6 minutes.
