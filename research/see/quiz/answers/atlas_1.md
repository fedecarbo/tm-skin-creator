# Answers (atlas_1)

1. "side skirt crease 2" runs (24, 18, 149) → (39, 19, 70) → (77, 22, 17); the end at (24, 18, 149) is nearer the nose
   (z 149 against z 17). The course `meshlines.line("side skirt crease 2")` starts at its NOSE end (start z 149,
   end z 17).
   From: car/anatomy.md (the line's points); cards_1.png, card 18 (START is the nose end, course runs nose first).

2. "body shell roll 2" runs z 38 to z -82 and its course runs TAIL first (start z -82, end z 38). So
   `deck.between(deck.start, deck.at(z=-60)).band(3)` covers z -82 to -60: the BACK part of the roll, about 22 cm
   of its 121.
   From: cards_1.png, card 20 (and the atlas legends, line 20); car/anatomy.md for the roll's ends.

3. sidepod top panel 1, on the sidepod top (the flat room on the sidepod top, 28 cm across, that faces up).
   From: `PY -m tool.meshlines at 70 61 -26`; car/anatomy.md (Where it's calm).

4. Centre (64, 36, -80) on the rear flank: its flat room is 37 cm across there (faces out and back), room for a
   25 cm badge with no stretch. (The other rear flank room, 28 cm at (81, 31, -51), would also take it.)
   From: car/anatomy.md (Where it's calm, rear flank).

5. It stops at the sidepod inlet's edge. The sidepod inlet is a piece of its own, with a gap of 1.4 cm round it
   to the rest of the skin, so a line or band along it stops there as a wrap would; it doesn't run on to the
   sidepod top or body shell (the sidepod top is sewn on at 0.41 cm, but the inlet isn't).
   From: car/anatomy.md (Where a graphic stops); the edge's parts from `PY -m tool.meshlines` (sidepod inlet only).

6. Yes: "engine cover seam 2" is the loop round the number panel (z -78 to -62, parts: engine cover and number
   panel), so a placard on its stretch z -74 to -62 sits on or within 3 cm of the number panel, which the game
   letters with the player's number. `show` names it in the verdict; the placard has to move or the car isn't shown.
   From: car/anatomy.md (Keep clear); `PY -m tool.meshlines` and `at 18 83 -68`; SKILL.md (Keep clear).

7. The body's wheel covers (wheel cover hub, wheel cover ring, wheel cover disc) and the inner car's rims, hubs
   and wheel rings, two sets of parts; all four wheels share the one paint.
   From: .claude/skills/paint/SKILL.md (Wheels and tyres are their own paint).

8. "side skirt crease 2", a crisp line, 146 cm ((24, 18, 149) → (39, 19, 70) → (77, 22, 17)).
   From: car/anatomy.md; `PY -m tool.meshlines`.

9. In front of it (nearer the nose, to your right). The inlet's opening (its mouth, the front lip at about z 14
   to 19, at y 46-56) is forward of the flat room at (70, 61, -26); the inlet's cavity runs back under the
   sidepod top to z -51, so the flat room sits above the inlet's rear part, not in front of its mouth.
   From: car/anatomy.md (sidepod inlet crease 1 and edge 1); atlas_side.png (panel I and line 41 against panel G);
   `PY -m tool.meshlines at 60 50 16`.

10. The tail corner and tail panel, a gap of 1.7 cm; the sidepod inlet (each side), 1.4 cm. (Sewn on at 1 cm or
    less, where a line may run on: the diffuser strake and diffuser 0.05 cm, the sidepod top 0.41 cm, the nose
    fin 0.35 cm.)
    From: car/anatomy.md (Where a graphic stops).

## Commands run

- `PY -m tool.meshlines`
- `PY -m tool.meshlines at 70 61 -26`
- `PY -m tool.meshlines at 18 83 -68`
- `PY -m tool.meshlines at 60 50 16`

Also read: `.claude/skills/paint/SKILL.md`, `car/anatomy.md`, `car/map/model.jpg`, and the atlas pictures
atlas_side.png, atlas_top.png, atlas_front.png, cards_1.png, cards_2.png, cards_3.png.

Time: about 4 minutes for the whole quiz (first command 10:23, answers written 10:27).
