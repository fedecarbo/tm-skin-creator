# Improvements to the tool

The queue of things the tool should do better. Newest at the bottom of each group. The `skin`
skill says how it's kept: during a skin, Claude fixes only what that skin needs and adds
anything else here. The user says when to work on the list. A finished item is deleted
from here, and what it taught goes under "Things we learned" in `CHECKLIST.md`.

Each item: what's wrong or missing, when and where it showed up, and an idea for the fix. A
bigger item keeps its working notes under "Improvements after the build" in `CHECKLIST.md`.

## Under way

- **Your own colours for the speed numbers, brake lights and car number** (2026-09-25, the
  user). Research done on the Mac: the speed digits and brake lights very likely can take a
  colour; the car's initials and number can't. The user's night screenshots of a pink-lit
  skin (2026-09-25) prove the digits and the rear lights' gear bands take a skin's colour.
  **Next, on the Windows PC:** `tool.skin show TSC_Lights_Test`, install it, and the user
  drives it (brake, turbo, day and night, F12 screenshots). Then the paint box gets the words
  ("speed numbers", "rear lights", "brake lights"). Notes and the full test in `CHECKLIST.md`.

## The tool

- **Motifs lined up across panels** (2026-09-24, checkpoint 6). The tool can spread pictures or
  dots evenly, but not in rows that line up from panel to panel, like a regular grid. Idea: a
  `regular` switch on `Skin.scatter`, using `looks.surface_points(regular=True)`.
- **Writing on the tyres** (2026-09-24, checkpoint 5). Not built: all four tyres share one
  paint and the left and right ones aren't mirrored, so text reads backwards on one side.
  Idea: symmetric words and logos only, or no text on tyres at all.
- **Raised detail on the inner car** (2026-09-24, checkpoint 5): bolts, embossed logos, ribs,
  through `Details_N`. Not built. The body can't take relief at all.
- **Some inner part names are guesses** (2026-09-24, checkpoint 3): side vent, side vane, nose
  sensor, airbox. Check them the first time a design paints them.
- **Claude's snapshots after the viewer's new look** (2026-09-25). The new look was checked on
  the Mac only. Run `tool.snap` once on the Windows PC and compare with an older views sheet:
  `?snap=1` should keep the old framing.

## The viewer, from the user's screenshots and videos

- **Cam 2 in the Driving menu is a guess** (2026-09-25) until a screenshot of the game's Cam 2.
- **The car number's lettering is a guess** (2026-09-25) until a close-up of the engine cover.
- **The rear wing flap** (2026-09-25): the straight-line video gave its timing (up from ~60
  to ~95 km/h under throttle, down at ~43-34 while coasting), and from behind the tail panel
  and tail corners rise together. The user saw other pieces move when braking, and the wing
  looks steeper then. Which pieces move, the hinge and the angles wait for a short video from
  the side: pull away, brake hard, let go. Notes under the lights improvement in
  `CHECKLIST.md`.

## To check in the game

These need the user to drive or look, so they're tested when a skin uses them.

- **Finishes never seen in the game** (2026-09-24, checkpoint 5): candy, chrome rims, rust,
  leather, metallic flake.
- **Glows never seen to light up** (2026-09-24, checkpoint 4): brake heat, turbo colour,
  exhaust heat, boost. The viewer shows them off. The lights test skin carries all four.
- **How see-through the glass is** (2026-09-24, checkpoint 4): the glass file's alpha made no
  visible difference, so the tool treats glass as tint only.
- **Does a skin installed while the game is running show up without a restart?** (2026-09-24,
  checkpoint 1). Still not recorded.
- **The upload size limit.** Zips stay under 8.5 MB until a limit shows up (2026-09-24,
  checkpoint 1).
