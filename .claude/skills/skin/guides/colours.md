# Colours and materials: the CMF designer's guide

Read at the studio's step 5 (`studio.md`). CMF is what car makers call the work on colour,
material and finish. It grows with every car: at the end of the step, add what the car taught
under "Learned", dated, with the car's name.

## What good looks like

- **Few finishes, each with a reason.** Two or three on the body: a base, the graphic, a trim.
  Metal as an accent, carbon for structure (underneath, functional parts), never everything shiny.
- **Finish contrast makes hierarchy.** A matte graphic on a gloss shell reads as drawn on; the same
  colour in gloss and matte is a quiet two-tone. Contrast of shine can replace contrast of colour.
- **Colour and finish are chosen together.** Gloss deepens dark colours and shows every highlight;
  matte lightens and flattens them; metal needs curves to read, and turns dark where it mirrors a
  dark room.
- **Every light.** Day on this map has the sun ahead, so the car's backs are in shade; sunset is
  warm; at night the flat top sees the dark sky and the back faces the lit stadium (3 to 8 times
  brighter). A colour that works by day can vanish at night.
- **Exact colours.** Name them as hex from the mood board's story, and keep them the same across
  the options when the choice is the finish. Very bright saturated colours clip on screen (a light
  blue turns cyan, yellow flattens); leave headroom.

## On this car

- Finishes by phrase or Lab code (`tool/finishes.py`, `CATALOGUE`: PA paint, ME metal, PL plastic,
  RU rubber, CF carbon, LF leather and fabric, WT wraps, WE wear, PT patterns, LI light). Put them
  in a `FINISH` dict at the top of the design, part by part, so an option changes one line.
- The body's varnish: matte paint needs none, and the tool ships the file that says so. Only the
  body has a varnish; the inner car and tyres take roughness and metal.
- Fine texture lives in the sheen, not the colour: dark paint's small colour variations are lost to
  the game's compression, a grain in the roughness holds (`WT-07`). Patterns under about 8 mm don't
  read on the car. A fine grain costs zip room (the budget halves the roughness maps).
- Can't: holographic or colour-shift paint. Never seen in the game yet: candy, chrome rims,
  metallic flake, rust, leather; say so if one's picked, and ask the user to look at the road test.

## Check before showing

- The glossiest option closest: gloss shows every flaw.
- Front, rear (the highlights run over the deck from behind) and night; the chase cameras.
- Small glossy shapes on dark matte from behind: they catch the sky as white dots.

## Learned

- 2026-09-28, TSC_Ladybird: the user picked the gloss shell and asked for the grass satin "so
  there's some contrast": the finish contrast between the bug and its graphic was the point.
- 2026-09-26/27: satin black under matte black shows as grey blotches (make both matte); a
  wet-look or gloss deck washes out from behind in the viewer's light; chips down to bare metal
  read as black specks (light primer reads as wear).
