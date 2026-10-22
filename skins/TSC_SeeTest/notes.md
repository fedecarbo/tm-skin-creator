# TSC_SeeTest

A test car (2026-10-22, Claude Fable 5.1): every stroke has a measurable right place. Painted on the footing where
the car is asked (the question tool), the design dry-run before every show, and the numbers, never the eye, decide.

## The brief (verbatim)

x is out to the car's left, y up from the ground, z forward; all in cm.

1. The whole body warm white above and deep navy satin below, split by one level line 40 cm off the ground, all the
   way round the car.
2. Both sidepod tops (the flat shelves either side behind the cockpit: the model's own panel there) matte black,
   filled right up to the panel's own edges.
3. A bright orange band 3 cm wide along the deck's rounded shoulder: the rounded edge where the engine cover's top
   rolls over into the flank, which passes through about (40, 62, -20) on the left. On its FRONT 40 cm only: from
   the end nearest the cockpit (the nose end) running back 40 cm. Both sides alike.
4. A white disc 20 cm across with a 2 cm navy ring, on each rear flank (the big side panel behind the sidepod,
   around (64, 36, -80) on the left), where it sits flat and whole, facing out.
5. The words "SEE 22" in black, 10 cm tall, on each side near the disc where they read flat, reading forward on
   both sides.
6. Small white discs 4 cm across scattered evenly over the engine cover's top (the deck behind the cockpit),
   nowhere else, none on the panels the game letters.
7. One orange ring 25 cm across pressed onto the nose at about (0, 58, 150), across the seam it crosses, on purpose.
8. Six small black dots 3 cm across, evenly spaced along the long crease that runs low along the side skirt from
   the nose back (through about (39, 19, 70) on the left), from its nose end to its tail end. Both sides.
9. Gold on the wheels (covers and rims) and a thin white ring on the tyres' sidewalls. The inner car dark grey
   satin. Nothing left in clay; the lights left as stock.

## How I read it (what the car answered)

- 1: "body" (the paint set without the wheel covers), ivory gloss, then deep navy satin under shapes.below(40).
- 2: sidepod top panel 1 (2459 cm2, z 12 to -50, x 54 to 87), both=True; panel 2 (68 cm2) isn't "the shelf".
- 3: body shell roll 2 (tilt 33, (40, 58, 38) to (40, 66, -82): y 62 at z -20, x 40; no other line within 5 cm of
  (40, 62, -20)). Its course runs TAIL first, so .reversed(), then between(start, at(s=40)): (40, 58, 38) to
  (44, 64, -1). band(3) centred on it, mirrored.
- 4: rear flank panel 1; flat room 37 cm centred (64, 36, -80): disc 20 there, ring(0.8) 20 over it (2 cm wide).
- 5: the rear flank's other flat room, 28 cm centred (81, 31, -51): the words there, 10 cm tall.
- 6: scatter of a 4 cm white disc on "engine cover" (engine cover, engine cover panel, number panel): the scatter's
  room keeps off the game's panels.
- 7: (0, 58, 150) is the nose panel (panel 1), the seam nose panel seam 1 / body shell seam 3 at z 142: ring 25
  with across=True, 3 cm wide (hole 0.76).
- 8: side skirt crease 2 (146 cm, (24, 18, 149) to (77, 22, 17), 0.7 cm from (39, 19, 70)), nose first: six
  3 cm discs at s = L(k+0.5)/6, across=True (a dot centred on a crisp line), mirrored.
- 9: "wheels" gold (covers, hub, ring, rim, wheel ring; the car says brake light shares it), TY-65 one white
  stripe on the sidewall, "inner" dark grey satin; no relight, so the lights stay stock.

## Record
- Dry run 1 (1024, 2026-10-22): the sidepod panel zone and the shoulder band reached no texels (a course's or a
  panel's zone is the 4096 map's texels: a smaller canvas gets none; checked at 4096 next). The words at the flat
  room turned 26° (bent) and shrank; teko with spacing -0.3 at (81, 31, -51) lays 10.0 cm tall, unmoved, no turn
  note (impact 22°, orbitron 28°, above the disc 29 to 33°). The skirt dots as stickers hung off the lip (7 to 83 %
  on the car; rear flank edge 1, where the body ends, is 3.2 cm from the crease): now 1.5 cm spheres on the side
  skirt, 12 dots = 91 cm². The deck scatter made 10 of 26 copies smaller than 4 cm: now a staggered lattice of 4 cm
  marks on the engine cover alone at points a scratch run showed take a whole, unmoved disc (DECK in design.py).
  The nose ring: 97 % on the car, 76 % nose panel, 22 % nose fin, across the seam at z 142 as the brief asks.
- Dry runs 2 and 3 (4096): the sidepod panel lands (4,907 cm², sidepod top alone, z 12 to -50) and the band
  (258 cm² on the body shell, z 39 to -1, y 57 to 65, both sides). At 4096 the flank disc shrank to 18.8 at
  (64, 36, -80) (rear flank crease 1 behind it at z -94): at (64, 36, -77) it lays 20.0, laid at (66, 35, -78).
  The words at (81, 31, -51) turned 20° at 4096: at (80, 31, -54), teko, spacing -0.3, 10.0 cm tall, no turn
  note. Five deck discs that fit at 1024 shrank at 4096: the lattice re-picked from a 3 cm grid at 4096 (ten a
  side, all 4.0 cm, unmoved). The skirt dots 92 cm². Shown.
- Shown (2026-10-22, version 1): painted in 32 s. Verdict: 5 findings, 1 blocking. BLOCK clear: the nose ring,
  44 cm² on the nose fin's plate, z 145 to 138 (the brief wants it across the seam at z 142 on purpose; the
  plate's 3 cm clear begins at 145, so the two can't both hold: let go, `tool.gate --despite`). Warn over: the
  white disc lies 86 % (left) / 87 % (right) across the navy split's edge, z -71 to -85 (meant: the brief puts a
  20 cm disc at y 36 on a split at y 40). Notes: the sidepod black's gap to the body's edge CLOSES 2.8 to 1.4 cm
  over 8 cm at z -22 to -30; the navy TOUCHES the sidepod black over 40.4 cm, z 0 to -39.
- Close looks: 71 looks in 13.1 s, five sheets; notes only: the sidepod panel's edge hidden by another part over
  6.5 to 12 cm stretches (looks 7, 8, 10, 12, 13, 15, 16, 18); the white disc 14 % (left) / 13 % (right) hidden
  at z -83 to -87 (looks 45, 46); the navy ring 100 % hidden on both sides (looks 47, 48: the camera square to the
  flank's back-facing surface looks through the rear wheel). Gate: passes with the one let go.
- Open (the nose ring): the let-go stands while the design is the same (despite.json). Not installed (a test car).
