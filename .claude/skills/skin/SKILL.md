---
name: skin
description: Make a Trackmania car skin from the user's words and put it in their game. Design it with the paint box, show it on the car, change it until they say yes, then install it. Use for every request to make, change, compare, show, install or pick up a skin, however vague ("something with flames", "make the wheels gold", "back to the ice cream car", "install it").
argument-hint: "[what the skin should look like]"
---

# Skins from words

The user describes a skin, sees it on the car, asks for changes, says yes, and it's in the game.
Their words, if they came with the command: $ARGUMENTS
If they haven't said what they want yet, ask: **what skin would you like?** One word ("lava")
or a whole scene is fine.

## One way of working

The user works by looking at the car and changing it, with options to pick whenever there's more
than one way to go (2026-09-28: "Two main things I like. It's having the car and me being able to
iterate. and I also like a place where you can provide options before building"). The quick way
and the studio's steps became this one way the same day.

- **A new car** (a new idea, not a change to one): read `new-car.md` beside this file and follow
  it: a short talk and its card, the first concepts as a set, then the car finished field by field
  from their notes, with every detail and the experts' guides, the critic before the game, and the
  release.
- **A change to a car:** make it on the car and show it (below).
- **Options, whenever they ask for a few ideas on anything, or there's a real choice:** a set
  ("Sets of options", below). They pick in the Lab's timeline or in the chat.

## Standing rules

- Everyday model: **Opus 5.5** (the user's choice, 2026-09-25). If this session runs on another
  model, say so once, in one line (type `/model`, pick Opus 5.5). If a design is still wrong
  after a few rounds, suggest switching to Fable 5.1.
- Looks before speed. A round can take up to about 10 minutes if the skin is clearly better.
  Never trade sharpness for build time.
- A clear idea gets one design. A vague one gets 2 or 3 takes as a set, each a different
  reading, not three shades of one.
- Plain words in replies: no code, file names, paths or tool output. Describe the car.
- Ask only about taste. Decide everything technical. When a word is genuinely ambiguous
  ("pearl", "metallic", "retro"), show it (two takes, or the Lab) rather than ask.

## Commands

From the repo root. `PY` is the tool's Python (`CLAUDE.md`: one for each computer); every
command below runs the same on both. The Mac has no picture maker (it needs the PC's NVIDIA
card) and no game: install from the Windows PC after a push.

| Command | What it does |
|---|---|
| `PY -m tool.skin list` | Every skin, newest first, with the user's words; marks those in the game. |
| `PY -m tool.sets <car>` | A car's sets of options (what's waiting for a pick, what was picked). Its commands are in `tool/sets.py`'s docstring and "Sets of options" below. |
| `PY -m tool.critic <car>` | A car's review by the critic: what it found, and what was fixed or left. Its commands, and the critic's pictures (`tool.snap <car> --review`), are in `new-car.md`, 4. |
| `PY -m tool.skin show <name>` | Paints `skins/<name>/design.py` (15 s to 4 min), puts it in the viewer, saves six views to `build/<name>_views.png`, keeps `versions/<n>.png`. Read every note it prints. |
| `PY -m tool.snap <name> --close` | Nine close looks → `build/<name>_close.png`: 1 bonnet, 2 nose, 3 front flank fold, 4 sidepod, 5 rear flank, 6 deck and tail, 7 right side, 8 front wheel, 9 driving camera. Run it after `show`. |
| `PY -m tool.snap <name> --cams` | The game's Cam 1 and 2 and their alts (the key pressed twice) standing still, by day and at night, at 16:9 → `build/<name>_cams.png` (`--size 2560x1440` for the user's screenshots' size). |
| `PY -m tool.snap <A> [<B> <C>] --picture --titles "…" "…" [--views front rear top] [--close-row <name> 3 4 9]` | The picture for the user: a titled row per take (views: front, rear, left, right, top, night), plus rows of close looks (`--close-row` again for each take). Opens it on their screen. |
| `PY -m tool.gallery` (background) | The page of all skins. Clicking one spins it in 3D. |
| `PY -m tool.swatches` (background) | The Lab, http://localhost:8765/lab.html: the car (the user's notes hang on it as tags) with its timeline beside it, "With Claude" (the notes, Claude's lines, the sets of options); the UV map and every material the tool knows on a ball (with its code, numbers and a "Copy for Claude" button) in the car's menu. |
| `PY -m tool.skin install <name>` | Builds the game files (2 to 3 minutes) and installs them. Reinstalling a skin replaces it. |
| `PY -m tool.publish` | Puts the skins in the game on the page online (the user's phone and friends), about 10 s plus the upload. `--here` shows it on this computer only. |
| `PY -m tool.pictures decal "<words>" [--style …] [-n 4]` | Candidate cut-out pictures on one sheet, `build/pictures/<slug>.png`, about 20 s each. Styles: sticker (default), flat, print, painted, line art, retro, photo. |
| `PY -m tool.pictures tile "<words>"` | Seamless tiles, for a continuous print. |
| `PY -m tool.pictures keep <slug> <k> <skin> <name>` | Keeps candidate k as `skins/<skin>/art/<name>.png`, for `s.art("<name>")`. |
| `PY -m tool.textures search "<surface>"`, then `add "<surface>" <Id> --scale <cm>` | Adds a photographed surface (ambientCG, CC0) to the library by name. Do this rather than say no. |
| `PY -m tool.tyres [TY-01 ...]` | The tyre markings library on the car (about 6 s each): `build/tyres/library.png`, each one's three views. After adding or changing markings, rebuild the user's page (`tyresheet.page()` into the scratchpad) and republish it to https://claude.ai/artifact/2TdLiRLDGKxUkMiKBo89ko (`url`). |

## Designing

- A design is `skins/<name>/design.py`: a `design(s)` function of `paintbox.Skin` calls.
  Before the first design in a session, read **the car map, `car/map.md`, and look at its
  pictures** (`car/map/`) **and the body sheet, `car/sheet.png`** (the skin flattened in true size,
  in millimetres: `car/sheet.json` has every line and station on it), then the docstrings of
  `tool/paintbox.py` (the key), `tool/shapes.py` (zones) and `tool/finishes.py`, and `SPOTS` in
  `tool/paintbox.py`. **Design on the sheet first:** a graphic drawn on it (`shapes.sheet(...)`,
  `shapes.sheet_line`, `shapes.offset`, `s.decal(picture, "sheet", at=(x, y), width=mm)`) lands
  on the car at true size and follows its lines; the 3D zones are for what the sheet can't say. Part names are in
  `car/parts.json`. Colour and finish words go through `finishes.resolve()`.
- **Built in steps, from clay (the Lab, the user's idea, 2026-09-26).** A new design
  starts with `s.clay()`: the body, wheel covers and inner car in the Lab's neutral white
  clay, which stays on any part no later step paints, in the game too (the user's choice). So
  design every part, or say which stay clay. Then open each step with `s.step(name, does,
  words=...)`: a few words, what it paints in plain words, and the user's verbatim words that
  asked for it; `look="rear night"` for a step the day's front view can't show (lights). A
  change the user asks for edits its step, so later steps stay on top. While `show` paints, the
  Lab shows the car at the end of each step.
- **Lines from the Lab.** The user may paste a line copied from the Lab, like `ME-07 Gold (matte
  28%, metal 100%, varnish 0%)`. The code is that finish, exactly: put the code in the phrase
  (`s.paint("sidepod", "ME-07")`, `"ME-07 matte"`, or `s.paint("body", "PA-03", colour="#1a1c20")`
  for one without its own colour). The numbers are there for the user to read. The Lab's names
  work in phrases too ("rose gold", "stainless steel"). A part copied from the Lab's UV map room,
  like `floor|left|part (Details map, 79% of its paint shared with ...)`: the phrase before the
  bracket is exactly that part as `where` (`s.paint("floor|left|part", ...)`); the bracket says
  what else its paint lands on. A surface picked on the UV map adds `; the Details map's
  surface 278, used by floor edge (left, right)`: the user pointed at that one shape of paint.
  Paint it by the parts it names; if it's only part of a part (the part names other surfaces
  too), say so and paint the part, or ask whether the whole part will do.
- **Notes on the car (the Lab, the user's picks, 2026-09-27).** The user clicks the car in the Lab
  where they mean and writes what they want there; the note hangs on the car as a tag and keeps
  the view they wrote it from. They can also write in the box under the Lab's timeline ("in the
  Lab's box"), about the option on the car when one is. New notes arrive with their next message (a
  hook prints them), or at once while you wait for them (`tool.notes wait`, below): the skin (an
  option's name when the timeline had put that option on the car), the note's number, the part
  clicked as a `where` phrase (`sidepod top|left`), their words, and a picture of what they were
  looking at with the note's dot drawn on: look at it before acting. They're the user's words about
  that spot, as if typed in the chat: act on them in that skin (its notes.md: `Change <n> (user,
  note N): "…"`), answer a question in the reply, and once a note is handled mark it done with a
  line for the Lab's timeline saying what changed, in plain words, one or two sentences: `PY -m
  tool.notes done <skin> <n> --say "…"`. Its tag leaves the car; the note and your line stay in the timeline. Anything else worth
  saying in the Lab (a set's offer, a question while they look at the car): `tool.notes say <car>
  "…"`. `PY -m tool.notes` lists the ones not done. The notes stay on the computer they were
  written on (`.notes/`, off git).
- **Sets of options** (the user, 2026-09-28: "a place where I can pick options as I go ... can we
  try 3 different materials for X ... a few concepts for the wheels, or anything in a non linear
  way"). Whenever the user asks for a few ideas on anything (or a loose idea's first takes, a new
  car's concepts), make them a set on the car: `tool.sets new <car> "<what, e.g. Wheels · 3
  ideas>" --words "<their words>"` (it prints the set's number), `tool.sets option <car> <n>
  "<Title>"` for each (a copy of the car's design to change, `<car>_<Title>`; an empty folder for a
  new car), then paint and snap each (the Lab's timeline shows its gallery picture as soon as it's
  painted), and `tool.sets open <car> <n>` once all are, with a line for the timeline (`tool.notes
  say <car> "…"`: what the options are, in a sentence). The timeline beside the car shows the set as
  Claude's; a click puts an option on the car, where the user can turn it and leave notes on it. Then
  start `PY -m tool.notes wait` with the Bash tool in the
  background and end the turn: a pick or a few words in the Lab end it at once ("in the Lab's
  timeline, set 2 (Wheels · 3 ideas), picked B (Magenta)"), with no message in the chat. The pick:
  `tool.sets pick <car> <n> <letter> "<what was picked>"` makes it the car's design (the others go,
  each one's picture kept for the timeline), then `show <car>`; a mix they spell out
  ("B, but with A's ring"): change that option, then pick it. A set no longer wanted: `tool.sets
  drop`. Name the options A, B, C in replies too.
- Names: `TSC_<Idea>` in CamelCase, no spaces. Name takes `TSC_<Idea>_<Twist>`. A change to a
  skin edits that skin, unless the user wants to keep both.
- For a skin that builds on an earlier one, load that design (as
  `skins/TSC_CMYK_Peel/design.py` does) rather than copy it.
- When something isn't in the box, write it. A reusable pattern or placement goes in `tool/`. A
  new finish goes in `finishes.LIBRARY` and at the end of its family in `finishes.CATALOGUE`
  (never reorder it: the codes are what the user copies), so the Lab shows it.
  A shape for one skin only stays in its `design.py`. Keep it small. Record what the game or
  a test teaches under "Things we learned" in `CHECKLIST.md`.
- Each picture-maker run needs its own wording or style: two runs with the same words share a
  folder, and the second overwrites the first.

## The improvement list: `IMPROVEMENTS.md`

- It's the queue of things the tool should do better. Read it at the start of each skin (it's
  short). If the idea runs into an item, fix that item first, or tell the user what it means
  for the skin.
- During a skin, fix only what this skin needs. Anything else that falls short goes on the
  list, whether you spotted it or the user did: the date, what's wrong, the skin that showed
  it, and an idea for the fix. Tell the user in one line that it's on the list.
- Anything the user asks the tool to do better, in or out of a skin, is an item here, never a
  new checkpoint. A big one keeps its working notes under "Improvements after the build" in
  `CHECKLIST.md`.
- Work on the list when the user asks. When an item is done, delete it from the list and
  record what it taught under "Things we learned" in `CHECKLIST.md`. An item marked for the
  game gets tested when a skin uses it: ask the user to look.

## What works on this car

- **The wheels are their own step.** "body" leaves out the wheel covers. Paint "wheels"
  (covers, rims, hubs, rings) and "tyres" with their own calls. The user settles the wheels car
  by car, as one piece of work: covers, rims, the tyres' marking and their tread together ("the
  wheels in general is a full workflow as I build cars", 2026-09-27). So the library sets no
  tread for them; in that step, suggest a marking and a tread that suit the car and show them.
- **Tyre markings: the library, `s.tyre_marks("TY-07")`** (`tool/tyres.py`: 95 of them, F1 rings to
  whitewalls, raised letters and tread patterns). A code the user pastes, like `TY-01 ring soft
  (tyre marking)`, is that marking; `colour=` and `words=` change it where its layout takes them.
  A tread from the Lab's Treads, like `TR-04 Wet tread (...)`, is `s.tyre_tread("TR-04")`, or a
  marking's `tread="TR-04"` (the Formula 1 ring on a slick). All four tyres wear one marking.
  Words on a tyre read backwards on the right-hand wheels unless every letter is one of B C D E
  H I K O X 0 3 8 (the library's are): for the user's own word, say
  which side reads right (`reads="right"` swaps) or suggest a flip-proof one. A new look for the
  tyres goes in the library (its layouts are short), not in a design.
- **The car map** (`tool/carmap.py`, `car/map.md` and its pictures, 2026-09-29: the user wanted
  the AI to understand the car "so that no matter what design is done, the Ai just knows"). The
  body's shape worked out once from its mesh: its areas, its lines, positions that bend with it,
  what's open, what the chase cameras see and the air over it. Place graphics by it, not by cm
  guesses: `shapes.area("top")` (between the shoulders; never the ledges and lips low down),
  `shapes.outside(0.4)` (never inside an inlet or under a panel), `shapes.across(a0, a1)` and
  `shapes.along(a0, a1)` for bands that follow the body, `~shapes.near("opening", 3)` or
  `near("fold", 2)` to keep clear, `shapes.line("shoulder", w)` along its lines, `shapes.hit` and
  `shapes.streamlines` for the air. A round spot seen from above: `shapes.cylinder((x, -50, z),
  (x, 250, z), r) & shapes.area("top") & shapes.outside(0.4)`. The map rebuilds itself when the
  mesh changes (`python -m tool.carmap`, 30 s); after a change to its code, rebuild, repaint the
  four TSC_Map_ cars, take their `--body` sheets into `car/map/` and `--describe` again.
- **The body sheet** (`tool/surface.py`, `car/sheet.png`, `.svg`, `.json`, 2026-09-29: the user
  wanted the model's curvature mapped so "any design AI can easily understand it and accurately
  design"): the outer skin flattened into a sewing pattern in true millimetres, the nose's tip at
  the left, the top centreline along the top, the map's lines and the stations drawn on it. A
  shape drawn on the sheet is that size on the paint and follows the body; the right side is the
  mirror. `shapes.sheet(svg | picture, box= | polylines, width= | f(x, y))`, `shapes.sheet_line`,
  `shapes.sheet_near`, `shapes.offset(line, mm)` (a band 30 mm below the shoulder:
  `shapes.sheet(shapes.offset(shapes.sheet_lines("shoulder")[0], 30), width=8)`), `along_cm`,
  `across_cm`, and `s.decal(picture, "sheet", at=(x, y), width=mm)`. Its checks: `python -m
  tool.carmap --check` (the sheet's table) and `python -m tool.sheetcheck <car>` on a painted car
  (every band's crossing of a join measured on the texture). The test cars: TSC_Map_Sheet (a 10 cm
  checker and offset bands) and TSC_Map_Proof (a livery drawn only on the sheet). Where the body
  turns through three faces (the sidepod's rear and front corners) the sheet shears a little
  rather than cut the paint: keep fine lettering off those two corners.
- **Keep clear** of the places the map can't know are special: the number panel (x ±19, z -78 to
  -62) and the engine cover panel (x ±19, z -120 to -82), where the game draws the player's number
  and name, and the nose fin's plate (x ±8, z 118 to 142): its fin stands upright, so a spot there
  leaves a notch.
- **Grass up the sides:** `shapes.grass(base=, height=, line=)`, filled blades or ink strokes,
  the same silhouette both sides (TSC_Ladybird). It fills everything low, so keep it behind the
  nose: under it the side skirt runs forward as a flat ledge facing up, and the wing's pylon sits
  low, and both came out a solid green slab. Pale marks on a dark nose read as eyes: keep them
  off unless a face is wanted, or draw them out into streaks along the nose (TSC_Ladybird).
- The user prefers illustrations, prints and decals to photographs. "sticker" is the default.
- A print made of objects: `s.scatter` (whole copies, each inside one panel, spread evenly).
  A continuous texture: a tile through `s.print`. Ask the picture maker for a few large
  objects, never a dozen small ones.
- Big pictures go on the flat spots: "left side" / "right side" (the rear flank behind the
  sidepod, 34 cm) and "bonnet" (45 cm). The front flank has a deep fold, so it takes lettering
  only, on its top strip ("left flank" with `at=(35, 62, 60)`, "right flank" with `at=(-35, 62,
  60)`). `show` reports a decal that crosses a fold or runs off an edge.
- Keep lettering and detail off "number panel" and "engine cover panel": the game draws the
  player's number and name there.
- Crisp edges. The zone edge is 0.2 cm (about two texels). A fade along an edge reads as soft.
- Aged paint: `under = s.keep()` of the primer, paint the livery, then `s.wear(under, fade=,
  chips=, scrapes=, clearcoat=)` (stone chips, wall scrapes, sun). Light primer under chips, not
  bare metal: metal mirrors the dark and reads as black specks.
- Paint can't fake big 3D shapes (curls, folds): use small, crisp cues. A painted shadow must be
  the same width all round (as if lit from above), or it looks wrong from the other camera.
- Glow is for the inner car only, as far as we know: Nadeo's list of skin files has no glow map
  for the body, but one was never tried in the game (the user doubts it, 2026-09-29: the test is
  on `IMPROVEMENTS.md`). Don't tell the user the body can't glow as a fact. `s.glow(part, colour,
  kind)`. Seen working: "always on" (day
  and night), "night only" (at night and sunset), "front lights" (at night and sunset only, the
  brightest), "brake lights" (at night, and when braking), "energy" (only in the garage, tinted by
  the game; dark on the track), "brake
  heat" (rims glow while braking hard, building over about 1.5 s), "turbo" (glows in the
  turbo pad's colour, yellow for a yellow pad, for about 3 s after it: the stock hubs carry it,
  seen inside the wheels). Exhaust heat and boost were never seen to light up, so don't
  promise them.
- The car's own lights take any colour: `s.relight("speed numbers" | "brake lights" | "rear
  lights", colour)`. The rear lights fill up with the gear in that colour and turn red when
  braking, whatever the colour, and for about 1.5 s after a turbo pad. A tinted rear lens ("rear light lens") colours them too, and
  filters the braking red: keep it clear or warm.
- `s.glass(colour, strength)` only tints. It also tints the lights behind the lenses.
- Most inner parts share their paint with their twin on the other side, so `"…|left"` also
  paints the right, and some share with other parts: the front wing's panels wear the floor's
  paint, and a small patch serves many inner parts (the front uprights among them). `show` names
  every part a colour also lands on, with how much: read it. All four wheels and tyres share one
  paint.
- `s.dirt(amount)`: how dirty the car gets on dirt (1 = stock, 0 never).
- Say these can't be done, if asked: holographic or colour-shift paint, relief on the body,
  the player's number and name or their colour (the game mode sets it: white in a normal race), the turbo colour,
  the gear display on the glass.

## Before showing anything

1. Look at `build/<name>_views.png`.
2. Run `tool.snap <name> --close` and look at every close view. Check each graphic where it
   meets a join, fold, hole or edge: nothing cut, sunk, stretched or soft.
3. Go over the whole car. Every visible part should serve the idea: sidepod frames, seams,
   wheels, inner car, front wing, glass. Check paint left over from an earlier skin most of all.
4. Fix what you find and look again. The user zooms in. Don't leave anything for them to find.

## Showing the user

- Run `tool.snap … --picture` with a short plain title per take. Add a close row with the
  telling close views, and usually the driving camera. It opens on their screen.
- Start `tool.gallery` in the background once per session, so they can spin each skin in 3D.
  After each round, tell them to refresh it.
- The Lab (http://localhost:8765/lab.html) opens on the car, which follows the skin being
  painted while `show` runs, no refresh needed: the car shows each step as it's done. Tell the
  user once per session they can keep it open to watch the car being built, click the car to
  leave a note on a spot (it hangs there as a tag), and pick options and talk to you in the
  timeline beside it.
- Reply in a few sentences: what the car looks like, the takes numbered by title, and one line
  on what you checked close up. End with one bold question: which one, or what to change. Say
  that a yes puts it in the game.

## The record: `skins/<name>/notes.md`

- Start with the user's words verbatim, the date and the model, then how you read them.
- Add one line per event: `Shown <date>: …`, `Change <n> (user): "<verbatim>" <what changed>`,
  `Installed <date>: …`. `show` keeps a picture of each round in `versions/`.
- A cold session must be able to pick up any skin from its `notes.md` and `design.py` alone.

## Installing

1. On the user's yes, or when they name a skin, run `tool.skin install <name>`. If the skin
   has small stickers or lettering, look at a magnified crop of an outline in
   `build/<name>/Skin_B.dds` (`tool.dds.decode`). Edges should be about two texels, with no
   fringes.
2. Tell them: in the game, Garage → My Skins → Upload skin, then pick `<name>`. No restart
   is needed (TSC_Lights_Test, 2026-09-25). If anything looks off, an F12 screenshot shows it.
3. Run `PY -m tool.publish` (under a minute) so the page online shows it too, and tell the user
   it's there for their phone and friends.
4. Add the `Installed` line to `notes.md`.
5. Screenshots are in
   `C:\Program Files (x86)\Steam\userdata\53610290\760\remote\2225070\screenshots\`. Look
   only at ones taken after the install.
