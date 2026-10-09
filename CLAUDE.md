# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## The project

A tool that makes skins (paint jobs) from the user's words for the Trackmania 2020 stadium car
(CarSport). The user describes a skin in a chat; Claude shows it on the car and changes it until
they say yes, then installs it. They judge it by four things (`BRIEF.md`): they'd drive it in the
game; it's fast, minutes from their words to the car; it's all in words; it stays small and simple.

The user isn't technical and won't read code. Claude makes every technical decision.

**Every request to make, change, show or install a skin goes through the `skin` skill.** Load it
first.

## The rules

@RULES.md

## Where things are

- `RULES.md`: how we work, as the mistakes not to repeat. `IMPROVEMENTS.md`: the queue of what the
  tool should do better; whatever the user asks the tool to do better goes there, and it's worked
  on when they ask. `.claude/rules/tool.md` loads with the tool's code: checking a change (the
  self-test), the machinery's commands, the game's texture format.
- **Two computers** share the repo through GitHub: the Windows PC (the game, installing, the
  picture maker) and the Mac (designing, the viewer, snapshots). A hook pulls at the start of each
  session (if it failed, sort that out first), then checks the tool (`tool/doctor.py`: GitHub, the
  tool's Python, the Lab's server, the work folder, the game's list, the queue) and prints where each
  skin stands and what's open.
- `tool/`: the Python machinery. `viewer/`: the Lab, the one page with the car. `car/parts.json`: every part's
  name. `skins/<name>/`: one folder per skin. `skins/installed.json`: what the tool put in the game.
- `PY` is the tool's Python, run from the repo root: on the PC
  `%LOCALAPPDATA%\TrackmaniaSkinChallenge\venv\Scripts\python.exe`, on the Mac
  `"$HOME/Library/Application Support/TrackmaniaSkinChallenge/venv/bin/python"`. Its parent folder
  is the work folder (caches, builds, the viewer's data): all rebuildable.
- GitHub `fedecarbo/tm-skin-creator` (public), branch `main`. Never push files that aren't ours to
  publish. Credit the car model's author, amogusstrikesback2 (CC-BY-4.0), wherever it's reused.

## Don't look in the game's skin folder

`C:\Users\fedec\OneDrive\Documents\Trackmania\Skins\Models\CarSport\`

- It holds skins the user made outside this project. Never list, open, read, copy or unzip anything
  there, by any means (tools, shell or scripts), and never let them shape a choice.
  `.claude/settings.json` denies the file tools there, and a hook (`tool/guard.py`) refuses any
  shell command that names it. Don't work around either.
- Only `tool/install.py` writes there. It checks only its exact target file name, and never
  overwrites or deletes a file this project didn't create (`skins/installed.json` and sha256).

## Keeping this file useful

It loads every session: only what every session needs. Instructions for one part of the code go
in `.claude/rules/*.md` with `paths:`; the design routine in the `skin` skill. Delete what stops
being true.
