"""The tool's self-test: does this code still paint every skin exactly as an earlier commit did?

    python -m tool.selftest --against <ref>             the representative set (SET), old and new
    python -m tool.selftest --against <ref> SelfTest_Tour   only the skins named
    python -m tool.selftest --against <ref> --all       every design, and the tour
    python -m tool.selftest --against <ref> --snap      the viewer's sheets of SNAP too, pixel for pixel
    python -m tool.selftest --against <ref> --at <ref2> <ref2>'s code instead of the working tree's
    python -m tool.selftest                             this code alone: paint, encode, time

Run it before and after any change to the tool. Each skin is painted in a fresh process, from the
code in the working tree and from <ref>'s code, extracted by `git archive` into the work folder
(never the repo: the PC's is in OneDrive). Per texture it compares the painted floats, the uint8
image the viewer and install take, and the whole DDS file the game reads; per skin, the notes, the
lines drawn, the palette, the steps and the parts left in clay. A difference is shown texel by
texel, by painting that skin again on both sides.

A commit's results are kept in the work folder (selftest/<commit>/), so each side is paid for once
per computer: a minute or two a skin. The working tree's are painted afresh
every run. Both sides share the work folder's caches, so a change to what a cache
holds must change the cache's name or version, or the old side reads the new cache and agrees.
"""

import argparse
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import time
from pathlib import Path

from tool import paths

# Together they use every part of the paint box: the user's car (peel, relief, emboss, glows, relit
# lights, a library finish, the canvas by hand) and TOUR, a test car of the self-test's own that
# makes every other call once.
SET = ("TSC_CMYK_EndsInK", "SelfTest_Tour")
TOUR = "SelfTest_Tour"
SNAP = ("TSC_CMYK_EndsInK",)
HOME = paths.WORK / "selftest"
OLD = 946684800  # 2000-01-01: the old code's files predate every cache, so none rebuilds for them

# The tour: clay, steps, a fade, zones by facing and height, a noise pattern, wear, the car map's
# areas, air, lines and edges, grass, a blob, lines drawn on the skin, a decal, a scatter, a print,
# lettering, a camo pattern, fabric, glows, a relit light, glass, dirt, a wheel ring, tyre markings
# and a tread. Its pictures are drawn here, so it needs no stored art.
TOUR_CODE = r'''
def tour(s):
    from pathlib import Path
    from PIL import Image, ImageDraw
    from tool import shapes, skindraw, textures
    pic = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(pic)
    d.ellipse((16, 16, 240, 240), fill=(250, 200, 30, 255), outline=(20, 20, 20, 255), width=14)
    d.polygon([(128, 50), (200, 200), (56, 200)], fill=(200, 30, 60, 255))
    tile = Path(out).with_suffix(".tile.png")
    t = Image.new("RGB", (256, 256), (30, 110, 160))
    ImageDraw.Draw(t).ellipse((64, 64, 192, 192), fill=(240, 240, 230))
    t.save(tile)
    s.clay()
    s.step("Base", "A base, a fade, a split by facing and height, a stripe, splashes and wear.")
    s.paint("body", "gloss red")
    under = s.keep()
    s.paint("body", "candy teal", zone=shapes.fade("z", 120, -150, curve=0.8))
    s.paint("body", "matte black", zone=shapes.facing("up", 0.4, soft=0.006) & shapes.above(30))
    s.paint("body", "splatter", palette=["keep", "hot pink", "lemon"], scale=9, zone=shapes.along(0.6, 0.8))
    s.paint("nose fin", "satin", colour="#e02020", zone=shapes.stripe(4))
    s.wear(under, fade=0.3, chips=0.08, scrapes=0.05, clearcoat=0.2)
    s.step("The map", "The car map's areas, its air, its lines, grass and a blob.")
    s.paint("body", "satin", colour="#f4f2ec", zone=shapes.area("top") & shapes.outside(0.4) & shapes.along(0.2, 0.4))
    s.paint("body", "satin", colour="#9fc3e6", zone=shapes.streamlines(shapes.front_rake(np.arange(3, 84, 12)), 1.2))
    s.paint("body", "satin", colour="#d0208e", zone=shapes.streamlines(shapes.rake(150, [1.35]), 1.2))
    s.paint("body", "satin", colour="#1f8f3a", zone=shapes.line("shoulder", 1.6))
    s.paint("body", "satin", colour="#2e7d32", zone=shapes.grass(base=6, height=(18, 30), every=3.0, seed=7))
    s.paint("body", "gloss", colour="#111111", zone=shapes.blob((30, 0, 60), 9, seed=1))
    s.step("Lines", "A sweep of three colours drawn on the skin, on both sides.")
    sweep = skindraw.through([(20.5, 43.7, 172.2, "side"), (32.1, 50.9, 99.6, "side"), (52.8, 61.4, 12.9, "side"),
                              (59.4, 54.4, -94.1, "side")], name="the sweep", smooth=40)
    for mm, colour in ((20, "#e0a82e"), (0, "#e8601c"), (-20, "#c8102e")):
        line = skindraw.parallel(sweep, mm, name=f"the sweep at {mm} mm")
        for curve in (line, skindraw.mirror(line)):
            s.paint("body", "satin", colour=colour, zone=skindraw.band(curve, 16))
    s.step("Pictures", "A decal, a scatter, a print and lettering.")
    s.decal(pic, "bonnet", width=30)
    s.scatter(pic, "engine cover", size=6, seed=3)
    textures.add_file("selftest tile", tile, 20, about="the self-test's tile")
    s.paint("rear flank", "selftest tile")
    s.text("TOUR 7", "left side", colour="black", font="russo", height=10, outline="white")
    s.step("Details", "The inner car, glass, dirt, glows, a light and the tyres.")
    s.paint("inner", "camo matte", palette=["charcoal", "slate", "light grey", "jet black"], scale=26)
    s.paint("seat", "cloth", colour="charcoal")
    s.glow("rear strake", "ice blue")
    s.relight("wheel ring", "#e0a82e", keep_level=True)
    s.glass("plum", 0.5)
    s.dirt(1.3)
    s.paint("sidewall", "satin", colour="#e0a82e", zone=shapes.wheel_ring(31.8, 32.6))
    s.tyre_marks("TY-26", colour="#e0a82e")
    s.tyre_tread("TR-04")
'''
# A kept result of the tour is the tour's as it was then: its file is named by the tour's code.
TOUR_KEY = hashlib.sha256(TOUR_CODE.encode()).hexdigest()[:10]

# What runs in each fresh process, from the code tree it's started in. Only calls both sides have.
CHILD = r'''
import hashlib, json, re, sys, time
import numpy as np
from tool import dds, paintbox, skin

name, out = sys.argv[1], sys.argv[2]
dump = sys.argv[3] if len(sys.argv) > 3 else None
sha = lambda b: hashlib.sha256(b).hexdigest()[:20]
''' + TOUR_CODE + r'''
t0 = time.time()
with skin.paint_slot():
    t = time.time()
    if name == "SelfTest_Tour":
        s = paintbox.Skin(name)
        tour(s)
        s.end_steps()
    else:
        s = skin.paint(name)
    painted = time.time() - t
t = time.time()
textures, arrays = {}, {}
for tex, (arr, fourcc, opts) in sorted(s.textures().items()):
    arr = np.asarray(arr)
    u8 = np.clip(np.rint(arr * 255), 0, 255).astype(np.uint8)   # as save_painted rounds
    img = u8.astype(np.float32) / 255                            # as build_zip reads it back
    blob = dds.encode(dds.build_mips(img[..., None] if img.ndim == 2 else img, **opts), fourcc)
    textures[tex] = {"shape": list(arr.shape), "dtype": str(arr.dtype), "fourcc": fourcc,
                     "float": sha(np.ascontiguousarray(arr).tobytes()), "u8": sha(u8.tobytes()), "dds": sha(blob)}
    if dump:
        arrays[tex] = u8
        arrays[tex + ".dds"] = np.frombuffer(blob, np.uint8)
if dump:
    np.savez(dump, **arrays)
record = {"drawn": s.drawn, "palette": s.palette, "icon": s.icon_colours,
          "steps": [{"name": st["name"], "paints": st.get("paints", [])} for st in s.steps],
          "clay": s.clay_left}
notes = [re.sub(r"\(\d+ s\)", "(… s)", n) for n in s.notes]  # how long a step took isn't the paint
json.dump({"textures": textures, "record": sha(json.dumps(record, sort_keys=True, default=str).encode()),
           "notes": notes, "seconds": {"paint": round(painted, 1), "encode": round(time.time() - t, 1),
                                       "total": round(time.time() - t0, 1)}}, open(out, "w"), indent=1)
'''

SNAP_CHILD = r'''
import sys
from pathlib import Path
from tool import snap, view
name, folder = sys.argv[1], Path(sys.argv[2])
view.prepare(name)
for kind, shots, size, query in (("views", snap.SHOTS, (960, 720), ""), ("close", snap.CLOSE, (960, 720), ""),
                                 ("cams", snap.CAMS, (1280, 720), "lens=game")):
    snap.snap(name, out=folder / f"{name}_{kind}.png", size=size, shots=shots, prepare=False, query=query)
'''


def git(*args):
    return subprocess.run(["git", "-C", str(paths.REPO), *args], capture_output=True, check=True).stdout


def tree(ref):
    """<ref>'s code, extracted once into the work folder: (commit, folder)."""
    commit = git("rev-parse", "--verify", f"{ref}^{{commit}}").decode().strip()
    folder = HOME / commit[:12] / "tree"
    if not (folder / "tool").exists():
        print(f"extracting {ref} ({commit[:12]})...", flush=True)
        tmp = folder.with_name("tree.tmp")
        shutil.rmtree(tmp, ignore_errors=True)
        blob = git("archive", commit, "--", "tool", "car", "viewer", "skins",
                   ":(exclude)skins/*/versions", ":(exclude)skins/*/sets")
        with tarfile.open(fileobj=io.BytesIO(blob)) as t:
            t.extractall(tmp, filter="data")
        for p in tmp.rglob("*"):
            os.utime(p, (OLD, OLD))
        tmp.rename(folder)
    return commit, folder


def child(script, cwd, log, *args):
    """Runs a script in a fresh process with `tool` imported from cwd, its output into log. None
    when it worked, else {"error": its last line}."""
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env["PYTHONHASHSEED"] = "0"
    with open(log, "w") as f:
        r = subprocess.run([sys.executable, "-B", "-c", script, *args], cwd=cwd, env=env,
                           stdout=f, stderr=subprocess.STDOUT)
    if r.returncode:
        tail = log.read_text(errors="replace").strip().splitlines()[-1:] or ["(no output)"]
        return {"error": tail[0]}
    return None


def paint(name, cwd, folder, keep):
    """One skin's results from the code at cwd, from folder if kept there already."""
    out = folder / (f"{name}-{TOUR_KEY}.json" if name == TOUR else f"{name}.json")
    if keep and out.exists():
        return json.loads(out.read_text())
    folder.mkdir(parents=True, exist_ok=True)
    failed = child(CHILD, cwd, out.with_suffix(".log"), name, str(out))
    if failed:
        out.unlink(missing_ok=True)
        return failed
    return json.loads(out.read_text())


def same(a, b):
    """How two results of one skin differ: (the textures that differ, other differences in words)."""
    if "error" in a or "error" in b:
        return [], [] if a.get("error") == b.get("error") else [f"error: {a.get('error')} / {b.get('error')}"]
    textures = [f"{t}: only one side has it" for t in sorted(set(a["textures"]) ^ set(b["textures"]))]
    for t in sorted(set(a["textures"]) & set(b["textures"])):
        x, y = a["textures"][t], b["textures"][t]
        bad = [k for k in ("shape", "dtype", "fourcc", "float", "u8", "dds") if x[k] != y[k]]
        if bad:
            textures.append(f"{t}: {', '.join(bad)} differ")
    other = []
    if a["notes"] != b["notes"]:
        gone = [f"- {n}" for n in a["notes"] if n not in b["notes"]]
        new = [f"+ {n}" for n in b["notes"] if n not in a["notes"]]
        other.append("notes differ:\n      " + "\n      ".join(gone + new))
    if a["record"] != b["record"]:
        other.append("the record differs (lines drawn, palette, steps, clay)")
    return textures, other


def detail(name, old_cwd, new_cwd):
    """Paints the skin again on both sides and says how far each texture is from the other."""
    import numpy as np
    tmp = HOME / "detail"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    for side, cwd in (("old", old_cwd), ("new", new_cwd)):
        failed = child(CHILD, cwd, tmp / f"{side}.log", name, str(tmp / f"{side}.json"), str(tmp / f"{side}.npz"))
        if failed:
            print(f"    {side}: {failed['error']}")
            return
    a, b = np.load(tmp / "old.npz"), np.load(tmp / "new.npz")
    for t in sorted(set(a.files) & set(b.files)):
        x, y = a[t], b[t]
        if x.shape != y.shape:
            print(f"    {t}: {x.shape} / {y.shape}")
        elif not np.array_equal(x, y):
            d = np.abs(x.astype(np.int16) - y.astype(np.int16))
            what = "bytes" if t.endswith(".dds") else "values"
            print(f"    {t}: {int((d > 0).sum())} {what} differ, by up to {int(d.max())}")
    shutil.rmtree(tmp, ignore_errors=True)


def snapshots(names, old_cwd, new_cwd, commit):
    """The viewer's sheets (views, close looks, the game's cameras) from both sides' viewer code,
    over the same skin data, compared pixel for pixel."""
    from PIL import Image, ImageChops
    ok = True
    for name in names:
        folders = {"old": HOME / commit[:12] / "snap", "new": HOME / "live" / "snap"}
        for side, cwd in (("old", old_cwd), ("new", new_cwd)):
            folders[side].mkdir(parents=True, exist_ok=True)
            failed = child(SNAP_CHILD, cwd, folders[side] / f"{name}.log", name, str(folders[side]))
            if failed:
                print(f"  {name} ({side}): {failed['error']}")
                ok = False
        for kind in ("views", "close", "cams"):
            a, b = (folders[s] / f"{name}_{kind}.png" for s in ("old", "new"))
            if not (a.exists() and b.exists()):
                continue
            box = ImageChops.difference(Image.open(a).convert("RGB"), Image.open(b).convert("RGB")).getbbox()
            print(f"  {name} {kind}: {'identical' if box is None else f'differs within {box}'}")
            ok &= box is None
    return ok


def designs():
    return sorted(p.parent.name for p in paths.SKINS.glob("*/design.py"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("skins", nargs="*", help="the skins to test (the representative set if none)")
    ap.add_argument("--against", metavar="REF", help="the commit to compare with")
    ap.add_argument("--at", metavar="REF", help="test this commit's code instead of the working tree's")
    ap.add_argument("--all", action="store_true", help="every design")
    ap.add_argument("--snap", action="store_true", help="the viewer's sheets too, pixel for pixel")
    args = ap.parse_args()
    names = args.skins or (designs() + [TOUR] if args.all else list(SET))
    old_cwd = commit = None
    if args.against:
        commit, old_cwd = tree(args.against)
    new_cwd, live, fresh = paths.REPO, HOME / "live", True
    if args.at:
        at, new_cwd = tree(args.at)
        live, fresh = HOME / at[:12], False
    print(f"{len(names)} skins" + (f" at {args.at}" if args.at else "")
          + (f", against {args.against} ({commit[:12]})" if commit else ""), flush=True)
    differing = []
    for name in names:
        new = paint(name, new_cwd, live, keep=not fresh)
        if "error" in new:
            print(f"{name:<40} new: FAILED {new['error']}", flush=True)
            differing.append(name)
            continue
        line = f"{name:<40} paint {new['seconds']['paint']:>5.1f} s  encode {new['seconds']['encode']:>5.1f} s"
        if commit:
            if not (old_cwd / "skins" / name / "design.py").exists() and name != TOUR:
                print(f"{line}  (new since {args.against})", flush=True)
                continue
            old = paint(name, old_cwd, HOME / commit[:12], keep=True)
            textures, other = same(old, new)
            if "seconds" in old:
                line += f"   was {old['seconds']['paint']:>5.1f} s / {old['seconds']['encode']:>5.1f} s"
            print(f"{line}  {'DIFFERENT' if textures or other else 'identical'}", flush=True)
            for d in textures + other:
                print(f"    {d}")
            if textures or other:
                differing.append(name)
            if textures:
                detail(name, old_cwd, new_cwd)
        else:
            print(line, flush=True)
    if args.snap and commit:
        print("snapshots:", flush=True)
        if not snapshots(SNAP, old_cwd, new_cwd, commit):
            differing.append("snapshots")
    if commit:
        print("\nall identical" if not differing else f"\ndifferent: {', '.join(differing)}")
    sys.exit(1 if differing else 0)


if __name__ == "__main__":
    main()
