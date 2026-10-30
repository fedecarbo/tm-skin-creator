# TSC_Trial1030

A trial car (`tool.trial`), painted by the trial painter with nothing but the instructions; the user wasn't there,
so each place the skill asks them is a guess from their words, marked (guess).

The user's words, 2026-10-30 (Claude, Opus 5.5): "Midnight blue, with a thin gold outline round the side panels and a
few small gold stars on the nose."

How I read them: a calm night car. The body one deep midnight blue. "The side panels" (the car has no part by that
name): the big panels down each side, read from the car (`tool.meshlines`): the rear flank panel behind the sidepod
(the car's main side face), with the sidepod inlet and the side skirt as the other side faces; each traced round its
own edge by one thin gold line, as a coachbuilder's pinstripe. "A few small gold stars on the nose": three to five
five-pointed stars, a few cm across, on the nose tip and nose panel, clear of the nose fin's plate.

## Events
- Language (Claude, Opus 5.5, 2026-10-30): `language.json`, "a coachbuilt car at night": midnight blue 90 %, night
  black 7 %, gold 3 % (the accent: coachlines and stars only); the signature one thin gold coachline traced just
  inside a side panel's edge, closed round it. Accepted as the user would (guess: no page shown, the user away).
  Line width: one 0.5 cm for every coachline (the judge blocks a `meshlines.panel` trim wider than 0.5 cm as short).
- Set 1, the composition, three takes (2026-10-30): A `TSC_Trial1030Lacquer` (blue, inner car black, one coachline
  round the rear flank), B `TSC_Trial1030Coachwork` (all blue, inner car too; a coachline round each side face),
  C `TSC_Trial1030Nightfall` (blue shell, inner car and wheel covers black; rear flank and sidepod inlet).
  Picture: work/build/TSC_Trial1030Lacquer_picture.png.
- Pick (guess, as the user from their words): B, "Coachwork". Its design is now this car's.
  What each big shape is for: the midnight-blue gloss body and wheel covers are the car, the night, one lacquer
  whole; the inner car satin midnight blue, so the car reads as one colour from every side; three gold coachlines
  each side, 0.5 cm, just inside the edge of the rear flank panel (the main side face, behind the sidepod), the
  sidepod inlet panel and the side skirt panel (the sill, from the sidepod's back at z -25 forward to the front
  wheel at z +149; forward of z +72 it narrows to a shelf running in under the nose's side): the signature,
  "the thin gold outline round the side panels". The nose is left clear for the stars (details pass).
- Surfaces (Claude, Opus 5.5, 2026-10-30): four steps. "The hardware": the language's night black (PA-03 satin)
  only on what's under and between (seat, belts, steering wheel and column, dashboard, engine bay, exhausts,
  driveshafts, brakes, rear dampers, the speed display's backing), so the pick's all-blue inner car still reads as one
  colour; left blue: the dampers, airbox and tail frame (their paint lands on the floor too) and the sidepod grilles
  (gold never touches black). "The tyres": RU-01 black rubber, sidewalls plain (no words, the language's never),
  Nadeo's own tread. "The lights": speed numbers, rear lights and brake slots gold, the night's first stars; the
  wheel rings a faint midnight blue, so the gold stays rare. Glass left stock and clear, so the gold lights read
  true. "Kept new": `s.dirt(0.5)`, polished, half the stock dust. Guesses (the user away): the hardware's split,
  gold lights, blue wheel rings, half the dust.
- Details (Claude, Opus 5.5, 2026-10-30): one step, "The stars": four gold (ME-07) five-pointed stars on the nose
  (`s.mark`, `marks.star(5, inner=0.45)`, the DNA's), each its own size and loosely set, none mirrored: 5.5 cm on
  the nose panel right of the middle (z 166), 3.5 cm on the nose panel left (z 152, 8 cm clear of the fin's plate),
  4.5 cm on the nose tip's left shoulder (z 178, its top turned forward, `up=(0, 0, 1)`, so all four point the
  same way from behind), 3 cm on the nose tip ahead of the panel, right (z 199). Large and medium: nothing added,
  the body and the coachlines (the composition's) are them, and the fullness, nearly empty, asks no more. Guesses
  (the user away): four stars for "a few"; asymmetric, no mirror twins, as real stars are; all upright, top forward.
- Art direction fixed (Claude, Opus 5.5, 2026-10-30): the coachlines ran mostly under the floor, in the wheel well and
  under the bonnet, so they never read as outlines; each is now a course traced closed round the face the eye sees,
  0.5 cm: the rear flank up its front curve behind the sidepod, back along the deck edge's rounded line, down just in
  front of the tail corner, over the rear wheel's opening, along the sill's lower rounded edge; the side skirt along
  its top creases, across its front at the front wheel, back along its outer edge; one line where the two share the
  edge at z -25 (it was doubled). The sidepod inlet's line dropped (it showed only as a lip, the rest under the cowl).
  The lights left gold: speed numbers, rear lights, front brake lights and wheel rings in the body's midnight blue at
  its own low level (the gold speed display made a gold cluster at the tail; the wheel rings read as electric-blue
  neon). The 4.5 cm star moved off the nose tip's rounded shoulder onto its flat top (8, 190). The language's night
  black now names the hardware it covers, its medium size no longer the inlet. Guesses (the user away): the inlet
  dropped rather than outlined; the lights in midnight blue (the language's, dim) rather than night black (off); the
  deck edge's line on its rounded edge's middle (tilt 47), seen from the side and above. The white strip in each front
  wheel at night is the night light's highlight on its ribs (relit bright red as a test, it stayed white; blue by
  day), not a light. Passed by the gate despite the two corners of the rear flank's line the judge reads as a step and
  a thin spot (see the gate's line).
- Art director's second look (Claude, Opus 5.5, 2026-10-30): seven of its eight items closed; the corners let go read
  clean to the eye. New: the stub closing the rear flank's line at z -25 was a straight joint 1.5 cm beside the
  panel's seam (an added corner). Closed (the trial painter): the loop now closes up the panel's own seam
  (`meshlines.line("rear flank seam 1")`), one upright line meeting the skirt's and the sill's in square corners
  (close looks 1-2). The edit brought back the two corner blocks (a let-go keeps only for the design it was given
  for); let go again, the same why.
- Open (Claude): at night, from behind, the front brake light strips inside each front wheel show a red rim round a
  blue core (Cam 1 alt night, Cam 2 alt night). Relit midnight blue; every stock glow kind on "brake light" and the
  wheels' brake heat swapped for another colour as a probe: no change. Cause unknown: maybe the viewer's own red,
  maybe the game's; check in the game at night, and ask the steward if it's a stock colour no call reaches.
- Ready to show (Claude, Opus 5.5, 2026-10-30), the gate passing it (two corners let go, above). Time per pass: the
  language and the three takes about 10 min; surfaces 7; details 9; art direction 10; the fix 36; the second look
  8; the closing fix and the red at night 15. About 95 min from the words to the car.
