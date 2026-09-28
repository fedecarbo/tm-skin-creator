"""TSC_Ladybird (the studio, 2026-09-28): a ladybird in the grass, made for the grass maps. From the
concept round, the user's mix: "I like B the most. I do like the grass from C though": B's jockey's
silks, satin red with a few big black spots, and C's turf-green blades rising up the lower sides.

Shapes, from the user's notes on the car: the spots are blobs, not perfect circles ("lady bug spots
are not perfect circles, more like a blob close to being a circle"); the nose is the ladybird's
black head, with two white blobs low on its sides ("I wonder if we make this black? as if it's the
head. Maybe too white blobs on the sides"); the grass is taller and denser ("Maybe more grass or
taller?"); no spot is clipped ("This spot is clipped", twice: one ran off the deck's edge, one
touched the cockpit's rim and went, the head taking its place).

The spots are painted on the outer panels only, so none runs down into what lies under it (on B one
ran inside a sidepod inlet: "The spot in b also transfers to the next object in the car"), and
they keep clear of the inlets and of the number panel and the engine cover panel, where the game
draws the player's number and name. Still rough: flat colour, one finish, no details yet.

Colours and materials, option A as the user changed it: the ladybird's own shine, the shell, its
spots, the head and its marks glossy under a clear varnish, like a beetle's wing cases; the grass
satin ("How about a but the grass make it a silky grass finish, so there's some contrast in the
ladybug and the grass").

The head's fringe keeps clear of its white marks, a thin black gap round each (the user's note on
the car: "Why is the grass touching this object.  Now it looks weird").

Wheels, option A: black legs. The wheel covers gloss black like the ladybird's legs and head, the
tyres plain black with a wet-look shine, like a beetle's glossy legs: the quietest, the body does
the talking."""
from tool import shapes

WORDS = "I like B the most.  I do like the grass from C though"
HEAD = "I wonder if we make this black? as if it's the head.  Maybe too white blobs on the sides"
BLOBS = "I think lady bug spots are not perfect circles, more like a blob close to being a circle"
GRASS = "Maybe more grass or taller?"
WHEELS = "the wheels in general is a full workflow as I build cars"
AROUND = "you need to include the grass where the black is as well.  The grass should be around the car"
RED, BLACK, WHITE, TURF = "#D7262B", "#111111", "#F3EEDF", "#3E8E3A"
# the outer panels a spot may sit on: never the inlets, the number panel or the engine cover panel
OUTER = ["body shell", "nose tip", "nose panel", "sidepod top", "engine cover|part", "rear flank"]
# big spots from above, (x, z, radius) in cm, scattered as silks' spots are, each on one panel: the
# sidepods' tops behind the inlets, the deck either side of the engine cover panel (x ±19), the
# right one forward of the deck's edge (z -132), where it was clipped
TOP = [(68, -32, 12), (-66, -38, 12), (33, -100, 11), (-33, -110, 11)]
# and one on each rear flank (y, z, radius), the flat spot behind the sidepod
SIDE = [(40, -70, 12)]
# the head: the nose ahead of a curved edge, as a ladybird's head meets its wing cases: 116 cm down
# the middle, just behind the nose fin's plate (z 118 to 142, which it takes in with its fin),
# curving forward to about 128 at the nose's sides (x ±26)
HEAD_BACK, HEAD_CURVE, HEAD_HALF = 116.0, 14.0, 28.0
# the nose's black body, whose lower edge (HEAD_LIP cm up) its own fringe of grass rises from
NOSE, HEAD_LIP = ["nose tip", "nose panel", "body shell"], 41.0
# its two white blobs on the nose's sides (y, z, radius): marks on its flanks, not eyes on top. The
# nose is 20 to 57 cm high there, rounded over the top, so a blob seen from the side at y 45 stays
# on its side by its height alone; painted after the grass, which rises that high. Kept off "the
# top" (as the spots are) they came out as slivers, and to the surfaces facing sideways as
# half-moons: the nose's sides slope up
MARKS = (48, 162, 6)
# the black gap the head's fringe keeps round each mark, cm
MARK_GAP = 2.5
# the finishes, part by part
FINISH = dict(shell="gloss", spots="gloss", head="gloss", grass="satin", marks="gloss")


def top():
    return shapes.facing("up", 0.4, soft=0.006) & shapes.above(30)


def head():
    return shapes.field(lambda p, n: p[:, 2] - (HEAD_BACK + HEAD_CURVE * (p[:, 0] / HEAD_HALF) ** 2))


def design(s):
    s.clay()
    s.step("Silks", "Gloss red all over, big black blob spots over the top and on the rear flanks.", words=BLOBS)
    s.paint("body", FINISH["shell"], colour=RED)
    for k, (x, z, r) in enumerate(TOP):
        s.paint(OUTER, FINISH["spots"], colour=BLACK, zone=shapes.blob((x, 0, z), r, seed=k) & top())
    for k, (y, z, r) in enumerate(SIDE):
        s.paint(OUTER, FINISH["spots"], colour=BLACK, zone=shapes.blob((0, y, z), r, axis="x", seed=10 + k) & ~top())
    s.step("The head", "The nose black, as the ladybird's head, with two white blobs low on its sides.", words=HEAD)
    s.paint("body", FINISH["head"], colour=BLACK, zone=head())
    s.step("The grass", "Taller, denser turf-green blades rising up the lower sides, all round the car, "
           "under the black head too.", words=GRASS + " / " + AROUND)
    # all round. Ahead of the head's edge the nose floats: its black body's lower edge is 41 to 44
    # cm up, over the side skirt running forward as a flat ledge facing up (y 16 to 21) and the
    # wing's pylon. Blades from the ground only reached the nose as stray tips, and specks on the
    # pylon, so the ledge is a lawn under the head, solid (blades left black gaps across it), and
    # the head has its own fringe, rising from its lower edge
    s.paint("body", FINISH["grass"], colour=TURF, zone=shapes.grass(base=6, height=(18, 40), every=2.2, seed=7) & ~top() & ~head())
    s.paint("side skirt", FINISH["grass"], colour=TURF, zone=head())
    y, z, r = MARKS
    clear = ~shapes.blob((0, y, z), r + MARK_GAP, axis="x", seed=20)
    s.paint(NOSE, FINISH["grass"], colour=TURF, zone=shapes.grass(base=HEAD_LIP, height=(5, 11), every=2.0, seed=9) & ~top() & head() & clear)
    s.step("The head's marks", "Two white blobs on the sides of the black head.", words=HEAD)
    s.paint("body", FINISH["marks"], colour=WHITE, zone=shapes.blob((0, y, z), r, axis="x", seed=20) & head())
    s.step("Wheels", "Gloss black covers, like the ladybird's legs; plain black tyres with a wet-look shine.", words=WHEELS)
    s.paint("wheels", "satin", colour=BLACK)
    s.paint("wheel covers", "gloss", colour=BLACK)
    s.tyre_marks("TY-74")
    # the wheel rings' own light, on day and night (stock cyan), in warm white, like the head's marks
    s.relight("wheel ring", WHITE, keep_level=True)
    s.step("For now", "The inner car black: it gets its own step.", words=WORDS)
    s.paint("inner", "satin", colour=BLACK)
