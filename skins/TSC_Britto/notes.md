# TSC_Britto

The user, 2026-10-22 (Opus 5.5): "what's the name of an artist that paints each part of something with for example
red and circles, then another part with another color with some different shapes. etc. I think he uses primary and
secondary colors." (Romero Britto), then: "How about we design a car like that".

Read as: Britto's pop art on the car. Thick black outlines cut the car into a few big sections along its own lines,
each section a flat primary or secondary colour with its own pattern (dots, stripes, checks, hearts), glossy and new.

- Language written (`language.json`), shown; the user, 2026-10-22: "yep".
- Composition, set 1 (three takes cutting the car into sections by lines across its pieces: Slices, Flow, Arcs):
  dropped after the first was painted. The user, 2026-10-22: "I want you to actually paint each part differently,
  does that make sense?", "e.g tail panel is one, fuel cap, etc". The language changed: each of the car's own parts
  (the tool's part names) its own colour and pattern, a black line on every seam between two parts.
- Composition, set 2, opened 2026-10-22: A every part patterned; B calmer (the body shell plain blue, a few parts
  patterned); C two sides (each side's parts unlike their twins). The outline is the seams between parts (an edge two
  parts share, or a sewn-on piece's gap under 2.5 cm), 4 cm wide, kept 5.5 cm off the plates the game letters (plain,
  the colour round them), off the underside and the wing pylon, and off what's hidden. Let go on each: the stripes and
  waves stop under the black line, as meant.
- Closed (Claude): where the sidepod top meets its inlet the colours touch under the lip with no black line (it's
  hidden there); the lights by day and night; the glass. (The lights and glass: pass 3; the joint: pass 4.)
- Picked C, two sides (the user, in the Lab, 2026-10-22). What the composition is, for the passes to build on:
  every part of the body is a section of the picture, each its own colour and pattern (PLAN in design.py); the right
  side's sided parts (side skirt, sidepod top, sidepod inlet, rear flank, rear quarter panel, tail corner) unlike their
  left twins; the black seam outline holds it together (seams(): 4 cm, off the plates, the underside, the wing pylon
  and what's hidden); the plates plain in the colour round them; the inner car's parts solid colours (INNER); the
  wheel covers red with white dots in a yellow ring, a blue hub. Shown, judged, let go as before; close looks clean.
- Surfaces, pass 3 (Claude, Opus 5.5, 2026-10-22): the body, its outline and the wheel covers stay gloss, the inner
  car gloss plastic, as the language says. Added: the tyres plain black rubber (the black line round the car; the stock
  markings gone); the glass clear (white at 0.9: the stock grey canopy and nose lens and the black mirror glass cleared,
  so the red seat and blue steering wheel show, and the clear rear lens lets the braking red through); every light its
  own colour of the palette, none left stock (checked texel by texel): the speed numbers yellow, the gear bar along the
  tail green (blue was lost in the blue tail frame), the slots inside the front wheels purple, the front wing's lamps sun
  yellow at night, the ring round each wheel a faint orange, and each inner part's own stock lamps and strips (white,
  grey, cyan) in a palette colour that isn't its paint, at the stock brightness (LIT; the cockpit tub and nose inner
  share paint, both green). No new glows: the body can't glow, and a glowing inner part also lights the paint it shares
  (the front uprights, the floor). The car stays new on purpose, as the language's ageing says: no wear, no fading,
  and no dirt even on a dirt road (s.dirt(0)). Shown, judged; the same four pattern ends let go again; close looks clean.
- Open (Claude): the language gives white "the light in the car"; the lights took palette colours instead, as white
  reads as the stock's. The language's line may want changing (the user's call).
- Details, pass 4 (Claude, Opus 5.5, 2026-10-22): the sidepod joint, seen close: the colour there isn't hidden. The
  green round each inlet's mouth is the inner car's sidepod frame, and it touched the yellow and red sidepod tops, the
  checks, the skirts and the inlets' stripes with no black, as the blue tail frame and the purple bumper touched the
  tail corners, flanks and tail panel. Added "The outline round the inner car": a 3 cm black line on the body wherever
  it meets a coloured inner part (contacts(): a body edge within 1 cm of one, or its edge lying on the body; inside the
  inlets too), and the frame black where it shows only as a sliver (the gaps between the sidepod top, rear flank and
  skirt, and its ledge above the skirt behind the ring). Then the small size, three marks, each outlined in black
  1.2 cm round (motif()/layer(): the black and the colour from one distance field, so the line is even): a red heart
  on the cockpit surround's left, beside the driver's heart; a sun (yellow, a thin black ring, an orange core) on the
  left rear quarter panel; a green star (the language's proportions, tips and notches rounded) on the right one, the
  two sides unlike. Few on purpose: the car is full, so the marks sit on the plain pieces and read close up and from
  the chase camera. Shown, judged; six pattern ends let go (the four, and the inlets' and tail panel's stripes that
  now stop under the new line); close looks clean.
- Open (Claude): the inner car's coloured parts still touch one another with no black between them (the red rear
  strakes on the blue tail frame, the front wing's pieces, the wishbones at their joints); they stand apart in 3D, but
  the language says black between.
- Open (art director, 2026-10-23, Opus 5.5): eleven items, ranked by what shows first behind the car. Nothing fixed:
  the session was stopped while the car was still being measured, and design.py is unchanged. Shown, closed and
  gated once as it is (passes; the same pattern ends let go). The list, with what was measured:
  1. the deck: the plates and the strip between them a green hole in the waves, yellow crumbs at its edges; to be
     one plain green section outlined in black about 5.5 cm off the plates (the strip between the number panel,
     z -62 to -78, and the engine cover panel, z -81 to -120, is only 3 cm, so a margin round both covers it);
  2. the back one blue mass (tail frame, diffuser, rear arms, hubs): the hub, painted last of the inner parts,
     shares its paint with the front uprights (as do the tail frame, rear arms, sidepod frame, rear strakes...), so it
     colours them too; the hubs and the diffuser want colours unlike the tail frame and the arms;
  3. no black line where the side skirt meets the rear flank: under 15 cm, so seam_points() drops it;
  4. no line across the top of the nose: the nose panel (z 142 to 187) meets the fin's plate (z 118 to 142) edge to
     edge, so the seam lies within 5.5 cm of the plate all the way across; run it to CLEAR, or close the U below it;
  5. each inlet melts into its green frame: take green off both, the sides still unlike;
  6. the sidepod hearts scattered, not in rows: a regular grid of upright hearts, a little bigger;
  7. the checks read as long diamonds on the nose's sides, front on: the unfolding keeps them true squares (measured)
     but its rows turn up and outward there; wrap="planes" keeps the rows square to the car, untested (it may leave
     a seam where the shoulder turns from top to side);
  8. the skirts' dots flattened and bean-shaped (left front most): likely centres on the skirt's rolled lip, half out
     of sight; method="grid" lays them in rows in the unfolding;
  9. the cockpit heart a black blob close up: about 8 cm so the outline keeps its notch;
  10. slivers: 1 cm of colour between two black bands by the right rear quarter panel's checks, a white sliver at
     the left quarter panel's top corner, doubled bands where the seam line runs beside the line round the inner car
     on the cockpit surround;
  11. the white mirrors melt into the white checks (a palette colour); the sidepod grille's green dots and the
     frame's triangle holes look stock.
- 2026-10-23, the user: "Can we start wrapping things up, this has taken years!" The fixing pass stopped before its
  first edit: the art director's eleven items stay Open (in the line above), the car as the details pass left it. The
  language's white line changed to what the car does (the lights in the palette's colours), as the art director said.
- 2026-10-23, the user: "Leave it for next session". Next: the art director's items, first the deck's plain patch
  framed as a chosen section, the blue back and wheels, the two missing seam lines (side skirt to rear flank, across
  the nose); then show it in the Lab for their yes; install on the PC when it's back.
- 2026-10-23, the user, notes in the Lab (Opus 5.5): "This needs a black line to close the fin." (on the nose panel's
  top, where it meets the nose fin); "I think in general lines are too thick"; "Not sure what's going on here but
  there's a line gap here" (the left rear quarter panel and the engine cover, by the number panel); "I don't like
  when there's only a shape in a part.  Maybe for smaller parts, do dotted?" (the sun on the rear quarter panel);
  "This part needs to close the black line" (drawn: the tail corner's edge by the rear wheel); "This stroke went too
  far that it lands on the orange and white spots" (the line round the frame running from the sidepod top onto the
  rear flank); "There are now many places that have this sort of circle brush by brush and it doesn't look like a
  continuous stroke, make sure this is fixed.  Not sure. if this is lack of tools or an error".
- Change (Claude, Opus 5.5, 2026-10-23), from those notes: the lines 2.5 cm, as the language says. They were wider
  because where one piece lies over another both edges took the line (1.7 to 1.9 cm apart): now only the edge that
  sees more of the open air does, and any edge seeing 0.3 of it or more (was 0.4: the tail panel's top edge broke).
  A black line round the nose fin, closing the nose panel's U. The lines no longer drop out within 5.5 cm of the
  plates: they keep 3 cm off the deck's two plates only (the gap by the number panel). The tail corner's edge by
  each rear wheel traced from the user's line (the open air is low there, the eye sees it; the judge says the wheel
  stands in front of it seen square, let go: the user saw the gap). The line round the inner car: the surfaces read
  densely (its points came in clusters, drawn as round dabs), none on a seam (the seam's own line outlines it there,
  and the two stacked made a lopsided tab onto the flank), none in a stretch under 10 cm, and on each part only
  within 5 cm of where that part itself meets the inner car (no running on onto the next part). The three small marks
  gone; the small rear quarter panels in small dots (6 cm apart), purple with yellow on the left, orange with white
  on the right; the cockpit surround plain yellow. Shown, closed, gated (the pattern ends under the lines let go).
- Closed (art director's list, 2026-10-23): 4 (the line across the nose), 9 (the cockpit heart: gone), and the
  doubled bands of 10 (one edge per seam now). Still open from it: 1 (the deck's plain patch), 2 (the blue back),
  3 (no line where the side skirt meets the rear flank: under 15 cm), 5 to 8, 11, and the green frame showing as a
  thin line inside the seam between the sidepod top and the rear flank.
- 2026-10-23, the user, notes in the Lab (Opus 5.5): "gaps here" (the tail: the black line along the bottom of the
  tail corner and the tail panel breaks at the seam between them); "Thick stroke here, not sure why" (the tail
  corner's edge by the left rear wheel: the traced line and the flank's line round the tail frame stacked); "Not sure
  what happened here" (a black stub off the line round the right inlet's green frame, along the sidepod's crease).
  Then: "I honestly don't get why you always make mistakes like these, no matter what car im building there's so
  many bugs like that.  Like why dabs anyways? should it just be strokes or outlines? Im giving up, I thought this
  whole "car provides the reads" work was going to solve it, and this tool just keeps making silly mistakes".
- Open (Claude, Opus 5.5, 2026-10-23): the three notes above are not fixed; design.py holds an unfinished hour of
  patches (the line round the inner car: none on a flange inside the body, none in a joint of the sidepod panel,
  along a seam judged by direction and only where the seam is seen on both sides), shown but not closed or judged
  by eye. The cause of every line fault today: the outline is round dabs stamped at points found near the edges
  (near()), not a stroke, so missing, doubled or hidden points show as bumps, stubs, gaps and thick patches.
  Decided: rebuild the outline as one stroke along every part's own edge, inside the part (course.edge(part) with an
  even band, measured along the surface), two neighbours meeting in one 2.5 cm line; and a check in the tools that
  refuses a line whose edge is lumpy (IMPROVEMENTS.md). Waiting on the user: rebuild now, or stop for today.
- 2026-10-23, the user: "can you do it so I can see and if not we go back?"
- Change (Claude, Opus 5.5, 2026-10-23), for the user's look, to keep or undo: the outline rebuilt as strokes, no
  stamped dabs left. Every part's every edge loop (course.edge, loops under 15 cm left out) drawn as a band inside the
  part, measured across the surface: 2.5 cm along an edge nothing of the body meets, 1.25 cm along a seam (each part
  its half), and along an edge tucked under the one it meets, 1.25 cm past that one's edge. The inner car's edges
  lying on the body (the frames round the inlets, the bumper, the mirrors' feet): their points walked into courses, a
  band 5 cm wide centred on them (half under the frame), on each part beside them alone. The wheel covers outlined the
  same way. Shown; the judge reads the strokes as lines and blocks 63 findings, most where a stretch changes width at
  a part's corner (a step of half the line) or where a stroke runs off the body's edge; not yet judged by eye. The
  line round the inlets' rings reads thinner than the rest (half of it under the frame). Going back: design.py as
  committed in f365dcb (the dab version), or 3bfc7bf (before notes 9 to 11).
