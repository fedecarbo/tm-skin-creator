# The car

Written by `python -m tool.carmap --describe` from the car's own shape (2026-10-22). Lengths in cm: x out to the car's left (the right mirrors it), y up from the ground, z forward (the nose's tip at 215, the tail at -162). Along the car: 212 the nose's tip; 190 the nose, over the front wing; 178 the front wheels' axle; 150 the nose; 130 the nose fin's plate; 110 the bonnet; 85 the cockpit opening's front; 60 the front flank; 30 the front flank, the sidepods begin; 0 the sidepods, their inlets; -30 the sidepods; -60 the sidepods' back, the number panel; -90 the deck, the engine cover panel; -120 the rear wheels' axle; -140 the tail; -158 the tail's end. Everything else about its shape the car answers, exact from its mesh: `PY -m tool.meshlines` and its questions.

## Where a graphic stops

- One skin, sewn, over most of the body: the body shell, rear flank, side skirt, nose tip, wing pylon, cockpit surround, engine cover, rear quarter panel, nose fin, fuel cap, nose panel, engine cover panel and number panel. A band or a line runs on across the seams between them.
- Pieces of their own, a gap of more than 1 cm round them: the tail corner and tail panel, 1.7 cm; the sidepod inlet (each side), 1.4 cm. A line stops there, as a wrap would.
- Pieces sewn on, 1 cm or less from the skin: the diffuser strake and diffuser, 0.05 cm; the sidepod top (each side), 0.41 cm; the diffuser strake, 0.04 cm; the nose fin, 0.35 cm. A line may run on.
- A graphic laid whole (a badge, words, a picture) stays on one piece, and off a fold.
- The cockpit leaves no skin down the top's middle from z 85 to -48, 28 cm out each side.
- Keep clear: the number panel (z -78 to -62) and the engine cover panel (z -120 to -81), which the game letters, and the nose fin's plate (z 118 to 142): nothing on them or within 3 cm (`show` names anything there).
