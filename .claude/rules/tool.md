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

`PY` is the tool's Python, one for each computer (`CLAUDE.md`), from the repo root. The two
computers' differences live in `tool/paths.py` (the work folder, the snapshots' browser, opening a
picture) and `requirements.txt` (the picture maker's packages, the PC only).

- Set up a fresh clone: Python 3.14 (on the Mac Homebrew's `python@3.14`), `python -m venv <the
  work folder>/venv`, `PY -m pip install -r requirements.txt`, on the Mac `PY -m playwright install
  --only-shell chromium` (with `PLAYWRIGHT_BROWSERS_PATH=<the work folder>/browsers`, where `paths` looks),
  `PY -m tool.prepare` (downloads Nadeo's template, checks the `official/` zips and unpacks them;
  the model zip is copied from the other computer), and on the PC `PY -m tool.pictures setup`
  (the picture maker's 16 GB of weights).
- `PY -m tool.view <name>`: serves http://localhost:8765/?skin=<name> and opens it. Run it in
  the background.
- `PY -m tool.install <name> ...` installs built zips.
- The Lab (`viewer/lab.html`, http://localhost:8765/lab.html): `PY -m tool.swatches` paints a ball
  for every finish in `finishes.CATALOGUE` and opens it.
  After a change to `tool/server.py`, `tool/view.py` or `tool/notes.py`, stop whatever serves 8765 (our own
  `tool.swatches` or `tool.view`) and start `PY -m tool.swatches --no-tab` in the background:
  it serves without opening a tab (`--no-open` only paints).
  **The Lab shows only the tool's own data**, never a list of its own that could drift: a gap
  in the Lab is a gap in the tool, to fix in the tool (the user, 2026-09-26). Notes: "The Lab" in
  `CHECKLIST.md`. The UV map room (`lab.html?room=uv`, `viewer/lab-rooms.js`) comes from
  `tool/rooms.py` (its maps, parts and camera; every part must be in a room) and reads
  `view.export_uvmap`'s data (the map picks surfaces: `view._surfaces`, the shapes it outlines,
  `<Set>_Surfaces.png`), which `tool.view` and `tool.swatches` rebuild when the parts, the rooms or
  their code change. The car's room (the user's pick of the fresh layouts, A, 2026-09-28) is the car
  (`viewer/lab-studio.js`; the tags, `viewer/lab-tags.js`) and its timeline beside it, "With Claude"
  (`viewer/lab-car.js`, A of the timeline's mockups, 2026-09-28), with the car's name, in the game
  and Claude's status over them. The car
  reads the frames `tool.skin show` writes at each `Skin.step` (`view.export_steps`, `studio.json`)
  and follows Claude's painting; `install` paints without them. It drives the embedded viewer
  (`index.html?embed=1`) through `window.viewer`: `inset` (the box the car is framed in, the rest left
  to the tags), `track` (its points' places on the page, pushed at the end of each frame that moves
  them), `project`, `camera`, `go`, `mood`, `views` (the viewer's own Cam buttons: "Game view") and
  `picture({ crop: 'inset' })`. All of it is embed-only: the page online and Claude's snapshots
  mustn't change (compare a snapshot before and after). The embedded viewer draws only when something
  changed (the camera, a `window.viewer` call, a resize: `rouse`), so anything new that changes the
  picture on its own must call `rouse`. The embedded viewer with no skin has no car until its first
  `dress` (or `stock()`). Its notes on the car (`tool/notes.py`, `.notes/notes.json`: git-ignored,
  each computer keeps its own, writers take an mkdir lock) go through the viewer's server (`/api/notes`,
  this computer's pages only) and reach Claude through a UserPromptSubmit hook (`.claude/settings.json`),
  or at once through `tool.notes wait` in the background.
- The sets of options: `tool/sets.py` (its docstring is the key, standard library only) writes
  `skins/<car>/sets.json`, the only writer; the Lab's timeline reads it through `/api/sets?skin=<name>`
  (`sets.lab`: the car the skin is or is an option of), which also carries `said`, everything said in
  the Lab about the car and its options (`notes.timeline`: the user's notes, done or not, with their
  pictures, served as `/notes/<file>`, and Claude's lines, `by: "claude"`, from `tool.notes say` and
  `done --say`). Each option's picture is its gallery thumb, and a pick keeps every option's picture
  in `skins/<car>/sets/<n>/` (served as `/sets/<car>/<n>/<letter>.png`) for the timeline. A pick is a
  note with `answer` (the set, the option), the box's words a note with no point: the car's tags
  leave both out. Notes: "The design studio" (W3) and "The Lab's timeline" in `CHECKLIST.md`.
- `PY -m tool.snap --page "<page>"` photographs any page of the viewer's whole, e.g. a Lab room.
- The studio's critic: an agent, `.claude/agents/critic.md`, given only a car's brief and pictures
  (never the design). `tool/critic.py` (its docstring is the key) cuts `tool.snap`'s four sheets
  into its pictures (`--review`: the angles the others miss) and keeps its findings in
  `skins/<car>/review.json` (keep, mark: standard library only). Its test car, TSC_CriticTest,
  carries seven known faults (its design's docstring, never given to the critic). Notes: W2 in
  "The design studio", `CHECKLIST.md`.
- Several at once (the studio's three concept designers): paints take turns on a computer
  (`skin.paint_slot`, an OS lock on `paint<k>.lock` in the work folder, freed if a paint dies;
  `TSC_PAINTS=<n>` for more slots), since each paint needs a few GB and the Mac's old container (7.7 GB)
  lost two of three to its memory limit.
- Tyre markings: `tool/tyres.py` (its docstring says how the tyres' map wraps the wheel, and why
  its words are flip-proof), drawn in the map's own rows and columns, with relief in `Wheels_N`
  (the paint box's `Canvas.normal`); its tread library (TR codes) is the Lab's Treads, each drawn
  on the car's own tyre (`swatches.write_tread`, a lathe in `lab.js`). `PY -m tool.tyres` photographs the library
  (`tool/tyresheet.py`); `tyresheet.page(folder)` fills `viewer/tyres.html` for the user's page.
- Drawing on the skin, the one way lines are drawn: `tool/skinmesh.py` is the whole car's
  paintable surface as one mesh (its panels sewn across their joins, mirrored to the whole car and
  subdivided; `PY -m tool.skinmesh --build`, cached in the work folder); `tool/skindraw.py` draws on it (`through`, `taut`, `parallel`, `circle`, `loop`, `mirror`, `edge`, `meet`, `band`; `PY -m
  tool.skindraw --probe "place,place"`); `PY -m tool.skincheck <name>` (`--falsify`, `--floor`)
  measures every band on the car. Notes: "Drawing on the car's own skin" in `CHECKLIST.md`.
- The user's pins: the Lab's lines room (`lab.html?room=lines`, `viewer/lab-lines.js`; the car in
  the viewer's clay, `view.ensure_clay`, wheels off) saves them through `/api/lines` to
  `car/lines.json` (committed); `PY -m tool.lines` lists them. A pinned line's name is a place
  list for `skindraw.through`, which runs a curve through its pins.
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
  `build.build_zip` halves the normal map, then the roughness maps, when a zip runs over.
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
  | 0 | Brake lights: on at night, flaring when braking |
  | 32 | Energy, tinted in game (team colour); the RGB must be grey. Dark on the track (2026-09-27) |
  | 64 | Brake heat, on when braking hard (builds over ~1.5 s) |
  | 96 | Always glowing |
  | 128 | Front lights: off by day, the brightest at night |
  | 160 | Turbo colour; the RGB must be grey |
  | 192 | Exhaust heat, on during turbo |
  | 224 | Boost colour; the RGB must be grey |
  | 255 | Glowing at night only |
