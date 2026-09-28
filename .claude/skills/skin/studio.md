# The studio

A car built the way a real car studio builds one, from the car's idea to the last detail (the
user, 2026-09-28: "not the typical amateur skins ... every single detail from start to finish").
The plan and its history: "The design studio" in `CHECKLIST.md`. Read this when the user asks for
the studio; `SKILL.md` still applies for everything it says about designing, checking, showing,
the record and installing.

## When

- Only when the user asks for it: "studio", "through the studio", "do it properly". Say so in
  one line ("I'll take this through the studio"). Anything else goes the quick way, exactly as
  `SKILL.md` says.
- First-time builds only, for now (the user, 2026-09-28: "lets focus on first time building, we
  can later figure the already built"). A studio car is a new car under a new name
  (`TSC_<Idea>`). A car made the old way stays on the Lab's stand with its notes.
- A studio car starts fresh: it borrows no looks from earlier cars, and no design of theirs,
  unless the user names one. What the game has taught about the car itself (`SKILL.md`, "What
  works on this car", and "Things we learned") still counts.

## How it runs

- The steps: Brief, Mood, Concepts, Shapes, Colours and materials, Wheels, Details, Lettering,
  Review, Road test, Release. One at a time, in that order.
- **A step stops for the user only when there's more than one real direction.** Then show the
  options and ask for a pick. When there's one sensible answer, do it, show it in a line or a
  picture and move on; the user can still say otherwise. A step that adds nothing on this car is
  skipped, and you say why in a few words. Technical choices stay yours.
- **Every step is checked against the brief.** An option that drifts from it isn't shown.
- **A decided step stays decided.** A later step never quietly changes an earlier decision: if it
  must, say so and ask.
- **Going back:** see the build sheet's `back`. Only the later steps a change affects need a
  look; say which, and why, in a few words.
- **The build sheet** (`tool/sheet.py`, its docstring is the key) is the car's record of the
  steps, the only thing the Lab's wizard will show. Keep it true at every move: `on` when you
  start a step, `option` for each option, `ask` once they're shown, `pick` or `decide` on the
  user's answer, `skip`, `back`. Run it on the PC as `PY -m tool.sheet`, on the Mac as
  `python3 -m tool.sheet` (no container). A pick deletes the options not kept (the user's rule,
  2026-09-28): tell the user in a few words, git's history keeps them.
- `notes.md` as for any skin: the user's words verbatim, the date and the model first, then a line
  per event (`Brief approved <date>: …`, `Picked <date>, <step>: …`, `Change <n> (user): …`).
- Commit and push after each decided step, so the other computer has it.

## 1. The brief

What the car is, agreed before anything is painted. Always the user's decision, and a
conversation, not a form (the user, 2026-09-28: "I would prefer if it's just open ended? Similar
to how other ai tools does that they like "what do you want to...", and then it reasons about it,
maybe help shape the direction. But obviously I don't want a complete form to fill out").

1. If they haven't said yet, ask one open question: **what car do you want to build?** A word, a
   feeling, a scene: anything goes.
2. Give the car a working name (`TSC_<Idea>`, CamelCase, a name no skin has), then
   `tool.sheet new <car> --words "<their words verbatim>"` and `tool.sheet on <car> brief`.
   Start `notes.md`. When the brief settles on something more telling, `tool.sheet rename` it
   before the yes (the first studio car began as TSC_Grass and became TSC_Ladybird).
3. Think about their words and answer as a designer would, in a few sentences of plain talk: the
   character you hear in the idea, what it could draw from (specific worlds: "a 1990s Le Mans
   prototype at night", "a Braun radio", never "motorsport"), the traps it could fall into ("a
   toy", "a gamer RGB car"), and where you'd take it. That's how you help shape it.
4. If there's a real fork in the direction, name it and ask the one question that settles it, in
   a sentence ("it could be quiet and menacing, or loud and proud: which is closer?"). Never a
   list of questions, never choices to tick. If their words leave nothing open, go straight to
   the card. A round or two at most.
5. Write the card, `skins/<car>/brief.md`: your reading, shaped by what they said, in this shape
   (the Lab will read it):

   ```markdown
   # <Title>: the brief

   The user's words (<date>): "<verbatim>"

   ## What it is
   <the character, in a sentence>

   ## Drawn from
   - <world>: <what it gives the car, in a few words>

   ## Not
   - <what it must not look like>

   ## Fixed
   - <what they said has to be there>, or "Nothing."
   ```

   "Fixed" holds only what the user asked for; the rest is your reading, which their yes approves.
6. Show the card in the reply, short, and ask in bold: **is this the car?** Changes go into the
   card and it's shown again. On a yes: `tool.sheet decide <car> brief "<the character, a few
   words>"`, `Brief approved` in `notes.md`, commit and push.

## 2. Mood

The brief turned into a look before it touches the car: two or three boards, each a real
direction (its own finish, graphic language and colour story, not three shades of one). Always the
user's decision on a new car.

1. `tool.sheet on <car> mood`.
2. Write each board as `skins/<car>/mood/<slug>.json` (its shape is in `tool/mood.py`'s
   docstring):
   - a title, and the direction in a sentence;
   - the colour story: main, support, one accent, with shares adding up to 100;
   - the finishes the car would wear, in its colours: they're painted on the Lab's balls, so
     they show the truth;
   - a wall of four pictures: a wide one first (the idea at a glance), whatever the brief fixes
     drawn in the board's style (TSC_Ladybird's grass fringe), and how it reads where it's used
     (from above on its map). Drawings are SVG you write; on the PC add the picture maker's
     (`tool.pictures`, kept in `mood/<slug>/`). Never pictures from the web. A drawn creature
     gets no face unless the brief asks for one.
   When drawings repeat (grass, spots), write them with a script in the scratchpad: the JSON is
   what's kept.
3. `tool.sheet option <car> mood "<title>" --file mood/<slug>.json` for each, in the order to
   show them (A, B, C).
4. `tool.mood <car>` (on the Mac `docker compose exec app python -m tool.mood <car>`), then look
   at the page yourself: `tool.mood <car> --snap` on the PC, `node docker/snap.mjs --page
   "mood.html?car=<car>"` on the Mac. Crop and enlarge every drawing: nothing cut off, nothing
   the brief's "Not" rules out. Fix and look again.
5. Open the page for the user (http://localhost:8765/mood.html?car=<car>; on the Mac `open` it),
   `tool.sheet ask <car> mood`, and reply: a line per board, the one you'd pick and why in a
   sentence, then in bold: which one, or what to take from each?
6. One board: `tool.sheet pick <car> mood <letter> "<its colour story and finish, a few words>"`.
   Two or more boards to carry on (the user, 2026-09-28: "c and b actually"): pick them together
   (`A+B`) and draw the concepts from both, one reading per board and one that blends them. A mix
   into one board: write it as a new option, show it, then pick it. The pick deletes the boards not
   kept and their pictures. `Picked` in `notes.md`, commit and push.

## 3. Concepts

Three truly different ideas on the car, rough on purpose: flat colour in the board's base finish,
the big shapes only, no details. Each a different reading of the brief and the mood (from two
boards: one per board and one that blends them). Always the user's decision.

1. `tool.sheet on <car> concepts`, then `tool.sheet option <car> concepts "<Title>"` for each:
   it makes `skins/<car>_<Title>/` (empty while the car has no design). Write each `design.py`
   there: `s.clay()`, a few steps, the body's big shapes, the wheels and inner car in one dark
   colour ("they get their own steps"). Each stands on its own: no concept loads another.
2. `tool.skin round "<Title> concepts" <car>_A=<Title> ...` before painting them, so a Lab
   that's already open shows the switch between them (recorded after, it showed only after a
   reload, and the user couldn't find concept B, 2026-09-28).
3. Paint each (`show`; on the Mac `docker compose exec app python -m tool.skin show <name>
   --no-snap`, then `node docker/snap.mjs <name>` and `--close`) and look: the six views and the
   close looks, as for any skin. Fix and look again. Then the picture (`--picture`, views front,
   left and top, the driving camera's close row for each) and `tool.sheet ask <car> concepts`.
4. Reply: a line per concept, the one you'd pick and why, that the Lab's stand flips between them,
   then in bold: which one, or what to take from each?
5. One: `tool.sheet pick <car> concepts <letter> "<the idea in a few words>"`: its design becomes
   the car's and the others go with their round; then `show <car>` to paint it under its own name.
   A mix the user spelled out ("I like B the most. I do like the grass from C though"): write it
   as a new option from the picked parts, check it as any concept, pick it, and show the car.
   Notes left on concepts the pick deleted still get marked done (`tool.notes done` takes them).

## The steps after Concepts

Still being built (W1's piece 4, `CHECKLIST.md`). Until then, after Concepts, tell the user the car
is waiting at Shapes and stop.
