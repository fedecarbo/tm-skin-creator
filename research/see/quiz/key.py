"""The answer key, computed from the mesh (not written by hand)."""
import sys
sys.path.insert(0, "/private/tmp/claude-501/-Users-fcarbo-Developer-personal-tm-skin-creator/d6323ffa-b930-4235-8278-bb2973c2c74f/scratchpad/see")
import json
import numpy as np
import ask
from tool import meshlines
P = ask.P
out = []
L = meshlines.named()["side skirt crease 2"]
p0, p1 = L["pts"][0], L["pts"][-1]
out.append(f"Q1: nose end {P(p0 if p0[2] > p1[2] else p1)}, tail end {P(p1 if p0[2] > p1[2] else p0)}; the course starts at the "
           f"{'NOSE' if p0[2] > p1[2] else 'TAIL'} end.")
deck = meshlines.line("body shell roll 2", tilt=33)
st = deck.between(deck.start, deck.at(z=-60))
zs = st.pts[:, 2]
out.append(f"Q2: z {zs.max():.0f} to {zs.min():.0f} ({st.length:.0f} cm): the BACK part (the roll runs z {deck.pts[:,2].max():.0f} to "
           f"{deck.pts[:,2].min():.0f}; its course starts at the tail end {P(deck.start)}).")
found, under = meshlines.near((70, 61, -26))
out.append(f"Q3: {under}; part: {meshlines.named()[under]['parts'][0]}.")
rooms = ask.rooms_cache()["rear flank"]
out.append("Q4: inside a flat room of the rear flank facing out, 25 cm or more across: " +
           "; ".join(f"{a:.0f} cm across centred {P(c)} facing {ask.facing_words(n)}" for a, c, n in rooms if a >= 25) +
           " (score: the centre within (across-25)/2 + 3 cm of a room's centre).")
pc = [p for p in ask.PIECES if "sidepod inlet" in p["parts"]][0]
out.append(f"Q5: STOPS: the sidepod inlet is a piece of its own, a gap of {pc['gap_cm']:.1f} cm to the {pc['nearest']}.")
seam = meshlines.named()["engine cover seam 2"]
out.append(f"Q6: YES: the number panel (the seam runs along {', '.join(seam['parts'])}; the number panel spans z -78 to -62, keep clear "
           f"within 3 cm): the judge blocks it / the mark is refused or moved.")
out.append("Q7: " + " ".join(ask.ask_paint("wheels")))
best = [(n, r) for n, r in meshlines.named().items() if not isinstance(r, list) and ask.kind_of(n) != "panel"
        and r["parts"][0] == "side skirt" and not r["closed"] and abs(r["pts"][:, 2].max() - 149) < 6 and abs(r["pts"][:, 2].min() - 17) < 6]
out.append("Q8: " + "; ".join(f"{n}, {r['length']:.0f} cm" for n, r in best))
inlet = [p for p in ask.PARTS if p["name"] == "sidepod inlet"]
from tool import surface
S = surface.load()
tris = np.isin(S.part, [p["id"] for p in inlet])
V = S.V[S.F[tris]].reshape(-1, 3)
out.append(f"Q9: IN FRONT (nearer the nose): the sidepod inlet spans z {V[:,2].max():.0f} to {V[:,2].min():.0f} and faces forward; its "
           f"opening is at its front (z about {V[:,2].max():.0f}), ahead of z -26.")
own = [p for p in ask.PIECES if p["gap_cm"] > 1.0]
out.append("Q10: " + "; ".join(f"{', '.join(p['parts'])}: {p['gap_cm']:.1f} cm" for p in own) + ".")
print("\n".join(out))
open("/private/tmp/claude-501/-Users-fcarbo-Developer-personal-tm-skin-creator/d6323ffa-b930-4235-8278-bb2973c2c74f/scratchpad/see/quiz/key.md", "w").write("\n".join(out))
