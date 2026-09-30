# Shapes: the livery designer's guide

Read for a new car's first concepts (`new-car.md`, 2: the concepts' big shapes) and on the car (3: making
them right on the picked car).
It grows with every car: when the car's work here is done, add what the car taught under "Learned", dated,
with the car's name.

## What good looks like

- **It reads in half a second.** One dominant shape, then a second, then details: a hierarchy.
  Shrink the car to a thumbnail (the top and the chase cameras): if the idea is gone, the shapes
  are too many or too small.
- **Graphics follow the car's form.** Lines run along its main lines (the shoulder from the nose
  back over the sidepod, the sidepod's top, the deck's curve) and end at natural edges: a fold, a
  panel join, an inlet's rim. A graphic cut by a fold it didn't plan for looks like a mistake.
- **Shapes set the car's stance.** Lines raked back read as speed; long horizontal bands make the
  car longer and lower; a vertical split shortens it. A shape that leans forward on one side must
  lean forward on the other too (the right is not the left's mirror in the texture, it is on the car).
- **Leave room.** The base colour needs open areas for the graphic to read against; filling every
  panel makes noise.
- **Every camera has a job.** The player sees the back and the top all race (the chase cameras):
  what reads there is the car for them. Other players and replays see the sides; the front is the
  face test. Say in a line what each sees.

## On this car

- Where things are: **the car map**, `car/map.md` and its pictures (`car/map/`): the body along its
  length (where the top ends and the side turns under at each station), its openings, every panel
  (where it sits, how open, how big from the chase cameras), where the air hits. The places the map
  can't know are special (the number and name panels, the nose fin's plate) are in `SKILL.md`,
  "What works on this car". The car runs from z -162 (tail) to 215 (nose), the wheels at z 179 and
  -120. The front flank isn't flat: its lower half sits back under a lip along a diagonal crease.
- **Lines on the car's own skin** (`tool/skindraw.py`): stripes, bands, pinstripes, rings and
  sweeps are curves on the surface (`through`, `circle`, `parallel`, `mirror`, `band`), exact in
  width over every fold and seam, run off the car's edge rather than stopped mid-panel. A
  multi-colour stripe is parallels of one curve, so its gaps hold. See `SKILL.md`, "Draw lines on
  the car's own skin", and TSC_Solstice.
- Zones (`tool/shapes.py`): the map's first (`area`, `outside`, `across`, `along`, `line`, `near`,
  `hit`, `streamlines`), which follow the body by themselves; then planes for diagonal
  splits, `facing`, `blob`, `grass`, `fade`, combined with & | ~. Spots and shapes seen from above:
  `& shapes.area("top") & shapes.outside(0.4)`. A line that runs with the car's shape: `skindraw`; with the air: `streamlines`. Patterns made of things: `s.scatter`;
  continuous prints through the unfolding (they break at folds, as a real wrap would).
- Crisp edges: the zone edge is 0.2 cm. A fade along an edge reads as blurred. Paint can't fake big
  3D shapes; a painted shadow has to be even all round.
- An assembly's name reaches further than it looks ("front wing" also paints the pylons under the
  nose; "floor" and "sidepod" too): `show` notes it, and gives the `|part` phrase.

## Check before showing

- The six views, the close looks, the top and the game's cameras (`--cams`), and the review angles
  (`--review`): straight on, low behind, under the tail, the right-hand flanks.
- Every graphic where it meets a fold, a join, an inlet's rim, and **the lower crease where the
  body turns under**: nothing cut, sunk, stretched or running into the part below.
- Left against right: the same shapes where they should match.

## Learned

- 2026-09-28, TSC_Ladybird: a shape projected from the side (the grass blades) stretches into
  slashes where the surface turns under, below the flank's lower crease; Claude's own review called
  it clean and the critic found it. There, switch to a solid band (`facing("down", ...)`) or stop
  the shape at the crease. Spots placed without the top's map were cut in half at the shell's
  edge; one ran down into a sidepod inlet (the outer panels only now). A zone of "everything low"
  made a green slab under the nose, where the side skirt runs forward as a ledge facing up.
- 2026-09-28, the concept designers' trial (TSC_ConceptTrial): all three found it on their own: the
  side skirt runs forward of each sidepod as a ledge facing up, so grass or a green wash there shows
  from above as a strip at the car's waist; keep it the dark ground colour, or start the grass behind
  it. Spots over the deck's outer edge dip into the hollow above the rear wheels and come out
  kidney-shaped from the chase cameras: keep them on the deck's top. A pair of dark shapes either
  side of the nose can read as brows from straight on (the face test).
- 2026-09-26, the concept round (Kintsugi, Thrown, Unravelled): crimson drops on black read as
  blood; noise finer than a few cm makes faceted edges; stripes draped round a line along the car
  fan into a sunburst near the line (TSC_FlagPeel_CostaRica).
- 2026-09-30, TSC_Solstice (the first livery drawn on the car's own skin): a sweep of three
  colours reads as crafted when they are parallels of one curve with a thin gap of the base colour
  between them (16 mm bands, 4 mm gaps, held over every fold); twin stripes edged in a second colour
  are a wide band with a narrower one on it. Stripes stopped mid-nose looked unfinished: start the
  curve at the front edge so they run off the car. A middle stripe can't run down the top's centre
  (the cockpit is open from z +70 to -45): twin stripes framing the cockpit, kept outside the number
  and name panels, read well from the chase camera. The tail, the skirt, the diffuser and the inlet's
  duct are pieces of their own, across real gaps in the model: a line stops at them.
- 2026-09-29, the car map (TSC_WindTunnel's smoke lines): lines that follow the car are the map's
  now, never measured in a design (its first smoke lines cut the body into sections by hand: 403
  lines). A band that bends with the body: `across`; a line with the air: `streamlines` from a
  `front_rake`, which covers the car evenly, as a wind tunnel's rake does; seeded on the nose alone
  they spread far apart over the sidepods. Lines waved for a wake cross where the body narrows:
  keep the wave small (under 2 cm).
