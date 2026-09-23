# Checklist

This is the plan for building the skin tool, one checkpoint at a time.

- **For Claude:** at the start of every session, read this file, find the first checkpoint whose
  box isn't ticked, and carry on from there. Tick a box only after the user has seen what the
  checkpoint promises. If something we learn changes the plan, change this file and tell the
  user.
- **Switching model:** each checkpoint names the Claude model to use. At the start of a session,
  type `/model` in the chat box and pick it.
- Each checkpoint has plain-language parts for you, then **Notes for Claude**, which you can
  skip.

## How the project is organised

```
Trackmania Skin Challenge/
  BRIEF.md, CLAUDE.md, CHECKLIST.md   the brief, Claude's standing notes, this plan
  official/            the files you gave me, never changed
  tool/                the machinery, a few small programs that:
                         read the car, paint it, make the game files, install
  viewer/              the page where you look at the car in 3D
  skins/<name>/        one folder per skin:
                         your words and each change you asked for,
                         the design recipe,
                         a small picture of each version
  skins/installed.json a list of what the tool has put in your game,
                       so it never touches anything else
  requirements.txt     the exact versions of the tools the machinery uses
```

The bulky working files live on this PC, outside OneDrive, so OneDrive doesn't spend its time
syncing them: `%LOCALAPPDATA%\TrackmaniaSkinChallenge\`. They are:
- the tool's software setup (the Python environment);
- the unpacked car model;
- the tool's maps of the car;
- the built game files.

All of them can be rebuilt from the project at any time.

## Checkpoints

### [ ] 0. The plan

- **What it's for:** agreeing the steps before anything gets built.
- **What you'll see:** this file. We go through it together.
- **Model:** Opus 5.5. Deciding how the whole tool fits together is the hardest thinking in the
  project.

### [ ] 1. A test paint job in your game

- **What it's for:** proving the basics first. The tool has to make files the game accepts and
  put them where the game finds them. If that fails, nothing else matters, so it comes first.
  This step also sets up the folders and the tools.
- **What you'll see:** in the game, go to Garage → My Skins → Upload skin and pick
  "TSC_Test". The car wears a loud test pattern:
  - a numbered grid, with arrows that say LEFT, RIGHT and FRONT;
  - one chrome area and one matte area;
  - lights glowing an odd colour.

  Tell me what you see, or press F12 in the game. Steam then saves a picture I can look at.
- **Model:** Opus 5.5. The game gives no error messages. If the skin doesn't show up, working out
  why takes careful reasoning. If it stalls, step up to Fable 5.1, the most capable and most
  expensive model.
- **Notes for Claude:**
  - **Setup.**
    - Make the Python venv at `%LOCALAPPDATA%\TrackmaniaSkinChallenge\venv`.
    - Install the latest release of each library from PyPI at that moment, and pin the exact
      versions in `requirements.txt`.
    - Check python.org for a newer Python. If there is one, tell the user; installing it is
      their call.
    - Extract the `official/` zips into the work folder. Never edit the zips. Check their sha256
      against `official/SOURCES.md`.
  - **DDS writer.**
    - Write legacy headers (FourCC `DXT1`, `DXT5`, `ATI1`, `ATI2`) with a full mip chain, at
      2048². Nadeo's reference files in the model zip have 12 mips.
    - Get the block data from Pillow's `bcn` encoder. Pillow writes BC5 with a DX10 header and no
      mips, so write the header yourself.
    - BC4 needs its own small numpy encoder, or the R half of Pillow's BC5 blocks.
    - Keep BC1 blocks in 4-colour mode (color0 > color1).
    - Self-test: decode every file written and compare it with the source.
    - Compare the header layout and the ATI2 channel order with Nadeo's files.
  - **Install.**
    - Build a zip with the textures at its root plus an `Icon.tga`, and use no spaces in its
      name.
    - Record each file in `skins/installed.json` (name + sha256).
    - Only write when the exact target name is free, or is ours in the manifest with a matching
      hash. The game folder's path lives only in the install code (see `CLAUDE.md`).
  - **Questions the test settles.** Record the answers under "Things we learned":
    - Which files the game needs. Try a full zip and a Skin-only zip.
    - Which way CoatR and DirtMask values run. Nadeo's reference CoatR is a 16×16 DXT1, while
      the ReadMe says BC4.
    - Whether a new skin needs a game restart. One guide says a black car is fixed by leaving
      the garage and coming back.
    - How big a zip can be. Uploads have reportedly failed around 9 MB, so aim well under.
  - **Steam screenshots.**
    - Look in `C:\Program Files (x86)\Steam\userdata\<id>\760\remote\2225070\screenshots\`, and
      check that 2225070 is Trackmania's Steam app id.
    - Read only that folder, or pictures the user pastes.

### [ ] 2. The viewer

- **What it's for:** seeing a skin before it goes into the game. You see it to decide whether
  you like it. I see it to check my work before I show you.
- **What you'll see:** a page in your browser showing the car on a floor like the game's
  stadium, wearing the test skin.
  - Drag to spin it.
  - Scroll to zoom.
  - One button switches between day and night. At night the lights and glowing parts come on.

  Put it next to the game: does it look the same? Tell me what's missing.
- **Model:** Opus 5.5. Getting a hidden browser to draw 3D reliably, and making the picture
  match the game, both take judgment. "I like it in the game" depends on that match. If the
  viewer still doesn't match the game after a few tries, step up to Fable 5.1.
- **Notes for Claude:**
  - **Page and server.**
    - Keep three.js in `viewer/` at its latest release, with the version pinned (0.186.0 on
      2026-09-23; check again).
    - Serve the page with Python's built-in web server, because ES modules don't load from
      `file://`.
    - Export the mesh from the FBX into a compact file the page loads.
  - **Lighting and floor.**
    - Take a free CC0 HDRI from Poly Haven (latest).
    - Give the floor a road-like material.
  - **Materials.**
    - The game's Skin_R holds R = roughness and G = metalness. three.js reads roughness from G
      and metalness from B, so swizzle when making the viewer's textures.
    - Showing CoatR as clearcoat is a guess until it has been compared with the game.
  - **Night.** Use the Details_I alpha codes (table in `CLAUDE.md`) to decide which parts glow.
  - **Claude's snapshots.**
    - Playwright (latest) drives the installed Edge headless and saves one sheet of angles:
      front and rear three-quarter, both sides, top, and night.
    - Look at the sheet before showing anything to the user.
    - Prove that headless WebGL works first. If it fights, try Chrome, or
      `--enable-unsafe-swiftshader`.
  - **Credit.** Put a line on the page crediting the car model's author, amogusstrikesback2
    (CC-BY-4.0).

### [ ] 3. Teaching the tool the car's shape

- **What it's for:** making sure "a stripe down the middle" or "a 7 on the doors" lands
  straight, unbroken and in the right place. Without this, I'd be guessing on a flat map.
- **What you'll see:**
  - In the viewer, the car with each area painted its own colour and named: nose, bonnet, roof,
    sides, tail, wheel covers and so on.
  - The areas that are always mirrored left-to-right, marked.
  - A sample skin with a stripe running unbroken from nose to tail, and a 7 that reads correctly
    on both sides. You see it in the viewer and in the game.
- **Model:** Fable 5.1, the most capable model. Turning the car's 3D shape into a painting guide
  is the hardest technical step, and every design after it depends on getting it right.
- **Notes for Claude:**
  - **Baking.**
    - Bake a 3D position, a normal and an area label per texel for the Skin and Details
      textures, by rasterising the mesh in UV space (image row = 1 − v).
    - Cache the results in the work folder.
  - **Mirrored areas.**
    - Measured 2026-09-23: the mid-body is unique per side, but the outer wheel covers (|x| > 90)
      and the nose and tail ends share texels between left and right. Details are about 90 %
      shared.
    - A shared texel has only one position, so evaluate designs at |x|. They come out symmetric.
  - **Decals.**
    - Put decals (text, numbers) only on unique areas, and only on faces that point the way the
      decal is projected.
    - Refuse a placement that crosses into a shared area, and say why.
  - **Edges.**
    - Pad the UV islands by about 16 px, so seams don't show from a distance.
    - Downsample colour for the mips in linear light.

### [ ] 4. The paint box

- **What it's for:** the building blocks for your designs:
  - any colour;
  - finishes: gloss, matte, metallic, chrome;
  - fades;
  - stripes and bands;
  - numbers and words in a few bold fonts;
  - glowing light colours.

  Other patterns, such as camo, carbon fibre or hexagons, get added when one of your designs asks
  for them.
- **What you'll see:** 3–4 very different sample skins in the viewer, with one of them in the
  game.
- **Model:** Sonnet 5. These are straightforward pieces built on checkpoint 3.
- **Notes for Claude:**
  - A design is `skins/<name>/design.py`, a short script that calls the paint library. The user
    never reads it.
  - Fonts come from Windows: Bahnschrift, Impact, Arial Bold.
  - Use free tools only. The user decided against paid image generation (2026-09-23).

### [ ] 5. Your first skin, start to finish

- **What it's for:** the real test. You describe a skin in your own words, and I show it in the
  viewer. You ask for changes, then say yes, and it's in your game.
- **What you'll see:** your own skin in the game, one you'd actually drive with. We also time
  it:
  - under a minute from your words to the viewer;
  - under 30 seconds from "yes" to the game.
- **Model:** Opus 5.5 first. This step is a rehearsal of everyday use, so it should run on the
  model everyday use will run on: the speed and the designs you judge are then what you'll
  really get. If the designs don't land after a couple of rounds, switch to Fable 5.1 for the
  same skin. Whichever one gives you skins you like becomes the everyday model.
- **Notes for Claude:**
  - `skins/<name>/notes.md` keeps the user's words and each change request, so a cold session
    can pick up any skin.
  - Keep a small picture of each version.
  - While iterating, preview from uncompressed textures, and encode DDS only at install.

### [ ] 6. Tidy up for everyday use

- **What it's for:** making every future chat start straight at "describe your skin", without
  the building notes getting in the way.
- **What you'll see:** a fresh chat where you describe a skin and it just works.
- **Model:** Sonnet 5. It only writes down a routine that already works.
- **Notes for Claude:**
  - Move the chat loop (describe → view → change → install) into a project skill in
    `.claude/skills/`.
  - Cut the build-phase parts of `CLAUDE.md`. Replace the `@BRIEF.md` import with the few lines
    of the brief that still apply.
  - Check the current Claude Code docs on skills first.
  - The skill recommends whichever model won checkpoint 5 for the everyday loop. Fable 5.1
    turns can take minutes, so weigh speed against design quality.

## Decisions (for Claude)

- **The tool is Python.** Each library is the latest release at the time it's added, pinned in
  `requirements.txt`. The venv lives outside OneDrive.
- **The car is read straight from the FBX,** with a small parser: binary v7300, meshes Skin_01,
  Details_01, Glass_01 and Wheels_01. No Blender, no converters.
- **The model's Skin UVs match Nadeo's `UV_Skin.png`** (IoU 0.95, image row = 1 − v), so the
  community model can stand in for the game's car.
- **Painting happens in 3D** (position and normal per texel) and is baked into the flat
  textures.
- **The viewer is a three.js page** served by Python. Claude's snapshots come from Playwright
  driving Edge.
- **DDS files come from our own writer:** Pillow's block encoder, a legacy header and a mip
  chain.
- **Install:** one zip per skin, no spaces in its name, with `Icon.tga`, recorded in
  `skins/installed.json`.
- **Viewer must-haves (user, 2026-09-23):** spin and zoom, day and night, a game-like setting.
  Comparing versions isn't wanted.
- **Free tools only (user, 2026-09-23).** If a paid tool would be far better, tell the user and
  discuss it first.
- **The user has Club access (2026-09-23),** which custom skins need.
- **Models (user, 2026-09-23):** the user can use Fable 5.1, for the steps that need the best.
  Fable 5.1 runs checkpoint 3 and is the step-up when a step stalls. Opus 5.5 handles the other
  hard steps, and Sonnet 5 the straightforward ones.
- **Credit:** amogusstrikesback2, CC-BY-4.0, wherever the car model is reused.

## Things we learned

Filled in as we go.
