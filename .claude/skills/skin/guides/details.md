# Details: the detail designer's guide

Read on a new car (`new-car.md`, 3) when the work reaches the details: the inner car, its lights, the glass. It's what
separates a finished car from an amateur skin. It grows with every car: at the end of the step,
add what the car taught under "Learned", dated, with the car's name.

## What good looks like

- **Structure recedes, one detail speaks.** On a real race car the frames and the floor are carbon
  or satin black and the mechanics are metal or carbon; one small thing carries the accent (the
  springs, the calipers, the lights). Details in the accent colour everywhere cheapen it.
- **Nothing stays stock by accident.** Every light and part that shows is either chosen or dark.
  A stock colour in no part of the palette reads as unfinished (the critic looks for it).
- **The livery's ground reaches the edge.** Where the body's bottom colour meets the floor and the
  front wing, they belong to the car's colours, not to a default.
- **The lights are the driver's view all race:** the speed numbers and the rear lights, a brighter
  version of the car's accent, because lights glow.

## On this car

- `s.paint("inner", ...)` first, then the parts: carbon underneath (the floor and the front wing
  wear one paint), the frames round the inlets and the speed display in the body's trim finish.
  Most inner parts share paint with their mirror twin, and a small patch serves many parts (the
  front uprights, the tail frame, the sidepod frames, the rear strakes): `show` names every part a
  colour also lands on. Read it.
- What the chase cameras see of the inner car: the rear bumper and its corners, the rear strakes,
  the undertray's edge, the sidepod frames, the side vents, the front wing, the hubs through the
  covers. The rest is hidden or tiny.
- The stock inner car is full of lights: teal lamps in the cockpit, bulkhead and nose, a strip
  under the floor, white lights on the front wing's ends, a ring in each wheel, faint night glows
  on the airboxes and sidepod frames. The lights a skin recolours by name: `s.relight("speed
  numbers" | "rear lights" | "brake lights", colour)`; others with `s.glow`/`s.no_glow` on their
  parts. Braking turns the rear lights red whatever their colour; a tinted rear lens filters that
  red (keep it clear or warm). "Energy" is dark on the track; exhaust heat and boost were never
  seen: don't promise them.
- The glass: a tint also dims the lights behind the lenses; clear unless the idea wants it.
- Painted metal on the suspension arms shows Nadeo's carbon weave as woven metal: smooth it
  (`s.relief(parts, lambda pos, nrm: 0, replace=True)`). Words on inner parts read backwards on
  one side.

## Check before showing

- From behind first (`--cams`), then the review angles: low behind, under the tail, the underside.
- At night: every light that shows, in the car's colours.
- Where the body's paint meets the inner car: the diffuser, the floor's edge, the front wing.

## Learned

- 2026-09-28, TSC_Ladybird: the user wanted the floor and front wing green like the grass ("probably
  this needs to be green"), not carbon: the ground colour reaches the car's edge. The diffuser's
  fins under the tail caught the grass as slivers: paint such fins whole.
- 2026-09-25, TSC_CMYK_BlackTail: paint the tail after the exhaust (their trim shares texels); a
  glow's edge takes its neighbour's code (`paintbox.dark_take_codes`).
