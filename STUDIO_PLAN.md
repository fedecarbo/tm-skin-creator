# The design studio: a plan

A way of building cars the way a real car studio does: from the car's idea to the last detail,
with a stage for each kind of work, an expert for each stage, and the Lab showing where the car
is. Written 2026-09-28 from a chat with the user. Nothing here is built yet.

The user's words that started it (2026-09-28): "What's important is to actually have this as an
incredible workflow that builds cars (not the typical amateur skins) but actually work on every
single detail from start to finish."

The user's answers:

- **Three ways in** (2026-09-28: "both, and also make changes to an already existing car"):
  a quick way, the full studio, and reworking a car that already exists.
- **When the user decides** (2026-09-28: "any stage that needs a choosing of direction"): the user
  signs off wherever there is more than one real direction to go. Claude handles the rest and
  shows it, and the user can still leave notes on anything.

This plan is an improvement to the tool, not a new checkpoint (CLAUDE.md). Once the user agrees
to it, it goes on `IMPROVEMENTS.md` under "Under way", and its working notes go under
"Improvements after the build" in `CHECKLIST.md`. It takes in the Lab's remaining steps (9.3 to
9.6): see "How this fits with what's there".

---

## The three ways in

| Way | When | What happens |
|---|---|---|
| **Quick** | A clear, small idea ("make the wheels gold", "something with flames") | Same as today: words, pictures, changes, yes, in the game. Minutes. Can move into the Studio at any point, keeping the car. |
| **Studio** | A new car the user wants done properly | All the stages below, from the brief to the release. About an hour or two, spread over a few decisions. |
| **Rework** | An existing car that should be taken further, or changed in a big way | Starts with a teardown of the car as it is (below), then enters the Studio at the stage the change belongs to. Everything before that stage stays settled. |

Claude suggests a way from the user's words and says which in one line ("I'll take this through
the studio"). The user can always ask for the other.

---

## The stages

Each stage has a job, an expert, what the user sees, and whether it is usually a decision
point. The rule for decisions: **a stage stops for the user whenever there is more than one real
direction.** When there is only one sensible answer, Claude does the stage, shows it and moves
on. The user can still leave a note on it, which reopens it.

A stage that is decided stays decided. Going back to a stage reopens that stage and the ones
after it, never the ones before.

### 1. The brief

- **The job:** agree what this car is before anything is painted. Its character in a few words
  ("a night-time endurance racer, calm but dangerous"), 2 or 3 reference ideas (a real race car,
  a product, a place, a film), what it must **not** look like, and anything fixed (a colour, a
  word, a number).
- **The expert:** the design director (Claude, the voice the user talks to).
- **What the user sees:** a one-page brief card on the Lab, in plain words.
- **Decision:** always. The user approves the card or changes it. Every later stage is checked
  against it.

### 2. Mood

- **The job:** turn the brief into a look before it touches the car: 2 or 3 mood boards, each a
  wall of pictures, a colour story (the main colour, the support colours, one accent), and the
  kind of finish (raw carbon and matte, or deep gloss and chrome).
- **The expert:** the mood and research designer.
- **What the user sees:** the boards side by side, each with a name and its colours as chips.
- **Decision:** always, for a new car: pick a board, or say what to take from each.

### 3. Concepts

- **The job:** 3 truly different ideas on the car, rough on purpose: flat blocks of colour, no
  detail, no finishes yet. Different readings of the brief, not three shades of one.
- **The experts:** three concept designers, each working on one idea at the same time.
- **What the user sees:** the three cars side by side on the stand (A, B, C), from the front,
  the side and the game's camera.
- **Decision:** always. Pick one, or mix ("A's shapes with C's colours"). Once the user picks,
  the other ideas are deleted (the user's rule, 2026-09-28); git's history keeps them.

### 4. Shapes

- **The job:** refine the chosen idea's big shapes: where the stripes, blocks and graphics sit,
  how they follow the car's folds and edges, and how they read from far away, at speed, from the
  game's cameras and in a small picture. A good car reads in half a second.
- **The expert:** the livery designer.
- **What the user sees:** the car from the game's cameras, a small "from far away" picture, and
  the car from the side.
- **Decision:** only if there are real alternatives (the stripe over the top or along the sides).

### 5. Colours and materials

- **The job:** the finishes. Which parts are matte, satin, gloss, metal or carbon; the contrast
  between them; the exact colours; how it all looks by day and at night. This is the materials
  library's stage.
- **The expert:** the colour and materials designer (what car makers call CMF: colour, material,
  finish).
- **What the user sees:** the car with a day and night switch, and a board of the car's finishes
  as swatches, each one clickable to copy for Claude (as in the Materials room).
- **Decision:** usually, when there's a real choice (gloss or matte, warm or cold metal).

### 6. Details

- **The job:** everything that separates a finished car from an amateur skin, station by
  station:
  - **Details:** the inner car, the suspension, the floor, the fasteners, the lights and their
    colours, the glows at night;
  - **Wheels and tyres:** covers, rims, the tyre marking and tread, as one piece of work (the user,
    2026-09-27: "the wheels in general is a full workflow as I build cars");
  - **Lettering and badges:** numbers, words, logos, the typeface, and where they can go;
  - **Glass:** its tint.
- **The experts:** the detail designer (inner car and mechanics), the wheels designer, the
  typography and badges designer.
- **What the user sees:** the stations under the car (Body, Details, Tyres, Glass), each with its
  tries, and close-ups of each area.
- **Decision:** the wheels, always (the user settles them car by car). The rest only when there
  are real alternatives.

### 7. Review

- **The job:** a critic who did not design the car checks it, with fresh eyes, against the brief
  and a quality list:
  - does it still say what the brief says?
  - does it read from the game's cameras, at speed, by day and at night?
  - anything cut, stretched, soft or crooked where graphics meet a fold, join or edge?
  - paint left over from an earlier idea, or parts left as clay by accident?
  - words that read backwards on one side?
  - the game's rules (the number panel free, the file size).
  Claude fixes what the critic finds, and the critic checks again.
- **The expert:** the critic.
- **What the user sees:** the critic's findings as tags on the car, each one marked fixed with a
  before and after.
- **Decision:** none. The user just sees what was found and fixed.

### 8. Road test

- **The job:** the car in the game. The user drives it by day and at night, uses brakes and turbo,
  and takes a few F12 screenshots.
- **What the user sees:** their screenshots in the Lab, with notes on them.
- **Decision:** always. Yes, or what to change. A change reopens the stage it belongs to.

### 9. Release

- **The job:** the car is final: in the game, on the page online, and in its design book: a page
  telling the car's story, from the brief and the mood board, through the concept that was picked,
  to the finished car.
- **What the user sees:** the design book, which they can share with friends.
- **Decision:** none.

### Rework: the teardown

For an existing car, before anything changes:

- the critic goes over the car as it is, with the quality list above;
- Claude writes the car's brief as it stands now (from its record and the user's words back then);
- the user sees both, and says what stays and what's open ("keep the colours, redo the
  lettering");
- the car enters the Studio at that stage. "Redo the lettering" starts at Details; "make it feel
  more aggressive" starts at the brief.

---

## The experts

**Stages and an independent critic matter more than how many agents there are.** A crowd of
agents talking to each other would be slower, more expensive and contradictory, against the
user's "small and simple". So:

- **The design director** is the main Claude session. It is the only one that talks to the user,
  keeps the brief, and holds the car together.
- **The specialists** (mood, livery, colours and materials, details, wheels, typography) are
  know-how, not separate chats: one short guide per stage that the director loads when the car
  reaches that stage. Each guide says what good looks like in that field, what to check, and the
  tool's abilities and limits for it. This is where "expert in each field" really lives, and it
  grows with every car (what the game and the user teach).
- **The three concept designers** are real parallel agents, each given the brief and the mood
  board and asked for one idea. This makes the concepts better and costs no extra waiting.
- **The critic** is a real separate agent, given the car's pictures, the brief and the quality
  list, never the design itself or Claude's reasons. Being independent is the whole point: today
  the designer checks its own work.

---

## What the user sees in the Lab

**Decided (the user, 2026-09-28: "Lets just go with that, and see how it goes"): the wizard,
below.** The three first layouts (https://claude.ai/artifact/4RxUASJaYTfphRZbk1gFtG: a line of
stages, the car's sheet, a decision drawer) led to it. Quick cars keep the stand as it is today.

### The wizard (the user, 2026-09-28)

After the three layouts, the user liked the concepts screen ("feels like a wizard"), and asked to
imagine it as a Trackmania skin builder that other people could use one day, with each step
showing its options in its own format, not the same pictures every time. And: "what would happen
if I want to change an existing, or go back and make a change (what's the non linear process)".

Claude's answer, drawn as screens (https://claude.ai/artifact/JHwbvVDKNTCiHTGepPQB2F, a new car
"Press Run": brief, mood, concepts, colours and materials, wheels, and going back to change the
wrap):

- **A decision takes over the page,** as in the concepts layout: a question, its options, "Or tell
  Claude in your own words", Back and Next.
- **The build sheet on the left** is the wizard's map and the way back: one line per step with
  what was decided, and a small picture of the car so far (once there is a car).
- **Each step shows the smallest thing that settles its question, then the whole car to
  confirm:** the brief as questions and word choices; mood as boards; concepts as three whole
  cars; colours and materials as one car with a day and night split and the finishes as swatches;
  wheels as a row of wheels close up, then the pick on the car by day and at night.
- **Going back:** click a step on the sheet. Later steps are kept, not wiped: Claude carries the
  later picks onto the change, marks only the steps it affects as "needs a look" (a new wrap
  colour touches the lights and the lettering, not the tread), and shows the whole car before and
  after. A change is tried next to the current car, and the one not kept is deleted.
- **An existing car** opens with its sheet filled in from its history, every step decided, and
  goes straight to the step the change belongs to.
- **The steps:** Brief, Mood, Concepts, Shapes, Colours and materials, Wheels, Details, Lettering,
  Review, Road test, then Released. Wheels and Lettering are steps of their own (in the stages
  above they sit inside Details).
- **Notes on the car still work at any time,** on the stand as today: a note lands in the step it
  belongs to (a note on a wheel reopens Wheels).
- **Other people using it one day** would need hosting and would cost money per user: a
  separate decision for later. The wizard works either way.

## How this fits with what's there

Most of the machinery exists already. The studio mostly adds order, the brief, the experts' know-how
and the critic.

| Stage | What the tool has | What's new |
|---|---|---|
| Brief | the user's words in each skin's record | the brief card, kept with the skin |
| Mood | the picture maker, the textures library, the finishes library | mood boards and colour stories |
| Concepts | rounds of A, B, C in the Lab, the switch between them | three parallel designers; the three cars side by side on the stand (the Lab's step 9.4, options on the car) |
| Shapes | the paint box, the zones, the spots, the game's cameras | a "from far away" check |
| Colours and materials | the finishes library and its codes, day and night | the car's finishes board |
| Details | stations and tries, parts, tyre markings, glows, lights, lettering | the details guides |
| Review | Claude's own check before showing, the close looks | the independent critic; its findings as tags with before and after (the Lab's steps 9.3 and 9.5) |
| Road test | screenshots read after an install | screenshots in the Lab with notes (the Lab's step 9.6) |
| Release | install, the page online | the design book |

The Lab's step 9.7 (repainting only the station that changed) is separate and still worth doing:
it makes every stage faster.

---

## Building it

In this order, each step built, checked, shown to the user, then ticked (as the Lab's steps are).
The user tries each one on a real car before the next. The Lab's steps 9.3 to 9.6 are folded in
here (answers with a before and after, options on the car, Claude's checks, the game's
screenshots); 9.7, repainting only the station that changed, stays as it is and helps every step.

### W1. The studio routine

- **What it's for:** Claude can take a car through the studio in the chat, before any screen
  exists: the steps, the decisions, going back, and the three ways in (Quick, Studio, Rework).
- **What you'll see:** say "studio" with an idea, and Claude asks the brief's questions, shows the
  mood boards, the three concepts, and so on, one decision at a time, with pictures.
- **Model:** Opus 5.5.
- **Notes for Claude:**
  - A Studio section in the `skin` skill, used only when the user asks for the studio or a
    rework. The quick way stays exactly as it is.
  - The brief kept per skin (`skins/<name>/brief.md`).
  - **The build sheet as data:** `skins/<name>/sheet.json` (the name is free: `studio.json` is the
    Lab's timeline), written only by the tool's commands (`tool.sheet` or `tool.skin`
    subcommands): each step's state (to do, Claude on it, waiting for you, decided, needs a look),
    its decision in a few words, the date, its options (skin names), and the pick. A pick deletes
    the other options' folders (the user's rule, 2026-09-28). The Lab's rule: the page shows only
    this, never a list of its own.
  - **Going back:** a step's change marks the later steps it affects as "needs a look" (Claude
    decides which, and says why in a few words); the others stay decided. Claude carries the later
    picks onto the change and shows the whole car before and after.
  - **Rework:** writes the sheet of an existing car from its `notes.md` and `design.py`, every step
    decided, then opens the step the change belongs to.
  - Mood boards: pictures from the picture maker (`tool.pictures`), the textures library and
    colour strips. Web pictures are references only, never on git or on the car.

### W2. The experts

- **What it's for:** better options at each step, and a second pair of eyes.
- **What you'll see:** concepts that differ more and arrive together, and a review step with a
  list of faults found and fixed, each with a before and after.
- **Model:** Opus 5.5 to write the guides; the critic tried on Opus 5.5 and Fable 5.1 on the same
  cars, keeping the one that finds more real faults.
- **Notes for Claude:**
  - One short guide per step beside the `skin` skill (what good looks like, what to check, the
    tool's abilities and limits there), loaded only at its step, seeded from "What works on this
    car" and "Things we learned", growing with every car.
  - Three concept designers as parallel subagents, each given the brief and the mood and asked
    for one reading. Check first whether three paints can run at once on the PC (Edge, the GPU,
    the work folder): if not, the designs are written in parallel and the paints queue.
  - The critic as a subagent given only the pictures (views, close looks, the game's cameras, day
    and night), the brief and its quality list, never the design or Claude's reasons.

### W3. The wizard in the Lab

- **What it's for:** the screens the user chose (https://claude.ai/artifact/JHwbvVDKNTCiHTGepPQB2F).
- **What you'll see:** a Studio car opens in the Lab on its wizard: the build sheet on the left,
  the step waiting for you taking over the page, its options in that step's own format, "Or tell
  Claude in your own words", Back and Next. A pick in the Lab reaches Claude with your next
  message, like a note. Clicking a decided step goes back to it.
- **Model:** Opus 5.5.
- **Notes for Claude:**
  - Built from the mockups' look: the Lab's own stylesheet (`viewer/lab.html`), the build sheet
    300 px wide, the step's question in Teko at 44 px. The mockups' source is in the
    session's scratchpad, not the repo: rebuild from the pictures and this description.
  - Real renders everywhere the mockups used stand-ins: the options come from the viewer's
    picture car (`picture()`), as the strip's pictures do, kept in the browser the same way.
  - A pick or a free-text answer goes through the notes channel (`tool/notes.py`, the hook), so
    Claude gets it with the next message; it carries the step and the option.
  - Each step's format: Brief, questions and word choices, and the brief as Claude reads it;
    Mood, three boards; Concepts, three whole cars that turn; Shapes, the game's camera beside a
    small "from far away" picture; Colours and materials, one car with a day and night split and
    the finishes as swatches (codes from `finishes.CATALOGUE`, copied like the Materials room);
    Wheels, four wheels close up and turning, then the pick on the car by day and at night;
    Details and Lettering, close-ups of their area; Review, the critic's findings with before and
    after; Road test, the user's F12 screenshots after an install, with notes on them (ask first).
  - Going back: a changed step says "changed", the steps it affects "needs a look", and the page
    shows the whole car before and after.
  - Keep the Lab fast: draw only when something changes, pictures kept in the browser, nothing
    new drawn while Claude paints. Mockups first for any screen that differs from the chosen ones.

### W4. The test: Studio against Quick

- **What it's for:** check the studio is worth it (the user, 2026-09-28: "I want to do a test for
  the quick and the studio one to see the difference if its worth it").
- **How it runs:**
  - One idea of the user's, the same first message word for word, in two sessions: quick first,
    then studio, so the studio's brief and boards don't shape the user's taste before the quick
    car. Each session is told only its way. Names `TSC_<Idea>_Quick` and `TSC_<Idea>_Studio`.
  - Each `notes.md` records the start and end, the user's messages, the rounds, and each thing the
    user had to point out.
- **The verdict:** both cars side by side as "Car 1" and "Car 2" in a random order, from the game's
  cameras, by day and at night; then both in the game, and the user says which they'd drive; the
  critic reviews both with the same list; the time each took. The result goes under "Things we
  learned" in `CHECKLIST.md` and decides which steps stay.

### Later

- **The design book:** each finished car's story (brief, mood, concepts, the pick, finishes,
  details, the car in the game) on the page online, built by `tool.publish` from the sheet.
- **Other people building their own cars:** a separate decision (hosting and cost per user).

## Watch out for

- **Speed.** The studio is slower on purpose. Keep Quick as fast as it is today, and keep every
  stage honest: if a stage adds nothing on a car, skip it and say so.
- **Unused screens.** The Lab's separate rooms went unused (2026-09-27). New views live on the one
  stand and appear only at their stage.
- **Too many questions.** A decision needs a real choice between directions. Technical choices
  stay Claude's (CLAUDE.md).
- **Stages undoing each other.** A later stage never quietly changes an earlier decision. If it
  must, Claude says so and asks.

## Questions for the user

1. Is anything missing from the steps, or unwanted (a "sponsors and branding" step, or one for the
   car's name and story)? Until the user says, the steps are as above.
2. The idea for the test, when W1 to W3 are done.
