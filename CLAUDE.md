# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## The project

The tools that paint a skin (a paint job) for the Trackmania 2020 stadium car (CarSport) from the user's words: the
paint box and everything it paints with, the judge that measures what landed, the camera that photographs it, the
build and the install into the game. The user judges a skin by four things (`BRIEF.md`): they'd drive it in the
game; it's fast, minutes from their words to the car; it's all in words; it stays small and simple.

The user isn't technical and won't read code. Claude makes every technical decision.

The user designs a car in a **concept**: an interface with its own workflow, instructions, skill and repo, beside
this one, that runs the tools (pip-installed into the work folder's venv, so `PY -m tool.<x>` and `from tool
import` work from any folder). **The tools write, a concept reads:** the tools produce the car's data, every skin's
maps, the step frames, the verdicts, the job log (the work folder's viewer data, served by `tool/server.py`); a
concept reads them over the tools' server and writes only its own things. Concept 1 is the Lab
(`~/Developer/personal/tm-skin-lab`: the one page with the car, the user's notes on it, sets of takes); concept 2
the world (`~/Developer/personal/tm-world`). A session here works on the tools: it paints only the self-test's
cars, or a car the user asks for outright, and then it reads the `paint` skill first (the craft and the manual:
`.claude/skills/paint/SKILL.md`, which every concept's skill reads before painting).

## The rules

@RULES.md

## Where things are

- `RULES.md`: how we work, as the mistakes not to repeat. `IMPROVEMENTS.md`: the queue of what the
  tool should do better; whatever the user asks the tool to do better goes there, and it's worked
  on when they ask. `.claude/rules/tool.md` loads with the tool's code: checking a change (the
  self-test), the machinery's commands, the game's texture format.
- **Two computers** share the repo through GitHub: the Windows PC (the game, installing, the
  picture maker) and the Mac (designing, snapshots). A hook pulls at the start of each
  session (if it failed, sort that out first), then checks the tool (`tool/doctor.py`: GitHub, the
  tool's Python, the work folder, the game's list, the queue).
- `tool/`: the Python machinery. `viewer/`: the camera, the page the snapshots are taken on. `car/parts.json`:
  every part's name. `skins/<name>/`: one folder per skin: its design, its language, its record (`notes.md`), its
  art; a concept edits this repo only here. `skins/installed.json`: what the tool put in the game.
- `PY` is the tool's Python, run from the repo root: on the Mac `.venv/bin/python`, on the PC
  `%LOCALAPPDATA%\TrackmaniaSkinChallenge\venv\Scripts\python.exe`. The work folder (caches, builds, the
  viewer's data, the snapshots' browser: all rebuildable, never in git) is `work/` on the Mac and the PC's venv's
  parent, outside its OneDrive (`tool/paths.py`).
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
in `.claude/rules/*.md` with `paths:`; the craft in the `paint` skill. Delete what stops being true.
