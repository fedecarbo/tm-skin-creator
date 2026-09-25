# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## The project

A tool that makes skins (paint jobs) from the user's words for the Trackmania 2020 stadium car
(CarSport). The user describes a skin in a chat. Claude shows it on the car and changes it until
the user says yes, then installs it so they can pick it in the game. From the user's brief
(`BRIEF.md`), they judge it by four things:

- **They like the skin in the game:** one they would actually drive with, not only one that
  looks good in a picture.
- **It's fast:** from their words to the car in minutes, not hours.
- **It's all in words:** they never open a paint program or touch a file.
- **It stays small and simple:** they'd rather have less machinery than more.

The user isn't technical and won't read code or the files that describe a design. Claude makes
every technical decision. Ask them only about what the skin should look like, and whether they
like what you show them.

**Every request to make, change, show or install a skin goes through the `skin` skill**
(`.claude/skills/skin/SKILL.md`). Load it first.

## Talking to the user

- Use plain words. Leave code, file names, paths and jargon out of replies unless they ask.
- Show rather than describe. A preview picture beats a paragraph.
- Ask only about taste and real trade-offs. Don't ask about things good design handles anyway:
  a question about their driving camera felt pointless (2026-09-23).
- The user is happy to test in the game (drive, brake, turbo, day and night, F12 screenshots).
  Ask for that whenever the game is the only way to know.

## Where things are

- **Checkpoint 8 is waiting for the user.** They make a skin in a fresh chat through the `skin`
  skill. Once they've seen it work, tick checkpoint 8 in `CHECKLIST.md`, commit and push, and
  delete this line.
- The tool was built in checkpoints 0 to 8 (`CHECKLIST.md`). That file is the history, not a
  to-do list: every decision, and "Things we learned" from the game and the tests. It's long,
  so search it rather than read it all. `.claude/rules/tool.md` loads with the tool's code:
  commands for the machinery, the source assets and the game's texture format.
- `IMPROVEMENTS.md`: the queue of things the tool should do better. **Whatever the user asks the
  tool to do better (the viewer, new abilities, fixes) is an improvement, never a new
  checkpoint** (the user, 2026-09-25): it goes on that list, and a big one keeps its working
  notes under "Improvements after the build" in `CHECKLIST.md`. The `skin` skill says how the
  list is kept. Work on it when the user asks. "Under way" says what's in progress.
- **Two computers** share the repo through GitHub: this Windows PC (the game, installing,
  snapshots; no Docker) and a Mac (the viewer through Docker, `docker compose up`). A hook in
  `.claude/settings.json` pulls at the start of each session: if it failed, sort that out
  first. Work that isn't pushed doesn't exist on the other computer.
- `tool/`: the Python machinery. `viewer/`: the 3D page and the gallery. `car/parts.json`: every
  part's name. `skins/<name>/`: one folder per skin. `skins/installed.json`: what the tool has put
  in the game.
- `PY` is `%LOCALAPPDATA%\TrackmaniaSkinChallenge\venv\Scripts\python.exe`, run from the repo
  root.
- Work folder `%LOCALAPPDATA%\TrackmaniaSkinChallenge\`: `venv`, `official` (unpacked zips),
  `cache` (the parsed mesh and bakes), `build` (pictures, DDS files and zips), `models` (the
  picture maker's weights), `textures`, `viewer` (what the viewer page loads). All of it is
  rebuildable.
- Record technical decisions in the repo (the code, `CHECKLIST.md`, or this file if every
  session needs them), so the next cold session finds them.
- Version control: GitHub `fedecarbo/tm-skin-creator` (public), branch `main`. Commit and push
  without asking after each finished piece of work (a skin shown or installed, an improvement
  or a step of one, a checkpoint ticked), and before a session stops mid-way, so the other
  computer starts from it (the user, 2026-09-23 and 2026-09-25). Never push files that aren't
  ours to publish.
- Before adding any tool or library, look up its latest release and use that version, then
  record it. If a paid option would be far better, tell the user and discuss it before using it.
  Always suggest a one-time-payment tool when its quality is far better (user, 2026-09-24).
- Credit the car model's author, amogusstrikesback2 (CC-BY-4.0), wherever the model is reused.

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

## Keeping this file useful

It loads every session, so keep it short: only what every session needs. Instructions for one
part of the code go in `.claude/rules/*.md` with `paths:`. The design routine lives in the
`skin` skill. Delete lines that stop being true.
