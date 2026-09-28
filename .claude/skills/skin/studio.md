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

What the car is, agreed before anything is painted. Always the user's decision.

1. Name the car (`TSC_<Idea>`, CamelCase, a name no skin has), then
   `tool.sheet new <car> --words "<their words verbatim>"` and `tool.sheet on <car> brief`.
   Start `notes.md`.
2. Ask the brief's questions in one go with the question tool (AskUserQuestion), each with
   word choices drawn from *their* idea, never generic ones. Skip a question their words already
   answer. Every option is a real, different reading, in a few words, with a line on how the car
   would look.
   - **The character** (one pick): three readings of the idea ("calm but dangerous", "loud and
     playful", "precise, like an instrument").
   - **Drawn from** (several picks): the worlds the look could borrow from: a real race car, a
     product, a place, a film, a craft. Specific ones ("a 1990s Le Mans prototype at night",
     "a Braun radio"), never "motorsport".
   - **Not** (several picks): what it must not look like: the traps this idea falls into ("a toy",
     "a gamer RGB car", "a sticker bomb").
   - **Fixed** (several picks): anything that has to be there: a colour, a word, a number. Offer
     what their words hint at, and "nothing fixed".
3. Write the card, `skins/<car>/brief.md`, in this shape (the Lab will read it):

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
   - <what has to be there>, or "Nothing."
   ```

   Their answers in their words where they typed their own. Add nothing they didn't choose
   except the plain reading of their idea.
4. Show the card in the reply, short, and ask in bold: **is this the car?** Changes go into the
   card and it's shown again. On a yes: `tool.sheet decide <car> brief "<the character, a few
   words>"`, `Brief approved` in `notes.md`, commit and push.

## The steps after the brief

Still being built (W1's pieces 3 and 4, `CHECKLIST.md`). Until then, after the brief, tell the
user the car is waiting at Mood and stop.
