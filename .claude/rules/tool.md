---
paths:
  - "tool/**"
  - "viewer/**"
  - "official/**"
  - "car/**"
---

# Working on the tool

The tool's manual: what to run and how the pieces fit, read when working on the tool. The rules
are in `RULES.md`. The top docstring of each `tool/*.py` is its key.

## Checking a change

- `PY -m tool.selftest --against <commit>` checks that every command, file and name the
  instructions give still exists (`tool/instructions.py`) and trips on code nothing uses or the
  tool grown past its budget (raise `BUDGET` only saying why) or a graphics-chip kernel giving other
  bits than its numpy twin (`tool/gpu.py`), then paints the user's car and the
  self-test's own cars (the tour, every other paint call; the planted-flaw pair, one car clean and
  one with the user's kinds of flaw planted) with this code and with that commit's, compares every
  texture, every DDS file, the notes, the palette and the steps, and says which planted flaws the
  judge names: for a change to a check, before and after. `--snap` compares the viewer's sheets pixel
  for pixel, `--at <commit>` tests a commit instead of the working tree. A commit's side is kept in
  the work folder, so it's paid for once per computer. Run it before committing a change to `tool/`.
  `--profile` says where one paint's time and memory go.
- A cache whose contents change must change its name or version (`coverage._key`), or the old code
  under test reads the new cache and agrees with it.
- Claude's snapshots must not change with a change made for a concept's page (snapshots, `?snap=1`, draw
  the car alone, drawn every frame, every mood loaded first). The camera (`viewer/viewer.js`, with `studio.js`
  and `lib/`) is an engine with no buttons of its own: a page drives it through `window.viewer` and hears its
  state through `viewer.on` (`EVENTS` in `viewer/viewer.js`), drawing its own buttons; `viewer/index.html` is the
  bare car. A concept's page imports it from the server's `/camera/` (the Lab's `page/lab-ui.js`): a change to the
  camera is made here only, and its `--snap` sheets stay pixel for pixel. The page draws only when something changed
  (`rouse`): anything new that changes the picture on its own must call it.

## Commands for the machinery

`PY` is the tool's Python, one for each computer (`CLAUDE.md`), from the repo root. The two
computers' differences live in `tool/paths.py` (the work folder, the snapshots' browser, opening a
picture, writing a file whole) and `requirements.txt` (the picture maker's packages, the PC only; MLX, the
graphics chip's, the Mac only).

- Set up a fresh clone: Python 3.14 (on the Mac Homebrew's `python@3.14`), `python -m venv <the
  work folder>/venv`, `PY -m pip install -r requirements.txt`, `PY -m pip install -e . --no-deps` (the tools as a
  package, `pyproject.toml`: `PY -m tool.<x>` and `from tool import` work from any folder, a concept's beside this
  one), on the Mac `PY -m playwright install
  --only-shell chromium` (with `PLAYWRIGHT_BROWSERS_PATH=<the work folder>/browsers`, where `paths`
  looks), `PY -m tool.prepare` (downloads Nadeo's template, checks the `official/` zips and unpacks
  them; the model zip is copied from the other computer), and on the PC `PY -m tool.pictures setup`
  (the picture maker's 16 GB of weights). Then the Lab's repo, tm-skin-lab on the same GitHub account, cloned
  beside this one.
- A skin's life: `tool/skin.py` paints a design (`paintbox.Skin`), `tool/judge.py` names what's
  wrong on it (`PY -m tool.judge <name>`; its docstring is the key: every graphic measured where it landed,
  one list of findings, block, warn and note, kept with the design's hash in `build/<name>/verdict.json`;
  a kind of flaw it misses is planted on the self-test's pair next), `tool/gate.py` makes the verdict
  bite (its docstring is the key: the commands that wait for it, and the hooks in `tool/guard.py`
  that refuse a pass's agent and hold a turn), `tool/build.py` puts it in the
  viewer and builds the zip (`PY -m tool.build <name>`: a trial build of the last show's zip, to
  see its size), `tool/install.py` puts it in the game (`PY -m tool.install <name> ...` installs
  built zips). Paints take turns on a computer (`skin.paint_slot`, an OS lock on `paint<k>.lock` in
  the work folder, freed if a paint dies; `TSC_PAINTS=<n>` for more slots): each needs a few GB.
- `PY -m tool.view <name>`: serves http://localhost:8765/?skin=<name> from `viewer/` (the bare car) and opens it. Run
  it in the background. `tool/server.py` is the tool's static server (a page folder at `/`, the camera at `/camera/`
  whatever the page folder, the work folder's data at `/data/`, `/api/health`; reads open to any origin, for a
  concept's page from another folder); a concept's own routes are a handler built on it (the Lab's, serving its own
  page on the same port, started by its doctor).
  The tools write, a concept reads: `tool.skin show` writes the frames the page follows at each `Skin.step`
  (`view.export_steps`, `studio.json`; `install` paints without them), `tool/progress.py` the job log (every
  command that makes the user wait opens a `progress.job`), and no tool command refreshes a concept's lists.
- The close looks (`tool/close.py`, its docstring is the key) read what show keeps (`judge.save`: `graphics.json`,
  every graphic's stations or middle; `owner.npy`, whose paint each texel holds) through the viewer's texel pass
  (`viewer.uvs`, snapshots only: which texel each pixel shows, never a blend).
- Tyre markings: `tool/tyres.py` (its docstring says how the tyres' map wraps the wheel, and why
  its words are flip-proof), drawn in the map's own rows and columns, with relief in `Wheels_N`
  (the paint box's `Canvas.normal`); its tread library (TR codes). `PY -m tool.tyres`
  photographs the library (`tool/tyresheet.py`).
- A marking along the car's own lines or the user's stroke is a course (`tool/course.py`, its
  docstring is the key: the line's points every 0.25 cm, every one on the surface; a marking's width and
  side measured along the surface, the judge reading it back every half centimetre). A line beside a
  line is the surface's contour of the distance, a line carried on or joined to another the surface's
  straightest way: nothing is smoothed in the air and pushed back.
- The car's surface (`tool/surface.py`, its docstring is the key): the mesh welded and repaired once, exact
  distances and lines along it (`S.signed`: a line put in as a chain of the surface's edges, the surface cut
  along it, each side measured from its own copy; half a second to two a line; `S.path`, the straightest way
  through points, `S.carry`, a line carried on, `Field.contour`, a line beside a line: milliseconds; where a
  band's edge or a line beside a line bends across faces too big for it, those faces are cut finer and the
  distance solved again, to within half a texel), and every texel's face and weights from the bake's
  triangle; the foundation every graphic on the car is laid on and measured by. It rebuilds itself when the
  mesh changes (`PY -m tool.surface`, a tenth of a second, says what it did in numbers).
- The car map (`tool/carmap.py`: the open air each spot sees, where along the car it is) is built on the
  surface and rebuilds itself after it (`PY -m tool.carmap`, a minute), and so are the wear maps, per texel
  (`tool/wear.py`, its docstring is the key: how sharply the body bends, the open air, how thick, how far in from
  its outline; `PY -m tool.wear`, a minute): wear reads only them. The car in words, `car/anatomy.md`,
  comes from the model's lines and the map: after a change to either, `tool.carmap --describe` again, and
  retake its picture `car/map/model.jpg` (`tool.snap Template --body`). The model's own lines on the maps and on
  the car (`view.export_template`, from `meshlines.template`) are rebuilt when the mesh or `meshlines.py` change.
- Parts: `PY -m tool.parts` turns `tool/naming.py` into `car/parts.json` (`--review` renders the
  car coloured by part). `parts.load().mask(bake, "Details", "brake caliper", side="left",
  end="front")` is a texel mask. See `shared` in `car/parts.json` for shared texels.

## Facts the code doesn't say

- The car faces +z, y up, its left is +x, in cm (the FBX: Skin_01, Details_01, Wheels_01,
  Glass_01). The wheels' axles are fitted (`shapes.WHEEL_Y/Z`); the viewer lifts the car 1.2 cm.
- A shared texel's baked position may be another part's (the bake keeps the last triangle): zone a
  shared Details part with `parts.load().local_bake(...)`.
- `_R` maps: R roughness, G metalness (three.js reads G and B: swizzle). Dirt: 255 is full dust,
  the stock averages 53. Glass is tint only. A zip needs no spaces in its name and an `Icon.tga`;
  the running game finds a new skin without a restart.
- A glow's edge takes the nearest texel's code (the game blends colour, not code):
  `paintbox.dark_take_codes`. `glow()` also tints the paint.
- The game maps light to the screen straight, clipping each channel at white (the viewer's
  `LinearToneMapping` at 1.44). Fit its cameras' lens from screenshots, never by eye.
- Codes the user copies never reorder (`finishes.CATALOGUE`, the tyres' TY and TR): a new one goes
  at the end of its family, a retired one leaves None.
- Don't merge look-alike code that rounds differently (float32 against float64 conversions differ
  by a level on about 4 % of values). A check keeps its own copies of what it checks.
- Windows: long heredocs through Git Bash get cut off (write a script to the scratchpad); GNU sed
  reads backslash-backtick as text's start; the Edit tool reads `$'` as a replace pattern; a file
  another program has open can't be replaced (`paths.write` retries).
- Agents load when a session starts: a new or changed `.claude/agents/*.md` reaches the next one.
  `car/parts.json` shows up changed: delete the work folder's `parts_stats.json`, run `tool.parts`.

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
  | 32 | Energy, tinted in game (team colour); the RGB must be grey. Dark on the track |
  | 64 | Brake heat, on when braking hard (builds over ~1.5 s) |
  | 96 | Always glowing |
  | 128 | Front lights: off by day, the brightest at night |
  | 160 | Turbo colour; the RGB must be grey |
  | 192 | Exhaust heat, on during turbo |
  | 224 | Boost colour; the RGB must be grey |
  | 255 | Glowing at night only |
