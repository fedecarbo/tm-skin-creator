"""TSC_StealthBomber: a stealth bomber's darkness, finishes and quiet, every line from the car's own form (its visual
language: language.json). The composition, set 2's B: matte bomber grey, and tape grey tape laid along the car's own
leading edges, on the face the eye sees beside each (round the nose and on along the body's edge over the side openings,
all round the cockpit's outline, along the skirts' swept edges, round the intakes' lips), each ending where its line
ends. The surfaces (surfaces()):
the airframe in the skin's grey, black only inside the openings, the gear dark gunmetal, the tail's end cap in heat
tiles, plain tyres, every light in the tape's cool grey, and a hangar's patches."""

from tool import meshlines

SKIN, TAPE, HOLE, GOLD = "#3f4348", "#565b61", "#1b1d20", "#c9a24a"  # the language's colours
WORDS = "do a stealth bomber"


def base(s):
    """The skin, the openings, the gear and the canopy: the same in every take."""
    s.clay()
    s.step("The skin", "Bomber grey, matte, all over; black inside the intakes and the inner car; the gear dark "
           "gunmetal; the canopy's gold coating.", words=WORDS)
    s.paint("body", "matte", colour=SKIN)
    s.paint("sidepod inlet", "matte", colour=HOLE)  # the intakes' insides, whole
    s.paint("inner", "matte plastic", colour=HOLE)
    s.paint("wheels", "gunmetal")
    s.paint("canopy", colour=GOLD)  # the gold coating on the canopy alone


def design(s):
    base(s)
    s.step("The leading edges", "Tape grey satin, 4 cm wide, laid beside the car's own leading edges on the face the "
           "eye sees, its edge on the edge: round the nose's "
           "front and on back along the body's edge over the side openings, all round the cockpit's outline, "
           "along the skirts' swept edges on to the rear and round the intakes' lips.",
           words=WORDS)
    # one smooth line: over the right side opening along the body's crisp edge (the user traced it), easing up onto
    # the nose's rounded edge, round the nose where it shows, and back down onto the left's crisp edge: no step
    rim = meshlines.line((0, 40, 210), kind="rounded")  # round the nose, its right end first
    side = meshlines.line((25.9, 47.3, 139.8))  # the crisp edge over the left side opening
    back = [(36.3, 52.8, 69), (35.4, 53.0, 75), (33.4, 51.4, 89)] + [tuple(side.at(z=z)) for z in (110, 124, 138)]
    # the rim's middle only: its ends turn up towards the cockpit, and taking them made a hump at the seam
    front = [tuple(rim.at(s=k * rim.length / 12)) for k in range(2, 11)]
    nose = meshlines.picked([(-x, y, z) for x, y, z in back] + front + back[::-1]).band(4, side="seen")
    crest = meshlines.line((0, 83, -51)).band(4, side="seen")  # the whole outline round the cockpit, closed behind it
    # the skirts' swept edge and on along the body's lower edge under the sidepod to the rear (the user: "make this
    # tape continuous until the rear"), to where the rear flank's rounded edge ends by the rear wheel
    low = [(23.9, 17.9, 148.6), (39, 19, 70), (77.3, 21.8, 17.1), (81, 22.1, 4.8), (82.3, 22.4, -11),
           (81.9, 21.6, -24.8), (66, 19.1, -63.9), (53, 20, -86), (49.1, 18.3, -107.4)]
    skirts = meshlines.picked(low).band(4, side="seen") | meshlines.picked([(-x, y, z) for x, y, z in low]).band(4, side="seen")
    s.paint("body", "satin", colour=TAPE, zone=nose | crest | skirts)
    lips = meshlines.line((75, 49, -45)).mirrored().band(4, side="seen")
    s.paint("body", "satin", colour=TAPE, zone=lips, across=True)
    surfaces(s)


HEAT, RECOAT, FRESH = "#7a7c79", "#484c51", "#4d5258"  # the heat tiles; a panel recoated and fresh tape, a shade off
AIRFRAME = ["front wing", "floor", "wing bracket", "front bulkhead", "side vane", "mirror", "mirror arm", "antenna"]
GEAR = ["front suspension", "rear suspension", "brake caliper"]
LENSES = ["rear light lens", "side lens", "wing lens", "nose lens"]  # the nose lens: the glass in the nose's side slots


def surfaces(s):
    """Every part's finish from the language's surfaces, and how the car ages: kept clean, but patched."""
    s.step("The airframe and the gear", "The inner car's outside pieces (the front wing, the floor and its sill, "
           "the struts and keel under the nose, the side vanes, the mirrors) in the skin's matte bomber grey: black "
           "stays only inside the openings. The suspension and the brake calipers in the wheels' dark gunmetal, "
           "rough. The tail's end cap over the exhausts in heat tiles, dry ceramic.", words=WORDS)
    s.paint(AIRFRAME, "matte", colour=SKIN)
    s.paint(GEAR, "gunmetal matte")  # the wheels' metal, rough: from above, the arms would flash the sky
    s.paint(["tail panel", "tail corner"], "PA-05", colour=HEAT)
    s.step("The tyres", "Plain matte rubber in the shadow's dark, Nadeo's lettering off, its tread kept.", words=WORDS)
    s.paint("tyres", "rubber", colour=HOLE)
    s.tyre_tread("TR-01")
    s.step("Lights and lenses", "Every light of the car's own in the tape's cool grey, as quiet as a bomber at night: "
           "the speed numbers dimmed to the tape's grey, the wheel rings dark, the rear lights, "
           "the front wing's lights and the side lights behind smoked lenses, the nose's side slots smoked too.",
           words=WORDS, look="rear night")
    s.relight("inner", TAPE, keep_level=True)  # the stock lights' hue, each as bright as it was
    s.no_glow("wheel ring")
    s.relight("speed numbers", TAPE)
    s.paint(LENSES, colour=TAPE, blend=0.6)
    s.step("Kept, patched", "Kept clean in its hangar: one rear quarter panel recoated a shade off the rest, and "
           "the left intake's lip freshly taped, a shade off the old.", words=WORDS)
    s.paint("rear quarter panel|left", "matte", colour=RECOAT)
    s.paint("body", "satin", colour=FRESH, zone=meshlines.line((75, 49, -45)).band(4, side="seen"), across=True)
