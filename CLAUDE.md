# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@BRIEF.md

## Where things stand

- **Phase: building the tool.** `CHECKLIST.md` tracks progress. Read it at the start of every
  session and carry on from the first unticked checkpoint. The user agreed the plan on
  2026-09-23. The foundation (the car's parts and materials, checked in game) comes before
  design tools.
- Commands (from the repo root; `PY` is `%LOCALAPPDATA%\TrackmaniaSkinChallenge\venv\Scripts\python.exe`):
  - Set up: `python -m venv <that venv>`, `PY -m pip install -r requirements.txt`, then
    `PY -m tool.prepare`, which checks the `official/` zips and unpacks them.
  - Test skins (checkpoint 1): `PY -m tool.testskin`. Install: `PY -m tool.install <name> ...`.
  - Viewer: `PY -m tool.view <name>` serves http://localhost:8765/?skin=<name> and opens the
    browser. Run it in the background so it keeps serving while the user looks.
  - Claude's check: `PY -m tool.snap <name>` saves six views to `build/<name>_views.png`. Look at
    it before showing the user anything. `snap.snap(..., shots=..., query=...)` takes close-ups.
  - `tool/preview.py` renders flat views without materials, for quick checks of texture layout.
  - Skins (checkpoint 5): a design is `skins/<name>/design.py`, a `design(s)` function of
    `paintbox.Skin` calls (the docstring of `tool/paintbox.py` is the key). `PY -m tool.skin
    show <name>` paints, exports to the viewer and snapshots; `PY -m tool.skin install <name>`
    builds the zip and installs it; `PY -m tool.gallery` opens the page of all skins;
    `PY -m tool.swatches` opens the materials page (every finish on a ball).
    Phrases go through `finishes.resolve()`: colour + finish + region words.
  - Pictures (checkpoint 6): `PY -m tool.pictures decal "a roaring tiger head"` or `tile "small
    bananas on cream"` makes candidates on a sheet in `build/pictures/`; look, then `PY -m
    tool.pictures keep <slug> <k> <skin> <name>` puts the chosen one in `skins/<skin>/art/`. In a
    design: `s.decal(s.art("tiger"), "left side", width=32)` (a picture at a spot, across every
    panel it covers); `s.scatter(s.art("banana"), "body", size=(7, 10), spacing=11)` (copies of a
    cut-out spread evenly, each whole and inside one panel: the user's choice for prints made
    of objects, 2026-09-24); `s.print("bananas", scale=36)` then `s.paint("body", "bananas")`
    (a seamless tile as one continuous sheet, for textures). Read the notes `show` prints: a
    decal says when it crosses a fold or falls off an edge. The user prefers illustrations,
    prints and decals to photo-real pictures (2026-09-24); the "sticker" style is the default.
    First-time setup: `PY -m tool.pictures setup` downloads the 16 GB of weights.
  - Parts (checkpoint 3): `PY -m tool.parts` turns the names in `tool/naming.py` into
    `car/parts.json` (`--review` renders the car coloured by part). `parts.load().mask(bake,
    "Details", "brake caliper", side="left", end="front")` is a texel mask. `PY -m tool.partskin`
    builds the TSC_Parts test skin. Shared texels: see `shared` in `car/parts.json`.
- Work folder `%LOCALAPPDATA%\TrackmaniaSkinChallenge\`: `venv`, `official` (unpacked zips),
  `cache` (the parsed mesh and bakes), `build` (DDS files and zips), `viewer` (what the viewer
  page loads). All of it is rebuildable.
- Record technical decisions in the repo (this file, `CHECKLIST.md` or the code), so the next
  cold session finds them.
- Version control: GitHub `fedecarbo/tm-skin-creator` (public), branch `main`. When a checkpoint
  is ticked, commit and push without asking; the user said yes on 2026-09-23. At other times,
  commit only when asked. Never push files that aren't ours to publish.
- Before adding any tool or library, look up its latest release and use that version, then
  record it. If a paid option would be far better, tell the user and discuss it before using it.

## Design rules from the user

- **The wheels are their own design step (2026-09-24).** Body paint, prints and scatters
  cover the body only; "body" in the paint box excludes the wheel covers. Paint the wheels
  ("wheels": covers, rims, hubs, wheel rings; "tyres" separately) with their own calls.

## Talking to the user

- Use plain words. Leave code, file names, paths and jargon out of replies unless they ask.
- Show rather than describe. A preview picture beats a paragraph.
- Ask only about taste and real trade-offs. Don't ask about things good design handles anyway:
  a question about their driving camera felt pointless (2026-09-23).
- The user is happy to test in the game (drive, brake, turbo, day and night, F12 screenshots).
  Ask for that whenever the game is the only way to know.

## Don't look in the game's skin folder

`C:\Users\fedec\OneDrive\Documents\Trackmania\Skins\Models\CarSport\`

- It holds skins the user made outside this project. They are **not** reference designs or
  examples of good practice. Never list, open, read, copy or unzip anything there by any
  means: tools, shell or scripts. Never let them shape a design or technical choice. Work
  from `official/`, Nadeo's documentation and your own research.
- `.claude/settings.json` denies Claude's file tools on that folder. That also stops the Write
  tool from creating files there. Shell commands and scripts aren't covered, so the rule
  above is what stops them. Don't work around the deny.
- The only thing that writes there is `tool/install.py`. It holds the folder path in its own
  code. It checks only whether its exact target file name is free, and it never overwrites or
  deletes a file this project didn't create (`skins/installed.json` + sha256).
- Steam screenshots (F12) are in
  `C:\Program Files (x86)\Steam\userdata\53610290\760\remote\2225070\screenshots\`. 2225070 is
  Trackmania. Look only at screenshots taken after the skin you're testing was installed.

## Source assets (`official/`)

Leave the zips unchanged: `official/SOURCES.md` records their sha256. Extract them to a working
folder and never edit them in place. They're git-ignored because the GitHub repo
(`fedecarbo/tm-skin-creator`) is public. A fresh clone downloads them from the links in
`SOURCES.md`.

- `CarSport-Template.zip` (from Nadeo): `ReadMe.txt` and the flat UV maps `UV_Skin.png`,
  `UV_Skin_Hollow.png` and `UV_Details_Hollow.png` (2048×2048), plus `UV_Details.png`. That one
  is **2018×2018**, so scale it before overlaying.
- `CarSport-Model.zip` is a community upload on Sketchfab. It is **CC-BY-4.0, so credit the
  author, amogusstrikesback2,** wherever you reuse the model. It holds `textures/*.png` and a
  nested `source/StadiumCAR2020_OffsetFix.zip`, which contains the FBX mesh and the unpainted
  DDS textures (`Skin_*`, `Details_*`, `Wheels_*`, `Glass_*`). The main textures are 2048×2048.

## Skin texture format

From Nadeo's `ReadMe.txt` and Nadeo's 2020 post "Stadium CAR Ressources" (link in
`official/SOURCES.md`). DDS files are required. They must use legacy D3D9 headers (FourCC
`DXT1`, `DXT5`, `ATI1` or `ATI2`), not DX10 headers.

| File | Compression | Content |
|---|---|---|
| `Skin_B`, `Details_B` | BC1 / `DXT1` | Base colour, RGB |
| `Skin_R`, `Details_R` | BC5 / `ATI2` | R = roughness, G = metalness |
| `Skin_CoatR` | BC4 / `ATI1` | Varnish: 0 glossy, 255 none |
| `Skin_DirtMask`, `Details_DirtMask` | BC4 / `ATI1` | Dirt mask, greyscale |
| `Details_I` | BC3 / `DXT5` | Self-illumination, RGB + alpha |
| `Details_N` | BC5 / `ATI2` | Normal map, OpenGL (Y+) |
| `Wheels_B` | BC1 / `DXT1` | Base colour, RGB (tyres and wheel faces) |
| `Wheels_R` | BC5 / `ATI2` | Roughness, metalness |
| `Wheels_N` | BC5 / `ATI2` | Normal map |
| `Wheels_DirtMask` | BC4 / `ATI1` | Dirt mask |
| `Glass_T` | BC3 / `DXT5` | Glass tint (RGB) + alpha, 1024² |
| `Glass_I` | untested | Self-illumination of the glass |

- Wheels and glass files aren't in the ReadMe. Checkpoint 1 confirmed in game that the wheel
  files work, and that the game reads `Glass_T`, not the `Glass_D` in Nadeo's 2020 post.
- Every texture is optional: anything left out of the zip keeps the game's stock look. Skin,
  Details and Wheels take 4096² (Wheels 1024×2048). Details of all of this are under "Things
  we learned" in `CHECKLIST.md`.
- `Skin_CoatR` is the varnish: 0 lays a glossy clear varnish over anything, 255 lays none, and
  a skin without the file is varnished all over. Matte paint needs 255 there, so always ship
  the file (checkpoint 4, 2026-09-24). Skin takes no normal map.
- A skin can't change the player number or ID, the turbo colour, the colour of the digits, the
  rear lights or the glass gear display (post).
- The shaders blend ambient occlusion (AO) themselves. Don't bake AO into the textures.
- The alpha channel of `Details_I` picks how each glowing area behaves:

  | Alpha | Behaviour |
  |---|---|
  | 0 | Brake lights, on when braking |
  | 32 | Energy, tinted in game (team colour); the RGB must be grey |
  | 64 | Brake heat, on when braking hard |
  | 96 | Always glowing |
  | 128 | Front lights, bright at night |
  | 160 | Turbo colour; the RGB must be grey |
  | 192 | Exhaust heat, on during turbo |
  | 224 | Boost colour; the RGB must be grey |
  | 255 | Glowing at night only |

## Keeping this file useful

- It loads every session, so keep it under 200 lines and hold only what every session needs.
  Add a line when leaving it out caused a mistake or a repeated explanation. Delete lines that
  stop being true.
- Put instructions for one part of the code in `.claude/rules/*.md`, with `paths:` frontmatter.
  Put step-by-step procedures in a skill.
- Once the tool works end to end, move the chat loop (describe → preview → change → install)
  into a project skill in `.claude/skills/`. Then cut the build-phase parts of this file, and
  replace the `@BRIEF.md` import with the few lines of the brief that still apply when the tool
  runs. Plan that as a checkpoint.
