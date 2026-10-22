# Answers (today_2)

1. The nose end is (24, 18, 149); the tail end is (77, 22, 17) (the line passes (39, 19, 70) between them, turning 25°).
   Whether `meshlines.line("side skirt crease 2")` starts at the nose end: the anatomy lists the line nose end first, but nothing I may read says the course runs in that order, so: don't know for certain (I'd expect the nose end).
   From: `car/anatomy.md` (Its crisp lines and edges); `PY -m tool.meshlines at 24 18 149` and `at 77 22 17` (side skirt crease 2 is 0.4 cm from each).

2. body shell roll 2 runs (40, 58, 38) → (40, 66, -82). If `deck.start` is the end listed first (z 38), the band covers z 38 to -60: the front part of the roll (about 98 of its 121 cm). If the course starts at the tail end, it would be z -82 to -60, the back part; the material I may read doesn't say which end is `start`, so the direction is: don't know.
   From: `car/anatomy.md` (Its rounded edges); `PY -m tool.meshlines at 40 66 -60` (body shell roll 2 is 2.2 cm from that point).

3. sidepod top panel 1, on the sidepod top (the left one); no model line within 5 cm of the point.
   From: `PY -m tool.meshlines at 70 61 -26`; `car/anatomy.md` (Its panels).

4. (64, 36, -80): the rear flank's biggest flat room, 37 cm across, facing out and back; a 25 cm badge fits inside it whole. (The other rear-flank room, 28 cm at (81, 31, -51), would also take it.)
   From: `car/anatomy.md` (Where it's calm); `PY -m tool.meshlines at 64 36 -80` (rear flank panel 1, no line within 5 cm).

5. It stops at the sidepod inlet's edge. "sidepod inlet edge 1" is where the body ends (a loop round the inlet, z 19 to -51), and the sidepod inlet is a piece of its own with a 1.4 cm gap to the rest of the body: a line stops there, as a wrap would. There is no neighbouring skin across that edge for a band to run onto.
   From: `car/anatomy.md` (Its crisp lines and edges; Where a graphic stops).

6. Yes: engine cover seam 2 is the seam between the engine cover and the number panel (z -62 to -78), and the number panel (z -78 to -62, plus 3 cm round it) is a keep-clear panel where the game letters the player's number. A placard on z -74 to -62 lies on it or within 3 cm of it; `show` names it in its receipt and the judge's verdict (a decal/mark is moved or shrunk until it is clear; whether a course placard is moved or refused outright I can't say from the material: don't know).
   From: `car/anatomy.md` (Where a graphic stops; Its crisp lines and edges); `.claude/skills/paint/SKILL.md` (Keep clear; Words and pictures); `PY -m tool.meshlines at 18 83 -68` (engine cover seam 2, 2.5 cm away, on engine cover panel 1).

7. On the wheels' two sets of parts: the body's wheel covers (each with its own hub, ring and disc) and the inner car's rims, hubs and wheel rings. All four wheels share one paint; the tyres are not included (their own call).
   From: `.claude/skills/paint/SKILL.md` (What the car allows: Wheels and tyres are their own paint).

8. "side skirt crease 2", a crisp line 146 cm long: (24, 18, 149) → (39, 19, 70) → (77, 22, 17). (side skirt roll 3 runs beside it but ends at z 23 and is 140 cm.)
   From: `car/anatomy.md` (Its crisp lines and edges); `PY -m tool.meshlines`.

9. In front of it (nearer the nose). The inlet's mouth faces forward: the inlet's floor lip and its edge are at z 10 to 19 (sidepod inlet crease 1 from (56, 47, 19) to (79, 46, -1)), and the roll where the sidepod top turns down into the duct's ceiling is at z about -16 (sidepod inlet roll 1, tilts 93 to 173); the flat room at (70, 61, -26) sits on the sidepod top above the duct, behind the opening. The picture agrees: the yellow inlet openings are seen head-on in the "front straight on" view.
   From: `PY -m tool.meshlines at 70 50 10` and `at 70 55 -16`; `car/anatomy.md`; `car/map/model.jpg`.

10. The tail corner and tail panel (together), 1.7 cm; and the sidepod inlet (each side), 1.4 cm. (The sidepod top at 0.41 cm, the diffuser and diffuser strake at 0.05/0.04 cm and the nose fin at 0.35 cm are sewn on, 1 cm or less: a line may run on.)
   From: `car/anatomy.md` (Where a graphic stops).

## Commands run

- `cat .claude/skills/paint/SKILL.md`
- `cat car/anatomy.md`
- Read `car/map/model.jpg`
- `PY -m tool.meshlines`
- `PY -m tool.meshlines at 70 61 -26`
- `PY -m tool.meshlines at 64 36 -80`
- `PY -m tool.meshlines at 70 50 10`
- `PY -m tool.meshlines at 70 55 -16`
- `PY -m tool.meshlines at 24 18 149`
- `PY -m tool.meshlines at 77 22 17`
- `PY -m tool.meshlines at 18 83 -68`
- `PY -m tool.meshlines at 40 66 -60`

Time: about 3 minutes in all (the commands themselves ran in about 2 minutes; reading and writing the rest).
