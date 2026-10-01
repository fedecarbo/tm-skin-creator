# What we learned

The tool's memory of what the game, the tests and the user taught us, by topic: search it before
changing how something works. A new lesson goes under its topic, dated, with the skin that showed
it, and replaces what it corrects. A big improvement under way keeps its working notes at the end
and folds them into the topics when done. The build's full story: `git show b0ca0e8:CHECKLIST.md`.

## Decisions

The user's standing calls on how the tool works. Technical choices stay Claude's (`CLAUDE.md`).

- **Quality and accuracy first, then speed** (2026-09-23; 2026-09-28: "We can always define
  improvements on performance, and most importantly quality and accuracy"). A better game file is
  worth a slower build (2026-09-24: "if the compressions are better then so be it... for me quality
  goes first"). The tool knows the car before it designs, and makes any kind of skin.
- **The whole car matters** (2026-09-25): "doesnt matter if its visible or not front or back, what
  matters is the quality of the entire car". Sharpness is judged close up in the game's skin editor:
  keep every edge, sticker and letter at the texel grain. Pictures: illustrations, prints and decals
  rather than photographs (2026-09-24).
- **How the user works** (2026-09-28): by reacting to the car, not through steps ("I don't really
  work that way"); "Two main things I like. It's having the car and me being able to iterate. and I
  also like a place where you can provide options before building." So: the car and their notes, and
  a set of options whenever they ask or there's a real choice (`tool/sets.py`). A new car: a short
  talk, three concepts, the guides, the critic before the game (`new-car.md`).
- **A pick deletes the other options** (2026-09-28: "I dont think we can keep on maintaining options
  that I don't like, hence maybe creating so much noise"). Git keeps them; one in the game stays.
- **The user decides only between real directions** (2026-09-28); with one sensible answer Claude
  does it and shows it. The wheels are settled car by car. Building the tool: "Build one step at a
  time, show me what it does, and wait for my OK".
- **A new car starts blank** (2026-09-28: "I don't want you to get influenced by previous builds"):
  no looks from earlier cars unless the user names one (then `borrow("TSC_X")` from `tool.skin`).
- **The Lab shows only the tool's own data** (2026-09-26: "If it doesn't come from the tool, then it
  will get outdated"). Claude's rough rounds show there live (2026-09-27).
- **Measured, then seen close up** (2026-09-29: "I don't think it's feasible to do it by eye";
  2026-10-01, every check passing: "lets stop. None of the cars make me think it's working").
  Numbers the eye disagrees with aren't done, and neither is a look with no numbers.
- **The viewer** (2026-09-23 to 27): spin, zoom, hide and show parts, four moods in one menu, a
  studio whose floor is the game's track colour, the "race garage" look (#e8ff47). Cam 1 and Cam 2
  are the game's closer cameras (`cam1alt`, `cam2alt`) through the viewer's own 32° lens ("I
  honestly hate the cam lenses... the car in the viewer looks really badly distorted"); `?lens=game`
  draws the game's. The page online carries only the skins in the game.
- **Tools** (2026-09-23, 24): Python, each library its latest release pinned in `requirements.txt`,
  the venv outside OneDrive, the car read straight from the FBX. Always suggest a one-time-payment
  tool of far better quality; a subscription needs a discussion first. In use from a search for
  useful tools (2026-09-29): potpourri3d (its exact geodesics draw every line) and libigl (a second
  curvature measure in the map's check), both with wheels for Python 3.14 on both computers. Looked
  at and left out: Substance 3D Painter (US$200 once, but painted by hand, not by words);
  Hunyuan3D-Paint and Meshy (they paint the whole mesh loosely from a sentence, ignoring the map and
  the game's format); Recraft (subscription) and Z-Image-Turbo (quality, not accuracy: revisit when
  quality is the focus); TypeSafe's Jev (it only picks from fixed answers).
- **Don't take the game's own files apart** (2026-09-24, asked twice): encrypted packs and compiled
  shaders, the licence forbids it, and it wouldn't replace tests. Fair game: Nadeo's published
  files, the stock textures, the user's screenshots and videos, a file the game's skin editor saves.
- **Models and machines**: Opus 5.5 everyday, Fable 5.1 when a design stalls. The critic is Opus 5.5
  (2026-09-28): of TSC_CriticTest's seven known faults it found six and part of one, Fable 5.1
  six. The PC: RTX 5070 Ti (16 GB), 16 GB of RAM; the Mac: M5, 16 GB. Club access, which skins need.

## The game's files

The texture table and the glow codes' list are in `.claude/rules/tool.md`.

- **`Skin_CoatR` is the varnish, and 0 means glossy** (2026-09-24, TSC_Lab, TSC_Lab_NoCoat). No file
  is glossy varnish all over, so matte paint needs 255 there: always ship it. The varnish never
  blurs the base (roughness 0 under 255 is still a mirror). The viewer's coat amount is 1 − CoatR.
- **Roughness and metalness are ordinary PBR** on body, details and tyres; `_R` holds R roughness, G
  metalness (three.js reads G and B: swizzle). Stock `Skin_R` is smooth metal under the paint. The
  tyres take a two-channel `Wheels_R` though the stock one has one channel.
- **Normal maps are OpenGL, Y up** (weak evidence: the lab's small wing domes). The body takes none.
  Nadeo's `Details_N` is mostly rounding noise (2.1 MB zipped, 0.57 MB with it flat; keep the faint
  carbon weave). The suspension arms' relief is a weave, so painted as metal they read woven:
  `s.relief(parts, lambda pos, nrm: 0, replace=True)` smooths it.
- **Dirt is a mask** (2026-09-24): 255 covers the paint with the track's dust; the stock averages
  53, so designs want moderate values. The game's number stays clean.
- **Glass is tint only**: the game reads `Glass_T`, not `Glass_D`; its alpha made no visible
  difference. A tint colours any light behind it.
- **Every texture is optional** (TSC_Test_SkinOnly, 0.21 MB): what a zip leaves out keeps the stock
  look. 4096² works; sizes can mix within a set. Install: one zip, no spaces in its name, an
  `Icon.tga`, recorded in `skins/installed.json`. The running game finds a new skin (no restart).
- **The zip budget is 8.5 MB** (`build.ZIP_BUDGET`). Nothing is documented; Ubisoft said in 2022 the
  "9mb car skin file size" "may be too big", and 8.45 and 8.65 MB zips worked. Over it,
  `build.build_zip` halves the normal maps, then the roughness maps (`Wheels_R` first); colour and
  glow stay full size. Stock grain upscaled barely compresses, so a design painting few inner parts
  hits the budget (`Details_R` alone 5.74 MB, TSC_Lights_Test).
- **What a skin can't change** (2026-09-25): the player's initials and number, lettered on the
  engine cover over the paint ("FCP 00") even in the editor, their colour set by the game mode
  (white in a race, orange in warm-up, the team's, red in danger); and the tyres' mapping (only a
  "3D skin" could, and Nadeo disabled uploaded ones in May 2024).

## Glows and the car's own lights

As last seen in the game (TSC_Lab, TSC_Lights_Test, TSC_Calibrate in four moods; standing still
unless said). `GLOWS` in `tool/finishes.py` and the viewer's `GLOW` follow it.

- **Always on (96)** keeps its colour: about 0.63 of it on the screen by day, 0.8 at night.
- **Night only (255)** is off by day and at sunrise, on at sunset and at night.
- **Front lights (128)** are off by day too (the "bright white by day" of 2026-09-24 was white
  paint), the brightest glow at sunset and night. They sit at z 192 to 213, some behind small
  lenses.
- **Brake lights (0)** are the slotted crescent inside each front wheel (part "brake light"; left
  and right share texels): dim at night at rest, near white while braking, in the skin's colour.
- **Energy (32)** glowed dim red in the garage, and stayed dark on the track in all four moods.
- **Brake heat (64)** lights the rims under hard braking: faint red at once, the painted colour by
  1.5 s, fading over about 1 s after.
- **Turbo colour (160)** lights in the pad's colour after a turbo pad, on the hubs inside all four
  wheels, for about 3 s, fading over the last half second; the sidepod frames carry it out of the
  chase cameras' sight. Nothing lights without a pad, at any speed.
- **Exhaust heat (192) and boost (224)** were never seen. The only source, xrayjay's table (linked
  by Nadeo): 192 "ON when Turbo is enabled", 224 "colored under boost input".
- **The speed digits** are part "digit display", code 96, all 21 bars on one patch: one colour. The
  game lights only the segments it needs, always three figures ("075", "000").
  `s.relight("speed numbers", colour)` keeps each texel's code and brightness. Paint dark round
  them, or the unlit segments show "888" in the body's colour.
- **The rear lights are a gear display** (code 96, behind the "rear light lens"): five bands a side
  fill from the corner, one per gear; their colour and the lens's tint multiply. Braking turns them
  red whatever their colour, and a tinted lens filters that red (cyan: teal by day, dark at night),
  so keep the rear lenses clear or warm. After a turbo pad they go red for about 1.5 s.
- **The stock inner car is full of lights** (2026-09-25): teal lamps in the cockpit tub, bulkhead
  and nose; a strip under the floor; an always-on cyan ring inside each wheel; faint night glows on
  the airboxes, sidepod frames and steering; the turbo code on the hubs, most of the suspension and
  the tail. Recolour what the design doesn't want (the critic caught the front hubs' orange on
  TSC_Ladybird).
- **A glow's edge takes the nearest texel's code**: the game blends colour between texels, not the
  code, so an unlit neighbour lit a dashed line round the tail's openings.
  `paintbox.dark_take_codes` gives the unlit texels near a glow its code.
- **`glow()` also tints the paint** (TSC_Calibrate: a night-only patch read lit by day): paint black
  over it afterwards to leave only the light.

## The game's cameras, lens and moods

- **The game's lens is wide** (fitted to the user's 2560x1440 screenshots, 2026-09-25 and 27): Cam 1
  72.8° tall, Cam 2 74.1°; Cam 1 alt 2.03 m up, 3.00 m behind, 7.7° down, 75.0°; Cam 2 alt 1.53 m
  up, 3.20 m behind, 3.3° down, 69.9° (within 2 px). The 58.7° assumed before fitted no pose: fit
  the lens, never set it by eye. In the game the cameras pull back at speed (not fitted yet).
- **How to fit one**: the tyres' edges against the model's outline, found exactly where its
  triangles' edges cross the same rows (a rasterised outline gives the solver nothing to follow),
  plus the horizon from the track's edge strips, which tells a closer camera from a wider lens
  (`least_squares`, soft L1, the overlays masked). By day only.
- **Through the viewer's 32° lens**, a Cam keeps the game camera's line to the car's middle, 7 to 14
  m back, sized so the tyres' widths match (by the middle alone the car came out too small).
- **What the chase cameras see** (2026-09-27): the tail's flat top, the deck's sides (part "engine
  cover"), and the tail frame's back face (74 % shared), whose top bar is the one clean band across
  the back; anything long along the car foreshortened by half. The top is 83 % of what the player
  sees (the shell 22 %, the engine cover 17 %, the rear flanks 14 %).
- **The game maps light to the screen straight**, clipping each channel at white: a bright
  light-blue glow turns cyan, never white. `LinearToneMapping` at 1.44 lands within 4 levels; ACES,
  AgX and Khronos Neutral were 9 to 27 off.
- **The moods' light** on the tail's top against the day: sunrise about 0.28 and neutral, sunset
  0.35 and warm, night about 0.03; by day the back faces are in shade. To get them: one map in the
  editor, the mood changed in Light settings, shadows computed after each change, a few seconds for
  the auto-exposure before F12.
- **The viewer's haze was its light** (2026-09-27): an HDR from every side lit the faces the key
  missed nearly as bright as the tops, and a full sheen lifted every dark colour like a veil. A sky
  whose sun is the key (its disc cut out, turned to the key: `envTurn`) and half the sheen (`SHEEN`)
  matched the game's greys. Night is about twice the game's on purpose ("night is too dark though").

## The car

- **Orientation** (2026-09-23): the car faces +z, y up, its left is +x (not mirrored). FBX binary
  7300 from Maya 2018, in cm: Skin_01, Details_01, Wheels_01, Glass_01. Its Skin UVs match Nadeo's
  `UV_Skin.png` (IoU 0.95; image row = 1 − v).
- **The wheels' axles are fitted, not read by eye** (TSC_CMYK_Peel_More): a ring round centres 5.7
  mm off wobbled in the game; circles fitted to the tread, bead and rims agree within 0.2 mm
  (`shapes.WHEEL_Y/WHEEL_Z`). The viewer lifts the car 1.2 cm (`lift_cm`): anything placed from the
  model's own figures needs it. The split ring at each wheel's centre is "brake caliper" (a wrong
  name); the "hub" is a fixed fairing, the brake light in its slot.
- **The meshes**: split by the exporter at every hard edge and UV seam, so vertex-connected pieces
  are the crease-and-island split. Details is a whole inner car; Wheels only the tyre ring (29 to 36
  cm). Surfaces are one-sided (the floor's middle faces down).
- **Shared texels** (2026-09-24): Skin 11 % (the four wheel covers on one set; the nose and tail
  ends), Details 82 %, Wheels 100 %, Glass 40 % (`shared` in `car/parts.json`). Mirror twins (the
  tail frame 74 %, the seat 99 %) read a word backwards on one side: use marks that read both ways.
- **Shared paint isn't only twins** (2026-09-26): the floor covers 93 % of the front wing's paint,
  and one tiny patch serves 15 kinds of inner part (the front hubs and uprights among them), so
  painting the floor, tail, engine cover, cockpit or sidepod frames paints them too. The exhaust's
  trim shares the tail frame's texels: paint the tail after it. `Skin._warn_shared` names the rest.
- **A shared texel's baked position may be another part's** (the bake keeps the last triangle): zone
  a shared Details part with `parts.load().local_bake(...)`.
- **A part border lies on a fold, never inside a smooth surface** (2026-09-24): the body shell has
  no crease over 10° but its centre seam, so it's one part and zones on it are the paint box's job.
- **The unfolding**: Nadeo's layout stretches the body shell under 5 % on 98 % of its area, one
  island; the Skin set under 10 % on 87 %; the inner car is hundreds of small pieces. Islands lined
  up across shared corners still miss by 3.9 cm (median); mirror twins can't line up.
- **Texel pitch** at 4096²: the body 0.09 cm, so a 12 cm sticker is about 130 texels and a BC1 block
  3.6 mm. Details at 2048²: about 4 mm (relief reads from 1 cm); the front wing's top about 6 a cm.
- **Flat spots** (2026-09-24): the front flank's lower half sits back under a lip along a diagonal
  fold (its top strip takes lettering only). Big stickers go on the rear flank behind the sidepod or
  the bonnet (z 91 to 142): `SPOTS`. Keep clear: the number and engine cover panels (the game
  letters them: paint them plain), the inlets, the nose fin's plate.
- **The top has a hole and a fin** (2026-09-30): the cockpit, z +70 to −45, nearest up-facing skin 8
  to 28 cm out; the "nose fin" is the bonnet's raised centre panel (84 of 94 triangles face up).
  Halfway up the side runs from 31 cm at the nose to 51 mid-car and 42 at the tail.
- **The body is nine pieces with real gaps**: the sidepod's top 4 mm off the shell, the inlet duct
  14 mm, the tail 17 mm behind the rear flank; 156 edges shared by three or more triangles; skin
  hidden under the loose panels. A band drawn across a gap is cut by it, whatever draws it.
- **The chase camera sees** of the small inner parts the rear bumper, rear strakes, undertray's
  edge, hubs, rims, sidepod frames, side vents and front wing; not the exhausts, calipers or airbox.
- **Moving bodywork** (2026-09-25, the user's video): two rear wings open from about 60 km/h and
  close below about 43, straight out then apart, not on hinges; the rear quarter panels and the nose
  panel tip up while braking. Ask how something moves before modelling it from one camera angle.

## The tyres

- **The map** (1024x2048, 2026-09-27): columns across the tyre from the inner bead (u 0, 29.8 cm
  from the axle) to the outer (u 1), the tread u 0.2 to 0.83 (35.6 to 36.4 cm); rows once round, row
  0 at 10 o'clock seen from the left, anticlockwise, about 45° per 256 rows but not evenly: read
  each row's angle from the bake. The rear tyres are 10 % wider, same texels. It's separable, so
  markings are drawn in its own rows and columns (`tool/tyres.py`), not in 3D.
- **The four share texels, and the right is the left's mirror**: words read backwards there. A
  flip-proof word (B C D E H I K O X, 0 3 8, - + = < > |, drawn upright and symmetric top to bottom,
  which B's bowls and K's arms aren't in most fonts) reads on both sides. Arrows round the wheel
  point the way it rolls on both.
- **What shows**: the covers hide the sidewall inside 30.2 cm; the stock `Wheels_AO` (a skin can't
  replace it) darkens three patches inside 31 cm and lines the stock grooves. Markings live in 30.9
  to 35.3 cm: caps of 2 to 2.5 cm. Nadeo's lettering comes off with each column set to its median.
- **Zip cost**: a marking over the stock tread adds about 1.7 MB, one with its own tread 0.3 MB, a
  slick 0.05 MB. Never yet seen in the game (`IMPROVEMENTS.md`).

## Painting

- **Patterns lie on the surface, never cut out of space** (the user, 2026-09-24): drops as 3D balls
  sliced by the body looked sunk, and any projection from outside merges or stretches where the
  surface turns. Continuous tilings (checks, stripes, weaves) use the car's own unfolding and break
  at the folds, as a real wrap would. Separate things (dots, splashes, cells) are points spread on
  the surface (`looks.surface_points`), each drawn by 3D distance: whole everywhere.
- **Prints of objects are scattered, not tiled** (the user's idea; `tool/scatter.py`): whole copies,
  each flat in one panel, the least-used picture among its neighbours, nudged, turned and shrunk
  before it's left out, bare patches filled by a second pass (TSC_IceCreamSweet).
- **Decals land on the nearest surface** (`paint.project_near`, a depth test), crossing panels like
  a sticker; the fold under them is measured. Pictures are filtered to the texel pitch first
  (`fit_to_texels`), or thin outlines break up.
- **Seams need no special code**: paint weighs each texel by the part's share of what covers it
  (`coverage.share`); the gaps between islands take the nearest island's colour
  (`raster.fill_holes`: an average left a fringe).
- **Clay and white paint look alike** (TSC_FlagPeel_CostaRica): `Skin.clay()` marks the clay and
  `still_clay()` names any part a fifth or more clay. Unpainted parts stay clay in the game too.
- **A name reaches further than it seems**: an assembly ("floor", "sidepod") takes all its parts;
  `Skin._warn_reach` says so and gives the `|part` phrase. A broader word later repaints what an
  earlier one named (TSC_IceCreamTruck's "inner" over its calipers), and a borrowed helper can
  repaint a step: read it before borrowing. Before showing a skin built on another, check every
  visible part's inherited paint.
- **Colour words and finishes**: a metal named as a colour is the metal ("gold"; "dark gold" darkens
  it). A finish name holding a colour word ("brushed titanium") is taken whole first
  (`finishes._pull`; "piano black" would lose its black).
- **Read at the car's scale**: a 3.5 mm knurl vanished, 8 mm reads; a 0.5 cm carbon weave in the
  wrap's black was invisible past arm's length, 0.8 cm and a touch lighter reads (TSC_CMYK_EndsInK).
- **Grain goes in the sheen, not the colour** (TSC_CMYK_EndsInK): BC1 keeps two 5-6-bit colours a
  4x4 block, so a few levels on dark paint go flat or blocky. A grain in the roughness map holds,
  but fills it and the budget halves it: draw grain to survive 2048² (2 to 3.5 mm specks).
- **Noise**: value noise finer than a few cm makes facets (a drop's edge at 1.25 cm came out
  many-sided, at 3 cm round); faceted noise (no smoothstep) tears like vinyl, fractal noise sprays
  specks; domain warping folds stripes into marbled swirls.
- **Gloss catches the sky**: small glossy shapes on dark matte read as white dots from behind
  (TSC_ChaosElegance_Thrown; satin fixed it); a glossy dot on a tight curve reads as a row of dashes
  (leave out dots whose normals spread over about 14°); satin black under matte black shows pale.
- **Paint can't fake big 3D shapes** (TSC_CMYK_Peel): a wrap folded back and shaded as a curl looked
  flat. Small crisp cues work: a hard-edged band, not a fade (any fade reads as a soft edge), even
  all round, since a shadow for one light looks wrong from the other side.
- **Things that read wrong**: crimson drops on black read as blood; pale marks on a dark nose read
  as eyes (TSC_Ladybird); a flag draped round a line along the car fans into a sunburst near the
  line; graphics below the flank's lower crease, where the body turns under, become slashes.
- **Low ledges catch what's meant for the sides** (TSC_Ladybird): the side skirt ahead of the
  sidepods faces up, so "whatever is low" or "faces up" takes it; spots placed without knowing where
  the top ends were cut at the shell's edge. `car/map.md` says where it ends.
- **A split by height is exact** (TSC_Split_Level, TSC_Split_Follow, 2026-09-30): a colour split "in
  the middle" seen from the side is a rule about height (a level, or a curve through the halfway
  points), continuous by construction. A curve on the surface is for lines that aren't a level.
- **Worn paint** (`tool/wear.py`): bare-metal chips mirror the room as black specks (grey primer
  reads worn); chips up to one height read as a band; small clear-coat failure reads as camo, a few
  big chalky patches on top as sun damage. It still doesn't read as worn (`IMPROVEMENTS.md`).
- **Judge gradients from full-size crops**: shrunk pictures band.

## Drawing lines on the car's skin

Since 2026-09-30: curves on the surface itself (`tool/skinmesh.py`, `skindraw.py`, `skincheck.py`).

- **A line on a car is a curve ON the surface.** Every way tried before defined it elsewhere, and
  failed for that reason: values per mesh corner on a 2 to 3.5 cm mesh facet every edge (crayon); a
  flattened sheet sheared 5.6 to 8 % on the flanks, and darts break lines; splines through pins in
  the air left the body by up to 22 cm, and pulled onto it landed on the wrong surface; a side view
  holds only on surfaces facing it (past about 53° it lands on pylons, undersides and tops), and no
  path crosses two views. Nadeo's files hold no design lines.
- **The shortest geodesic is not a drawing tool**: nose to tail it strays 278 mm and kinks 83°. A
  curve is a chain of geodesics through places the designer picks; `through` runs leg by leg, a
  corner at each place (`smooth=` rounds them). `taut` pulls the whole chain tight and passed up to
  217 mm from its places (the earlier cars keep it). A curve's places become mesh corners, or it
  runs corner to corner up to 10 mm off.
- **The skin mesh** (VERSION 4): every panel sewn across its joins and mirrored, each piece its own
  surface (welding pieces to each other twisted it), the right half keeping its own triangles, split
  into four twice (35 to 9 mm), holes under 12 cm filled.
- **A band's width is walked over the surface** by exact geodesics (a ribbon of points 0.25 mm
  apart), each texel taking its offset from the nearest: the same width on the flat and round a
  flank. It keeps to its own piece (`NEAR` under the model's gaps), stops at the curve's ends, picks
  its face by the texel's normal, and allows a 100° turn (the nose panel's groove turns 89°).
- **Other shapes**: `circle` walks a geodesic out every degree (a 220 mm ring measured 1381 mm round
  for 1382); `parallel` keeps gaps over every fold; `edge` draws in from the car's edge (14.7 mm for
  15; the heat method's contour was −18 to +22 mm out); `meet` makes a clean T.
- **Widths** (TSC_SkinExam): 2 mm is the thinnest whole line (texels 0.9 mm; 1.5 and 1 mm go
  patchy); from the chase cameras 3 to 4 mm reads as a line, 2 mm faintly. Bands measure within 0.2
  mm of their width, middles within 0.1 mm. A thin line wore a fringe (3 mm read 5) until the walks
  reached past the feather, a third of the width on a thin line, never under a texel.
- **The checker was wrong more often than the drawing.** Read the paint through the skin, not
  `carmap.Map.at` (its ±2 mm was blamed on "grain" and the limits loosened). An edge is the area
  under the coverage ramp. Sort each texel into the nearest colour drawn (`palette`); a blend of two
  colours can sit nearest a third, so read past an edge 2 mm on. A check of the paint against the
  curve passed while the curve missed its places by 9 to 22 cm: check the route too.
- **A check that cannot fail measures nothing**: `--falsify` moves every curve 5 mm, and every band
  must fail (it reads the move back as 4.99 to 5.01).

## The car map

`tool/carmap.py` and `car/map.md` (read before every design). Lines are no longer drawn from it; its
areas, what's open, the air and the chase cameras are still used.

- **Open** (2026-09-29): depth maps in 200 directions, cosine-weighted, the inner car in the way:
  the inlets, under the nose and the wheel pockets come out hidden. `Map.at` finds the body under a
  point, the nearest facing the same way (a panel lying on another isn't mistaken for it).
- **The areas** (`shapes.area`: top, sides, under) are cut by the shoulder's and the lower edge's
  fitted curves and the mesh's own edges, nothing else. The skin has no front or back face (facing
  within 45° of ahead only 411 cm², of behind 960 cm²). Behind the sidepods (z −95 to −35) there's
  no lower edge: the flank rolls under out of sight.
- **The air**: `hit` is the Newtonian rule (facing forward, squared) times how open a spot is from
  ahead; the flow is a potential solved over the welded body, walls only where the air runs into an
  opening. Turning the air locally made lines jog like circuit traces; a solved flow bends early and
  never merges two lines. Smoke lines want a rake across the whole width (`front_rake`).
- **What failed, one line each**: a threshold on each slice's facing puts a line wherever it falls,
  not on the crease; a girth summed round each slice moved bands 17 cm between neighbours; values
  per vertex make staircases; a 35° dihedral finds nothing on rounded edges; cm limits per 1 cm
  slice let a line zigzag. The crisp marks were always the model's own edges.
- **The two computers disagree** (2026-09-29): the Mac traces 66 ridges and 12 folds where the PC
  has 62 and 8 (tiny numpy and BLAS differences), so `area("top")` and `across` differ a little.

## The viewer, the Lab and the page online

- **Draw only when something changed** (2026-09-28): `setAnimationLoop` draws at the screen's rate
  (239 Hz here): the Lab's two cars cost 70 % of a core standing still, 1 % after. Anything that
  moves by itself must call `rouse`. Same-origin iframes share the main thread: a hidden viewer
  slows the visible one. A first visit is mostly shader compiling (2.5 s of 5.4); a reload 1.2 s.
- **Zooming never distorts the car; moving the camera does** (2026-09-27): a fixed 32° lens just
  sees less across a narrow window. Frame the car by its own outline (swept all round, only a tenth
  wider), centre the outline rather than the car, and let a glide carry the framing.
- **three.js**: materials whose `onBeforeCompile` differs need their own `customProgramCacheKey`;
  `Reflector` mirrors along the mesh's own +z (turn the mesh, not the geometry); a ground shadow's
  depth pass must be depth-tested; `scene.environmentRotation` turns the sky the other way to its
  Euler; hidden parts must cast no shadow. CSS: a rule scoped by a parent id also reaches its menus;
  a transform widens `getBoundingClientRect` but not the layout.
- **The studio** (2026-09-27): a curved cove shows its bend however smooth unless lit as flat floor;
  a shiny floor catches the sky's bright spots, so it's matte; a floor grain shrinks into the
  mipmaps fast (a 40 cm repeat holds). A vignette darkens the studio, never the car.
- **Motion is the game's**: the pad's pace, gears and braking are read frame by frame from the
  user's videos (`PACE`, `GEAR_UP`, `BRAKE`); timings by eye had been off every time. Wheels ease
  off to about 4 turns a second (290° a frame at 400 km/h can't show).
- **Notes on the car** (`.notes/notes.json`, off git: answers and states would churn a public file):
  the server's threads, the hook and the command line share one file under an mkdir lock. The server
  answers this computer's pages only (Host localhost, a matching Origin, a JSON body). After a
  change to the server, restart whatever serves 8765: old servers kept old code in memory.
- **The page online** (2026-09-25): 2048² JPEG at quality 90, 4:4:4, is only softer than 4096², and
  a 4096² texture takes about 90 MB of graphics memory with mips, too much on a phone.
  `tool.publish` force-pushes one commit to `gh-pages`, which Pages must be set to serve; clones
  leave that branch out of their fetches (a negative refspec, set by the hook).
- **Snapshots hold to the pixel** from run to run, so a change that leaks into them shows at once.
  The Lab's embed-only changes must leave them and the page online unchanged.
- **Codes the user copies never reorder** (`finishes.CATALOGUE`, the tyres' TY and TR): a new one
  goes at the end of its family, a retired one leaves None.

## Compression and building

- **Our own encoders** (`tool/dds.py`): Pillow's BC4 put 1 % of glow texels on the wrong code; its
  BC1 was 5 dB worse, with fringes (the user saw pixelated stickers). `dds.bc1_blocks` (principal
  axis, least squares, a local search) is on a par with texconv: quality over build time (the
  user, 2026-09-24). Each distinct block is encoded once (2026-10-01), so it's quick as well.
- **ATI2's first block is channel 0** (X in a normal map, roughness in `_R`), as Nadeo's files store
  it, with "A2XY" in the bit-count field; the first test's chrome nose confirmed it in the game.
- **Mips keep glow codes exact**: Nadeo's own average them (35 % off-code at mip 6); ours
  point-sample the alpha. Colour is averaged in linear light. Legacy headers, a full mip chain.
- **Painting is most of a show** (20 to 60 s a car on the Mac, more on the PC). The nearest covered
  texels are kept (`Canvas.near`), `Skin.textures()` is built once, and a step's picture for the Lab
  rebuilds only the texture sets painted since the last step. The UV map's data rebuilds only when
  `paintbox.SIZES` or `UVMAP_VERSION` change: bump it when `export_uvmap` or `_surfaces` write anew.
  Paints take turns (`skin.paint_slot`): each needs a few GB, and three at once killed two.
- **The self-test** (`tool/selftest.py`) paints skins with this code and an earlier commit's and
  compares them byte for byte. A change to what a cache holds must change its name or version.

## The picture maker

- **FLUX.2 [klein] 4B** (Apache 2.0) through diffusers, on the PC's card only: the text encoder and
  the transformer (8 GB each) load one after the other; PyTorch's CUDA 13 build covers the card and
  Python 3.14. Cut-outs are drawn on plain white (BiRefNet through rembg), tiles on a torus.
- **A few large objects come out crisp, a dozen small ones mushy**: ask for four and scale on the
  car. Two runs with the same words share a folder, the second overwriting the first: give each
  style its own slug. A picture's "landed" share is counted in half-centimetre cells, not pixels.

## Working on this repo

- **Long heredocs through Git Bash get cut off** ("unexpected EOF"): write the script to the
  scratchpad with the Write tool and run it.
- **GNU sed reads backslash-backtick as the start of the text**, and a Python string that isn't raw
  reads a Windows path's backslash-and-digits ("2225070") as a character code: both corrupted pushed
  files. Edit docs with the Edit tool.
- **The Edit tool reads `$'` in a replacement as a JavaScript replace pattern** (it pasted in the
  rest of the file): keep that pair out of edits, or write the line with a script.
- **Windows refuses to replace a file another program has open** (the page's poll, OneDrive,
  Defender): files the pages read are written whole by `paths.write`, which retries. An `os.mkdir`
  lock is atomic and works across processes.
- **Measure before guessing**: the Lab's slowness was timed in headless Edge first (the load, long
  tasks, the browser's CPU summed over its child processes).
- **Check the viewer against the game before building a fix** (2026-09-25): its lens glass already
  filtered the braking red, as the game does.
- **Agents load when a session starts**: a new or changed `.claude/agents/*.md` reaches the next
  session; until then give a general-purpose agent the same text.
- **`car/parts.json` shows up changed**: delete the work folder's `parts_stats.json` and run
  `tool.parts`. **ambientCG wants a User-Agent** (a bare Python one gets 403).

## The deep tidy-up (2026-10-01)

The user: "I've made lots of iterations on the tool and I'm kind of concerned that it's become a bit
messy? Or slow? ... Making it simple wherever it can, make sure things work properly and is
optimised properly." Done on the Mac, each step checked by `tool/selftest.py` (written first):
every skin paints the same textures, game files, notes and record as commit b0ca0e8 (`--all`: 48 of
50 designs identical; the other two, the cars that draw smoke lines, corrected on purpose, below),
and the viewer's snapshots are the same to the pixel. The PC's check is queued in `IMPROVEMENTS.md`.

- **Encode each distinct block once.** A painted body map is about 2 % distinct 4x4 blocks
  (TSC_Solstice: 22,489 of 1,048,576), and every BC1 and BC4 block is encoded on its own (no
  statistics across blocks), so encoding the distinct ones and copying them gives byte-identical
  files. `np.unique` on the blocks viewed as `np.void` takes 0.08 s; `np.unique(axis=0)` 6.6 s.
- **Sparse coverage looked faster and wasn't.** Working on the parts' own texels instead of the
  whole 16.7M-texel map gives the same floats but took 2.3 to 3 s a call against 0.14 to 0.17 s
  for the dense sums: numpy's whole-array passes are cheap, gathers and unions aren't.
- **Measure the paint before caching it.** TSC_CMYK_EndsInK paints in 23 s on the Mac, its cost
  spread thin (distance transforms 2.8 s, blends 2.1 s, noise 3 s, coverage 2.9 s, the canvases'
  set-up 3.8 s, the peel 5 s): no cache on disk is worth a gigabyte for that.
- **Don't merge look-alike code that rounds differently.** The three float-to-uint8 conversions
  (float32 against float64) differ by one level on about 4 % of painted values, and the normal
  maps' Z is rebuilt by two formulas that differ in the last bit: merging either changes files.
- **A timing in a note isn't the paint:** the self-test leaves "(8 s)" out of the notes it compares.
- **The viewer drew a parked car every frame:** 2,880 draw calls in 3 still seconds on the page
  online. Every page now draws only when something changes (0 at rest), and every frame while
  driving or coasting, as before. Claude's snapshots still draw every frame.
- **The page online showed the Lab's link** (to a page it doesn't publish) as soon as a skin
  loaded: the viewer rewrites its address to `./lab.html?skin=...`, which `a[href="./lab.html"]` in
  `public.css` no longer matched.
- **Hidden parts cast shadows:** only Skin and Details had the depth material that skips them, and
  the floor's soft shadow was drawn again only when a whole mesh was hidden.
- **Install reused a kept paint by its design's date,** blind to the designs it borrows (chains five
  deep), its pictures and the tool. It always paints now: one paint, far cheaper than a stale car.
- **The car map's memos remembered the wrong points** (TSC_WindTunnel, TSC_Map_Air): they matched a
  call by its points' count and first and last points, and the smoke lines' traced points keep their
  ends while their middles move, so 480 of 7,540 lookups (349 of 2,990 on TSC_Map_Air) got a
  neighbour's answer. They compare all the points now: a few smoke lines shift a little, the same
  designs. `car/map/air.jpg` was taken before the fix; retake it with the map's next rebuild.
- **A check stays apart from what it checks:** `skincheck` keeps its own copies of what it shares
  with `skindraw` rather than importing them.
- **"Couldn't show the skin: [object Event]"** was a file that failed to load, rarely, on a busy
  computer, in the old code too. The viewer now names the file.
- **Cancelled `.hdr` requests** (`net::ERR_ABORTED`) show in the old and the new viewer alike, and
  the car still comes up: harmless.

Timings on the Mac, with other work running (before, after):

| | before | after |
|---|---|---|
| a zip built (TSC_CMYK_EndsInK, two maps halved) | 147 s | 29 s |
| an install's paint and build (TSC_CMYK_EndsInK) | about 170 s | about 52 s |
| a car's game files encoded (the self-test's 13 cars) | 33 to 87 s | 4 to 26 s |
| a show's paint and its 8 step pictures (TSC_CMYK_EndsInK) | 47 s | 43 s |
| the page online at rest, draw calls in 3 s | 2,880 | 0 |

Left alone, on purpose: the car map's algorithms (the Mac and the PC trace different ridges:
`IMPROVEMENTS.md`); drawing on the skin, paused by the user; re-routing the `taut` cars (it changes
their paint); the viewer's shaders (no measured cost); an indexed `car.bin` (GitHub Pages already
gzips it, 11.5 to 2.1 MB); baking the skies in Python (its half-float rounding differs from the
browser's); the step records' unused fields (harmless data); the viewer's calibration settings in
its address (the wings', air brakes' and plate's), kept for the open fine-tuning items.

## Under way: working notes

### Drawing on the skin

`IMPROVEMENTS.md`, "Drawing on the skin"; its lasting lessons are in the topic above.

- **How it works now**: `PY -m tool.skinmesh --build` makes the surface; a design draws with
  `skindraw.through`, `taut`, `parallel`, `circle`, `loop`, `mirror`, `edge`, `meet`, and paints a
  curve with `band`. A place is a name, (x, y, z) in cm with the way it faces ("up"), or a pinned
  line from `car/lines.json` (`through(["side crease"])` runs through the user's six pins).
  `PY -m tool.skincheck <name>` (`--falsify`) measures every band. Test cars: TSC_Skin, TSC_SkinMore,
  TSC_Solstice (the first crafted livery), TSC_SkinExam, TSC_Split_Level and TSC_Split_Follow.
- **The exam** (2026-10-01; the user: "I would like to put it as a test"): pinstripes 4 to 1 mm, a
  double coachline on the user's crease, lines ending on it, a line 15 mm off the cockpit's rim,
  square corners, a chevron, a crossing, the 70 mm nose band. 15 of 17 pass (the 1.5 and 1 mm
  pinstripes). It found `through` missing its places, the thin lines' fringe, the facing gate, holes
  in the skin and the checker's own errors: all fixed, and the earlier cars re-measured.
- **Left**: the nose band over the bonnet's centre fin (±12 mm); the hoop wobbles 1.8 mm and a third
  can't be measured down the flanks; whether the hole and stray-paint judgements can be trusted; a
  filled area bounded by a drawn curve; flagged spots (TSC_Skin's flank sweeps, 40 mm² of holes at a
  panel joint at z −82; SkinMore's two middle stripes and Solstice's cream stripe, 3 to 6 mm² at
  their ends). The black and gold pinstripe livery the user picked after the exam isn't started.
- **The user, after the exam: "lets stop. None of the cars make me think it's working."** The
  numbers didn't convince them by eye. Before building more, ask what they'd need to see, and don't
  count a check passing as the item working.

### The car map

`IMPROVEMENTS.md`, "The car map". Work on it goes through `.claude/agents/car-mapper.md`.

- **What it holds**: `open`, `along`, `across`, the areas, `Map.at`, the air (`hit`, the flow,
  `streamlines`, `rake`, `front_rake`), what the chase cameras see, and the shoulder, lower edge and
  8 folds as fitted curves (least-squares B-splines, a knot every 15 cm, evidence within 4.5 mm at
  the 95th). `PY -m tool.carmap --describe` writes `car/map.md`; `--check` prints every measure
  against its limit (`tool/mapcheck.py`). Test cars: TSC_Map_*.
- **Still used**: `car/map.md` before every design, the areas, what's open, the air
  (TSC_WindTunnel's smoke lines) and the chase layer. `shapes.line` only shows the map's lines on
  its test cars.
- **From the handover, still true**: `open`, `hit`, the flow, `along` and `Map.at` can be trusted,
  but were checked close up only here and there. Judge a line close up, never from whole-car sheets:
  `tool.snap --body` and `--stretches` (wheels off, both sides), enlarged where the body changes,
  then on the flat texture. Say what's still off before calling anything done.
- **Waiting and left**: the user's look at `car/map/lines.jpg` and `areas.jpg` before anything built
  on them is called done (TSC_WindTunnel waits too); then what each game camera shows, flat spots
  measured rather than typed (`SPOTS`), a check for graphics crossing a fold or an opening, streaks
  along the flow, and the two computers' difference.
