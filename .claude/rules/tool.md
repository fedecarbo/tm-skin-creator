---
paths:
  - "tool/**"
  - "viewer/**"
  - "resources/**"
  - "car/**"
---

# Working on the tool

The tool's manual, read when working on the tool. Each tool is one file in `tool/`, and the top docstring of each
`tool/*.py` is its key: what it's for, its commands, how it's used. This file holds only what no docstring holds.
The rules are the mistakes not to repeat: a new rule replaces or merges another, and a fact about the game or the
code goes into the code (a warning, a check, a docstring).

## The rules

- **Don't add a step that every skin pays for.** The cost repeats on every car. Say first what a step costs in
  time; if every skin would pay it, leave it out.
- **Don't build machinery the user hasn't seen.** One step at a time, shown, then their OK. When they doubt
  something, ask what they'd need to see before building more on it.
- **Don't grow the instructions.** The more there is to read, the slower and more alike the work. Replace or
  merge instead of adding; a fact that prevents a mistake goes into the code. The self-test holds the
  instructions to a word budget (`WORDS` in `tool/selftest.py`) as it holds the code to a line budget.
- **Don't mention what no longer exists, or how things used to be,** in instructions, comments or docstrings.
  Naming it puts it back in mind. Write as if things had always been this way; history is in git. (A skin's
  `notes.md` is its record, and keeps its story.)
- **Don't change the tool without the self-test.** Every car's game files stay identical, byte for byte, unless
  the change means to alter them, and the commit says which and why.
- **Don't guess.** Measure slowness before fixing it, and check the viewer against the game before building a
  fix for it.
- **Don't take the game's own files apart.** The licence forbids it and they're encrypted. Nadeo's published
  files, the stock textures and the user's screenshots and videos are fair.
- **Don't pick a tool or library from memory.** Look up its latest release first. Offer a one-time-payment
  option when it's far better; discuss any subscription first.

## Checking a change

- `PY -m tool.selftest --against <commit>` (its docstring is the key): the instructions' names checked
  (`tool/instructions.py`), the tripwires (code nothing uses, code written twice, errors hidden, the code and
  the instructions past their budgets: raise `BUDGET` or `WORDS` only saying why in the commit), the graphics
  chip's kernels against their numpy twins (`tool/gpu.py`), then the user's car and the self-test's own cars
  painted with this code and with that commit's and compared texture by texture, DDS by DDS, with the notes, the
  palette, the steps and the planted flaws the judge names. `--snap` compares the viewer's sheets pixel for
  pixel, `--at <commit>` tests a commit instead of the working tree, `--profile` says where one paint's time and
  memory go. A commit's side is kept in the work folder, so it's paid for once per computer. Run it before
  committing a change to `tool/`; on the Mac, one paint at a time (each takes a few GB).
- A cache whose contents change must change its name or version (`coverage._key`), or the old code under test
  reads the new cache and agrees with it.
- Claude's snapshots must not change with a change made for a concept's page (snapshots, `?snap=1`, draw the
  car alone, drawn every frame, every mood loaded first). The camera (`viewer/viewer.js`, with `studio.js` and
  `lib/`) is an engine with no buttons of its own: a page drives it through `window.viewer` and hears its state
  through `viewer.on` (`EVENTS` in `viewer/viewer.js`), drawing its own buttons; `viewer/index.html` is the bare
  car. A concept's page imports it from the server's `/camera/` (the Lab's `page/lab-ui.js`): a change to the
  camera is made here only, and its `--snap` sheets stay pixel for pixel. The page draws only when something
  changed (`rouse`): anything new that changes the picture on its own must call it.

## The machinery

`PY` is the tool's Python, one for each computer (`CLAUDE.md`), from the repo root. The two computers'
differences live in `tool/paths.py` (the work folder, the snapshots' browser, opening a picture, writing a file
whole) and `requirements.txt` (the picture maker's packages, the PC only; MLX, the graphics chip's, the Mac only).

- Set up a fresh clone: Python 3.14 (on the Mac Homebrew's `python@3.14`), `python -m venv .venv` (on the PC,
  the work folder's `venv`), `PY -m pip install -r requirements.txt`, `PY -m pip install -e . --no-deps` (the
  tools as a package, `pyproject.toml`: `PY -m tool.<x>` and `from tool import` work from any folder, a
  concept's beside this one), on the Mac `PY -m playwright install --only-shell chromium` (with
  `PLAYWRIGHT_BROWSERS_PATH=<the work folder>/browsers`, where `paths` looks), `PY -m tool.prepare` (downloads
  Nadeo's template, checks the `resources/official/` zips and unpacks them; the model zip is copied from the
  other computer), and on the PC `PY -m tool.pictures setup` (the picture maker's 16 GB of weights). Then the
  Lab's repo, tm-skin-lab on the same GitHub account, cloned beside this one.
- A skin's life, one tool each, its docstring the key: `tool/skin.py` reads a design against the car (every call's
  landing in its receipt, `tool/receipt.py`; drawn by `tool/sketch.py`), paints it (`paintbox.Skin`, the toolbar
  every design calls) and shows or installs it; `tool/judge.py` names what's wrong on it; `tool/gate.py`
  makes the verdict bite, with the hooks in `tool/guard.py`; `tool/close.py` looks close up; `tool/build.py`
  puts it in the viewer and builds the zip; `tool/install.py` puts it in the game. Paints take turns on a
  computer (`skin.paint_slot`, an OS lock on `paint<k>.lock` in the work folder, freed if a paint dies;
  `TSC_PAINTS=<n>` for more slots).
- The camera: `tool/server.py` serves it (`PY -m tool.view <name>` serves and opens the bare car; run it in the
  background), `tool/view.py` prepares its data, `tool/snap.py` takes Claude's snapshots. The tools write, a
  concept reads: `tool.skin show` writes the step frames a page follows and each step's strokes, what was meant
  beside where it landed and what the judge found on it (`view.export_steps`), `tool/progress.py` the job log,
  and no tool command refreshes a concept's lists.
- The car: `tool/surface.py` (the foundation every graphic is laid on and measured by), `tool/carmap.py` (the open
  air, where along the car), `tool/wear.py` (the wear maps), `tool/meshlines.py` (the model's own lines, the
  template, the car's answers to questions), `tool/course.py` (markings along a line), `tool/marks.py` (shapes on a
  panel), `tool/tyres.py` (the tyres' map and markings), `tool/parts.py` (the names, from `tool/naming.py`, into
  `car/parts.json`). After a change to the mesh or to `meshlines.py`: the surface, the car map, the wear maps and
  the flat rooms rebuild themselves (`PY -m tool.surface`, `tool.carmap`, `tool.wear` do it by hand); then
  `tool.carmap --describe` rewrites the page `car/anatomy.md` (the axes, where a graphic stops).

## Facts the code doesn't say

- A shared texel's baked position may be another part's (the bake keeps the last triangle): zone a shared
  Details part with `parts.load().local_bake(...)`.
- Fit the viewer's cameras' lens from screenshots, never by eye.
- Don't merge look-alike code that rounds differently (float32 against float64 conversions differ by a level on
  about 4 % of values). A check keeps its own copies of what it checks.
- Windows: long heredocs through Git Bash get cut off (write a script to the scratchpad); GNU sed reads
  backslash-backtick as text's start; the Edit tool reads `$'` as a replace pattern; a file another program has
  open can't be replaced (`paths.write` retries).

## The game's files

The game takes DDS files with legacy D3D9 headers (`DXT1`, `DXT5`, `ATI1`, `ATI2`; never DX10, so no BC7):
`tool/dds.py` writes only those. Which map takes which compression and size is `paintbox.Skin.textures`
(`SIZES`, the FourCC per file); the zip's budget is `build.ZIP_BUDGET`; what each alpha code of `Details_I` makes
a glow do, and what the game showed for each, is `finishes.GLOWS`. The source is Nadeo's `ReadMe.txt` and its post
"Stadium CAR Ressources" (links in `resources/official/SOURCES.md`). The shaders blend ambient occlusion
themselves: never bake it into a texture.

## Source assets (`resources/official/`)

Leave the zips unchanged: `resources/official/SOURCES.md` records their sha256. Extract them to a working folder
and never edit them in place. They're git-ignored because the GitHub repo is public. A fresh clone downloads them
from the links in `SOURCES.md`.

- `CarSport-Template.zip` (from Nadeo): `ReadMe.txt` and the flat UV maps `UV_Skin.png`, `UV_Skin_Hollow.png`
  and `UV_Details_Hollow.png` (2048×2048), plus `UV_Details.png`. That one is **2018×2018**, so scale it before
  overlaying.
- `CarSport-Model.zip` is a community upload on Sketchfab. It is **CC-BY-4.0, so credit the author,
  amogusstrikesback2,** wherever you reuse the model. It holds `textures/*.png` and a nested
  `source/StadiumCAR2020_OffsetFix.zip`, which contains the FBX mesh and the unpainted DDS textures (`Skin_*`,
  `Details_*`, `Wheels_*`, `Glass_*`). The main textures are 2048×2048.
