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

## Standing rules

- Everyday model: **Opus 5.5** (the user's choice, 2026-09-25). If this session runs on another
  model, say so once, in one line (type `/model`, pick Opus 5.5). If a design is still wrong
  after a few rounds, suggest switching to Fable 5.1.
- Looks before speed. A round can take up to about 10 minutes if the skin is clearly better.
  Never trade sharpness for build time.
- A clear idea gets one design. A vague one gets 2 or 3 takes, each a different reading, not
  three shades of one.
- Plain words in replies: no code, file names, paths or tool output. Describe the car.
- Ask only about taste. Decide everything technical. When a word is genuinely ambiguous
  ("pearl", "metallic", "retro"), show it (two takes, or the materials page) rather than ask.

## Commands

From the repo root. `PY` = `"$LOCALAPPDATA/TrackmaniaSkinChallenge/venv/Scripts/python.exe"`.

| Command | What it does |
|---|---|
| `PY -m tool.skin list` | Every skin, newest first, with the user's words; marks those in the game. |
| `PY -m tool.skin show <name>` | Paints `skins/<name>/design.py` (15 s to 4 min), puts it in the viewer, saves six views to `build/<name>_views.png`, keeps `versions/<n>.png`. Read every note it prints. |
| `PY -m tool.snap <name> --close` | Nine close looks → `build/<name>_close.png`: 1 bonnet, 2 nose, 3 front flank fold, 4 sidepod, 5 rear flank, 6 deck and tail, 7 right side, 8 front wheel, 9 driving camera. Run it after `show`. |
| `PY -m tool.snap <A> [<B> <C>] --picture --titles "…" "…" [--views front rear top] [--close-row <name> 3 4 9]` | The picture for the user: a titled row per take (views: front, rear, left, right, top, night), plus rows of close looks. Opens it on their screen. |
| `PY -m tool.gallery` (background) | The page of all skins. Clicking one spins it in 3D. |
| `PY -m tool.swatches` (background) | The materials page: every finish on a ball, by family. |
| `PY -m tool.skin install <name>` | Builds the game files (2 to 3 minutes) and installs them. Reinstalling a skin replaces it. |
| `PY -m tool.pictures decal "<words>" [--style …] [-n 4]` | Candidate cut-out pictures on one sheet, `build/pictures/<slug>.png`, about 20 s each. Styles: sticker (default), flat, print, painted, line art, retro, photo. |
| `PY -m tool.pictures tile "<words>"` | Seamless tiles, for a continuous print. |
| `PY -m tool.pictures keep <slug> <k> <skin> <name>` | Keeps candidate k as `skins/<skin>/art/<name>.png`, for `s.art("<name>")`. |
| `PY -m tool.textures search "<surface>"`, then `add "<surface>" <Id> --scale <cm>` | Adds a photographed surface (ambientCG, CC0) to the library by name. Do this rather than say no. |

## Designing

- A design is `skins/<name>/design.py`: a `design(s)` function of `paintbox.Skin` calls.
  Before the first design in a session, read the docstrings of `tool/paintbox.py` (the key),
  `tool/shapes.py` (zones) and `tool/finishes.py`, and `SPOTS` in `tool/paintbox.py`. Part names
  are in `car/parts.json`. Colour and finish words go through `finishes.resolve()`.
- Names: `TSC_<Idea>` in CamelCase, no spaces. Name takes `TSC_<Idea>_<Twist>`. A change to a
  skin edits that skin, unless the user wants to keep both.
- For a skin that builds on an earlier one, load that design (as
  `skins/TSC_CMYK_Peel/design.py` does) rather than copy it.
- When something isn't in the box, write it. A reusable pattern or placement goes in `tool/`.
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
  (covers, rims, hubs, rings) and "tyres" with their own calls.
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
- Paint can't fake big 3D shapes (curls, folds): use small, crisp cues. A painted shadow must be
  the same width all round (as if lit from above), or it looks wrong from the other camera.
- Glow is for the inner car only: `s.glow(part, colour, kind)`. Seen working: "always on",
  "night only", "front lights" (white), "energy" (the game tints it), "brake lights". Brake
  heat, turbo, exhaust heat and boost were never seen to light up, so don't promise them.
- `s.glass(colour, strength)` only tints. It also tints the lights behind the lenses.
- Most inner parts share their paint with their twin on the other side, so `"…|left"` also
  paints the right (`show` notes it). All four wheels and tyres share one paint, and writing on
  a tyre reads backwards on one side.
- `s.dirt(amount)`: how dirty the car gets on dirt (1 = stock, 0 never).
- Say these can't be done, if asked: holographic or colour-shift paint, relief on the body,
  the player's number and name, the turbo colour, the digits, the rear lights, the gear
  display on the glass.

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
2. Tell them: in the game, Garage → My Skins → Upload skin, then pick `<name>`. If it isn't
   there, restarting the game brings it in. Whether that's ever needed is still on the
   improvement list, so ask them. If anything looks off, an F12 screenshot shows it.
3. Add the `Installed` line to `notes.md`.
4. Screenshots are in
   `C:\Program Files (x86)\Steam\userdata\53610290\760\remote\2225070\screenshots\`. Look
   only at ones taken after the install.
