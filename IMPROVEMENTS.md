# Improvements to the tool

The queue of things the tool should do better. Newest at the bottom of each group. The `skin`
skill says how it's kept: during a skin, Claude fixes only what that skin needs and adds
anything else here. The user says when to work on the list. A finished item is deleted
from here, and what it taught goes under "Things we learned" in `CHECKLIST.md`.

Each item: what's wrong or missing, when and where it showed up, and an idea for the fix. A
bigger item keeps its working notes under "Improvements after the build" in `CHECKLIST.md`.

## Under way

- **The Lab** (2026-09-26): the tool's own lists, each thing with a line to copy for Claude.
  Steps 1 and 2, the materials room and the UV map room, are built and wait for the user to
  look. The user's new idea (2026-09-26): the Lab as the place a car gets designed, starting
  from a clay model: the Studio (step 5), built, waits for the user to try it on a new car. The
  steps and notes are in `CHECKLIST.md`, "The Lab".

## The tool

- **Words on the inner car** (2026-09-25, TSC_CMYK_BlackTail): `Skin.emboss` raises lettering,
  but most inner parts share their texels with their mirror twin (74 to 99 %), so a word reads
  backwards on one side. Only marks that read the same both ways work there (the registration
  marks). Idea: list the inner parts' unshared areas big enough for a word (the tail frame's
  centre, the floor's centre plank?) and name them as spots, like `SPOTS` on the body.
- **The shared-paint note knows only twins with one name** (2026-09-26, the UV map room). When
  a design paints a part whose paint other parts share, `Skin._warn_shared` notes it only if the
  sharer has the same name (the mirror twin). The UV map room showed more: the front wing shares
  most of its paint with the floor, and 16 inner parts use one patch of the sidepod frame's and
  floor's paint. Idea: take the sharers from `coverage.twins()` and name them in the note, as
  `parts.Parts.share_words` does.
- **Motifs lined up across panels** (2026-09-24, checkpoint 6). The tool can spread pictures or
  dots evenly, but not in rows that line up from panel to panel, like a regular grid. Idea: a
  `regular` switch on `Skin.scatter`, using `looks.surface_points(regular=True)`.
- **Writing on the tyres** (2026-09-24, checkpoint 5). Not built: all four tyres share one
  paint and the left and right ones aren't mirrored, so text reads backwards on one side.
  Idea: symmetric words and logos only, or no text on tyres at all.
- **Some inner part names are guesses** (2026-09-24, checkpoint 3): side vent, side vane, nose
  sensor, airbox. Check them the first time a design paints them. Known since the air brakes
  (2026-09-25): "nose sensor" is the nose panel's lifting arms, "rear damper" the rear quarter
  panel's arm, and "airbox" the opening under each quarter panel. Known since the turning
  wheels (2026-09-25): "brake caliper" is the split ring at each wheel's centre (5 to 7 cm from
  the axle, on the outer face, under the cover's hub), and "hub" the fixed fairing inside the
  wheel, with the brake light in its slot. Renaming them means updating
  `tool/naming.py`, `skins/TSC_Stealth_CMYK/design.py`, `tool/partskin.py` and `AIRBRAKES` in
  the viewer.
- **Pictures on the Mac** (2026-09-26, TSC_FlagPeel_CostaRica): `tool.snap` drives Edge on the
  Windows PC, so on the Mac there's no command for the six views, the close looks or the titled
  picture for the user. Claude did them by hand, with a small Node script driving the Mac's
  Chrome over CDP (`viewer.show` per view) and Pillow in the container for the sheets. Idea:
  `tool.snap --mac`, or a script in `docker/` the Mac runs, with the same `SHOTS` and `CLOSE`.

## The viewer, from the user's screenshots and videos

- **The game's cameras at speed** (2026-09-25, the user). Cam 1, 2 and 3 are fitted to the
  user's screenshots standing still (Things we learned, "the game's lens"). In the game they
  pull back and lower as the speed rises and close in again when the car slows (the
  straight-line video; the lights test's and turbo videos show Cam 1 through whole runs, up to
  about 440 km/h). Idea: fit Cam 1 at a few speeds from those videos' frames the same way (the
  tyres and the horizon), ask for a short run in Cam 2 and Cam 3, and let the viewer slide
  between the poses with the pad's speed. `tool/snap.py`'s close look 9 ("driving camera") is
  still an older, narrower view.
- **The car number's lettering is a guess** (2026-09-25) until a close-up of the engine cover.
  The lights test's videos have one ("CAR 00", day at 13.2 s, night at 10.8 s).
- **The rear wings and air brakes, fine-tuning** (2026-09-25): the viewer opens both wings (up
  or down, then apart) at the video's pace, and raises the air brakes (rear quarter panels,
  nose panel, with their arms) while braking. How far the wings move, the air brakes' angles
  and how quick they are were set by eye. A short video from the side (pull away, brake hard,
  let go) would pin them. Notes under the lights improvement in `CHECKLIST.md`.
- **The page online, sharper on big screens** (2026-09-25, `tool/publish.py`): it carries
  2048² paint so a phone can hold it, so on a computer, close up, it's softer than the viewer
  here. Idea: publish the 4096² colour maps too and let the viewer take them when the screen
  is large and `renderer.capabilities.maxTextureSize` allows.
- **The page online, a lighter first visit** (2026-09-25): about 20 MB before the car shows
  (the car's shape 11 MB, the studio lighting 6 MB), slow on mobile data. Idea: the mesh in
  half floats or meshopt-compressed, and the 1K studio HDR on phones.

## To check in the game

These need the user to drive or look, so they're tested when a skin uses them.

- **Finishes never seen in the game** (2026-09-24, checkpoint 5): candy, chrome rims, rust,
  leather, metallic flake.
- **Glows never seen to light up** (2026-09-24, checkpoint 4): exhaust heat and boost (brake
  heat and turbo lit in the lights test, 2026-09-25). TSC_CMYK_BlackTail and TSC_CMYK_EndsInK
  (2026-09-25) carry exhaust heat where the chase cameras see it: inside the tail's two openings
  (orange) and in place of every stock turbo glow (magenta inside the wheels): whichever is
  installed, a turbo pad settles it. The viewer lights it with its Turbo button, a guess.
  Still to see: a reactor boost, a red turbo pad (red, as the pad?), and whether the sidepod
  frames light with the turbo like the hubs.
- **Whether the wheel covers turn** (2026-09-25): the viewer turns them with the tyres and
  rims; the tyres are known to turn (the tyre line in the game), the covers are assumed to. A
  skin with a pattern on the covers, driven slowly past the camera, would show it.
- **How see-through the glass is** (2026-09-24, checkpoint 4): the glass file's alpha made no
  visible difference, so the tool treats glass as tint only.
- **The upload size limit.** Zips stay under 8.5 MB until a limit shows up (2026-09-24,
  checkpoint 1); the install halves the roughness maps to fit (2026-09-25). Undocumented;
  Ubisoft said in 2022 that 9 MB "may be too big".
