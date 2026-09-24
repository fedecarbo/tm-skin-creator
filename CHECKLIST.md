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
- the built game files;
- what the viewer page loads (the car, the sky, each skin's pictures).

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
  - **Night.** Use the Details_I alpha codes (table in `CLAUDE.md`) to decide which parts glow.
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
    - The promise "yes reaches the game in under 30 seconds" is now 51 s: the new BC1 encoder
      doubled the build time. Worth trimming (fewer refinement passes on flat blocks, or the
      mips in parallel) before checkpoint 8.
    - The user watches sharpness closely and checks it in the game's skin editor at close
      range: keep every edge, sticker and letter at the texel grain.
  - [ ] **The comparison round, still to do:** one skin made on Opus 5.5, in a fresh chat with
    that model picked at the top. Then the user says which model they prefer for everyday
    use, and checkpoint 8's skill recommends it.

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
- **DDS files come from our own writer:** our own block encoders (numpy), a legacy header and
  a mip chain. Pillow's BC1 was 5 dB worse (2026-09-24).
- **Install:** one zip per skin, no spaces in its name, with `Icon.tga`, recorded in
  `skins/installed.json`.
- **Viewer must-haves (user, 2026-09-23):** spin and zoom, day and night, hide and show parts.
  Comparing versions isn't wanted. The setting is a photo studio, not the game's stadium
  (user, 2026-09-24).
- **Free tools only (user, 2026-09-23).** If a paid tool would be far better, tell the user and
  discuss it first. The picture maker is free and local.
- **The user has Club access (2026-09-23),** which custom skins need.
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
  lights or the glass gear display. See `CLAUDE.md` for the texture table.
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
    - Default: 4096² for painted textures. Keep zips ≤ 8.5 MB until an upload limit shows up.
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
