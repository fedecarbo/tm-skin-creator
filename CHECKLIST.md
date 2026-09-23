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
                         read the car, find its parts, paint it,
                         make the game files, install
  viewer/              the page where you look at the car in 3D,
                         and the page of all your skins
  car/parts.json       the name of every part of the car
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
- the tool's maps of the car and its parts;
- the picture maker's model files;
- the built game files.

All of them can be rebuilt from the project at any time.

## Checkpoints

The work comes in two parts:
- **Part 1, setting up (checkpoints 1–4):** the tool learns the car. It learns which files the
  game takes, every part of the car, and exactly how every material looks in the game.
- **Part 2, designing (checkpoints 5–8):** the design tools, then your first real skin, then
  everyday use.

Part 1 comes first, because every design depends on it.

### [x] 0. The plan

- **What it's for:** agreeing the steps before anything gets built.
- **What you'll see:** this file. We went through it together on 2026-09-23.
- **Model:** Opus 5.5. Deciding how the whole tool fits together is the hardest thinking in the
  project.

## Part 1: Setting up

### [ ] 1. A test paint job in your game

- **What it's for:** proving the basics first. The tool has to make files the game accepts and
  put them where the game finds them. If that fails, nothing else matters, so it comes first.
  This step also sets up the folders and the tools.
- **What you'll see:** in the game, go to Garage → My Skins → Upload skin and pick
  "TSC_Test". The car wears a loud test pattern on the body, the details, the wheels and the
  glass:
  - a numbered grid, with arrows that say LEFT, RIGHT and FRONT;
  - one chrome area and one matte area;
  - lights glowing an odd colour;
  - tinted glass.

  A second test, "TSC_Test_Sharp", has the same pattern at double sharpness, to see whether
  the game takes it.

  Tell me what you see, or press F12 in the game. Steam then saves a picture I can look at.
- **Model:** Opus 5.5. The game gives no error messages. If the skin doesn't show up, working out
  why takes careful reasoning. If it stalls, step up to Fable 5.1, the most capable and most
  expensive model.
- **Notes for Claude:**
  - **Setup.**
    - Make the Python venv at `%LOCALAPPDATA%\TrackmaniaSkinChallenge\venv`. The system Python
      is 3.14.2 (2026-09-23).
    - Install the latest release of each library from PyPI at that moment, and pin the exact
      versions in `requirements.txt`.
    - Check python.org for a newer Python. If there is one, tell the user; installing it is
      their call.
    - Extract the `official/` zips into the work folder. Never edit the zips. Check their sha256
      against `official/SOURCES.md`.
  - **DDS writer.**
    - Write legacy headers (FourCC `DXT1`, `DXT5`, `ATI1`, `ATI2`) with a full mip chain.
      Nadeo's reference files in the model zip have 12 mips at 2048².
    - Get the block data from Pillow's `bcn` encoder. Pillow writes BC5 with a DX10 header and no
      mips, so write the header yourself.
    - BC4 needs its own small numpy encoder, or the R half of Pillow's BC5 blocks.
    - Keep BC1 blocks in 4-colour mode (color0 > color1).
    - Self-test: decode every file written and compare it with the source.
    - Compare the header layout with Nadeo's files.
    - The ATI2 channel order is ambiguous: NVIDIA says ATI2 is BC5 with R and G swapped. Settle
      it by decoding Nadeo's stock `Skin_R`/`Details_R` (R = roughness, G = metalness) and
      `Details_N`, and with an asymmetric test pattern in game.
    - Keep the whole pipeline resolution-independent.
  - **Wheels and glass.** They aren't in the ReadMe, but Nadeo's 2020 post lists them:
    - `Wheels_B` BC1, `Wheels_R` BC5, `Wheels_N` BC5, `Wheels_DirtMask` BC4;
    - `Glass_D` BC1, where tint is the colour and luminosity the opacity;
    - `Glass_I`, which the post calls "BC5, RGB + alpha". That can't be right, so try BC3.
    - The stock files disagree: `Wheels_R` is one-channel `ATI1` at 512×1024, and the glass set
      is `Glass_T`/`Glass_I` (`DXT5`, 1024²). Test which ones the game reads.
  - **Install.**
    - Build a zip with the textures at its root plus an `Icon.tga`, and use no spaces in its
      name.
    - Record each file in `skins/installed.json` (name + sha256).
    - Only write when the exact target name is free, or is ours in the manifest with a matching
      hash. The game folder's path lives only in the install code (see `CLAUDE.md`).
  - **Questions the test settles.** Record the answers under "Things we learned":
    - Which files the game needs. Try a full zip and a Skin-only zip.
    - Which wheel and glass files and formats the game reads.
    - Whether 4096² works for Skin, Details and Wheels, and how big the zip gets. Uploads have
      reportedly failed around 9 MB, so pick the default resolution from this.
    - Whether a new skin needs a game restart. One guide says a black car is fixed by leaving
      the garage and coming back.
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
  - Buttons show or hide the body, the details, the wheels and the glass. For example, hide the
    body to see what's underneath.

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
    - Export the mesh from the FBX into a compact file the page loads. Keep the four meshes
      separate so they can be hidden.
  - **Lighting and floor.**
    - Take a free CC0 HDRI from Poly Haven (latest).
    - Give the floor a road-like material.
  - **Materials.**
    - The game's `_R` holds R = roughness and G = metalness. three.js reads roughness from G
      and metalness from B, so swizzle when making the viewer's textures.
    - Showing CoatR as clearcoat is a guess until checkpoint 4 has compared it with the game.
  - **Night.** Use the Details_I alpha codes (table in `CLAUDE.md`) to decide which parts glow.
  - **Claude's snapshots.**
    - Playwright (latest) drives the installed Edge headless and saves one sheet of angles:
      front and rear three-quarter, both sides, top, and night.
    - Look at the sheet before showing anything to the user.
    - Prove that headless WebGL works first. If it fights, try Chrome, or
      `--enable-unsafe-swiftshader`.
  - **Credit.** Put a line on the page crediting the car model's author, amogusstrikesback2
    (CC-BY-4.0).

### [ ] 3. The car taken apart

- **What it's for:** the tool learns every part of the car, so "red brake discs" or "a stripe
  down the bonnet" lands exactly where it should. The 3D model has no named parts. It's four
  lumps: body, details, wheels and glass. So the tool finds the parts itself:
  - it separates the pieces;
  - it splits them along the creases;
  - it groups the matching ones, such as four identical brake parts, or the same piece on the
    left and the right.

  Then I name every part: bonnet, sidepods, front wing, wishbones, springs, brake discs, cables,
  exhaust, cockpit, seat, steering wheel, headlights, tyre, rim and so on.
- **What you'll see:**
  - The car in the viewer, each part in its own colour. Click any part to see its name.
  - A list of every part, where you can hide or show each one.
  - The areas that are always mirrored left-to-right, marked.
  - A test skin in your game that paints named parts, such as "brake discs red, cables yellow,
    rims gold". You confirm that the right things changed colour, and tell me any name I got
    wrong.
- **Model:** Fable 5.1, the most capable model. Turning the car's 3D shape into a map of named
  parts is the hardest technical step, and every design after it depends on getting it right.
- **Notes for Claude:**
  - **What the FBX holds (measured 2026-09-23):**
    - Binary FBX 7300 from Maya 2018, Y up, in cm. The car spans x ±107, y −1.2 to 87 and
      z −161.8 to 216.6.
    - An empty `TMCar` node holds `Wheels_01`, `Glass_01`, `Details_01` and `Skin_01`, all with
      identity transforms.
    - One UV set (`map1`) and one Lambert material per mesh.
    - No names below mesh level, no material indices, no smoothing (all 0), no creases, no
      vertex colours. Per-corner normals, tangents and binormals are present.
    - Details: 53,159 vertices, 65,246 triangles, 1,918 connected pieces and 2,087 UV islands.
      Skin: 17,710 vertices, 27,184 triangles, 133 pieces. Glass: 36 pieces. Wheels: 4 pieces.
  - **Segmentation.**
    - Connected components first.
    - Then split at crease edges: the dihedral angle, and breaks in the corner normals.
    - Then split at UV-island boundaries.
    - Group mirrored pieces (x → −x) and repeated identical shapes: 122 Details shapes appear 4
      or more times, such as bolts.
    - Build a hierarchy, for example suspension → arms, springs.
  - **Naming.**
    - Render each group highlighted from several angles, and name it by eye.
    - Cross-check against the stock `Details_I` alpha regions (lights) and the user's in-game
      screenshots.
    - Store the full map in the work folder: part → mesh, triangle ids and a texel mask per
      texture set. Commit the part names and hierarchy as `car/parts.json`.
  - **Baking.**
    - Bake a 3D position, a normal and a part label per texel for every texture set, by
      rasterising the mesh in UV space (image row = 1 − v).
    - Cache the results in the work folder.
  - **Mirrored and shared areas.**
    - Measured 2026-09-23: the Skin shares about 11 % of its texels between left and right
      (the outer wheel covers, |x| > 90, and the nose and tail ends). Details share about 82 %,
      with stacks up to 125 deep.
    - All four wheels share identical UVs that fill 0–1, so every wheel looks the same. Check
      whether the left and right wheels mirror the texture. That decides whether text on the
      wheels reads backwards on one side.
    - A shared texel has only one position, so evaluate designs at |x|. They come out
      symmetric.
  - **Decals.**
    - Put decals (text, numbers, pictures) only on unique areas, and only on faces that point
      the way the decal is projected.
    - Refuse a placement that crosses into a shared area, and say why.
  - **Edges.**
    - Pad the UV islands by about 16 px, so seams don't show from a distance.
    - Downsample colour for the mips in linear light.
  - **Viewer.** Add a parts list with hide/show, isolate, click-to-name and a colour-by-part
    mode.

### [ ] 4. The materials lab

- **What it's for:** testing every material in your game, until the tool knows exactly how each
  one looks and the viewer matches the game.
  - **Finishes:** a ladder from matte to glossy, and from plain paint to metallic and chrome, on
    the body, the details and the wheels.
  - **The clear coat:** off and on, to learn what it does. Nadeo mentions "glitter".
  - **Dirt:** where it shows and when.
  - **Every kind of glow,** each on a named part:
    - brake lights, and brake heat;
    - headlights;
    - always on, and night only;
    - team colour;
    - turbo, boost and exhaust heat.
  - **Glass:** tint and how see-through it is.
- **What you'll see:** a few test skins in your game. You drive them, brake, use turbo, and try
  day and night, and tell me or screenshot what you see. Then I tune the viewer until it
  matches your game. The result is a set of named finishes and glows the tool knows exactly,
  such as "satin black", "brushed metal", "chrome" and "neon blue at night".
- **Model:** Opus 5.5. It takes careful reasoning from what you see in the game. If the viewer
  won't match the game, step up to Fable 5.1.
- **Notes for Claude:**
  - **Test skins.**
    - A roughness × metalness swatch grid on the body, the details and the wheels, with labels.
    - CoatR at 0 and at 255. The post says "clearcoat, glitter paint effect", and without the
      file the coat follows roughness and metalness. Nadeo's reference CoatR is a flat 0,
      stored as a 16² DXT1.
    - DirtMask at 0 and at 255.
    - Every `Details_I` alpha code on a named part.
    - Glass tint and opacity.
    - An asymmetric `Details_N` pattern, to confirm OpenGL Y+ and the channel order.
  - **The stock `Details_I` (measured 2026-09-23):**
    - Alpha ≈160 covers 46 % (RGB ~35), ≈255 covers 32 % (RGB ~1), ≈96 covers 20 % (RGB ~16),
      ≈128 covers 0.5 %, and 0 covers 0.4 % (reddish).
    - Codes 32 and 64 are unused, and 192 is almost unused.
    - The values are spread slightly around each level (97, 161, 225 …), so snap to the
      nearest code when reading them.
  - **Stock `Details_R`:** roughness mostly 13 or 94–117. Metalness clusters at 64, 199 and
    255.
  - Record every result under "Things we learned". Tune the viewer's shaders to match.
  - **Output:** a named library of finishes and glows with measured values, in the code, for
    the paint box to use.

## Part 2: Designing

### [ ] 5. The paint box

- **What it's for:** the design tools, built on the parts from step 3 and the materials from
  step 4:
  - any colour, fades, stripes, bands and shapes;
  - patterns: camo, carbon fibre, hexagons, checks, splatter, worn and grungy effects and more;
  - numbers and words in many fonts;
  - pictures placed on the car;
  - any finish or glow on any part, for example "chrome rims, matte black suspension, glowing
    blue cables".

  Anything missing from the box can still be drawn, because I make every design fresh. The box
  makes the common things quick and reliable.
- **What you'll see:** 4 or 5 very different sample skins, for example a race car, a flag
  theme, an abstract art piece and a heavy pattern. They're shown together on a new page of all
  your skins. Click any one to see it in 3D. One of them goes into the game.
- **Model:** Sonnet 5. These are straightforward pieces built on checkpoints 3 and 4.
- **Notes for Claude:**
  - A design is `skins/<name>/design.py`, a short script that calls the paint library. The user
    never reads it.
  - Paint by part name, using `car/parts.json`.
  - Evaluate patterns procedurally in 3D (triplanar on the baked positions), so they don't
    break at seams.
  - Fonts: the Windows fonts (Bahnschrift, Impact, Arial Bold) plus a few free OFL Google
    Fonts. Pin them and record their licences.
  - **Gallery page** in `viewer/`: one thumbnail per skin, newest first, the installed one
    marked. Clicking a thumbnail opens the skin in 3D. It reads `skins/*/` and
    `skins/installed.json`.
  - Use free tools only. The user decided against paid image generation (2026-09-23).

### [ ] 6. The picture maker

- **What it's for:** detailed artwork, such as a realistic tiger across the doors or a painted
  character, made by a free program that runs on your PC.
- **What you'll see:** two sample skins with detailed art in the viewer. One of them goes into
  the game.
- **Model:** Opus 5.5. Setting it up on a brand-new graphics card, and judging whether the art
  is good enough, both take care.
- **Notes for Claude:**
  - At build time, research the best free local text-to-image model that fits 16 GB of VRAM
    and 16 GB of system RAM. Its licence must allow personal use, including a skin other
    players see online. Don't pick one in advance.
  - Tell the user the download size before downloading.
  - Run it through Hugging Face `diffusers` in the tool's venv, not a separate app. The RTX
    5070 Ti is Blackwell (sm_120), so it needs a PyTorch build with CUDA 12.8 or later.
  - Put the weights in `%LOCALAPPDATA%\TrackmaniaSkinChallenge\models` (set `HF_HOME`).
  - Output:
    - art with a transparent background (a free background-removal tool, latest release),
      placed through the decal system on unique areas only;
    - seamless tileable textures, for patterns.
  - Generate a few candidates and look at them before using one. Aim for under a minute per
    picture.

### [ ] 7. Your first skin, start to finish

- **What it's for:** the real test. You describe a skin in your own words, and I show it in the
  viewer. You ask for changes, then say yes, and it's in your game.
- **What you'll see:** your own skin in the game, one you'd actually drive with.
  - When your idea is clear, I show one design. When it's vague, I show two or three.
  - Looks come first. Each round takes up to about 10 minutes.
  - "Yes" reaches the game in under 30 seconds.
- **Model:** Fable 5.1 first, because you put looks before speed and it's the strongest
  designer. Then we make one skin on Opus 5.5 to compare. The one you prefer becomes the
  everyday model.
- **Notes for Claude:**
  - `skins/<name>/notes.md` keeps the user's words and each change request, so a cold session
    can pick up any skin.
  - Keep a small picture of each version.
  - While iterating, preview from uncompressed textures, and encode DDS only at install.

### [ ] 8. Tidy up for everyday use

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
  - The skill recommends whichever model won checkpoint 7 for the everyday loop. Fable 5.1
    turns can take minutes, which fits the user's "looks first".

## Decisions (for Claude)

- **The foundation comes first (user, 2026-09-23).** The tool must truly know the car: every
  part, found along the creases, and every material, checked in the game. Design tools come
  after.
- **A universal tool (user, 2026-09-23):** any kind of skin, not a fixed set of styles.
- **Looks before speed (user, 2026-09-23).** Up to about 10 minutes a round is fine if the skin
  is clearly better.
- **One design or a few (user, 2026-09-23):** one when the idea is clear, 2–3 takes when it's
  vague.
- **Wanted extras (user, 2026-09-23):** a local picture maker and a page of all skins. Sharing
  skins and copy-from-picture aren't wanted for now.
- **The user helps with in-game tests (2026-09-23).**
- **The tool is Python.** Each library is the latest release at the time it's added, pinned in
  `requirements.txt`. The venv lives outside OneDrive.
- **The car is read straight from the FBX,** with a small parser: binary v7300, meshes Skin_01,
  Details_01, Glass_01 and Wheels_01. No Blender, no converters.
- **The model's Skin UVs match Nadeo's `UV_Skin.png`** (IoU 0.95, image row = 1 − v), so the
  community model can stand in for the game's car.
- **Painting happens in 3D** (position, normal and part per texel) and is baked into the flat
  textures.
- **The viewer is a three.js page** served by Python. Claude's snapshots come from Playwright
  driving Edge.
- **DDS files come from our own writer:** Pillow's block encoder, a legacy header and a mip
  chain.
- **Install:** one zip per skin, no spaces in its name, with `Icon.tga`, recorded in
  `skins/installed.json`.
- **Viewer must-haves (user, 2026-09-23):** spin and zoom, day and night, a game-like setting,
  hide and show parts. Comparing versions isn't wanted.
- **Free tools only (user, 2026-09-23).** If a paid tool would be far better, tell the user and
  discuss it first. The picture maker is free and local.
- **The user has Club access (2026-09-23),** which custom skins need.
- **Models (user, 2026-09-23):** the user can use Fable 5.1, for the steps that need the best.
  Fable 5.1 runs checkpoint 3 and the first round of checkpoint 7, and is the step-up when a
  step stalls. Opus 5.5 handles the other hard steps, and Sonnet 5 the straightforward ones.
- **This PC (2026-09-23):** an RTX 5070 Ti with 16 GB, a Ryzen 7 5800X3D, 16 GB of RAM and
  Python 3.14.2.
- **Credit:** amogusstrikesback2, CC-BY-4.0, wherever the car model is reused.

## Things we learned

- **2026-09-23, from Nadeo's 2020 post and the stock files:** a skin can also paint the wheels
  and the glass, but not the player number or ID, the turbo colour, the digit colours, the rear
  lights or the glass gear display. See `CLAUDE.md` for the texture table.
