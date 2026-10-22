"""dryrun: a design read against the car before any paint. A throwaway sample (2026-10-22), not the tool.

    PY dryrun.py <skins/<name>/design.py or a skin's name> [--size 1024]

Runs the design on a small canvas (1024 by default: the geometry is the same, the texels are 16 times fewer), paints
nothing anyone sees, and says for every call where it landed: the stretch of the car (z front to back, y, x), the
parts under it, its area, the receipt's own words, and what the design meant by it (its step). Then a sketch:
see/out/dryrun_<name>.png, every call's texels on the side and top views, numbered.
"""
import importlib.util
import sys
import time
from pathlib import Path

import numpy as np
from PIL import ImageDraw

from tool import paintbox, paths

sys.path.insert(0, str(Path(__file__).resolve().parent))
import atlas  # noqa: E402

PALETTE = [(220, 40, 40), (30, 110, 220), (30, 160, 70), (230, 140, 0), (150, 50, 200), (0, 160, 170), (200, 30, 140),
           (120, 90, 30), (60, 60, 60), (240, 200, 0), (90, 170, 230), (170, 220, 60)]
SETS = {"Skin": "body", "Details": "inner car", "Wheels": "tyres", "Glass": "glass"}


def load(arg):
    p = Path(arg)
    if not p.exists():
        p = paths.SKINS / arg / "design.py"
    spec = importlib.util.spec_from_file_location(f"dry.{p.parent.name}", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return p.parent.name, mod.design


def extent(pos):
    lo, hi = pos.min(0), pos.max(0)
    side = "left side" if lo[0] > 1 else "right side" if hi[0] < -1 else "both sides" if lo[0] < -1 and hi[0] > 1 else "middle"
    return f"z {hi[2]:.0f} (front) to {lo[2]:.0f} (back), y {lo[1]:.0f} to {hi[1]:.0f}, x {lo[0]:.0f} to {hi[0]:.0f} ({side})"


def run(arg, size=1024):
    name, design = load(arg)
    t0 = time.time()
    s = paintbox.Skin(name, size=size)
    s.measure = True
    landed = []  # per op: {k, what, step, sets: {tset: (idx, pos, nrm, owners)}}

    def say(rec):
        k = s._op
        sets = {}
        for tset, c in s.canvases.items():
            if c.owner is None:
                continue
            idx = np.flatnonzero(c.owner == k)
            if len(idx):
                pos = np.asarray(c.pos).reshape(-1, 3)[idx]
                nrm = np.asarray(c.nrm).reshape(-1, 3)[idx]
                own = c.owners[idx]
                area = float(np.asarray(c.texel_area)[idx].sum())
                sets[tset] = (idx, pos, nrm, own, area)
        landed.append({"k": k, "what": rec.what, "step": rec.step, "rec": str(rec), "sets": sets})

    s.say = say
    design(s)
    took = time.time() - t0
    try:
        clay = s.still_clay()
    except Exception as e:  # noqa: BLE001
        clay = f"(couldn't tell: {e})"
    lines = [f"{name}: read against the car in {took:.0f} s at {size}² (nothing painted for anyone to see)."]
    step = None
    for L in landed:
        if L["step"] != step:
            step = L["step"]
            lines.append(f"\nStep: {step}")
        lines.append(f"  [{L['k'] + 1}] {L['what']}")
        for tset, (idx, pos, nrm, own, area) in L["sets"].items():
            parts_ = {}
            for i in own:
                if i >= 0:
                    nm = s.parts.instances[i]["name"]
                    parts_[nm] = parts_.get(nm, 0) + 1
            top = sorted(parts_.items(), key=lambda kv: -kv[1])
            total = max(1, sum(parts_.values()))
            who = ", ".join(f"{nm} ({n * 100 / total:.0f} %)" for nm, n in top[:5]) + (f" and {len(top) - 5} more" if len(top) > 5 else "")
            lines.append(f"      lands on the {SETS.get(tset, tset)}: {extent(pos)}; {area:,.0f} cm²; on: {who}")
            n = nrm / np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-9)
            faces = []
            for v, pos_w, neg_w in ((n[:, 1], "up", "down"), (n[:, 0], "left", "right"), (n[:, 2], "forward", "back")):
                if (v > 0.5).mean() > 0.3:
                    faces.append(pos_w)
                if (v < -0.5).mean() > 0.3:
                    faces.append(neg_w)
            if faces:
                lines[-1] += f"; faces {', '.join(faces)}"
        if not L["sets"]:
            r = L["rec"].split("\n")[0]
            if "(inner car)" in r or "(tyres)" in r or "(glass)" in r:
                lines.append("      lands off the body (the inner car, the tyres or the glass): the receipt says which parts")
            elif "nothing painted" in r:
                lines.append("      LANDS NOWHERE: nothing painted")
            else:
                lines.append("      covers no texel by half or more (a thin blend, a glow, a tyre marking)")
        rec = L["rec"].split("\n")
        lines.append(f"      receipt: {rec[0]}")
        for extra in rec[1:]:
            lines.append(f"               {extra.strip()}")
    lines.append(f"\nStill in clay: {clay if clay else 'nothing'}")
    sketch = draw(name, landed)
    lines.append(f"Sketch: {sketch}")
    return "\n".join(lines)


def draw(name, landed):
    side, top = atlas.Sheet(atlas.VIEWS["side"], 4.0, pad=20), atlas.Sheet(atlas.VIEWS["top"], 4.0, pad=20)
    for sh in (side, top):
        sh.body(shade=False)
    legend = []
    for j, L in enumerate(landed):
        col = PALETTE[j % len(PALETTE)]
        if "Skin" not in L["sets"]:
            continue
        idx, pos, nrm, own, area = L["sets"]["Skin"]
        if area > 12000:  # a coat over most of the body: said, not drawn, so the graphics show
            legend.append((str(L["k"] + 1), f"{L['what']}  ({area:,.0f} cm²: a coat over the body, not drawn)", (200, 200, 200)))
            continue
        if len(pos) > 400000:
            pick = np.random.default_rng(1).choice(len(pos), 400000, replace=False)
            pos, nrm = pos[pick], nrm[pick]
        for sh in (side, top):
            vis = (nrm @ sh.view.cam) > 0.05
            if not vis.any():
                continue
            q = sh.px(pos[vis])
            sh.d.point([tuple(p) for p in q], fill=col)
            c = q.mean(0)
            sh.tag(tuple(c), str(L["k"] + 1), col, size=13)
        legend.append((str(L["k"] + 1), f"{L['what']}  ({area:,.0f} cm²)", col))
    from PIL import Image
    w = max(side.im.width, top.im.width)
    h = side.im.height + top.im.height + 20 * (len(legend) + 2)
    im = Image.new("RGB", (w, h), (255, 255, 255))
    im.paste(side.im, (0, 0))
    im.paste(top.im, (0, side.im.height))
    d = ImageDraw.Draw(im)
    y = side.im.height + top.im.height + 4
    d.text((8, y), f"{name}: where each call lands, before the paint (side and top; each call's texels in its colour, numbered)",
           font=atlas.font(14), fill=(0, 0, 0))
    y += 20
    for tag, words, col in legend:
        d.rectangle([8, y + 3, 26, y + 15], fill=col)
        d.text((32, y), f"{tag}: {words}", font=atlas.font(13), fill=(20, 20, 20))
        y += 20
    atlas.OUT.mkdir(exist_ok=True)
    f = atlas.OUT / f"dryrun_{name}.png"
    im.save(f)
    return f


if __name__ == "__main__":
    a = sys.argv[1:]
    size = int(a[a.index("--size") + 1]) if "--size" in a else 1024
    print(run(a[0], size))
