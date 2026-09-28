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

- **Three steps:** Brief, Concepts, The car. Eleven until 2026-09-28, when the user, trying the
  wizard, said "it feels like a lot of steps ... Im really not sure if Im overengineering all of
  this", then: "I would keep it simple, after concepts, I would just have the 3d car and you just
  make changes, with the comments pop up windows throught". So the mood lives inside Concepts, and
  after the pick everything else (the shapes, the finishes, the wheels, the details, the lettering)
  happens on the car itself, from their notes on it, until they're happy; then the check and the
  release. TSC_Ladybird was built with the eleven.
- **A step stops for the user only when there's more than one real direction.** Then show the
  options and ask for a pick. When there's one sensible answer, do it, show it in a line or a
  picture and move on; the user can still say otherwise. A step that adds nothing on this car is
  skipped, and you say why in a few words. Technical choices stay yours.
- **Each field has its expert's know-how:** short guides in `guides/` beside this file, read when
  the work reaches their field and at no other time: `mood.md` and `shapes.md` at Concepts; on the
  car, `shapes.md` and `colours.md` for the shapes and finishes, `wheels.md`, `details.md` and
  `lettering.md` for theirs. Each says what good looks like in that field, what the car and the
  tool allow there, what to check. When a field's work is done, add what the car taught to its
  guide's "Learned" (dated, the car's name, a line or two), so the experts grow with every car. The
  critic (3, the check) has its own instructions.
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
- **The Lab's wizard** (the user's pick of the screens, 2026-09-28): a studio car opens in the Lab
  with its sheet on the left. The brief and the concepts are pages (the card, the three cars side
  by side with a Pick on each); after them, the car itself on the stand, where the user leaves
  notes on it (the user, 2026-09-28: "that could already as a 3d model where I can use the nice
  comment windows that we currently have"), with "Happy with it", and a Pick for the take on show
  when you offer a round of options. A box for their own words is on every step. Open it once the car has a sheet (http://localhost:8765/lab.html?skin=<car>; on the
  Mac `open` it) and say once that they can answer there or in the chat. It shows only the sheet,
  the brief's card, the options' pictures (their gallery thumbs: take each option's snapshot before
  `ask`) and the stand, so keep the sheet true and the page follows.
- **Waiting for their answer:** after every `ask` (the brief's too), start `python3 -m tool.notes
  wait` (on the PC `PY -m tool.notes wait`) with the Bash tool in the background, then end the
  turn. A pick, a yes or words in the wizard end it at once and print it as the hook does ("in the
  Lab's wizard at the Concepts step, picked B (Sunny): "…""), which wakes you with no message in
  the chat. Act on it as on a reply in the chat, then `tool.notes done <car> <n>`. One wait at a
  time: if they answer in the chat instead, the wait goes on to the next note, or two hours.
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
6. `tool.sheet ask <car> brief` (the wizard shows the card with "Approve the brief"), then show
   the card in the reply, short, and ask in bold: **is this the car?** Changes go into the card
   and it's shown again. On a yes: `tool.sheet decide <car> brief "<the character, a few words>"`,
   `Brief approved` in `notes.md`, commit and push.

## 2. Concepts

Its guides: `guides/mood.md` (the directions: a world, a colour story, the finishes) and
`guides/shapes.md` (the big shapes).

Three truly different ideas on the car, rough on purpose: flat colour in each one's base finish,
the big shapes only, no details. Each a different reading of the brief, with its own mood: the
world it draws from, its colour story and its finish. The mood lives here, on the car, not on
boards beside it (the user, 2026-09-28, when the steps went from eleven to three). Always the
user's decision.

1. `tool.sheet on <car> concepts`. Name three readings that truly differ (the mood guide: in at
   least two of the colour story, the finish, the graphic language and the world), each a title
   and a few lines: what the car is in that reading, the world it draws from, its colour story as
   hex with roles and shares, its base finish, and where its big shapes go. Then `tool.sheet option
   <car> concepts "<Title>"` for each: it makes `skins/<car>_<Title>/`, empty while the car has no
   design.
2. `tool.skin round "<the idea in a few words>" <car>_<A> <car>_<B> <car>_<C>` before painting
   them, so a Lab that's already open shows each take as it's painted (recorded after, it showed
   only after a reload, and the user couldn't find concept B, 2026-09-28).
3. **The three concept designers** (`.claude/agents/concept-designer.md`), launched at once in the
   background: the Agent tool, `subagent_type: concept-designer`, three calls in one message. Give
   each the car, its option's skin name, the brief's path, its own reading (with its colours and
   finish), the other two readings to stay clear of, and the computer (the Mac or the PC). Each
   writes its `design.py`, paints it (paints take turns on a computer: `tool.skin` queues them),
   looks, fixes and reports. A session begun before the agent existed doesn't list it: give a
   general-purpose agent the file's text below its header as its role.
4. When all three are back, look at each yourself: the six views, the close looks, the chase
   cameras. You hold the round together: each on the brief, each clearly its own, none rougher
   than the others by accident. Fix in its design what they left, and paint again. Take each one's
   snapshot (its gallery picture, which the wizard's card shows), then the picture (`--picture`,
   views front, left and top, the driving camera's close row for each) and `tool.sheet ask <car>
   concepts`.
5. Reply: a line per concept, the one you'd pick and why, that the Lab shows them side by side and
   each on the car, then in bold: which one, or what to take from each?
6. One: `tool.sheet pick <car> concepts <letter> "<the idea in a few words>"`: its design becomes
   the car's and the others go with their round; then `show <car>` to paint it under its own name,
   and its snapshot. A mix the user spelled out ("I like B the most. I do like the grass from C
   though"): write it as a new option from the picked parts, check it as any concept, pick it, and
   show the car. Notes left on concepts the pick deleted still get marked done (`tool.notes done`
   takes them).

## 3. The car

Its guides, as the work reaches their field: `guides/shapes.md` and `guides/colours.md`, then
`guides/wheels.md`, `guides/details.md` and `guides/lettering.md`.

The picked concept made into a finished car, on the car itself, with the user's notes throughout
(the user, 2026-09-28: "after concepts, I would just have the 3d car and you just make changes,
with the comments pop up windows throught"). Nothing is a separate stop: the user watches the car
on the stand, clicks where they want a change and writes it, and you change it and show it. Still
every detail from start to finish (the user's "not the typical amateur skins"), so you carry the
work on yourself between their notes, field by field.

1. `tool.sheet on <car> car`, then `ask <car> car` once the car is shown: the wizard shows it on
   the stand with "Happy with the car?". Start `tool.notes wait` in the background and end the turn,
   as after any ask: their notes on the car come like any note, their "Happy with it" as an answer.
   While you work, `on` again ("Claude on it"); `ask` again when you show the next state.
2. **The work, in this order unless their notes say otherwise:**
   - **The shapes** (the shapes guide): the concept's rough edges fixed: nothing clipped, sunk, or
     running into the part under it; nothing the brief rules out (TSC_Ladybird's white marks read as
     eyes; its grass made a slab under the nose); how it reads from far away and from the game's
     cameras (`--cams`; on the Mac `node docker/snap.mjs <car> --cams`): a good car reads in half a
     second. The player sees their car from behind: say in a line what reads from there.
   - **The finishes** (the colours guide): a `FINISH` dict at the top of the design, part by part
     (gloss, satin, matte, metal, carbon), the contrast between them and the exact colours, by day
     and at night. A matte graphic on a gloss shell reads as drawn on; shine shows every flaw, so
     look at the glossiest closest.
   - **The wheels** (the wheels guide): the covers, the tyre accent and tread, the wheels' lights.
     The user settles the wheels car by car: offer them a round (below).
   - **The details** (the details guide): the inner car, the lights and their colours, the glass,
     looked at from behind first and at night.
   - **The lettering** (the lettering guide), when the car wants words, numbers or badges: the
     places the shapes leave free, the typefaces. Say what reads only up close.
   Show each field's result on the car (`show <car>`, its snapshot, `ask <car> car`) with a picture
   and a few lines, and say which field comes next. Their notes on the car are the changes: act on
   them first, mark each done.
3. **A real choice** (the wheels, two places a graphic could go, gloss or matte when the brief and
   the concept disagree): an option each (`tool.sheet option <car> car "<Title>"` copies the car's
   design to change; keep everything else the same, so the choice is that alone), the round recorded
   before painting (`tool.skin round`), each painted, checked and snapped, the picture, then `ask`:
   the stand shows the round's switch, and a Pick for the take on show. Reply with a line per
   option, the one you'd pick and why. Their pick: `tool.sheet pick <car> car <letter> "<...>"` (the
   step stays open: the pick joins its history), then `show <car>` and carry on. A pick with a change ("a but the grass make it a
   silky grass finish"): change that option, check it, then pick it.
4. What only the game can judge (a colour meant to blend with the map) goes to the check: note it in
   `notes.md`. Commit and push after each field and each pick.
5. **When they're happy** ("Happy with it", or in the chat): the check, then the release, below.
   The step is decided at the end of the release.

### The check

**The critic.** An agent that didn't design the car (`.claude/agents/critic.md`), given only the
brief and the car's pictures, never the design, the sheet, `notes.md` or your reasons. No decision
for the user: they hear what was found and fixed.

1. `tool.sheet on <car> car`. Take the car's four sheets as it is now: the views, the close
   looks, the review angles (straight on, low behind, underneath, the right-hand flanks) and the
   game's cameras: `tool.snap <car>`, then `--close`, `--review`, `--cams` (on the Mac `node
   docker/snap.mjs <car>` with the same flags). Cut them into single pictures: `tool.critic
   pictures <car>` (on the Mac `docker compose exec app python -m tool.critic pictures <car>
   --sheets /app/.snap --out /app/.snap/critic/<car>/<round>`, the round 1, 2...).
2. Call the critic (the Agent tool, `subagent_type: critic`) with the brief's path and every
   picture in the folder by name, nothing else. A session begun before the critic existed doesn't
   list it: give a general-purpose agent the file's text below its header as its role, the Read
   tool only, on the files named, and the critic's model. Save the reply in the scratchpad, then
   `tool.critic keep <car> <file> --critic <model> --pictures <folder>`.
3. Look at every finding in its picture yourself. A real `fix` or `improve`: change its part of the
   design, then `tool.critic mark <car> <n> fixed "<what changed>"`. A misreading (a reflection,
   the car's own shape) or something the user chose against the brief: `mark <n> left "<why>"`,
   said to the user, not changed.
4. Paint, take the pictures again into the next round's folder, and give the critic its findings
   with their numbers and the new pictures (its instructions' re-check); keep that round too.
   Stop when it finds nothing new to fix, three rounds at most.
5. What the critic can't see is yours: parts left in clay (`tool.skin paint <car>` names them), and
   the size, a trial build (`paintbox.build_zip(<car>, icon)`, about 90 s in the Mac's container)
   against `ZIP_BUDGET`.
6. Tell the user in a few lines: what the critic found, what was fixed, what was left and why.

The critic's test car, TSC_CriticTest, has seven faults of known kinds (its design's docstring):
after a change to the critic's instructions, run it there and compare with the score in
`CHECKLIST.md` (W2).

**The road test.** The car in the game, on the Windows PC: `tool.skin install <car>`, then the
user drives it (a map that suits the idea, day and night, brakes, turbo) and takes F12
screenshots; look only at those taken after the install. A change is made on the car as any note is, and checked again where it matters. If the
user waives the drive ("Let's assume it works"), note in `notes.md` what only the game could have
shown.

**The release,** on their yes: the car final, in the game (installed at the road test, or now on
the PC), on the page online (`tool.publish`, on the PC: it shows the skins in the game), and in its
design book.

- **The design book** is a private page on claude.ai (an artifact) the user can share: the car's
  story from the brief to the finished car, one chapter per step, with the user's own words at each
  decision and the options beside the pick. The studio's look (the Lab's: Teko, slanted keys, one
  yellow-green accent on a dark ground). TSC_Ladybird's is the model: its page is
  `skins/TSC_Ladybird/book.html`, its link in its `notes.md`; start the next from it.
- Its pictures come from the rounds' picture sheets in `.snap/` (a row is a 70 px title bar and
  960x720 tiles; the tiles' working labels are cut off the top) and the final views, close looks
  and cameras, as JPEGs about 960 wide (about 2.5 MB for 27). Credit the car model's author.
- Then `tool.sheet decide <car> car "<the car in a few words: found and fixed, in the game,
  released>"` once it's in the game and online, a line in `notes.md`, commit and push.
