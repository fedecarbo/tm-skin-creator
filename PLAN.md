# The plan: the Claude Code of Trackmania skins

2026-10-02. What an AI harness is, what this tool already is as one, and the next steps, in the
brief's form: what each is for, what you'll see, what it costs, which Claude model and why. One
step at a time, shown, then your OK (`RULES.md`). The queue of steps is in `IMPROVEMENTS.md`; this
file keeps the why.

## 1. What an AI harness is

**Agent = model + harness.** The harness is everything around the model that isn't the model: the
loop, the tools, how the context is assembled (instructions, skills), memory and state,
permissions and guardrails, verification and feedback loops, and the surface the user works in.
"If you're not the model, you're the harness" (LangChain, March 2026). The term went mainstream in
February 2026: Mitchell Hashimoto's habit of turning every agent mistake into a permanent fix in
the environment instead of retrying the prompt, and OpenAI's report on building a product with no
hand-written code ("humans steer, agents execute"). Claude Code is the canonical harness product;
the Claude Agent SDK is the same harness as a library.

Eight findings that bear on this tool:

1. **Fix the environment, not the prompt.** OpenAI's five-month experiment (about a million lines,
   1,500 pull requests, three to seven engineers) was slow at first "not because the model was
   incapable, but because the environment was underspecified": missing tools, abstractions and
   structure. The engineers' job became designing environments, specifying intent and building
   feedback loops. `RULES.md` already says it: a fact that prevents a mistake goes into the code.
2. **Short map, deep shelf.** One big instruction file failed at OpenAI (crowding, overload, rot,
   impossible to verify). What worked: a hundred-line map pointing to documents read on demand,
   validators that fail when a reference goes stale, and regular pruning. Anthropic's context
   engineering post: performance degrades as the context grows ("context rot"), so find the
   smallest high-signal set. Agent Skills load in tiers: a line always, the skill on request,
   reference files only when needed. This repo did that cut already (about 20,600 words of guidance
   down to 5,700, rules scoped to the paths they are about).
3. **The tool's interface shapes behaviour as much as the model.** SWE-agent (2024): few simple
   commands, informative feedback after every action, guardrails against cascading errors.
   Anthropic's tool-writing guide: consolidate, return only the next decision's inputs ("3 checks
   passed, 1 failed: lint"), meaningful errors, evaluate tools by running the agent on them.
   Microsoft's study of 11,700 agent runs (August 2026): structured interfaces made agents up to
   4.7 times more consistent; Python-script interfaces reached the same results in 42% fewer steps
   and 56% fewer tokens; scratchpads changed little. The paint box (a short Python script of paint
   calls on named parts) is the efficient shape.
4. **Verification must be grounded outside the agent's own transcript.** The "progress mirage"
   paper (July 2026): an agent grading its own work accepts plausible changes as progress while
   the real outcome stagnates; evaluation grounded in the real system is "a structural
   requirement", and even a bare accept/reject gate works if it is grounded. Anthropic's
   three-agent harness (April 2026) separates the one who plans, the one who makes and the one
   who judges, handing off through files, "because models are unreliable judges of their own
   output". Anthropic's long-running harness (November 2025): a feature list with pass/fail as the
   ground truth, a progress file, one feature per session, a clean state at the end, and a browser
   to actually use the app. Claude Code's `/goal` keeps working until a condition holds, checked by
   a separate small model after each turn.
5. **Visual work: the agent must see its output, and loops left alone drift to the generic.**
   In the Blender agent tools, "sending a screenshot back to the model after each operation was
   the single biggest quality improvement": render, look, fix, from several angles. A study in
   Patterns (December 2025) ran 700 image-describe-image loops across four image models and four
   describers: every one converged on about twelve generic motifs ("visual elevator music"). The
   authors call for anti-convergence mechanisms and sustained human-AI interplay. Anthropic's own
   front-end design skill exists because without direction the model "converges on the statistical
   average". Claude Design (April 2026) refines by chat, comments, direct edits and sliders, and
   starts from the user's own materials. The user's pick is the diversity engine; the loop must
   stay theirs.
6. **Evals: start from real failures, keep them cheap, separate the graders.** Anthropic's evals
   guide: tasks, trials, graders (code, model, human), capability versus regression, pass@k versus
   pass^k, start with 20 to 50 real failures. This tool's self-test is a regression eval of the
   pipeline (bytes identical). Nothing measures the look, and the look is what the user judges.
7. **Claude Code's parts, as the reference.** An instruction file as a map; skills loaded on
   request; rules scoped by path; hooks for deterministic enforcement at the session's events
   (start, each message, before and after each tool, stop); permission allow and deny lists;
   subagents with fresh context and few tools; memory in files; `/goal`. The rule the guides
   converge on: hooks and permissions enforce ("an instruction in CLAUDE.md is a request, not a
   guarantee"), skills inform, subagents isolate.
8. **Durable state lives in files and git; sessions hand off through artifacts.** This repo's two
   computers already do exactly that through GitHub.

In one line: the model can already design a car; what decides quality and speed is the harness:
how fast the car gets in front of the model's and the user's eyes, how grounded the check is, how
little must be read each time, and how every mistake becomes a permanent fix.

## 2. The tool today, read as a harness

It already is one, and a thorough one: the model never touches a texture; it writes a short script
of paint calls on named parts, and code does the rest.

| Harness part | Here today | The gap |
|---|---|---|
| Map and knowledge on demand | `CLAUDE.md` and `RULES.md` every session (about 1,150 words); the `skin` skill on request; the machinery's rules only on its paths; the car map only when a design needs it. | Nothing checks that the instructions stay true: a renamed command rots silently. |
| The tool interface | Parts from the mesh, zones in centimetres, the map's areas, fixed spots for lettering; `show` prints its notes (shared paint, parts left in clay, lettering shrunk, a decal crossing a fold). | The checks before showing are three commands and a reading of pictures. |
| Grounded verification | The self-test (game files identical across commits), the band check (measured on the car, with a falsifier), the map check (lines measured). | **The look has no grounded check.** Claude judges its own views in the same context that wrote the design, which is the progress mirage exactly. No before-and-after at a fixed camera. |
| Seeing the car | A hidden browser renders the viewer: six views, nine close looks, the game's cameras by day and night; the Lab shows each step. | The map that tells designs where the car's edges are is a reading, differs slightly between the Mac and the PC, and has not been proven against the game. |
| Hooks and permissions | A pull at session start; the Lab's notes delivered with each message; file reads denied in the game's skin folder. | The game-folder rule is only a request on the shell side. "Don't leave work unpushed" is a rule, not a check (the page online was five days behind the game). |
| Memory and handoff | Each skin's `notes.md` (the words verbatim, every change, open items), `IMPROVEMENTS.md`, `RULES.md`, the versions' pictures, GitHub between the computers. | Nothing surfaces the open items at a cold start. |
| Subagents | The car mapper. | No fresh eyes: the only second opinion on a car is the user's. |
| Evals | None for the look. The record holds the material: every change the user asked for is a real failure case. | No way to tell whether a change to the tool makes cars better before the user sees them. |
| The surface | The Lab: the car, the timeline, picks as widgets, pins on the car with the picture the user saw. | Fine. |
| The loop | "Change it until they say yes": the user's. | Keep it the user's. |

What the user said when asked (2026-10-02):

- Fresh eyes are wanted, but "the problem isn't the designs per se": when the intent is a line
  from the rear all the way to the nose, "there's always a glitch: a line seems cut, or didn't
  cover the full rear side." "A perfectly mapped car: if the intention is to do X, then you
  receive X." On Rescue, after the fix, "the line didn't cover the rear, as in the farthest back
  of the side of the car."
- The map: "It's not about deciding. It's about just knowing. A skeleton that functions like a
  guide for the blind." "Layer by layer, accurate throughout, like a topographic skeleton every x
  cm", and "literally painting lines, as in a skeleton."
- Drawing on the skin stays paused until the skeleton is trusted. The materials and the UV map
  "in a new way" come after that, from the user's words.

So the centre is **intent to result**: the tool must know the car (a skeleton, not a picture),
measure every result against the intent in the skeleton's terms before anyone looks, and only then
use eyes, fresh ones, for what numbers can't catch. Seeing better is not the goal; needing to see
less is.

A contour at a fixed height, or a section at a fixed distance along the car, is a plane cut
through the mesh: pure geometry, nothing to interpret, nothing for two computers to disagree about.
The map already cuts the body every centimetre along its length and keeps each cut's outline; what
it adds on top (the shoulder, the lower edge, the ridges, the areas) is a reading of those cuts,
and the reading is where the doubt lives. The skeleton is the cuts, shown and checked.

## 3. The steps

### Step 1. Shortfalls measured, not seen

- **For:** the user's exact case. Each design step already computes exactly which texels it
  paints, and the map can already say, for any point on the body, how far along it sits from nose
  to tail and how far it is from each edge. Nothing joins the two. Joined, `show` prints, per step
  and per side, where the paint runs and where it stops short, in centimetres: "Reflective band:
  left side from the nose's fifth to the tail's last tenth; stops 9 cm short of the rear flank's
  end on both sides." The same measure says when a part is only partly covered, when paint meant
  for the side spills onto the top, and when the two sides differ. The intent is the zone Claude
  wrote; the result is measured on the car; the shortfall is a number.
- **You'll see:** TSC_Snow's open gap at the rear named in centimetres before anyone looks at a
  picture; the fix; the rear close up, before and after at the same camera, with the measure
  beside each. Before-and-after at a fixed camera stays as an ability: the last close sheet is
  kept per version and the tiles that changed are marked.
- **Costs:** two to five seconds per `show`. No new instructions: it arrives in `show`'s notes.
- **Model:** a big one (Opus 5.5 or Fable 5.1) to build it: geometry on the map's layers. After
  that no model is in the loop; it is code.
- **Checked by:** the self-test (every game file identical; only the notes change, and the commit
  says so); on TSC_Snow as committed the report names the rear shortfall before any fix; a band
  painted deliberately 10 cm short is reported as 10 cm short.

### Step 1b. Progress in the chat

- **For:** the user has no terminal and can't read one; the Lab's chat is their window. Today it
  shows a live line only while a paint runs ("Claude is painting · Reflective band") and nothing
  during the rest of the waiting: the pictures, building the game files, installing (about 100 s on
  the PC), publishing (plus GitHub's minute or two), the self-test, the picture maker, the map's
  rebuild, later the fresh eyes. The user (2026-10-04): "the chat shows options to choose, but it
  would be nice to have progress indicators when it's doing something." So: one progress widget at
  the foot of the chat, one per job. While a command runs it shows the job, the stage, a bar where
  the count is known ("Taking pictures · 4 of 6", "Game files · 7 of 9", "Checking the tool · car
  2 of 3") or a quiet pulse where it isn't ("Installing", "Putting it online"), and the time
  elapsed; when the job ends it settles into one short line ("Painted and photographed · 1 min
  12 s"). Every command reports its stages through one small module that writes a file the Lab
  already polls for; the paint's own steps keep arriving as they do now.
- **You'll see:** under the last message in the chat, a line that always says what the tool is
  doing and how far along, for every job; nothing left looking stuck.
- **Costs:** milliseconds per stage. No new instructions: it lives inside the commands.
- **Model:** a small one (Sonnet 5.5): plumbing. Built in the same Mac session as Step 1, so the
  user watches Step 1's own work through it.
- **Checked by:** during a paint, an install, a publish and a self-test the widget names each
  stage as it happens and the count where there is one; a job killed midway leaves nothing stuck (a
  report older than a minute reads as "stopped"); the game files identical.

### Step 2. The topographic skeleton: cut from the mesh, painted on the car

- **For:** the guide for the blind. Three families of plane cuts through the body every x cm:
  sections across the car along its length (the map's one-centimetre cuts, already computed),
  contours at fixed heights, and profiles along the car at fixed distances from the middle. Each
  is a clean outline in centimetres with no reading applied, named by its number ("the contour at
  30 cm", "the section at minus 120"). Saved once as data in the repo, so both computers hold the
  same car. Then literally painted on a car: TSC_Skeleton, the clay car with the contours every
  5 cm and the sections every 10 cm as thin dark lines, painted into a real skin texture exactly
  as any design's paint is, visible in the Lab from every angle. It is both the guide the tool
  works from and the test of the mapping from the car to its texture. Step 1's measures are then
  stated in cuts ("stops at section minus 142, 9 cm short of the last section the side reaches").
- **You'll see:** the skeleton car in the Lab, turnable, with its grid of cuts (two spacings
  offered as a widget, the user picks).
- **Costs:** a session or two of tool work, once. Per skin: nothing.
- **Model:** a big one for the cuts and the check (the car mapper, whose brief becomes "cut it and
  prove it"); a small one (Sonnet 5.5) for the data loading.
- **Checked by:** the cuts identical on the Mac and the PC; every contour level and every section
  evenly spaced in the viewer's low side views, by number; the user's own look at the skeleton car in
  the Lab. Drawing on the skin waits for this.

### Step 3. Fresh eyes on a finished car

- **For:** what numbers can't catch: a graphic sunk or soft at a fold, a part forgotten in clay, a
  leftover from an earlier version, the idea not reading from the game's cameras. A second Claude
  with no memory of the design gets only the user's words, the pictures and Step 1's measures, and
  answers in a few lines: what is wrong, in which picture, where. The designer fixes; the eyes look
  again at the changed places only. Only where the close looks already run (a car shown alone, the
  pick, before install), never on takes: a check, not a stage.
- **You'll see:** one line in the Lab's timeline before a finished car is shown: "Fresh eyes
  checked it: two things fixed (the band's end at the rear; a clay strip under the left sidepod)."
  A clean car gets "Fresh eyes: nothing to fix."
- **Costs:** about a minute per finished car; nothing per take. Measured (2026-10-05): the
  pictures 10 s; the eyes' first look 1 min 40 s to 4 min 36 s over six runs (45k to 85k tokens);
  a second look at the changed pictures 44 s.
- **Model:** a big one with vision (Fable 5.1 or Opus 5.5): judging a car from pictures is the hard
  thinking. Opus 5.5, as the studio's critic trial chose (2026-09-28).
- **Checked by:** on a car with a known flaw the eyes name it with the right picture; on a clean
  car, nothing; the time stays near a minute.
- **Dropped (2026-10-05).** Built and tried (a Read-only agent on Opus 5.5 given the user's words,
  the steps, the measures and 20 pictures; a test car with four planted faults over four rounds):
  on Rescue v2 it found three real flaws the close looks had missed, but none of the three the user
  flagged next (the band over the bottom piece's black, RESCUE across a fold the paint box had
  warned of, an icon "too deliberate"), its next top finding was wrong, and each look took 2 to 5
  minutes. The user: "probably I can flag things more accurately". In its place, at their
  suggestion, the Lab's pen: drawing on the car what a note means (built and used, 2026-10-05). What stayed: the measure sees the
  body resume bare past an opening, behind the rear wheel ("STOPS SHORT past an opening").

### Step 4. Rules that are checks, not requests

- **For:** three rules that only hold while Claude remembers them. A hook refuses any shell
  command naming the game's skin folder unless it is the install command. A hook refuses to end a
  session with uncommitted or unpushed work and says what to do. The install command publishes the
  page online itself.
- **You'll see:** nothing new in the Lab; a refused command should one ever name that folder; a
  session that can't end with work unpushed; the page online always matching the game.
- **Costs:** milliseconds per command; the publish's minute per install, already the rule.
- **Model:** a small one (Sonnet 5.5).
- **Checked by:** a command naming the folder refused with the reason, the install command not; a
  session with an unpushed commit held until pushed; after an install the page online lists it.

### Step 5. Instructions that can't rot

- **For:** every command and path the guidance names must exist; a renamed command then fails the
  self-test, not a session.
- **You'll see:** one line in the self-test's output: how many commands and paths are named, all
  present.
- **Costs:** nothing per skin; a second in the self-test.
- **Model:** a small one.
- **Checked by:** renaming a command on a branch fails the self-test naming it.

### Step 6. Where we are, at a cold start

- **For:** a new session on either computer sees the open items without reading every record: a
  command lists every skin's open items and the last thing shown, and the session-start hook
  prints it after the pull.
- **You'll see:** a session that starts already knowing "TSC_Snow: open: the gap at the rear".
- **Costs:** nothing.
- **Model:** a small one.
- **Checked by:** a fresh session prints TSC_Snow's open item before anything else.

### Step 7. The tool measured against the record

- **For:** knowing whether a change to the tool makes cars better before the user sees them. Every
  flaw the user ever pointed out is a real failure case, and the records hold them with the picture
  shown before each (the deleted skins' records are still in git). A command gathers what the user
  said, Claude sorts it once (a flaw, with its kind and place, or a wish), and each flaw's car is
  painted again as the user saw it, with this code; Step 1's measures and the paint box's own
  checks run on it; the score is how many flaws they name. On demand only.
- **You'll see:** one line: "your record: 26 flaws you pointed out, 8 on cars that can be painted
  again; the tool now names 2 of them before you would".
- **Costs:** on demand, about 20 to 40 seconds per car (2¼ minutes for the 8, 2026-10-05).
- **Model:** a big one to sort the record (each flaw's kind and place is a reading); then no model
  in the loop, it is code.
- **Checked by:** the score printed, and up after Step 1 on the same cases (the checks are named per
  flaw, so a check's own share shows).

### Not building, and why

- **No loops that polish on their own.** Image loops converge on the generic; the user's picks are
  the diversity engine.
- **No taste guides, example cars or design rules.** Fresh eyes judge against the user's words, not
  a style.
- **No flat drawing surfaces.** A view is trustworthy only on the surfaces that face it; everything
  is measured on the car.
- **No growth of the instructions.** Every step puts its fact in code; the skill changes by
  replacing a line, not adding one.
- **Deferred by the user:** drawing on the skin (until Step 2 is green); the materials and the UV
  map in a new way (after that, from their words).

### Where the work runs

Steps 1, 1b, 2, 3 and 7 need the tool and the self-test: a session on the Mac (the PC for installs
and the game). Steps 4, 5 and 6 are plain Python and hook settings: drafted anywhere, passed through
the self-test on the Mac before they count as done.

## Sources

Read through web-search summaries (this session's network could not open the pages themselves).

- Anthropic: Effective harnesses for long-running agents (Nov 2025); Effective context engineering
  for AI agents (Sep 2025); Equipping agents for the real world with Agent Skills (Oct 2025);
  Writing tools for agents; Demystifying evals for AI agents; Building effective agents; Building
  agents with the Claude Agent SDK; the three-agent harness (Apr 2026, as reported by InfoQ).
  https://www.anthropic.com/engineering
- OpenAI: Harness engineering: leveraging Codex in an agent-first world (Feb 2026).
  https://openai.com/index/harness-engineering/
- LangChain: The anatomy of an agent harness (Mar 2026). Wikipedia: Agent harness.
- Mitchell Hashimoto's February 2026 post on engineering fixes into the agent's environment.
- Yang et al.: SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering (2024).
  https://arxiv.org/abs/2405.15793
- The Devil Is in the Interface: Evaluating How Tool Architecture Shapes Coding Agent Behavior
  (Microsoft Research, Aug 2026). https://arxiv.org/abs/2608.11386
- When Do Agent Loops Mistake Stagnation for Progress? Self-Evaluation Bias and Externally Grounded
  Verification in Long-Running Autonomous LLM Agent Loops (Jul 2026). https://arxiv.org/abs/2607.25152
- Autonomous language-image generation loops converge to generic visual motifs. Patterns (Dec 2025).
  https://www.cell.com/patterns/fulltext/S2666-3899(25)00299-5
- Claude Code: the /goal command and the features overview. https://code.claude.com/docs
- Claude Design launch (Apr 2026), TechCrunch. Blender agent tools with render-check-fix loops
  (blender-asset-mcp; the 3D-Agent write-up on devtalk.blender.org).
- ai-boost/awesome-harness-engineering (an index of the field).
