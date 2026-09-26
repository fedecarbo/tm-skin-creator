---
paths:
  - "tool/**"
  - "viewer/**"
  - "official/**"
  - "car/**"
---

# Working on the tool

`CHECKLIST.md` records why the tool works as it does: each checkpoint's "Notes for Claude",
"Decisions", and "Things we learned" (what the game, the tests and the user showed). Search
it before changing how something works. The top docstring of each `tool/*.py` is its key.

## Commands for the machinery

`PY` = `%LOCALAPPDATA%\TrackmaniaSkinChallenge\venv\Scripts\python.exe`, from the repo root.

- Set up a fresh clone: `python -m venv <that venv>`, `PY -m pip install -r requirements.txt`,
  `PY -m tool.prepare` (checks the `official/` zips and unpacks them), `PY -m tool.pictures
  setup` (downloads the picture maker's 16 GB of weights).
- `PY -m tool.view <name>`: serves http://localhost:8765/?skin=<name> and opens it. Run it in
  the background. `tool/preview.py` renders flat views without materials, for texture layout.
- Test skins: `PY -m tool.testskin` (checkpoint 1), `PY -m tool.partskin` (TSC_Parts),
  `tool/labskin.py` (the materials lab). `PY -m tool.install <name> ...` installs built zips.
- The Lab (`viewer/lab.html`, http://localhost:8765/lab.html): `PY -m tool.swatches` paints a ball
  for every finish in `finishes.CATALOGUE` and opens it; the Mac's container paints them at start.
  **The Lab shows only the tool's own data**, never a list of its own that could drift: a gap
  in the Lab is a gap in the tool, to fix in the tool (the user, 2026-09-26). The same goes for
  its painting rooms (Body, Details, Tyres, Glass: the game's maps). Notes: "The Lab" in `CHECKLIST.md`. The rooms
  (`lab.html?room=wheels`, `viewer/lab-rooms.js`) come from `tool/rooms.py` (each room's parts and
  camera; every part must be in one) and read `view.export_uvmap`'s data (the UV map picks
  surfaces: `view._surfaces`, the shapes it outlines, `<Set>_Surfaces.png`), which `tool.view` and
  `tool.swatches` rebuild when the parts, the rooms or their code change. The Studio (the first room,
  `viewer/lab-studio.js`) reads the frames `tool.skin show` writes at each `Skin.step`
  (`view.export_steps`, `studio.json`); `install` paints without them. A round of concepts
  (`skins/rounds.json`, `tool.skin round`, on each take's `gallery.json` entry) puts a switch
  between its takes in the Studio and the rooms (`viewer/lab-round.js`).
- Parts: `PY -m tool.parts` turns `tool/naming.py` into `car/parts.json` (`--review` renders the
  car coloured by part). `parts.load().mask(bake, "Details", "brake caliper", side="left",
  end="front")` is a texel mask. See `shared` in `car/parts.json` for shared texels.

## Source assets (`official/`)

Leave the zips unchanged: `official/SOURCES.md` records their sha256. Extract them to a working
folder and never edit them in place. They're git-ignored because the GitHub repo is public. A
fresh clone downloads them from the links in `SOURCES.md`.

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

- The game reads the wheel files and `Glass_T` (not the `Glass_D` in Nadeo's post).
- Every texture is optional: anything left out of the zip keeps the stock look. Skin, Details
  and Wheels take 4096² (Wheels 1024×2048). Keep zips ≤ 8.5 MB until an upload limit shows up:
  `build_zip` halves the normal map, then the roughness maps, when a zip runs over.
- Relief on the inner car (`Details_N`, `tool/relief.py`) is drawn over Nadeo's own map with its
  rounding noise set flat (it cost 1.5 MB zipped and carries no shape).
- `Skin_CoatR` is the varnish: 0 lays a glossy clear varnish over anything, 255 none, and a
  skin without the file is varnished all over. Matte paint needs 255 there, so always ship the
  file. Skin takes no normal map.
- The shaders blend ambient occlusion themselves. Don't bake AO into the textures.
- The alpha channel of `Details_I` picks how each glowing area behaves (`GLOWS` in
  `tool/finishes.py` says what the game showed for each):

  | Alpha | Behaviour |
  |---|---|
  | 0 | Brake lights, on when braking |
  | 32 | Energy, tinted in game (team colour); the RGB must be grey |
  | 64 | Brake heat, on when braking hard (builds over ~1.5 s) |
  | 96 | Always glowing |
  | 128 | Front lights, bright at night |
  | 160 | Turbo colour; the RGB must be grey |
  | 192 | Exhaust heat, on during turbo |
  | 224 | Boost colour; the RGB must be grey |
  | 255 | Glowing at night only |
