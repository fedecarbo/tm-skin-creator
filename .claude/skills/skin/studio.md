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

## 4. Shapes

The picked concept's big shapes made right: where each graphic sits, how it meets the car's folds,
edges and holes, and how the car reads from far away and from the game's cameras. A good car reads
in half a second. The user decides only when there's a real alternative.

1. `tool.sheet on <car> shapes`. Act on the user's notes on the car in its design, and fix what the
   concept left rough: nothing clipped, sunk, or running into the part under it; nothing the brief
   rules out (TSC_Ladybird's white marks read as eyes; its grass made a slab under the nose).
2. Look at it as the game shows it: the six views and the close looks as always, and the game's
   cameras by day and at night (`--cams`; on the Mac `node docker/snap.mjs <car> --cams`). The
   player sees their car from behind: say in a line what reads from there and what only others see.
3. One sensible answer: `tool.sheet decide <car> shapes "<the shapes in a few words>"`, show it in a
   picture and move on. A real alternative (the user's words against the brief, two places a
   graphic could go): an option each (`tool.sheet option <car> shapes "<Title>"` copies the car's
   design to change), the round recorded before painting, each painted and checked, the picture
   (front, left and top, with a close row where they differ), then `tool.sheet ask <car> shapes`.
   Reply with a line per option, the one you'd pick and why, and in bold: which one?
4. The pick as for concepts: `tool.sheet pick <car> shapes <letter> "<...>"`, then `show <car>`.
   `Picked` in `notes.md`, commit and push.

## 5. Colours and materials

The finishes, part by part (gloss, satin, matte, metal, carbon), the contrast between them, the
exact colours, by day and at night. Usually the user's decision: the boards and the brief tend to
disagree about shine.

1. `tool.sheet on <car> colours`. Read the directions off the brief and the mood boards: each
   board's finishes are one, a finish the brief names is always one (TSC_Ladybird's "glossy"), and
   the car as it is when it's a real candidate. Contrast counts: a matte graphic on a gloss shell
   reads as drawn on.
2. An option each (`tool.sheet option <car> colours "<Title>"`), with the finishes in a `FINISH`
   dict at the top of its design, part by part. Keep the colours the same across them, so the
   choice is the finish alone, unless the colour is the question. Record the round before painting.
3. Paint and check each; shine shows every flaw, so look at the glossiest closest. The picture:
   front, rear (the highlights run over the deck) and night, with close rows 3 and 6. Then `ask`,
   reply with a line per option and the one you'd pick, and in bold: which one?
4. The pick as for concepts, then `show <car>`. A pick with a change ("a but the grass make it a
   silky grass finish"): change that option, check it, then pick it. What only the game can judge (a colour meant to
   blend with the map) goes to the Road test: note it in `notes.md`.

## 6. Wheels

The covers, the rims, the tyres' marking and tread, and the wheels' own lights, as one piece: the
user settles the wheels car by car. Always the user's decision.

1. `tool.sheet on <car> wheels`. Two or three readings of the car's idea on the wheels: the covers
   are the big area (black, a body colour), the tyres carry an accent from the car's colours (the
   library, `s.tyre_marks`) and a tread that suits it. The stock wheel rings glow cyan day and
   night: recolour them to fit (`s.relight("wheel ring", colour, keep_level=True)`).
2. An option each, with its own "Wheels" step in place of the wheels "for now". Record the round
   before painting. On the Mac, markings with words don't paint (`IMPROVEMENTS.md`): pick ones
   without there.
3. Check each, close looks 8 (the front wheel) and 9 (the driving camera: the rear tyres are what
   the player sees most). The picture: front, left and night, close rows 8 and 9. Then `ask`, and
   the pick as for concepts.

## 7. Details

What separates a finished car from an amateur skin: the inner car (the frames, the suspension, the
floor and front wing, the cockpit), the lights and their colours, the glass. Usually one sensible
answer: do it, show it, `tool.sheet decide <car> details "<...>"`; options only for a real choice.

- Look from behind first (`--cams`): the tail, the speed numbers and the rear lights are what the
  driver sees all race, so the lights carry the car's accent (`s.relight("speed numbers" | "rear
  lights", colour)`, a brighter version of the colour, as lights glow).
- The inner car starts in one colour (`s.paint("inner", ...)`); then carbon underneath (the floor
  and the front wing wear one paint), and the frames round the inlets and the speed display in the
  body's trim finish. `show` names the parts a paint also lands on: check they're dark or alike.
- The glass: a tint also dims the lights behind the lenses; leave it clear unless the idea wants it.

## 8. Lettering

Words, numbers and badges, their typeface and where they go. The user's decision when there's more
than one direction (the mood boards' lettering, and none).

1. `tool.sheet on <car> lettering`. The places left free by the shapes (`SPOTS` in the paint box;
   never the number and name panels), and the typefaces in `tool/fonts.py` (a new Google font at
   google/fonts' latest commit, its sha256 recorded). A graphic can carry the lettering: a spot as a
   number's roundel (TSC_Ladybird).
2. An option each (and "No Lettering" when none is a real answer), the round before painting. Check
   each where it meets the car's own pieces (the flank's fin), from both sides (words read right on
   each), and from the front: a number the right way up only from behind reads as another letter.
3. The picture: front, left and right, close rows where the lettering sits. Say what reads only up
   close. Then `ask`, and the pick as for concepts.

## 9. Review

The whole car checked with fresh eyes, against the brief and the studio's quality list, by the
critic: an agent that didn't design the car (`.claude/agents/critic.md`), given only the brief and
the car's pictures, never the design, the sheet, `notes.md` or your reasons. No decision for the
user: they hear what was found and fixed.

1. `tool.sheet on <car> review`. Take the car's four sheets as it is now: the views, the close
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
3. Look at every finding in its picture yourself. A real `fix` or `improve`: change its step of the
   design, then `tool.critic mark <car> <n> fixed "<what changed>"`. A misreading (a reflection,
   the car's own shape) or something the user chose against the brief: `mark <n> left "<why>"`,
   said to the user, not changed.
4. Paint, take the pictures again into the next round's folder, and give the critic its findings
   with their numbers and the new pictures (its instructions' re-check); keep that round too.
   Stop when it finds nothing new to fix, three rounds at most.
5. What the critic can't see is yours: parts left in clay (`tool.skin paint <car>` names them), and
   the size, a trial build (`paintbox.build_zip(<car>, icon)`, about 90 s in the Mac's container)
   against `ZIP_BUDGET`.
6. `tool.sheet decide <car> review "<found and fixed, a few words>"`, a line in `notes.md` with
   what's left for the road test, commit and push. Tell the user in a few lines: what the critic
   found, what was fixed, what was left and why.

The critic's test car, TSC_CriticTest, has seven faults of known kinds (its design's docstring):
after a change to the critic's instructions, run it there and compare with the score in
`CHECKLIST.md` (W2).

## 10. Road test

The car in the game, on the Windows PC: `tool.skin install <car>`, then the user drives it (a map
that suits the idea, day and night, brakes, turbo) and takes F12 screenshots; look only at those
taken after the install. Always the user's decision: a yes decides it, a change reopens the step it
belongs to. If the user waives it ("Let's assume it works"), `tool.sheet skip <car> road "<their
words>"` and note in `notes.md` what only the game could have shown.

## 11. Release

The car final: in the game (installed at the road test, or now on the PC), on the page online
(`tool.publish`, on the PC: it shows the skins in the game), and in its design book.

- **The design book** is a private page on claude.ai (an artifact) the user can share: the car's
  story from the brief to the finished car, one chapter per step, with the user's own words at each
  decision and the options beside the pick. The studio's look (the Lab's: Teko, slanted keys, one
  yellow-green accent on a dark ground). TSC_Ladybird's is the model: its page is
  `skins/TSC_Ladybird/book.html`, its link in its `notes.md`; start the next from it.
- Its pictures come from the rounds' picture sheets in `.snap/` (a row is a 70 px title bar and
  960x720 tiles; the tiles' working labels are cut off the top) and the final views, close looks
  and cameras, as JPEGs about 960 wide (about 2.5 MB for 27). Credit the car model's author.
- Then `tool.sheet decide <car> release "<...>"` once it's in the game and online, a line in
  `notes.md`, commit and push.
