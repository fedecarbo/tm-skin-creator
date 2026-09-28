# A new car

A car built from the idea to the last detail, the way a real car studio builds one (the user,
2026-09-28: "not the typical amateur skins ... every single detail from start to finish"), and the
way the user works: the car in front of them, their notes on it, and options to pick whenever
there's more than one way to go (the user, 2026-09-28: "Two main things I like. It's having the car
and me being able to iterate. and I also like a place where you can provide options before
building"). Read this when the user wants a new car, not for a change to one; `SKILL.md` still
applies for everything it says about designing, checking, showing, the record and installing. The
history (the studio's steps, the wizard, and why they went): "The design studio" in `CHECKLIST.md`.

## How it runs

- **No steps.** The user sees the car in the Lab and the list of options beside it: a short talk,
  the first concepts as a set, then the car, finished field by field from their notes, then the
  check and the release. They stop only for a real choice: a set of options (`SKILL.md`, "Sets of
  options"), picked in the Lab or in the chat. When there's one sensible answer, do it and show it;
  they can still say otherwise. Technical choices stay yours.
- **A new car starts fresh:** it borrows no looks from earlier cars, and no design of theirs, unless
  the user names one. What the game has taught about the car itself (`SKILL.md`, "What works on
  this car", and "Things we learned") still counts.
- **Each field has its expert's know-how:** short guides in `guides/` beside this file, read when
  the work reaches their field and at no other time: `mood.md` and `shapes.md` for the concepts;
  on the car, `shapes.md` and `colours.md` for the shapes and finishes, `wheels.md`, `details.md`
  and `lettering.md` for theirs. Each says what good looks like in that field, what the car and the
  tool allow there, what to check. When a field's work is done, add what the car taught to its
  guide's "Learned" (dated, the car's name, a line or two), so the experts grow with every car. The
  critic (4) has its own instructions.
- **Everything is checked against the brief's card.** An option that drifts from it isn't shown.
- **The Lab:** open it on the car once it has a folder (http://localhost:8765/lab.html?skin=<car>;
  on the Mac `open` it) and say once that they can pick there, write about an option, or click the
  car to leave a note. After each set is opened, wait for them (`tool.notes wait`, `SKILL.md`).
- `notes.md` as for any skin: the user's words verbatim, the date and the model first, then a line
  per event (`Brief approved <date>: …`, `Picked <date>, set <n>: …`, `Change <n> (user): …`).
- Commit and push after each pick and each field, so the other computer has it.

## 1. The talk and the card

What the car is, agreed before anything is painted. A conversation, not a form (the user,
2026-09-28: "I would prefer if it's just open ended? Similar to how other ai tools does that they
like "what do you want to...", and then it reasons about it, maybe help shape the direction. But
obviously I don't want a complete form to fill out"). A clear idea with its details needs a round
at most; still write the card.

1. If they haven't said yet, ask one open question: **what car do you want to build?** A word, a
   feeling, a scene: anything goes.
2. Give the car a working name (`TSC_<Idea>`, CamelCase, a name no skin has) and start its
   `notes.md`. When the talk settles on something more telling, rename the folder before anything
   is painted (the first such car began as TSC_Grass and became TSC_Ladybird).
3. Think about their words and answer as a designer would, in a few sentences of plain talk: the
   character you hear in the idea, what it could draw from (specific worlds: "a 1990s Le Mans
   prototype at night", "a Braun radio", never "motorsport"), the traps it could fall into ("a
   toy", "a gamer RGB car"), and where you'd take it. That's how you help shape it.
4. If there's a real fork in the direction, name it and ask the one question that settles it, in
   a sentence ("it could be quiet and menacing, or loud and proud: which is closer?"). Never a
   list of questions, never choices to tick. If their words leave nothing open, go straight to
   the card. A round or two at most.
5. Write the card, `skins/<car>/brief.md`: your reading, shaped by what they said, in this shape
   (the critic reads it):

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
   card and it's shown again. On a yes: `Brief approved` in `notes.md`, commit and push.

## 2. The first concepts

Their guides: `guides/mood.md` (the directions: a world, a colour story, the finishes) and
`guides/shapes.md` (the big shapes).

Three truly different ideas on the car, rough on purpose: flat colour in each one's base finish,
the big shapes only, no details. Each a different reading of the card, with its own mood: the
world it draws from, its colour story and its finish (the mood lives on the car, not on boards).

1. Name three readings that truly differ (the mood guide: in at least two of the colour story, the
   finish, the graphic language and the world), each a title and a few lines: what the car is in
   that reading, the world it draws from, its colour story as hex with roles and shares, its base
   finish, and where its big shapes go.
2. `tool.sets new <car> "3 concepts" --words "<their words>"`, then `tool.sets option <car> <n>
   "<Title>"` for each: it makes `skins/<car>_<Title>/`, empty while the car has no design. Do it
   before painting, so an open Lab lists each concept as it's painted.
3. **The three concept designers** (`.claude/agents/concept-designer.md`), launched at once in the
   background: the Agent tool, `subagent_type: concept-designer`, three calls in one message. Give
   each the car, its option's skin name, the card's path, its own reading (with its colours and
   finish), the other two readings to stay clear of, and the computer (the Mac or the PC). Each
   writes its `design.py`, paints it (paints take turns on a computer: `tool.skin` queues them),
   looks, fixes and reports. A session begun before the agent existed doesn't list it: give a
   general-purpose agent the file's text below its header as its role.
4. When all three are back, look at each yourself: the six views, the close looks, the chase
   cameras. You hold the set together: each on the card, each clearly its own, none rougher than
   the others by accident. Fix in its design what they left, and paint again. Take each one's
   snapshot (its gallery picture, which the Lab's list shows), then the picture (`--picture`, views
   front, left and top, the driving camera's close row for each), `tool.sets open <car> <n>`, and
   wait for them.
5. Reply: a line per concept, the one you'd pick and why, that the Lab lists them and puts each on
   the car, then in bold: which one, or what to take from each?
6. Their pick: `tool.sets pick <car> <n> <letter> "<the idea in a few words>"`: its design becomes
   the car's, the others go (their pictures kept); then `show <car>` to paint it under its own
   name, and its snapshot. A mix they spelled out ("I like B the most. I do like the grass from C
   though"): write it into the option they like most, check it as any concept, and pick it. Notes
   left on the concepts still get marked done (`tool.notes done` takes a deleted option's name).

## 3. The car

Its guides, as the work reaches their field: `guides/shapes.md` and `guides/colours.md`, then
`guides/wheels.md`, `guides/details.md` and `guides/lettering.md`.

The picked concept made into a finished car, on the car itself, with the user's notes throughout
(the user, 2026-09-28: "after concepts, I would just have the 3d car and you just make changes,
with the comments pop up windows throught"). The user watches the car in the Lab, clicks where they
want a change and writes it, and you change it and show it. Still every detail from start to finish,
so you carry the work on yourself between their notes, field by field.

1. **The work, in this order unless their notes say otherwise:**
   - **The shapes** (the shapes guide): the concept's rough edges fixed: nothing clipped, sunk, or
     running into the part under it; nothing the card rules out (TSC_Ladybird's white marks read as
     eyes; its grass made a slab under the nose); how it reads from far away and from the game's
     cameras (`--cams`; on the Mac `node docker/snap.mjs <car> --cams`): a good car reads in half a
     second. The player sees their car from behind: say in a line what reads from there.
   - **The finishes** (the colours guide): a `FINISH` dict at the top of the design, part by part
     (gloss, satin, matte, metal, carbon), the contrast between them and the exact colours, by day
     and at night. A matte graphic on a gloss shell reads as drawn on; shine shows every flaw, so
     look at the glossiest closest.
   - **The wheels** (the wheels guide): the covers, the tyre accent and tread, the wheels' lights.
     The user settles the wheels car by car: offer them a set.
   - **The details** (the details guide): the inner car, the lights and their colours, the glass,
     looked at from behind first and at night.
   - **The lettering** (the lettering guide), when the car wants words, numbers or badges: the
     places the shapes leave free, the typefaces. Say what reads only up close.
   Show each field's result on the car (`show <car>`, its snapshot) with a picture and a few lines,
   and say which field comes next. Their notes on the car are the changes: act on them first, mark
   each done.
2. **A real choice** (the wheels, two places a graphic could go, gloss or matte when the card and
   the concept disagree): a set (`SKILL.md`, "Sets of options"), everything else the same across
   its options so the choice is that alone; the picture; reply with a line per option and the one
   you'd pick and why. A pick with a change ("a but the grass make it a silky grass finish"):
   change that option, check it, then pick it.
3. What only the game can judge (a colour meant to blend with the map) goes to the check: note it in
   `notes.md`.
4. **When they're happy** (in the chat, or a note saying so): the check, then the release.

## 4. The check

**The critic.** An agent that didn't design the car (`.claude/agents/critic.md`), given only the
brief and the car's pictures, never the design, the sets, `notes.md` or your reasons. No decision
for the user: they hear what was found and fixed.

1. Take the car's four sheets as it is now: the views, the close
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
screenshots; look only at those taken after the install. A change is made on the car as any note
is, and checked again where it matters. If the user waives the drive ("Let's assume it works"),
note in `notes.md` what only the game could have shown.

## 5. The release

On their yes: the car final, in the game (installed at the road test, or now on the PC), on the
page online (`tool.publish`, on the PC: it shows the skins in the game), and in its design book.

- **The design book** is a private page on claude.ai (an artifact) the user can share: the car's
  story from the brief to the finished car, a chapter per set and per field, with the user's own
  words at each pick and the options beside it (its earlier picks keep their pictures:
  `skins/<car>/sets/`). The Lab's look (Teko, slanted keys, one yellow-green accent on a dark
  ground). TSC_Ladybird's is the model: its page is
  `skins/TSC_Ladybird/book.html`, its link in its `notes.md`; start the next from it.
- Its pictures come from the rounds' picture sheets in `.snap/` (a row is a 70 px title bar and
  960x720 tiles; the tiles' working labels are cut off the top) and the final views, close looks
  and cameras, as JPEGs about 960 wide (about 2.5 MB for 27). Credit the car model's author.
- Then a line in `notes.md` (`Released <date>: …`), commit and push.
