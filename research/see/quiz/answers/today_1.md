# Answers (today_1): a fresh agent, from the skill, the anatomy, its picture and `tool.meshlines`

1. "side skirt crease 2" runs (24, 18, 149) → (39, 19, 70) → (77, 22, 17); the end nearer the nose is (24, 18, 149) (the nose's tip is at z 215). The anatomy lists the nose end first, so if `meshlines.line()` runs in the listed order the course starts at its nose end; nothing I was allowed to read says that outright, and `at` names the lines near each end without saying which way they run, so the direction is a reading of the listing, not a fact I could confirm.
   From: `car/anatomy.md` (crisp lines); `PY -m tool.meshlines at 24 18 149` and `at 77 22 17` (both ends are 0.4 cm from the line).

2. "body shell roll 2" runs (40, 58, 38) → (40, 66, -82), 121 cm, one line tilted 33°. If `deck.start` is the listed first end (z 38), the band covers z 38 to -60: the front part of the roll, about 98 of its 121 cm. If the course starts at the other end it would be z -82 to -60, the back 22 cm. The material doesn't say which end a course starts at, so: front part by the listing order, not confirmed.
   From: `car/anatomy.md` (rounded edges); `PY -m tool.meshlines at 40 58 38` and `at 40 66 -82`.

3. "sidepod top panel 1" (2459 cm², the sidepod top), on the sidepod top; no model line within 5 cm of the point. It is the sidepod top's 28 cm flat room, facing up.
   From: `PY -m tool.meshlines at 70 61 -26`; `car/anatomy.md` (panels, flat rooms).

4. (64, 36, -80) on the rear flank: the flat room there is 37 cm across, facing out and back, no model line within 5 cm, so a 25 cm badge sits whole with no stretch to speak of. (The other flank room, 28 cm at (81, 31, -51), would also take it.)
   From: `car/anatomy.md` (Where it's calm); `PY -m tool.meshlines at 64 36 -80`.

5. It stops at the sidepod inlet's edge. The sidepod inlet is a piece of its own, 1.4 cm from the rest of the body, and the anatomy says a line stops there as a wrap would; "sidepod inlet edge 1" is besides an edge where the body ends (a loop, z 19 to -51), so there is no body on the far side to run onto. The sidepod top is sewn on 0.41 cm from the skin, so a line may run across that seam, but not across the inlet's gap.
   From: `car/anatomy.md` (Where a graphic stops; crisp lines and edges); `PY -m tool.meshlines at 75 49 -45`.

6. Yes: the number panel, z -78 to -62, where the game letters the player's number; keep clear of it and of 3 cm round it. "engine cover seam 2" runs along the engine cover and the number panel (its loop is z -62 to -78), so a placard between z -74 and -62 lies on or within 3 cm of it. What happens: `show` names anything on or round the number panel in its verdict (the skill lists keep-clear among the things the judge names; for `s.mark` shapes the paint moves or shrinks them until clear). Whether a course's placard is blocked outright or only named I can't say from the material.
   From: `.claude/skills/paint/SKILL.md` (Keep clear); `car/anatomy.md` (Where a graphic stops); `PY -m tool.meshlines at 18 83 -62`.

7. On two sets of parts: the body's wheel covers (wheel cover hub, ring and disc) and the inner car's rims, hubs and wheel rings. All four wheels share one paint, so the gold lands on every wheel alike. Not the tyres (their own paint) and not the body.
   From: `.claude/skills/paint/SKILL.md` (What the car allows: wheels and tyres); the wheel cover parts also appear in `PY -m tool.meshlines` (wheel cover ring/disc/hub panels).

8. "side skirt crease 2": a crisp line, 146 cm, (24, 18, 149) → (39, 19, 70) → (77, 22, 17).
   From: `PY -m tool.meshlines` (lines list); `car/anatomy.md`.

9. In front of it (nearer the nose). In the picture the inlet is the framed, grilled opening on the flank that faces forward, around mid-car; the inlet piece's own lines put its forward parts nose-ward of z -26 (its crease's vertical stretch at z 14 to 19, its flat room at (73, 46, -4)), while the flat room at (70, 61, -26) is on the sidepod top behind that. Read from the picture, so moderate confidence; the material has no named "opening" I could measure.
   From: `car/map/model.jpg` (left side, front three-quarter views); `car/anatomy.md` (sidepod inlet crease 1, flat rooms); `PY -m tool.meshlines at 70 50 15`, `at 60 52 10`, `at 72 50 -45` (all on sidepod inlet panel 1).

10. The tail corner and tail panel, 1.7 cm from the rest; and the sidepod inlet (each side), 1.4 cm. (The diffuser strake and diffuser, the sidepod top and the nose fin are sewn on within 1 cm, so a line may run on there.)
    From: `car/anatomy.md` (Where a graphic stops: pieces of their own).

## Commands run

- `PY -m tool.meshlines`
- `PY -m tool.meshlines at 24 18 149`
- `PY -m tool.meshlines at 77 22 17`
- `PY -m tool.meshlines at 40 58 38`
- `PY -m tool.meshlines at 40 66 -82`
- `PY -m tool.meshlines at 70 61 -26`
- `PY -m tool.meshlines at 64 36 -80`
- `PY -m tool.meshlines at 75 49 -45`
- `PY -m tool.meshlines at 18 83 -62`
- `PY -m tool.meshlines at 70 50 15`
- `PY -m tool.meshlines at 72 50 -45`
- `PY -m tool.meshlines at 60 52 10`
(plus `cat` of SKILL.md and anatomy.md, the Read of model.jpg, and one failed batch of the same `at` calls where the shell passed the three numbers as one word)

## Time

About 3 minutes (10:23 to 10:27) from first reading the questions to writing this file.
