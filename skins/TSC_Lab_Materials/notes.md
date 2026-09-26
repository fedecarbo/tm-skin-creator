# TSC_Lab_Materials

The Lab's test chart (2026-09-26, Opus 5.5). It isn't a skin to drive for looks. It's every
material new to the Lab, each on its own patch, so the game can be read against the Lab
(http://localhost:8765/lab.html). When the user has driven it and sent screenshots, each
material the game confirms gets `source="game"` in `tool/finishes.py`. Anything that looks off
gets its numbers fixed there, and the Lab shows the change.

What to do in the game: look at it in the garage from both sides, then drive it by day and at
night. Take F12 screenshots of the left side, the right side, the wheels and the cockpit.

## The key

The body has ten bands down each side, nose to tail, with thin matte black gaps.

| Band | Left side (the car's left) | Right side |
|---|---|---|
| 1 (nose tip) | PA-05 Chalk, white | CF-02 Gloss carbon |
| 2 | PA-06 Wet look, racing red | CF-03 Plain-weave carbon |
| 3 (front wheel) | ME-05 Stainless steel | CF-06 Fibreglass |
| 4 | ME-08 Brass | PL-02 Satin plastic, royal blue |
| 5 (cockpit front) | ME-10 Rose gold | PL-04 Soft-touch, charcoal |
| 6 | ME-12 Black chrome | PL-05 Textured plastic, light grey |
| 7 (sidepods) | ME-13 Bead-blasted titanium | PL-06 Acrylic, black |
| 8 | WT-04 Chrome wrap | PL-07 Sparkle plastic, purple |
| 9 (rear wheel) | WT-05 Brushed wrap | WT-02 Gloss wrap, orange |
| 10 (tail) | WE-08 Muddy, over white | WT-03 Matte wrap, olive |

- **Wheel covers** (all four share one paint): the disc is RU-04 Knurled grip, the ring RU-03
  Silicone in teal, the hub RU-02 Soft rubber.
- **Tyres:** RU-05 Worn rubber.
- **Inner car:**
  - the seat: LF-03 Perforated leather;
  - the steering wheel: LF-04 Suede;
  - the sidepod panels: LF-07 Denim;
  - the sidepod frames: neon blue, LI-02 Night glow (lit at night only);
  - everything else: charcoal satin.

## Record

- Made 2026-09-26 with the Lab (CHECKLIST.md, "The Lab", step 1). Not installed yet: install
  it on the Windows PC with `tool.skin install TSC_Lab_Materials`.
