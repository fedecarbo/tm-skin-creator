# Rules

How we work on the tools, written as the mistakes not to repeat: what not to do, why, and what to do
instead (how we work with the user is each concept's: the Lab's RULES.md). It stays a page: a new rule
replaces or merges another. A fact about the game or the code goes into the code (a warning, a check, a
docstring).

## Designing

- **Don't load a design with taste rules, past cars or examples.** They make every car look the same.
  Start each car blank, from the user's words; borrow an earlier car only when the user names it.
- **Don't put words on a car the user didn't ask for.** Lettering has never come out well on this
  car's curves (the user, 2026-10-05: "The approach is always terrible"); write only words they ask
  for.
- **Don't paint the car's lines for their own sake, or spread a detail over the car by a rule.** Follow
  the car's own flow, read from its mesh (the user, 2026-10-06: "just follow the flow of the car"): one
  of the model's lines whole, or a line beside one, is there when it's the line a graphic needs. A line on
  a skin needs a reason in the idea (some liveries use lines for mood; most have none). A detail goes a
  few at a time where it means something, in the car's own language (its own fasteners and seams), shown
  close up before there are more: bolts round every panel by a rule were "one of the biggest failures"
  (the user, 2026-10-05).
- **Don't trade quality for speed, and don't confuse checks with quality.** A better game file is
  worth a slower build. A check names an accident, never a design: a shape that crosses parts on
  purpose stays (the user, 2026-10-05: "would a check ruin the creative approach?").
- **Don't leave any part as it came because it's hidden.** The user judges the whole car, close up.
- **Don't call something done because a number passed.** The user's eye decides. Show it close up,
  with the measure beside it.
- **Don't promise what the game can't do.** Say so plainly (the skill lists what can't be done).

## Building the tool

- **Don't add a step that every skin pays for.** The cost repeats on every car. Say first what a
  step costs in time; if every skin would pay it, leave it out.
- **Don't build machinery the user hasn't seen.** One step at a time, shown, then their OK. When they
  doubt something, ask what they'd need to see before building more on it.
- **Don't grow the instructions.** The more there is to read, the slower and more alike the work.
  Replace or merge instead of adding; a fact that prevents a mistake goes into the code.
- **Don't mention what no longer exists, or how things used to be,** in instructions, comments or
  docstrings. Naming it puts it back in mind. Write as if things had always been this way; history
  is in git. (A skin's `notes.md` is its record, and keeps its story.)
- **Don't change the tool without the self-test.** Every car's game files stay identical, byte for
  byte, unless the change means to alter them, and the commit says which and why.
- **Don't guess.** Measure slowness before fixing it, and check the viewer against the game before
  building a fix for it.
- **Don't take the game's own files apart.** The licence forbids it and they're encrypted. Nadeo's
  published files, the stock textures and the user's screenshots and videos are fair.
- **Don't pick a tool or library from memory.** Look up its latest release first. Offer a
  one-time-payment option when it's far better; discuss any subscription first.
