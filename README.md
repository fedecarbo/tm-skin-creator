# tm-skin-creator

The tools that paint a skin (a paint job) for the Trackmania 2020 stadium car from the user's words, judge what
landed, photograph it, build the game file and install it. A front end (the Lab, `../tm-skin-lab`) plugs into them.

- `tool/`: the machinery, in Python.
- `viewer/`: the camera, the car in its studio (three.js).
- `car/`: the car's data: its parts, its map, the car in words.
- `skins/`: one folder per skin: its design, its language, its record, its art.
- `resources/`: what we didn't make: Nadeo's template and the car model (`official/`, with their sources), and other
  players' skins kept for reference (`community/`, not in git).
- `research/`: the state-of-the-art study of October 2026 and its notes.
- `work/` (not in git): everything the tools make or cache: the painted maps the camera shows, the pictures, the game
  files, the caches. Safe to delete; the tools remake it. `.venv/` is the tools' Python.
- `BRIEF.md` (what the user wants), `CLAUDE.md`, `RULES.md` and `IMPROVEMENTS.md` (how the work is done, and its queue).

The car model is by amogusstrikesback2 (CC-BY-4.0).
