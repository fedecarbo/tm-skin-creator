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
  instructions give still exists (`tool/instructions.py`), then paints the user's car and the
  self-test's own tour car (every other paint call) with this code and with that commit's, and
  compares every texture, every DDS file, the notes and the record; `--snap` compares the
  viewer's sheets pixel for pixel, `--at <commit>` tests a commit instead of the working tree. A
  commit's side is kept in the work folder, so it's paid for once per computer. Run it before
  committing a change to `tool/`.
- `PY -m tool.record` scores the checks against the user's record (the test set `tool/record.json`;
  `tool/record.py`'s docstring is the key): each car they were shown before a flaw they pointed out, painted again with this
  code; how many flaws the checks name first (a few minutes). For a change to a check, before and
  after. `tool.record new` lists what the records say that the test set hasn't sorted yet.
- A cache whose contents change must change its name or version (`coverage._key`,
  `view.UVMAP_VERSION`), or the old code under test reads the new cache and agrees with it.
- Claude's snapshots must not change with a change made for the Lab (the embedded viewer's
  features are `embed`-only). Every page draws only when something changed
  (`rouse` in `viewer/viewer.js`): anything new that changes the picture on its own must call it.
  Snapshots (`?snap=1`) draw every frame and load every mood first.

## Commands for the machinery

`PY` is the tool's Python, one for each computer (`CLAUDE.md`), from the repo root. The two
computers' differences live in `tool/paths.py` (the work folder, the snapshots' browser, opening a
picture, writing a file whole) and `requirements.txt` (the picture maker's packages, the PC only).

- Set up a fresh clone: Python 3.14 (on the Mac Homebrew's `python@3.14`), `python -m venv <the
  work folder>/venv`, `PY -m pip install -r requirements.txt`, on the Mac `PY -m playwright install
  --only-shell chromium` (with `PLAYWRIGHT_BROWSERS_PATH=<the work folder>/browsers`, where `paths`
  looks), `PY -m tool.prepare` (downloads Nadeo's template, checks the `official/` zips and unpacks
  them; the model zip is copied from the other computer), and on the PC `PY -m tool.pictures setup`
  (the picture maker's 16 GB of weights).
- A skin's life: `tool/skin.py` paints a design (`paintbox.Skin`), `tool/checks.py` names what's
  wrong on it (`PY -m tool.checks <name>`; its docstring is the key), `tool/build.py` puts it in the
  viewer and builds the zip (`PY -m tool.build <name>`: a trial build of the last show's zip, to
  see its size), `tool/install.py` puts it in the game (`PY -m tool.install <name> ...` installs
  built zips). Paints take turns on a computer (`skin.paint_slot`, an OS lock on `paint<k>.lock` in
  the work folder, freed if a paint dies; `TSC_PAINTS=<n>` for more slots): each needs a few GB.
- `PY -m tool.view <name>`: serves http://localhost:8765/?skin=<name> and opens it. Run it in the
  background. `tool/server.py` is the server: the pages, the work folder's data, and the Lab's
  `/api/notes`, `/api/sets` and `/api/progress` (what the tool is doing,
  `tool/progress.py`: every command that makes the user wait opens a `progress.job`), for this
  computer's pages only.
- The Lab (`viewer/lab.html`, http://localhost:8765/lab.html): `PY -m tool.swatches` paints a ball
  for every finish in `finishes.CATALOGUE` and serves it; `PY -m tool.doctor server` starts it
  detached (a background task is stopped at its time limit, and the Lab with it) and restarts it
  after a change to the tool; the session-start hook (`PY -m tool.doctor session`) does the same when
  the server's code is older than the tool's (`/api/health`), prunes the work folder of skins that
  no longer exist, and keeps the server's output in the work folder's server.log. A gap in the Lab
  is a gap in the tool, to fix in the tool. Its rooms share `viewer/lab-common.js`:
  - the car (`lab-studio.js`, its tags `lab-tags.js`) and its timeline, "With Claude"
    (`lab-car.js`); its Mesh button lays the template's mesh over the paint (`viewer.mesh`, embed only,
    `template/<Set>_Mesh.png`). The car follows the frames `tool.skin show` writes at each `Skin.step`
    (`view.export_steps`, `studio.json`; `install` paints without them), and drives the embedded
    viewer (`index.html?embed=1`, no car until its first `dress` or `stock()`) through
    `window.viewer`: `inset`, `track`, `project`, `camera`, `go`, `mood`, `views`, `picture`, and the
    pen: `pen`, `onStroke`, `drawings`.
  - the UV map room (`lab.html?room=uv`, `lab-rooms.js`), from `tool/rooms.py` (every part must be
    in a room) and `view.export_uvmap` (`<Set>_Surfaces.png`), rebuilt when the parts, the rooms or
    their code change; its Template (`view.export_template`, the model's own lines from
    `meshlines.template`) on the maps and on the car, rebuilt when the mesh or `meshlines.py` change.
  - the materials (`lab.js`; the balls by `balls.js`).
  - the notes on the car (`tool/notes.py`: `.notes/notes.json`, git-ignored, each computer its own,
    writers take an mkdir lock) reach Claude through a UserPromptSubmit hook (`.claude/settings.json`)
    or at once through `tool.notes wait` in the background. The hook runs `notes.py` as a script,
    perhaps on the Mac's own python3: it stays standard library only.
- The sets of options: `tool/sets.py` (its docstring is the key, standard library only) writes
  `skins/<car>/sets.json`, the only writer; the Lab's timeline reads it through `/api/sets?skin=<name>`
  (`sets.lab`: the car the skin is or is an option of), which also carries `said`, everything said in
  the Lab about the car and its options (`notes.timeline`: the user's notes, with their pictures,
  served as `/notes/<file>`, and Claude's lines, `by: "claude"`, from `tool.notes say` and `done
  --say`). Each option's picture is its gallery thumb, and a pick keeps every option's picture in
  `skins/<car>/sets/<n>/` (served as `/sets/<car>/<n>/<letter>.png`) for the timeline. A pick is a
  note with `answer` (the set, the option), the box's words a note with no point: the car's tags
  leave both out.
- The widgets in the timeline (`tool/notes.py`'s docstring is the key): a set, Claude's question
  (`tool.notes ask`, `settle`: a Claude line with `ask`, its choices' pictures copied into `.notes/`
  and served as `/notes/<skin>-ask<k><key>.png`) and yes or no. An answer is a note with `answer`,
  checked in `notes.add` against its question. The timeline redraws whole on every change, so
  `lab-car.js` keeps a widget's typed words and ticks by widget (`drafts`, `chosen`) and gives the
  focus back.
- `PY -m tool.snap --page "<page>"` photographs any page of the viewer's whole, e.g. a Lab room.
- Tyre markings: `tool/tyres.py` (its docstring says how the tyres' map wraps the wheel, and why
  its words are flip-proof), drawn in the map's own rows and columns, with relief in `Wheels_N`
  (the paint box's `Canvas.normal`); its tread library (TR codes) is the Lab's Treads, each drawn
  on the car's own tyre (`swatches.write_tread`, a lathe in `lab.js`). `PY -m tool.tyres`
  photographs the library (`tool/tyresheet.py`).
- A marking along the car's own lines or the user's stroke is a course (`tool/course.py`, its
  docstring is the key: the line's points every 0.25 cm, zones measured square to it).
- The car map (`tool/carmap.py`; in words `car/anatomy.md` and `car/map/tables.md`, its pictures in
  `car/map/`) rebuilds itself when the mesh changes (`PY -m tool.carmap`, 30 s). After a change to its
  code: rebuild, `tool.carmap --describe` again (on the Mac, whose map the pages hold: the two
  computers trace different ridges, `IMPROVEMENTS.md`) and retake the pictures in `car/map/`
  (`tool.snap <name> --body` of a car painted by the map's zones; `flow.jpg` paints each of
  `carmap.flow_lines` in its colour, `carmap.COLOURS`, as a 3 cm strip of `course.flow`).
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
