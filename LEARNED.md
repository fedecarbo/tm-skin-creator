# What we learned

The tool's memory of what the game, the tests and the user taught us, by topic: search it before
changing how something works. A new lesson goes under its topic, dated, with the skin that showed it,
and replaces what it corrects. A big improvement under way keeps its working notes at the end and folds
them into the topics when it's done. The build's full story is in git: `git show b0ca0e8:CHECKLIST.md`.

## Decisions

The user's standing calls on how the tool works. Technical choices stay Claude's (`CLAUDE.md`).

- **Quality and accuracy first, then speed** (2026-09-23; 2026-09-28: "We can always define
  improvements on performance, and most importantly quality and accuracy"). A better game file is
  worth a slower build (2026-09-24: "if the compressions are better then so be it... for me quality
  goes first").
- **The foundation first, and a universal tool** (2026-09-23): the tool truly knows the car, every part
  and material checked in the game, before design tools; any kind of skin, not a set of styles.
- **The whole car matters** (2026-09-25): "doesnt matter if its visible or not front or back, what
  matters is the quality of the entire car". Sharpness is judged close up in the game's skin editor
  (2026-09-24): keep every edge, sticker and letter at the texel grain. Pictures: illustrations,
  prints and decals rather than photographs.
- **How the user works** (2026-09-28): by reacting to the car, not through steps ("I don't really work
  that way"); "Two main things I like. It's having the car and me being able to iterate. and I also
  like a place where you can provide options before building." So: the car and their notes, and a set
  of options whenever they ask or there's a real choice (`tool/sets.py`). One design when the idea is
  clear, two or three when it's vague. A new car: a short talk, three concepts, the guides, the critic
  before the game (`new-car.md`). Claude's rough rounds show live in the Lab ("I like to see the work
  going on, so yes", 2026-09-27).
- **A pick deletes the other options** (2026-09-28: "I dont think we can keep on maintaining options
  that I don't like, hence maybe creating so much noise"). Git keeps them; an option in the game stays.
- **The user decides only between real directions** (2026-09-28); with one sensible answer Claude does
  it and shows it. The wheels are settled car by car ("the wheels in general is a full workflow").
  Building the tool: "Build one step at a time, show me what it does, and wait for my OK".
- **A new car starts blank** (2026-09-28: "I don't want you to get influenced by previous builds"): no
  looks from earlier cars unless the user names one (then `borrow("TSC_X")` from `tool.skin`). What the
  game taught about the car still counts.
- **The Lab shows only the tool's own data** (2026-09-26: "If it doesn't come from the tool, then it
  will get outdated"). A gap in the Lab is a gap in the tool.
- **Measured, then seen close up** (2026-09-29: "I don't think it's feasible to do it by eye";
  2026-10-01, every check passing: "lets stop. None of the cars make me think it's working"). Numbers
  the eye disagrees with aren't done, and neither is a look with no numbers.
- **The viewer** (2026-09-23 to 27): spin, zoom, hide and show parts, four moods (day, sunrise, sunset,
  night) in one menu; a studio, not the stadium, its floor the game's track colour; the "race garage"
  look (skins down the left, slanted Teko, one accent #e8ff47). Cam 1 and Cam 2 are the game's closer
  cameras (`cam1alt`, `cam2alt`) through the viewer's own 32° lens ("I honestly hate the cam lenses...
  the car in the viewer looks really badly distorted"); `?lens=game` and `tool.snap --cams` draw the
  game's. The page online carries only the skins in the game (2026-09-25).
- **Tools** (2026-09-23, 24): Python, each library its latest release pinned in `requirements.txt`, the
  venv outside OneDrive, the car read straight from the FBX. Always suggest a one-time-payment tool of
  far better quality; a subscription needs a discussion first. Paid material libraries add nothing:
  the game takes only colour, matte, metal and varnish per texel.
- **Don't take the game's own files apart** (2026-09-24, asked twice): encrypted packs and compiled
  shaders, the licence forbids it, and it wouldn't replace tests. Fair game: Nadeo's published files,
  the stock textures, the user's screenshots and videos, a file the game's skin editor saves.
- **Models and machines**: Opus 5.5 for everyday work and the critic, Fable 5.1 the step-up when a
  design stalls. The PC: RTX 5070 Ti (16 GB), Ryzen 7 5800X3D, 16 GB of RAM; the Mac: M5, 16 GB. The
  user has Club access, which custom skins need.

## The game's files

The texture table and the glow codes' list are in `.claude/rules/tool.md`.

- **`Skin_CoatR` is the varnish, and 0 means glossy** (2026-09-24, TSC_Lab, TSC_Lab_NoCoat). No file
  is glossy varnish all over, so matte paint needs 255 there: always ship it. The varnish never blurs
  the base (roughness 0 under 255 is still a mirror). The viewer's coat amount is 1 − CoatR.
- **Roughness and metalness are ordinary PBR** on the body, details and tyres; `_R` holds R roughness,
  G metalness (three.js reads G and B: swizzle). Stock `Skin_R` is smooth metal under the paint. The
  tyres take a two-channel `Wheels_R` though the stock one has one channel.
- **Normal maps are OpenGL, Y up** (the lab's wing domes read raised; weak evidence). The body takes
  none. Nadeo's `Details_N` is mostly rounding noise (three texels in four within 1.5/255 of flat:
  2.1 MB zipped, 0.57 MB with it flat; keep the faint 1 to 2 % carbon weave). The suspension arms'
  relief is a weave: painted as metal they read woven (`s.relief(parts, lambda pos, nrm: 0,
  replace=True)` smooths it).
- **Dirt is a mask** (2026-09-24): 255 covers the paint with the track's dust; the stock mask averages
  53, so designs want moderate values. The game's number stays clean.
- **Glass is tint only** (2026-09-24): the game reads `Glass_T`, not `Glass_D`; its alpha made no
  visible difference. A tint colours any light behind it.
- **Every texture is optional** (TSC_Test_SkinOnly, 0.21 MB): what a zip leaves out keeps the stock
  look. 4096² works (TSC_Test_Sharp), and sizes can mix within a set.
- **The zip budget is 8.5 MB** (`build.ZIP_BUDGET`). Nothing is documented; Ubisoft said in 2022 the
  "9mb car skin file size" "may be too big", and 8.45 and 8.65 MB zips worked. Over it,
  `build.build_zip` halves the normal maps, then the roughness maps (`Wheels_R` first); colour and
  glow stay full size. Stock grain upscaled barely compresses, so a design painting few inner parts
  hits the budget (`Details_R` alone 5.74 MB, TSC_Lights_Test).
- **Install**: one zip per skin, no spaces in its name, an `Icon.tga`, recorded in
  `skins/installed.json`. No restart needed (2026-09-25): the running game finds a new skin.
- **What a skin can't change** (2026-09-25): the player's initials and number, which the game letters
  on the engine cover over the paint ("FCP 00"), even in the editor (the game mode sets their colour:
  white in a race, orange in warm-up, the team's, red in danger); and the tyres' mapping (only a "3D
  skin" could, and Nadeo disabled uploaded ones in May 2024).
- **The shaders add ambient occlusion themselves**: never bake it in. The stock `Wheels_AO`, which a
  skin can't replace, darkens patches on every tyre (below).

## Glows and the car's own lights

As last seen in the game (TSC_Lab 2026-09-24, TSC_Lights_Test 2026-09-25, TSC_Calibrate in four moods
2026-09-27; standing still unless said). `GLOWS` in `tool/finishes.py` and `GLOW` in the viewer follow it.

- **Always on (96)** keeps its colour: about 0.63 of it on the screen by day, 0.8 at night.
- **Night only (255)** is off by day and at sunrise, on at sunset and at night.
- **Front lights (128)** are off by day too, on at sunset and at night, then the brightest glow (the
  "bright white by day" of 2026-09-24 was white paint). They sit at z 192 to 213: the front wing's ends
  and hooks, some behind small lenses.
- **Brake lights (0)** are the slotted crescent inside each front wheel (part "brake light"; left and
  right share texels): dim at night at rest, near white while braking, in the skin's colour.
- **Energy (32)** glowed dim red in the garage and editor, and stayed dark on the track in all moods.
- **Brake heat (64)** lights the rims under hard braking: faint red at once, the painted colour by
  1.5 s, fading over about 1 s after.
- **Turbo colour (160)** lights in the pad's colour after a turbo pad, on the hubs inside all four
  wheels, for about 3 s, fading over the last half second; the sidepod frames carry it out of the chase
  cameras' sight. Nothing lights without a pad, at any speed.
- **Exhaust heat (192) and boost (224)** were never seen. The only source, xrayjay's table (linked by
  Nadeo): 192 "ON when Turbo is enabled", 224 "colored under boost input".
- **The speed digits** are part "digit display", code 96, all 21 bars on one patch: one colour. The
  game lights only the segments it needs, always three figures ("075", "000").
  `s.relight("speed numbers", colour)` keeps each texel's code and brightness. Paint dark round them,
  or the unlit segments show "888" in the body's colour.
- **The rear lights are a gear display** (code 96, behind the "rear light lens"): five bands a side
  fill from the corner, one per gear; their colour and the lens's tint multiply. Braking turns them
  and the centre piece red whatever their colour, and a tinted lens filters that red (cyan: teal by
  day, dark at night), so keep the rear lenses clear or warm. After a turbo pad they go red ~1.5 s.
- **The stock inner car is full of lights** (2026-09-25): teal lamps in the cockpit tub, bulkhead and
  nose; a strip under the floor; an always-on cyan ring inside each wheel; faint night glows on the
  airboxes, sidepod frames and steering. The turbo code covers the hubs, most of the suspension and
  the tail's fins and undertray. Recolour what the design doesn't want (the critic caught the front
  hubs' stock orange at night on TSC_Ladybird).
- **A glow's edge takes the nearest texel's code**: the game blends colour between texels, not the
  code, so an unlit neighbour of another code lit a dashed line round the tail's openings.
  `paintbox.dark_take_codes` gives the unlit texels near a glow its code.
- **`glow()` also tints the paint** (TSC_Calibrate: a night-only patch read lit by day): paint black
  over it afterwards to leave only the light.
- **Check the viewer against the game before building a fix** (2026-09-25): its lens glass already
  filtered the braking red, as the game does.

## The game's cameras, lens and moods

- **The game's lens is wide** (fitted to the user's 2560x1440 screenshots, 2026-09-25 and 27): Cam 1
  72.8° tall, Cam 2 74.1°; Cam 1 alt 2.03 m up, 3.00 m behind, 7.7° down, 75.0°; Cam 2 alt 1.53 m up,
  3.20 m behind, 3.3° down, 69.9° (within 2 px). The 58.7° assumed before fitted no pose: fit a lens,
  never set it by eye. In the game the cameras pull back at speed (not fitted yet).
- **How to fit one**: the tyres' edges scanned in from the track against the model's outline found
  exactly where its triangles' edges cross the same rows (a rasterised outline gives the solver nothing
  to follow), plus the horizon from the track's edge strips, which tells a closer camera from a wider
  lens (`least_squares`, soft L1, the overlays masked). By day only.
- **Through the viewer's 32° lens**, a Cam keeps the game camera's line to the car's middle and the
  middle's height in the picture, 7 to 14 m back, sized so the tyres' widths match (sizing by the
  middle alone drew the car too small: the wide lens enlarges the near tyres).
- **What the chase cameras see** (2026-09-27): the tail's flat top, the deck's sides (part "engine
  cover"), and the tail frame's back face (74 % shared with its twin), whose top bar is the one clean
  band across the back. Anything long along the car is foreshortened about half from Cam 1. The top is
  83 % of what the player sees (the shell 22 %, the engine cover 17 %, the rear flanks 14 %).
- **The game maps light to the screen straight**, clipping each channel at white: a bright light-blue
  glow turns cyan, never white. `LinearToneMapping` at 1.44 lands within 4 levels; ACES, AgX and
  Khronos Neutral were 9 to 27 off.
- **The moods' light** on the tail's top against the day: sunrise about 0.28 and neutral, sunset 0.35
  and warm, night about 0.03; by day the back faces are in shade (the sun ahead on that map). Getting
  them: one map in the editor, the mood changed in Light settings, shadows computed after each change,
  a few seconds for the auto-exposure before F12.
- **The viewer's haze was its light** (2026-09-27): an HDR from every side lit the faces the key missed
  nearly as bright as the tops, and a full sheen lifted every dark colour like a veil. A sky whose sun
  is the key (its own disc cut out, turned to the key: `envTurn`) and half the sheen (`SHEEN`) matched
  the game's greys. Not matched: the finishes' reflections and the sun's direction. Night is about
  twice the game's on purpose ("night is too dark though").

## The car

- **Orientation** (2026-09-23): the car faces +z, y up, its left is +x (not mirrored, the game showed).
  FBX binary 7300 from Maya 2018, in cm: Skin_01, Details_01, Wheels_01, Glass_01. Its Skin UVs match
  Nadeo's `UV_Skin.png` (IoU 0.95; image row = 1 − v).
- **The wheels' axles are fitted, not read by eye** (TSC_CMYK_Peel_More): a ring round centres 5.7 mm
  off wobbled in the game; circles fitted to the tread, bead and rims agree within 0.2 mm
  (`shapes.WHEEL_Y/WHEEL_Z`). The viewer lifts the car 1.2 cm (`lift_cm`): anything placed from the
  model's own figures needs it. What turns: tyre, rim, the ring at the bead, covers, the split ring
  ("brake caliper", a wrong name); the "hub" is a fixed fairing, the brake light in its slot.
- **The meshes**: split by the exporter at every hard edge and UV seam, so vertex-connected pieces are
  the crease-and-island split (Skin 133, Details 1918, Wheels 4, Glass 36). Details is a whole inner
  car; Wheels only the tyre ring (29 to 36 cm). Surfaces are one-sided (the floor's middle faces down).
- **Shared texels** (2026-09-24): Skin 11 % (the four wheel covers on one set; the nose and tail ends),
  Details 82 %, Wheels 100 %, Glass 40 % (`shared` in `car/parts.json`). Mirror twins (the tail frame
  74 %, the seat 99 %) read a word backwards on one side: use marks that read both ways.
- **Shared paint isn't only twins** (2026-09-26): the floor covers 93 % of the front wing's paint, and
  one tiny patch serves 15 kinds of inner part (the front hubs and uprights among them), so painting the
  floor, tail, engine cover, cockpit or sidepod frames paints them too. The exhaust's trim shares the
  tail frame's texels: paint the tail after it. `Skin._warn_shared` names what else takes 5 % or more.
- **A shared texel's baked position may be another part's** (the bake keeps the last triangle): zone a
  shared Details part with `parts.load().local_bake(...)`.
- **A part border lies on a fold, never inside a smooth surface** (2026-09-24): the body shell has no
  crease over 10° but its centre seam, so it's one part and zones on it are the paint box's job. The
  few cuts left (tread from sidewall at 34.5 cm) are anti-aliased distance fields.
- **The unfolding**: Nadeo's layout stretches the body shell under 5 % on 98 % of its area, one island;
  the Skin set under 10 % on 87 %; the inner car is hundreds of small pieces. Islands lined up across
  shared corners still miss by 3.9 cm (median); mirror twins can't line up.
- **Texel pitch** at 4096²: the body 0.09 cm, so a 12 cm sticker is about 130 texels and a BC1 block
  3.6 mm. Details at 2048²: about 4 mm (relief reads from 1 cm); the front wing's top about 6 a cm.
- **Flat spots** (2026-09-24): the front flank's lower half sits back under a lip along a diagonal
  fold, so its top strip takes lettering only. Big stickers go on the rear flank behind the sidepod
  (about 34 cm) or the bonnet (z 91 to 142). `SPOTS` in `tool/paintbox.py`. Keep clear: the number and
  engine cover panels (the game letters them: paint them plain), the inlets, the nose fin's plate.
- **The top has a hole and a fin** (2026-09-30): the cockpit, z +70 to −45, nearest up-facing skin 8 to
  28 cm out; the "nose fin" is the bonnet's raised centre panel (84 of 94 triangles face up). Halfway up
  the side runs from 31 cm at the nose to 51 mid-car and 42 at the tail.
- **The body is nine pieces with real gaps**: the sidepod's top 4 mm off the shell, the inlet duct
  14 mm, the tail 17 mm behind the rear flank; 156 edges shared by three or more triangles; skin
  hidden under the loose panels. A band drawn across a gap is cut by it, whatever draws it.
- **Small inner parts the chase camera sees**: the rear bumper, rear strakes, undertray's edge, hubs,
  rims, sidepod frames, side vents, front wing; not the exhausts, calipers, airbox or mirror arms.
- **Moving bodywork** (2026-09-25, the user's video): two rear wings open from about 60 km/h and close
  below about 43, straight out then apart, not on hinges; the rear quarter panels and the nose panel
  tip up while braking. Ask how something moves before modelling it from one camera angle.

## The tyres

- **The map** (1024x2048, 2026-09-27): columns across the tyre from the inner bead (u 0, 29.8 cm from
  the axle) to the outer (u 1), the tread u 0.2 to 0.83 (35.6 to 36.4 cm); rows once round, row 0 at
  10 o'clock seen from the left, anticlockwise, about 45° per 256 rows but not evenly: read each row's
  angle from the bake. The rear tyres are 10 % wider, same radii and texels. It's separable, so
  markings are drawn in its own rows and columns (`tool/tyres.py`), not in 3D.
- **The four share texels, and the right is the left's mirror**: words read backwards there. A
  flip-proof word (B C D E H I K O X, 0 3 8, - + = < > |, drawn upright and symmetric top to bottom,
  which B's bowls and K's arms aren't in most fonts) reads on both sides. Arrows round the wheel point
  the way it rolls on both; rings, dots and chequers don't mind.
- **What shows**: the covers hide the sidewall inside 30.2 cm; the stock `Wheels_AO` darkens three
  patches inside 31 cm and faintly lines the stock grooves on any tread. Markings live in 30.9 to
  35.3 cm, so lettering wants caps of 2 to 2.5 cm. Nadeo's lettering comes off with each column set to
  its median round the tyre.
- **Zip cost**: a marking over the stock tread adds about 1.7 MB, one with its own tread 0.3 MB, a
  slick 0.05 MB. Never yet seen in the game (`IMPROVEMENTS.md`).

## Painting

- **Patterns lie on the surface, never cut out of space** (the user, 2026-09-24): drops as 3D balls
  sliced by the body looked sunk, and any projection from outside merges or stretches where the surface
  turns. Continuous tilings (checks, stripes, weaves) use the car's own unfolding and break at the
  folds, as a real wrap would. Separate things (dots, splashes, cells) are points spread on the surface
  (`looks.surface_points`), each drawn by 3D distance: whole everywhere.
- **Prints of objects are scattered, not tiled** (the user's idea; `tool/scatter.py`): whole copies,
  each flat in one panel, the least-used picture among its neighbours, nudged, turned and shrunk
  before it's left out, bare patches filled by a second pass (TSC_IceCreamSweet).
- **Decals land on the nearest surface** (`paint.project_near`, a depth test), crossing panels like a
  sticker; the fold under them is measured. Pictures are filtered to the texel pitch first
  (`fit_to_texels`), or thin outlines break up.
- **Seams need no special code**: paint weighs each texel by the part's share of what covers it
  (`coverage.share`); the gaps between islands take the nearest island's colour (`raster.fill_holes`:
  an average left a fringe); a texel missing every triangle takes the nearest covered one's position.
- **Clay and white paint look alike** (TSC_FlagPeel_CostaRica): `Skin.clay()` marks the clay and
  `still_clay()` names any part a fifth or more clay. Parts no step paints stay clay in the game too.
- **A name reaches further than it seems**: an assembly ("floor", "sidepod") takes all its parts;
  `Skin._warn_reach` says so and gives the `|part` phrase. A broader word later repaints what an
  earlier one named (TSC_IceCreamTruck's "inner" over its calipers), and a borrowed helper can repaint
  a step: read it before borrowing. Before showing a skin built on another, check every visible part's
  inherited paint.
- **Colour words and finishes**: a metal named as a colour is the metal ("gold"; "dark gold" darkens
  it). A finish name holding a colour word ("brushed titanium") is taken whole first (`finishes._pull`;
  "piano black" would lose its black). The user never sorts their words: the tool does.
- **Read at the car's scale**: a 3.5 mm knurl vanished, 8 mm reads; a 0.5 cm carbon weave in the
  wrap's black was invisible past arm's length, 0.8 cm and a touch lighter reads (TSC_CMYK_EndsInK).
- **Grain goes in the sheen, not the colour** (TSC_CMYK_EndsInK): BC1 keeps two 5-6-bit colours a 4x4
  block, so a few levels on dark paint go flat or blocky; the roughness map holds them. A fine grain
  fills that map and the budget halves it, so draw grain to survive 2048² (2 to 3.5 mm specks).
- **Noise**: value noise finer than a few cm makes facets (a drop's edge at 1.25 cm came out
  many-sided, at 3 cm round); faceted noise (no smoothstep) tears like vinyl, fractal noise sprays
  specks; domain warping folds stripes into marbled swirls.
- **Gloss catches the sky**: small glossy shapes on dark matte read as white dots from behind
  (TSC_ChaosElegance_Thrown; satin fixed it); a glossy dot on a tight curve reads as a row of dashes
  (leave out dots whose normals spread over about 14°); satin black under matte black shows pale.
- **Paint can't fake big 3D shapes** (TSC_CMYK_Peel): a wrap folded back and shaded as a curl looked
  flat. Small crisp cues work: a hard-edged band, not a fade (any fade reads as a soft edge), even all
  round, since a shadow for one light looks wrong from the other side.
- **Things that read wrong**: crimson drops on black read as blood; pale marks on a dark nose read as
  eyes (TSC_Ladybird); a flag draped round a line along the car fans into a sunburst near the line;
  graphics below the flank's lower crease, where the body turns under, become slashes (the critic).
- **Low ledges catch what's meant for the sides** (TSC_Ladybird): the side skirt ahead of the sidepods
  faces up, so "whatever is low" or "faces up" takes it; spots placed without knowing where the top
  ends were cut at the shell's edge. `car/map.md` says where it ends.
- **A split by height is exact** (TSC_Split_Level, TSC_Split_Follow, 2026-09-30): a colour split "in
  the middle" seen from the side is a rule about height (a level, or a curve through the halfway
  points), continuous by construction. A curve on the surface is for lines that aren't a level.
- **Worn paint** (`tool/wear.py`): bare-metal chips mirror the room as black specks (grey primer reads
  worn); chips up to one height read as a band; small clear-coat failure reads as camo, a few big chalky
  patches on top as sun damage. It still doesn't read as worn (`IMPROVEMENTS.md`).
- **Judge gradients from full-size crops**: shrunk pictures band.

## Drawing lines on the car's skin

The current way (since 2026-09-30): curves on the surface itself (`tool/skinmesh.py`,
`tool/skindraw.py`, `tool/skincheck.py`). Its status is under "Under way" below.

- **A line on a car is a curve ON the surface.** Every way tried before defined it elsewhere and failed
  for that reason: values per mesh corner on a 2 to 3.5 cm mesh facet every edge (crayon); a
  flattened sheet sheared 5.6 to 8 % on the flanks, and darts break every line across them; splines
  through pins in the air left the body by up to 22 cm and, pulled onto the nearest surface, landed on
  the wrong one; a side view is trustworthy only on surfaces facing it (past about 53° it lands on
  pylons, undersides and tops), and no path crosses two views. Nadeo's files hold no design lines.
- **The shortest geodesic is not a drawing tool**: nose to tail it strays 278 mm and kinks 83°. A curve
  is a chain of geodesics through places the designer picks; `through` runs leg by leg, a corner at
  each place (`smooth=` rounds them). `taut` pulls the whole chain tight and passed up to 217 mm from
  its places (the earlier cars keep it). A curve's places become mesh corners, or it runs corner to
  corner up to 10 mm off.
- **The skin mesh** (VERSION 4): every panel sewn across its joins and mirrored, each piece its own
  surface (welding pieces to each other twisted it), the right half keeping its own triangles (mirrored,
  it read none of the right's paint), split into four twice (35 to 9 mm), holes under 12 cm filled.
- **A band's width is walked over the surface** by exact geodesics (a ribbon of points 0.25 mm apart),
  each texel taking its offset from the nearest: the same width on the flat and round a flank. It keeps
  to its own piece of surface (`NEAR` under the model's gaps), stops at the curve's ends, picks its face
  by the texel's normal, and allows a 100° turn (the nose panel's groove turns 89°).
- **Other shapes**: `circle` walks a geodesic out every degree (a 220 mm ring measured 1381 mm round for
  1382), never a loop pulled tight; `parallel` keeps gaps over every fold; `edge` draws in from the
  car's edge (14.7 mm for 15; the heat method's contour was −18 to +22 mm out); `meet` makes a clean T.
- **Widths** (TSC_SkinExam): 2 mm is the thinnest whole line (texels 0.9 mm; 1.5 and 1 mm go patchy);
  from the chase cameras 3 to 4 mm reads as a line, 2 mm faintly. Bands measure within 0.2 mm of their
  width, middles within 0.1 mm. A thin line wore a fringe (3 mm read 5) until the walks reached past
  the feather, a third of the width on a thin line, never under a texel.
- **The checker was wrong more often than the drawing.** Read the paint through the skin, not
  `carmap.Map.at` (its ±2 mm was blamed on "grain" and the limits loosened). An edge is the area under
  the coverage ramp. Sort each texel into the nearest colour drawn (`palette`); a blend of two colours
  can sit nearest a third, so read past an edge 2 mm on. A check of the paint against the curve passed
  while the curve missed its places by 9 to 22 cm: check the route too.
- **A check that cannot fail measures nothing**: `--falsify` moves every curve 5 mm, and every band
  must fail (it reads the move back as 4.99 to 5.01).

## The car map

`tool/carmap.py` and `car/map.md` (read before every design). Lines are no longer drawn from it; its
areas, what's open, the air and the chase cameras are still used.

- **Open** (2026-09-29): depth maps in 200 directions, cosine-weighted, the inner car in the way: the
  inlets, under the nose and the wheel pockets come out hidden. `Map.at` finds the body under a point,
  the nearest facing the same way (a panel lying on another isn't mistaken for it).
- **The areas** (`shapes.area`: top, sides, under) are cut by the shoulder's and the lower edge's fitted
  curves and the mesh's own edges, nothing else. The skin has no front or back face (facing within 45°
  of ahead only 411 cm², of behind 960 cm²). Behind the sidepods (z −95 to −35) there's no lower edge:
  the flank rolls under out of sight.
- **The air**: `hit` is the Newtonian rule (facing forward, squared) times how open a spot is from
  ahead; the flow is a potential solved over the welded body, walls only where the air runs into an
  opening. Turning the air locally made lines jog like circuit traces; a solved flow bends early and
  never merges two lines. Smoke lines want a rake across the whole width (`front_rake`).
- **What failed, one line each**: a threshold on each slice's facing puts a line wherever it falls,
  not on the crease the eye sees; a girth summed round each slice moved bands 17 cm between
  neighbours; values per vertex make staircases; a 35° dihedral finds nothing on rounded edges; a
  median-and-smooth put lines between two ridges; cm limits per 1 cm slice let a line zigzag. The crisp
  marks were always the model's own edges.
- **The two computers disagree** (2026-09-29): the Mac traces 66 ridges and 12 folds where the PC has
  62 and 8 (tiny numpy and BLAS differences), so `area("top")` and `across` differ a little.

## The viewer, the Lab and the page online

- **Draw only when something changed** (2026-09-28): `setAnimationLoop` draws at the screen's rate
  (239 Hz here): the Lab's two cars cost 70 % of a core standing still, 1 % after. Anything that moves
  by itself must call `rouse`. Same-origin iframes share the main thread: a hidden viewer slows the
  visible one. A first visit is mostly shader compiling (2.5 s of 5.4); a reload 1.2 s.
- **Zooming never distorts the car; moving the camera does** (2026-09-27): with a fixed 32° lens a
  narrow window sees less across. Frame the car by its own outline (swept all round, only a tenth wider
  than the front view's), centre the outline rather than the car, and let a glide carry the framing.
- **three.js**: materials whose `onBeforeCompile` differs need their own `customProgramCacheKey`;
  `Reflector` mirrors along the mesh's own +z (turn the mesh, not the geometry); a ground shadow's depth
  pass must be depth-tested; `scene.environmentRotation` turns the sky the other way to its Euler;
  hidden parts must cast no shadow either. CSS: a rule scoped by a parent id also reaches its menus; a
  transform widens `getBoundingClientRect` but not the layout.
- **The studio** (2026-09-27): a curved cove shows its bend however smooth unless lit as flat floor; a
  shiny floor catches the sky's bright spots, so it's matte; a floor grain shrinks into the mipmaps
  fast (a 40 cm repeat holds). A vignette darkens the studio, never the car.
- **Motion is the game's**: the pad's pace, gears and braking are read frame by frame from the user's
  videos (`PACE`, `GEAR_UP`, `BRAKE`); timings by eye had been off every time. Wheels ease off to
  about 4 turns a second (290° a frame at 400 km/h can't show).
- **Notes on the car** (`.notes/notes.json`, off git: answers and states would churn a public file):
  three writers (server threads, the hook, the command line) share one file under an mkdir lock. The
  server answers this computer's pages only (Host localhost, a matching Origin, a JSON body). After a
  change to the server, restart whatever serves 8765: old servers kept old code in memory.
- **The page online** (2026-09-25): 2048² JPEG at quality 90 with 4:4:4 is only softer than 4096², and a
  4096² texture takes about 90 MB of graphics memory with mips, too much five times on a phone.
  `tool.publish` force-pushes one commit to `gh-pages`, which Pages must be set to serve; clones leave
  that branch out of their fetches (a negative refspec, set by the hook).
- **Snapshots hold to the pixel** from run to run, so a change that leaks into them shows at once. The
  Lab's embed-only changes must leave them and the page online unchanged.
- **Codes the user copies never reorder** (`finishes.CATALOGUE`, the tyres' TY and TR): a new one goes
  at the end of its family, a retired one leaves None. Our gold was set against the game, not measured.

## Compression and building

- **Our own encoders** (`tool/dds.py`): Pillow's BC4 put 1 % of glow texels on the wrong code; its
  BC1 was 5 dB worse, with fringes (the user saw pixelated stickers). `dds.bc1_blocks`: endpoints on
  each block's principal axis, least squares, a local search; on a par with texconv. A build takes
  about 2 minutes, and that's worth it.
- **ATI2's first block is channel 0** (X in a normal map, roughness in `_R`), as Nadeo's files store
  it, with "A2XY" in the bit-count field; the first test's chrome nose confirmed it in the game.
- **Mips keep glow codes exact**: Nadeo's own average them (35 % off-code at mip 6); ours point-sample
  the alpha. Colour is averaged in linear light. Legacy headers, a full mip chain.
- **Painting is the slow part** (1 to 2 minutes a car at 4096²). The nearest covered texels are kept
  (`Canvas.near`) and `Skin.textures()` built once. The UV map's data rebuilds only when
  `paintbox.SIZES` or `UVMAP_VERSION` change: bump it when `export_uvmap` or `_surfaces` write anew.
  Paints take turns (`skin.paint_slot`): each needs a few GB, and three at once killed two.
- **The self-test** (`tool/selftest.py`) paints skins with this code and an earlier commit's and
  compares them byte for byte. A change to what a cache holds must change its name or version.

## The picture maker

- **FLUX.2 [klein] 4B** (Apache 2.0) through diffusers, on the PC's card only: the text encoder and the
  transformer (8 GB each) load one after the other; PyTorch's CUDA 13 build covers the card and Python
  3.14. About 3 s a picture. Cut-outs on plain white (BiRefNet through rembg); tiles on a torus.
- **A few large objects come out crisp, a dozen small ones mushy**: ask for four and scale on the car.
  Two runs with the same words share a folder, the second overwriting the first: give each style its
  own slug. A picture's "landed" share is counted in half-centimetre cells, not pixels.

## Working on this repo

- **Long heredocs through Git Bash get cut off** ("unexpected EOF"): write the script to the
  scratchpad with the Write tool and run it.
- **GNU sed reads backslash-backtick as the start of the text**, and a Python string that isn't raw
  reads a Windows path's backslash-and-digits ("2225070") as a character code: both corrupted pushed
  files. Edit docs with the Edit tool.
- **The Edit tool reads `$'` in a replacement as a JavaScript replace pattern** (it pasted in the rest
  of the file): keep that pair out of edits, or write the line with a script.
- **Windows refuses to replace a file another program has open** (the page's poll, OneDrive,
  Defender): files the pages read are written whole by `paths.write`, which retries. An `os.mkdir`
  lock is atomic and works across processes.
- **Measure before guessing**: the Lab's slowness was timed in headless Edge first (the load, long
  tasks, the browser's CPU summed over its child processes).
- **Agents load when a session starts**: a new or changed `.claude/agents/*.md` reaches the next
  session; until then give a general-purpose agent the same text.
- **`car/parts.json` shows up changed**: delete the work folder's `parts_stats.json` and run
  `tool.parts`. **ambientCG wants a User-Agent** (a bare Python one gets 403).

## Under way: working notes

### Drawing on the skin

`IMPROVEMENTS.md`, "Drawing on the skin". The lasting lessons are in "Drawing lines on the car's skin".

- **How it works now**: `PY -m tool.skinmesh --build` makes the surface; a design draws with
  `skindraw.through`, `taut`, `parallel`, `circle`, `loop`, `mirror`, `edge`, `meet`, and paints a curve
  with `band`. A place is a name, (x, y, z) in cm with which way it faces ("up"), or a pinned line from
  `car/lines.json` (`through(["side crease"])` runs through the user's six pins). `--probe` says what
  a route crosses; `PY -m tool.skincheck <name>` (`--falsify`) measures every band on the car.
- **Test cars**: TSC_Skin and TSC_SkinMore (bands of eight kinds), TSC_Solstice (the first crafted
  livery: a three-colour sweep, twin cream stripes on gold), TSC_SkinExam, TSC_Split_Level, _Follow.
- **The exam** (2026-10-01; the user: "I would like to put it as a test"): pinstripes 4 to 1 mm, a
  double coachline on the user's crease, two lines ending on it, a line 15 mm off the cockpit's rim,
  square corners, a chevron, a crossing, the 70 mm nose band. 15 of 17 pass (the 1.5 and 1 mm
  pinstripes: too thin for the texture). It found `through` missing its places, the thin lines' fringe,
  the facing gate, holes in the skin and the checker's own errors; all fixed, earlier cars re-measured.
- **Left**: the nose band over the bonnet's centre fin (±12 mm); the hoop's middle wobbles 1.8 mm and a
  third can't be measured down the flanks; whether the hole and stray-paint judgements can be trusted;
  a filled area bounded by a drawn curve; flagged spots (TSC_Skin's flank sweeps, 40 mm² of holes at a
  panel joint at z −82; SkinMore's two middle stripes and Solstice's cream stripe, 3 to 6 mm² at their
  ends). The black and gold pinstripe livery the user picked after the exam isn't started.
- **The user, after the exam: "lets stop. None of the cars make me think it's working."** The numbers
  didn't convince them by eye. Before building more, ask what they'd need to see, and don't count a
  check passing as the item working.

### The car map

`IMPROVEMENTS.md`, "The car map". Work on it goes through the car mapper (`.claude/agents/car-mapper.md`).

- **What it holds**: `open`, `along`, `across`, the areas, `Map.at`, the air (`hit`, the flow,
  `streamlines`, `rake`, `front_rake`), what the chase cameras see, and the shoulder, lower edge and 8
  folds as fitted curves (least-squares B-splines, a knot every 15 cm, evidence within 4.5 mm at the
  95th). `PY -m tool.carmap --describe` writes `car/map.md`; `--check` prints every measure against its
  limit (`tool/mapcheck.py`). Test cars: TSC_Map_*.
- **Still used**: `car/map.md` before every design, the areas, what's open, the air (TSC_WindTunnel's
  smoke lines: 403 design lines down to 76) and the chase layer. `shapes.line` only shows the map's
  lines on its test cars.
- **From the handover, still true**: `open`, `hit` and the flow, `along` and `Map.at` can be trusted,
  but were checked close up only here and there. Judge a line close up, never from whole-car sheets:
  `tool.snap --body` and `--stretches` (each stretch, wheels off, both sides), enlarged where the body
  changes, then on the flat texture (a line that steps there steps on the car). Say what's still off
  before calling anything done.
- **Waiting and left**: the user's look at `car/map/lines.jpg` and `areas.jpg` before anything built
  on them is called done (TSC_WindTunnel waits too); then what each game camera shows, flat spots
  measured rather than typed (`SPOTS`), a check for graphics crossing a fold or an opening, streaks
  along the flow, and the two computers' difference.
