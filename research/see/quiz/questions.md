# Ten questions about the car

Answer each in one to three lines, with coordinates in cm where asked (x out to the car's left, y up, z forward).
Say "don't know" rather than guess. Under each answer, name the file or command the answer came from.

1. Which end of the model line "side skirt crease 2" is nearer the nose (give both ends' coordinates), and does the
   course `meshlines.line("side skirt crease 2")` start at its nose end or its tail end?
2. A design writes: `deck = meshlines.line("body shell roll 2", tilt=33)` then paints
   `zone=deck.between(deck.start, deck.at(z=-60)).band(3)`. Which stretch of the car does that band cover: give its
   z range, and say whether it is the front part of the roll or the back part.
3. Which named panel of the model is under the point (70, 61, -26), and on which part of the car?
4. Give a centre point for a round badge 25 cm across on the rear flank, facing out, where it reads flat (no stretch
   to speak of).
5. A band laid along the model line "sidepod inlet edge 1": does it run on across onto the neighbouring body (the
   sidepod top, the body shell), or stop at the sidepod inlet's edge? Why?
6. A small placard laid along the model line "engine cover seam 2", on the stretch between z -74 and z -62: does it
   fall foul of a panel the car must keep clear? Which one, and what happens?
7. `s.paint("wheels", "gold")`: which parts of the car does the gold land on?
8. Which named model line runs along the side skirt from about z 149 back to about z 17, and how long is it?
9. Standing at the car's left side with the nose to your right: is the sidepod inlet's opening in front of (nearer the
   nose than) or behind the flat room on the sidepod top at (70, 61, -26)?
10. Which parts of the body are pieces of their own, with a gap of more than 1 cm to the rest, so that a line or a
    band stops at their edge as a wrap would? Give the gaps.
