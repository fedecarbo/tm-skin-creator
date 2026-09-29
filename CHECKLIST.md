# Checklist

This is the plan for building the skin tool, one checkpoint at a time.

- **For Claude:** while a checkpoint is unticked, read this file at the start of a session, find
  the first checkpoint whose box isn't ticked, and carry on from there. Tick a box only after
  the user has seen what the checkpoint promises. If something we learn changes the plan,
  change this file and tell the user. Once every box is ticked, sessions start from the `skin`
  skill (`.claude/skills/skin/`) and this file is the record: search it when changing the tool.
  Anything the user asks for after the build is an improvement, never a new checkpoint (see
  "Improvements after the build").
- **Switching model:** each checkpoint names the Claude model to use. At the start of a session,
  type `/model` in the chat box and pick it.
- Each checkpoint has plain-language parts for you, then **Notes for Claude**, which you can
  skip.

## How the project is organised

```
Trackmania Skin Challenge/
  BRIEF.md, CLAUDE.md, CHECKLIST.md   the brief, Claude's standing notes, this plan
  IMPROVEMENTS.md      the queue of things the tool should do better
  .claude/skills/skin/ the everyday routine: your words -> the car -> your game
  .claude/rules/       Claude's notes for working on the machinery
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
  Dockerfile, compose.yaml, docker/
                       the viewer on the Mac; the Windows PC doesn't need Docker
```

The bulky working files live on this PC, outside OneDrive, so OneDrive doesn't spend its time
syncing them: `%LOCALAPPDATA%\TrackmaniaSkinChallenge\`. They are:
- the tool's software setup (the Python environment);
- the unpacked car model;
- the tool's maps of the car and its parts;
- the picture maker's model files;
- the built game files;
- what the viewer page loads (the car, the sky, each skin's pictures).

All of them can be rebuilt from the project at any time.

## Checkpoints

The work comes in two parts:
- **Part 1, setting up (checkpoints 1–4):** the tool learns the car. It learns which files the
  game takes, every part of the car, and exactly how every material looks in the game.
- **Part 2, designing (checkpoints 5–8):** the design tools, then your first real skin, then
  everyday use. After that, what you ask for is an improvement: it goes on the improvement list
  (`IMPROVEMENTS.md`), and its notes go at the end of this file.

Part 1 comes first, because every design depends on it.

### [x] 0. The plan

- **What it's for:** agreeing the steps before anything gets built.
- **What you'll see:** this file. We went through it together on 2026-09-23.
- **Model:** Opus 5.5. Deciding how the whole tool fits together is the hardest thinking in the
  project.

## Part 1: Setting up

### [x] 1. A test paint job in your game

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

### [x] 2. The viewer

- **What it's for:** seeing a skin before it goes into the game. You see it to decide whether
  you like it. I see it to check my work before I show you.
- **What you'll see:** a page in your browser showing the car in a photo studio, wearing the
  test skin. You swapped the stadium for a studio on 2026-09-24.
  - Drag to spin it.
  - Scroll to zoom.
  - One button switches between day and night. At night the room darkens with the car, and the
    lights and glowing parts come on.
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
  - **Lighting and background (user's choice, 2026-09-24).** The user tried the stadium, then
    three studios, and chose the studio look of another project of theirs
    (`Documents\Trackmania Skin Studio`). They showed it for its lighting and background only:
    take nothing else from that project.
    - Day: Poly Haven "Studio Small 09" (2K) at strength 1, plus one warm key light from above
      the front left (0.55, 1, 0.35) that casts the shadow.
    - Night: Poly Haven "Dikhololo Night" (1K) at 2.2, with a dim blue key.
    - The room is lit by the same light, so it darkens with the car at night (the user asked
      for that instead of fixed background colours). It's a seamless charcoal cove: floor, curve,
      walls and ceiling, with a linear grey of 0.035 (`TUNE.room`). There's a soft dark patch
      under the car. The room is drawn from inside only, so the camera can go under the floor to
      see the underside. ACES tone mapping, exposure 0.9.
  - **Materials.**
    - The game's `_R` holds R = roughness and G = metalness. three.js reads roughness from G
      and metalness from B, so swizzle when making the viewer's textures.
    - Showing CoatR as clearcoat is a guess until checkpoint 4 has compared it with the game.
  - **Night.** Use the Details_I alpha codes (table in `.claude/rules/tool.md`) to decide which
    parts glow.
  - **Claude's snapshots.**
    - Playwright (latest) drives the installed Edge headless and saves one sheet of angles:
      front and rear three-quarter, both sides, top, and night.
    - Look at the sheet before showing anything to the user.
    - Prove that headless WebGL works first. If it fights, try Chrome, or
      `--enable-unsafe-swiftshader`.
  - **Credit.** Put a line on the page crediting the car model's author, amogusstrikesback2
    (CC-BY-4.0).
  - **Done 2026-09-24.** The user saw it and approved it for now ("leave it like that"). The
    viewer stays open to change: checkpoint 4 tunes it against the game.
    - `tool/view.py` prepares the data and serves the page. The data is `car.bin`, PNG texture
      "slots" and the sky. Missing textures fall back to stock, as in the game. `tool/snap.py`
      takes the snapshot sheets. The page is `viewer/index.html` + `viewer/viewer.js`, with
      three.js 0.186.0 in `viewer/lib/three`.
    - The HDRIs are downloaded into the work folder and checked against Poly Haven's md5s
      (`HDRIS` in `tool/view.py`).
    - Headless Edge draws on the real RTX 5070 Ti through ANGLE/D3D11 (`--use-angle=d3d11
      --enable-gpu`). Load to first picture takes about 2.5 s.
    - Paint colour against the user's editor screenshots of TSC_Test_SkinOnly: orange (234,
      148, 58) against the game's (253, 159, 46), blue (56, 102, 213) against (27, 57, 189).
      ACES pulls orange towards yellow, as the game does. `TUNE` in `viewer.js` (exposure, env,
      key, coat) can be overridden from the URL when matching again.

### [x] 3. The car taken apart

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
  - **Done 2026-09-24.** The user checked TSC_Parts in the game (several rounds on the borders,
    see "Clean borders" under Things we learned) and the viewer, and ticked it.
    - `tool/segment.py` splits each mesh into pieces (vertex-connected), groups (touching
      pieces) and mirror twins; ids are deterministic and cached in the work folder.
    - `tool/naming.py` is the naming table, written by eye from labelled renders: 87 names in
      14 assemblies. `tool/parts.py` resolves it to every triangle (unnamed pieces join the
      nearest named piece of their mesh), writes `car/parts.json` (205 instances: name + side +
      end, pieces, texels, shared share) and gives texel masks: `parts.load().mask(bake, set,
      name, side=, end=)`. `python -m tool.parts --review` renders `build/parts_review.png`.
    - `tool/bake.py` now also bakes `count` (triangles per texel) and `sides` (left/right bits).
    - `tool/partskin.py` builds TSC_Parts, which paints named parts in loud colours; it's
      installed. The user checks it in the game; the viewer shows the same.
    - The viewer has a parts panel (hide/show per part or assembly, "only", click a part to see
      its name, colour by part, shared-areas overlay). `viewer.showParts(...)` drives it for
      snapshots (`tool/snap.py` shots take a fifth item).
    - Known rough edges: some inner names are guesses (side vent, side vane, nose sensor,
      airbox). The body shell is one part on purpose (see "Clean borders" below).
    - Pieces inside a named group can be named apart when a design needs them: the exporter
      split the meshes along every crease, so each crease-bounded piece has an id. Put the new
      entry before the group's entry (first name wins). First case: "sidepod grille plate"
      (2026-09-24), which the user spotted by its creases.

### [x] 4. The materials lab

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
  - **Where it stands (2026-09-24, Fable 5.1):** `tool/labskin.py` builds and the tool installed
    two lab skins, **TSC_Lab** and **TSC_Lab_NoCoat** (identical, minus `Skin_CoatR`). The
    docstring at the top of `tool/labskin.py` is the key: what sits where.
    - Done: the skin editor screenshots (09:46-09:48) settled the varnish, roughness, metalness
      and the tyres (see "Things we learned"). The viewer's varnish now follows the game
      (`Skin_Coat` = 255 - CoatR as the coat amount). `tool/finishes.py` holds the named
      finishes; its `GLOWS` table waits for the driving tests.
    - Done too: the user drove TSC_Lab at night and on dirt (screenshots 10:07-10:11). `GLOWS`
      in `tool/finishes.py` and `GLOW` in `viewer/viewer.js` now say what the game showed.
      `build/night_vs_game.png` puts the viewer's night beside the game's.
    - Left open, on purpose: brake heat, turbo colour, exhaust heat and boost were never seen to
      light up. They stay off in the viewer until a design wants them; then test that design.
    - **Done 2026-09-24.** The user checked the viewer against their screenshots and ticked it.

## Part 2: Designing

### [x] 5. The paint box

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
  - **Start from `tool/carbonskin.py`** (2026-09-24): a design built by hand from parts and
    `tool/finishes.py` (a triplanar carbon weave, matte body, gloss on named parts). The user
    liked it in the game. The paint box should make that kind of thing from words.
  - A design is `skins/<name>/design.py`, a short script that calls the paint library. The user
    never reads it.
  - Paint by part name, using `car/parts.json`.
  - Evaluate patterns procedurally in 3D (triplanar on the baked positions), so they don't
    break at seams.
  - **A library of finishes (user, 2026-09-24).** "Finish" is the user's word for the whole
    family: how a surface looks, from its shine, a pattern, or wear. Grow `tool/finishes.py`
    into a named library, each entry a look (a pattern drawn in 3D) plus a default shine
    (roughness, metalness, varnish), with any shine able to override it ("scratched matte
    olive", "brushed gold"). The user asked for car-relevant materials; the agreed target:
    - paint: gloss, satin, matte, metallic (flake), pearl, candy;
    - metal: chrome, polished aluminium, brushed steel, brushed titanium, gunmetal, gold,
      copper, anodised (a colour on metal), raw cast;
    - composites and plastics: carbon weave, forged carbon, kevlar, gloss plastic, matte
      plastic, rubber, vinyl wrap;
    - inside: leather, cloth, belt webbing;
    - wear: scratched, chipped, dusty, faded, rusted, greasy, race-worn;
    - light: neon (a self-lit colour, via `Details_I` code 96), reflective tape.
    **The user won't sort their words into colour, finish and layout; the tool must** (user,
    2026-09-24). Every painted area is a colour plus a finish. A finish may bring its own
    colour (carbon is black, chrome silver, gold gold), which a stated colour overrides ("red
    carbon" tints the weave). Layouts (stripes, camo, fades) arrange colours; the finish under
    them defaults to gloss. When a phrase is genuinely ambiguous, show a picture and ask.
    Limits to say out loud when asked: no holographic or colour-shift paint (the game's
    shading can't), and the body takes no relief, so body patterns and scratches are paint
    only; the inner car can have relief through `Details_N`.
  - Fonts: the Windows fonts (Bahnschrift, Impact, Arial Bold) plus a few free OFL Google
    Fonts. Pin them and record their licences.
  - **Gallery page** in `viewer/`: one thumbnail per skin, newest first, the installed one
    marked. Clicking a thumbnail opens the skin in 3D. It reads `skins/*/` and
    `skins/installed.json`.
  - Use free tools only. The user decided against paid image generation (2026-09-23).
  - **Done 2026-09-24 (Fable 5.1); the user looked at the samples and ticked it.** A design
    is `skins/<name>/design.py` with a `design(s)` function of `paintbox.Skin` calls; the
    docstring at the top of `tool/paintbox.py` is the key. `PY -m tool.skin show <name>` paints
    it (15-75 s at 4096², the Nebula's fine sparkle 4 min), puts it in the viewer, snapshots it
    and makes `skins/<name>/thumb.png`; `PY -m tool.skin install <name>` encodes and installs
    (32 s). The pieces:
    - `tool/colours.py`: colour words and hex codes, with modifiers ("dark", "pale");
    - `tool/finishes.py`: the library (paint, metals, composites, inside, wear, light,
      patterns), aliases, and `resolve(phrase)`, which sorts a phrase into colour + finish +
      leftover words. A metal named as a colour ("gold") is the metal; a shine word overrides
      ("matte gold", "scratched matte olive");
    - `tool/looks.py`: the patterns, drawn in 3D (triplanar) on the baked positions: carbon,
      weave, forged, cloth, webbing, brushed, flake, pearl, candy, scratched, dusty, faded,
      greasy, worn, camo, hex, checks, splatter, lines; `tool/noise.py` underneath;
    - `tool/textures.py`: rust, chips, brushed steel, cast iron, leather and quilted leather
      come from photographs (ambientCG, CC0, downloaded once into the work folder, 1K JPG
      sets ~5 MB each), wrapped on in 3D; the rust and chip pictures act as masks over the
      paint colour;
    - `tool/shapes.py`: zones with soft edges in 3D (stripe, band, plane, sphere, box, fade,
      facing, named regions "nose", "bonnet", "deck", "sides"...), combinable with & | ~;
    - `tool/coverage.py`: every part's texel coverage cached sparsely per size (built once,
      about a minute per set at 4096², 35-63 MB files in `cache/`);
    - lettering: `Skin.text()` and `Skin.decal()` project onto named spots (`paintbox.SPOTS`:
      left/right side, flanks, nose, bonnet, sidepods, decks, tail). Fonts in `tool/fonts.py`:
      Windows ones plus six OFL Google fonts pinned by commit and sha256;
    - glow: `Skin.glow(part, colour, kind)` writes `Details_I` (inner car only);
    - the gallery: `viewer/gallery.html` + `tool/gallery.py` (`PY -m tool.gallery` serves and
      opens it); `PY -m tool.skin list` prints the same list.
    - **A growing library (user, 2026-09-24: "a fairly large library").** `PY -m tool.textures
      search "snake skin"` fetches candidates from ambientCG (thousands of CC0 surfaces) and
      lays their thumbnails on one sheet in `build/`; look, then `PY -m tool.textures add
      "snake skin" Leather008 --scale 40` names the chosen one. From then on "snake skin"
      works in any phrase ("green snake skin, glossy"). Added sets are kept in the work
      folder's `textures/library.json`. When the user asks for a surface we don't have, do
      this in the chat rather than say no.
    - Five samples in `skins/`: TSC_Race (white, red stripe, 27), TSC_Tricolore (Italian
      flag, gold wheels), TSC_Nebula (candy fade, splatter, glow), TSC_Camo (matte urban
      camo), TSC_RatRod (rust and chips from photos), plus TSC_Dots (the wrapping test).
      TSC_Race is installed in the game. The user liked them (2026-09-24, "quite impressed"),
      and spotted the sunk splashes on the Nebula, since fixed. The three dot versions
      (TSC_Dots, TSC_Dots_Scatter, TSC_Dots_Grid) stay in the gallery for reference.
    - **The materials page (user, 2026-09-24):** `PY -m tool.swatches` paints every finish
      onto a 30 cm ball with the same code as the car, pictures it through
      `viewer/swatch.html` with the car's lighting, and `viewer/materials.html` shows them
      all by family with their names, so the user can point at what they mean. Swatches are
      rebuilt when the finish code changes (a hash of the source), and added photo surfaces
      appear by themselves.
    - **Not yet seen in the game:** the richer finishes (candy, chrome rims, rust, leather,
      metallic flake at 1 mm). Test one or two of the samples in the game when convenient.
    - `shapes.seams(width, kinds=("border", "open"), crease=60)` (2026-09-24): a line along the
      body panels' seams, found on the mesh (part borders, free edges, optionally folds), for
      tape and pinstriping. First used by TSC_Seams_Black and TSC_Seams_White.
    - **Seam texels (2026-09-24):** `coverage.get()` adds the parts' coverage (clipped to 1).
      It used to take the largest, so where two parts meet each covered half the seam texel
      and "body" paint landed at half strength there, with the stock glossy grey showing
      through as a dotted line along every panel seam. Skins painted before this need
      `tool.skin show` again before they're reinstalled.
    - Pictures placed on the car: `Skin.decal(image, spot, width)` (tested with a drawn
      badge on the bonnet and both sides). Not built yet, by choice: tyre lettering (reads
      backwards on one side, see "Things we learned"); relief on the inner car.

### [x] 6. The picture maker

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
  - **Done 2026-09-24 (Fable 5.1).** The user looked closely at the samples, sent the placement
    code back twice (below), asked for a candy car with donuts (TSC_Donuts, installed) and
    said: "for these kind of randomness graphics it works pretty well." Still open, for the
    design work ahead: ordered layouts across panels (a regular grid of dots or motifs that
    should line up from panel to panel). `looks.surface_points(regular=True)` gives a
    lattice-like spread, so `Skin.scatter` could take a `regular` switch; the lined-up
    unfolding covers continuous prints. `tool/pictures.py`:
    - **The model: FLUX.2 [klein] 4B** (Black Forest Labs, January 2026, Apache 2.0, not
      gated), through diffusers 0.40.0. Chosen over Z-Image-Turbo (Apache 2.0 too, but a 33 GB
      download, fp32 weights, and photo-leaning) and Qwen-Image (20B, needs quantising); the
      newer Qwen-Image-2.1 and FLUX.2 [klein] 9B are non-commercial. 16 GB of weights in
      `%LOCALAPPDATA%\TrackmaniaSkinChallenge\models` (`HF_HOME`), 4 steps, about 3 s per
      1024² picture; a decal with its cut-out about 20 s, a tile about 8 s.
    - **Memory:** the text encoder (Qwen3 4B, 8 GB) and the transformer (8 GB) don't fit the
      card together, and the PC's 16 GB of RAM (7 GB free) can't hold either as a fallback.
      So they're loaded straight onto the card one after the other (`device_map="cuda"`
      with the other half passed as None): all prompts are encoded, the encoder dropped, then
      the pictures made. About 8 s per load.
    - **PyTorch 2.14.0+cu130:** the cu128 index stops at 2.11 and has no Python 3.14 wheels;
      the CUDA 13 build has them and covers Blackwell (sm_120). Driver 610.88 is fine.
    - **Decals:** asked for on a plain white background in a style (sticker with a white
      border by default; also flat, print, painted, line art, retro, photo), cut out with
      BiRefNet (MIT) through rembg 2.0.85 on the processor (ONNX; 1 GB model in
      `models/rembg`), cropped to the subject. Kept PNGs carry their prompt and seed.
    - **Tiles** are drawn on a torus: after every denoising step the latents are rolled by a
      random amount, so every edge is an interior for most steps; the picture is decoded from
      a 2×2 repeat and the middle cut out. Seam score (edge jump / inner jump) about 1.0, i.e.
      no join. (First try was rolling the finished picture and re-drawing the cross with the
      rest pinned; it left half-objects and hard cuts at the band's edges.)
    - **The user's review (2026-09-24), which reshaped the placement code.** They looked
      closely and found the tiger cut by neighbouring panels and the bonnet's cockpit surround,
      and the banana print cut at every panel and mushy. Fixes:
      - `paint.project_near()`: a decal lands on the nearest surface along its facing (a depth
        test per 1.5 cm cell), so it crosses every panel in its footprint and never reaches
        the far side; the old panel list is gone. It also measures how much of the picture
        landed and how far from flat the surface is (`step_cm`); `Skin.decal` notes both, so
        a picture across a fold is flagged before anyone looks.
      - The front flank has a deep fold (the lower flank sits back under an overhanging lip):
        no place for a big sticker. Flat spots on a side: the rear flank behind the sidepod
        (34 cm) and a thin strip along the top of the front flank (lettering, `at=(±35, 62,
        60)`). The bonnet spot moved to z 117 (the free bonnet is z 91..142; the cockpit
        surround takes it up to 91).
      - **Prints as one sheet:** the unfolding's islands are now lined up across their seams
        (`uvmap._offsets`: least squares over shared mesh corners; median mismatch 3.9 cm on
        the Skin set, but some seams can't line up because the two sides are mirror images).
        A projection per facing (`wrap="facing"`) was tried and rejected: it smears the print
        wherever the surface turns. The unfolding bends a print over the shoulder with no
        stretch.
      - **Prints as objects (the user's idea): `Skin.scatter()`.** Copies of a cut-out are
        spread evenly over the surface (Poisson-disc points), each laid flat on its panel as
        its own sticker, whole: one that would cross a fold or run off an edge is nudged and
        shrunk a little, and left out if it still doesn't fit. The tool says how many were
        placed and left out (359 and 27 on TSC_Bananas, 13 s). This is the way for any print
        made of separate things, and could replace the dots' distance drawing too.
    - Samples: **TSC_Tiger** (a tiger sticker on each rear flank and the bonnet, matte
      black, orange trim; installed in the game), **TSC_Bananas** (scattered banana
      stickers) and **TSC_Bananas_Print** (the same as one continuous seamless tile, for
      comparison).
    - The user's taste (2026-09-24, mid-build): illustrations, prints and decals rather than
      photographs. The styles and the defaults follow that.

### [x] 7. Your first skin, start to finish

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
  - **Done 2026-09-24 (Fable 5.1), the first round.** The user asked for "an ice cream truck
    theme". Two takes were shown (TSC_IceCreamTruck, the truck itself; TSC_IceCreamSweet, a
    mint body sprinkled with cones, lollies and three-scoop cones). The user chose the sweet
    one, then three rounds of change, each from the game's skin editor close up: an even
    sprinkle (no clusters of one picture, no bare patches), stickers not pixelated (filtered
    sampling and a better BC1 encoder), stripe edges sharp (the shape feather 1.5 cm → 0.2 cm).
    Then: "Sure... if you are confident." Installed and accepted. What the user said and each
    change: `skins/TSC_IceCreamSweet/notes.md`; pictures of every round in `versions/`.
    - The promise "yes reaches the game in under 30 seconds" became 51 s with the new BC1
      encoder. The user's call (2026-09-24): "if the compressions are better then so be it...
      for me quality goes first." So the encoder got a local endpoint search too (+2 dB; a build is now
      about 2 minutes). Don't trade quality for build time.
    - The user watches sharpness closely and checks it in the game's skin editor at close
      range: keep every edge, sticker and letter at the texel grain.
  - [x] **The comparison round:** one skin made on Opus 5.5, in a fresh chat with that model
    picked at the top. Then the user says which model they prefer for everyday use, and
    checkpoint 8's skill recommends it. **Done 2026-09-25: Opus 5.5 for everyday use.** The
    user: "in Opus 5.5 the skin looks pretty cool. I'm impressed. Could have looked for other
    minor details, but I'm very happy with initial results. I can then tweak."
    - **Made 2026-09-24/25 on Opus 5.5:** the user asked for their CMYK car with "the skin
      peeling off" to reveal CMYK. Two takes (TSC_CMYK_Peel, TSC_CMYK_Peel_More), four rounds
      of change (see their notes.md); the user chose TSC_CMYK_Peel_More and it's installed.
      The user's verdict is above. The "minor details" were things like the sidepod frame
      still wearing the old colour run, which the user had to spot: before showing a skin
      built on an earlier one, go over every visible part's inherited paint.
    - New in the paint box: `Skin.keep()` and `Skin.peel()` (tool/peel.py), a top layer torn
      open to show a kept layer underneath.

### [x] 8. Tidy up for everyday use

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
  - The skill recommends Opus 5.5 for the everyday loop: it won checkpoint 7's comparison
    (2026-09-25). Fable 5.1 stays the step-up when a design stalls.
  - **Where it stands (2026-09-25, on Opus 5.5; the user said "go ahead" without switching to
    Sonnet 5).** Checked against the current docs (code.claude.com/docs/en/skills and
    /memory): a project skill is `.claude/skills/<name>/SKILL.md`; its description decides when
    it loads (1,536 characters with `when_to_use`); once loaded it stays in the chat, and after
    the chat is summarised the first 5,000 tokens are put back. So the skill is kept to about
    2,500 tokens, and survives whole. CLAUDE.md: under 200 lines; path-scoped rules load only
    when Claude reads matching files. `model:` in a skill only lasts one turn, so the skill
    tells the user to pick Opus 5.5 with `/model` instead.
    - `.claude/skills/skin/SKILL.md` (new): the routine, the commands, the design rules the
      user taught us, the checks before showing, the record in `notes.md`, installing.
    - `CLAUDE.md`: 84 lines instead of 130 plus the imported brief. The `@BRIEF.md` import is
      replaced by the brief's four measures of success and the user's role. The build-phase
      commands, the source assets and the texture format moved to `.claude/rules/tool.md`,
      which loads with `tool/`, `viewer/`, `official/` and `car/` files.
    - Two routines that the last skins wrote by hand each round are now commands in
      `tool/snap.py`: `--close` (nine close looks at the joins, folds, wheel and the driving
      camera) and `--picture` (the takes side by side with close-ups, opened on the user's
      screen).
    - **The improvement list (the user's question, 2026-09-25):** `IMPROVEMENTS.md` is the
      queue of things the tool should do better. It started with the open items scattered in
      this file (ordered layouts, tyre lettering, inner relief, guessed part names, and what's
      still to check in the game). The skill reads it at the start of each skin. It fixes only
      what the skin needs, adds the rest to the list, and works on the list when the user asks.
    - **Out of step, fixed 2026-09-25:** this work sat on the Windows PC unpushed while the Mac
      carried on from the old `CLAUDE.md` and made the viewer's new look and the lights work
      checkpoints 8 and 9. They're improvements now (below). A SessionStart hook in
      `.claude/settings.json` pulls at the start of each session, and `CLAUDE.md` says to push
      after each piece of work.
    - **Ticked 2026-09-25 by the user** ("I think we did the brand new skin, Opus 5.5 worked
      pretty well"). The routine, on Opus 5.5, carried TSC_CMYK_Peel_More through six rounds
      (lights in its colours, the orange end, three wheel takes, the tyre line, the wobble fix
      from the game) and three installs. The skin itself was designed in checkpoint 7's round,
      before the routine was written down; the user counted the work as the test.

## Improvements after the build

Changes the user asked for once the tool worked (the user, 2026-09-25: "I'm always going
to be queuing improvements"). They are never new checkpoints: each one is queued in
`IMPROVEMENTS.md`, and its working notes go here, newest last. When one is done, its line
leaves `IMPROVEMENTS.md` and its notes stay here as the record.

### The viewer's new look (done 2026-09-25)

- **What it's for:** a viewer that feels like part of the racing world, with better ways to
  look at a skin. You asked for it on 2026-09-25 and picked the "race garage" look out of three
  mockups.
- **What you'll see:** the viewer with your skins listed down the left. Click one and the car
  changes paint while the camera stays put, so two skins compare at the same angle.
  - The skin's name in big slanted letters, marked when it's in the game.
  - Along the bottom: front, rear, left, right, top, and a driving view like the game's chase
    camera; a slow spin; and Save picture, which saves the car in the studio as a picture.
  - Top right: day and night, show or hide the body, details, wheels and glass, and the parts
    list.
  - The page of all skins and the materials page wear the same lettering.

  The driving view is matched to your screenshot of the game's Cam 1.
- **Model:** Opus 5.5, the everyday model. Building a page to a chosen design is
  straightforward; matching the chase camera takes judgment.
- **Notes for Claude:**
  - The mockups: https://claude.ai/artifact/EErF9X9RmvMU8KZKcRu1w5 (A showroom, B race garage,
    C just the car). The user chose B.
  - `viewer/index.html` holds the layout and CSS. Teko (SIL OFL) is in `viewer/lib/fonts/`: the
    google/fonts file `tool/fonts.py` pins (sha256 d1321889…), renamed `Teko-Variable.ttf`.
    Icons are Lucide 1.48.0 (ISC), inline.
  - `viewer/viewer.js`:
    - `loadSkin()` switches a skin in place. Textures are cached by slot and URL and freed when
      the new skin doesn't use them (each is up to 4096²).
    - The list reads `data/gallery.json`, which now carries a `title` ("CMYK Peel More").
    - `VIEWS.cam1` (was `driving`) is the game's Cam 1, fitted to the user's 1920x1080
      screenshot (the car's box within 5 px): the camera 3.75 m up and 6.3 m behind the centre, tilted down 13.5°,
      fov 58.7° (the game's 90° wide at 16:9). `roomy` moves a view back on the page only.
      Later the same day the user found the car too small and low in that framing: the view
      keeps the game's lens (the user wanted it kept, not a narrower one) but aims at the car
      from 5.2 m instead of 7.3 m, and from 18° above it instead of 27°, so the speed digits
      read clearly, as the user remembers them in the game. The game's exact framing is in the
      comment on `VIEWS.cam1`.
    - Views glide round the car (spherical interpolation), never through it. Spin is
      OrbitControls' autoRotate. Save picture renders at pixel ratio 2 with the plain framing
      and no buttons.
  - The page frames the car beside the list with `camera.setViewOffset` (5 % up, zoom 0.92).
    `?snap=1` keeps the old framing: pixel-identical on 2026-09-25, so thumbnails and check
    sheets don't change. `window.viewer.show/showParts` are unchanged.
  - Under 900 px wide the list folds behind a button.
  - Newest first, on every computer: `tool/gallery.py` orders skins by the commit that added
    each design.py (a fresh clone gives every file the same time); a skin not committed yet
    goes by its design.py's time, above the rest. Ties within a commit go by name. The Mac's
    Docker image has git for this. The gallery shows the date in the viewing computer's clock.
  - Checked on the Mac with headless Chrome on 2026-09-25: every view, switching skins, night,
    the menus, Save picture, three window widths. The Windows `tool.snap` run matched too
    (Things we learned, 2026-09-25).
  - The user also sent the game's Cam 3 (a camera above the cockpit, looking over the nose).
    A first fit was close but not right, and the user said it isn't needed. Cam 2 wasn't sent.
    Later the user asked for a choice of cameras after all (Decisions, "The game's cameras").
  - **Done 2026-09-25.** The user: "you've done an amazing job with the ui", and asked for the
    list newest first (done).
  - **The game's number (added 2026-09-25, the user's idea).** Show → Number lays the initials
    and number the game writes on the engine cover (no skin can hide them) over the car as a
    layer of the viewer's own, never in the skin files. The initials go on "number panel" (the
    narrow one behind the cockpit), the number on "engine cover panel", both reading from
    behind, as in the user's Cam 1 screenshot ("DEC 01"). "CAR 01" by default (the user's
    choice); `?initials=DEC&number=07` tries others.
    - `addPlate` in `viewer/viewer.js` draws it in the body's shader, projected flat onto each
      panel (both are near-flat), in Russo One (in `viewer/lib/fonts`, the file `tool/fonts.py`
      pins), off-white, matte, not metal.
    - It's on by default and each browser remembers the choice. Snapshots leave it off (still
      identical to before, within 1/255).
    - The lettering is a guess until the user sends a close-up of the engine cover from the
      game. The user says the game's is "bold but not too bold" and likes Russo One, so the
      viewer thins its strokes a little (`PLATE_THIN` 0.02 of the letters' size, their pick
      out of four, 2026-09-25).

### Your own colours for the speed numbers, brake lights and car number (done 2026-09-25)

- **What it's for:** finding out what a skin can colour beyond its paint, then making the tool
  do it, so that when you design a skin you can simply say the colours. Three things:
  1. the speed numbers on the back of the car (white by default);
  2. the brake lights, when the car brakes;
  3. the initials and number on the engine cover ("CAR 01").

  You asked for it on 2026-09-25. You remember a skin with custom-coloured brakes and speed
  numbers, and weren't sure the tool could do it. Research comes first, because some of it
  may not be possible. The answer for each is yes or no, and why.
- **What you'll see:**
  - A short answer for each of the three: possible or not, and how it looks in the game,
    settled by a test skin you drive and brake with, by day and at night, with screenshots.
  - For each that's possible: you say it in words when designing ("green speed numbers, blue
    brake lights"), and the skin in your game has it.
  - In the viewer: the rear display showing a speed, like 218, instead of 888, in the skin's
    colour; a way to see the brake lights on; and the car number in its colour, if that can
    change.
- **Model:** Opus 5.5. The research and reading the game's behaviour from your screenshots take
  care.
- **Notes for Claude:**
  - **Start with research:** Nadeo's pages (links in `official/SOURCES.md`), community skin
    guides, and skins that do this. Then the in-game test. Don't take the game's files apart
    (Decisions). The tool may already be able to do some of it: `Skin.glow(where, colour,
    kind)` in `tool/paintbox.py` writes `Details_I` on any named inner part, so
    `s.glow("digit display", "green", "always on")` might already colour the speed numbers.
  - Nadeo's 2020 post says a skin can't change the digits' colour (the `skin` skill), but the
    user remembers a skin that did. Measured 2026-09-25 on the stock `Details_I` (2048²): the
    "digit display" part (`tool/naming.py`, 11,043 texels) is glow code 96 ("always on", which
    keeps its painted colour in the game: magenta in the lab), RGB ~227 white, with every
    segment lit (888). The game presumably masks the segments to show the speed. So painting
    that part's `Details_I` RGB may colour the digits: a test skin settles it.
  - Brake lights: code 0 keeps its RGB (`GLOWS` in `tool/finishes.py`). The stock strips
    behind the front wheels are reddish and flare to near white when braking. The lab's code-0
    part was hidden from every camera, so test a colour on those strips. Brake heat (64) has
    never been seen lit; "brakes" may also mean painted calipers, which already work. Find
    which named part holds the stock code-0 strips, so "brake lights" works as a place in a
    phrase.
  - Initials and number: the game draws them, and a skin can't change the player number or ID
    (the `skin` skill). Whether their colour follows anything in the skin (the panels' paint, a
    glow code, nothing) is unknown: research, then test (for example, paint the two panels a
    strong colour and see what the lettering does). The viewer draws them in `addPlate`,
    off-white, a guess.
  - Viewer: light only the segments of a chosen speed (`?speed=218`, default 218). Find each
    digit's seven segments from the lit texels' 3D positions, and mask the rest in the Details
    shader, the way `addPlate` does the number. A "Brake" button could show code 0 at full
    brightness (its `GLOW` gain).
  - Afterwards, record what's possible under "Things we learned", update the `skin` skill's line on
    what a skin can't change, and give the paint box the words ("speed numbers", "brake
    lights").
  - **Progress 2026-09-25 (Opus 5.5, on the Mac): research done, the test skin is ready.**
    **Next:** on the Windows PC, `tool.skin show TSC_Lights_Test` then `install`, and the user's
    in-game test (`skins/TSC_Lights_Test/notes.md` has the colour key and what to try; `key.png`
    is the viewer's picture to compare with). Then the words, the notes and the skill's line above.
    **Queued, the user will do it later (2026-09-25):** a short video from behind while pulling
    away from a standstill, for the rear lights' gear display (fill-up or one at a time, the
    centre piece).
    **Queued too: the rear wing flap in the viewer.** The user (2026-09-25): under full throttle
    from a standstill the wing at the back starts to open at 1.5 s (about 75 km/h) and is fully
    open at 2.5 s (about 115 km/h); checkpoint 4 saw it show red underneath. Likely the rear
    deck behind the engine cover ("tail panel", z -161.8..-130.7, top at y 65.5) hinged at its
    front edge, uncovering the rear lights; but the "tail corner" pieces reach forward to z
    -122.6 and would cut into the body if they swung with it, so which pieces lift, the hinge
    and the angle wait for the user's screenshot from the side with the wing fully open, and
    when it closes (off the throttle, braking, or below a speed). Then: rotate those parts'
    vertices about the hinge in the vertex shader (as `addDisplays` does per part), driven by
    `stepDrive`.
    - **Research** (web; Reddit threads read through an archive):
      - Speed digits: very likely yes. On r/TrackMania (2021-2024) players colour them with the
        `Details_I` RGB on the digits at alpha exactly 96. The game still lights only the
        segments it needs; a wrong alpha (120) broke that. One comment says the game tints the
        digits for effects (blue on cruise control, yellow on the yellow booster). Nadeo's
        "digits color" reads "(… digits color : rear lights and glass gears)", so it may mean
        the canopy's gear display. Threads: reddit.com/r/TrackMania/comments/uuwnkw,
        /vsnzy3, /1fyh2ef, /n0nwri.
      - Brake lights: yes, code 0 lights when braking anywhere on `Details_I` (xrayjay's table,
        which Nadeo credits: web.archive.org/web/20230427111112/https://i.imgur.com/shkhz5i.jpg).
        One report: orange brake lights lit "orange then red" (reddit …/o1wr5k).
      - Initials and number: no. Nadeo's changelog of 2021-03-18
        (blog.trackmania.com/2021/03/18/update-club-items-are-available) says the game mode sets
        their colour: white in a normal race, orange in warm-up, the team's colour in team
        modes, red in danger. The player sets the three letters in Settings > Profile >
        Trigram; the mode sets the number. The DossardPlus plugin changes them only on your own
        screen.
    - **Measured on the stock files:**
      - The brake lights are Details pieces 461 and 462 (and their twins): the slotted crescent
        inside each front wheel, 19 cm behind the axle. Front wheels only; left and right share
        texels. Now the part "brake light" (parent "wheel", in "wheels").
      - The rear lights are pieces 241 (a bar each side) and 231 (a small centre piece), white
        code 96 in the file, behind the "rear light lens" glass (stock `Glass_T` white). Now the
        part "rear light". The lenses have their own texels per side (0 % shared).
      - The speed display: three digits of seven segments. Each segment is a bar of three
        pieces (its face and two bevels, split at the model's creases); the backing between
        the bars is six more pieces. All 21 bars share one patch of texels, so the digits
        take one colour, never one per digit or segment. The backing is dark: painting the
        whole part would light it up, so `Skin.relight(where, colour)` recolours the stock
        glow instead (each texel keeps its code and brightness).
      - Piece 139 (a bevel of the right digit's bottom bar) had no mirror match and fell to
        "rear diffuser"; it's named "digit display" now. TSC_Stealth_CMYK_Bold, which paints the
        diffuser yellow, had painted that face yellow; it no longer does.
    - The test skin also carries the four driving glows (the user: "all those states you can
      customise, so we might need to do some tests"): brake heat orange on the rims, exhaust
      heat yellow on the side vents, turbo on the sidepod frames and boost on the rear strakes
      (grey: the game's colours), each part painted dark so a colour there is the glow.
    - `TSC_IceCreamSweet`, `TSC_IceCreamTruck` and `TSC_Stealth_CMYK` painted "hub" or "rear
      bumper", which lost the new parts; they now list them too (their textures checked
      identical).
    - `car/parts.json`: the Mac recomputed every part's texels and shared share with the
      current masks. The Windows cache (`parts_stats.json`) held figures from before the
      coverage fix, so every `view.prepare` there rewrote `car/parts.json` slightly wrong;
      rebuilt from scratch on 2026-09-25 (28 s), it now matches the Mac's. If the file shows
      up changed again, delete that cache and run `tool.parts`.
    - **Viewer:** the speed display shows `?speed=` (180 by default) instead of 888, lighting
      whole bars: `tool/view.py` `digit_segments` tags each bar's corners with its digit and
      segment in `car.bin`, and `addDigits` reads that. (A first try picked segments by position
      on the digit and cut across the bars; the user spotted it.) Show → Braking flares the brake lights (code-0 gain
      8 by day, 10 at night: a guess until the game's screenshots). The rear lights still show
      the file's colours; if the game keeps them red, the viewer should draw them red.
    - **The pad under the car (the user's idea, 2026-09-25):** hold Accelerate or Brake (or
      ↑/W, ↓/S) and the speed on the digits climbs or falls, with the brake lights flaring
      while braking (`stepDrive` in `viewer/viewer.js`; snapshots keep `?speed=`). First tuned
      to the user's timings (gear 2 at 2 s, … gear 5 at 10.76 s, on to 350; letting go 3 km/h a
      second; a stopped car's display dark); now to the straight-line video (below), which
      corrected all three. Brake still stops the car in half a second (not in the video).
    - **Turbo on the pad, provisional:** from 100 km/h the turbo-colour areas (code 160: the
      wheel rings and hubs, the front wing's lower edges) glow in the game's green, and the pad
      shows "Turbo". The user thinks turbo comes on at 100 (2026-09-25), and checkpoint 1 saw
      those areas green while driving and dark at rest. The documented trigger is "turbo
      input" (below), so the lights test is to settle it. Snapshots keep it off. Once the game's screenshots show what turbo, boost
      and the other glows do, they join the pad as states. **Taken out 2026-09-25:** the lights
      test's videos show nothing green up to 357 km/h on a straight without pads.
    - **The rear lights are a gear display** (the user, from the game, 2026-09-25): standing
      still only the far left and right ends light, each gear lights the next band (five
      gears), braking lights it all red. Each side's bar has five bands, split by dark lines in
      its texture (v 0.4747, 0.4903, 0.5030, 0.5157 of its UV strip; the corner end is band 1).
      First drawn in red at the Reddit tip's gear speeds (100, 160, 235, 340); the video
      (below) settled the rest.
    - **The user's straight-line video (2026-09-25):** `straight-line-test.mp4` (repo root,
      Windows PC only, git-ignored), driven with TSC_Parts (stock `Details_I`), Cam 1 from
      behind, 2560x1440 at 30 fps, 29 s: full throttle from the start on a flat straight to
      372 km/h at 12 s, then let go (no brake) and rolled to a stop at 23.7 s. The user's
      overlay shows the speed, gear, revs and pedals; read frame by frame (PyAV 18.1.0 in a
      scratch folder, not a project dependency; race time = video time − 0.67 s, checked
      against the race clock).
      - **Pace:** 101 km/h at 1.80 s, 162 at 3.64, 236 at 6.22, 342 at 10.70, 372 at 12.02.
        Nearly steady between: 56 km/h a second in gear 1, 37 in gear 2, 40 from 162 to 200,
        then 25 (a clear kink at 200, mid gear 3). The speed holds 0.15-0.3 s at each change up.
        The viewer's `PACE`, `SHIFT_PAUSE` 0.2 s; its pad matched the video within 1-3 km/h
        live. Past 372 the video stops (the top speed on the flat wasn't found online), so the
        last pace goes on, a guess.
      - **Gears:** up at 101, 162, 236 and 342 km/h; down while coasting at 279, 200, 142 and 90
        (`GEAR_UP`, `GEAR_DOWN`).
      - **Letting go:** the car loses 3.5 km/h a second plus 0.3 of its speed (`coast`): 371 to 0
        in 11.6 s, within 2 km/h of the video throughout.
      - **Digits:** always three, leading zeros lit ("075", "008"), "000" when stopped, both at
        the start and after rolling to a stop. (Unlit segments look dark in shade and beige in
        sunshine, so read them in the shade.)
      - **Rear lights:** the bands fill up from the corner, one per gear, down again with the
        gear (gear 1, standing still included, lights the corner only). Lit, they're the file's
        colour (the stock white, pale cyan through the lens); unlit they look like the lens
        glass. The car held at the start lights both bars whole and the centre piece red, as
        braking does; the centre piece is dark otherwise. The viewer now draws the bands in the
        file's colour, and braking in red with a red-tinted surface (a pure red, gain 4-4.5:
        stronger washed out to orange).
      - **The user's night screenshots of a pink-lit skin** (Steam, 12:28 throttle at 189 in
        gear 3, 12:33 braking at 147): the digits and the lit bands glow in the skin's pink, so a
        skin can colour both. Braking turns both bars fully red whatever their colour; the
        digits stay pink. Thin strips under the bars glow red to purple and flare white when
        braking (that skin's code 0, probably); the front wheels' brake lights glow pink and
        flare. The user didn't brake in the first one.
      - **The rear wings:** under full throttle they start to open at ~60 km/h (1.1 s) and are
        fully open by ~95 km/h (1.7 s). They stay open while coasting and close from ~43 to
        ~34 km/h (about 0.7 s), the sides first. Braking (the 12:33 screenshot) the top one
        looks steeper, and the user saw other pieces move when braking: not modelled yet.
      - **How they move (the user, 2026-09-25, correcting a first try with hinged flaps that
        tipped):** there are two, top and bottom. Neither tilts. The top wing (the tail panel
        between the two tail corners) lifts straight up, then the corners slide apart from the
        panel; the bottom wing (the diffuser and undertray between the diffuser strakes) drops
        straight down, then its sides slide apart. The blocks under each ("rear bumper",
        "rear bumper corner", white and purple in TSC_Parts) move out but not apart, so they
        show in the gaps: the white slivers and purple strips of the video. The top's
        "rear bumper" pieces also hold plates inside the tail corners' ends (|x| > 44 cm),
        which slide with the corners.
      - **The timeline** (frames 46-166 and 540-620; the user timed "2.70" for the full opening
        and confirmed it starts at 60): from 60 km/h (1.1 s on the race clock) out in 0.4 s, a
        0.4 s pause, apart in 0.75 s, fully open at 2.67 s (frame 100). Closing below 43, the
        sides come together in about 0.6 s, then the wings go back in within about 0.25 s. A
        first version opened in 0.6 s in all; the user found it too quick.
      - **In the viewer** (`WINGS`, `WING`, `addWing`, `stepWing`): Up 6 cm and apart 3.5 cm on
        top, down 8 cm and apart 3 cm below: set by eye against frames #580 (open) and #600
        (shut), where the camera hardly moves, and #460 (gaps about a tenth of the panel's
        width). The parts move in the vertex shader, the shadow too (`customDepthMaterial`).
        Snapshots keep them shut (identical to before); `?wing=1` opens them there, and
        `?wingLift=`, `?wingSpread=`, `?flapDrop=`, `?flapSpread=` (cm) try other distances. A
        side video would pin the distances.
      - **The air brakes (the user, 2026-09-25):** braking, the two rear quarter panels tip up at
        the front and the nose panel tips up at the back, "rather quick", each pushed by arms
        inside it. In the model the arms are "rear damper" (a telescopic arm in each quarter
        panel's opening) and "nose sensor" (two rods under the nose, and a crossbar at the
        panel); the openings are "airbox" and "nose plate" left/right; "nose plate" centre is the
        nose panel's underside. Names from checkpoint 3, before we knew (`IMPROVEMENTS.md`).
      - **In the viewer** (`AIRBRAKES`, `setupAirbrakes`, `showAirbrakes`): each panel turns about
        the edge that stays, along a hinge line in its own plane (from the mesh at load: its mean
        normal and the middle of its front- or rearmost corners), taking its underside and
        crossbar along; each arm swings about its lower end and stretches so its tip stays on
        the panel (its ends by power iteration on its corners). 20° for the quarter panels,
        after the user's braking screenshot (12:33: dark openings either side of the engine
        cover; 35° stood too tall); 30° for the nose, a guess (from Cam 1 it hides behind the
        cockpit at any angle). Up in 0.15 s, down in 0.2 s, while the pad's Brake or Show →
        Braking is on. Snapshots keep them down; `?airbrake=1`, `?quarterAngle=`, `?noseAngle=`.
        A first render showed a thin line above the car: the far quarter panel, edge-on.
      - **The canopy's rear:** its (magenta, in TSC_Parts) lines don't change with the gear
        from behind. The glass gear display wasn't visible from Cam 1.
      - **Turbo:** nothing turned green from behind; no turbo pads on this straight.
    - **What triggers the other glows** (research, 2026-09-25; the only source is xrayjay's
      table, "TM2020 Illum Alpha Tones", which Nadeo links): 160 turbo colour "is colored under
      turbo input" (the turbo pads), 192 exhaust heat "ON when Turbo is enabled", 224 boost "is
      colored under boost input" (most likely reactor boost, 6 s), 64 brake heat "ON when
      braking hard (ex: disc brake heating)", 32 energy the team colour. Nothing ties any of
      them to speed or throttle, and nothing documents their colours or fades. The user asked
      for these as pad states (2026-09-25): add Turbo, Super turbo, Reactor and a hard stop
      once the game's screenshots show them (the test notes ask for them), not before.
    - **Installed on the Windows PC (2026-09-25, Opus 5.5).** `show` then `install`. The first
      zip was 9.28 MB: `Details_R` alone was 5.74 MB, because a design that paints only a few
      inner parts ships the stock roughness (2048², grainy) upscaled to 4096², which barely
      compresses. `build_zip` now halves the roughness maps, largest first, when a zip is over
      `ZIP_BUDGET` (see Things we learned); this one came out 5.46 MB, `Details_R` at 2048².
    - **The user's two videos (2026-09-25):** `light-test-day.mp4` (17.5 s) and
      `light-test-night.mp4` (14.5 s), repo root, Windows PC only, git-ignored. Cam 1, 2560x1440
      at 30 fps: full throttle on a flat straight to 357 (day) or 314 km/h (night), then hard
      braking to a stop (the day one ends in a spin). No pads, no boost. Read frame by frame
      (PyAV 18.1.0 in a scratch folder; the user's overlay shows the pedals).
      - **Speed digits:** green by day and night, only the lit segments (the unlit ones dark,
        faintly visible by day), green while braking too. Yes.
      - **Rear lights:** the right bar glows magenta, the left (behind the cyan-tinted lens)
        blue: magenta through cyan. So both the glow colour and the lens tint work. They fill
        up band by band with the gear, in that colour. Braking turns the bars and the centre
        piece red, whatever the colour, the instant the pedal goes down and off the instant
        it's released; behind the cyan lens that red looked dark by night and teal by day (the
        tint filters it). Yes, with that catch.
      - **Brake lights (the slots inside the front wheels):** dim blue at rest (seen at night),
        flaring blue to near white while braking, back to dim at once. No red showed through.
        Yes.
      - **Initials and number:** white on the yellow and on the blue panel, day and night. The
        game mode sets them, as researched. No.
      - **Brake heat (code 64), seen for the first time:** the rims (all four) glow faint red
        within a moment of braking hard, red-orange at 1 s, the painted orange by 1.5 s, and
        fade out over about 1 s after letting go. The viewer's pad now does this
        (`BRAKE_HEAT`: the glow goes with the square of the heat).
      - **Braking pace:** read off the digits, about 180 km/h a second from 290 to 145 and 145
        from 185 to 85; from 357 or 314 the car stopped in 2 to 2.5 s. The pad's Brake is now
        93 + 0.4 of the speed a second (`BRAKE`), not the old 700.
      - **Turbo, exhaust heat, boost:** not triggered (no pads). The provisional turbo from 100
        km/h is out of the viewer. They stay on the improvement list's game checks.
      - Also seen: the air brakes (quarter panels and nose panel) up only while braking; Cam 1
        closing in as the car slows (for the cameras item); the engine cover's lettering close
        up (day 13.2 s, night 10.8 s: for the lettering item).
    - **The words:** `LIGHT_WORDS` in `tool/paintbox.py`: `s.relight("speed numbers" | "brake
      lights" | "rear lights", colour)`, and `glass()` or a paint on "rear light lens" tints a
      lens. `relight`'s docstring says what the game does with each.
    - Found on the way: `view.export_skin` deleted the gallery's `thumb.png` when a skin was
      re-exported (a lone `tool.snap` run), so the viewer's list lost that skin's picture until
      the next gallery refresh. It keeps it now.

### Your skins online, for your phone and friends (done 2026-09-25)

- **What it's for:** the user (2026-09-25): "would like to show the skins on my phone and
  friends". They had switched on GitHub Pages for the repo.
- **What you'll see:** https://fedecarbo.github.io/tm-skin-creator/ opens the 3D viewer on the
  newest skin; "My skins" lists the rest, "All skins" is the picture grid. Only the skins in
  the game (the user's pick, 2026-09-25), no test cars. A skin goes on when it's installed.
- **Notes for Claude:**
  - `PY -m tool.publish` builds the page in the work folder's `site/` (its own git repo) and
    force-pushes it as the single commit of `gh-pages`, so GitHub never keeps old textures and
    the OneDrive repo never holds them. `--here` serves it on this computer. Its docstring is
    the key. GitHub Pages must serve the `gh-pages` branch, root (Settings, Pages).
  - Clones leave `gh-pages` out of their fetches: the SessionStart hook sets the negative
    refspec `remote.origin.fetch ^refs/heads/gh-pages` (git 2.29 or later) on each computer.
  - Lighter for phones: at most 2048², JPEG at quality 90 with full-res colour (4:4:4) for
    colour, roughness, normals and glow; PNG for the glow codes, the glass tint, AO and the
    shared texels. Six skins: 36 MB, of which a first visit loads about 20 MB.
  - The workbench (parts list, part names on click, Copy camera, materials) is hidden by
    `viewer/public.css`, which only the published copy links. The published `index.html` opens
    the newest skin when the link names none.
  - On a phone: the `max-width: 600px` block in `viewer/index.html` (icons alone at the top, two
    rows of buttons at the bottom, the pedals above them, no gear) and `frame()` in
    `viewer/viewer.js`, which draws the car smaller in a window taller than 1.3 : 1 (16 : 9 for
    the Driving cameras) so it fits across.
  - Checked in headless Edge as an iPhone (390×844 at 3×, touch) and at 1440×900: no page errors,
    nothing overlapping. Next: the user on a real phone.

### The inner car finished: relief, the lights, the turbo (done 2026-09-25)

- **What it's for:** the user (2026-09-25), driving TSC_CMYK_Peel_More: "we could do some
  internal for future tool functionality and to keep on the great work on the skin", then
  "doesnt matter if its visible or not front or back, what matters is the quality of the
  entire car". Two list items went with it: raised detail on the inner car, and a Turbo button.
- **What you'll see:** raised detail inside the car (a quilted seat, marks on the tail), every
  light in a skin's own colours, and a Turbo button on the viewer's pad (or T).
- **Notes for Claude:**
  - `tool/relief.py` (its docstring is the key) and `Skin.relief` / `Skin.emboss`: heights in
    3D, turned into the normal map by their slope along each triangle's own texture directions,
    measured a fraction of a millimetre either way in 3D, so seams, folds and mirrored twins
    need nothing special. Patterns: ribs, studs, quilted, hex, rivets (at points or along a
    line; along a part's open edges too, but on the CMYK car those edges are tucked under other
    parts, so the rivets landed out of sight). `emboss` lays a word or a picture flat on the
    surface nearest a point, with its mirror image by default.
  - `relight(zone=, keep_level=)`: a fade of light colours, and a new hue at the stock
    brightness. `glow(replacing=, keep_level=)`: one kind of glow swapped for another where a
    part carries it (the stock turbo glow for exhaust heat). `peel` tears inner parts too, from
    a `keep("Details")`, and `hold=` keeps the wrap whole in a zone (tears shrink away, never cut).
  - The viewer's Turbo: `TURBO` in `viewer/viewer.js`, the values the turbo videos gave.
  - Checked with a picture of every inner part on its own and close looks from all sides, day,
    night and in a turbo, on TSC_CMYK_BlackTail and TSC_CMYK_EndsInK.

### The Lab (started 2026-09-26)

A page of the tool's own lists: what it can do, and a way to point at any of it. The user
(2026-09-26) wanted "a whole catalog of types of plastic, types of metals, types of rubber", like
the KeyShot library they used to render products with, showing "the matte %, metalness % etc
for each". Then, from the first mockups: "click somewhere to just copy the material so I can
paste it to Claude and Claude would know which I am talking about. That's the whole point of
the lab." Since the user's rethink (below, "The Lab rethought"), the rooms after the Studio
are painting rooms, one per area of the car; Materials stays a tab of its own.

**The Lab's rule (the user, 2026-09-26).** Every room shows the tool's own data, never a list
of its own: "If it doesn't come from the tool, then it will get outdated." The Lab also shows
the user what the tool can do. If the Lab can't name a part, the tool can't either, and that's
the thing to fix. Each room also gets the layout its job needs (the user: "other sections e.g
UV or whatever can be different layouts depending on the need"). So each step opens with its
own round of mockups, and only the Lab's header, its look and copy-for-Claude are shared.

Each step is ticked when the user has seen it.

**Paused (the user, 2026-09-26),** after the room cameras: the parts get defined first (see
`IMPROVEMENTS.md`, "Under way"). The Lab changes only when the user shares a thought for it.
**The design studio takes it over (the user, 2026-09-28):** the Lab's next work is the studio's
wizard (below, "The design studio", W3), and the studio takes in step 9's remaining steps 9.3 to
9.6. Step 9.7 is queued in `IMPROVEMENTS.md`, "The tool".

**Where the Lab may go (the user, 2026-09-26, while step 2 was being built):** "What if we treat
this "lab" as the place to design a car. Let's assume I ask claude to design a car, so basically
the car passes through the lab in a way (obviously in a non linear matter) but I can see how
things are getting built, etc. So in essence it basically starts as a blank car, like a clay
model in some sort, and the "lab" gives me the necessary views to work with claude to build the
car and better describe things etc". Claude suggested starting small: the clay start with a car
that follows Claude's work, and the design's steps to click through. The Studio is step 5 below,
the first room.

**The Lab rethought (the user, 2026-09-26, after the parts and spots mockups).** "When I ask for a
new car skin, or to work on an existing car skin, or design a variation of a car skin, the lab is
the place to see things live. I'm ok that the first tab is all about the building process, it
serves like a timeline, which is cool. But I think the views should cover particular "painting"
rooms. For example, the body, the wheels, the details, etc. My vision is that each room provides
the necessary views that tackle the objective. It could also provide concepts. For example, the
wheels view could be tailored to what's necessary for me to see only the wheels, (we can always
iterate on what to show). Or the body is could be wheels ghosted so that my eyes are on the body
for example. [...] Maybe each view can even display the concepts that the ai provides (like a
option a b and c). [...] I might eventually have a cables and mechanicals or whatever room,
instead of a whole Details room." Before that, "tabs like views": every tab shows the car being
worked on, live; not one page. What was settled the same day:
- **The rooms:** the Studio (the timeline) first, then Body, Wheels, Details and Lights. Wheels is
  its own room, not part of Details. Lights has a choice of Trackmania's four moods (sunrise, day,
  sunset, night); the viewer lights day and night so far.
- **The rooms come from the tool:** a list of rooms, each with the parts it covers, its views and
  what it fades (the Body room fades the wheels and the inner car). Rooms cut across the texture
  sets: Wheels is the tyres (Wheels set), the wheel covers (Skin) and the rims, hubs and brakes
  (the wheel assembly, on Details). A part in no room is a gap to fix; a new room ("cables and
  mechanicals") is a line in the list.
- **The UV map goes into the rooms** (each room's flat map of its own area). **Materials stays its
  own tab**, apart from the rooms.
- **Each room:** its views, Claude's takes for that area side by side (A, B, C), its parts with
  their paint and the step that painted them, the tool's warnings for its area, copy for Claude.
- Live costs no tokens: the tool writes what the page reads as it paints (a few seconds per
  step); Claude doesn't watch the page.

#### [x] 1. The materials room

- **What it's for:** every material the tool knows, on a ball, by family, with its code and
  its numbers (matte, metal and varnish, as %). One click copies a line to paste to Claude.
- **What you'll see:** the Lab (the viewer's "The Lab" link, or http://localhost:8765/lab.html).
  There are 70 materials in ten families, and each ball is painted by the same code that paints
  the car. There's a copy button on every ball, and "Copy for Claude" in the panel. Later,
  TSC_Lab_Materials in the game: every new material on a patch, to drive by day and at night.
- **Model:** Opus 5.5.
- **Notes for Claude:**
  - **The mockups:** https://claude.ai/artifact/PypRSjC19UwhtK3QU4Zk9k.
    - Round 1 offered A shelf and spec panel, B spec table and C on the car. The user loved "on
      the car", but they think about a material for a particular part.
    - Round 2 was about copying: A copy from the shelf, B part then material, C build a list.
      **The user chose A** ("A is the one for materials, at least for now. If I need to
      reiterate I can do it once I start actually using it to design").
    - The mockups' balls and gold car were rendered in the real viewer on the Mac. Headless
      Chrome over CDP, a `__THREE_DEVTOOLS__` hook to reach the scene, and a highlighted-part
      render as the mask to paint one part.
  - **Codes:** `finishes.CATALOGUE` holds each family's two letters and its finishes in order,
    and the code is the family's letters plus the place in it (ME-07 is gold).
    - **Never reorder or remove an entry:** the user copies codes. A new finish goes at the end
      of its family; a retired one leaves None in its place.
    - `finishes.get("ME-07")` and a code inside a phrase ("ME-07 matte") both work.
    - The copied line is `finishes.line()`: `ME-07 Gold (matte 28%, metal 100%, varnish 0%)`.
    - A finish changed by a shine word (`with_shine`) loses its code, because it's no longer
      the Lab's own.
  - **New finishes:** 28 new ones, the Lab's "New" tag (`source` "measured" or "eye"). The
    looks grain, plain, denim, suede, perforated, knurl and muddy are in `tool/looks.py`. Colours
    for stainless steel and brass start from Physically Based (physicallybased.info, CC0, API
    `api.physicallybased.info/v2/materials`, updated 2026-09-01), then set by eye. Measured
    colours are paler than ours: measured gold is sRGB (1, .89, .59), ours (1, .72, .25) was
    set against the game.
  - **Nothing paid:** the game takes only colour, matte, metal and varnish per texel, plus
    relief on the inner car and wheels. KeyShot's library can't be exported, and Substance
    and Poliigon are subscriptions whose detail the game can't show. ambientCG (CC0) is still
    `tool.textures` for photographed surfaces.
  - **`tool/swatches.py`** writes each ball's textures and `materials.json` (codes, numbers,
    colour, where it works, source, line). The Edge screenshot step is gone: `viewer/lab.js`
    draws the balls in the page, lit like the viewer (studio HDR, key light, ACES at 0.9). So
    the Lab works on the Mac too, where `docker/serve.py` paints the balls at start.
    `viewer/materials.html`, `swatch.html` and `swatch.js` were removed.
  - **Checked on the Mac (2026-09-26)** in headless Chrome:
    - every family at 1440×900, and the page at 390×844;
    - a click on a copy button put `ME-07 Gold (matte 28%, metal 100%, varnish 0%)` on the
      clipboard;
    - no page errors.
  - **Next:**
    - the user opens the Lab;
    - on Windows: `tool.skin show TSC_Lab_Materials` (for its snapshots), then `tool.skin
      install TSC_Lab_Materials`;
    - the user drives it. Each finish the game confirms gets `source="game"` (add "game" to
      `SOURCE` in `viewer/lab.js`).

#### [x] 2. The UV map room

- **What it's for:** the car's flat texture maps, as the tool paints them, with every part
  named. Hover over a spot to see its name, and see it light up on a small 3D car. Copy a
  part's name for Claude.
- **What you'll see:** the Lab's "UV map" button (`lab.html?room=uv`). The four maps (Skin,
  Details, Wheels, Glass) in a skin's own paint, every part outlined. Point at one: its name
  shows, and it lights up on the map and on the small car. Click to pick it (or click the car):
  the panel gives its map, assembly, whose paint it shares, sharpness (dots per cm) and size,
  and "Copy for Claude" copies a line like `sidepod top|left (Skin map, its own paint)`. Show:
  Paint, Parts (the viewer's colour by part) or Shared (striped where parts share paint).
- **Model:** Opus 5.5.
- **Notes for Claude:**
  - **The mockups:** https://claude.ai/artifact/YaEE5LWwsb8qHYCAtMeJui. Round 1 offered A the
    map first (the materials room's frame), B map and car side by side, C the car first. Claude
    recommended B; **the user chose A** (2026-09-26). The map and car pictures in it were the
    real ones: coverage masks over TSC_CMYK_Peel_More's paint, and the viewer over CDP.
  - **The tool's data** (`view.export_uvmap`, rebuilt when `car/parts.json`, `parts.py`,
    `coverage.py`, `paintbox.py` or `view.py` change; `tool.swatches` and `tool.view` run it):
    `<Set>_Parts.png`, the part covering each texel (`coverage.owners()` at the paint's size,
    sampled on the `<Set>_Shared.png` grid; R + 256 G = id + 1), and `uvmap.json`: each part's
    `label`, `line` and `paint` words (`parts.Parts`), its sharers (`coverage.twins()`), its
    share of the map, dots per cm and cm².
  - **The copied phrase is exact:** `Parts.token()` is the shortest `name|side|end` that picks
    that part alone; all 210 were checked through the paint box. "floor", "front wing" and
    "engine cover" name both an assembly and a part in it, so the paint box learnt `|part`
    ("floor|left|part"); the bare names still paint the whole assembly.
  - **Sharers** count texels both parts cover by three quarters or more (where two parts meet
    on one island, the texel they split counts for neither), at least 64 at the paint's size.
    A shared texel names the lowest id (the centre, then the left twin); pointing at one lights
    all its sharers.
  - **The car** is the viewer itself, `index.html?embed=1` (just the car, the viewer's own
    lighting): `window.viewer.light(ids)`, `aim(ids)` (glides to face the part's middle, from
    below for the floor) and `onPick`.
  - **Which skin's paint:** `?skin=`, else the one the viewer showed last (`localStorage`
    `tsc-viewer-skin`), else the one installed last (`installed_at` in `gallery.json`). The
    viewer's "The Lab" link carries its skin.
  - **What the room showed:** shared paint isn't only mirror twins. The front wing shares most
    of its paint with the floor, one patch of paint is used by 16 inner parts, and the floor
    shares 79 % of its own. On the list: the paint box's note about shared paint.
  - **Checked on the Mac (2026-09-26)** in headless Chrome: each map at 1440×900, pointing and
    clicking (sidepod top), picking from the car (the floor), Paint, Parts and Shared, 390×844
    with no sideways scroll, the materials room and the viewer as before, no page errors; a skin
    repainted (TSC_Seams_Black) as before.
  - **Next:** the user looks.

#### [replaced] 3. The painting rooms

- **Replaced** (2026-09-27) by one UV map room (7, and `tool/rooms.py`).

- **What it's for:** the rooms of "The Lab rethought" (above), Wheels first to settle what every
  room has; then all four were built the same way.
- **What you'll see:** the Lab's Body, Wheels, Details and Lights tabs: each the car with a camera
  on its area, or (UV map) its own flat maps, live as Claude paints. Body sees the car from higher
  up, Wheels one front wheel close, Details the inner car with the shell taken off, Lights the rear
  at night.
- **Model:** Opus 5.5.
- **Notes for Claude:**
  - **What came before (replaced):** a spots room and a parts room, live. Their mockups:
    https://claude.ai/artifact/TK9zZ8RL28oWKRTaxvYgEE (the ice cream truck painted in five
    steps in memory, every paint call recorded; not picked, the user rethought the Lab instead).
    Their lists and warnings move into the rooms; the named places for stickers and words
    (`paintbox.SPOTS`) into the Body room.
  - **What the tool knows but never showed the user** (found making those mockups):
    - TSC_IceCreamTruck's mint brake calipers and cream rims, hubs and brake lights never showed:
      `s.paint("inner", "charcoal satin")` comes after them and paints the whole inner car, which
      holds the wheel assembly. A room marks a part painted over: named in one step, repainted
      by a broader word in a later one.
    - Its "ICE CREAM" on the flanks sits over a 5 cm fold, and the paint box noted it would look
      cut there (the crease shows through the letters). The notes stay in the design's run.
    - `decal` and `text` don't go through `_ids`, so a step that only places pictures and words
      records no `paints`: the Studio's "Paints" row is empty for it.
  - **The mockups:** https://claude.ai/artifact/47FiUhMQm3yN4sqn6ryqC4. Round 1 is the view the room
    opens on: A the rest of the car faded, B the wheel taken apart, C as in the game (Cam 1). Every
    option has the same frame: the views down the rail (faded, taken apart, in the game, outside,
    inside, flat map), the big view, the takes under it (the car now, then A, B, C), the picked
    take's paint per piece with the tool's warnings, copy for Claude. The takes were real: three
    wheel designs over TSC_IceCreamTruck, painted by the tool and exported to the viewer as
    TSC_Mock_Wheels_A/B/C (the work folder only; remove them when the round is done). Faded and
    taken apart were prototyped in the render script (the viewer can't fade yet): the car at 30 %
    under the wheels drawn over black and white and keyed out; one wheel of four by redirecting
    the other wheels' part ids.
  - **What the room showed:** the front hubs share their paint with 14 other kinds of inner part
    (sidepod frames and panels, floor, wishbones...), so painting them in the Wheels room changes
    the Details room: a warning that crosses rooms.
  - **The user's answer (2026-09-26):** "Let's not do faded for now, let's focus on the rooms
    first, what you can do is just have a camera more focused to e.g wheels, each having their
    uv map as a different view but not as you have it on the left, just like a tab." So no fading,
    no takes side by side and no rail of views for now: each room is its camera and its UV map,
    as two tabs.
  - **Built (2026-09-26):**
    - `tool/rooms.py`: ROOMS (key, name, what it holds, the camera as a viewer view, night, the
      maps its UV map tab offers and the texture each shows) and `_member`, the rule for each
      room's parts. Body: the Skin set without the wheel covers, the canopy and the mirrors'
      glass. Wheels: the tyre, wheel cover and wheel assemblies. Details: the Details set without
      the wheel assembly. Lights: the parts that glow in Nadeo's light map (2 % of their texels,
      64 at least, by name so mirror twins go together: 35 kinds of part) and the other glass
      (lenses, gear display), at night, its map the light map (Details_I). `rooms()` raises when
      a part is in no room. 40, 38, 122 and 86 parts; a part may be in two (a rim: Wheels and
      Lights).
    - `view.export_uvmap` adds `rooms` to uvmap.json (rebuilt when `rooms.py` changes).
    - The Lab's tabs: Studio, the rooms from uvmap.json, Materials. The UV map room is gone
      (`lab-uv.js`); `?room=uv` opens the first room. `viewer/lab-rooms.js` is every room: the car
      (the viewer, `?embed=1`, dressed in the skin's textures, `viewer.show(room.view, night)`) or
      the room's maps (only its parts drawn, the rest of the map empty; a map button per set when
      there are several), the picked part in the panel with the room(s) it's in and its line to
      copy. Clicking the car picks a part; nothing is lit until one is picked, so the paint shows
      as it is. The Lights room has the moods: day and night work, sunrise and sunset are greyed
      ("not in the viewer yet").
    - Live as the Studio: the skin in the address, else the one Claude painted last, followed
      when Claude starts another (studio.json); while it's painted, the newest step's frame.
  - **Checked on the Mac (2026-09-26)** in headless Chrome: every room's Car and UV map tabs at
    1440×900 (Flag Peel Costa Rica Sun Faded), the Wheels room at 390×844, no sideways scroll, no
    page errors. The mock takes (TSC_Mock_Wheels_*) were removed from the work folder.
  - **The cameras (the user, 2026-09-26).** The first ones were set by eye: Body small in its
    frame, Wheels aimed between the wheels (both cut off), Details nearly Body's view (the shell
    hides the inner car), Lights with little glowing in view. The mockups:
    https://claude.ai/artifact/1j5ftfuzYn6TiZz7F5uddd, each room as built and two new cameras, real
    renders of TSC_FlagPeel_CostaRica_SunFaded in the embedded viewer. **The user chose** Body B
    (from higher up, the whole car: the most painted shell in one picture), Wheels A (one front
    wheel, close: its outside, and the far wheel's inside with the rim and brake ring), Details B
    (the shell taken off, as Claude recommended: a camera alone can't see the inner car) and
    **Lights as built** (Claude had recommended the front at night, for the rim rings and grilles).
    - Not picked: Body at today's angle filling the frame; Wheels the front pair head on; Details
      low at the front (the front suspension and wing only); Lights behind and low (the speed
      digits big).
    - **How it works:** a room's view in `rooms.py` names what it frames (`FRAMES`: "car", "front
      left wheel") and a margin; `rooms()` exports the ids as `view.fit`. The viewer (`fitView`)
      finds the distance and aim that put those parts' corners (every 8th) inside the picture with
      the margin to spare at the nearest edge, for the frame's own shape (checked at 1058×740,
      718×640 and a phone's 358×250), and frames again when the window changes until the user
      turns the car. A room's `hides` names a room whose parts it takes off (Details: the Body
      room's 40 parts, the number plate with them) through `viewer.hide(ids)`.
    - Hidden parts cast no shadow now (the Skin's and Details' shadow material reads the part
      table): the shell's shadow darkened the inner car it was hidden to show. The viewer's own
      Parts list gets the same.
    - A room's first part in the panel is its biggest part in the camera's frame (the Wheels room
      named a rear rim while it showed the front left wheel).
    - On a phone the page was 415 px wide since the rooms came (the six room tabs): the tabs now
      scroll sideways on their own, like the materials' families.
  - **Checked on the Mac (2026-09-26)** in headless Chrome: every room at 1440×900 and 390×844 (no
    sideways scroll), the Wheels room loaded at 1100×800 and resized to it (the same framing),
    switching Details → Body → Wheels in one page (the shell comes back), clicks in the Details
    room pick inner parts (cockpit tub, lower wishbone) and never the hidden shell, the Studio, and
    the viewer hiding the body; no page errors.
  - **Next:** the user looks.

#### [replaced] 4. What the rooms do next

- **Replaced** (2026-09-27): the rooms went (7).

- **What it's for:** what the user described for the rooms and put off for now (2026-09-26:
  "let's focus on the rooms first"), each when the user asks, opening with its own mockups.
- **Model:** Opus 5.5.
- **Notes for Claude:**
  - Claude's takes for a room side by side (A, B, C), as in the Wheels mockups. For a round of
    concepts the user chose a switch instead (step 6); side by side stays unbuilt.
  - A view that fades the rest of the car (the Body room with the wheels faded): the viewer
    would need a fade per part (a third channel in its part table). Taking parts off is built
    (the Details room, 2026-09-26: `hides`, `viewer.hide`).
  - The parts painted over (named in one step, repainted by a broader word in a later one) and
    the paint box's notes (a fold under a sticker) shown in the room: the paint box would record
    what each step put on each part (`decal` and `text` record no `paints` yet).
  - The named places for stickers and words (`paintbox.SPOTS`) in the Body room.
  - ~~Sunrise and sunset lighting in the viewer~~: dropped (the user, 2026-09-27: day and night only).

#### [replaced] 5. The Studio: a car built from clay

- **Replaced** (2026-09-28) by the car's room, the fresh layouts' A ("The design studio"). What
  lives on: the car follows Claude's painting step by step, from clay.

- **What it's for:** the room where a car gets designed with Claude. It starts as a clay car,
  and each step of the design (the colour run, a wrap, the lights, the wheels) becomes a frame
  of the car. The user watches it being built, goes back to any step to ask for a change there,
  and uses the other rooms to point at parts, places and materials.
- **What you'll see:** the Lab's first room. The car at the picked step, big; a filmstrip of
  the car at every step under it, clay first; the step's words, what it does and a line to copy
  on the right; a note when Claude has just changed something.
- **Model:** Opus 5.5.
- **Notes for Claude:**
  - **The mockups:** https://claude.ai/artifact/GLHzbyTXCwtP3C3Wg6tBc6. Round 1 offered A steps
    down the side, B a filmstrip under the car, C the design's story (each step with the user's
    words). **The user chose B** (2026-09-26), as Claude recommended. The pictures were real:
    TSC_CMYK_Peel_More painted step by step over clay (matte `#b3a089` on body, wheel covers
    and inner car; tyres and glass left alone), each step exported to the viewer and drawn over
    CDP. The lights step only shows at night (a rear view at night).
  - **The clay (the user, 2026-09-26):** parts no step paints stay clay in the game too, so the
    Studio shows what the game will ("I would do clay but ... the clay looks a bit too warm
    maybe? Is there a more whiteish clay color?"). Round 2 of the same page offered A warm white
    `#ddd2c0`, B neutral white `#dadad8`, C cool white `#d0d9df` (a first try at three whites
    looked alike under the studio light); **the user chose B, neutral white `#dadad8`**, matte,
    on the body, wheel covers and inner car (tyres and glass keep their own).
  - **How it works (built 2026-09-26):**
    - A design marks its steps: `s.clay()` (step 0, the clay finish, PA-10 in the Lab), then
      `s.step(name, does, words=, look=)`. Paint before the first step is a step of its own
      ("The design" if it's the only one). The paint box notes what each step paints (`_ids`).
    - `tool.skin show` paints with frames on (`paint(name, frames=True)`; `install` doesn't):
      at the end of each step the car's textures go to the viewer's data at half size, only the
      slots that changed, each URL carrying its picture's digest (`view.save_frame`), and
      `skins/<name>/steps.json` is rewritten (`view.export_steps`, written whole: the page reads
      it while it changes). `studio.json` names the skin being painted. Frames cost about 15 s
      more per show and 9 MB for TSC_CMYK_Peel_More.
    - The Studio (`viewer/lab-studio.js`, the Lab's first room) asks for both every 1.5 s: the
      filmstrip fills in while a design paints, a step still painting shows "painting…", the
      step just painted is New, and when Claude starts another skin the Studio follows it.
    - Two viewers in `?embed=1` with no skin (the stock car): the big one, and one hidden
      behind it that draws the filmstrip's pictures (`viewer.dress(urls)`, `viewer.picture()`).
      A step's `look` ("rear night") turns both. A skin painted before the Studio shows as one
      step, "The design", until it's shown again.
    - TSC_CMYK_Peel_More's chain now has steps (the colour run, the black wrap, torn open in
      TSC_CMYK_Peel; lights, wheels in its own design), with the user's words from the notes.
      It keeps Nadeo's paint where it paints nothing: it was made before the clay.
  - **Checked on the Mac (2026-09-26)** in headless Chrome: TSC_CMYK_Peel_More's five steps; a
    test car painted from clay while the Studio was open (clay, red body, stripe, gold wheels:
    the filmstrip filled in step by step, "Claude is painting", then New on the last); opened on
    another skin, it followed the new one; 390×844 with no sideways scroll; the materials and UV
    map rooms as before; no page errors. The test car was removed.
  - **Next:** the user tries it on a new car.
  - **Claude's rough rounds stay live** (the user, 2026-09-27, asked whether the fix rounds before
    showing were worth watching in the Studio: "I like to see the work going on, so yes"). So no
    quiet mode: every `tool.skin show` paints its frames and moves the Studio.

#### [replaced] 6. Concepts in the Lab: a switch between a round's takes

- **Replaced** (2026-09-28) by the sets of options; the rounds and their switch were removed the
  same day ("The Lab's timeline", 1).

- **What it's for:** a loose idea gets two or three concepts, and the Lab showed only the one
  painted last; the user saw them together only in the picture Claude opened ("I see the options
  because you launched Preview in mac with the 3 concepts. But in the lab I only see one").
- **What you'll see:** in the Studio, the round's title ("Chaos and elegance") and a button per
  concept, A · Kintsugi, B · Thrown, C · Unravelled; the same buttons in Body, Details, Tyres and
  Glass. Picking one shows it in the whole Lab, at the step the Studio was on.
- **Model:** Opus 5.5.
- **Notes for Claude:**
  - **How it came about (2026-09-26):** the user asked to run a whole concept round "from start to
    finish ... and see how you feel about the workflow (if there are any improvement from a
    backend and frontend)". Their brief, "I want chaos and elegance", gave TSC_ChaosElegance_
    Kintsugi, _Thrown and _Unravelled (the snags Claude hit are on `IMPROVEMENTS.md`).
  - **The mockups:** https://claude.ai/artifact/Cu34iPj7nZVy4WXrJRe4Ji, the real Studio with the
    three concepts (captured over CDP: the stage, the filmstrip's pictures and the markup, in the
    Lab's own stylesheet). A a switch in the title, B the concepts side by side (front and rear),
    C a filmstrip per concept. Claude recommended B; **the user chose A** (2026-09-26).
  - **How it works:** `python -m tool.skin round "<title>" <skin> <skin> ... --words "..."` writes
    `skins/rounds.json` (title, words, date, takes lettered A, B, C in that order; a take's title is
    what its name adds to the others', or `name=Title`). `gallery.refresh` puts each take's round
    on its `gallery.json` entry. `viewer/lab-round.js` draws the switch (`.show` of `.sk`) in the
    Studio's head (`#stRound`, the round's title as the heading) and the rooms' (`#prRound`); a
    pick sets `?skin=` (keeping `?step=`) and sends `lab:skin`, which the Studio and the rooms
    (each keeps its own car) both open. Following Claude's painting (studio.json) now updates
    `?skin=` too, so a room opened later shows the same car. The rooms' head wraps to two lines
    when the switch leaves the pickers no room (1100 px).
  - **What came of the round:** the user picked Unravelled, then asked for it in CMYK on dark grey
    (two takes, the round "Unravelled"), and on 2026-09-27 kept only the two CMYK takes to install;
    Kintsugi, Thrown and the ivory Unravelled were deleted (in the git history).
  - **Checked on the Mac (2026-09-26)** in headless Chrome: A to B at the Wheels step (B opens at
    Wheels), B carried into the Body room, C picked there and carried back to the Studio, a skin
    in no round shows no switch, 390 × 844 (Studio and Tyres, no sideways scroll), 1100 × 800 and
    1440 × 900 (the rooms' head on two lines, then one), no page errors.
  - **Next:** the user looks.

#### [x] 7. The Lab without the rooms: notes on the car

- **What it's for:** the user, 2026-09-27: "I'm starting to not find the views (body, details,
  etc) so helpful. And also, not sure I find the sidebar on the right useful. I like the design,
  but when doing skins I haven't used that, so I'm wondering we replace that for something more
  useful?" So the room tabs go and the Studio's right panel (the step's words, what it paints,
  copy for Claude) gives way to something the user would use.
- **Model:** Opus 5.5.
- **Notes for Claude:**
  - **The mockups:** https://claude.ai/artifact/RDHpVhtt3SYTP8X2t21zQ9, the real Studio (its
    stylesheet and markup captured over CDP, TSC_ChaosElegance_Unravelled_CMYKRise at step 5) with
    only Studio and Materials on top. A just the car (the whole width; Around, Cam 1, 2, 3 and day
    or night as buttons over it), B the game's views (Cam 1, Cam 1 at night, Cam 2, Cam 3 at the
    picked step down the side, cropped from 1280×720 renders around the car; click one to see it
    big), C notes on the car (click the car to pin a note; Claude reads them with the user's next
    message, which needs a store on the Mac's server and a hook). Claude recommended B; **the user
    chose C** (2026-09-27).
  - **The UV map stays, as one room.** The rooms' cameras go, but the user had said the map's
    surfaces would be useful ("for the uv map separating surfaces, that's going to be useful"), so
    `tool/rooms.py` holds one room, "UV map" (`?room=uv`): the four maps (Skin, Details, Wheels,
    Glass) and the whole car as a tab (Maps, Car), opening on the maps. The old rooms' addresses open
    it. The part card drops its Room line while there's one room. Left for later, if the user
    finds the map isn't used either: `lab-rooms.js`, `export_uvmap`/`_surfaces`, `coverage.sets`
    and the viewer's Lab-only calls, about 800 lines.
  - **Built (2026-09-27): notes on the car.**
    - The Studio's panel is "Your notes": click the car (a click, not a drag) and the viewer
      (`?embed=1`, `onPick(id, {at, normal})`) gives the part and the point; a white pin marks it
      while the box below names the part ("floor (right)") and takes the words; Enter or Add note
      keeps it, Shift+Enter a new line, Esc or Cancel drops it. Each note shows its number, words,
      part, step and "Claude has it" once read, with a × to take it back. The step's words, what
      it paints, the still-clay parts and Copy for Claude went with the old panel.
    - Pins (`viewer.pins`) are drawn by the viewer over its canvas, placed on their 3D point every
      frame, so they stay on the spot as the car turns; one fades while its spot faces away or
      the car hides it (a ray from the camera, checked when the camera has moved).
    - `tool/notes.py` keeps them in `skins/notes.json` (skin, number, words, step, part as label
      and `where` phrase, point, facing, time, state new → sent → done). The viewer's server
      (`view.Handler`, both computers) answers `GET/POST /api/notes`, only for this computer's
      pages: the Host must be localhost, an Origin must match it, and the body must be JSON (a page
      elsewhere can't send that without a preflight the server never answers). Checked with curl:
      a foreign Origin, a text/plain body and a foreign Host are refused, an unknown skin too.
    - A UserPromptSubmit hook (`.claude/settings.json`) runs `tool/notes.py --hook` with the
      computer's own Python (the Mac's python3, else the PC's venv): it prints the new notes into
      Claude's context and marks them sent. Claude marks one done (`tool.notes done <skin> <n>`)
      once handled and its pin leaves the car. Standard library only, runnable as a file.
    - Checked on the Mac (2026-09-27) in headless Chrome, TSC_ChaosElegance_Unravelled_CMYKRise:
      a click on the car opened the box on the part under it, Enter kept the note (list, count,
      pin), the pin followed the car when dragged and faded behind it, the hook printed it and the
      Studio then said "Claude has it", × took it back (no pin), `done` hid it; 390 × 844 with the
      notes under the car and no sideways scroll; the UV map room's four maps; no page errors.
  - **Next:** the user tries it on a skin.

#### [x] 8. A picture with each note; day and night only

- **What it's for:** the user asked for ideas for the Lab (2026-09-27) and picked two of six to
  mock up: a picture with each note, so Claude sees exactly what the user saw, and sunrise and
  sunset light (the greyed buttons in the rooms' mood picker).
- **Model:** Opus 5.5.
- **Notes for Claude:**
  - **The mockups:** https://claude.ai/artifact/DMCTNVNr9AnypiToeawde2. The note: A words only in
    the list, B words and picture; **the user chose A** (Claude still gets the picture). The skies:
    six real Poly Haven skies (CC0) on TSC_ChaosElegance_Unravelled_CMYKRise, three sunrises
    (kiara_1_dawn, spruit_sunrise, umhlanga_sunrise) and three sunsets (the_sky_is_on_fire,
    belfast_sunset_puresky, industrial_sunset_02_puresky). **The user dropped both:** "lets remove
    the option, let's just keep the day and night". The mood picker has Day and Night only.
  - **How the skies were tried** (for another time): the viewer's environment swapped in the page
    over CDP (`__THREE_DEVTOOLS__` catches the scene and renderer), the HDR loaded as floats, its
    brightest texel taken for the sun, the columns rolled so the sun sits where the key light comes
    from (azimuth atan2(0.35, 0.55)), the key low (8 to 35°) in the sun's colour, and the sky's
    brightness matched to the studio's (sun clamped at 50). Three's equirect lookup
    (u = atan2(z, x)/2π + 0.5, flipY rows) was checked on a plain page: the sun came out centred. A
    stronger key threw the car's shadow onto the room's wall. The candidate skies were downloaded
    to the work folder's viewer/try/ and removed.
  - **Mood files in the game** (the user asked): each mood is a decoration with a
    CGameCtnDecorationMood (Latitude, Longitude, DeltaGMT, TimeSunRise, TimeSunFall,
    SunMoonIntensity, tone-map exposure, IsNight, clouds, stars: Openplanet's documentation),
    inside the game's packed files; Openplanet (a third-party mod loader) can extract them. Not
    used: game screenshots are the simpler reference.
  - **Built (2026-09-27): the note's picture.** When a note is kept, the Studio renders the stage
    (`viewer.picture()`), draws the note's pin on it where the viewer placed it (scaled to the
    canvas), and sends it as a JPEG with the note. `tool/notes.py` checks it (a JPEG, 6 MB at
    most) and keeps it in `.notes/<skin>-<n>.jpg` (git-ignored); the hook's line ends with its
    path for Claude to look at; taking a note back or marking it done deletes it. Checked on the
    Mac: the picture showed the car as seen with pin 1 on the sidepod grille, the hook named it,
    `done` removed it.
  - **Brighter day and night (the user, 2026-09-27: "night is too dark though, and the lighting is
    too dimmed", "maybe the day could be brighter or maybe the background is too grey").** The
    mockups: https://claude.ai/artifact/Gfm17Zv9rUL5WX2D53PE1V, TSC_ChaosElegance_Unravelled_CMYKRise
    and TSC_IceCreamSweet through the viewer's own address settings. Day: A as it was, B brighter
    paint, C a light grey room, D a white room; night: A as it was, B twice the moonlight, C much
    brighter, D a bright car in a near-black room. Claude recommended C and D; **the user chose day
    B, and night B with brighter glows.** Each look now has its own exposure and glow (`LOOKS` in
    `viewer/viewer.js`; `TUNE`'s exposure, env, key and glow multiply them): day exposure 1.2 and
    env 1.25; night env 4.4, key 0.44 and every glow ×1.8 (`glowScale`, the rear lights too).
    Glows tried at 1, 1.8 and 2.6 close up (the speed digits, the wheel rings): at 2.6 the tinted
    digits had turned white. Claude's snapshots go through the same viewer, so they're brighter
    too.

#### [replaced] 9. The Lab as a factory: the car on the stand

- **Replaced** (2026-09-28) by the fresh layouts' A ("The design studio"). What lives on: the
  notes as tags on the car. The stations went.

- **What it's for:** the user, 2026-09-27, after Claude described how a car gets built: "I was
  kind of thinking on redesigning the lab ... since it's an iterative process then im not sure the
  current interface serves the purpose ... it seems there are options that you provide as well as
  you go ... if you were to not even take influence on the current one. How would you define the
  perfect interface that resembles like as if you are at a factory building a car?", then "you
  could even change the workflow in the backend if that helps as well. Without affecting quality".
- **What you'll see:** the car fills the Lab. Your notes, Claude's answers (with a before and
  after), the options Claude brings and Claude's own checks hang on the car as tags where they
  apply. The build's steps run small along the bottom, then the inspection, the test track and the
  car in the game.
- **Model:** Opus 5.5.
- **Notes for Claude:**
  - **What a replay of TSC_CMYK_EndsInK's build showed** (27 Sep, 14:03 to 15:48 UTC):
    - 10 notes, about 18 repaints (`show` painted in 90 to 127 s each) and 4 installs (the zip
      built in 196 to 258 s). Claude looked at about 46 pictures. The user's messages were mostly
      "added comments" and "Yes", and every change came through a note.
    - The gaps:
      - Claude's answer never came back to the note: the pin just went.
      - There was no before and after. The Studio shows the current version's steps only, and
        `versions/` keeps a picture per round that the Lab never shows.
      - The texture round was three separate skins behind the round switch.
      - `show`'s notes (shared paint, folds, still clay) and the close-ups reached only Claude.
      - The wheels' pieces were in three places, and the game test was outside the Lab.
  - **The factory, as Claude defined it:**
    - the line: Body, Inner car, Wheels, Lights, Glass, then Inspection, Test track and In the
      game;
    - the user's notes as rework tickets: open, then Claude on it, then answered with a before and
      after, then accepted or reopened;
    - options (A, B, C) held where they apply until the pick, the others kept;
    - Claude's checks visible, and one status line;
    - the test track: the user's F12 screenshots after an install, with notes on them;
    - the paint store: materials, treads and markings.
  - **The mockups:** https://claude.ai/artifact/LL5JJx8EqoHhAUeFNDrZXu, at the moment just after
    the texture round (A Carbon, B Halftone, C Brushed), with notes 4 and 5 answered.
    - A, the assembly line: stations across the top, the open station below.
    - B, the car on the stand: everything as tags on the car.
    - C, the review bay: the round's options side by side, the rounds as history.
    - Claude recommended A. **The user chose B** ("Let's try the car on the stand. Looks
      interesting").
  - **How the mockups were made** (for another round): a scratchpad script drove the viewer in
    Edge through Playwright, as `snap.snap()` does but without `view.prepare`, which re-exports the
    skin from the last built DDS files.
    - Cameras: `viewer.show` with view names or `{dir, dist, target}`.
    - A step's picture: `viewer.dress` with `steps.json`'s textures. TSC_CMYK_EndsInK's step 5
      against step 6 gave the mirror's before and after for notes 4 and 5.
    - Pins: `viewer.pins` projected 3D points onto the page. In `?snap=1` a pin's bounding rect
      reads as zeros, so the script read its `style.left` and `style.top` instead.
    - The mockups used the Lab's own stylesheet (lab.html's `<style>`) plus the new layouts, each
      at 1440×900 in its own frame on a plain sheet.
  - **The steps** (the plan the user approved, 2026-09-27; the stations put in on 2026-09-28, at
    the user's word), each built, checked, shown, then ticked:
    - 9.0, the groundwork;
    - 9.1, the stand;
    - 9.2, the stations and their tries (the user's pick, 2026-09-28);
    - 9.3, answers on the tags and the status line;
    - 9.4, options on the car. A pick becomes the station's next try, and the other takes are
      deleted (the user, 2026-09-28: "when I choose one, im assuming it can just discard the
      others ... I dont think we can keep on maintaining options that I don't like, hence maybe
      creating so much noise"). Their folders go from the repo, and git's history keeps them in
      case the user asks. The takes of rounds already made: list them and ask before deleting.
    - 9.5, Claude's checks and close-ups;
    - 9.6, the game (the F12 screenshots, after asking). 9.3 to 9.6 were folded into the design
      studio on 2026-09-28 (below, "The design studio");
    - 9.7, behind the scenes: repainting only the station that changed (each station is its own
      game file). Gated on identical game files. Queued in `IMPROVEMENTS.md` since the studio took
      over (2026-09-28).
  - **9.0, the groundwork (built 2026-09-28):**
    - **Notes:** `tool/notes.py` keeps the notes in `.notes/notes.json`, off git, with an
      mkdir lock, retries, a skin-name check and `TSC_NOTES_HOME` for tests.
    - **Server:** `view.Handler.do_POST` is an action table. It answers 503 when the notes stay
      busy, and 400 for a body that isn't a JSON object.
    - **The Mac:** `start_steps(follow=False)` lets the Mac's startup repaint (`serve.paint_all`)
      leave the Lab where it is.
    - **Viewer:** the pedal keys drive only the viewer's own page, and `hide()` rechecks the
      pins.
    - **Studio fixes:**
      - a skin opened after a night step no longer stays at night;
      - parts are looked up by id;
      - polling stops in hidden rooms;
      - the Studio doesn't follow Claude away from a note being written;
      - a note's step and picture are taken at the click.
    - **Checks:** 16 passed, in Edge on the PC, and the baselines were unchanged (the six views,
      two close looks, Cam 1 and the standalone viewer).
  - **9.1, the stand (built 2026-09-28):**
    - **What you'll see:** the Lab opens on the car, framed between two gutters. The notes hang in
      the gutters as tags, each joined by a line to a dot on its point. Under the car: the build's
      steps, the game's Cam 1 and Cam 2, and when the car went into the game. Day, Night and Front
      are over the car. The model's credit shows.
    - **Using it:**
      - Click the car and write: the note hangs there, and Enter keeps it.
      - Click a tag or its dot: it opens, and the car turns back to the view the note was
        written from.
      - Escape closes a tag. The stand doesn't follow Claude to another car while a tag is open or
        a note is being written.
    - **The viewer, embed only:**
      - `inset(box)`: `framing()` takes a box, and it's the standalone viewer's framing by the car's
        own outline.
      - `track(list, onMove)`: the points projected at the end of each frame that moves them.
        Behind-the-car raycasts wait for 10 still frames, at most 4 a frame.
      - `project`, `camera()` (dir, dist, target, fov, mood and framing), `go`, `mood`, `views`,
        and `picture({ crop: 'inset' })`.
      - `pins()` and `#pins` are gone.
    - **The Lab:**
      - `lab-tags.js` handles the gutters, the order by height, and one tag open at a time.
      - Under 1000 px the tags become a list under the car.
      - The picture car behind the stage is half its size and the same shape, so its pictures
        crop to the car's box as the stage does.
      - The first room's button is "The car".
    - **The note's `view`** is checked in `notes._view`; a bad value drops the view, not the note.
    - **The picture sent with a note** is the car's box only, with its dot drawn on.
    - **Checks:** 23 passed, in Edge on the PC, with six of the user's real notes copied into a
      scratch notes folder:
      - no two tags overlap, and every line ends on its dot, at the front and left views;
      - the notes' points fall in the car's box at the front, rear and left;
      - while the car glides, the dots stay on their points (0.05 px at worst);
      - a click on the tail panel starts a note there, and the dot lands where the click was;
      - the note keeps its view, and its picture is the box's size;
      - the hook prints it;
      - an open tag holds the car against a new studio.json;
      - the cameras in the strip are the viewer's;
      - at 1100×800 and 390×844 nothing scrolls sideways;
      - the UV map room's car still picks parts and shows the credit;
      - no page errors.
      - The baselines were unchanged.
    - **Found on the way:** a skin painted before the Studio has no steps.json. The stand now asks
      for it only when Claude starts a paint, not every 1.5 s.
    - **On the PC:** two old servers were still listening on port 8765 (yesterday's `tool.view` and
      `tool.swatches`, both allowed to by the reuse flag), with the old notes code in memory. They
      were stopped, and `tool.swatches` was started afresh. After a change to the server, restart
      whatever serves 8765.
    - **Next on the Mac:**
      - `docker compose restart` after the pull, so the container serves the new notes code;
      - the concurrency test with the server in the container and the hook on the host;
      - check that start-up no longer moves the Lab;
      - check that the stand renders.
    - **The user tried it (2026-09-28):** "the clicking and comments works pretty good. Im kinda
      concerned with the overal workflow because the website now is soooo slow. And im imagining
      we are adding so many pictures". They asked whether the Lab should be a standalone app that
      runs only locally. Claude's answer: it already runs only on this computer, and an app would
      draw the car with the same engine. The slowness was the page's own work.
  - **Speed, between 9.1 and 9.2 (built 2026-09-28):**
    - **What was slow:** both of the stand's cars (the stage, and the picture car behind it) were
      drawn every frame at the screen's rate, 240 a second on the user's 2560×1440 239 Hz screen,
      with shadows and the glass's extra pass, while nothing moved. And the picture car loaded
      every step's textures again at each visit to draw the strip.
    - **Now:**
      - The embedded viewer draws only when something changed: the camera moved (a drag, its
        damping, a glide), a call from the Lab (every `window.viewer` call but the read-only
        `project`, `camera`, `views` and `gpu`, when made and when done), a resize, or the frames
        a call awaits. `trackAnchors` still runs every frame, so the still-frame count for the
        dots' raycasts goes on. Embed only: the page online and the snapshots draw every frame.
      - The strip's pictures are kept in the browser (the Cache API, `tsc-lab-pictures`), by the
        frame's hash, the view and day or night, under the `Last-Modified` dates of `viewer.js`
        and `studio.js`, so a change to how the car looks draws them afresh. The newest 400 are
        kept. A skin from before the Studio has no hash: drawn each visit, never kept.
      - The picture car starts only when a picture is missing.
      - The Materials room's ball isn't drawn while its room is hidden.
    - **Measured** in headless Edge on the PC, 1440×900, TSC_CMYK_Brushed (7 steps, Cam 1 and 2):
      - standing still, Edge used 70 % of a core before and 1 % after;
      - a second visit: the car ready in 1.15 s, not 4.25 s; the strip in 1.33 s, not 8.9 s; the
        picture car not started;
      - the first visit is unchanged (8.9 s to the whole strip).
    - **Checks:**
      - 14 passed on what's drawn: after a drag, Day, Night, a step, a resize, a glide and a room
        change, a forced redraw changes no pixel;
      - a dot still dims when its point turns away;
      - the Materials ball still turns;
      - step 9.1's 23 checks passed again;
      - the baselines are unchanged to the pixel.
    - **Left as it is:** the server sends `Cache-Control: no-store` for everything, so every
      texture is fetched again at each visit. On this computer that costs little next to decoding
      them. On the Mac's Docker it may cost more.
    - **For the answers** (the user's worry about more pictures): the answer's after picture is
      drawn only when its tag is opened, and kept like the strip's. The before is the note's own
      JPEG.
  - **9.2, the stations and their tries (built 2026-09-28):**
    - **The user, 2026-09-28:** "I know we have a full timeline of the build of a car, but shouldnt
      it be better to just have default stations? Like a typical car factory? ... like the body,
      the details, etc. And I guess each might have their iteration?" Claude answered that stations
      wouldn't hurt the game files, and rendered the stand both ways
      (https://claude.ai/artifact/BianuzqYpsLrVSQBGMXJDL): A, the build's steps; B, stations with
      their tries. **The user chose B.**
    - **What you'll see:** four stations under the car, Body, Details, Tyres and Glass, the same on
      every car. Each says its try ("try 3"), or "as it comes" when nothing paints it. The open
      station shows all its tries. A click on one puts it on the car, with the other stations as
      they are now. A click on a station turns the car to it (Body the front, Details the rear,
      Tyres the left, Glass from above the front). While Claude paints, the car shows each step
      as it's done, and a station being changed says "painting…". At the end, the stations that
      changed get their new try, marked New.
    - **Why stations are safe:** a station is one of the game's four maps, which are the car's
      groups (car/parts.json), so nothing about the paint changes. A try is read from the last
      frame's pictures of that map.
    - **How it's built:**
      - `rooms.STATIONS` (key, name, map, view) goes into uvmap.json, so the page has no list of
        its own.
      - At the end of a show, `view.export_stations` runs before the final steps.json. It
        compares each station's own pictures (their digests) with its newest try. A change gives
        a new try `{n, at, sig, textures}` (every slot of its map but the AO), with its pictures
        copied to `tries/`. The newest 8 are kept, and older pictures deleted.
      - steps.json says whether stations.json exists (`stations`). A skin shown before the
        stations gets one try per painted station, made up from its last frame, and no request
        that would 404.
      - The page builds the car from the last frame, each station at its newest try, and the
        open station at the picked one.
      - A note keeps `station: {key, name, try, latest}`, the station of the clicked part's map.
        The hook says "looking at the Tyres station, try 2 (an earlier try than the newest)".
      - The round's switch keeps `?station=`.
      - Pictures are keyed by a hash of their textures' URLs and the view, so a try that looks
        like an earlier one shares its picture. While Claude paints, no new pictures are drawn.
    - **Checks:**
      - 13 passed on `export_stations` with made-up frames: first paint, the same paint, only one
        map changed, back to stock, 8 kept, pictures deleted.
      - A real test car (TSC_Test_Stations, deleted afterwards) painted three times:
        - Body, Details and Tyres got try 1;
        - the same paint again gave no new try, so the paint is repeatable to the digest;
        - with only the sidewalls changed, only Tyres got try 2.
      - 24 of 25 passed in Edge. The 25th expected two pictures for three tries, but tries 1 and
        3 look the same and rightly share one. The checks:
        - four stations;
        - a skin shown before the stations;
        - the address opens a station;
        - a click on a try changes the car and the label;
        - a note on a sidewall keeps "Tyres, try 2, not the newest", and the hook says so;
        - a station click turns the car;
        - a live paint in a subprocess: "painting…" on the stations being changed, then Tyres'
          new try marked New and named on the live line;
        - the round's switch keeps the station;
        - no sideways scroll at 1100 or 390;
        - no page errors.
      - TSC_CMYK_Brushed shown again: its tries kept, read with a 200 and no errors.
      - Step 9.1's 23 checks and the 14 drawing checks passed again, and the baselines are
        unchanged to the pixel.
      - **Speed:** the first visit's strip takes 5.7 s (6 pictures, not the timeline's 9); a
        second visit 1.6 s, the picture car not started.
      - **Standing still:** Edge used 1 to 13 % of a core over several runs, the page's own
        process 3 to 8 %. Counted WebGL draws: none while still, and a drag's drawing stops within
        5 s. The rest is the two cars' frame loops at 240 a second and the 1.5 s polls.
    - **Found on the way:** New never showed after a paint while the page watched. `seen` was read
      only when a skin opened. Now `fresh` holds what's new against what the page had before the
      paint.
    - **The strip, only the stations (the user, 2026-09-28):** asked what Cam 1, Cam 2 and "In the
      game" were for, then: "I would remove cam 1 and 2 for now and remove the in game". The
      line over the car now says "in the game since …" for an installed car. The viewer's
      `views()` stays (embed only), unused. Step 9.6's screenshots had been meant to go under
      "In the game": if that step happens, ask where they go.
    - **No flash on a reload (the user, 2026-09-28):** "when i hit reload, the original viewer that
      is the library of cars, loads and then flicers a bit and then the lab page loads". The
      embedded viewer shows its own page until its script adds the embed look, then the stock
      car until the Lab dresses it. A cover in the Lab's colour (`#stCover`, and `#prCover` for
      the UV map room's car) hides the car's space until the car is dressed, framed and turned,
      then fades in 0.25 s. It lifts even if loading fails. Checked in Edge, 7 passed: on a first
      load and on a reload the cover lifts only once the viewer is ready, in its embed look, with
      the strip drawn. The viewer itself didn't change.
    - **The load (the user, 2026-09-28: "it takes 8 seconds to fully load").**
      - **Profiled** in headless Edge at 2560×1300: a CPU profile of the page from the start to
        the cover lifting, and the car's files.
        - First visit: the car showed at 3.7 s. Of the main thread's 5.4 s, 2.5 s was
          `onFirstUse` (waiting for the shaders to compile), 1.3 s `texSubImage2D` (decoding and
          uploading the textures) and 0.4 s decoding the HDRs.
        - Reload: 1.5 s, the shaders cached.
        - The user's 8 s was most likely a first reload after the pictures' names changed (a
          repaint, or a new `viewer.js`): the picture car loaded beside the stage and slowed it.
      - **Now:**
        - the strip's pictures wait until the stage is shown (the picture queue starts behind
          the reveal);
        - the embedded viewer with no skin builds no stock car. The Lab's first dress builds the
          car, so no stock textures are loaded first and thrown away. `viewer.stock()` puts the
          stock car on for the UV map room when there's no skin at all.
      - **Measured:** first visit 3.2 s, reload 1.2 s. The rest of a first visit is the shader
        compile, which the browser keeps.
      - **Checks:** baselines unchanged; step 9.1's 24 checks, the 14 drawing checks and the 7
        reload checks passed; `stock()` checked on an empty viewer.
      - **Left for later if needed:**
        - decoding textures off the main thread (ImageBitmapLoader, embed only, 0.4 to 0.8 s);
        - loading only the day and night HDRs in the Lab;
        - `compileAsync`.
    - **Next:** the user tries it. Tries appear as cars get repainted: each car shown before today
      has one try per station until then.

### Defining the parts (started 2026-09-26, dropped 2026-09-28)

- **Dropped** (the user, 2026-09-28, asked whether it was still next: "Drop it"). What was done
  stays: the groups on top are the game's maps, the tail frame, floor edge and wing mounts as parts,
  the UV map picking surfaces.

Led by the user, step by step ("I honestly don't know how we are going to do this, but maybe we
can go step by step"). The steps are theirs; each is agreed before it's built.

- **Step 1, the top level** (the user, 2026-09-26): "the list of parts, at least the main ones
  are too broken down ... Wheel cover, Tyre, etc. should be in a parent category called Wheels.
  Same with body ... the parent of sidepod, engine cover, tail ... At least the external bits.
  Then there's Mechanicals (or some other name you think is best) which covers cables,
  suspensions etc." Then: "or we can have external body, and internal, or something. I don't
  know what would be best." Claude recommended groups by what a part is, not where: a brief
  names things ("gold wheels", "black suspension"), and outside and inside blur on this car (the
  suspension arms, the sidepod grilles, the exhausts and the floor are inner parts seen from
  outside). The user: "ok sounds good. Something to note is that I might be breaking things
  apart from the child after putting together the parent categories."
  - [x] **Built (2026-09-26).** `naming.GROUPS` over `naming.ASSEMBLIES` (each now names its
    group): **Body** (shell, sidepod, engine cover, tail, front wing, floor), **Wheels** (wheel
    cover, tyre, rims and brakes), **Mechanicals** (chassis, front and rear suspension, with the
    brake lines), **Cockpit** (the cockpit). The old assembly "body" is now "shell" and "wheel"
    is "rims and brakes", so no assembly is named like a group. The Glass assembly is gone: each
    glass piece joined the assembly it sits in, by its nearest parts (canopy and nose lens: shell;
    rear light and side lenses: tail; wing lenses: front wing; mirror glass and the gear display:
    cockpit). Every part carries its `group`; a group's name picks its parts (`Parts.select`,
    the viewer's `showParts`).
  - **Painting didn't change.** The paint box's words "body" (the paint set without the wheel
    covers) and "wheels" (no tyres) keep their meanings over the groups of the same name: the Body
    group also holds the floor and the black inner parts of the sidepods and tail, which "paint
    the body red" must not reach. An assembly or group leaves its glass out unless the glass is
    named, so painting the tail doesn't tint the rear light lenses. Checked: all 210 parts kept
    their triangles, texels and sides; 17 paint-box names picked the same parts as before; the
    Lab's four rooms hold the same parts.
  - The viewer's Parts list: the groups on top (open), their assemblies under them (closed); an
    assembly alone in its group and named like it (the cockpit) lists its parts right under the
    group. The Lab's part card says "Body › sidepod". Part ids changed order (by group), so the
    viewer's `car.bin` was rebuilt with `parts.json`. Checked in headless Chrome, 1440×900 and
    390×844: no sideways scroll, no page errors.
- **The floor** (the user, 2026-09-26): "I have a feeling we could separate the bottom floor, but
  at the moment it in details, but it covers the floor and front wings I believe." Measured on
  the Details paint (`coverage.twins()`): 47 % of each front wing's paint is the floor's (both
  sides), 4 % of the floor's is the wing's; the endplates and brackets share only with their
  twins. A throwaway car with only the floor red (removed) showed where: the whole underside,
  the floor's edge as a thin line along each side, and the flat panels on the front wing's top
  and its underside. The list can separate them; the paint can't (Nadeo's layout). The user
  agreed ("Sure. Let's do that for now"):
  - [x] **Built (2026-09-26).** Floor is a fifth group, after Body, holding the floor assembly
    (floor, planks, rail, rear diffuser); the viewer lists its parts right under it. The front
    wing stays in Body. Paint picks nothing new: "floor" named the same parts before.
  - [x] **The tie said aloud.** `Skin._warn_shared` used to note only a mirror twin with the
    same name. It now names every part not chosen that would take 5 % or more of its paint
    (`SHARED_NOTE`), from `coverage.twins()` at the paint's size, with how much: "floor: its paint
    also lands on upright (front left, front right: all of it), front wing (left, right: 93 %)".
    Measured with it: the whole floor covers 93 % of the front wing's paint (each half 47 %, so
    "about half" to the user was one half's figure); the wing's panels cover 9 % of each floor
    half. The front uprights sit wholly in the small patch many inner parts share, so painting
    the floor, the tail, the engine cover, the cockpit or the sidepod frames also paints them.
    1.7 s for 21 names, once per set.
- **What the floor holds** (the user, 2026-09-26, looking at it): "there's quite a few parts for
  the floor, you have the front wing left and right as well. And also you are including a big
  portion of the rear. That's not the floor." Seen with the floor alone, coloured by part: the
  "rear diffuser" (a rule cutting the floor's smooth piece behind z -100) was the frame the tail
  hangs on: the face round the speed numbers, the channels under it and two arms reaching
  forward, as big as half the floor. The front wing is not in the floor; it shows beside it
  where the tool lists who shares the floor's paint (the Lab's part card).
  - [x] **Moved (2026-09-26):** "rear diffuser" is now **"tail frame"**, in Body › tail (the
    tail had a "diffuser" already). Same triangles; the designs that named it
    (TSC_CMYK_BlackTail, TSC_FlagPeel_CostaRica, TSC_Stealth_CMYK, _Bold) and `tool/relief.py`
    say "tail frame" now; their notes keep the old name. The Floor group is the floor, its
    planks and the rail (a thin rod on top of the floor, ahead of the cockpit).
- **One-sided surfaces** (the user, 2026-09-26: "Are there non 3d elements in the model? the
  floor's center looks like a hole, but when I look from the bottom, it looks like a full
  object"). The model's surfaces are one-sided, as in games: the floor's middle (|x| < 25 cm,
  z -60..60, 11 cm up) is a sheet facing the ground (98 % of its area faces down; the whole floor
  part 69 % down, 28 % up: the rim has a top). The viewer draws front faces only (three.js's
  default on the car's materials), as the game does, so from above, with the car around it
  hidden, the middle vanishes and the ground's shadow shows through. Painting the floor paints
  its underside and the rim; there's no top to the middle, and nothing sees it from above.
- **The front wing joins the floor** (the user, 2026-09-26: "I still see the front wing objects in
  body ... All should be floor I would assume. Except for wing pylon. And wing bracket").
  - [x] **Built (2026-09-26).** Floor holds two assemblies: floor (the underside, planks, rail)
    and front wing (the wing, its endplates, its lenses). The pylons and brackets that hold it
    under the nose are Body's new "wing mounts". A group's name no longer picks its parts when a
    part or assembly has that name (`Parts.__init__`, the viewer's `showParts`): "floor" is still
    the underside, not the Floor group. "front wing" now paints the wing and endplates only;
    the eight designs that painted it (TSC_Camo, _IceCreamSweet, _IceCreamTruck, _Nebula,
    _RatRod, _Race, _Stealth_CMYK, _Tricolore) name ["front wing", "wing mounts"], the same
    parts as before (checked), and `tool/labskin.py` does the same by ids. TSC_Parts
    (`tool/partskin.py`) paints the tail frame grey as it did as the floor's.
- **Parts and surfaces** (the user, 2026-09-26: "Should we reconsider how we are separating
  things? ... we have parts and then we have surfaces, for example in UV map, there are
  "surfaces" that are visually separate but when I hover it hovers a lot of elements that are not
  even together"). Measured, per texel the parts' names covering it by 3/4 or more, at paint size:
  Skin 100 % and Wheels 100 % of the painted texels belong to one name (a part, its mirror twin,
  the four wheels); Details 99.2 %. The mixes: floor + front wing 0.75 % of the Details map (now
  one group), driveshaft + rear arm 0.02 %, body shell + mirror mount 0.02 % of Skin, and one tiny
  patch (under 0.005 %) that 15 names use (the front uprights wholly). So the parts are the
  surfaces, by name. The Lab's hover looks otherwise for two reasons: a part's paint may sit in
  several islands across the map, and a shared texel lights the part with every part it shares
  anything with (`hit()` in `viewer/lab-rooms.js`: `twins`), so the tiny patch ties the floor to
  about 17 parts all over the car.
- **Surfaces on the UV map** (the user, 2026-09-26: "I've seen many car skins that have the
  surface that go around the floor. That surface they something paint it to glow for example.
  But in the uv map, I can't select that surface because it selects almost all details surfaces
  ... in the 3d to select parts, but in the uv map to be able to select surfaces").
  - [x] **"floor edge"** (2026-09-26): the band round the floor's side, its own crease-bounded
    piece (1446 and its twin 1455, 677 cm² each, 44 % facing out, z -110 to 194), taken from the
    floor. Its paint is its own, shared only with its mirror twin; it can glow (Details). A test
    car (removed) with it glowing cyan showed the thin line along each side.
  - [x] **The UV map picks surfaces, the car picks parts.** A surface is a shape the Lab outlines
    on the map: touching texels with the same part on top (`view._surfaces`; touching texels
    alone merged the body shell with the cockpit surround, and every tyre's paint into one).
    Each lists the parts that cover 3/4 of its texels on 16 or more (`coverage.sets`; a seam's
    texels are half each side's). 48 on Skin, 511 on Details, 3 on Wheels, 20 on Glass; only
    three Details surfaces hold more than one name (floor + front wing, driveshaft + rear arm,
    and the tiny patch of 15 names). `<Set>_Surfaces.png` numbers them, grown 2 texels into the
    gaps; the viewer lights one on the car by that map (`viewer.lightSurface`, a shader test on
    the part's UV), so the car shows exactly where the paint goes, not whole parts. The card
    gets a "Surface" row, and the copied line names the surface. Checked in headless Chrome:
    the floor edge's strip lit alone on the map, "floor edge (left, right)", and on the car
    the line along both sides.
- **Back to the game's maps** (the user, 2026-09-26: "Thing is that I'm overcomplicating the
  interface. I think we can just for now go back to the default, Body, Details, Tyres, Glass. I
  don't think we need a tab for lights because for each we can just have a picker. I'm just trying
  to simplify things because I think it's now getting over engineered. I do like the work you did
  for the uv map separating surfaces, that's going to be useful").
  - [x] **Built (2026-09-26).** `naming.GROUPS` are the four maps; a part's group is the map it's
    painted on (`GROUP_OF_SET`), so an assembly can sit in two (the sidepod's top in Body, its
    grille in Details). The groups by what parts are (Body, Floor, Wheels, Mechanicals, Cockpit)
    are gone; kept from that day: "tail frame" in the tail, "floor edge", "wing mounts", "rims and
    brakes", the glass in the assemblies it sits in, the shared-paint note, the UV map's surfaces.
    The viewer's list: the four groups, their assemblies; a short group (Tyres, Glass: 10 rows or
    fewer) lists its parts right under it.
  - [x] **The Lab's rooms are the maps too:** Body (Skin, wheel covers included now), Details
    (all of it, rims and brakes too), Tyres, Glass, each with its one map. The Lights room is gone
    (and `rooms.glowing`): every room has the Day/Night picker (sunrise and sunset shown, not in
    the viewer yet). Cameras: Body and Details as picked; Tyres the Wheels room's, framing the
    front left tyre; Glass has Body's until the user picks one. Old addresses ?room=wheels and
    ?room=lights open Tyres and Details. Painting picks the same parts as before (checked). Checked
    in headless Chrome: the viewer's list, each room, Details at night, 390 wide with no sideways
    scroll.

### The viewer matched to the game's moods (done 2026-09-27)

The user, 2026-09-27: "a car that will help you calibrate the moods? Something I can do later
with my pc", then, on the Mac: "maybe you can compare the 4 moods that trackmania has. I am not in
my pc but maybe you can create the calibration car?" The item is in `IMPROVEMENTS.md`.

- [x] **1. The calibration car, TSC_Calibrate (2026-09-27, on the Mac).** A test chart where the
  chase cameras see it standing still: the grey scale on the tail's flat top, six colours on the
  deck beside the engine cover's panel, four finishes beside the cockpit, a row of the five glow
  kinds on the back under the tail, the rest one mid grey (the key: its `notes.md`).
  - **What the chase cameras see** (the viewer's Cam 1 and 2 at 2560x1440, with the parts
    coloured and lit one by one): the tail panel is the tail's flat *top* (y 62 to 65, facing
    up), not its back; the deck's sides are the "engine cover" part (|x| 20 to 58 cm, round the
    engine cover's and number's panels, where the game letters); the back face round the speed
    numbers and the two openings is the inner car's "tail frame" (74 % shared with its twin, so
    mirrored); its top bar (y above 48) is the one clean band across the whole back. Cam 3 sees
    the cockpit tub (its stock always-on slashes along the canopy's front), the steering wheel,
    the front tyres; the nose top only at a grazing angle. Anything long along the car is
    foreshortened about half from Cam 1, so patches there go side by side across the car.
  - **Glow patches on black paint:** `glow()` also tints the paint, so a "night only" patch read
    as lit by day; black paint after the glow leaves only the light. The digit display needs its
    dark paint too, or the unlit segments show "888" in the body's grey.
  - **`tool.snap <name> --cams`** (and `node docker/snap.mjs <name> --cams` on the Mac): the
    game's three cameras by day and at night at 16:9, the viewer's side of the comparison.
- [x] **2. The drive (the user, on the PC, 2026-09-27).** Installed, then each of the four moods
  standing still, F12 in Cam 1, 2 and 3 (the steps are in its `notes.md`; they worked as written).
  The user also took each camera's second view (the key pressed again): 24 screenshots,
  09:18 to 09:22, in the order sunrise, day, sunset, night, each Cam 1, 1 again, 2, 2 again, 3, 3
  again.
  - **How to get the four moods** (a lookup, 2026-09-27, untried): one map in the editor, its mood
    changed in Light settings ("calculate shadows and change the mood of your track"; Map Options
    → Edit Light Settings; Mood: Morning, Day, Sunset, Night), so the car keeps its spot and
    heading while the sun moves. The shadows (the lightmap) must be computed after every change,
    or the light isn't the map's; test mode is Enter, then a click where the car starts. The game
    adjusts its exposure by itself ("Stabilize autoexposure… especially on night", March 2023):
    wait a few seconds before F12. Official maps mix moods (Winter 2026: 02 Day, 05 Sunrise, 06
    Night, 07 Sunset) but each faces the sun its own way. Openplanet's mood plugins set any time of
    day, not the four moods: not for this. Sources: wiki.trackmania.io (map editor, settings
    menu), 22ndcorner.wordpress.com (map editor basics, 2020), the Maniaplanet docs on lightmaps,
    trackmania.com news 7444, 7901, 8256, trackmania.com/access.
- [x] **3. The match (2026-09-27).** The screenshots beside `--cams` renders at 2560x1440, read
  on Cam 2 (the closest to the tail): the grey scale on the tail's top, the deck's colours, the
  glow row. What it showed is under "Things we learned". The viewer maps light straight now
  (`LinearToneMapping`), by day at exposure 1.44 (greys within a few levels of the game's), at
  night 0.6 (a middle: the game's night light is uneven, see below), and `GLOW`'s gains are levels
  on the screen (the glow scale is 1 / the exposure). The Lab's balls take the same day look.
  Not matched: the finishes (their reflections are the stadium's in the game, the studio's here)
  and the light's direction (the game's sun lights one side; the studio all round). A trial tone
  mapping is `?tone=aces` (or neutral, agx) in the viewer's address.
- [x] **4. Sunrise and sunset in the viewer (the user, 2026-09-27: "lets add them").** Each a
  Poly Haven sky (CC0) chosen beside the screenshots: Belfast Sunset (Pure Sky) for sunrise, hazy
  with a low golden sun, and Qwantani Dusk 2 (Pure Sky) for sunset, a pink dusk. Both skies came
  out too purple on the car, so `LOOKS` takes a `tint` for each sky (`tintSky`, on its half
  floats at load): the white patch then reads 190, 190, 195 at sunrise (the game's 193, 194,
  196) and 241, 200, 195 at sunset (245, 199, 193). Exposure 0.48 and 0.6; `lights` picks GLOW's
  day or night column (sunset lights the night glows, sunrise doesn't); `keyFrom` puts the sun
  low, ahead at sunrise and behind at sunset (the game's sunset warmed the car's back), key 1.6
  there. The dark end stays lighter than the game's (black 40 against 20): the skies' bright
  horizons sheen on matte at the chase cameras' grazing angle.
- [x] **5. The moods in one menu (the user, 2026-09-27: "the interface is getting busy").** Day,
  Sunrise, Sunset and Night moved from four buttons into a drop-down beside Show, its button
  showing the mood picked (icon and name; the icon alone on a phone). Lucide's sunrise and
  sunset icons (lucide-static 1.48.0, ISC), as the others.
- [x] **6. Cam 1 alt and Cam 2 alt; Cam 3 out (the user, 2026-09-27).** The Driving menu is now
  Cam 1, Cam 1 alt, Cam 2, Cam 2 alt (each camera's key pressed again). Fitted to the daytime
  screenshots (below, "fitting a game camera"); `tool.snap --cams` takes all four.

### The studio render (done 2026-09-27)

The user, 2026-09-27: "I want to make the studio render nicer", then "i kind of feel we need a
floor, it could still be studio like" and "Keyshot has always been a nice default background and
surface that i've liked". The item is in `IMPROVEMENTS.md`.

- [x] **1. A floor.** Six floors rendered on TSC_CMYK_Peel_More and TSC_IceCreamSweet, on a page:
  https://claude.ai/artifact/XdJVttMnJD4M8AyCXLqrCP. The user liked them all, but not the line
  where the floor bends up into the wall ("is there one that actually you can't tell the spheric
  to the background"), and asked for all of them in the viewer to pick from there. So the viewer
  has a **Floor menu** (`viewer/floors.js`, beside the moods; `?floor=` for snapshots, which keep
  today's otherwise; the choice is remembered in the browser, and the Lab's Studio follows it;
  hidden on the page online until the pick). Then the user: "was thinking like a matte floor with
  a bit of texture?", so the menu is a surface and a shade (dark, today's 0.035, or KeyShot's light
  0.2): as today, KeyShot, four matte textured floors (`SURFACES`: concrete Concrete034, fine
  asphalt Asphalt031, rubber Rubber004, speckled rubber Rubber001, ambientCG CC0, fetched by
  `view.ensure_floor`), a turntable 5.2 m across, a grid a metre apart. The light on the car is the
  same under all of them. Then the user's pick, tentative ("Maybe let's do. Matte, tiny bit grainy
  texture in the grid one, and the grid make it tiny bit smaller"): **the grainy grid**, the
  rubber's grain at 0.45 under a line every 75 cm (one under the car's middle), now what the viewer
  opens with (dark; the choice is kept under a new key, `tsc-viewer-floor-2`, so the pick showed on
  refresh). Then "Maybe make the whole thing a bit whiter but with some kind of vignette so that
  the buttons dont dissapear. and also I need the grid smaller in scale. but a bit farther
  covering": the light shade is now 0.34 (near white behind the car) with a vignette on the studio
  only (not the car: the paint stays true), centred on the car's middle on the screen; the buttons
  over it get a dark glass (`body.lightStudio`); the grid is a line every 50 cm (7 mm wide), fading
  between 8 and 13.8 m. Then "the vignette is very strong": now gentle, 0.6 of the grey by the
  corners (it was 0.2), since the buttons read by their glass; by day the car's name and the speed
  are in dark ink over the near-white studio (`body.brightStudio`, white again at night).
  The viewer opens on the grainy grid, light (`tsc-viewer-floor-3`). Next: the user confirms; then
  it's the only floor (snapshots, the Lab, the page online) and the menu goes, unless they want to
  keep it.
  - **"A bit of texture":** each matte floor averages the backdrop's grey (its colour picture
    divided by its own mean, so the rubber's blue cast goes too) and keeps part of the picture's
    contrast, a power of each texel's ratio to the mean (asphalt 0.4, rubber 0.6, speckle 0.36,
    concrete 1.3), with the normal map faint; no shine at all, and the grain fades out 4 to 13 m
    from the car.
  - **No line where the floor bends:** every floor but today's lights the whole cove as flat floor
    (the normal straight up, no shine), so it's one even grey up the walls, in every mood; the
    floors on it fade to see-through (concrete, grid) or to the cove's own grey (KeyShot's skin),
    and the concrete averages the cove's grey so no ring shows where it ends. Materials with
    `onBeforeCompile` need their own `customProgramCacheKey` when their code differs, or three.js
    reuses the first one's program; the fade distances are uniforms.
- [x] **2. Less haze by day (the user, 2026-09-27: "the car itself looks a little hazy, can it be a
  bit more dehazed?").** The calibration car from Cam 2 (`?lens=game`, 2560x1440) beside the game's
  screenshot: on the tail's top 76 % of the light came from the studio HDR all round and 24 % from
  the key, so the faces the key misses were nearly as light as the tops (its back 93 and 86 against
  the game's 29 and 40, the tyres 104 against 48). `LOOKS.day` now halves the HDR (1.25 -> 0.625)
  and gives the key 2.8 times (1.1 -> 3.08): the grey scale stays the game's (60 88 119 158 201 247
  against 53 80 114 158 204 247), the back 66 and 61, the tyres 74. 0.35 and 3.3 came closer still
  and looked harsh for a studio. The key's shadow softened to match (radius 3 -> 8), and the Lab's
  balls take the same light (`viewer/lab.js`).
- [x] **3. A day like the game's (the user, 2026-09-27: "its still a bit hazy", then "I think you
  also have a studio hdr, can it actually be day time but not realistic, something like in
  trackmania").** Day is now Kloofendal 48d Partly Cloudy (Pure Sky, Poly Haven, CC0, 2K), a blue
  sky with white clouds. Its sun (found as the brightest texel, three.js's equirect directions) is
  48 degrees up at (0.555, 0.742, 0.377), over the car's front left, where the key already came
  from: the key is the sun there (`keyFrom`), and the sky's own sun disc is cut to luminance 8
  (`sunless`: it held 48 % of the sky's light) so the sun isn't counted twice and the sky gives
  only the cool fill. Env 0.44, key 4.4 in 0xfffcf1 (the sky's blue and the sun's warmth even out
  on the grey scale): the calibration car's tail 64 91 123 161 206 253 (the game's 53 80 114 158
  204 247), N8 neutral (206, 207, 206), its back 43 and 38, bluish, as the game's (23 to 38), the
  tyres 29 (44). The Lab's balls alike; the studio HDR left the downloads (`view.HDRIS`).
- [x] **4. One studio, light or dark (the user, 2026-09-27: "To reduce load, we can have the grainy
  grid, and have the dark and light options").** The Floor menu is now a Studio menu, Light studio
  or Dark studio (`viewer/studio.js`, `?studio=`; the viewer, the Lab's Studio, the snapshots and
  the page online all stand on it, light unless picked). The other floors, their pictures, the
  mirror (`Reflector.js`) and the old cove and dark patch (`addRoom`) are gone; the grain is the 1K
  set now (a metre a repeat needs no more), and the page online carries it. The ground shadow is
  drawn only when a mesh is shown or hidden (its depth pass sees the car at rest anyway), not every
  frame.
- [x] **5. Every mood as the day (the user, 2026-09-27: "I would like to apply that approach to the
  other moods").** Read from the user's Cam 2 screenshots of the calibration car in each mood (the
  third of each six: 09:19:11, 09:20:20, 09:21:24, 09:22:09) beside the viewer's at 2560x1440
  (`?lens=game`), the tail's grey strip, its back face and a tyre:
  - **A sheen on the paint lifted every dark colour** in every mood (pure black 64 by day against
    the game's 53, 37 at sunrise against 17, 20 at night against 10) while the whites matched: the
    body's `specularIntensity` is now half (`SHEEN` 0.5, the Lab's balls alike). By day Black to
    N6.5 then read 81 117 158 204 against 80 114 158 204.
  - **Each sky turned so its glow is where the key comes from** (`envTurn`; three.js turns the sky
    the other way to the Euler: turn = the sky's sun azimuth - the key's). Sunrise's hazy sky had its
    sun on the horizon 76 degrees round from the key, sunset's dusk glow in front of the car with the
    key behind: -75.8 and 170. Night's sky has no moon (its brightest texel is a lamp on the horizon).
  - **Sunrise** env 1 -> 0.37, key 1 -> 5.8, cooler (0xf8f8ff): the strip 29 49 70 96 125 157 (the
    game's 17 38 60 86 119 157), N8 (155, 156, 161) against (155, 156, 160), the back 34 and 31 (21
    and 31; were 59 and 54). **Sunset** the sun lower behind the car (keyFrom y 0.45 -> 0.17), env 0.8,
    key 1.6 -> 8: the strip 22 49 75 105 139 176 (18 40 64 97 134 173), N8 (210, 165, 154) against
    (203, 162, 156), the back warm (97, 74, 66); the game's back is warmer still (85-107, 45-62,
    29-42), its sky bluer on the top than on the back. **Night** kept the user's brightness (the
    strip twice the game's) with deeper shade: env 4.4 -> 2.64, key 0.44 -> 1.5, a paler blue.
  - **The "deck" spot beside the engine cover's panel reads the game's lettering** (the player's
    "FCP 00", light grey) in Cam 2, not the deck's paint: so the 2026-09-27 note that at night "the
    deck and the tail's back face are 3 to 8 times brighter than the flat top" rests on the lettering
    for the deck; the back face at night is as dark as the top (10 and 22 against N5 20).
- [x] **6. One studio, the colour of the game's track (the user, 2026-09-27: "Maybe we keep one
  floor, but meet in the middle?", then "Or maybe just meet the color that the screenshots
  have").** No Studio menu: one room (`viewer/studio.js`, `FLOOR` 0.353 0.329 0.349 linear, a light
  grey with the track's faint warm-pink cast). Read on the road round the car in the user's Cam 2
  screenshots and the viewer's (four spots clear of the car, its shadow and the overlays): lit by
  the moods alone it read the track's colour by day (205, 198, 203 against 205, 200, 204) and at
  sunrise; each mood's `studio` in `LOOKS` corrects the rest (sunrise 1.02 1.07 1.01, sunset 0.918
  1.1 1.184, night 0.335 0.326 0.3: the car lit brighter than the game's at night, its surroundings
  as dark), so the floor reads 124 123 127 at sunrise (the game's 124 123 128), 155 129 129 at sunset
  (155 129 129), 54 52 56 at night (54 52 56). The car's name and the speed in dark ink by day and at
  sunset, where the floor is light; the vignette and the buttons' dark glass always.
  - **The Lab's numbers read "undefined" on this PC:** its materials data predated the fields
    (`tool.swatches` hadn't run here since); `PY -m tool.swatches --no-open` rebuilt it (72).
  - **KeyShot's ground:** the floor is the room's own matte grey, so there's no edge; a mirror
    (`Reflector`) under it shows through 22 % by the car and none 6 m out, drawn at half the
    screen's size, which softens it. `Reflector` takes the mesh's own +z as the mirror's normal:
    turn the mesh, not the geometry, or it mirrors sideways.
  - **The ground shadow** (B to F, in place of the dark patch): the car seen from the floor up
    with an orthographic camera, its nearness as darkness, blurred twice, in two layers (within
    90 cm, wide and soft; within 22 cm, tight and dark under the tyres). The depth pass must be
    depth-tested, or the car's top overwrites its underside and the shadow comes out faint. Drawn
    each frame for now; the final can draw it only when the car or its wings move.
  - **A shiny or satin floor catches the studio HDR's lamps** at a grazing angle (white blotches
    on the floor, lamps the grey room doesn't have): the floors stay matte and let the mirror
    carry the reflection.
- [x] **7. A finer floor grain (the user, 2026-09-27: "make the floor grain a bit smaller").** Four
  grains rendered in the viewer, side by side at true pixel size
  (https://claude.ai/artifact/J4TkiZkYFsa894qKXYfA4u); the user picked D: a repeat every 40 cm (was
  1 m), grey only, power 0.7 (was 0.45). Up close the rubber's picture carried lilac and beige
  blotches, now gone: the grain is each texel's lightness against the mean. A grain shrinks into
  the mipmaps fast: at the opening view a screen pixel covers about 4 mm of floor, so at 25 cm a
  repeat the grain was near plain grey; 40 cm holds with the stronger power. The floor's average
  colour stays the track's (within half a level across all four).

### The viewer on smaller screens, and its buttons (done 2026-09-27)

The user, 2026-09-27: "when the screen gets smaller, the viewer of the car shrinks and get's
distorted". Each choice was made from real renders of the viewer, side by side on one page
(https://claude.ai/artifact/KRjTpvGLtMhVKYkvgoB3Nm, the user's /visual-plan).

- [x] **The car framed by its own outline** (`frame()` and `outline()` in `viewer/viewer.js`), in
  the space the page leaves it: beside the list, between the name above and the bottom stack. The
  camera stays where the view puts it, so the car keeps its shape at any size; the zoom sizes the
  picture and a view offset centres the car's own outline there. Sized by the outline swept all the
  way round (24 turns at the view's height), so a drag never cuts the car on a computer, and never
  bigger than on a full screen (0.92, as before).
- [x] **A phone: the car closer (C, of three: "I'm ok with the phone for the car to not cover the
  full screen. Because right now it's too distant").** On a screen taller than wide the car grows
  past the width, 1 + 2.7 x (0.8 - width/height), nearly twice as big as before on a phone, its nose
  and tail off the edges; never more than 1.55 widths of its own outline, so the side views keep half
  of each wheel (all body on a phone; a pinch zooms out).
- [x] **The list folds under 1280 px wide (B, of three: it stays, it folds sooner, a slim list of
  pictures).** Below that the list cost the car size; the name stays on one line beside the buttons.
- [x] **The buttons (the user: "once the numbers start to change in the kilometers then the buttons
  kind of move around", "the buttons overlap on top of the views", Save picture "on the top right
  corner ... as an icon", "I don't think spin is actually necessary").** The speed above the pedals
  (B, of three: held still between them, above them, in the corner), its number three digits wide;
  the pedals, the views and the credit in one stack along the bottom (`#dock`), so nothing overlaps;
  Save a camera icon at the end of the top row, still yellow ("You can still have the picture icon
  as the accent"); Spin gone. Then: "remove the e.g copy cam X ... just have the alt ones ... rename
  them to Cam 1 and Cam 2", "maybe just have them without dropdown": the Driving menu and Copy Cam
  are gone; the game's closer cameras (cam1alt, cam2alt) are two buttons after Top, named Cam 1 and
  Cam 2. `tool.snap --cams` still draws all four. The menus on the light studio are solid now (the
  buttons' see-through glass rule reached their items).

### Tyre markings (done 2026-09-27)

The user, 2026-09-27: "You can actually change the mapping of the tyres. Can you research that and
provide a vast library of tyre markings to use". The research (two web searches and the mesh) is
under "Things we learned"; what was built:

- [x] **`tool/tyres.py`, the library: 95 markings, TY-01 to TY-95, in 11 families** (Formula 1's
  ring and its compounds 2011 on, Formula 1 before 2011, American racing, other single-seaters,
  endurance, bikes and touring cars, rally, drift/drag/karts, road and show, fun, treads). Each is a
  layout function after a real tyre's, in our own words and shapes: the maker's name is OXIDE on
  every one, the models' names change with the family (BOX BOX, CHECK, CODEX, ECHO, HEX 8...), all
  flip-proof. Codes never reorder (as the Lab's finishes). Hex colours per compound from the
  research, judged from photos (no series publishes them).
- [x] **Drawn on the tyre's own map, not in 3D.** The map is separable (each row is an angle round
  the wheel, each column a radius or a place across the tread), so a marking is drawn as seen on the
  car's left, in cm from the axle and degrees clockwise from 12 o'clock, sampled 4 x 2 per texel,
  and each face (outer, inner sidewall, tread) replays the same calls. Lettering and symbols are
  masks at 60 px/cm placed along the arc (their verticals radial). Nadeo's sidewall lettering (NADEO
  on the inner face, three marks near the outer bead) comes off, in colour and relief, by setting
  each sidewall column to its median round the tyre; a tread pattern does the same to the tread.
- [x] **Relief in `Wheels_N`**: raised letters (0.6 to 1 mm, a 0.5 mm bevel), grooves (tread
  patterns: grooved, rain, inter, gravel, snow, mud, asphalt, ribs, diamond, semi-slick, lugs), studs.
  The paint box's Wheels canvas now keeps a normal map (`Canvas.normal`) and ships it.
- [x] **`s.tyre_marks("TY-07", colour=..., words=..., reads="left")`** in the paint box.
- [x] **The pictures: `PY -m tool.tyres`** (`tool/tyresheet.py`): each marking on the car with the
  wheels a plain dark grey (`TyreLib_<code>` in the viewer's data, no gallery lists it), the front
  wheels from both sides and the rear tread from behind, one Edge session (`viewer.load()` swaps
  skins in the page); `build/tyres/library.png`, and the page (`viewer/tyres.html`, filled by
  `tyresheet.page()`) published privately for the user: https://claude.ai/artifact/2TdLiRLDGKxUkMiKBo89ko
  (republish to that link, with `url`, when the library changes).
- [x] **The tread library, in the Lab's materials (the user, 2026-09-27: "In the material library,
  can we add a tread library as well?")**: `tyres.TREAD_LIBRARY`, TR-01 to TR-13 (Nadeo's own, slick,
  grooved, wet, intermediate, rally asphalt, gravel blocks, snow studs, mud lugs, semi-slick, ribbed,
  vintage diamond, round lugs), a family "Treads" in the Materials room. Each is on the car's own
  tyre rather than a ball: `tool.swatches` writes the tyre's cross-section (`tyre.json`, from the
  map's columns) and each tread's maps as the paint box paints them, turned so a lathe reads them
  (round the tyre along u, across it along v, the normal's channels swapped to match), with Nadeo's
  shading as the ambient occlusion; `viewer/lab.js` turns the section on a lathe, the axle across the
  picture and the tread filling each tile (the whole tyre rolling in the big view). A first try, the
  whole tyre small in each tile, read as a dark ring with no pattern. Treads have their own stamp,
  so changing the tyres' code repaints 13 tyres, not the 73 balls. `s.tyre_tread("TR-04")`, and any
  marking's `tread=` takes a TR code.
- [ ] **In the game** (IMPROVEMENTS.md, "To check in the game"): the first skin that uses a marking.

### The design studio (started 2026-09-28)

A way of building cars the way a real car studio does: from the car's idea to the last detail,
with a stage for each kind of work, an expert for each stage, and the Lab showing where the car
is. Planned 2026-09-28 in a chat with the user (as `STUDIO_PLAN.md` on the branch
`claude/car-design-workflow-wzexkl`, moved here the same day) and agreed: "Lets just go with that,
and see how it goes".

The user's words that started it (2026-09-28): "What's important is to actually have this as an
incredible workflow that builds cars (not the typical amateur skins) but actually work on every
single detail from start to finish."

The user's answers:

- **Three ways in** (2026-09-28: "both, and also make changes to an already existing car"):
  a quick way, the full studio, and reworking a car that already exists.
- **When the user decides** (2026-09-28: "any stage that needs a choosing of direction"): the user
  signs off wherever there is more than one real direction to go. Claude handles the rest and
  shows it, and the user can still leave notes on anything.
- **Cars made the old way stay as they are** (2026-09-28, while W1 was being built: "I don't want
  you to get influenced by previous builds, so if a build is done the old way, I would just have a
  standard view how we have it for notes or something. Or whatever you think"). Claude's reading,
  made the rule: a car made the old way (every car before the studio, and every quick car) keeps
  the Lab's stand and its notes, with no build sheet pieced together from its history. A studio
  car starts from a blank sheet and its brief, under a new name, and borrows no looks from
  earlier cars unless the user names one; what the game taught about the car itself (the experts'
  guides, "Things we learned") still counts. Then: "I guess lets focus on first time building, we
  can later figure the already built". So the studio is for cars built from the start, going back
  to a step included; taking an already built car further (Rework, a quick car into the studio)
  is for later.

An improvement to the tool, not a new checkpoint: queued in `IMPROVEMENTS.md` under "Under way".
It takes in the Lab's remaining steps (9.3 to 9.6): see "How this fits with what's there".

#### The three ways in

| Way | When | What happens |
|---|---|---|
| **Quick** | A clear, small idea ("make the wheels gold", "something with flames") | Same as today: words, pictures, changes, yes, in the game. Minutes. Stays on the Lab's stand with its notes; moving it into the Studio is for later (the user, 2026-09-28, above). |
| **Studio** | A new car the user wants done properly | All the stages below, from the brief to the release. About an hour or two, spread over a few decisions. |
| **Rework** (for later: the user's answer above) | An existing car that should be taken further, or changed in a big way | Starts with a teardown of the car as it is (below), then goes back to the stage the change belongs to. Everything before that stage stays settled. |

Claude suggests a way from the user's words and says which in one line ("I'll take this through
the studio"). The user can always ask for the other.

#### The stages

**Three since 2026-09-28** (the user, after trying the wizard: W3 below): Brief, Concepts (with the
mood inside it), and The car (everything after, on the car from the user's notes, then the critic,
the road test and the release). The stages below are the plan as first agreed, and TSC_Ladybird's
steps; `studio.md` has the three.

Each stage has a job, an expert, what the user sees, and whether it is usually a decision
point. The rule for decisions: **a stage stops for the user whenever there is more than one real
direction.** When there is only one sensible answer, Claude does the stage, shows it and moves
on. The user can still leave a note on it, which reopens it.

A stage that is decided stays decided. Going back to a stage reopens that stage and the ones
after it, never the ones before.

##### 1. The brief

- **The job:** agree what this car is before anything is painted. Its character in a few words
  ("a night-time endurance racer, calm but dangerous"), 2 or 3 reference ideas (a real race car,
  a product, a place, a film), what it must **not** look like, and anything fixed (a colour, a
  word, a number).
- **The expert:** the design director (Claude, the voice the user talks to).
- **What the user sees:** a one-page brief card on the Lab, in plain words.
- **Decision:** always. The user approves the card or changes it. Every later stage is checked
  against it.

##### 2. Mood

- **The job:** turn the brief into a look before it touches the car: 2 or 3 mood boards, each a
  wall of pictures, a colour story (the main colour, the support colours, one accent), and the
  kind of finish (raw carbon and matte, or deep gloss and chrome).
- **The expert:** the mood and research designer.
- **What the user sees:** the boards side by side, each with a name and its colours as chips.
- **Decision:** always, for a new car: pick a board, or say what to take from each.

##### 3. Concepts

- **The job:** 3 truly different ideas on the car, rough on purpose: flat blocks of colour, no
  detail, no finishes yet. Different readings of the brief, not three shades of one.
- **The experts:** three concept designers, each working on one idea at the same time.
- **What the user sees:** the three cars side by side on the stand (A, B, C), from the front,
  the side and the game's camera.
- **Decision:** always. Pick one, or mix ("A's shapes with C's colours"). Once the user picks,
  the other ideas are deleted (the user's rule, 2026-09-28); git's history keeps them.

##### 4. Shapes

- **The job:** refine the chosen idea's big shapes: where the stripes, blocks and graphics sit,
  how they follow the car's folds and edges, and how they read from far away, at speed, from the
  game's cameras and in a small picture. A good car reads in half a second.
- **The expert:** the livery designer.
- **What the user sees:** the car from the game's cameras, a small "from far away" picture, and
  the car from the side.
- **Decision:** only if there are real alternatives (the stripe over the top or along the sides).

##### 5. Colours and materials

- **The job:** the finishes. Which parts are matte, satin, gloss, metal or carbon; the contrast
  between them; the exact colours; how it all looks by day and at night. This is the materials
  library's stage.
- **The expert:** the colour and materials designer (what car makers call CMF: colour, material,
  finish).
- **What the user sees:** the car with a day and night switch, and a board of the car's finishes
  as swatches, each one clickable to copy for Claude (as in the Materials room).
- **Decision:** usually, when there's a real choice (gloss or matte, warm or cold metal).

##### 6. Details

- **The job:** everything that separates a finished car from an amateur skin, station by
  station:
  - **Details:** the inner car, the suspension, the floor, the fasteners, the lights and their
    colours, the glows at night;
  - **Wheels and tyres:** covers, rims, the tyre marking and tread, as one piece of work (the user,
    2026-09-27: "the wheels in general is a full workflow as I build cars");
  - **Lettering and badges:** numbers, words, logos, the typeface, and where they can go;
  - **Glass:** its tint.
- **The experts:** the detail designer (inner car and mechanics), the wheels designer, the
  typography and badges designer.
- **What the user sees:** the stations under the car (Body, Details, Tyres, Glass), each with its
  tries, and close-ups of each area.
- **Decision:** the wheels, always (the user settles them car by car). The rest only when there
  are real alternatives.

##### 7. Review

- **The job:** a critic who did not design the car checks it, with fresh eyes, against the brief
  and a quality list:
  - does it still say what the brief says?
  - does it read from the game's cameras, at speed, by day and at night?
  - anything cut, stretched, soft or crooked where graphics meet a fold, join or edge?
  - paint left over from an earlier idea, or parts left as clay by accident?
  - words that read backwards on one side?
  - the game's rules (the number panel free, the file size).
  Claude fixes what the critic finds, and the critic checks again.
- **The expert:** the critic.
- **What the user sees:** the critic's findings as tags on the car, each one marked fixed with a
  before and after.
- **Decision:** none. The user just sees what was found and fixed.

##### 8. Road test

- **The job:** the car in the game. The user drives it by day and at night, uses brakes and turbo,
  and takes a few F12 screenshots.
- **What the user sees:** their screenshots in the Lab, with notes on them.
- **Decision:** always. Yes, or what to change. A change reopens the stage it belongs to.

##### 9. Release

- **The job:** the car is final: in the game, on the page online, and in its design book: a page
  telling the car's story, from the brief and the mood board, through the concept that was picked,
  to the finished car.
- **What the user sees:** the design book, which they can share with friends.
- **Decision:** none.

##### Rework: the teardown

For later (the user's answer above: first-time building comes first). For an existing car, before
anything changes:

- the critic goes over the car as it is, with the quality list above;
- Claude sets that beside the car's brief (a studio car has one; for a car made the old way, how
  to go about it is to be figured out then);
- the user sees both, and says what stays and what's open ("keep the colours, redo the
  lettering");
- the car enters the Studio at that stage. "Redo the lettering" starts at Details; "make it feel
  more aggressive" starts at the brief.

#### The experts

**Stages and an independent critic matter more than how many agents there are.** A crowd of
agents talking to each other would be slower, more expensive and contradictory, against the
user's "small and simple". So:

- **The design director** is the main Claude session. It is the only one that talks to the user,
  keeps the brief, and holds the car together.
- **The specialists** (mood, livery, colours and materials, details, wheels, typography) are
  know-how, not separate chats: one short guide per stage that the director loads when the car
  reaches that stage. Each guide says what good looks like in that field, what to check, and the
  tool's abilities and limits for it. This is where "expert in each field" really lives, and it
  grows with every car (what the game and the user teach).
- **The three concept designers** are real parallel agents, each given the brief and the mood
  board and asked for one idea. This makes the concepts better and costs no extra waiting.
- **The critic** is a real separate agent, given the car's pictures, the brief and the quality
  list, never the design itself or Claude's reasons. Being independent is the whole point: today
  the designer checks its own work.

#### What the user sees in the Lab

**Decided (the user, 2026-09-28: "Lets just go with that, and see how it goes"): the wizard,
below.** The three first layouts (https://claude.ai/artifact/4RxUASJaYTfphRZbk1gFtG: a line of
stages, the car's sheet, a decision drawer) led to it. Quick cars keep the stand as it is today.

##### The wizard (the user, 2026-09-28)

After the three layouts, the user liked the concepts screen ("feels like a wizard"), and asked to
imagine it as a Trackmania skin builder that other people could use one day, with each step
showing its options in its own format, not the same pictures every time. And: "what would happen
if I want to change an existing, or go back and make a change (what's the non linear process)".

Claude's answer, drawn as screens (https://claude.ai/artifact/JHwbvVDKNTCiHTGepPQB2F, a new car
"Press Run": brief, mood, concepts, colours and materials, wheels, and going back to change the
wrap):

- **A decision takes over the page,** as in the concepts layout: a question, its options, "Or tell
  Claude in your own words", Back and Next.
- **The build sheet on the left** is the wizard's map and the way back: one line per step with
  what was decided, and a small picture of the car so far (once there is a car).
- **Each step shows the smallest thing that settles its question, then the whole car to
  confirm:** the brief as a conversation, then its card (the user, 2026-09-28, while W1 was built:
  open ended, "I don't want a complete form to fill out"); mood as boards; concepts as three whole
  cars; colours and materials as one car with a day and night split and the finishes as swatches;
  wheels as a row of wheels close up, then the pick on the car by day and at night.
- **Going back:** click a step on the sheet. Later steps are kept, not wiped: Claude carries the
  later picks onto the change, marks only the steps it affects as "needs a look" (a new wrap
  colour touches the lights and the lettering, not the tread), and shows the whole car before and
  after. A change is tried next to the current car, and the one not kept is deleted.
- **A car taken further** (for later) opens on its sheet, every step decided, and goes straight to
  the step the change belongs to. A car made the old way has no sheet: it opens on the stand with
  its notes (the user, 2026-09-28).
- **The steps:** Brief, Mood, Concepts, Shapes, Colours and materials, Wheels, Details, Lettering,
  Review, Road test, then Released. Wheels and Lettering are steps of their own (in the stages
  above they sit inside Details).
- **Notes on the car still work at any time,** on the stand as today: a note lands in the step it
  belongs to (a note on a wheel reopens Wheels).
- **Other people using it one day** would need hosting and would cost money per user: a
  separate decision for later. The wizard works either way.

#### How this fits with what's there

Most of the machinery exists already. The studio mostly adds order, the brief, the experts' know-how
and the critic.

| Stage | What the tool has | What's new |
|---|---|---|
| Brief | the user's words in each skin's record | the brief card, kept with the skin |
| Mood | the picture maker, the textures library, the finishes library | mood boards and colour stories |
| Concepts | rounds of A, B, C in the Lab, the switch between them | three parallel designers; the three cars side by side on the stand (the Lab's step 9.4, options on the car) |
| Shapes | the paint box, the zones, the spots, the game's cameras | a "from far away" check |
| Colours and materials | the finishes library and its codes, day and night | the car's finishes board |
| Details | stations and tries, parts, tyre markings, glows, lights, lettering | the details guides |
| Review | Claude's own check before showing, the close looks | the independent critic; its findings as tags with before and after (the Lab's steps 9.3 and 9.5) |
| Road test | screenshots read after an install | screenshots in the Lab with notes (the Lab's step 9.6) |
| Release | install, the page online | the design book |

The Lab's step 9.7 (repainting only the station that changed) is separate and still worth doing:
it makes every stage faster.

#### Watch out for

- **Speed.** The studio is slower on purpose. Keep Quick as fast as it is today, and keep every
  stage honest: if a stage adds nothing on a car, skip it and say so.
- **Unused screens.** The Lab's separate rooms went unused (2026-09-27). New views live on the one
  stand and appear only at their stage.
- **Too many questions.** A decision needs a real choice between directions. Technical choices
  stay Claude's (CLAUDE.md).
- **Stages undoing each other.** A later stage never quietly changes an earlier decision. If it
  must, Claude says so and asks.

#### Questions for the user

1. Is anything missing from the steps, or unwanted (a "sponsors and branding" step, or one for the
   car's name and story)? Until the user says, the steps are as above.
2. The idea for the test, when W1 to W3 are done.

#### The build

In this order, each step built, checked, shown to the user, then ticked (as the Lab's steps are).
The user tries each one on a real car before the next. The Lab's steps 9.3 to 9.6 are folded in
here (answers with a before and after, options on the car, Claude's checks, the game's
screenshots); 9.7, repainting only the station that changed, stays as it is and helps every step.

#### [x] W1. The studio routine

- **Ticked 2026-09-28** (the user, asked whether to mark it done and start the wizard next: "Yes, but
  for another agent to pick up the experts"): every step's routine is in `studio.md`, tried once on
  TSC_Ladybird from the brief to the release (its install and the page online wait for the PC).

- **What it's for:** Claude can take a car through the studio in the chat, before any screen
  exists: the steps, the decisions, going back, and the three ways in (Quick, Studio, Rework).
- **What you'll see:** say "studio" with an idea, and Claude asks the brief's questions, shows the
  mood boards, the three concepts, and so on, one decision at a time, with pictures.
- **Model:** Opus 5.5.
- **Notes for Claude:**
  - A Studio section in the `skin` skill, used only when the user asks for the studio or a
    rework. The quick way stays exactly as it is.
  - The brief kept per skin (`skins/<name>/brief.md`).
  - **The build sheet as data:** `skins/<name>/sheet.json` (the name is free: `studio.json` is the
    Lab's timeline), written only by the tool's commands (`tool.sheet` or `tool.skin`
    subcommands): each step's state (to do, Claude on it, waiting for you, decided, needs a look),
    its decision in a few words, the date, its options (skin names), and the pick. A pick deletes
    the other options' folders (the user's rule, 2026-09-28). The Lab's rule: the page shows only
    this, never a list of its own.
  - **Going back:** a step's change marks the later steps it affects as "needs a look" (Claude
    decides which, and says why in a few words); the others stay decided. Claude carries the later
    picks onto the change and shows the whole car before and after.
  - **Rework** is for later (the user, 2026-09-28: "lets focus on first time building, we can
    later figure the already built"). No sheet is written for a car made the old way.
  - Mood boards: pictures from the picture maker (`tool.pictures`), the textures library and
    colour strips. Web pictures are references only, never on git or on the car.
  - **The pieces** (Claude's split, 2026-09-28, at the user's word: "Build one step at a time, show
    me what it does, and wait for my OK before the next step"):
    1. the build sheet (`tool/sheet.py`): the steps as data, options and the pick, going back;
    2. the brief: the Studio section of the `skin` skill starts (the three ways in, and how Claude
       says which), the brief's questions, the brief card (`skins/<car>/brief.md`);
    3. mood boards: a board picture per direction (the colour story as chips, the finishes, the
       textures, the picture maker's pictures);
    4. concepts to the release: the rest of the routine in the skill (three concepts, a "from far
       away" picture for Shapes, the finishes board, wheels, details, lettering, Claude's own
       review until W2's critic, the road test, the release) and going back, tried on a real car.
    A fifth, an old car's sheet pieced together from its history, was left for later the same day
    (the user's answer: first-time building first). Going back to a step during a build is in
    piece 4.
  - **1. The build sheet (built 2026-09-28):**
    - `tool/sheet.py`, standard library only, so it runs with the Mac's own python3 (3.9) as
      `tool.notes` does, in the container, and on the PC. `skins/<car>/sheet.json`: the car, its
      title, the user's first words, the start date, and the eleven
      steps (`sheet.STEPS`: brief, mood, concepts, shapes, colours, wheels, details, lettering,
      review, road, release), each with its key and name (for the Lab), state, decision, date,
      options, pick, why, and `was` (earlier decisions, so the page can say "changed" and the
      design book can tell the story).
    - **Commands:** `new`, `on`, `option`, `ask`, `pick`, `decide`, `skip`, `back`, the sheet
      printed (`tool.sheet <car>`) and every studio car (`tool.sheet`). The docstring is the key.
    - **Options** are skins (`<car>_<Title>`) or files in the car's folder (mood boards).
      `option` without `--skin` or `--file` makes the skin as a copy of the car's design.py and
      `art/` (a design's pictures are found by its own skin's name, so an option needs its own
      copy). `ask` wants two or more, each skin with a design.
    - **The pick** moves the chosen skin's design.py, `art/` and thumb.png into the car and
      deletes every other option (and the chosen one's folder), and takes them out of
      `skins/rounds.json` (a round left with one take goes). `pick none`: the car's design as it
      is, a mix Claude wrote into it. It refuses when the design the car ends up with loads the
      car's own or a deleted option's (designs load each other by folder name: it would break or
      load itself), and keeps an option that's in the game (`installed.json`). The work folder's
      copies of deleted skins are left: the gallery lists only folders with a design.
    - **Going back:** `back <car> <step> "<why>" --affects ...` keeps the old decision in `was`,
      makes the car as it is option A (for the steps that paint the car: concepts to lettering),
      marks the named later steps "needs a look" and review, road test and release too ("the car
      changed"). `decide` on a step that needs a look, without words, confirms its decision;
      after going back, a change made in the car itself (no other option) is decided directly.
    - **Only new cars:** `new` refuses a car that has a design (made the old way), since the
      user's answer; the `--rework` switch and the sheet's "way" went with it.
    - **Checks:** 40 passed (39, then the refusal of an old car), on the Mac's python3 3.9 and the container's 3.14, in a scratch
      skins folder (`TSC_SKINS_HOME`): the refusals (a design loading a deleted option or the car,
      fewer than two options, an option with no design, a bad letter, going back to a step not
      decided or marking an earlier step), a refused pick deleting nothing, the pick moving the
      design and pictures, an option in the game kept, the round forgotten, the car kept as it is,
      going back touching only the steps named and the checks, `pick none`, and the mood boards'
      files. A pretend car taken through all eleven steps, with a change of colour at the end,
      printed as expected.
  - **2. The brief (built 2026-09-28):**
    - The studio's routine is its own guide, `.claude/skills/skin/studio.md`, read only when the
      user asks for the studio; `SKILL.md` gained a short "The studio" section pointing to it
      and a line for `tool.sheet` in its commands. So a quick car's session reads nothing new.
    - `studio.md` holds when the studio is used (asked for, first-time builds, a new name, no
      looks borrowed from earlier cars), how it runs (a stop only for a real choice, each step
      checked against the brief, decided stays decided, the sheet kept true at every move, a
      commit after each decided step), and the brief. The steps after the brief come in pieces 3
      and 4; until then it stops at Mood.
    - **The brief, first as a form:** four questions in one go with the question tool, word
      choices drawn from the user's idea (the character, what it's drawn from, what it must not
      be, what's fixed). The user, before trying it: "I would prefer if it's just open ended?
      Similar to how other ai tools does that they like "what do you want to...", and then it
      reasons about it, maybe help shape the direction. But obviously I don't want a complete
      form to fill out".
    - **The brief, now a conversation:** one open question ("what car do you want to build?"),
      then Claude's reading of the idea in plain talk (the character, the worlds it could draw
      from, its traps, where Claude would take it), and at most one question in a sentence when
      there's a real fork, a round or two at most. Then the card, `skins/<car>/brief.md`, in a
      fixed shape the Lab can read (What it is, Drawn from, Not, Fixed): Claude's reading shaped
      by the talk, "Fixed" only what the user asked for, shown with "is this the car?".
      `tool.sheet decide <car> brief` refuses without the card (41 checks passed, on the Mac's
      python3 and the container's).
    - **Tried on the first studio car, TSC_Ladybird (2026-09-28), in three messages:** the user's
      idea (a fun car for the grass maps, not camouflage, "happy to figure it out as I go");
      Claude's reading (camouflage is the wrong job on a green map: start from things made to be
      picked out against grass, a jockey's colours, a golf flag, a ladybird) and one fork (stand
      out, or belong to grass sport); the user's turn on it ("the bottom is some lever of grass,
      that acts as the blend between the grass and the bug"); the card; "Sure, ladybird. We could
      potentially have a family of bugs". The idea came from the talk, not from either side alone.
    - **Found on the way:** the working name (TSC_Grass) stopped fitting once the brief settled.
      `tool.sheet rename`, only before anything is painted (designs and their pictures are found
      by folder name); 44 checks passed.
  - **3. Mood boards (built 2026-09-28):**
    - **A board is data:** `skins/<car>/mood/<slug>.json` (a title, a line, the colour story with
      roles and shares, the finishes as phrases in its colours, a wall of drawings and pictures),
      the build sheet's file option. The pick deletes the other boards with their pictures:
      `sheet.drop` takes a file option's companions (same name, other extension, and a folder of
      that name).
    - **`tool/mood.py`** paints each finish on a ball with the Lab's own code (`swatches.paint_ball`
      split into `paint_look`, any finish in any colour, and `write_ball`; the Lab's balls came out
      identical to the texel for eight finishes, and its stamp now repaints them once), copies the
      pictures, and writes `mood/<car>/boards.json`, lettered as on the sheet, with the brief's
      "What it is". Twelve balls in under a second. `--snap` photographs the page in Edge (the PC).
    - **`viewer/mood.html`**: the boards side by side in the Lab's look: the colour story as a bar
      on top, the letter and title, the wall, the balls, the chips. The balls come from
      `viewer/balls.js`, the Lab's ball code moved out of `lab.js` so both draw them alike (the
      materials room photographed before and after: the same to the pixel but for the big ball,
      which spins). Claude's drawings show as `data:` pictures, so their ids (gradients, filters)
      can't clash between drawings.
    - **`node docker/snap.mjs --page <page>`**: any page of the viewer's, whole, once its
      `window.mood` or `window.lab` says ready: how Claude looks at the boards on the Mac.
    - **Tried on TSC_Ladybird:** three boards, A Lacquer (candy red, piano black, black chrome, a
      lush fringe), B Racing colours ("red, black spots", a real set of jockey's silks; satin, a
      sharp graphic fringe, a saddle-cloth 7), C Field guide (matte vermilion, ink, paper, the Latin
      name as lettering, an ink-line fringe). The first look caught the ladybirds' pale head marks
      reading as cartoon eyes (the brief's "Not"), a caption cut off, an unclear jockey's cap, a
      lone fourth ball and gaps in two walls; fixed before showing.
    - **On the Mac the walls are drawings only:** the picture maker runs on the PC
      (`IMPROVEMENTS.md`, "The picture maker on the Mac").
    - **The user picked C, then "c and b actually".** B had been deleted by the first pick; it came
      back from git, Mood was reopened (`back`, the first pick kept in its history) and both boards
      kept: `pick` takes several letters for files (`A+B`), never for cars (a car keeps one
      design). The concepts draw on both. 48 checks passed.
  - **4. Concepts to the release (started 2026-09-28):** built step by step on TSC_Ladybird, each
    step's routine written into `studio.md` as the car reaches it.
    - **Concepts:** three designs as the sheet's options (`tool.sheet option` makes each
      `TSC_Ladybird_<Title>` folder), each rough: flat colour in its board's finish, wheels and
      inner car one dark colour. A Specimen (the Field guide board: a matte vermilion shell over
      the top with the seven-spot's spots, paper sides with grass drawn in ink over sage), B Silks
      (the Racing colours board: satin red, big bold black spots over the top and down the sides,
      a cream rail line with sharp turf teeth under it), C Anatomy (both boards: the car as the
      ladybird, a black head for the nose, the wing cases' seam as a black stripe nose to tail,
      the seven spots where they sit on the insect, green blades up the lower sides). About 25 s
      each to paint in the Mac's container.
    - **New in the tool:** `shapes.grass` (blades rising up the sides as seen from the side,
      filled or as ink strokes that thin to the tip; points bucketed along the car so a hundred
      blades cost little). The grass fringe is the brief's fixed element, and a family of bug cars
      would share it.
    - **What the first look caught:** spots placed without knowing the car's top were cut in half
      at the shell's edge (a map of the car from above in cm placed them: in `SKILL.md`, "What
      works on this car"); the shell as "whatever faces up" also took the lip at the bottom that
      turns up again, and its edge blurred over centimetres where the body curves gently (now
      `facing("up", 0.4, soft=0.006) & above(30)`); the ink grass was too thin and sparse to read;
      concept C's two pale marks on the black nose read as eyes (the brief: no face), so they went;
      B's turf barely showed until it rose to meet the rail line.
    - **Left for Shapes:** A's ink grass bunches into a barcode on the front flank; a small white
      piece on the bonnet (one of the car's own) shows on A.
    - **The user's pick:** "I like B the most. I do like the grass from C though", with a note on
      the car (written on C: "I like B but I cant see the vehicle ... The spot in b also transfers
      to the next object in the car, making it look weird and not properly applying pain").
      - **The mix** was written as option D (B's silks, C's grass in place of B's rail and turf),
        checked, and picked: its design became TSC_Ladybird's, A, B, C and D's folders went with
        the round, and TSC_Ladybird was shown under its own name. Nobody asked for the rail back.
      - **The spot:** a side spot projected across the car ran down inside a sidepod inlet, and a
        top one sat on the number panel. Spots now go on the outer panels only, placed clear of the
        inlets, the number and name panels and the nose fin's plate (their places, from the parts'
        texels, in `SKILL.md`). The fin's plate took two tries: a spot over it left the upright fin
        red, a notch; the plate painted black whole made a keyhole; the spot moved clear of it.
      - **"I cant see the vehicle":** the Lab's switch between the concepts was there (photographed
        on B), but the round was recorded after the paint, so a Lab already open showed it only
        after a reload. The routine now records a round before painting it.
      - **Found on the way:** `tool.notes done` refused a note on a skin the pick had deleted;
        it now takes any skin's name (the server doesn't use `done`, so no restart).
    - **Shapes, from the user's five notes (2026-09-28):** the spots as blobs (`shapes.blob`, new
      in the tool: a round spot whose edge wanders in a few slow lobes, projected from above or
      the side), the right deck spot moved off the deck's edge, the bonnet spot dropped (it touched
      the cockpit's rim, z 91), the nose the ladybird's black head (ahead of a curved edge, z 116
      down the middle, taking in the nose fin's plate) with two white blobs on its sides, the grass
      taller and denser. The white blobs took three tries: kept off "the top" they were slivers,
      kept to surfaces facing sideways they were half-moons, and at y 41 they hid under the nose's
      curve; at y 48, z 162 they show.
    - **Shapes, picked up in a new session (2026-09-28):** the routine written into `studio.md` (4.
      Shapes): the notes and the concept's rough edges fixed, the game's cameras looked at, a
      choice only where there's a real alternative. Found before showing: the grass fills
      everything low, so it made a solid green slab under the nose (the side skirt runs forward
      there as a flat ledge facing up, and the wing's pylon sits low) and blade tips on the nose's
      underside: it now stops where the head begins (in `SKILL.md`, the grass line). The white
      marks the user asked for read as eyes from the front three-quarter (the brief: no face):
      shown as a choice, A Round Marks as asked and B Streak Marks, each drawn out into a streak
      from the head's back edge, tapering forward along the nose's side. From the game's cameras
      the red and the spots read at once, even at Cam 1's distance, day and night; the grass and
      the head can't be seen from behind (they're for other players, replays and the garage).
    - **The pick:** "I would just keep with a and move on" (Claude had suggested B). A's design is
      the car's, B went with the round.
    - **The grass all round** (the user, reopening Shapes: "you need to include the grass where the
      black is as well.  The grass should be around the car"): the nose floats 41 to 44 cm up over
      a flat plate and the wing's pylon, so blades from the ground only reached it as stray tips.
      The head got its own fringe, short blades rising from its lower edge, and the plate a solid
      lawn (blades left black gaps across it). The back of the car is mostly the inner car's frame
      (Details); the body's rear corners carry the grass round. `back`, the change, `decide`.
    - **Colours and materials** (its routine in `studio.md`, 5): three finishes as options, the
      colours the same in all so the choice is the finish alone: A Beetle gloss (the brief's
      "glossy": shell, spots, head and marks under a clear varnish, the grass matte, so it reads
      drawn on), B Silks satin (the car as it is), C Painted wood (the Field guide board: matte,
      chalky black). The gloss's highlights run over the deck and the spots; nothing broke under
      the shine. The green against the game's own grass is left for the Road test.
    - **The pick:** "How about a but the grass make it a silky grass finish, so there's some
      contrast in the ladybug and the grass": A changed (the grass satin), then picked. With it, a
      note on the nose ("Why is the grass touching this object"): the head's fringe keeps a black
      gap round the white marks.
    - **Wheels** (its routine in `studio.md`, 6): three readings, the covers the big choice and a
      tyre accent from the car's colours: A Black legs (gloss black covers, plain glossy tyres), B
      Red shells (red cover discs, slick tyres), C Grass line (black covers, a thin turf stripe
      round each tyre, slick). The stock wheel rings glow cyan day and night (an "always on" glow,
      0.16 0.38 0.43): recoloured in each to fit. Lettered tyre markings don't paint on the Mac
      (Windows fonts; on the list).
    - **The pick:** "C" (the Grass line), as Claude suggested.
    - **Details** (its routine in `studio.md`, 7), one sensible answer, decided and shown: the inner
      car satin black, carbon underneath (the floor and the front wing, the tail's undertray and
      strakes), the frames round the inlets and the speed display gloss black; the speed numbers and
      the rear gear lights in the grass's green as a light (#60DC5A), what the driver sees all race;
      the glass clear. The tail frame, sidepod frames and rear strakes share a patch with the front
      uprights and a little of the floor: all dark, so nothing strays.
    - **Lettering** (its routine in `studio.md`, 8): A the Latin name (EB Garamond Italic, new in
      `tool/fonts.py` at the same pinned google/fonts commit, still the latest) along the front
      flanks, 4 cm tall, a specimen's label; B a cream 7 inside the black spot on each rear flank,
      the spot as the number's roundel; C none. The first tries: the name under the flank's small
      black fin (moved down), the 7 on the black nose read as an L from the front and risked a face
      between the head's white marks.
    - **The picks:** Lettering "c" (none). Then notes 7 and 8 on the front wing and the floor's edge
      ("probably this needs to be green", "Also this"): Details reopened, the floor and front wing
      green in the grass's satin.
    - **Review** (its routine in `studio.md`, 9), Claude's own until W2's critic: nothing in clay,
      graphics clean, reads from the cameras, panels free, a trial build in the Mac's container
      (`paintbox.build_zip`: 2.95 MB against 8.5, 86 s, so the size check needs no PC). Found and
      fixed: the diffuser's fins under the tail caught the grass as slivers (solid green now).
      Noted: the head's white marks read as eyes from above and the front (the user's choice).
    - **Road test** skipped at the user's word ("Let's assume it works"); its routine in `studio.md`
      (10) as it would run on the PC.
    - **Release** (its routine in `studio.md`, 11): the design book, a private page on claude.ai
      (https://claude.ai/artifact/436i2ACcm45oN5SVAsWuLL), the car's story chapter by chapter in the
      studio's look, the user's words at each decision and the options beside each pick; its page
      kept as `skins/TSC_Ladybird/book.html`, the model for the next car's. Its 27 pictures were cut
      from the rounds' picture sheets and the final snapshots (2.5 MB).
    - **Where it stopped (2026-09-28):** TSC_Ladybird's release waits for the Windows PC: install it
      (`tool.skin install TSC_Ladybird`), publish the page online (`tool.publish`), then `tool.sheet
      decide TSC_Ladybird release`. With that, W1's piece 4 has its routine for every step, tried
      once on a real car: show it to the user before W1 is ticked.


#### [x] W2. The experts

- **Ticked 2026-09-28** (the user, asked whether to mark it done and remove the trial cars: "Sure"):
  the critic, the step guides and the concept designers, each tried on the Mac. TSC_ConceptTrial and
  its three options deleted the same day (git's history keeps them), their round out of
  `skins/rounds.json`; TSC_CriticTest stays, the critic's test car. Left for the PC: whether two
  paints fit at once there (`TSC_PAINTS`).

- **Handed over 2026-09-28** (the user: "for another agent to pick up the experts"); W3 went to
  another agent too. For the agent who picks it up:
  - Best on the Windows PC: the three concept designers need three paints at once, which the
    notes below say to check there first, and the picture maker runs there. The critic needs only
    pictures, so it could start anywhere.
  - Where things stand: the studio's routine is `.claude/skills/skin/studio.md` (steps 1 to 11).
    Step 3 (Concepts) is where the three designers come in; step 9 (Review) is Claude's own review
    standing in for the critic, with the quality list the critic should use. TSC_Ladybird's
    `notes.md` and `sheet.json` are the one car built so far: its rounds, picks and review.
  - The user's rule for any build: one piece at a time, shown, and their OK before the next. Split
    W2 into pieces the same way W1 was split (for example: the critic first, tried on Opus 5.5 and
    Fable 5.1 on TSC_Ladybird's pictures; then the step guides; then the concept designers), write
    the split here, and show each piece.
  - Working beside W3's agent: pull before starting (the session hook does), commit and push after each
    piece. W3 owns the Lab's pages (`viewer/`); W2 owns `studio.md`'s Concepts and Review and the
    guides. A change either needs in the other's files (`tool/sheet.py`'s data, a new field the
    wizard should show, such as the critic's findings) goes in a note here first, so the other side
    sees it.
- **Picked up 2026-09-28 on the Mac** (the user: "Do the next job the agent bit"). **The pieces**
  (Claude's split, as the handover suggested), each shown to the user and their OK before the next:
  1. **the critic:** an agent given only the car's pictures and its brief; the pictures it needs;
     its findings kept for the wizard and the design book; tried on Opus 5.5 and Fable 5.1 on a car
     with known faults and on TSC_Ladybird, keeping the one that finds more real faults; the
     Review step of `studio.md` run with it;
  2. **the step guides:** one short guide per step (mood, shapes, colours and materials, wheels,
     details, lettering), loaded only at its step, seeded from "What works on this car" and
     "Things we learned";
  3. **the concept designers:** three agents at once at Concepts, each given the brief and the
     mood and asked for one reading; on the PC first, whether three paints can run at once.
- **For W3 (the wizard), the critic's findings as data:** `skins/<car>/review.json`, written only by
  `tool.critic keep` and `mark` (the shape in `tool/critic.py`'s docstring): the rounds (the critic's
  model, its verdict, its pictures' folder) and the findings (where on the car in words, the picture
  and the point in it, what and why, fix / improve / brief, open / fixed / left with Claude's words,
  and the critic's word on it at the next round). The before is the finding's picture in its round's
  folder, the after the same file in the next round's. Those folders are on the computer that ran
  the review, not on git (`build/critic/<car>/<round>/` on the PC, `.snap/critic/<car>/<round>/` on
  the Mac): if the wizard needs them elsewhere, say so here. `tool.critic picture` draws a round's
  findings (rings where the critic pointed, the after beside each) as a picture for now.
- **For W3, the concept round:** it's now recorded before any take is painted (the three designers
  paint at once, taking turns), so `skins/rounds.json` can name a take whose folder has no design yet;
  such a take has no entry in `gallery.json` until its first paint, and the Lab's switch lists it
  from the round. The wizard's Concepts step should show a take still being made as such.
- **1. The critic (built 2026-09-28, on the Mac):**
  - `.claude/agents/critic.md`: an agent with the Read tool only, given the brief card and a folder
    of pictures, never the design, the sheet, the notes or Claude's reasons. Its text: the role, what
    the pictures are, what the car is (so it doesn't flag the car's own relief, the number and name
    panels, the speed numbers), studio.md's quality list in seven (the brief, it reads, craft,
    leftovers, both sides, the game's rules, the whole), and a JSON reply (where, the picture and the
    point in it, what, why, fix / improve / brief, how sure); a re-check says fixed, not fixed or
    partly for each earlier finding. Agents load when a session starts: the trial's session gave
    general-purpose agents the same text, and `studio.md` says to do so in a session begun before.
  - Its pictures: the four sheets cut into 29 (`tool.critic pictures`), each read whole at 960x720 (a
    whole sheet is read scaled down by a third). `tool.snap --review` (`docker/snap.mjs --review`) is a
    new sheet of what the others miss: straight on (the face test), low from behind, under the tail,
    the underside from below the floor (the room isn't drawn from there, so it's dark), and the
    right-hand flanks. About 5 s on the Mac.
  - Its findings: `skins/<car>/review.json` (`keep`, `mark`; 12 checks passed on the Mac's python3 in
    a scratch skins folder: a round kept from a fenced reply, marks, a re-check, and five refusals),
    and `tool.critic picture`, a round's findings with a ring where the critic pointed.
  - **The trial:** TSC_CriticTest is TSC_Ladybird as it stood before its review (commit 7ce51ee)
    with four faults planted: seven known faults, listed in its design's docstring. Four critics at
    once, Opus 5.5 and Fable 5.1, on it and on the finished TSC_Ladybird, the pictures in folders
    named car-a and car-b; about 4 minutes and 85k tokens each.

    | Known fault on TSC_CriticTest | Opus 5.5 | Fable 5.1 |
    |---|---|---|
    | the diffuser's fins under the tail in green and red slivers (Claude's review) | found | found |
    | the front wing and floor dark carbon beside the green (the user's notes 7 and 8) | partly: "looks unpainted" | missed |
    | the head's white marks read as eyes (the brief's "Not") | found | found |
    | a spot on the number panel (planted) | found | found |
    | a spot cut at the sidepod's edge, merged with its neighbour (planted) | found | found |
    | the wheel rings' stock cyan (planted) | found | found |
    | the Latin name backwards on the right (planted) | found | found |

    Beyond the key, both found a real one on both cars that Claude's own review had called clean:
    below the flank's lower crease, where the body turns under, the grass blades become red slashes
    on green ("like scratches or tiger stripes"; from the front, flames). And the front hubs' orange
    glow at night, a stock light in no colour of the car's. Not faults: Opus's spots "grey" on flat
    panels (the room in the gloss) and the right side's "muddier" green (the viewer's light is on the
    car's left); Fable's deck spots "not mirror images" (placed so on purpose). Fable alone found the
    grass running inside the openings behind the sidepods and the tail's sides without grass; Opus
    alone the green blades murky over the rear flanks' black spots.
  - **Kept: Opus 5.5** (`model: opus` in the agent): every known fault, and the slashes as a fix it
    was sure of. The two together found more than either: if Opus misses things on later cars, a
    second critic on Fable 5.1 beside it costs no waiting.
  - TSC_Ladybird's review round 1 kept (Opus's): four findings left with their reasons, three open
    (the slashes, the murky blades, the orange glow) until the user says whether to reopen the
    car's Review. Shown to the user as the round's picture.
  - **The user's word (2026-09-28):** "I think at the end of the day this whole thing was a test
    car, so I would just move on to next": the three open findings left as they are (marked left
    with those words), and on to piece 2.
- **2. The step guides (written 2026-09-28, on the Mac):** `.claude/skills/skin/guides/`, one per
  expert: `mood.md` (the mood and research designer), `shapes.md` (the livery designer, for the
  concepts' big shapes and the Shapes step), `colours.md` (colour, material and finish), `wheels.md`,
  `details.md` (the inner car, its lights, the glass), `lettering.md` (typography and badges), 45 to
  58 lines each. Each: what good looks like in that field (from design practice: a direction you
  can say in a sentence, a colour story as proportions checked in greyscale, a hierarchy that reads
  in half a second, graphics that follow the car's lines and end at its edges, few finishes with
  finish contrast as hierarchy, structure receding and one detail speaking, a typeface as the car's
  voice); what this car and the tool allow at that step (from `SKILL.md`'s "What works on this
  car", the tool's docstrings and "Things we learned", pointed to rather than copied where
  `SKILL.md` already says it); what to check before showing; and "Learned", dated lines from the
  cars so far, TSC_Ladybird's and the critic's findings first. `studio.md` points each step at its
  guide ("Its guide: ...") and says to read it only then, and to add what the car taught at the end
  of the step, so the guides grow; the know-how its Wheels, Details and Lettering steps held moved
  into the guides, leaving the routine (the sheet, the options, the pictures). Every function and
  name a guide cites checked in the code. A quick car reads none of it. First real use: the next
  studio car (W4's test, if that comes first).
  - **The user's word (2026-09-28):** "Sure", with "Is that. big work? Just worried of your context
    window. I could have another agent to pick up": Claude's context was under a fifth used, so
    piece 3 went on in the same session.
- **3. The concept designers (built 2026-09-28, on the Mac):**
  - **Three paints at once killed two:** the Mac's container has 7.7 GB and a paint needs a few GB;
    TSC_CriticTest and TSC_Tiger died (exit 137) while TSC_Ladybird finished. So paints take turns:
    `tool/skin.py`'s `paint_slot`, an operating-system lock on a file in the work folder (fcntl in the
    container, msvcrt on Windows) around the paint and its export or zip, freed with the process if a
    paint dies; `TSC_PAINTS=<n>` gives more slots, for the PC once it's checked there. The same three
    at once then took turns and all finished (80 s). The Mac's snapshots each take a free DevTools
    port (Chrome's port 0, read from the profile's `DevToolsActivePort`): three at once took 14 s.
  - `tool.skin round` takes a studio option's folder before it has a design, so the round is recorded
    before any paint and an open Lab shows each take as it appears (`gallery.record_round`).
  - `.claude/agents/concept-designer.md` (Opus 5.5; Read, Write, Edit, Bash, Glob, Grep): given the
    car, its option's skin name, the brief, the board(s), its reading (a title and a line from the
    director), the other two readings to stay clear of, and the computer. It reads `SKILL.md`, the
    shapes guide and the tool's keys, writes only its option's `design.py` (a rough concept: flat
    colour in the board's base finish, the big shapes, wheels and inner car dark, no concept loading
    another, no looks from other skins), paints, looks at every picture (the review angles too, since
    the trial), fixes, at most three paints, and reports in plain words. `studio.md`'s Concepts: the
    director names three readings, makes the options, records the round, launches the three at once,
    then looks at each and fixes what they left before the picture.
  - **The trial:** TSC_ConceptTrial, TSC_Ladybird's brief and both boards taken through the sheet to
    Concepts; the three designers given the angles Claude had made alone for TSC_Ladybird (Specimen,
    Silks, Anatomy), to compare. All three at once: about 22 minutes for the round (11, 12 and 22
    minutes each), three paints each, 160k to 245k tokens each. Side by side with Claude's own
    round (the picture: `.snap/TSC_ConceptTrial_Specimen_picture.png`, not on git):
    - Specimen: better than Claude's: an ink rim drawn round the shell, a cream band across the tail
      so the idea shows from the chase cameras ("without it, the first paint looked from behind like
      any red car with spots"), the paper warmed so it doesn't read as clay.
    - Silks: bolder than Claude's (a few big spots, not polka dots), a clean turf band and cream rail;
      two faults it found after its last paint: the front spots may read as brows from straight on,
      and the rear ones dip over the deck's edge into kidney shapes.
    - Anatomy: close to Claude's, the head black with no marks (no face), the spots where the insect
      has them; left: the side skirt's ledge in front of the sidepods green from above.
    - All three found the same ledge on their own (now in the shapes guide). The readings were as
      far apart as Claude's, since the director gave the same angles; each car was more worked out.
  - Shown to the user as they came (not fixed by the director), with the comparison picture and the
    Lab's switch; deleted at the tick.

- **What it's for:** better options at each step, and a second pair of eyes.
- **What you'll see:** concepts that differ more and arrive together, and a review step with a
  list of faults found and fixed, each with a before and after.
- **Model:** Opus 5.5 to write the guides; the critic tried on Opus 5.5 and Fable 5.1 on the same
  cars, keeping the one that finds more real faults.
- **Notes for Claude:**
  - One short guide per step beside the `skin` skill (what good looks like, what to check, the
    tool's abilities and limits there), loaded only at its step, seeded from "What works on this
    car" and "Things we learned", growing with every car.
  - Three concept designers as parallel subagents, each given the brief and the mood and asked
    for one reading. Check first whether three paints can run at once on the PC (Edge, the GPU,
    the work folder): if not, the designs are written in parallel and the paints queue.
  - The critic as a subagent given only the pictures (views, close looks, the game's cameras, day
    and night), the brief and its quality list, never the design or Claude's reasons.

#### [replaced] W3. The wizard in the Lab

- **Replaced** (2026-09-28) by the fresh layouts' A, built as "Building A" (below); the wizard's
  code removed.

- **Handed over 2026-09-28** (the user: "Another agent will do the wizard"). Nothing built yet. For
  the agent who picks it up:
  - The screens' source isn't lost (unlike the note below says): the mockups' artifact
    (https://claude.ai/artifact/JHwbvVDKNTCiHTGepPQB2F) holds w1.html to w7.html and lab.css,
    readable with the Artifact tool's read and its `paths`.
  - The Lab today: `viewer/lab.html`'s rooms; `lab-studio.js` is the stand (`studio.json` names the
    skin Claude painted last; `steps.json` and `stations.json` per skin); the notes go through
    `/api/notes` in `tool/view.py`'s Handler, the page's only way to write, this computer only. The
    build sheet, `skins/<car>/sheet.json` (`tool/sheet.py`), isn't served yet: the server serves
    `viewer/` and the work folder's data, so the wizard needs a way to read it.
  - A pick deletes the options' folders, so a decided step keeps no pictures of what was offered;
    the wizard's history will need them kept (at `ask`, say). TSC_Ladybird's exist only in its
    design book (https://claude.ai/artifact/436i2ACcm45oN5SVAsWuLL) and the Mac's `.snap/` sheets.
  - The user's rule: one piece at a time, shown, their OK before the next. W2 is with another agent
    too: coordinate through notes here.
- **Picked up 2026-09-28 on the Mac** (the user: "Ok I think lab wizard is next"). **The pieces**
  (Claude's split; after piece 1 the studio went to three steps and pieces 2 to 4 changed: see below),
  each shown to the user and their OK before the next:
  1. **the wizard and its sheet:** a studio car opens in the Lab on its wizard (a room of its own,
     the stand one click away for notes on the car); the build sheet on the left from `sheet.json`,
     served; each step's page in a plain form (the brief's card, the options as cards with the car's
     picture, a decided step's decision and what was offered); a pick, an approval or words for
     Claude go through the notes channel with their step, and reach Claude at once while Claude
     waits for them; tried on TSC_Ladybird's sheet and a trial car at a real choice;
  2. **each step's own format:** mood as boards, concepts as cars that turn, shapes with the game's
     camera and a "from far away" picture, colours and materials with a day and night split and the
     finishes as swatches, wheels close up then on the car, details and lettering close up;
  3. **review and road test:** the critic's findings with a before and after, the F12 screenshots
     with notes on them (the PC);
  4. **going back:** "changed" and "needs a look" on the sheet, the whole car before and after, and
     the options' pictures kept so a decided step still shows what was offered.
- **1. The wizard and its sheet (built 2026-09-28, on the Mac):**
  - **What you'll see:** a studio car, or any of its options, opens in the Lab on a room of its own,
    "The build" (a car made the old way has no such room and opens on the stand, as before). On the
    left the build sheet: the eleven steps, each with what was decided, "your turn", "Claude on it",
    "needs a look" or "changed", and the car so far (a click opens it on the stand, "The car", where
    notes go). The step on show fills the page: "Step 3 of 11", its question in Teko at 44 px when
    it waits for you ("Is this the car?", "Which idea?"), else its name. A click on a step on the
    sheet shows it; Back and Next move along; the page follows the car's step again when Claude
    moves on.
  - **Each step in a plain form** (its own format is piece 2): the brief's card (What it is, Drawn
    from, Not struck through, Fixed, the user's words), or the user's words while Claude reads them;
    the options as cards, a car's gallery thumb or a mood board's colour story, first drawing and
    line, each with "On the car" (the option on the stand); a decided step's decision, its options
    marked picked or not kept, and what it decided before ("Before"); a step with no options shows
    the car now. Options whose folders a pick deleted show as their names only (their pictures are
    piece 4).
  - **Answering:** Pick on a card, "Approve the brief", "Keep it as it is" (a step that needs a
    look), and "Or tell Claude in your own words" (Enter) go as a note with `sheet` (the step, the
    pick and its title, or yes) and any words typed. The answer shows under the step ("You picked
    B · Sunny", then "Claude has it"), with "Take it back" until Claude has read it; a second pick
    replaces the first.
  - **Reaching Claude at once:** `tool.notes wait`, run by Claude in the background after an `ask`,
    ends as soon as a note comes and prints it as the hook does, which wakes Claude with no message
    in the chat (tried: the notification came as the note was written). `studio.md` says when.
  - **How it's built:** `sheet.find` (the car a skin is, or is an option of, now or in a step's
    history), `sheet.card` (brief.md read into its parts), `sheet.lab` (the sheet with the card, the
    step it's at, `ASKS`: each step's question and line, and the states' words) served as
    `/api/sheet?skin=`; `ask <car> brief` takes the card instead of options. `notes.add(sheet=...)`,
    a pick or a yes needing no words, on a car with a sheet and no design yet; the hook's line for
    it; `deliver` shared by the hook and `wait`. `viewer/lab-wizard.js`, its room and styles in
    `lab.html` (the mockups' look); `lab.js` opens it for a studio car and checks every 5 s whether
    the Lab's car is one; the stand leaves the wizard's answers off its tags. The cards take as many
    columns as make a 4:3 thumb biggest, side by side unless far smaller, no taller than 5:6 of their
    width (portrait cells cropped the cars to their middle). The page asks for the sheet and the
    answers every 2 s, only while its room is open.
  - **Checks:** 10 on the sheet (a scratch skins folder: the brief asked by its card and refused
    without, the card read with wrapped lines, `find` for the car, an option and strangers, `lab`,
    a question for every step) and 16 on the notes (a scratch notes folder: a pick, a yes, words,
    four refusals, the hook's lines, the stand's notes as before, `wait` ending on a note and giving
    up). In the Mac's headless Chrome, 24 on a trial car at its brief (the room, the question, the
    sheet, approve, Sent, take back, words by Enter, a later step, the address, Back, the stand and
    back, no sideways scroll at 390 and 1100, a car made the old way on the stand, TSC_Ladybird's
    mood with both boards picked, no page errors) and 10 at its concepts (three cars, a pick, its
    note, another pick replacing it with the words typed, take back, On the car).
  - **The trial car:** TSC_WizardTrial, TSC_Ladybird's brief and boards, and three stand-in concepts
    (TSC_WizardTrial_Red, _Sunny, _Tangerine: the Ladybird's design with its shell recoloured), not on
    git, to be deleted after the user has tried it.
  - **The user's try (2026-09-28):** "Approve the brief", then B Racing colours, then A Red, each in
    the Lab and each reaching Claude at once through `tool.notes wait`, with no message in the chat;
    Claude moved the sheet on after each. Found on the way: the car's own next step, not begun yet,
    said "Not yet" and was greyed on the sheet; it now says Claude starts it next, with the car now.
  - **The user's word (2026-09-28):** "It's kind of ok. But it feels like a lot of steps first of
    all. Im really not sure if Im overengineering all of this", and the pages with more words "looks
    really streteced ... I wonder if there's a bit of sapcing thta can help with breathing room"
    (the concept pickers looked fine). At their 2560 px the boxes ran 1,700 px wide: words now sit
    at a reading width (960 px at most; the options' cards keep the whole width), the brief's card
    on the left with the user's own words beside it, more padding and space between the blocks.
- **Three steps, and the car on the stand after the concepts (built 2026-09-28, on the Mac).** Claude,
  asked about the steps: on TSC_Ladybird the user decided seven times, and several steps split one
  piece of work in two; suggested five (Brief, Concepts with the mood inside it, Finish, Wheels and
  details, Check) and to cut before building more of the wizard. The user: "Yes, feels like a good
  call. I think after concept it does come to a point where I do refinements and details etc, and
  that could already as a 3d model where I can use the nice comment windows that we currently have,
  I really like that concept". Then, while the five were being built: "I would keep it simple,
  after concepts, I would just have the 3d car and you just make changes, with the comments pop up
  windows throught". So three.
  - **The steps:** `sheet.STEPS` is brief, concepts, car ("The car"); every command reads a sheet's
    own steps, so TSC_Ladybird's eleven still read and change. `STAND`, the steps the wizard shows
    on the car; `ask` on the car takes no options (the car itself, for a yes or notes); a pick on the
    car doesn't end the step (it joins its history, the car goes on), `decide` does, once the car is
    released. `ASKS` has a question for a pick and one for a yes.
  - **The routine:** `studio.md` rewritten for the three, all the old steps' know-how kept: the mood
    inside Concepts (each reading carries its world, colour story and finish: no boards, `tool/mood.py`
    and `mood.html` left unused; the concept designer is given its reading's colours and finish);
    on the car, Claude carries the work on field by field (the shapes, the finishes, the wheels, the
    details, the lettering, each with its guide), shows each on the car, acts on the notes first,
    offers a round only for a real choice (the wheels, which the user settles car by car); when the
    user is happy, the check (the critic, the road test) and the release.
  - **The Lab: one car room.** "The build" tab is gone: the car's room holds the stand, and for a
    studio car the sheet beside it and the step over it. The brief and the concepts are pages (the
    card, the cars side by side); the car step shows the car on the stand, its notes and stations as
    always, with "Happy with it", or, when Claude offers a round, the round's switch and "Pick B ·
    Red Covers" for the take on show. A card's "On the car" shows it on the stand, with "Side by
    side" back. A car made the old way is the stand alone. The wizard opens the stand only when it
    first shows it; while it's hidden the stand doesn't frame, follow or draw (no picture kept at the
    size of nothing), and it says which skin it shows (`lab:stand`). The tags' gutters are a fifth of
    the stage, 200 to 300 px, not of the window, so the car keeps its size beside the sheet.
  - **Checks:** 9 on the sheet (a scratch skins folder: three steps, the brief by its card, the car
    asked on the car and refused without a design, an option on the car, going back, TSC_Ladybird's
    eleven) and 3 on a pick on the car (its history, asked again, decided at the end); in the Mac's
    headless Chrome, 21 on the trial car at its car step (one room, the sheet and the stand, the
    question, a note clicked on the car kept with its point and not as an answer, Happy with it and
    back, Concepts as a page, On the car and back, the brief's card, 390 wide, a car made the old way
    as the stand alone, TSC_Ladybird's eleven with its release on the car, its mood's boards, no
    page errors) and 9 on a round of wheels on the car (the switch, the Pick following the take on
    show, the note, take back). The first run after restarting the Mac's container missed the note
    click once (the car still loading); it passed on the rerun.
  - **The pieces after this:** 3, the check (the critic's findings as tags on the car with a before
    and after; the game's screenshots); 4, going back and the history (the options' pictures kept).
    The old piece 2, each step's own format, went with the steps: the concepts' cards stay, the rest
    is the car on the stand.
- **Second thoughts on steps (the user, 2026-09-28, after the three were built):** "Im kind of second
  guessing around this step by step. Because I don't really work that way.. Don't know what to do".
  Claude: they work by reacting to the car (notes on it), so keep the studio's good parts as how
  Claude works (a short talk for a new idea, three different first ideas, every detail with the
  guides, the critic before the game) and drop the steps from the screen. The user: "Two main things
  I like. It's having the car and me being able to iterate. and I also like a place where you can
  provide options before building. Instead of you sending me images, etc. feels like there needs to
  be a place where I can pick options as I go. Because I might say, "can we try 3 different
  materials for X" Or I can say can you give me a few concepts for the wheels, or anything in a non
  linear way, and having a place where you show me and I chose and comment, is something nice to
  have."
  - **So the direction (Claude's reading, to be shown as mockups first):** no steps. The Lab is the
    car with its notes, plus a place for options: whenever Claude offers options, for anything and
    in any order (three materials for the sidepods, a few wheels, whole-car concepts), they show
    there as a set named by what it's about, side by side and each on the car, with a Pick and
    notes on each; open sets on top, picked ones kept as the car's history. Much of what's built
    carries over: the cards with a Pick (the concepts' page), the answers through the notes
    channel, `tool.notes wait`, rounds (`skins/rounds.json`) and their switch on the stand. The
    step list, the sheet on screen and the three steps would go.
  - **Fresh layouts (2026-09-28):** the user: "I do want to come back to the drawing board because
    the layout wasn't perfect in the past, lot's of stuff going around (apart from the comment
    thing, which I think was quite good). So I kind of want an agent to have a think and give me new
    fresh layouts". A fresh agent, given the user's words and the page's jobs but none of the old
    layouts to follow, made three (https://claude.ai/artifact/MWqNtBfhErGaBCLy9Sevb6, each at 1440×900:
    the car with notes, "Wheels · 3 ideas", a new car's 3 concepts): A, the car and a list (the car
    fills the page, every set of options in a list on the right, a click puts one on the car); B,
    one stage (the sets as buttons in the top bar, a set opens as three live cars side by side); C,
    the car over a shelf (a shelf of options rises under the car when a set arrives). Its pick: A,
    the smallest structure, nothing moving or changing shape. Everywhere: earlier picks kept small,
    the game's cameras as one "Game view" button, "in the game" a label, the materials library and
    the UV map off the page. **The user picked A** ("a", 2026-09-28).
- **Building A (started 2026-09-28, on the Mac).** No steps: any car can have **sets of options**,
  whenever the user asks, in any order; the studio and the quick way become one way of working.
  The pieces, each shown and OK'd before the next:
  1. **the page and its sets:** `tool/sets.py` (a car's sets in `skins/<car>/sets.json`: a set is
     painting, open, picked or dropped; a pick makes the picked option the car's design, keeps
     each option's picture for the history in `skins/<car>/sets/<n>/`, deletes the others), served
     to the Lab; the car's room as A: the car's name, "in the game" and Claude's status along the
     top; the big car with its notes, Day, Night and Game view; the list on the right ("For you to
     pick", a set being painted, "Earlier picks"), a click puts an option on the car, a Pick and a
     comment box on it, all reaching Claude at once; the stations' strip, the room tabs and the
     wizard gone (the materials and the UV map in the car's menu); tried on a trial car;
  2. **the way of working:** `SKILL.md` and `studio.md` made one routine (a new car: a short talk,
     three concepts as its first set; then the car and the user's notes, sets on request, every
     detail with the guides, the critic before the game), the build sheet and the wizard's code
     removed.
- **1. The page and its sets (built 2026-09-28, on the Mac):**
  - **What you'll see:** the Lab opens on the car. Over it, the car's name (a menu: the other cars,
    the materials, the UV map, back to the viewer), "In the game since …" or "Not in the game yet",
    and what Claude is doing ("Claude is painting · Wheels", "Waiting for your pick"). The car fills
    the room with the notes as before, Day, Night and "Game view" (the game's Cam 1) over it. On the
    right, "For you to pick": each set of options waiting, named by what it's about, with the user's
    words and when; each option's picture, letter and title; a click puts it on the car ("On the car
    · B · Red Covers · Wheels · 2 ideas", and "Back to your car"), with a box under it to say
    something about it; a Pick on each. A set being painted says so, its options appearing as they're
    painted. "Earlier picks" at the bottom, folded while something waits: each set's title, "You
    picked A · Red · 4 h ago", its options' pictures, the pick outlined. Nothing waiting: "Nothing to
    pick right now. Ask Claude for a few ideas on anything, like "three materials for the sidepods",
    and they land here." Gone: the room tabs, the stations' strip, the step list and the wizard.
  - **How it's built:** `tool/sets.py` (new, standard library): `new`, `option`, `open`, `pick`,
    `drop`, a pick keeping each option's picture (`skins/<car>/sets/<n>/<letter>.png`) and deleting
    the options (one in the game kept); `find` and `lab` for the page. `tool/view.py` serves
    `/api/sets?skin=` and `/sets/<car>/<n>/<letter>.png` (the build sheet's `/api/sheet` went).
    `tool/notes.py`: an answer is `answer` (the set, its title, the option picked or talked about, its
    title), a pick needing no words, on a car with a design or sets; the hook's line "in the Lab's
    list, set 2 (Wheels · 2 ideas), picked B (Red Covers)". `viewer/lab-studio.js` is now the car and
    its notes only (the strip, the stations' tries, the picture car and its cache went; `show(name)`
    puts a skin on the car; it says what it shows and what Claude is doing); `viewer/lab-car.js`
    (new) the header and the list; `viewer/lab-wizard.js` removed; `lab.html`'s car room and header
    rewritten, the list 364 to 480 px wide. `SKILL.md`'s stations and rounds became "Sets of
    options"; `.claude/rules/tool.md` rewritten for the room. `tool/sheet.py` and `studio.md`'s steps
    wait for piece 2.
  - **Checks:** 16 on the sets (a scratch skins folder: a new car's first set and its folder, options
    as empty folders then copies of the car's design, open refused before designs and with one
    option, the lab from an option, the pick making the car's design, the others gone, each picture
    kept, picked twice refused, a design loading the car refused, drop keeping one in the game, the
    newest first, a car with no sets, bad names) and 7 on the answers (a pick, words about an option,
    three refusals, the hook's two lines); in the Mac's headless Chrome, 22 on a trial car
    (TSC_WizardTrial: set 1 "3 concepts" picked, set 2 "Wheels · 2 ideas" open): the header, no tabs
    or strip, the menu shut, the set's two pictures, earlier picks folded, B on the car with its chip
    and words box, the address, words about B as an answer, take back, pick B, Your pick, back to
    the car, earlier picks opened with three pictures and A outlined, the menu, a note on the car by
    a click, Game view, another car from the menu with nothing to pick, the materials and back, 390
    wide, no page errors.
  - **The user's try (2026-09-28):** picked A (Black Covers) in the list; it reached Claude at once, the
    pick made it the car's and the car was painted again; the list then showed nothing to pick and
    two earlier picks. "Feels good. I think I can leave with it. If not I can just simply iterate with
    another agent." The trial car deleted (it was never on git).
- **2. The way of working (built 2026-09-28, on the Mac):**
  - **One way:** `SKILL.md`'s "The studio" became "One way of working": a new car goes by
    `new-car.md`, a change is made on the car, and options, whenever the user asks or there's a real
    choice, are a set. The quick way and the studio's steps are gone.
  - **`new-car.md`** (in place of `studio.md`): no steps and no sheet. 1, the talk and its card
    (`brief.md`, which the critic reads); 2, the first concepts as a set (`tool.sets new ... "3
    concepts"`, an option each, made before painting so the Lab lists each as it's painted, the three
    concept designers, `open`, the wait, the pick); 3, the car, field by field with the guides
    (shapes, finishes, wheels as a set, details, lettering), the notes first; 4, the check (the
    critic, the size, the road test); 5, the release (the game, the page online, the design book,
    now a chapter per set and per field with the earlier picks' pictures).
  - **Gone:** `tool/sheet.py` (TSC_Ladybird's `sheet.json` stays as its record, and `tool/mood.py`
    still letters its boards from it); the guides, the critic, the concept designer and
    `tool/critic.py` point at `new-car.md`; `tool/mood.py` stays for boards on request (its title
    from `tool.sets`).


- **What it's for:** the screens the user chose (https://claude.ai/artifact/JHwbvVDKNTCiHTGepPQB2F).
- **What you'll see:** a Studio car opens in the Lab on its wizard: the build sheet on the left,
  the step waiting for you taking over the page, its options in that step's own format, "Or tell
  Claude in your own words", Back and Next. A pick in the Lab reaches Claude with your next
  message, like a note. Clicking a decided step goes back to it.
- **Model:** Opus 5.5.
- **Notes for Claude:**
  - Built from the mockups' look: the Lab's own stylesheet (`viewer/lab.html`), the build sheet
    300 px wide, the step's question in Teko at 44 px. The mockups' source is in the
    session's scratchpad, not the repo: rebuild from the pictures and this description.
  - Real renders everywhere the mockups used stand-ins: the options come from the viewer's
    picture car (`picture()`), as the strip's pictures do, kept in the browser the same way.
  - A pick or a free-text answer goes through the notes channel (`tool/notes.py`, the hook), so
    Claude gets it with the next message; it carries the step and the option.
  - Each step's format: Brief, an open conversation (no form: the user, 2026-09-28), and the
    brief's card as Claude reads it;
    Mood, three boards; Concepts, three whole cars that turn; Shapes, the game's camera beside a
    small "from far away" picture; Colours and materials, one car with a day and night split and
    the finishes as swatches (codes from `finishes.CATALOGUE`, copied like the Materials room);
    Wheels, four wheels close up and turning, then the pick on the car by day and at night;
    Details and Lettering, close-ups of their area; Review, the critic's findings with before and
    after; Road test, the user's F12 screenshots after an install, with notes on them (ask first).
  - Going back: a changed step says "changed", the steps it affects "needs a look", and the page
    shows the whole car before and after.
  - Keep the Lab fast: draw only when something changes, pictures kept in the browser, nothing
    new drawn while Claude paints. Mockups first for any screen that differs from the chosen ones.

#### [dropped] W4. The test: Studio against Quick

- **Dropped** (the user, 2026-09-28: "Drop it. But ill probably explore ways to make the workflow
  better for designing"): it compared two ways of working that became one.

- **What it's for:** check the studio is worth it (the user, 2026-09-28: "I want to do a test for
  the quick and the studio one to see the difference if its worth it").
- **How it runs:**
  - One idea of the user's, the same first message word for word, in two sessions: quick first,
    then studio, so the studio's brief and boards don't shape the user's taste before the quick
    car. Each session is told only its way. Names `TSC_<Idea>_Quick` and `TSC_<Idea>_Studio`.
  - Each `notes.md` records the start and end, the user's messages, the rounds, and each thing the
    user had to point out.
- **The verdict:** both cars side by side as "Car 1" and "Car 2" in a random order, from the game's
  cameras, by day and at night; then both in the game, and the user says which they'd drive; the
  critic reviews both with the same list; the time each took. The result goes under "Things we
  learned" in `CHECKLIST.md` and decides which steps stay.

#### Later

- **The design book:** each finished car's story (brief, mood, concepts, the pick, finishes,
  details, the car in the game) on the page online, built by `tool.publish` from the sheet. The first
  was made by hand for TSC_Ladybird (2026-09-28) as a private page on claude.ai (W1's Release step);
  building it from the sheet onto the page online is still for later.
- **Other people building their own cars:** a separate decision (hosting and cost per user).

### The Lab's timeline (started 2026-09-28)

- **What it's for:** the user (2026-09-28): "I still want to continue iterating but with the new
  layout, having the sidebar on the right as the ai helper. I am however thinking if we have the
  sidebar like a scrollable timeline of the options choosing etc, and the latest would be at the
  bottom. Similar to how an ai chat functions where the conversation just starts moving the content
  upwards." Then: "I guess it's somewhat like A2ui ... widgets so the ai can just communicate through
  dynamic content?" Yes: Claude records what it offers or says through the tool, and the Lab draws
  each kind with its own widget (a note, Claude's line, a set of options, "in the game").
- **The mockups:** https://claude.ai/artifact/6nKpAWW1VFPfbrAZTfVZWM (the Lab at 1440×900, TSC_CMYK_
  EndsInK just after the texture round on 27 Sept, its real notes 1 to 5 and answers): A, chat, two
  voices (the user's notes and words on the right, Claude's lines and sets on the left, "in the game"
  centred); B, one log on a rail (dense, options as rows); C, A with the open set docked over the box.
  Claude's pick: A, the simplest, docking later only if an open set getting pushed away bothers the
  user. **The user picked A** (2026-09-28). Their source: the session's scratchpad (`build.py`), not
  the repo.
- **What you'll see:** the list on the right becomes "With Claude", a timeline, newest at the bottom,
  opened at the bottom and following new entries unless you've scrolled up. Your notes on the car
  (their number, the part, the picture of where you clicked, your words) and your words on the right;
  Claude's short answers on the left with a yellow-green line; a set of options as Claude's, the
  cards and Picks as before, your words that asked for it just above it; a pick, and "In the game",
  as they happen. At the bottom a box to say something to Claude (about the option on the car when
  one is), reaching Claude like a note: at once while it waits, else with your next message. Notes
  not done still hang on the car as tags; done, they leave the car and stay in the timeline.
- **The pieces:**
  1. the leftovers of the earlier layouts cleared (a read-only check on 2026-09-28 listed them:
     unused styles and functions, the stations' export still run on every paint, rounds and their
     switch, the notes' step and station, lines in the skill and guides about the sheet and steps);
  2. the timeline: `tool/notes.py` keeps done notes' pictures and gains Claude's lines (`say`, and
     `done ... --say`); the server gives a car's whole timeline; `viewer/lab-car.js` draws it; the
     skill tells Claude to answer in the Lab when it handles notes.
- **The user's asks while it was built (2026-09-28):** "Just make sure there's a bit of breathing room
  per conversation": 14 px between entries, 30 px above a new exchange (the user's words after
  Claude's), roomier bubbles. "And make the top fade out a bit, so that you can tell there's content
  above to scroll": the top fades over 64 px while there's more above.
- **1. The leftovers (done 2026-09-28):** the rounds (`tool.skin round`, the gallery's rounds,
  `skins/rounds.json`, the UV map room's switch; `viewer/lab-round.js` became `lab-address.js`, the
  address only); the stations' tries, which every paint still wrote (`view.export_stations`,
  `rooms.STATIONS`); `viewer.aim`; unused styles, flags, exports and the Room row the UV map room
  always hid; the skill, guides and concept designer no longer speak of rounds, the sheet or steps.
  Left as they are: `steps.json`'s fields the page doesn't read (Claude may), `tool/mood.py` lettering
  from TSC_Ladybird's `sheet.json` (boards on request), the old `?room=` names the Lab still maps.
- **2. The timeline (built 2026-09-28, on the Mac):**
  - **How it's built:** `tool/notes.py`: a done note keeps its picture (only a note taken back loses
    it); Claude's lines (`say`, `done ... --say`, `by: "claude"`, no number, so the pins' numbers run
    on); `timeline(skins)`; the Studio's step and the stand's station gone from a note, and an answer
    is a pick only (the box took over the words about an option); the hook's lines "in the Lab's box"
    and "in the Lab's timeline". `tool/view.py`: `/api/sets` carries `said` for the car and its
    options, `/notes/<skin>-<n>.jpg` serves a note's picture to this computer's pages. `viewer/lab-car.js`
    draws the timeline from the sets and `said` in the order things happened (a set at when Claude
    made it, the user's words that asked for it just before, a pick's "B · Halftone is the car now",
    "In the game" from the gallery), days apart, and follows the bottom unless the user scrolled up;
    the box under it (`lab.html`, static, so a redraw never takes the typing away). `lab-studio.js`:
    `look(note)` turns the car to a note's view (a click on it in the timeline), and the car's tags
    are the notes with a point only.
  - **Checks** (the Mac's headless Chrome, TSC_CMYK_EndsInK with a test history, removed after): the
    timeline in order ("Yesterday · In the game", then today: the user's ask, note 1 with its picture,
    Claude's line, the user's words a new exchange 30 px down, Claude's line, the set), opened at the
    bottom with the top faded; scrolled to the top, no fade; B put on the car, the box "Say
    something about B · Halftone…"; words sent, a bubble "About B · Halftone · On its way to Claude",
    Take it back, followed to the bottom; B picked, "Pick: B · Halftone", B's button "Your pick"; the
    hook's three lines; a decided set (the kept pictures, B outlined, "B · Halftone is the car now")
    and a set being painted at the bottom; no tags on the car for the box's words or the pick; the UV
    map room and the materials unchanged; no page errors.

### The car map (started 2026-09-29)

- **What it's for** (the user, 2026-09-29, after TSC_WindTunnel's concepts): "would it be best to
  focus on actually mapping the car properly, so that no matter what design is done, the Ai just
  knows?", then "I don't care about a car anymore, because I actually care that the Ai can prperly
  understand how to design cars". Claude had proposed a tool for the air's path; the user saw the
  bigger gap. Today the tool knows the car's part names (`car/parts.json`), plain cm (`shapes`), the
  panels' seams (`shapes.seams`), a few measured regions and spots (`REGIONS`, `SPOTS`) and a map of
  the top typed by hand in the skill. Each design learned the rest alone: TSC_WindTunnel_Smoke spent
  250 lines cutting the body into sections to find where the top ends, the cockpit and the openings,
  and the guides' "Learned" repeat the same lessons (a fold, an inlet, the lower crease, the ledge).
- **The mesh** (measured 2026-09-29): Skin_01 welded at 0.01 cm is 14,678 vertices; the body is one
  piece of 10,892 triangles, the wheel covers 4 x 2,113 and 4 x 1,236, then small loose panels (nose
  panel, fin, mirror mounts ...); 2,254 open edges, 156 edges shared by more than two triangles.
- **The plan, a step at a time, each shown on the car as a picture before the next:**
  1. [x] **The base** (`tool/carmap.py`): the body as one surface (loose panels stitched to what they
     touch), smoothed normals, and what's outside: how much of the open air each spot sees, so "the
     outer body" is known without lists of parts. Cached in the work folder, rebuilt with the mesh.
     - **Built 2026-09-29:** the body welded (14,678 vertices); "open" from depth maps in 200
       directions (the inner car in the way, not the wheels or glass), cosine-weighted, 26 s in the
       Mac's container. `Map.at(pos, nrm)` finds the body under any point (a tree of points every
       0.5 cm, the nearest facing the same way, so a panel lying on another isn't mistaken for it).
       Its test car, TSC_Map_Open (five bands, white open to violet hidden), reads right: the inlets'
       insides, under the nose, the wheel pockets and the low flanks behind the floor hidden, the rest
       open. The user: "you might need to hide the wheels so you see the body" (yes): `tool.snap --body`
       (`node docker/snap.mjs <name> --body`), nine views with the wheels taken off.
  2. [x] **Where things are, and the car's lines:** top, sides, front, back and underneath as soft
     areas split along the car's own lines; the lines: folds, panel joins, the rims of openings, the
     shoulder (where the top turns into the side), the lower edge (where the side turns under).
  3. [x] **Positions that bend with the body:** along the car, and across it (0 the top's middle, 1
     the shoulder, 2 the lower edge), so a stripe or a line placed by them follows the body.
     - **Built 2026-09-29 (steps 2 and 3 together):** each 1 cm slice's outline is the body cut
       there, chained through the welded mesh (a stretch that sees under 20 % of the open air, or
       lies under another stretch, left out; gaps bridged), walked from the top's middle. On it,
       the shoulder: the first turn past 50 degrees from facing up that lasts 2 cm, or where the
       top's surface ends and the outline carries on lower (the inner car takes over there, as in
       front of the sidepods); the lower edge: the first turn past 125 degrees after which the
       outline faces out for under 6 cm (the front flank's lip turns down, then the flank carries
       on). The marks' x and y per slice, outliers replaced by their neighbours' median, smoothed.
       A point's `across` comes straight from where it sits against its length's marks (how far
       out over the top, how far down the side, how far in under), never from a sum round the
       outline: the first two tries summed the girth from the top's middle, and anything that came
       or went higher up (an inlet's mouth, a panel under a panel) moved every band below it by up
       to 17 cm between neighbouring slices (bands in steps). Per point, not per vertex: stored on
       the mesh's corners, a line across a long triangle came out as a staircase.
       `shapes.area/outside/across/along/near/line` (the docstring of `tool/carmap.py`). Test cars:
       TSC_Map_Areas (the areas in colour, the lines drawn) and TSC_Map_Grid (a grid that bends with
       the body). Left rough: under the nose, between the wing pylons.
  4. [x] **The air:** the flow over the surface (the oncoming air flattened onto it, turned round
     the openings by a Laplace solve on the mesh: potential flow), its speed and pressure, and lines
     traced along it from any seeds.
     - **Built 2026-09-29:** `hit`, how hard the oncoming air hits a spot: the Newtonian rule
       (facing forward, squared) times how open the spot is from straight ahead (the directions
       within 25 degrees of forward, from step 1's depth maps). The flow: a potential over the
       welded body, least squares against the oncoming air laid flat on each triangle (which is
       itself the gradient of -z), with a heavy penalty on the flow across each wall edge, one sparse
       solve. A wall is an opening the oncoming air runs into, off the surface (the cockpit's front
       rim, the inlets' mouths: 4,120 edge points), not one it runs along or leaves. Two tries
       before it, turning the air locally near every opening, made lines jog round the cockpit
       like circuit traces (turning within 12 cm), then swerve at every bottom and back edge
       (35 cm, every opening a wall), then merge into two bundles along the rim (walls only): a
       solved flow bends early and never merges two lines. Streamlines: midpoint steps of 0.5 cm,
       projected back on the body; they slide along a wall, end where the surface turns to face back
       (the air leaves there), where they run off the body, or where they stall head-on (the
       cockpit dead ahead of the middle line). `shapes.hit`, `shapes.rake`, `shapes.streamlines`.
       Test car: TSC_Map_Air (the hit as a warm ramp over black, smoke lines from a rake at the
       nose and two along each flank).
  5. [x] **The map for the AI:** a sheet of pictures and words the skill loads (the areas, the lines,
     the openings, the places to keep clear, what the chase cameras see), replacing the maps typed by
     hand in `SKILL.md`; the shapes guide and the concept designer's brief point to it.
     - **Built 2026-09-29:** `python -m tool.carmap --describe` writes `car/map.md` from the map:
       the body at 16 stations (where the top ends and the side turns under), its openings (loops
       30 cm round or more, which ones are walls to the air), every panel (area; its share on the
       top, the sides and under; how open; how big from the chase cameras, a new layer, "chase",
       seen from behind 25 degrees up; how much air it takes), what the player sees and where the
       air hits. Its four pictures, `car/map/*.jpg`, are the TSC_Map_ cars' `--body` sheets. The
       skill reads it before the first design; the hand-typed map of the top in `SKILL.md` went
       (the places the map can't know are special stay); the shapes guide, the concept designer's
       brief and the zones' key point to it. The nose fin and the mirror mounts are left out of the
       outlines: the fin, upright on its plate, made the top end at the car's middle over z 118 to
       142. From the chase cameras the top is 83 % of what the player sees (the body shell 22 %,
       the engine cover 17 %, the rear flanks 14 %).
  6. [x] **The test:** TSC_WindTunnel's smoke lines redrawn on the map (the design should shrink to a
     few lines), and the other two concepts' ideas (streaks, pressure) sketched on the same map.
     - **Done 2026-09-29:** TSC_WindTunnel's design went from 403 lines to 76: its smoke lines are
       streamlines from a rake across the car's width (`shapes.front_rake`: for each x, where the air
       first meets the top, facing up, never a low ledge or a strut), two along each flank, waved
       behind the sidepods by the design (the wake: 1.8 cm, each line a little later than its
       neighbour; 3 cm crossed lines where the deck narrows), the red line the middle streamline,
       which stops at the cockpit's rim as the air does. A rake on the nose alone spread every
       line apart over the sidepods (the real air's way; a wind tunnel's rake spans the car). The
       rake's first seeds sat on the side skirt's front end, which runs under the nose to its tip,
       and on the wing's pylons: the pylons left the outlines with the fin and the mirror mounts.
       Pressure and streaks: TSC_Map_Air shows the air's hit as a pressure map, and the flow field
       is there for streaks (noise combed along `Map.flow`), not drawn yet.
  7. [x] **The lines redone from the car's curvature, checked by measurement** (2026-09-29, the car
     mapper on the Mac, after the user's review and the handover below; the method changed mid-way at
     the user's word: "There has to be a more optimised way of doing this. I don't think it's feasible
     to do it by eye": the gate for "right" became numbers the tool computes on every rebuild).
     - **The ridges** (`carmap._smooth_normals`, `_curvature`, `_principal`, `_trace_ridges`): the
       normals averaged over 2.5 cm (SMOOTH), the curvature tensor per vertex (Rusinkiewicz 2004 per
       triangle, summed at the corners), its greatest bend k1 and directions; every ridge traced from
       the crests bent over RIDGE_SEED (0.09/cm), a 1 cm step at a time along the least-bent direction,
       pulled back each step onto the nearest local maximum of k1 across (never the biggest in the
       window: where the nose's crease and the lip converge to 4 cm the biggest would jump ridges),
       refined by a parabola, with samples off the body (past an open edge: the tail's top edge) left
       out; all seeds at once, then strongest first each cut where it runs within 1.5 cm of a kept one,
       the pieces of one ridge joined end to end (`_join`, gap 4 cm, nearly straight), pieces under
       10 cm dropped, each smoothed as a curve (2 cm) and put back on the body; then made the same on
       both sides (`_symmetric`: the left side's traces mirrored; the two sides' own traces differed by
       a cm or two and in where they ended). 62 ridges, 38 m in all; `line("fold")` is now these
       (the 35 degree dihedral found almost nothing on this car's rounded edges). Their test car:
       TSC_Map_Lines, every ridge in its own colour on clay (`shapes.polyline`).
     - **The named lines** (`_marks`, per 1 cm slice, on the ridges the slice's outline crosses, each
       crossing the ridge's own point in the slice's plane, `_in_plane`): the shoulder is the crossing
       up to 4 cm past where the outline first runs steeper than 50 degrees for 3 cm that turns the
       surface most (2 to 6 cm after against before, at least 20 degrees; of a double crest within 8 cm
       the outer), else the crossing within 2 cm of that point, else no crease; the top's end at the
       sidepod's front (an open edge) is the shoulder there. The lower edge: where the skin contiguous
       with the shoulder (chained through gaps over hidden skin, or over nothing under 6 cm) reaches
       the floor (an open edge under 30 cm, not at the middle), the mesh's own edge (the skirt, the
       body's edge under the rear flanks; the sidepod's side-panel crease above it stays a fold);
       else the first crest facing out-and-down (45 to 150 degrees) beyond which the surface faces
       past 110 degrees (2 cm on, or the median over 4 or 10 cm) and stays under for the rest of its
       stretch (the lip over the nose's belly, the tail corner's lower crease; at the tip the lip is
       both lines). Kinds per slice: 0 a ridge, 1 the skin's end, 2 no crease, 3 a ridge with the
       skin ending below (the lip), 4 the skin's own open edge (exact). A slice whose choice differs
       from both neighbours while they agree is repaired to the crossing nearest them (`_repair`, runs
       of up to three). No median or smoothing along the car any more: they put the line between two
       ridges, on neither. `sec_kind`, `sec_raw`, `sec_draw` (the slices where a line is drawn) are
       stored with the map; `line("shoulder"/"lower")` draws nothing on undrawn slices.
     - **The front and the back** (`_faces`, `Map.face_distance`): whole faces grown over the mesh's
       triangles from those facing squarely forward or back (0.85), across shared edges, never across
       a ridge (both ends within 1.5 cm) nor onto a triangle facing under 0.5 or a wheel cover; their
       edge is the boundary between labelled triangles and the rest, or the smooth 0.5 contour where no
       ridge bounds them (the nose's tip). `shapes.area("front"/"back")` use them; "top", "sides",
       "under" leave them out.
     - **The check** (`tool/mapcheck.py`, `python -m tool.carmap --check [-v]`): per slice and line, on
       both sides (the right side's sections from the mirrored mesh): ridge (cm from the line to the
       crest of the bend across the section, a parabola on 0.25 cm samples), contrast (the crest over
       the flatter side 3 to 10 cm off, or over the body's median bend with one side only), shift
       (the crest's move under 1, 2 and 4 cm of smoothing), step, bend (beyond the ridge's own),
       sides, jumps (a step beyond the line's slope, not at a ridge's end), texture (a jump in the
       flat texture within one island beyond the texel scale). Limits from the mesh (median edge 2.17
       cm, median bend 0.073/cm): ridge 0.6 (a quarter edge), contrast 1.5, shift 2.2 (one edge),
       step 1.5, bend 0.25, sides 0.5, jumps 0, texture 0. Exempt: slices where the ridge runs across
       the car (over 45 degrees to its length: corners, the tail's top edge), where another ridge is
       within 8 cm or the ridge turns a corner (no single crest across the slice), a ridge's last 8 cm
       (its fade-out), the slices either side of a change of kind (the car's own steps), a mesh edge's
       bends (its facets). A stretch is "no line" when under half its slices are drawn, with the
       reason. `sec_draw` comes from the same measures at build (`mapcheck.draw_mask`).
     - **Tried and dropped:** tracking each line along z from the tip (it started on the only
       crossing the first slices have, the skirt's front, and followed it the whole way); a slope
       threshold for the top's end (the nose's flank runs at 45 degrees like the engine cover at 43:
       the turn at the crest tells them apart); the deepest crest for the lower edge (it took the
       diffuser's strakes at the tail and the belly's inner lip at the nose); the mean of facings
       past 180 degrees (it wraps to nothing: the median of |facing|); the median-and-smooth cleanup;
       a peak within 3 cm of the visible end for the skin's edge (it wobbled between the crest and
       the cut); snapping to any boundary point within 5 cm (it took the underside's inner edges).
     - **State at hand-back** (the check's table is in the report and below): the shoulder passes on
       every stretch, both sides, except the sidepods' front and inlets (z 35 to -12), where it is
       the rim's crease behind the inlet, the top's open edge over the sidepod's front, and no crease
       for 11 slices between the lip's end and the drop, with a 9 cm jog at the rim's outer corner
       that the check counts as a jump. The lower edge passes from the tip to the front flank's lip;
       behind, it is the skin's own edge along the skirt (the mesh's boundary), and its steps of 2 to
       7 cm from slice to slice (the boundary's own notches, the arch, the sidepod's front end) and a
       2.5 cm difference between the sides fail the step and sides limits; at the tail it is the
       corner's lower crease on 19 slices and "skin's end" behind z -142. The front flank's lower edge
       moves from the lip to the skirt at z 70 (the car's own).

       ```
       /app/tool/carmap.py:441: RuntimeWarning: All-NaN axis encountered
         return np.nanmax([soon, on, at2]) > UNDER and (len(rest) < 4 or (rest < 100.0).mean() < 0.4)
       line      side  stretch                           ridge  contr  shift   step   bend  sides jumps  tex  verdict
       --------------------------------------------------------------------------------------------------------------
       shoulder  left  the nose's tip                        -      -      -   0.90   0.13      -     0    0  ok (3: the skin's own edge) [2 slices at a ridge's end]
       shoulder  left  the nose                           0.59   8.86   1.92   0.45   0.06   0.00     0    0  ok [3 slices at a ridge's end]
       shoulder  left  the fin's plate                    0.41   7.24   1.67   0.35   0.05   0.00     0    0  ok
       shoulder  left  the bonnet                         0.21   5.83   0.12   0.31   0.05   0.00     0    0  ok
       shoulder  left  the front flank and its lip        0.28   3.83   2.12   0.53   0.23   0.00     0    0  ok (7: no crease) [8 slices at a ridge's end]
       shoulder  left  the sidepods' front and inlets        -      -      -   6.89   6.48   0.00     1    0  FAIL step bend jumps (11: no crease, 12: the skin's own edge) [42 slices at a ridge's end]
       shoulder  left  the sidepods                       0.26   2.62   1.46   0.58   0.16   0.00     0    0  ok (2: no crease) [6 slices at a ridge's end]
       shoulder  left  the rear flanks and the deck       0.58   2.40   2.04   0.83   0.07   0.01     0    0  ok (1: no crease) [9 slices at a ridge's end]
       shoulder  left  the tail                           0.32   5.14   1.70   0.41   0.07   0.00     0    0  ok (6: no crease)
       shoulder  right the nose's tip                        -      -      -   0.90   0.13      -     0    0  ok (3: no crease) [2 slices at a ridge's end]
       shoulder  right the nose                           0.59   8.86   1.92   0.45   0.06   0.00     0    0  ok [3 slices at a ridge's end]
       shoulder  right the fin's plate                    0.41   7.24   1.67   0.35   0.05   0.00     0    0  ok
       shoulder  right the bonnet                         0.21   5.83   0.12   0.31   0.05   0.00     0    0  ok
       shoulder  right the front flank and its lip        0.28   3.83   2.12   0.53   0.23   0.00     0    0  ok (7: no crease) [8 slices at a ridge's end]
       shoulder  right the sidepods' front and inlets        -      -      -   6.89   6.48   0.00     1    0  FAIL step bend jumps (11: no crease, 12: the skin's own edge) [42 slices at a ridge's end]
       shoulder  right the sidepods                       0.26   2.62   1.46   0.58   0.14   0.00     0    0  ok (2: no crease) [6 slices at a ridge's end]
       shoulder  right the rear flanks and the deck       0.58   2.40   2.04   0.83   0.07   0.01     0    0  ok (1: no crease) [9 slices at a ridge's end]
       shoulder  right the tail                           0.32   5.14   1.70   0.41   0.07   0.00     0    0  ok (6: no crease)
       lower     left  the nose's tip                        -      -      -   0.90   0.13      -     0    0  ok (3: skin's end, 13: ridge, skin ends below) [2 slices at a ridge's end]
       lower     left  the nose                           0.57   2.89   2.14   0.30   0.03   0.01     0    0  ok (50: ridge, skin ends below, 4: weak or wandering crest)
       lower     left  the fin's plate                    0.47   4.88   1.36   0.25   0.02   0.00     0    0  ok (25: ridge, skin ends below)
       lower     left  the bonnet                         0.43   7.37   1.65   0.25   0.01   0.00     0    0  ok (28: ridge, skin ends below)
       lower     left  the front flank and its lip        0.41   6.20   0.02   3.26   0.01   1.59     1    0  FAIL step sides jumps (20: ridge, skin ends below, 35: the skin's own edge)
       lower     left  the sidepods' front and inlets        -      -      -   2.69      -   0.00     4    0  FAIL step jumps (47: the skin's own edge) [16 slices at a ridge's end]
       lower     left  the sidepods                          -      -      -   2.93      -   2.54     6    0  FAIL step sides jumps (38: the skin's own edge)
       lower     left  the rear flanks and the deck          -      -      -   5.57   0.00   2.58     5    0  FAIL step sides jumps (61: the skin's own edge) [4 slices at a ridge's end]
       lower     left  the tail                           0.08   4.57   1.20   3.53   1.43   0.00     1    0  no line (19/40 slices drawn: 21: skin's end, 2: ridge, skin ends below); FAIL step bend jumps [9 slices at a ridge's end]
       lower     right the nose's tip                        -      -      -   0.90   0.13      -     0    0  ok (3: skin's end, 13: ridge, skin ends below) [3 slices at a ridge's end]
       lower     right the nose                           0.57   2.89   2.14   0.30   0.03   0.01     0    0  ok (50: ridge, skin ends below, 4: weak or wandering crest)
       lower     right the fin's plate                    0.47   4.88   1.36   0.25   0.02   0.00     0    0  ok (26: ridge, skin ends below)
       lower     right the bonnet                         0.43   7.37   1.65   0.24   0.01   0.00     0    0  ok (28: ridge, skin ends below)
       lower     right the front flank and its lip        0.41   6.20   0.02   2.12   0.01   1.59     2    0  FAIL step sides jumps (20: ridge, skin ends below, 35: the skin's own edge)
       lower     right the sidepods' front and inlets        -      -      -   2.69      -   0.00     4    0  FAIL step jumps (47: the skin's own edge) [16 slices at a ridge's end]
       lower     right the sidepods                          -      -      -   2.93      -   2.54     5    0  FAIL step sides jumps (38: the skin's own edge)
       lower     right the rear flanks and the deck          -      -      -   5.57   0.00   2.58     4    0  FAIL step sides jumps (61: the skin's own edge) [3 slices at a ridge's end]
       lower     right the tail                           0.08   5.05   1.20  19.43  19.40  38.52     2    0  FAIL step bend sides jumps (19: skin's end, 3: ridge, skin ends below) [7 slices at a ridge's end]
       
       limits: ridge 0.6, contrast 1.5, shift 2.2, step 1.5, bend 0.25, sides 0.5, jumps 0, texture 0
       12 stretches fail
       ```
  8. [x] **Round 2: the failing stretches worked through until the check passes** (2026-09-29, the car
     mapper; the coordinator's order: the tail, the sidepods' front, the skirt, the z 70 handover, the
     faces; nothing loosened: the limits stand, `edge` added).
     - **The tail's lower edge, right side:** the corner's lower crease crosses each slice as the first
       point of its stretch, right after the wheel arch's gap, where the smoothed facing is one-sided
       and read as facing in; the crest's facing is now the median over its first centimetre. Where a
       ridge's crossing is missing on one or two slices between two on it (four slices at z -130 to
       -127), the mark is now the point between the neighbours (`_repair`), instead of the arch's slot
       on one side and a diffuser strake on the other. The mesh's boundary is mirrored to 0.09 cm
       (5,222 boundary points under 30 cm), so no asymmetry is the body's own.
     - **The shoulder over the sidepods' front and inlets:** the boxes and jogs were the rule flipping
       between the rim's two crests and the top's open edge. Now, where the top's own stretch of skin
       runs out within 8 cm of turning down and its end lies on the mesh's boundary with skin on below
       (over the sidepod's front, along the inlet's rim: the rim is an inner part), the shoulder is that
       edge, exact (kind 4, snapped onto the boundary), one continuous curve from z 25 to -9; between
       the lip's end and it (z 30 to 25) there is no crease: 7 slices "no line", one span. At the tail
       the top's edge runs across and belongs to the back: not the shoulder (the outline ends there).
     - **The lower edge along the skirt:** measured, the "skin's own edge" of round 1 was 5.5 cm
       (median) from any boundary point: it was where the skin stops being seen (open under 0.2) on a
       roll that carries on hidden to the floor, not an edge. The mesh's real edges at the floor: the
       sidepods' bottom edge (y 26 to 30, x 84, z 35 to -30, with the mesh's own 4 cm step near z 2),
       and the floor's edge itself far inboard (x 31 at z 66, x 42 to 60 under the rear flanks), out of
       sight. So: a mark is the skin's own edge only where the outline passes within 2 cm of a
       boundary point (the first such point along the piece of skin; the sidepod's skin and the
       skirt's touch along that edge and the outline runs on, to 0.02 cm of it), and then it is put
       on the boundary itself (the nearest boundary point in the slice's own plane: the nearest in
       3D came from another slice on a slanted edge, up to 1.5 cm off) and measured as a curve on it
       (`edge`, cm from the boundary, limit 0.5; no steps or bends, which are the boundary's own
       notches, and the neighbour repair leaves a notch between edge marks alone). The lines are drawn as the
       distance to the marks' own curve (`Map.mark_distance`), not through `across`, which on the
       underside depends on x alone and smeared the lower line over the skirt strip. Otherwise the first crest turning under (the skirt's crest along the front flank,
       kind 0: the z 70 handover from the lip is then between two ridges and smooth), or, with no
       traced ridge, the crest of the roll read on the slice within 6 cm of where the skin disappears
       (kind 5, judged like a ridge). Behind the sidepods (z -95 to -35) that roll bends 0.09 to
       0.10/cm, 1.3 to 1.6 times the body's median bend, under the 1.5 limit on most slices: **the
       body's own: no clear lower edge there**, the flank rolls under out of sight; 30 of 72 slices
       drawn. Under the rear wheel pocket the arch's rim (a crest 11 cm above the floor's edge) is the
       lower edge, not the floor: an edge wins only within 5 cm of the first crest.
     - **The faces:** measured, the skin facing within 45 degrees of straight ahead is 411 cm² and of
       straight back 960 cm² (the inlet rims, the nose's wing and the tail's number panel are inner
       parts): this car's skin has no single front or back face. `area("front")` is the two flank
       bulges ahead of the sidepods (1,553 cm², z 16 to 63), `area("back")` the two rear flank panels
       behind them that face back more than sideways (2,193 cm², z -97 to -57), grown from 0.5 facing,
       kept over 0.5, never across a ridge, pieces under 100 cm² dropped; each bounded by the shoulder
       and the lower edge and by the smooth 60 degree contour fore and aft. `car/map.md` says so.
     - **The check:** the ridge's own bend allowance now takes its nodes two either side of the
       crossing (a kink one node off counted against the line) and scales with the ridge's slant;
       steps, bends and jumps are counted over drawn slices only; sides only where both sides draw.
     - The pictures: `car/map/areas.jpg`, `lines.jpg`, and the flat texture with the lines on it,
       `car/map/texture.jpg` (the areas car's Skin_B).
     - **The check at the end of round 2** (every stretch passes; "no line" where the body has none, with the reason):

       ```
       /app/tool/carmap.py:448: RuntimeWarning: All-NaN axis encountered
         return np.nanmax([soon, on, at2]) > UNDER and (len(rest) < 4 or (rest < 100.0).mean() < 0.4)
       line      side  stretch                           ridge  contr  shift   step   bend  sides  edge jumps  tex  verdict
       --------------------------------------------------------------------------------------------------------------------
       shoulder  left  the nose's tip                        -      -      -   0.90   0.00      -     -     0    0  ok (3: skin's end) [2 slices at a ridge's end]
       shoulder  left  the nose                           0.59   8.86   1.92   0.45   0.00   0.00     -     0    0  ok [3 slices at a ridge's end]
       shoulder  left  the fin's plate                    0.41   7.24   1.67   0.35   0.01   0.00     -     0    0  ok
       shoulder  left  the bonnet                         0.21   5.83   0.12   0.31   0.00   0.00     -     0    0  ok
       shoulder  left  the front flank and its lip        0.28   3.83   2.12   0.26   0.00   0.00     -     0    0  ok (7: no crease) [8 slices at a ridge's end]
       shoulder  left  the sidepods' front and inlets        -      -      -      -      -   0.00  0.24     0    0  ok (7: no crease, 39: the skin's own edge) [41 slices at a ridge's end]
       shoulder  left  the sidepods                       0.26   2.62   1.46   0.58   0.14   0.00  0.00     0    0  ok (1: no crease, 1: the skin's own edge) [6 slices at a ridge's end]
       shoulder  left  the rear flanks and the deck       0.58   2.40   2.04   0.83   0.00   0.01     -     0    0  ok (1: no crease) [9 slices at a ridge's end]
       shoulder  left  the tail                           0.32   5.14   1.70   0.41   0.01   0.00     -     0    0  ok (6: no crease)
       shoulder  right the nose's tip                        -      -      -   0.90   0.00      -     -     0    0  ok (3: no crease) [2 slices at a ridge's end]
       shoulder  right the nose                           0.59   8.86   1.92   0.45   0.00   0.00     -     0    0  ok [3 slices at a ridge's end]
       shoulder  right the fin's plate                    0.41   7.24   1.67   0.35   0.01   0.00     -     0    0  ok
       shoulder  right the bonnet                         0.21   5.83   0.12   0.31   0.00   0.00     -     0    0  ok
       shoulder  right the front flank and its lip        0.28   3.83   2.12   0.27   0.00   0.00     -     0    0  ok (7: no crease) [8 slices at a ridge's end]
       shoulder  right the sidepods' front and inlets        -      -      -      -      -   0.00  0.24     0    0  ok (7: no crease, 38: the skin's own edge) [42 slices at a ridge's end]
       shoulder  right the sidepods                       0.26   2.62   1.46   0.58   0.13   0.00  0.00     0    0  ok (1: no crease, 1: the skin's own edge) [6 slices at a ridge's end]
       shoulder  right the rear flanks and the deck       0.58   2.40   2.04   0.83   0.00   0.01     -     0    0  ok (1: no crease) [9 slices at a ridge's end]
       shoulder  right the tail                           0.32   5.14   1.70   0.41   0.01   0.00     -     0    0  ok (6: no crease)
       lower     left  the nose's tip                        -      -      -   0.90   0.00      -  0.33     0    0  ok (13: ridge, skin ends below, 3: the skin's own edge)
       lower     left  the nose                           0.57   2.89   2.14   0.30   0.00   0.01     -     0    0  ok (50: ridge, skin ends below, 4: weak or wandering crest)
       lower     left  the fin's plate                    0.47   4.88   1.36   0.25   0.00   0.00     -     0    0  ok (25: ridge, skin ends below)
       lower     left  the bonnet                         0.43   7.37   1.65   0.25   0.00   0.00     -     0    0  ok (28: ridge, skin ends below)
       lower     left  the front flank and its lip        0.41   5.31   0.56   0.94   0.00   0.00  0.26     0    0  ok (20: ridge, skin ends below, 9: the skin's own edge) [7 slices at a ridge's end]
       lower     left  the sidepods' front and inlets        -      -      -      -      -      -  0.26     0    0  ok (47: the skin's own edge) [10 slices at a ridge's end]
       lower     left  the sidepods                          -      -      -      -      -   0.00  0.24     0    0  ok (21: the skin's own edge, 3: a roll's crest, 15: weak or wandering crest) [6 slices at a ridge's end]
       lower     left  the rear flanks and the deck       0.20   1.55   0.00      -      -   0.00  0.29     0    0  no line (31/72 slices drawn: 9: skin's end, 28: the skin's own edge, 10: a roll's crest, 32: weak or wandering crest) [1 slices at a ridge's end]
       lower     left  the tail                              -      -      -      -      -   0.07  0.39     0    0  ok (16: skin's end, 23: the skin's own edge) [7 slices at a ridge's end]
       lower     right the nose's tip                        -      -      -   0.90   0.00      -  0.33     0    0  ok (13: ridge, skin ends below, 3: the skin's own edge)
       lower     right the nose                           0.57   2.89   2.14   0.30   0.00   0.01     -     0    0  ok (50: ridge, skin ends below, 4: weak or wandering crest)
       lower     right the fin's plate                    0.47   4.88   1.36   0.25   0.00   0.00     -     0    0  ok (26: ridge, skin ends below)
       lower     right the bonnet                         0.43   7.37   1.65   0.24   0.00   0.00     -     0    0  ok (28: ridge, skin ends below)
       lower     right the front flank and its lip        0.41   6.20   0.56   0.94   0.00   0.00  0.26     0    0  ok (20: ridge, skin ends below, 9: the skin's own edge) [7 slices at a ridge's end]
       lower     right the sidepods' front and inlets        -      -      -      -      -      -  0.26     0    0  ok (47: the skin's own edge) [10 slices at a ridge's end]
       lower     right the sidepods                          -      -      -      -      -   0.00  0.24     0    0  ok (21: the skin's own edge, 2: a roll's crest, 15: weak or wandering crest) [6 slices at a ridge's end]
       lower     right the rear flanks and the deck       0.43   1.55   0.00   0.44   0.00   0.00  0.21     0    0  no line (32/72 slices drawn: 9: skin's end, 28: the skin's own edge, 8: a roll's crest, 31: weak or wandering crest) [1 slices at a ridge's end]
       lower     right the tail                              -      -      -      -      -   0.07  0.39     0    0  ok (17: skin's end, 23: the skin's own edge) [7 slices at a ridge's end]
       
       limits: ridge 0.6, contrast 1.5, shift 2.2, step 1.5, bend 0.25, sides 0.5, jumps 0, texture 0, edge 0.5
       all stretches pass
       ```
  9. [x] **Round 3: the lines as fitted curves, the areas cut by them; the check measures what the eye
     sees** (2026-09-29, the car mapper; the user: "the markings that I see are wobbly and it just
     feels like a kid just drawn in crayons with zero precision ... We have the model and the UV map,
     there has to be an accurate way to do it").
     - **Why round 2's check passed crayon.** It measured only the two named lines, slice by slice,
       with cm limits: a 1.5 cm step per 1 cm slice lets a line zigzag, and it never measured the
       folds or the areas' edges at all. The crayon came from two things: anything read point by point
       off the 2 cm mesh and joined up (the marks, the traced ridges), and anything bounded by a
       threshold on a per-vertex value (the faces' 60 degree facing contour, the hidden insides'
       openness, the areas' region by girth per slice). The crisp marks were the ones taken straight
       from the model's own edges (the joins, the openings).
     - **The named lines are curves** (`_fit`, `_runs`, `_curves`): each stretch of evidence (the
       marks: the ridges' own crossings and the mesh's own edges, where drawn) fitted by least
       squares as cubic B-splines in x(z), y(z) (`scipy.interpolate.make_lsq_spline`), a knot every
       15 cm (KNOT), one more only where the curve misses a kept point by over 10 mm (FIT_MAX, down
       to a knot every 5 cm), and a break only where it still misses (a corner); evidence over 8 mm
       from the curve fitted to the rest is left out, up to a third (DROP: a second edge's points
       interleaved with the line's, a traced crest's jitter stays in); gaps of up to 20 slices bridged
       when the marks either side are within 3 cm per slice of gap (the top's edge across the
       no-crease span at z 27 to 42); a run breaks at a 3 cm jump; a line is 12 cm or more. The curve
       is not put back onto the faceted mesh (that gave it the facets' kinks: radius 1 cm, 40 to 140
       bends a metre); its evidence lies on the skin, and it stays within a millimetre of it. Marks on
       the skin's own edge keep to the boundary they are on from slice to slice (the arch's rim and
       the tail corner's edge interleaved before). Result: the shoulder in 3 curves (the nose's crease
       to the sidepod's rear corner in one, 235 cm, 15 knots), the lower edge in 4; evidence within
       4.5 mm at the 95th percentile, 7.9 mm at most; tightest radii 9 to 61 cm; 0.9 mm ragged.
     - **The areas are cut by the curves** (`Map._frames`, `across_level`): a point's offset across
       the nearest curve point in the curve's own frame (N x T, pointed to the top or up), within 3 cm
       along the car; elsewhere, where the body has no line, the distance to the skin's own end (the
       mesh's boundary), signed by the region. The frame test holds only near the curve (within 5
       cm, and 2 cm in from a curve's ends): projected from far off, or from beyond an end, its
       sign is meaningless (it painted the deck "under"); further off the sign is the region's,
       the magnitude the distance to the curve; a point whose nearest outline point is the lower
       mark itself is on the side. Nothing is bounded by a threshold on facing, open or across any
       more; the front and back areas are dropped (`shapes.area` knows top, sides, under),
       as the round-2 measurement showed the skin has no front or back face (411 and 960 cm² in
       patches); `car/map.md` says so, and where the air hits is `shapes.hit`. The hidden insides are
       no longer painted in the test car (a threshold on openness).
     - **Only real design edges are folds** (`_folds`, `_ridge_contrast`): of the 62 traced ridges, 47
       stand out 1.5 times or more from the surface 3 to 10 cm either side (the contrast measure,
       along the ridge) and run 20 cm or more; each fitted as a curve by its arc length. Of those, 39
       are a named line, an opening's rim or a join (within 2 cm for most of their length) and are
       drawn as that, not again as a fold: 8 folds are drawn (798 cm), each on both sides: the skirt's
       crest along the whole flank (381 cm, the lower edge being the sidepod's bottom edge and the
       lip above it), the inlet rim's crease, the tail corner's middle crease, the diffuser's edge.
     - **The check measures what the eye sees** (`mapcheck.curves`, printed by `--check` after the
       evidence table, which now reads the marks as read, `sec_raw`, and mirrors the traced ridges,
       not the drawn folds, for the right side): per curve its length, knots, evidence, fit95 and fitmax (mm), the share of
       evidence left out, the tightest radius (cm, 98th percentile), bends per metre (how often the
       sense of its bend changes where it bends tighter than 50 cm; any curve may have two), ragged
       (mm from its own course smoothed over 4 cm, on the car) and texture (the same on its path in
       the flat texture, per island, 3 cm clear of the seams, texels over the local texel scale).
       Limits: fit95 6 mm (a quarter of the mesh's median edge, as the ridge limit), fitmax 10,
       dropped 33 %, bends 4 a metre, ragged 2 mm, texture 4 mm (the map bends a line at every
       triangle's edge, about 1 mm over 4 cm on this mesh, the floor printed under the table; twice
       it and more is the map stretching). The areas' boundaries are the curves and the mesh's own
       edges, nothing else, so a boundary of another kind cannot exist to fail.
     - **The check at the end of round 3** (the evidence table, then the curves):

       ```
       /app/tool/carmap.py:449: RuntimeWarning: All-NaN axis encountered
         return np.nanmax([soon, on, at2]) > UNDER and (len(rest) < 4 or (rest < 100.0).mean() < 0.4)
       line      side  stretch                           ridge  contr  shift   step   bend  sides  edge jumps  tex  verdict
       --------------------------------------------------------------------------------------------------------------------
       shoulder  left  the nose's tip                        -      -      -   0.90   0.00      -     -     0    0  ok (3: skin's end) [2 slices at a ridge's end]
       shoulder  left  the nose                           0.59   8.86   1.92   0.45   0.00   0.00     -     0    0  ok [3 slices at a ridge's end]
       shoulder  left  the fin's plate                    0.41   7.24   1.67   0.35   0.01   0.00     -     0    0  ok
       shoulder  left  the bonnet                         0.21   5.83   0.12   0.31   0.00   0.00     -     0    0  ok
       shoulder  left  the front flank and its lip        0.28   3.83   2.12   0.26   0.00   0.00     -     0    0  ok (7: no crease) [8 slices at a ridge's end]
       shoulder  left  the sidepods' front and inlets        -      -      -      -      -   0.00  0.40     0    0  ok (7: no crease, 39: the skin's own edge) [42 slices at a ridge's end]
       shoulder  left  the sidepods                       0.26   2.62   1.46   0.58   0.14   0.00  0.00     0    0  ok (1: no crease, 1: the skin's own edge) [6 slices at a ridge's end]
       shoulder  left  the rear flanks and the deck       0.58   2.40   2.04   0.83   0.00   0.01     -     0    0  ok (1: no crease) [9 slices at a ridge's end]
       shoulder  left  the tail                           0.32   5.14   1.70   0.41   0.01   0.00     -     0    0  ok (6: no crease)
       shoulder  right the nose's tip                        -      -      -   0.90   0.00      -     -     0    0  ok (3: no crease) [2 slices at a ridge's end]
       shoulder  right the nose                           0.59   8.86   1.92   0.45   0.00   0.00     -     0    0  ok [3 slices at a ridge's end]
       shoulder  right the fin's plate                    0.41   7.24   1.67   0.35   0.01   0.00     -     0    0  ok
       shoulder  right the bonnet                         0.21   5.83   0.12   0.31   0.00   0.00     -     0    0  ok
       shoulder  right the front flank and its lip        0.28   3.83   2.12   0.27   0.00   0.00     -     0    0  ok (7: no crease) [8 slices at a ridge's end]
       shoulder  right the sidepods' front and inlets        -      -      -      -      -   0.00  0.40     0    0  ok (7: no crease, 38: the skin's own edge) [42 slices at a ridge's end]
       shoulder  right the sidepods                       0.26   2.62   1.46   0.58   0.13   0.00  0.00     0    0  ok (1: no crease, 1: the skin's own edge) [6 slices at a ridge's end]
       shoulder  right the rear flanks and the deck       0.58   2.40   2.04   0.83   0.00   0.01     -     0    0  ok (1: no crease) [9 slices at a ridge's end]
       shoulder  right the tail                           0.32   5.14   1.70   0.41   0.01   0.00     -     0    0  ok (6: no crease)
       lower     left  the nose's tip                        -      -      -   0.90   0.00      -  0.36     0    0  ok (13: ridge, skin ends below, 3: the skin's own edge)
       lower     left  the nose                           0.57   2.89   2.14   0.30   0.00   0.01     -     0    0  ok (50: ridge, skin ends below, 4: weak or wandering crest)
       lower     left  the fin's plate                    0.47   4.88   1.36   0.25   0.00   0.00     -     0    0  ok (25: ridge, skin ends below)
       lower     left  the bonnet                         0.43   7.37   1.65   0.25   0.00   0.00     -     0    0  ok (28: ridge, skin ends below)
       lower     left  the front flank and its lip        0.41   5.31   0.56   0.94   0.00   0.00  0.44     0    0  ok (20: ridge, skin ends below, 9: the skin's own edge) [8 slices at a ridge's end]
       lower     left  the sidepods' front and inlets        -      -      -      -      -      -  0.40     0    0  ok (47: the skin's own edge) [10 slices at a ridge's end]
       lower     left  the sidepods                          -      -      -      -      -      -  0.37     0    0  ok (21: the skin's own edge, 3: a roll's crest, 15: weak or wandering crest) [6 slices at a ridge's end]
       lower     left  the rear flanks and the deck       0.20   1.55   0.00      -      -   0.00  0.39     0    0  no line (31/72 slices drawn: 9: skin's end, 28: the skin's own edge, 10: a roll's crest, 32: weak or wandering crest) [1 slices at a ridge's end]
       lower     left  the tail                              -      -      -      -      -   0.07  0.50     0    0  ok (16: skin's end, 23: the skin's own edge) [7 slices at a ridge's end]
       lower     right the nose's tip                        -      -      -   0.90   0.00      -  0.36     0    0  ok (13: ridge, skin ends below, 3: the skin's own edge)
       lower     right the nose                           0.57   2.89   2.14   0.30   0.00   0.01     -     0    0  ok (50: ridge, skin ends below, 4: weak or wandering crest)
       lower     right the fin's plate                    0.47   4.88   1.36   0.25   0.00   0.00     -     0    0  ok (26: ridge, skin ends below)
       lower     right the bonnet                         0.43   7.37   1.65   0.24   0.00   0.00     -     0    0  ok (28: ridge, skin ends below)
       lower     right the front flank and its lip        0.41   6.20   0.56   0.94   0.00   0.00  0.44     0    0  ok (20: ridge, skin ends below, 9: the skin's own edge) [8 slices at a ridge's end]
       lower     right the sidepods' front and inlets        -      -      -      -      -      -  0.40     0    0  ok (47: the skin's own edge) [10 slices at a ridge's end]
       lower     right the sidepods                          -      -      -      -      -      -  0.37     0    0  ok (21: the skin's own edge, 2: a roll's crest, 15: weak or wandering crest) [6 slices at a ridge's end]
       lower     right the rear flanks and the deck       0.43   1.55   0.00   0.44   0.00   0.00  0.39     0    0  no line (32/72 slices drawn: 9: skin's end, 28: the skin's own edge, 8: a roll's crest, 31: weak or wandering crest) [1 slices at a ridge's end]
       lower     right the tail                              -      -      -      -      -   0.07  0.50     0    0  ok (17: skin's end, 23: the skin's own edge) [7 slices at a ridge's end]
       
       limits: ridge 0.6, contrast 1.5, shift 2.2, step 1.5, bend 0.25, sides 0.5, jumps 0, texture 0, edge 0.5
       all stretches pass
       
       line                     z   cm knots  evid  fit95 fitmax radius bends/m ragged texture  verdict
       ------------------------------------------------------------------------------------------------
       shoulder       -52 to -156  104     6   105    4.1    5.4      9     1.9    0.9     2.5  ok
       shoulder       188 to  -48  235    15   198    3.9    7.9     14     1.7    0.9     3.8  ok (14 slices without evidence) (24 points left out)
       shoulder       208 to  188   19     0    20    2.0    2.5     17     5.2    0.8     2.4  ok
       lower          -96 to -134   37     1    38    3.7    6.8     22     0.0    0.6     2.8  ok
       lower           42 to  -32   75     4    70    4.2    7.7     24     1.3    0.5     3.2  ok (6 points left out)
       lower           70 to   44   25     1    26    1.7    1.8     61     0.0    0.2     2.5  ok
       lower          208 to   70  137     8   134    2.4    3.7     22     0.0    0.6     2.4  ok (4 slices without evidence)
       fold           215 to -127  381    24   370    3.7    7.4     12     0.3    0.8     2.7  ok (8 points left out) (contrast 4.6)
       fold          -117 to -141   28     1    31    3.0    4.9      6     3.6    1.4     3.2  ok (contrast 13.7)
       fold            12 to  -11   24     1    27    1.2    1.4     69     0.0    0.1     1.1  ok (contrast 5.2)
       fold          -125 to -148   24     1    25    2.6    2.7     14     8.5    0.4     1.9  ok (contrast 4.5)
       fold           215 to  -24  266    17   266    2.6    3.7     11     0.0    0.7     2.7  ok (contrast 7.8)
       fold          -117 to -141   28     1    31    3.3    5.1      6     3.6    1.5     3.9  ok (contrast 15.2)
       fold            12 to  -11   24     1    27    1.1    1.3     52     0.0    0.1     0.9  ok (contrast 5.2)
       fold          -125 to -148   24     1    25    1.0    1.1      8     8.5    0.8     1.9  ok (contrast 4.5)
       
       limits: fit95 6.0, fitmax 10.0, dropped 33.0, bends 4.0, ragged 2.0, texture 4.0 (mm, mm, %, per metre, mm, mm); the texture's own floor, the median over the curves: 1.1 mm
       the areas' boundaries: the top and the sides meet on the shoulder's curves, the sides and the underside on the lower edge's curves or, where the body has no lower line, on the skin's own end (the mesh's boundary); nothing else
       all curves pass
       ```
  10. [x] **The body sheet: the skin flattened in true size, so any design AI draws flat and the paint
     follows the body** (2026-09-29, the car mapper on the Mac; the user: "Something this tool is really
     lacking is the accuracy of following the models curvatures etc. Is there an optimised way that
     doesnt need manual or by eye ... map them so that any design AI can easily understand it and
     accurately design?"; the plan `something-this-tool-is-delegated-mist.md`).
     - **What it is** (`tool/surface.py`, its docstring the key; `car/sheet.png`, `.svg`, `.json`,
       `car/sheet_body.png` from `python -m tool.carmap --sheet`, `tool/sheetmap.py`): the left half
       of the outer skin (open ≥ 0.2, no wheel covers, no blades or struts, no slivers), cut at the top
       centreline, flattened with **libigl 2.6.3** (`igl.lscm`, then `igl.arap_solve` six rounds:
       3.7 % / 2.3° on the skin piece against 5.3 % / 3.1° from our own ARAP, so the library's) into a
       sewing pattern in millimetres: the nose's tip at the left, the top centreline along the top,
       y down; the map's lines (the shoulder, the lower edge, the folds, the openings, the joins) and
       the stations (z 150, 100 ...) drawn on it, the areas filled. The right side is the mirror by
       construction. Every Skin texel's place on it is cached (`surface.sheet_cm`, next to the bake):
       a left texel through its own triangle's weights, a right texel through the mirror twin (the
       twin found by its three corners within 0.2 cm: a centroid alone matched a long sliver to a
       small triangle 5 cm off), the 66 right triangles without a twin (the number panel's surround
       is triangulated differently) through their corners' mirror vertices, loose pieces too small for
       the sheet (the rivets, the fin's blade) through the nearest sheet triangle facing their way.
     - **Pieces, sewn by measure.** Panels with real gaps in the model are bridged by a strip of new
       triangles zipped across the gap (`_bridge`: nothing moves, the strip covers no paint, a vertex
       within 0.3 cm of the other panel's vertex is welded), in runs of 12 cm cut at corners, only for
       gaps under STITCH = 1 cm: the sidepod's top (0.6 cm off the shell) is sewn into the body piece,
       so a band carries over its edge; the tail (1.9 cm behind the rear flank) is a piece of its own,
       as are the skirt (the underside, cut from the shell along the skirt's crest, a fold the map
       draws), the diffuser and the inlet's duct. Sewing the tail strained the rear body to 6.3 % /
       3.8° (the paint round its runs bent 10°); a run whose surroundings bend over UNSEW = 8° is
       unsewn and stays an open seam at the model's own gap (none now). Pinch vertices are split
       (`_split_fans`) so every piece is manifold, as the libraries need.
     - **Measured, not looked at** (`python -m tool.carmap --check`, the sheet's table after the
       curves'): per piece and per area the singular values' 95th percentile by area over the painted
       body (open ≥ 0.4): area %, angle (how much a right angle bends), stretch (the most a length
       changes), and the biggest patch over twice the limits (a sheared corner is small next to the
       body: a percentile let the user's spot through). Now: the body 5.2 % / 3.3° (its top 4.1 % /
       2.4°, its sides 7.2 % / 4.5°, the biggest patch 99 cm² at the sidepod's corners), the skirt
       3.2 % / 4.2°, the sidepod's top (sewn in), the tail 1.7 % / 1.6°, the diffuser 0.3 % / 0.7°, the
       duct 2.1 % / 1.4°: the body misses the 5 % / 3° targets by the sidepod's corners, where the
       surface turns through three faces. A 20 mm stripe drawn at any of 12 angles is 20 mm on the paint
       within 0.92 mm over 95 % of the painted body (11.5 mm at most, at a corner). 30 mm below the
       shoulder on the sheet is 30 mm along the surface within 1.28 mm at 95 % of 144 places (5.0 mm at
       most), by exact geodesics traced on the piece's mesh (**potpourri3d 1.4.0**, `GeodesicTracer`);
       the sheet agrees with potpourri3d's log map round the left flank's spot within 2.0 mm over 10 cm
       (the log map is sound near its source only: far vertices came out small). Symmetry: the right
       side's vertices mirrored lie on the left surface within 0.00 mm (95 %), 2.1 mm at most.
     - **Darts, tried and turned off.** Where a piece can't lie flat, a dart (a cut from the worst
       patch's heart to the nearest edge by the way of most strain, the fan at its end opened too) got
       the body to 4.5 % / 2.9° / 42 cm² with five short darts at the sidepod's corners: but a dart
       breaks every line drawn across it, and the user's rule (their close-up of the sidepod's rear
       corner: "The lines don't follow continuously") is unbroken lines first. DARTS = 0: the corners
       shear a little instead, measured and named. The code stays (`_dart`, `_cut`, `flatten_piece`).
     - **On the painted texture** (`python -m tool.sheetcheck <car>`, `tool/sheetcheck.py`; the user:
       "Your numeric checks must have missed this, so the checks are wrong too"): continuity (texel
       pairs next to each other on the car whose sheet places jump off any declared seam: a dart, an
       opening, a join, the cut at the skirt's crest), scale (the local stretch and shear of the map as
       painted, from each texel's neighbours), and crossings (every band's centre fitted on both sides
       of every join and UV seam it crosses: the sideways gap and the turn). TSC_Map_Sheet before the
       fix (six pieces flattened apart): 99 % of texels stretched under 13.6 % and sheared under 8.7°,
       1,068 cm² over 10 % / 6°, the worst patches at the tail's corners (up to 1,300 %: the old
       texel lookup clamped points outside their triangle onto its edge). After: 5.7 % / 3.9° at 95 %,
       14.0 % / 8.9° at 99 %, 1,268 cm² over the limits in patches at the nose's tip (135 cm², a cone's
       apex), the cockpit surround's rivets (131 cm²: domes mapped onto the flat surround) and the
       sidepod's rear corners (107 cm² each side, stretch up to 39 %: the sewn corner). Continuity:
       238 texel pairs (of 8 million) jump up to 8.5 mm off any declared seam, at the sidepod's inlet
       rim on the right. Crossings on TSC_Map_Sheet: 10, 2 over the limits: the 30 mm band at the
       sidepod's rear corner join, gap 1.64 mm, turn 7.4° (the corner; the turn measure takes the
       band's own bend round it as well); the nose panel's joins 0.26 to 0.37 mm and 1.1 to 1.2°. On
       TSC_Map_Proof: 4 of 10 over: the pale band 48 mm below the shoulder steps 18.6 mm at that
       corner, where the map's own shoulder is two curves (the sidepod's edge ends, the rear flank's
       crease starts lower): a band offset from each steps with them; the teal band 4.9 mm and 8.3°.
     - **Designing on it** (`tool/shapes.py`, `tool/sheetink.py`, `tool/paintbox.py`): `shapes.sheet`
       (an SVG in the sheet's frame, a picture with its box, polylines with a width, or a function of
       x and y in mm, rasterised once at 2 px/mm, `Ink`, and read per texel through the cache: the
       paint box hands a zone its texels, `shapes._TEXELS`), `sheet_line`, `sheet_near`, `sheet_lines`,
       `offset`, `along_cm`, `across_cm`, and `s.decal(picture, "sheet", at=(x, y), width=mm)` with a
       note when it crosses a fold, an opening or a seam. A decal's lettering reads backwards on the
       right side (the sheet is the mirror), like the tyres' words. The old zones are untouched:
       TSC_Tricolore, TSC_Map_Areas and TSC_WindTunnel paint texel-identical before and after (sha256 of
       every texture). Test cars: TSC_Map_Sheet (a 10 cm checker and three offset bands, drawn only on
       the sheet: `car/map/sheet.jpg`) and TSC_Map_Proof (`car/map/proof.jpg`: petrol blue, gold
       pinstripes along the shoulder, the lower edge and the folds, bands at 25 and 48 mm, contour
       lines every 25 mm, three roundels, a "10" decal on the sidepod's top). `python -m tool.joins
       <car>`: close looks at every join between panels, both sides.
     - **libigl's curvature as a second measure** (`mapcheck.curves`, the `igl` column): the crest's
       bend by `igl.principal_curvature` (three rings) over the body's median, beside the map's own
       contrast: the named lines and most folds stand out on both (the shoulder 3.0 / 3.5, 6.2 / 9.6;
       folds 5.9 / 10.5, 5.7 / 8.5), two weak folds on neither; libigl marks 7,836 of 14,678 welded
       vertices unfit for its fit (loose panels, thin pieces), and per vertex the two measures
       correlate only 0.26.
     - **Found on the way, not this step's:** the map built fresh on the Mac differs from the PC's
       recorded state: 66 ridges and 12 folds against 62 and 8, and `--check` fails 4 stretches (the
       shoulder over the rear flanks: ridge 0.85; the lower edge at the sidepods: a 16 cm step) and 1
       curve (the shoulder 188 to −50: ragged 3.4 mm, texture 4.2 mm) where step 9 recorded all
       passing: the ridge tracing isn't the same on the two computers' numpy. To look at.
     - **Round 2 (the user's two close-ups: "The lines don't follow continuously"; "the lines are such
       a mess (hidden, wobbly, not even connect)"; the earlier project's lesson, trackmania-skin-studio's
       `forge/composite.py` and check 17: a line or a band is a function of the point on the car, the
       distance to ONE smooth 3D curve, continuous across every seam, join and gap by construction; the
       sheet is only for lattices, logos and decals).**
       - **The design lines** (`Map.design_lines`, `BLEND_*`): each named line as one smooth curve per
         stretch the body carries it on: the map's measured curves (unchanged, for the check) chained
         nose to tail and each gap bridged by one C2 cubic B-spline through both (no knot inside a gap;
         the bridge put back on the skin and smoothed); a gap is bridged when it is under 15 cm (a
         corner) or under 60 cm with the chord within 60° of both ends (a continuation), so the lower
         edge's 25 cm drop from the nose's lip to the skirt's crest at z 70 stays a hand-over and its 64
         cm behind the sidepods a break. For the shoulder the measured line's stretch on the shell's own
         edge round the sidepod's top (kind 4, z 34 to -12, a panel gap, not a crease) is left out and
         bridged: a band offset from it had wrapped round the panel's corner. Result: the shoulder one
         curve, z 207 to -154, 428 cm, blends at the nose's tip (26 cm), over the sidepod's front (79 cm,
         crossing the inlet's mouth, a hole: up to 19 mm off the skin there, 2.5 mm elsewhere) and at
         the sidepod's rear corner (32 cm, 10 mm off in the slot); off the measured curves outside the
         blends by 2.7 mm (95 %). The lower edge in three (the lip 207 to 71, the skirt 69 to -32 with
         a 31 cm blend, the tail). Drawn on the sheet in a paler shade, the blends orange (`car/sheet.png`,
         `.json`: `lines.design-shoulder`, `design-lower`, `blend`).
       - **Bands from the curve in 3D** (`shapes.line_offset(kind, d_mm, width_mm)`; `line` and `near` on
         "shoulder"/"lower" now go by the design lines; `across_level` tests the line's existence by its
         z span, not the nearest point's z, which had sent the shoulder's bands along the skirt's edge):
         the exact signed distance to the one curve (`Map.across_level`); on this body the chord is within
         0.2 mm of the arc at 30 mm on the tightest 9 cm crease, and the exact geodesic check holds.
         potpourri3d's signed heat method wants each curve segment inside one face, so it wasn't used.
         `sheet_line`, `sheet_near`, `offset` stay for drawings on the sheet only.
       - **The sheet for lattices and decals; lettering reads on both sides** (`_sheet_decal`: the right
         side samples the picture flipped). **A decal never straddles a panel's edge, a fold, an opening
         or a seam:** its box is moved up to CLEAR = 60 mm clear (a note says from where to where) or it
         is refused (a FAIL note saying where); and its size on the paint is measured (the painted
         texels' extents along their two principal directions against the picture's): aspect off by
         over ASPECT = 3 % is a FAIL note. TSC_Map_Proof's roundels as decals: the front flank's 2.6 %
         (at 60 mm below the shoulder; 11.6 % at 110 mm, on the flank's roll toward the lip), the
         sidepod's side 5.6 % FAIL, the rear flank's 8.0 % FAIL (the sheet shears there), the "10" 1.6 %,
         one roundel moved 30 mm clear of the sidepod's edge.
       - **The model's pieces** (`tool/pieces.py`, `car/pieces.json`, a table in `car/map.md`): the body
         (wheel covers out) is 9 pieces of 5 cm² or more, 156 edges shared by three or more triangles.
         The main piece (the shell, the rear flanks, the skirt, the nose, the cockpit surround, the engine
         cover and its loose panels: 55,054 cm² both sides); the sidepod's top (2,528 cm² each, 0.41 cm
         off the shell at the closest, 19 % of its edge within 1 cm, 35 cm² of shell hidden behind it);
         the tail (3,585 cm², 1.74 cm behind the rear flank, 104 cm² hidden behind it); the inlet duct
         (1.39 cm off); the diffuser and its strakes (0.05 cm, 158 cm² hidden); the fin's blade. "Hidden"
         paint in the user's close-up: the 3D bands paint the shell's rim under the sidepod's top and the
         skin inside the slot (open under 0.2, not on the sheet), which the viewer shows only edge-on.
       - **The crossing check redone** (`sheetcheck.crossings`): every band's line walked on the car in
         2 mm steps, a crossing wherever the panel or the texture's island under it changes (so the
         sidepod top's own edges count, which the sheet's sewn edges had hidden); at each, the painted
         band's texels either side within 1.5 cm along the curve, their offsets from the curve (medians):
         the step; and lines fitted over 3 cm either side, the turn less the curve's own bend between
         them; not judged where the two panels face apart by over 20° (a strut under the nose, a mirror's
         mount, the sidepod's rounded rear edge against the flank), which is another surface, not a join
         of the skin. **`--falsify`:** the rear flank, the nose tip and the sidepod's top painted 10
         texels (9 mm) off along the texture, once per axis, against the honest paint: caught when a
         crossing's step moves by 2 mm over the limit or its band no longer meets the join; nothing
         falsified is cached.
       - **Numbers.** TSC_Map_Sheet before round 2 (the sheet's own offsets): 10 crossings, 2 over: the 30
         mm band at the sidepod's rear corner, gap 1.64 mm, turn 7.4°. After: 18 crossings, 0 over: the
         rear corner 0.38 mm (the 90 mm band, offsets 89.7 | 90.1), the nose panel's joins 0.13 to 0.34
         mm and 0.4 to 0.7°; falsify caught along both axes (3.3 and 8.5 mm). TSC_Map_Proof before: 4 of
         10 over (the pale band 18.6 mm, the teal 4.9 mm and 8.3° at the corner). After: 12 crossings, 0
         over (the nose panel's joins 0.04 to 0.50 mm, 0.2 to 0.6°; the rear corner's teal and pale bands
         "facing apart": the sidepod's rounded rear edge against the flank); falsify caught along u (8.4
         mm), not along v, where the shift runs along the bands at the joins it reaches. The sheet's mesh
         checks unchanged (the body 5.2 % / 3.3°, stripe 0.92 mm, offset 1.28 mm).
       - **The model or the method?** The model: nine separate pieces with real gaps (0.4 cm round the
         sidepod's top, 1.7 cm behind the tail, 1.4 cm at the inlet duct), 156 non-manifold edges, a
         doubled shell here and there, and hidden skin under the loose panels: a band drawn across a gap
         is cut by it, whatever draws it; its two sides line up only because the band is measured from
         one curve. The method's part in the two close-ups: the first sheet flattened the sidepod's top
         apart from the flank (a step in every band at its edge) and sheared the rear flank's front (the
         checker leaning); the bands were the sheet's y (a step wherever the sheet stepped); the
         shoulder's design line followed a panel's edge (the bands wrapped round the corner); a roundel
         was drawn across the sewn join. All four are gone; what remains is the model's.
       - Pictures: `build/TSC_Map_Proof_joins_before2.png` (the user's view, before) against
         `build/TSC_Map_Proof_joins.png` (after; the first tile is that view), `TSC_Map_Sheet_joins.png`,
         `TSC_Map_Proof_close.png`, `_views.png`, `_body.png`; `car/map/sheet.jpg`, `car/map/proof.jpg`.
     - **Left:** the install of TSC_Map_Sheet and TSC_Map_Proof on the PC (the user's drive, day and
       night, F12); the roundels that fail the aspect check on the sidepod's side and the rear flank
       (the sheet shears there: place them elsewhere or darts); the tail's join (a 2 cm slot: a line
       drawn across it steps); TSC_WindTunnel's bands redrawn on the sheet (its lines are streamlines,
       already traced on the surface, 1.7 cm wide by 3D distance: the sheet would change them by under
       0.4 %); the cross-computer difference (an item in `IMPROVEMENTS.md`).
  Later, once those work: what each game camera shows of the car, the flat spots for pictures
  measured rather than typed, a check on every paint for graphics crossing a fold or an opening.
- **Handover (2026-09-29, the user: "I just prefer another session with an agent that actually
  really covers the the mapping of the car and really takes close consideration because these
  mistakes are just quite stupid ... feels like a bit careless").** The session that built the map
  judged its lines from whole-car sheets and never zoomed in on them; close up they don't sit on
  the car's edges. The next session works on the map with the car mapper
  (`.claude/agents/car-mapper.md`), and nothing else built on the map moves until the user has
  looked at its lines close up and said yes.
  - **Can be trusted** (checked close up only here and there, so look again): `open` (the depth
    maps: the inlets' insides, under the nose, the wheel pockets come out hidden); the air's `hit`
    and flow (the solved potential; streamlines part round the cockpit, never merge); `along`;
    the lookup `Map.at` (a point to the body's triangle, facing the same way).
  - **Wrong, to redo:** the shoulder and the lower edge (so `area` "top", "sides", "under",
    `across`, `line("shoulder"/"lower")`, `rake`, `front_rake`, the grid and `car/map.md`'s station
    table). They're a threshold on each 1 cm slice's facing (50 and 125 degrees), outliers swapped
    for a median and smoothed along the car: on a rounded edge the line sits wherever the
    threshold falls, not on the edge the eye sees, and it wanders or makes an S where the section
    changes (the sidepods' front at z 10 to 35, under the nose's and the front flank's lip at z 80 to
    190, the nose's tip); the lower edge makes blotches at the nose. The front and back areas are a
    threshold on the facing (0.7), so they come out as blotches, not faces. The fold line uses a
    35-degree dihedral, and this car's edges are rounded, so it finds almost none of them.
  - **The idea for the redo** (the user saw it and asked for a careful session to do it): the car's
    real feature lines from its curvature. Curvature per vertex (smoothed normals, a few cm), the
    ridges where it's highest across the line, each traced from end to end as one continuous curve
    (following a ridge from slice to slice, never jumping to another), then smoothed as a curve.
    Draw them all on a clay car and check every one against the car's shading close up before
    naming any: the shoulder is the long ridge bounding the top on each side, the lower edge the
    one where the side turns under; where the body's skin ends (the lip at z 80 to 190), say so
    rather than draw a line. The front and back: whole faces bounded by those lines.
  - **How to check** (the user zooms in; so must the check): `tool.snap <name> --body` for the whole
    body, then close looks of each stretch of each line with the wheels off, both sides: the nose's
    tip, the nose, the fin's plate, the bonnet, the front flank and its lip, the sidepods' front and
    inlets, the sidepods, the rear flanks, the deck, the tail. Enlarge them (crop and scale) and look
    at every line where it meets a change in the body: on the edge the eye sees, smooth, no steps,
    no S the body doesn't make, the same both sides. Then the same lines on the flat texture (a line
    that steps in the texture steps on the car). Say what's still off before calling anything done.

### The car's lines, pinned by the user (started 2026-09-29)

The user's diagnosis, and the brainstorm that followed: "I initially thought that claude actually
knew how to paint just by having the 3d model and the UV map. But ive been learning that it paints
blindly ... wobbly lines, or disjointed lines." And: "Is there anything that I can help with the
mesh? Maybe we build a tool to build the tool?" Yes: the one thing Claude can't do is see and click.

**What was checked before pivoting.** Nadeo's files hold no design lines: the stock `Skin_B` is a
flat grey, `Skin_AO` is soft baked shading (panel gaps and recesses, no creases sharp enough to
trace), the template `UV_Skin.png` is the mesh's wireframe, and the body takes no normal map. The
mesh (2 cm, 27k triangles, nine pieces with gaps) is fine to paint on and poor to read lines from:
that is why ten steps of curvature-derived lines still looked like crayon and came out different on
the two computers. Most lines a designer wants (a swoosh along the side) aren't mesh features anyway:
they look right from a viewpoint. The plan (the Mac, `~/.claude/plans/hi-i-need-to-lucky-parnas.md`):
the user pins the car's lines, Claude draws everything else on blueprints. `IMPROVEMENTS.md` has the
order and the early stop.

**Step 1, the lines room (done 2026-09-29).** `lab.html?room=lines` (`viewer/lab-lines.js`; in the
car's menu and the rooms' bar as "The lines"). The stock car, turned by a drag, Left/Right/Front/
Rear/Top buttons. A click on the body pins a point (the viewer's `onPick`, the same as a note's);
the pins are numbered dots over the car (`viewer.track`), the curve through them a thin yellow tube
on the body (`viewer.curves`, new) and its mirror a dimmer one. A click beyond an end carries the
line on, a click between two pins adds one there (the nearest segment), a click on a pin picks it
(then a click on the body moves it, Delete takes it off), Undo (also Ctrl/Cmd+Z, 60 steps). A line
has a name (a list of suggestions to start from: shoulder, lower edge, sidepod top and bottom, the
arches, nose crease, tail edge; any name works) and "Both, mirrored" or "This side only". A click on
the inner car (the Wheels or Details map) is refused with a line saying what it hit: the lines live
on the body. Everything saves as it changes (`POST /api/lines`, 400 ms after the last change) to
`car/lines.json`, committed: a small asset, the same on both computers (points in cm, 0.01; normals
for the snap).

- **The curve, the same in the page and in the paint.** A centripetal Catmull-Rom spline through
  the pins (the ends carried straight on), put back on the body and smoothed: in the page
  `viewer.snap` (a ray along the pin's normal, either way, the nearer hit within 5 cm) then a
  moving average over ±2 cm, then snapped again; in `tool/lines.py` the same spline every 0.25 cm,
  `carmap.Map.project` (the nearest point on the skin) and a Gaussian of 1 cm, twice, then
  projected once more. The user pins roughly; the curve is allowed to miss a pin by a few mm to
  stay smooth, and `python -m tool.lines` prints by how much per pin (on a test line whose pins
  were 3.6 mm off the body on purpose: 2 to 7 mm).
- **The paint box goes by the pins first.** `shapes.line(name)`, `near(name, reach)` and
  `line_offset(name, d_mm, width_mm)` take a pinned line's name before the map's line of the same
  name; `line_offset` is the signed 3D distance to the curve (nearest point, the sign from N × T
  oriented down the body, or outboard where the line runs up and down), both sides when mirrored.
  An unknown name raises with the pinned and the map's names. Existing skins unchanged.
- **Tested** by driving the room in the hidden browser (Playwright, the scratchpad's
  `drive_lines.py`): six clicks along the map's own shoulder (one refused: from the left it landed
  on the front wheel), a pin picked and moved, a pin added between two, Delete then Undo, "This
  side only", a rename, a second line, the list, the top view with the mirror; the file after each
  step read back through the API; a bad name refused with 400. Pictures in
  `build/lines_room/`. Not yet: the user's own pins.
- **Next:** the user pins two or three lines and looks at them close up (step 2 of the item in
  `IMPROVEMENTS.md`). Only if they convince: the blueprints.

## Decisions (for Claude)

- **The foundation comes first (user, 2026-09-23).** The tool must truly know the car: every
  part, found along the creases, and every material, checked in the game. Design tools come
  after.
- **A universal tool (user, 2026-09-23):** any kind of skin, not a fixed set of styles.
- **Looks before speed (user, 2026-09-23).** Up to about 10 minutes a round is fine if the skin
  is clearly better.
  The same for the build: a better game file is worth a slower install (user, 2026-09-24).
- **One design or a few (user, 2026-09-23):** one when the idea is clear, 2–3 takes when it's
  vague.
- **Wanted extras (user, 2026-09-23):** a local picture maker and a page of all skins. Sharing
  skins and copy-from-picture aren't wanted for now.
- **The game's cameras in the viewer (user, 2026-09-25):** Driving opens a choice of the
  game's cameras that show the car, not the cockpit ones. Built as a placeholder: Cam 1 is
  matched to the user's screenshot (then centred and closer, at their wish); Cam 2 is a guess,
  labelled so, until a screenshot of it comes (`VIEWS.cam2` in `viewer/viewer.js`). Any other
  camera that shows the car joins the menu the same way, each matched to a screenshot.
  **The user's way to set them (2026-09-25):** by eye, in the viewer next to the game. Picking a
  Driving camera and moving the view shows "Copy Cam N", which copies the camera's position,
  the point it looks at and the lens. The user pastes that in the chat; Claude squares it up
  straight behind the car (keeps the height, the tilt, the distance and the target's height
  and depth, sets the side-to-side to zero) and writes it into `VIEWS`. What they set is in
  the viewer's framing (the list on the left, `FRAMED`), so it's kept as seen there, not
  converted to the game's full screen. All three set that day, standing still. Cam 1 and 2
  were set twice: first aimed at the car, then at a point above it, so the car sits low in the
  picture and the track ahead shows, "the game's intention" (the user). Cam 1 2.47 m up and 12°
  down at a point 1.32 m up, near the first screenshot's framing; Cam 2 lower and a little
  closer, 1.82 m up and 6° down at a point 1.28 m up (not the farther camera guessed before); Cam 3 over the driver's shoulder, 1.08 m up, almost level, 0.9 m behind a
  point over the bonnet. Cam 3's first try met the orbit's 1 m limit, so a Driving camera may
  come to 0.2 m (`DRIVING_MIN`), and the user set it again closer and lower. The same evening the
  user sent the game's Cam 1, 2 and 3 as screenshots, and all three were fitted to them, lens
  and all (Things we learned, "the game's lens"); their by-eye settings are in the comment on
  `VIEWS`. A Driving camera now frames the car at the game's size (`GAME_FRAMED`: no zoom-out),
  lifted 12 % so the pad doesn't cover the tail. Next: the pull-back at speed (`IMPROVEMENTS.md`).
  **Since 2026-09-27 (the user):** Cam 1, Cam 1 alt, Cam 2 and Cam 2 alt (each key pressed
  again), fitted to the calibration car's screenshots; Cam 3 is out (the game hides the cockpit
  there). **The same day, the viewer's own lens for them** (the user: "I honestly hate the cam
  lenses... the car in the viewer looks really badly distorted"): the game's 70 to 75° lens,
  right on a big screen, bends the car in the viewer's smaller picture. Each Driving camera keeps
  the game camera's line to the car's middle (so its angle on the car) and the middle's height in
  the picture, through the 32° lens, 7 to 14 m back (`VIEWS`' `ours`), where the tyres' widths
  across the picture, rear and front averaged, are the game's. Keeping the middle's size alone
  drew the car too small: the wide lens enlarges the near rear tyres. The game's poses stay in
  `VIEWS`; `?lens=game` (and `tool.snap --cams`) still draws them for pictures set beside the
  game's.
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
- **DDS files come from our own writer:** our own block encoders (numpy), a legacy header and
  a mip chain. Pillow's BC1 was 5 dB worse (2026-09-24).
- **Install:** one zip per skin, no spaces in its name, with `Icon.tga`, recorded in
  `skins/installed.json`.
- **Viewer must-haves (user, 2026-09-23):** spin and zoom, day and night, hide and show parts.
  Comparing versions isn't wanted. The setting is a photo studio, not the game's stadium
  (user, 2026-09-24).
- **Viewer look (user, 2026-09-25): "race garage",** chosen from three mockups (showroom, race
  garage, just the car): skins listed on the left, slanted Teko lettering, one yellow-green
  accent (#e8ff47). The car, studio and lighting stay as tuned against the game.
- **Free tools only (user, 2026-09-23).** If a paid tool would be far better, tell the user and
  discuss it first. The picture maker is free and local.
  **One-time-payment tools of incredible quality: always suggest them (user, 2026-09-24).**
  Subscriptions still need a discussion first.
- **The user has Club access (2026-09-23),** which custom skins need.
- **Everyday model (user, 2026-09-25): Opus 5.5,** after checkpoint 7's comparison.
- **Models (user, 2026-09-23):** the user can use Fable 5.1, for the steps that need the best.
  Fable 5.1 runs checkpoint 3 and the first round of checkpoint 7, and is the step-up when a
  step stalls. Opus 5.5 handles the other hard steps, and Sonnet 5 the straightforward ones.
- **This PC (2026-09-23):** an RTX 5070 Ti with 16 GB, a Ryzen 7 5800X3D, 16 GB of RAM and
  Python 3.14.2.
- **Credit:** amogusstrikesback2, CC-BY-4.0, wherever the car model is reused.
- **Don't take the game's own files apart (2026-09-24).** The user asked twice whether Claude
  could read the game's shaders to get exact answers. Claude declined: the game's data is in
  encrypted packs and its shaders are compiled code, so reading them means decrypting Ubisoft's
  files, which the licence forbids, and it would still not replace tests in the game. What's
  fair game: Nadeo's published files, the stock textures, the user's in-game tests and
  screenshots, and files the game's own skin editor saves, if the user copies one out for us.

## Things we learned

- **2026-09-29, the Mac without Docker (the user: "I don't need docker anymore because I now have
  my personal mac").** The Mac runs the tool itself, like the PC: Homebrew's Python 3.14.7, a venv
  in `~/Library/Application Support/TrackmaniaSkinChallenge` (`paths.WORK`), the PC-only packages
  (the picture maker's) marked `sys_platform == "win32"` in `requirements.txt`. The container,
  `docker/serve.py` and `docker/snap.mjs` are gone: `tool.snap` takes the Mac's pictures with
  Playwright's own headless Chromium (`--only-shell`, 200 MB in the work folder's `browsers`), which
  draws WebGL on the M5 through ANGLE's Metal backend (`paths.launch`); `tool.snap --page` photographs
  any page, as `snap.mjs --page` did; `tool.prepare` downloads Nadeo's template itself. The user
  browses in Safari; the snapshots don't need Chrome installed. The Sketchfab model zip is copied
  from the PC (git-ignored).

- **2026-09-28, the Lab slow (the user: "the website now is soooo slow").**
  - A three.js page drawn in `setAnimationLoop` draws at the screen's rate. On the user's 239 Hz
    screen, the stand's two cars cost 70 % of a processor core while nothing moved.
  - Same-origin iframes share the page's main thread, so a hidden second viewer slows the one the
    user is using.
  - Drawing only when something changed brought it to 1 %. The canvas keeps its last picture
    through the frames that draw nothing. Look for anything that moves by itself before doing
    this: the standalone viewer's driving does, so it still draws every frame.
  - Measure before guessing. A scratch script drove the Lab in headless Edge and timed three
    things: the load, the long tasks (a `longtask` PerformanceObserver) and Edge's CPU over 6
    still seconds. For the CPU, it summed psutil's `cpu_times` over the browser Playwright
    started and all its children, the GPU process included. Headless Edge ran at 240 frames a
    second, like the user's screen.
- **2026-09-28, the notes on the car made safe (the Lab as a factory, step 9.0).**
  - **Windows refuses to replace a file another program has open:** the page's 1.5 s poll,
    OneDrive, Defender. Every writer of a file the page reads retries its `os.replace`
    (`notes.save` now does, as `view._write_json` already did).
  - **Three writers, one file.**
    - The server's threads, the hook (another process) and the command line each rewrote
      `notes.json` whole, with no lock. Two writes at once could lose a note, or give two notes
      the same number.
    - A lock made with `os.mkdir` fixed it. It's atomic, and it holds across the Mac's container
      and host, where file locks don't reach.
    - Checked: 100 notes from two threads, with the hook run 30 times and a reader holding the
      file open, came out as 100 unique numbers.
  - **The notes left git** for `.notes/notes.json`. Answers and state changes would have churned
    a public file that both computers pull at the start of every session. Each skin's `notes.md`
    stays the record.
  - **The embedded viewer's pedal keys:** nothing counts the turbo down in the Lab (the drive
    loop doesn't run there), so a T left the car glowing for good. The keys now drive only the
    viewer's own page.
  - **Baselines hold to the pixel:** Claude's snapshots and the standalone viewer render the same
    from run to run in Edge on the PC, so a Lab change that leaks into them shows at once.

- **2026-09-27, the tyres' map and the markings (`CHECKLIST.md`, "Tyre markings").**
  - **A skin can't change how the tyres are mapped.** Only a "3D skin" (a whole car model through
    NadeoImporter and a community fix-up script) gives each wheel its own mesh and UVs; Nadeo
    disabled uploaded 3D skins in May 2024 (Eole on the Ubisoft Discord, quoted on Steam): they
    show only on the PC that installed them by hand, not on consoles, and can crash. Nadeo's 2020
    post promised UV maps "for each set"; its link is dead, and today's download has no wheel
    template. Nobody online describes the wheel map: the mesh is the source.
  - **The map** (1024x2048 as shipped): columns across the tyre, the inner bead (u 0, 29.8 cm from
    the axle) to the outer bead (u 1), the tread u 0.2 to 0.83 (35.6 to 36.4 cm, 26 cm across on the
    front tyre); rows once round, row 0 at 10 o'clock seen from the left, anticlockwise from there,
    about 45° per 256 rows but not exactly even (43.9 to 45.4), so the tool reads each row's angle
    from the bake. The rear tyres are the front's 10 % wider in x, the same radii, the same texels.
  - **The right tyres are the left's mirror image** (the same angle maps to the same row on both
    sides, and the outer sidewall uses the same columns). A word reads backwards on the right, but
    the mirror of a word whose letters are the same upside down (B C D E H I K O X, 0 3 8, - + = <
    > |) is that word turned half a turn with its letters' tops toward the hub: it reads right on
    both sides (seen in the viewer: on the right, the copy at 6 o'clock reads upright). Drawn upright
    (a slant flips), and symmetric top to bottom (the bottom half mirrored up: B's bowls and K's arms
    differ in most fonts). Arrows round the wheel point the way it rolls on both sides for free (the
    mirror keeps forward forward); rings, dots, stars, chequers don't mind.
  - **What shows:** the wheel covers hide the sidewall inside 30.2 cm; the stock `Wheels_AO`, which
    the game applies and a skin can't replace, darkens three patches inside 31 cm (under Nadeo's
    marks) and faintly lines the stock grooves (80 %) on any tread; the tread starts at 35.6. So
    markings live in 30.9 to 35.3 cm, 4.4 cm: the band on this car is thin, so lettering wants caps
    of 2 to 2.5 cm (half the band) to read at all.
  - **Zip cost:** a marking over the stock tread adds about 1.7 MB zipped (the upsampled stock tread's
    scuffs in `Wheels_R` and `_B`); one with its own tread pattern 0.3 MB, a slick 0.05 MB. When a zip
    runs over, `build_zip` halves `Wheels_R` before any other roughness map.
  - The long Python heredocs the Bash tool sends through Git Bash get cut off after a few hundred
    lines with "unexpected EOF": write the script to the scratchpad with the Write tool and run it.
    Two more that corrupted a pushed file: GNU sed reads a backslash-backtick as "the start of the
    text" (it put a backtick before every line), and a Python string that isn't raw reads a Windows
    path's backslash-and-digits (the screenshots folder's "2225070") as a character code. Edit docs
    with the Edit tool, or copy lines from git.

- **2026-09-27, the viewer on smaller screens (`CHECKLIST.md`, "The viewer on smaller screens").**
  - **Zooming never distorts the car; moving the camera does.** A fixed lens top to bottom (32°)
    makes a narrow window see less across; zooming the picture out keeps the car's shape (only the
    camera's place sets its perspective). The "distortion" never showed in a still picture: it was
    the car shrinking into a mostly empty screen, the floor's grid then reading like a wide lens.
  - **Frame the car by its outline, not a rule of thumb.** The old rule (fit a 1.3-wide box) left
    the car 77 % of full size beside the list in a 1100-wide window and 36 % on a phone; its outline
    swept all the way round is only about a tenth wider than the front view's, so a spin-safe fit
    costs little. A 3/4 view's outline sits left of the car's centre (the near front wheel looks
    bigger): centre the outline, not the centre.
  - **A glide between views has to carry the framing too**, or the zoom jumps at the start: every
    framing is one view offset of the whole window (x, y, zoom), so a glide can blend two of them.
  - **CSS:** a rule scoped by a parent id (`body.lightStudio #bar .sk:not(...)`) also reaches the
    menus inside that parent; a transform (the buttons' skew) widens `getBoundingClientRect` but not
    the layout, so measure a wrapping row by the rows' tops.

- **2026-09-27, the studio render (`CHECKLIST.md`, "The studio render").**
  - **Haze came from light, not from the picture.** The studio HDR lit the car from every side (76 %
    of the light on its top), so faces the key missed were nearly as light as the tops; and the
    paint's full dielectric sheen lifted every dark colour by a near-constant amount, like a veil.
    A sky whose sun is the key (the sky's own sun disc cut out) and half the sheen matched the
    game's greys from black to white, by day within a few levels.
  - **A seamless cove shows its bend** where the floor turns into the wall, however smooth, because
    the two face the light differently: lit as flat floor everywhere (the normal up, no shine) it's
    one even colour and no line shows.
  - **A shiny or satin floor catches the sky's bright spots** as blotches the room doesn't have;
    the studio's surfaces are matte.
  - **three.js:** materials whose `onBeforeCompile` code differs need their own
    `customProgramCacheKey`, or the first one's program is reused; `Reflector` takes the mesh's own
    +z as the mirror's normal (turn the mesh, not the geometry); a ground shadow's depth pass must
    be depth-tested; `scene.environmentRotation` turns the sky the other way to its Euler (the sun's
    new azimuth is the old minus the turn).
  - **In the game's Cam 2 screenshots, the spot beside the engine cover's panel is the player's
    lettering** ("FCP 00"), not paint: measure the deck elsewhere.

- **2026-09-27, the four moods (TSC_Calibrate in the editor's test drive, standing still).**
  - **The game maps light to the screen straight, clipping each channel at white.** By day the
    grey scale on the tail's top reads 54 81 115 158 205 248 255 255 (pure black, the six
    ColorChecker greys, pure white): mid-grey where the viewer's ACES had it, but N8 and white
    clip where ACES rolled them off (216, 230). A light blue (#00b4ff) glow turns cyan (7, 254,
    254) when bright, never white; yellow and magenta clip to (253, 253, 70) and (254, 130, 206).
    Three.js's `LinearToneMapping` at exposure 1.44 lands within 4 levels on average; Khronos
    Neutral, AgX and ACES were 9 to 27 off.
  - **Glows, standing still:** "always on" shows its own colour a little dimmed (0.63 of it on the
    screen by day, 0.8 at night). "Night only", the front lights and the brake lights are off by
    day and on at night and at sunset (1.6, 2.5 clipped to cyan, 1.6); sunrise is like day. So the
    front lights aren't lit by day: the "bright white by day" of 2026-09-24 was white paint.
    **Energy stayed dark in all four moods** on the track (it glowed dim red in the garage).
  - **The moods' light on the tail's top, against the day:** sunrise about 0.28 and neutral;
    sunset about 0.35 and warm (the white patch 245, 199, 193, mid grey 120, 87, 85);
    night about 0.03 there, but not even: the deck and the tail's back face, which see the lit
    stadium, are 3 to 8 times brighter than the flat top, which sees the dark sky. By day the
    back faces are in shade (N5 at 48 against the top's 158): on this map the sun is ahead.
  - **Cam 3 hides the cockpit** in the game: no steering wheel, no canopy lamps, the canopy's
    glass dark over it. The viewer showed them; Cam 3 left its menu the same day (the user).
  - **The game letters the player's name and number** ("FCP 00") on the engine cover even in the
    editor, over the paint.
  - **Fitting a game camera** (Cam 1 alt and Cam 2 alt): the tyres' outlines and the track's
    vanishing point, solved for height, distance, pitch and lens (`scipy.optimize.least_squares`,
    a soft L1 loss). What made it work: each tyre's outer edge on 15 rows and top on 9 columns,
    scanned in from the track (dark = under 0.6 of the track's own brightness, so the grey
    sidewall counts); the model's outline at the same rows and columns found exactly, where the
    projected triangles' edges cross them (a rasterised outline gives the solver nothing to follow
    for small moves); the game's overlays masked (the inputs, the timer, Ubisoft Connect); the
    horizon from the green strips along both track edges, fitted as lines with outliers dropped.
    Tyres alone can't tell a closer camera from a wider lens; the horizon settles it. Checked on
    Cam 1 and 2 (within 6 cm, 0.4° and 1.5° of lens of their 2026-09-25 fits); Cam 1 alt 2.03 m
    up, 3.00 m behind, 7.7° down, 75.0° lens, 1.2 px; Cam 2 alt 1.53 m up, 3.20 m behind, 3.3°
    down, 69.9°, 1.8 px. By day only: at night the track is as dark as the tyres.

- **2026-09-27, a faster show (the code check's first two clean-ups).**
  - **The gaps between UV islands were filled from scratch at every build.** `raster.fill_holes`
    found each texel's nearest covered texel (a distance transform, 0.9 s at 4096²) for every map
    of every set, every time textures were built: each step's Studio frame, then four more times
    at the end (the last frame, `summary()`, the viewer, `save_painted`). The Canvas had already
    found the same nearest texels for its positions; it keeps them now (`Canvas.near`, flat int32),
    and `Skin.textures()` is built once when the design is done (`end_steps`) and reused. On
    TSC_ChaosElegance_Unravelled_CMYKRise (5 steps) a show went from 112 s painting + 17 s export
    (+ an untimed summary) to 87 s + 6 s, with `painted.npz` identical, texel for texel.
  - **The UV map's data (23 s) no longer rebuilds after every edit to `paintbox.py` or
    `view.py`:** of those it takes only `paintbox.SIZES` and `UVMAP_VERSION` (bump it when
    `export_uvmap` or `_surfaces` change what they write), in `uvmap.key`.

- **2026-09-26, a whole concept round (TSC_ChaosElegance_Kintsugi, _Thrown, _Unravelled).**
  - **A borrowed helper can repaint what a step just painted.** TSC_Stealth_CMYK's `stealth_base`
    ("the inner car") also paints the body matte black: it covered Kintsugi's porcelain and gold
    with no note. Read a helper before reusing it; the tool doesn't warn yet (`IMPROVEMENTS.md`).
  - **Value noise finer than a few cm makes facets.** `noise.value` flattens at every lattice
    point, so a drop's edge wobbled by noise at 1.25 cm came out many-sided; at 3 cm it's round.
    Only the close looks showed it.
  - **Small glossy shapes on a dark matte body catch the sky as white dots from behind** (the
    chase camera's side): Thrown's drops in wet look. Satin fixed it. A wet-look or gloss deck
    also washes out from behind in the viewer's studio light.
  - **Paint in 3D, then pushed, folds lines into loops.** Contour lines of a stripe field with
    noise added only go wavy; moving the points by a noise vector before measuring the stripe
    (domain warping) folds them into marbled swirls (Unravelled's tail).
  - **Crimson drops on black read as blood.** An "elegant" brief took ultramarine instead.
  - Painting took 60 to 100 s per concept; most of the round's time was Claude's own fix rounds
    (seven paints for three concepts), each shown live in the Studio.

- **2026-09-26, the first car built in the Studio (TSC_FlagPeel_CostaRica), and three fixes after
  it (the user asked: "Are they quick to fix? Can you do them?").**
  - **Clay and white paint look alike.** The flag's white on the cockpit rim read as parts left
    in clay inside the cockpit. `Skin.clay()` now marks the clay texels, later paint clears them
    (a peel puts back the layer's own), and `Skin.still_clay()` names every part with a fifth or
    more of its texels still clay: a note from `show` and `install`, and on the Studio's last
    step a "Still clay" row, the parts lit on the car ("Nothing: every part is painted" when
    none). Painting a part "clay" on purpose counts as painting it. The Studio's rows had also
    ignored `hidden` (`.row` is a flex box): an empty "Your words" showed on every step with no
    words.
  - **An assembly's name reaches further than it seems.** "front wing" is the wing, its
    endplates and brackets (inner car) and the pylons under the nose (body): the wing's stripes
    landed on the pylons, over the wrap. `Skin._warn_reach` notes it when a name is both an
    assembly and a part, or its parts are in more than one texture set, and gives the `|part`
    phrase. "floor" and "sidepod" reach as far.
  - **A flag draped round a line along the car fans out near the line.** Stripes as angles round
    a line at the floor's height looked right on the body, but on the nose's underside, close
    to the line, they spread into a sunburst. The line drops 30 cm under the nose, so its tip is
    red all over.
  - **Snapshots on the Mac.** The container can't drive the Mac's Chrome: that needs Chrome's
    DevTools port open beyond 127.0.0.1, which the safety check refused (rightly). So
    `docker/snap.mjs` (Node 24, nothing to install) drives the Mac's Chrome headless on
    127.0.0.1, takes the views `tool.snap --shots` lists, and hands the pictures to the
    container through the repo's `.snap/` folder (git-ignored, `/app/.snap` inside), where
    `tool.snap --tiles` makes the same sheets. The container has no Arial: its labels are in
    Russo One. Six views take about 6 s on the M5.
  - **Worn paint (`tool/wear.py`, the user: "more on looking worn, the flag? Instead of torn
    paint?").** Chips down to bare aluminium mirrored the dark room and read as black specks:
    light grey primer reads as worn paint (and hides, rightly, on white). Chips low on the sides
    up to a fixed height made a speckled band that read as a pattern: the line now wanders and
    the chips come in patches. Clear coat failure over a fifth of the top in 20 cm patches read
    as camouflage: a few big patches on the highest faces, chalky inside, with a lighter lifting
    edge, read as sun damage. Scrapes need their gate (outer side, wall height, patch) as a
    hard switch, not a sum: summed, almost none got through. The picture takes a close row
    per take now (`--close-row` again).
- **2026-09-26, the Lab (materials).**
  - **Finish names with a colour word in them were being split.** In "brushed titanium",
    "titanium" is a colour, so the phrase became the brushed steel finish in titanium grey.
    "polished aluminium" became gloss paint in aluminium grey, with "polished" left over.
    `finishes._pull` now takes out a Lab code, or a whole name (or alias) of two or more words
    that holds a colour word, before the colour words are read. That covers only finishes with
    their own colour; "piano black" would lose its black.
  - **What that changed in existing designs.** Painted again with the old and new tool on the
    Mac:
    - TSC_RatRod's brushed-steel wheel covers and rims are about 18/255 lighter (the finish's
      own steel, not the colour word's);
    - TSC_Stealth_CMYK and TSC_CMYK_BlackTail's titanium exhausts are 13/255 rougher (brushed
      titanium's own 0.5, not brushed steel's 0.45);
    - TSC_Race is unchanged.

    It shows in the game only if those skins are installed again.
  - **Patterns must read at the car's scale.** A knurl at 3.5 mm vanished on the ball, and would
    have on the car (a Skin texel is about 0.9 mm): 8 mm reads. The wear looks at their default
    amount (scratched, dusty, faded, chipped) are faint on a 30 cm ball; the Lab's big ball
    shows them.

- **2026-09-25, finishing the inner car (TSC_CMYK_BlackTail, TSC_CMYK_EndsInK).**
  - **Nadeo's Details_N** is 2048² and three texels in four are rounding noise within 1.5/255 of
    flat: 2.1 MB zipped as it is, 0.57 MB with the noise set flat and every real detail kept
    (the faint weave on carbon parts is real, 1 to 2 %: keep it). Upscaled to 4096² it zips to
    about 2 MB, so a zip near the budget ships the relief at 2048² (8.11 MB for the CMYK car).
    At 2048² a texel is about 4 mm on most inner parts: relief reads from 1 cm up.
  - **Most inner parts share their texels with their mirror twin** (the tail frame 74 %, the
    seat 99 %): a word raised on one side reads backwards on the other. Marks that read the
    same both ways work (a printer's registration mark).
  - **The stock inner car is full of lights** a design never sees until it paints around them:
    teal lamps in the cockpit tub, bulkhead and nose, a light strip under the floor ("floor
    rail"), white front lights on the front wing's ends, an always-on ring inside each wheel,
    faint night glows on the airboxes, sidepod frames and steering, and a white always-on panel
    under the deck ("rear bumper"), hidden by the body. The turbo colour (code 160) is on the
    hubs and most of the suspension, the tail's fins, undertray and bulkhead.
  - **A glow's edge takes the code of the nearest texel**: the viewer (and the game, which
    filters the same way) blends the glow colour between texels but not the code, so an unlit
    texel of another code beside a glow lit a line of the glow's colour on that code's terms. A
    dashed line of always-on orange ran round the tail's openings, whose glow is exhaust heat.
    `paintbox.dark_take_codes` gives the unlit texels near a glow its code.
  - **A second coat left the first along every island's edge**: an edge texel is partly outside
    every triangle, and paint weighed by that coverage mixed with what was there. Paint now
    weighs by the part's share of what covers the texel (`coverage.share`): full on an edge only
    it reaches, mixed only where another part shares it. Skins repainted from now on have
    cleaner edges.
  - **The exhaust's trim shares a few texels with the tail frame**: paint the tail after it, or
    the exhaust's colour shows as dashes along the tail's edges.
  - **Satin black under a matte black wrap** catches the light as pale grey blotches; for tears
    that should vanish into the black, the paint under them is matte too.

- **2026-09-25, the page online.** The viewer's lens is fixed top to bottom (32°), so a phone
  held upright sees about a third as much across, and the car was cut off at both ends until
  `frame()` drew it smaller by the window's shape. Next to the 4096² PNG at twice the size,
  2048² JPEG (quality 90, 4:4:4) is only softer, with no blocks or ringing; a 4096² texture
  takes about 90 MB of graphics memory with its mips, too much times five on a phone. GitHub
  Pages kept building `main` after `gh-pages` was pushed: the source is a setting. The Edit
  tool reads `$'` in a replacement as a JavaScript replace pattern (it pasted in the rest of
  the file), so keep that pair out of edits or write the line with a script.

- **2026-09-25, the wheels turn in the viewer (the user's idea).** Lighting each wheel part on
  its own showed what goes round: the tyre, the rim (the gold barrel), the thin ring at the
  tyre's bead, the covers, and the split ring at the centre ("brake caliper", a wrong guess of
  a name). The "hub" is a fixed fairing inside the wheel with a slot that shows the brake
  light, which the game keeps behind the axle, so both stay still. The viewer turns those parts
  about the fitted axles in the vertex shader (`SPIN`), shadows too, with the pad's speed. A
  screen can't show the true rate (290° a frame at 400 km/h looks like crawling or running
  backwards), so it eases off to about 4 turns a second: true at walking pace, a steady fast
  spin from about 40 km/h. `?spin=` turns them in snapshots. The first version wobbled (the
  user saw it at once): the viewer lifts the whole car 1.2 cm so the tyres sit on its floor
  (`car.json`'s `lift_cm`), and the axles hadn't been lifted with it. Anything placed in the
  viewer from the model's own figures needs that lift; the fitted cameras got it too. Checked
  by rendering a wheel at 0, 90, 180 and 270°: the centre cap stays within 0.3 px.
- **2026-09-25, the turbo (TSC_Lights_Test, the user's day and night turbo videos).** One
  yellow turbo pad each, Cam 1, full throttle to about 440 km/h, then braking. The turbo glow
  (code 160) lights in the pad's colour: the stock hubs (grey, code 160) glowed yellow inside
  all four wheels from the pad (day 2.2 s, night 1.6 s) for about 3 s, fading over the last
  half second (gone by day 5.3 s, night 5.0 s). Found by lighting up each candidate part in the
  viewer from the same angle: the hubs' shape matched exactly. The sidepod frames, which carry
  it too, can't be seen from behind. The rear lights went red, as when braking, for about
  1.5 s after the pad, with no brake pressed (the user's pedal overlay), then back to the gear
  display. The speed digits stayed green. The speed rose from about 130 to 400 km/h in 2 s.
  Exhaust heat (the side vents) is out of the chase cameras' sight, and there was no boost pad.
- **2026-09-25, the game's lens is wider than we thought (the user's Cam 1, 2, 3 screenshots,
  2560x1440, standing still).** Fitting each camera to the tyres' outer edges and tops and the
  horizon (projected from the model, lens free) gives 72.8° tall for Cam 1 and 74.1° for Cam 2,
  both within 1.5 px; Cam 3 (plus the nose fin and a mirror) 76.9°, within about 8 px. With the
  58.7° tall (90° wide) lens assumed since checkpoint 7, no pose fits (13 to 16 px off), and
  the user's by-eye settings drew the car about 1.4 times too big. Poses: Cam 1 3.36 m up, 5.21
  m behind the car's centre, 10.9° down; Cam 2 2.22 m up, 4.56 m behind, 3.4° down; Cam 3 0.93
  m up at the front of the canopy, level. Overlaying the viewer's outline on the screenshots
  confirmed all three. Match a camera by fitting its lens too, not by eye.
- **2026-09-25, a ring round the wheels must use the true axle (TSC_CMYK_Peel_More).** A line
  round each tyre, drawn round the wheel centres measured on 2026-09-23, wobbled in the game as
  the wheel turned: those centres were 5.7 mm too far forward. Circles fitted to the tread's
  crown, the tyre's bead, the covers' and the rims' edges all agree within 0.2 mm (35.252;
  178.314 front, -120.163 rear); `shapes.WHEEL_Y/WHEEL_Z` hold them. All four tyres share one
  shape in one texture layout (within 0.1 mm), so a ring in 3D is round on each. Anything that
  turns needs its centre fitted to the geometry, not read off by eye. Redrawn round the fitted
  centres, the user saw it round in the game (2026-09-25). `tool/parts.py` now takes them from
  `shapes` too, so the tyre's sidewall/tread split (34.5 cm) is round: it moved 33 triangles a
  tyre, nothing else changed, and TSC_CMYK_Peel_More repaints identically.
- **2026-09-25, the viewer's lenses already filter the braking red (TSC_Lights_Test).** The
  improvement list said the viewer drew the red without the lens. It doesn't: the glass is a
  transmission material, which multiplies what's behind it by `Glass_T`. Behind the cyan lens
  the braking red comes out dull teal by day and dark at night, as in the videos (day 12.4 s,
  night 9.2 to 10 s); with the glass hidden both bars show red. Check the viewer against the
  game before building a fix for it.
- **2026-09-25, the lights test (TSC_Lights_Test, the user's day and night videos).** A skin can
  colour the speed digits, the rear lights (a glow colour and a lens tint, which multiply) and
  the brake lights inside the front wheels. It can't colour the initials and number: they stay
  white. Braking turns the rear lights red whatever their colour, and a tinted lens filters
  that red too (keep the rear lenses clear or warm). Brake heat works: the rims glow while
  braking hard, building over about 1.5 s. A straight without pads lights no turbo colour at
  any speed. Details under the lights improvement.
  - **No restart needed:** the user found TSC_Lights_Test in the game without restarting it
    (the question open since checkpoint 1).
- **2026-09-25, the zip budget (TSC_Lights_Test).** Ubisoft's Ubi-Milky passed on in 2022
  that "the team were a little concerned about the 9mb car skin file size, believing it may be
  too big" (devtrackers.gg/trackmania/p/95b8392e): the only public word on a limit, and none
  is documented. Zips of 8.45 and 8.65 MB have worked. So `paintbox.ZIP_BUDGET` is 8.5 MB, and
  `build_zip` enforces it: over it, the roughness maps drop to 2048² (the stock's own size),
  largest first, and it warns if that isn't enough. Colour stays 4096². A skin that paints a
  few inner parts is the case that hits it (the stock grain upscaled barely compresses);
  mixed sizes within a set already worked in the game (TSC_Lab: `Details_B` 4096²,
  `Details_I` and `Details_N` 2048²).
- **2026-09-25, Claude's snapshots after the viewer's new look,** checked on the Windows PC:
  TSC_CMYK_Peel_More re-snapped against its sheet from before the new look differs in 855 of
  4.1 million pixels, all on the speed digits (a speed now, not 888), the rear light bands
  and single-pixel edge flicker. `?snap=1` keeps the framing.
- **2026-09-25, the user's straight-line video and night screenshots** (full notes under the
  lights improvement).
  - The game's pace, gear changes (up and down) and roll-down are now measured from frames:
    the earlier figures, timed by eye while playing (2 s to gear 2, 3 km/h a second when
    letting go, a dark display when stopped), were off each time. Where a short video can
    settle something, ask for one.
  - The digits always show three figures ("075", "000"). The rear bars fill up with the gear
    in the skin's own colour; braking turns them red whatever that colour.
  - A skin can colour the digits and the rear lights (the user's screenshots).
  - Two rear wings open at ~60-95 km/h, stay open while coasting and close at ~40. They
    move straight out and then apart, not on hinges (the user), so ask how something moves
    before modelling it from one camera angle.
- **2026-09-24/25, a torn wrap (checkpoint 7's comparison round, TSC_CMYK_Peel).**
  - Paint can't fake big 3D shapes: strips of wrap folded back over the body, shaded as a
    curl, looked flat to the user. Small, crisp cues work; big illusions don't.
  - Any fade along an edge reads as a soft edge. A soft shadow inside the tears made crisp cuts
    look blurred; a hard-edged band (solid, one-texel edge) gives depth and stays crisp.
  - A shadow painted for one light direction looks wrong from the other side: from the rear
    camera it didn't read as 3D. An even band all round every edge (light from straight
    above) reads from every camera.
  - Torn edges: fractal noise gives spray-paint specks; faceted noise (value noise without its
    smoothstep) gives straight runs and sharp corners, like torn vinyl.
  - A texel whose centre misses every triangle had its baked position at the origin, so a
    pattern drew a speck there along the seams. The paint box's canvas now gives such texels
    the nearest covered texel's position.
  - `noise._hash` in 32-bit arithmetic gives the same values in half the time; `value()` is
    1.7x faster, which every pattern benefits from.
  - (2026-09-27, the user's notes on TSC_CMYK_EndsInK) The distance to a tear's edge as field /
    gradient only holds near a real crossing: where two tears nearly meet, the field dips close
    to zero without crossing, and a shadow line was drawn across open paint with no wrap beside
    it ("the black didn't come through"). The shadow now needs a wrap texel within its width
    (a 3D lookup, so it still works across seams). And where the paint under a tear looks like
    the wrap (the black tip), the shadow alone read as "an outline and the paint is not there":
    it fades out as the two come to look alike, so tears dissolve into a matching colour.
- **2026-09-27, texture in a black wrap (TSC_CMYK_EndsInK and its round of takes).**
  - A grain in the colour of dark paint doesn't survive the game's colour map: BC1 keeps two
    5-6-bit colours per 4x4 block, so a few levels of variation on #232528 come out as flat or
    blocky steps. A grain in the sheen (the roughness map, BC5, 8-bit per channel) holds: the
    "sheen grain" look and the "textured wrap" finish (WT-07).
  - A fine grain fills the roughness map with detail zip can't squeeze, so the budget halves it
    (and the Details normal map) to 2048²: EndsInK went from 7.3 to 7.1 MB, Skin_R from 0.25 to
    1.2 MB zipped. Draw a grain for half size: 3.5 mm specks kept a spread of 0.100 of 0.103,
    and 2 mm (the user's "smaller") still 0.092 of 0.097.
  - The first carbon weave (0.5 cm, in the wrap's own black) couldn't be seen beyond arm's
    length: 0.8 cm and a touch lighter than the wrap read. Glossy dots on matte black read
    clearly, but a dot on a tight curve (the sidepod inlet's lip) shows the highlight as a row
    of bright dashes: leave out any dot whose normals spread more than about 14 degrees.
  - Pictures of the car look banded when shrunk for a quick look, and not at full size: judge
    gradients from full-size crops.
  - Nadeo's relief (Details_N) on the suspension arms (wishbones, pushrods, tie rods, rear
    arms) is a carbon weave. Painted as metal they read as woven metal: `s.relief(parts, lambda
    pos, nrm: 0, replace=True)` smooths it.

- **2026-09-24, pictures on the car (checkpoint 6).**
  - A decal restricted to one named panel stops dead at the next panel; the user saw the
    tiger cut in half. Project onto the nearest surface instead (a depth test), and let it
    cross panels like a real sticker. Then choose spots that are flat: the tool now measures
    the fold under a picture and says so.
  - The front flank of the body shell is not flat: the lower half sits back under an
    overhanging lip along a diagonal crease. Big stickers go on the rear flank (behind the
    sidepod) or the bonnet (z 91..142); the front flank's top strip takes lettering.
  - A tiled print laid per island breaks at every panel edge, because each island starts the
    pattern at its own offset. Lining the islands up along their shared mesh corners fixes
    most seams (median 3.9 cm off); mirrored twins can't be lined up.
  - Projections per facing smear a pattern wherever the surface turns; the unfolding doesn't.
  - For prints made of separate objects, don't tile at all: scatter whole copies, each laid
    flat inside one panel (the user's idea). No seam can show because nothing crosses one.
  - The model draws small repeated things badly: a dozen bananas per 1024² tile came out
    mushy; four across came out crisp. Ask for a few large objects and scale on the car.
  - The picture maker's "landed" measure must be counted in half-centimetre cells: the picture
    has more pixels than the car has texels, so a per-pixel count reports 10-50 %.

- **2026-09-24, the paint box (checkpoint 5).**
  - **Patterns must be laid on the surface, not cut out of space (user, 2026-09-24).** The
    first splatter drew drops as balls in 3D and sliced them with the body: on curves the
    drops looked sunk into the panel. Every pattern now uses the triplanar way (drawn flat
    from the direction each panel faces): dots, splashes, weaves, hexagons all follow the
    curves. The user then spotted dots merging on the sidepod's shoulder, where two of the
    three directions overlap, and after a "tube" projection was tried, dots stretched on the
    flanks and the nose: any projection invented from outside stretches wherever the surface
    curves away from it. **The real fix is the car's own unfolding** (`tool/uvmap.py`).
    Measured: Nadeo's UV layout stretches the body shell by under 5 % on 98 % of its area and
    the shell is one continuous island; the Skin set as a whole is under 10 % on 87 %. So flat
    patterns on the body (dots, splashes, hexagons, checks, weaves) are drawn in texture
    space, each island scaled by its own texels-per-cm and turned so the car's length runs
    up the pattern. Islands meet along the folds between parts, where a break is natural.
    The inner car's unfolding is in hundreds of small pieces, so it keeps the three-direction
    projection (fine for its small parts). The tube mapping stays in `looks.py` for comparison.
  - **Then the user asked for dots that cover the whole car unbroken**, and the unfolding
    clips a pattern at every panel edge. So patterns made of separate things (dots, splashes,
    honeycomb cells) are no longer patterns at all: `looks.surface_points()` spreads points
    evenly over the painted surface itself (Poisson-disc thinning of candidate texels, in
    lattice order for a grid-like look or random for a hand-placed one), and each element
    is drawn by 3D distance from its point. Whole everywhere, round on every curve, and one
    that lands on a fold bends over it like a sticker. Honeycomb is the cells between such
    points (nearest two). What can't be seamless: continuous tilings (checks, stripes,
    weaves); those use the unfolding and break at the folds, where a real wrap would too.
    TSC_Dots is the test.
  - Sequential compositing with anti-aliased part coverage handles every seam: a texel half
    in part A and half in part B takes half of each paint. No special seam code.
  - A phrase's colour words can collide with finishes ("gold", "chrome", "copper", "rust"):
    when no finish word is present, the metal wins and its own colour is used; "dark gold"
    darkens the metal. "gold satin" is satin gold metal.
  - Texel budget at 4096² on the body: about 1 texel per mm on the flanks, so 20 cm letters
    are crisp; lettering is drawn at 40 px per cm before projection.
  - The usable flat area on each side, between the sidepod inlet and the rear wheel, is about
    34 cm wide, centred 66 cm behind the axle line (paintbox.SPOTS "left side"): the wheel
    cover hides the flank behind that, the sidepod's recess swallows it in front. Text wider
    than its spot is shrunk to fit, with a note.
  - ambientCG's download needs a User-Agent header (a bare Python one gets 403). Its 1K JPG
    sets are ~5-7 MB; the API is https://ambientcg.com/api/v2/full_json.
  - Cost: fine sparkle patterns (a Voronoi cell per 1 mm over the whole body) take minutes;
    everything else seconds. Building the zip is 32 s, nearly all BC1 encoding through Pillow.

- **2026-09-24, the lab skins in the skin editor (checkpoint 4).** The user's screenshots
  (09:46-09:48) of TSC_Lab and TSC_Lab_NoCoat, read against `tool/labskin.py`'s key.
  - **`Skin_CoatR` is the varnish, and 0 means glossy.** On TSC_Lab the deck's varnish-0
    columns carry a whitish sky sheen even at roughness 100 %, the varnish-255 columns show the
    plain, deeper orange; on the black bonnet the varnish-255 half at roughness 50 % is a hazy
    grey and the varnish-0 half a dark mirror. TSC_Lab_NoCoat looks like varnish 0 everywhere.
    So: no file = glossy varnish all over; **matte paint needs CoatR 255 on that area**, and the
    tool always ships `Skin_CoatR`. This explains checkpoint 1's "matte isn't fully matte" (its
    CoatR was a flat 0). The varnish never blurs the base: roughness 0 under varnish 255 is
    still a sharp mirror. Modelled in the viewer as a glossy clear coat whose amount is
    1 - CoatR.
  - **Roughness and metalness behave like ordinary PBR.** The R0..R100 bands go from a sharp
    mirror to matte (under the varnish the steps are subtle), the metal half of the deck is
    metal, and the flank's M0 / M50 / M100 bands step up in reflectivity.
  - **The tyres take roughness and metalness** from a two-channel `Wheels_R` (ATI2), although
    the stock file is one-channel: sector 5 (roughness 0, metal) is chrome, 4 (rough, paint) is
    white matte, 6 and 7 blur in between.
  - **Energy (code 32) glows dim red at rest** in the skin editor: the sidepod frames, painted
    dark grey, show as maroon. The game's colour, not ours.
  - **Glass:** the canopy's cyan tint shows only faintly, the amber not at all from behind, and
    the alpha bands (255 / 128 / 32) made no visible difference in the editor. Not settled.
  - **The wing domes** are in the game; zoomed in, they read as raised (lit on the sun's side),
    so the game takes our normal maps as written (OpenGL, Y up). Weak evidence: they're small.
- **2026-09-24, the lab skin driven (checkpoint 4).** The user's night and dirt screenshots
  (10:07-10:11), read against `tool/labskin.py`'s key.
  - **Brake lights (0):** the lab put them on the rear bumper corners, which turn out to be
    hidden from every camera, so nothing new; checkpoint 1's stock strips stand (dim always,
    near white when braking).
  - **Energy (32)** is on at rest, dim, tinted by the game (red here).
  - **Always on (96)** keeps its colour (magenta), day and night.
  - **Front lights (128)** are bright white by day and at night, in the daytime dirt shot too.
  - **Night only (255)** is on at night, and on a dusk map in daylight.
  - **Not seen:** brake heat (64) when braking from 133 km/h, exhaust heat (192) and turbo colour
    (160) on turbo pads, boost (224). The hubs (160) are hidden by the wheel covers anyway.
    Treat these four as off in the viewer until a design needs them.
  - **The game's own rear lights** are two red bars on the tail wing and two under the bumper,
    on all the time and pink-white when braking (the user's "pink/white"). The wing flaps up
    under hard acceleration and shows red underneath. None of that is ours to change.
  - **Dirt:** the mask works as a mask: the body's left half (255) turns the track's dusty
    brown, the right half (0) stays clean; the tread (255) browns, the sidewalls (0) don't. At
    255 the dirt covers the paint completely, so designs want moderate values (the stock mask
    averages 53 with a few texels up to 230). The game's number stays clean.
  - **Glass:** the canopy's alpha made no visible difference from any angle (user). Treat
    `Glass_T` as tint only.
- **2026-09-24, building the lab skins (checkpoint 4).**
  - Nadeo's `ReadMe.txt` calls `Skin_CoatR` a "Varnish layer" (greyscale). Whether it's the
    varnish's amount or its roughness is what the lab's deck swatches decide.
  - **The four tyres use identical texels and the left and right wheels aren't mirrored**
    (measured from the mesh: the same angle round the axle maps to the same UV on both
    sides). So any writing on a tyre reads backwards on one side of the car. Inner and outer
    sidewalls have their own texels (image columns 0..206 inner, 311..511 outer at 512 wide;
    the tread sits between).
  - **A shared texel's baked position can belong to a different part** (the main bake keeps the
    last triangle drawn). Zoning a shared Details part by the main bake's positions gives
    nonsense; `parts.load().local_bake(set, w, h, name)` rasterises only that part's triangles
    and gives its own positions and normals (its mirror twin's at worst).
  - The Details atlas is coarse on some parts: the front wing's top has ~6 texels per cm, the
    rear bumper's face (the strip above the digits) is only 12 cm tall. Lettering in relief is
    hopeless there; the lab uses a 10 cm dome instead.
  - Parts the game's chase camera can actually see, out of the small inner ones (checked in the
    viewer): rear bumper and its corners, rear strakes, the rear undertray's edge, hub
    brackets, hubs (through the wheel covers' spokes), rims, sidepod frames, side vents, the
    front wing. Exhausts, wing brackets, mirror arms, calipers and the airbox are hidden or
    tiny. The glows in the lab sit on the visible ones.
- **2026-09-23, from Nadeo's 2020 post and the stock files:** a skin can also paint the wheels
  and the glass, but not the player number or ID, the turbo colour, the digit colours, the rear
  lights or the glass gear display. See `.claude/rules/tool.md` for the texture table.
- **2026-09-23, ATI2 channel order.** Nadeo's ATI2 files store the first block = channel 0.
  - In `Details_N`, texture features running along the columns line up with the first block:
    correlation +0.50, and +0.46 in `Wheels_N`. So the first block is X, and by the same tool
    it's roughness in `_R`.
  - Their bit-count field holds "A2XY". `tool/dds.py` copies both.
  - Stock `Skin_R` then reads roughness ≈ 3 and metalness ≈ 255: smooth metal under the paint.
  - The test skin's CHROME/MATTE patches confirm the order in game.
- **2026-09-23, compression.**
  - Pillow's BC4/BC5/BC3-alpha encoding is loose. It put 1 % of `Details_I` texels on the
    wrong glow code, and was off by 21/255 at hard edges. `tool/dds.py` has its own BC4
    encoder (min/max endpoints, both modes). Glow codes now survive on 99.999 % of texels,
    with a maximum of 8 off, so they still snap to the right code.
  - Pillow's BC1 did colour until checkpoint 7 (2026-09-24), when the user's close-up game
    screenshots showed pixelated stickers: it was 5 dB worse than a refined encoder and put
    fringes round every edge. `tool/dds.py` now has its own BC1 (`bc1_blocks`: endpoints on
    each block's principal axis, refined by least squares; on a par with Microsoft's texconv,
    which was tried and removed). Building a zip went from 25 s to 51 s.
  - Nadeo's own mips average the glow codes: 35 % of texels are off-code at mip 6. Ours
    point-sample the alpha, so the codes stay exact at every mip.
- **2026-09-23, the model's orientation.**
  - The car faces +z, with y up. The wheels are at z +178.9 (front) and −119.6 (rear).
  - The car's left is +x. The game confirmed it: the model isn't mirrored.
  - The discs over the wheels are part of the Skin mesh, and their texels are shared between
    both sides.
  - The glass pieces include the cockpit canopy and lenses on the sides.
- **2026-09-24, checkpoint 1 in game.** The user ran all three test skins and took F12
  screenshots (from 00:10 to 00:11).
  - **All our files load.** The legacy headers, mips and formats are right. Left and right are
    correct.
  - **ATI2 order confirmed.** The CHROME nose shines like a mirror.
  - **Matte isn't fully matte.** Roughness 255 with metalness 0 still looks "slightly
    reflective" to the user. Suspect the clear coat: `Skin_CoatR` was a flat 0, like Nadeo's
    reference. Test it in checkpoint 4.
  - **Glass:** the game reads `Glass_T` (it showed green), not `Glass_D` (red). `Glass_D` was
    ignored when both were present.
  - **Wheels:**
    - `Wheels_B` covers the tyres; the grid showed on the rubber.
    - The rim's inner part is Details: it showed yellow.
    - The outer hub discs are Skin: they showed blue on both sides.
    - The user saw a thin green ring between the tyre and the rim.
  - **Glow (stock `Details_I` layout):**
    - Brake lights (code 0) are strips behind the front wheels, visible from the chase
      camera. They glow all the time and flare to near white when braking.
    - Front lights (code 128) are crescents inside the front wheel pods.
    - The code 160 areas (turbo colour) are grey in the file and showed green in game: the
      front wing's lower edges and the rings at the wheels. That colour is the game's.
    - Located by baking Details. The lit texels per code are:

      | Code | Lit texels | Where |
      |---|---|---|
      | 160 | 278k | around the wheel pods and the wing edges |
      | 96 | 72k | mostly at the rear |
      | 0 | 3.7k | the front pods |
      | 128 | 3.3k | z 192–213 |
      | 224 | 2k | beside the rear wheels |
      | 192 | 104 | |
  - **The game's own number:** in a race it draws "CAR 01" on the engine cover's centre. In
    the game's skin editor, big "AB" and "CDE" letters sat in the same spot: placeholders for
    the player number and username, which the game draws there (user, 2026-09-24). Those
    rectangles are the parts "number panel" and "engine cover panel": paint them plain and keep
    lettering and detail off them.
  - **The game has a built-in skin editor.** It opened our skin, and its paint has "Matte %"
    and "Metal %" sliders. It's a handy reference for checkpoint 4.
  - **4096² works.** TSC_Test_Sharp loaded and looks visibly sharper. Its zip was 8.45 MB,
    with painted textures at 4096² and Nadeo's dirt and normal maps at 2048². It loaded fine.
    - Nadeo's dirt masks and normal maps are most of a zip's weight: 2K stock DirtMasks
      4.3 MB, `Details_N` 2.1 MB.
    - Default: 4096² for painted textures. Keep zips ≤ 8.5 MB until an upload limit shows up
      (`build_zip` enforces it since 2026-09-25: Things we learned).
  - **Every texture is optional.** TSC_Test_SkinOnly held only `Skin_B` and `Skin_R`
    (0.21 MB) and worked. Everything else kept the stock look. So a skin need only ship the
    textures it changes.
  - **No restart needed:** the user started the game after the install, and all three uploaded
    easily. Still unknown: whether a skin installed while the game is running shows up
    without a restart. Check that in checkpoint 3's game test.
- **2026-09-24, checkpoint 2: the viewer next to the game's screenshots.**
  - Shapes, layout, left/right, stock tyres ("NADEO" sidewalls) and stock rims all match.
  - With the sky light at 1, paint looked washed out: orange measured (250, 154, 105) against
    the game's (253, 159, 46). Lowering it to 0.55 fixed that. The clear coat hardly changed
    the colour.
  - **Glow puzzles for checkpoint 4:**
    - The stock turbo-colour (160) areas on the wheel pods hold smooth white-to-black fades.
      That looks like a mask the game animates. At rest in the game they stayed dark, so the
      viewer shows 160, 224, 64 and 192 off on a parked car.
    - **Solved:** in the game the front wing's lower hooks and the thin line under the nose
      glowed green, although the file made them cyan (code 128) and white-blue (code 96).
      They sit behind small glass lenses, and TSC_Test's `Glass_T` was green. The viewer
      shows the same green with the glass on, and cyan and white with it hidden. The pod
      crescents have no lens and showed cyan. So glass tint colours the lights behind it.
  - `Skin_CoatR` is probably clear-coat roughness, following Nadeo's `_R` naming. A flat 0
    means a mirror coat over everything, which would explain "matte isn't fully matte". The
    viewer uses it that way until checkpoint 4 tests it.
- **2026-09-24, checkpoint 3: the car taken apart.**
  - **The exporter already split the meshes at every hard edge and UV seam** by duplicating
    vertices: no piece has a normal break or a UV seam inside it. So vertex-connected pieces
    (Skin 133, Details 1918, Wheels 4, Glass 36) are the crease-and-island split the plan
    asked for. Welding vertices by position instead gives the touching-piece groups (Skin 38,
    Details 417), such as an arm with its bolts. Dihedral splitting adds nothing useful: the
    big body panel and the tyres are smooth, so their regions come from rules (z ranges,
    normals, radius).
  - **The Details mesh is a whole inner car:** chassis, floor and plank, front wing with
    endplates, wishbones, pushrods, dampers, tie rods, brake lines, hubs, rims, calipers,
    seat, belts and buckle, steering wheel and column, dashboard, mirrors, airboxes, exhausts,
    rear bumper with three seven-segment digit displays, rear diffuser, side vents.
  - **The Wheels mesh is only the tyre ring** (radius 29–36 cm): tread and sidewalls. The rims
    and hubs are Details. The Skin's wheel covers are 16 pieces each: ring, spoked disc, hub.
  - **Glass:** the canopy carries 15 tiny pieces at its rear, the gear display. Other glass:
    lenses inside the nose, at the wing hooks, the rear lights, the side vents and the mirrors.
  - **Mirrored pieces:** 1795 of the 1918 Details pieces have an x-mirrored twin (matched by
    mirrored bounding box and triangle count ±20 %).
  - **Shared texels** (several triangles on one texel): Skin 11 % of covered texels (the four
    wheel covers share one set, plus the nose and tail ends), Details 82 % (nearly every
    left/right pair, and the four wheels' rims, hubs, calipers), Wheels 100 % (all four tyres),
    Glass 40 %. `car/parts.json` records each part's `shared` share: a colour on such a part
    lands on its twin too. Painting one side differently is impossible there.
  - Rasterising a part's own triangles gives its texel mask; a bake's "last triangle wins"
    label would lose the shared ones.
  - **Clean borders: the rules (from the user's game screenshots, 2026-09-24).**
    1. **A part border lies on a fold of the mesh, never inside a smooth surface.** Splitting
       the body shell into nose, bonnet and flank was wrong three times over: cut by triangle
       it was a sawtooth; cut by the surface's slope it kinked at every triangle (the slope is
       interpolated inside each one) and left slivers at seams; the shell has no fold at all
       (no crease over 10° except its centre seam). So the shell is one part, "body shell".
       Zones on it are the paint box's job: shapes in 3D with soft edges, not part names.
    2. **The few cuts that remain use a distance field with anti-aliased edges:** tread and
       sidewall by radius from the axle (34.5 cm), the chassis by z. `parts.coverage()` gives
       0..1 along the border over one texel; `mask()` is coverage > 0.5.
    3. **Texels between UV islands take the colour of the nearest island** (`raster.fill_holes`
       is a nearest-neighbour fill). The push-pull average tried first mixed neighbouring
       islands, and the game's filtering showed a fringe of odd colour along every seam.
    4. **Paint at 4096²**, the sharpness already decided: a hard edge's step is then ~1 mm.
    5. **Seams between parts are anti-aliased.** Many islands touch in the atlas with no gap
       (the cockpit surround and the body shell share a border of 3,500 texels at 4096), so
       a texel on the seam belongs partly to each. `parts.coverage()` takes 2×2 samples per
       texel, and a painter mixes each texel's colour by every part's share (`tool/partskin.py`
       shows the pattern: last colour per instance, then a weighted mix, then the nearest fill
       for the gaps). Before this, the seam texel went whole to one part, and the game showed
       a one-texel overflow of the wrong colour, stepped along the seam.
    6. Cost: painting all 200-odd parts at 4096² takes about 3½ minutes, nearly all of it the
       coverage rasterising. The paint box should cache each part's coverage per size.
  - **Looked at the user's other project (`Documents\Trackmania Skin Studio`), with their
    permission, for this one question.** Its faces are cut only along welded mesh edges that
    fold by 30° or more, and its shapes are painted as supersampled coverage with feathered
    (distance-transform) edges. Those two ideas are what rules 1 and 2 adopt. Nothing else was
    taken from it.
  - scipy 1.18.1 added (connected components, nearest-neighbour lookups).
- **Checkpoint 7, the first skin (2026-09-24, Fable 5.1).**
  - **Texel pitch on the body at 4096² is 0.09 cm** (median; measured on the bake). A 12 cm
    sticker is about 130 texels wide, a BC1 block 3.6 mm.
  - **Pictures were aliased:** a decal or scatter copy took one picture pixel per texel, and a
    400-px sticker has three times the texels' pixels, so its thin outlines came out broken;
    the user saw them pixelated in the game's skin editor. `paint.project_points` now filters
    the picture down to the texel pitch (Lanczos) and samples it bilinearly (`fit_to_texels`).
  - **An even scatter** (the user: clusters of the same picture, bare patches): each copy takes
    the picture least used among its neighbours; a copy that doesn't fit is nudged, turned and
    shrunk before it's given up; a second pass fills patches still bare (measured from the
    copies' outlines) with smaller copies.
  - A tall picture (a cone) on the flank: `PIL.Image.rotate(expand=True)` then crop to the
    alpha's bbox, or `width` counts the empty corners and the picture comes out small.
  - Two picture-maker runs with the same words share one folder in `build/pictures/`, so the
    second overwrites the first even with another style: give the style its own slug.
  - `tool/skin.py` keeps `skins/<name>/versions/<n>.png`, one picture per round shown.
