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

The Lab's stand stays the one page (the separate rooms went unused, 2026-09-27):

- **A line of stages over the car:** Brief, Mood, Concepts, Shapes, Colours and materials,
  Details, Review, Road test, Released. Each shows its state: to do, Claude on it, waiting for
  you, decided. The stage waiting for the user stands out.
- **The stand changes with the stage:** the brief card; the mood boards; three cars side by side
  for the concepts; day and night and the swatches for colours and materials; the stations and
  close-ups for details; the critic's tags for the review; the screenshots for the road test.
- **The stations stay under the car.** The stages say when; the stations say where on the car.
- **Notes on the car work everywhere,** as now. A note on a decided stage reopens it, and the Lab
  says so.
- **Quick cars** show no line of stages, just the stand as today.

---

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

Step by step, each agreed before it's built, and ticked only when the user has seen it (as the
Lab's steps are). Mockups first for anything the user will look at, so they pick from real
pictures.

### S1. The test: Studio against Quick

- **What it's for:** find out whether the studio is worth it before building anything for it
  (the user, 2026-09-28: "I want to do a test for the quick and the studio one to see the
  difference if it's worth it"). One idea of the user's, made twice, in two sessions: once the
  quick way, once through the studio.
- **What you'll see:** two cars of the same idea, shown side by side without saying which is
  which, then both in the game. You pick the one you'd drive, and we compare how long each took
  and how many things you had to point out.
- **Model:** Opus 5.5 in both sessions, so only the way of working differs.
- **Before the test (Claude):** write the studio routine into the `skin` skill as its own section,
  used only when the user asks for the studio: the stages, the decisions, the brief card
  (`skins/<name>/brief.md`), the critic as a subagent with its quality list, the three concept
  designers in parallel. The quick way stays exactly as it is. No Lab changes: the studio session
  works in the chat and the Lab as they are.
- **How the test runs:**
  - The user's first message is the same, word for word, in both sessions. Each session is told
    only its way ("quick" or "studio"), not about the other.
  - The quick session goes first, so the studio's brief and mood boards don't shape the user's
    taste before the quick car is made.
  - Names: `TSC_<Idea>_Quick` and `TSC_<Idea>_Studio`.
  - Each session writes in its `notes.md`: when it started and ended, how many messages the user
    sent, how many rounds, and each thing the user had to point out.
- **The verdict:**
  - Both cars side by side as "Car 1" and "Car 2" in a random order, from the game's cameras, by
    day and at night. The user picks without knowing which is which.
  - Both installed and driven. The user says which they'd drive and why.
  - The critic reviews both with the same quality list, and we count the faults.
  - The time each took, and how much of it was the user's.
  - The result goes under "Things we learned" in `CHECKLIST.md`, and decides whether S2 to S6
    happen, and which stages stay.
- **The frontend meanwhile:** the Lab's layout for the studio is chosen from mockups
  (https://claude.ai/artifact/4RxUASJaYTfphRZbk1gFtG: A, the line of stages over the car; B, the car's sheet beside it; C, a decision drawer; made from the Lab's own stylesheet and the CMYK texture round's pictures), and built only if the test says the
  studio is worth it.

### S2. The experts

- **What it's for:** the specialists' know-how, the three concept designers working at once, and
  the independent critic.
- **What you'll see:** concepts that differ more and arrive together; a critic's list of findings
  on each car, and fewer things for you to spot yourself.
- **Model:** Opus 5.5 to write the guides; the critic tried on both Opus 5.5 and Fable 5.1 on the
  same cars, keeping the one that finds more real faults.
- **Notes for Claude:**
  - One guide per stage beside the `skin` skill, short, loaded only at its stage. Seed them from
    "What works on this car" and "Things we learned"; each car adds to them.
  - The critic as a subagent with a fixed quality list, given pictures (views, close looks, the
    game's cameras, day and night) and the brief only.
  - Check first whether three paints can run at the same time on the PC (Edge, the GPU and the work
    folder shared): if not, the designers write their designs in parallel and the paints queue.
    Measure the time either way.

### S3. The stage record

- **What it's for:** the tool keeps each car's stage, decisions and brief, so the Lab can show
  them (the Lab's rule: it shows only the tool's own data).
- **What you'll see:** nothing new yet; it's what S4 reads.
- **Model:** Opus 5.5.
- **Notes for Claude:** one small file per skin (stage, state per stage, the decision and its
  date, the brief), written by the tool's commands, not by hand. Quick cars have none.

### S4. The line of stages in the Lab

- **What it's for:** see where the car is and what's waiting for you.
- **What you'll see:** mockups first (two or three directions rendered on a real car), then the
  line over the stand, and the stand changing with the stage.
- **Model:** Opus 5.5.
- **Notes for Claude:** keep the Lab's speed (it draws only when something changes, pictures
  kept in the browser). Nothing new drawn while Claude paints.

### S5. The decision views

- **What it's for:** each decision in the Lab, not just in the chat: the mood boards, the concepts
  side by side (takes over the Lab's 9.4), the finishes board, the critic's tags with before and
  after (9.3 and 9.5), the road test screenshots (9.6).
- **What you'll see:** one at a time, each from its own mockups, in the order the stages come.
- **Model:** Opus 5.5.
- **Notes for Claude:** the mood pictures from the web are references only: they stay off git
  (never push files that aren't ours to publish) and never go on the car. The pictures on the car
  come from the picture maker, the textures library, or Claude's own painting.

### S6. The design book

- **What it's for:** each finished car's story, to keep and share.
- **What you'll see:** a page per car on the page online: the brief, the chosen mood board, the
  concepts with the picked one marked, the finishes, the details, the car in the game.
- **Model:** Opus 5.5, or a smaller model: it's mostly layout.
- **Notes for Claude:** built by `tool.publish` from the stage record, so it's never written by
  hand.

---

## Watch out for

- **Speed.** The studio is slower on purpose. Keep Quick as fast as it is today, and keep every
  stage honest: if a stage adds nothing on a car, skip it and say so.
- **Unused screens.** The Lab's separate rooms went unused (2026-09-27). New views live on the one
  stand and appear only at their stage.
- **Too many questions.** A decision needs a real choice between directions. Technical choices
  stay Claude's (CLAUDE.md).
- **Stages undoing each other.** A later stage never quietly changes an earlier decision. If it
  must, Claude says so and asks.

## Questions for the user, before S1

1. Is this list of stages right, or is anything missing or unwanted (a "sponsors and branding"
   stage, or a stage for the car's story or name)?
2. The idea for the test (the user brings one they're pursuing).
