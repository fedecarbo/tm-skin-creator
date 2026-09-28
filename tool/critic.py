"""The studio's critic (CHECKLIST.md, "The design studio", W2): the pictures it's given, and what it
found, kept as the car's review. The critic itself is an agent, .claude/agents/critic.md: it sees only
the car's pictures and its brief, never the design, the notes or the designer's reasons (studio.md, 9).

    python -m tool.critic pictures <car> [--sheets DIR] [--out DIR]
        the car's four sheets (views, close, review, cams: tool.snap) cut into one picture per view,
        named by its label, for the critic to read whole. On the PC from the work folder's build/
        into build/critic/<car>/<round>/; on the Mac in the container, from and to the repo's .snap/
        (--sheets /app/.snap --out /app/.snap/critic/<car>/<round>). Prints the folder.
    python -m tool.critic keep <car> <reply.json> [--critic <model>] [--pictures <folder>]
        the critic's reply as the review's next round: its verdict, its new findings (numbered on from
        the last), and on a re-check its word on the earlier ones
    python -m tool.critic mark <car> <n> fixed|left "<what was done, or why it stays>"
    python -m tool.critic picture <car> <folder> <out.png> [--round N] [--after <folder>]
        the round's findings for the user: each one's picture with a ring where the critic pointed,
        and with --after the next round's picture of the same view beside it (the before and after)
    python -m tool.critic <car>                               the review so far

skins/<car>/review.json: {"car", "rounds": [{"n", "date", "critic", "pictures", "verdict"}],
"findings": [{"n", "round", "where", "picture", "at", "also", "what", "why", "severity", "sure",
"status", "how", "recheck"}]}. A finding's picture is the file the critic named in that round's
folder, "at" the point it meant (x, y as shares of the picture from its top-left), so the same view
in the next round's folder is the after. severity: fix (a flaw), improve (clearly better), brief (it
goes against the brief: said to the user, changed only if they want). status: open, fixed or left
(Claude's); recheck: the critic's word on it in a later round (fixed, not fixed, partly).

keep, mark and the printout are standard library only, so they run with the Mac's own python3, as
tool.sheet does; pictures and picture need Pillow (the PC's venv, the Mac's container).
TSC_SKINS_HOME puts the skins elsewhere, for tests."""

import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKINS = Path(os.environ.get("TSC_SKINS_HOME") or REPO / "skins")
NAME = re.compile(r"[A-Za-z0-9_\-]+")
KINDS = ("views", "close", "review", "cams")  # the sheets, in the order the critic reads them
SEVERITY = ("fix", "improve", "brief")
RECHECK = ("fixed", "not fixed", "partly")


class CriticError(Exception):
    pass


def path(car):
    if not NAME.fullmatch(car or ""):
        raise CriticError(f"not a skin's name: {car!r}")
    return SKINS / car / "review.json"


def load(car):
    p = path(car)
    return json.loads(p.read_text("utf-8")) if p.exists() else {"car": car, "rounds": [], "findings": []}


def save(review):
    p = path(review["car"])
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(review, indent=1, ensure_ascii=False) + "\n", "utf-8")
    os.replace(tmp, p)


def slug(label):
    return re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")


def pictures(car, sheets=None, out=None):
    """Cut the car's sheets into single pictures: <out>/<kind>-<label>.png. Returns the folder."""
    from PIL import Image

    from tool import paths, snap
    shots = {"views": snap.SHOTS, "close": snap.CLOSE, "review": snap.REVIEW, "cams": snap.CAMS}
    sheets = Path(sheets or paths.BUILD)
    out = Path(out or paths.BUILD / "critic" / car / str(len(load(car)["rounds"]) + 1))
    missing = [k for k in KINDS if not (sheets / f"{car}_{k}.png").exists()]
    if missing:
        raise CriticError(f"no {', '.join(missing)} sheet for {car} in {sheets}: take them first (tool.snap)")
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.png"):
        old.unlink()
    for kind in KINDS:
        im = Image.open(sheets / f"{car}_{kind}.png")
        labels = [s[0] for s in shots[kind]]
        rows = (len(labels) + 2) // 3
        w, h = im.width // 3, im.height // rows
        for k, label in enumerate(labels):
            im.crop(((k % 3) * w, (k // 3) * h, (k % 3 + 1) * w, (k // 3 + 1) * h)).save(out / f"{kind}-{slug(label)}.png")
    print(out)
    return out


def picture(car, folder, out, rnd=None, after=None):
    """The findings for the user: each finding's picture from its round's folder with a ring where
    the critic pointed and its words under it, three to a row; with after (a later round's folder)
    the same view beside it. rnd: one round's findings (the last by default). Returns the path."""
    import textwrap

    from PIL import Image, ImageDraw

    from tool import snap
    review = load(car)
    rnd = rnd or len(review["rounds"])
    found = [f for f in review["findings"] if f["round"] == rnd]
    if not found:
        raise CriticError(f"{car}'s review has no findings in round {rnd}")
    folder, w, h, band = Path(folder), 640, 480, 250
    cells = []
    for f in found:
        tiles = [(folder, f["picture"])] + ([(Path(after), f["picture"])] if after else [])
        for k, (d, name) in enumerate(tiles):
            im = Image.open(d / name).convert("RGB").resize((w, h))
            if f.get("at") and k == 0:
                x, y = f["at"][0] * w, f["at"][1] * h
                ImageDraw.Draw(im).ellipse((x - 34, y - 34, x + 34, y + 34), outline=(255, 214, 0), width=5)
            head = f"{f['n']}  {f['where']}" if k == 0 else "after"
            body = f["what"] if k == 0 else (f["recheck"] or {}).get("note", "")
            tag = f"{f['severity']}, {f['status']}" if k == 0 else ""
            cells.append((im, head, body, tag))
    cols = 2 if after else 3
    rows = (len(cells) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * w, rows * (h + band)), (24, 24, 26))
    draw, font, small = ImageDraw.Draw(sheet), snap._font(21), snap._font(17)
    for i, (im, head, body, tag) in enumerate(cells):
        x, y = (i % cols) * w, (i // cols) * (h + band) + h + 10
        sheet.paste(im, (x, y - h - 10))
        for line in textwrap.wrap(head, 50)[:2]:
            draw.text((x + 12, y), line, fill=(255, 214, 0), font=font)
            y += 26
        for line in textwrap.wrap(body, 64)[:7]:
            draw.text((x + 12, y + 2), line, fill=(225, 225, 225), font=small)
            y += 22
        if tag:
            draw.text((x + 12, y + 8), tag, fill=(150, 150, 155), font=small)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    print(out)
    return out


def keep(car, reply, critic=None, folder=None):
    """The critic's reply ({"verdict", "findings": [...]}, a re-check's with "n" and "status") as a round."""
    review = load(car)
    rnd = len(review["rounds"]) + 1
    if not isinstance(reply, dict) or not isinstance(reply.get("findings"), list):
        raise CriticError("the reply needs a verdict and a list of findings")
    known = {f["n"]: f for f in review["findings"]}
    new = []
    for f in reply["findings"]:
        if "status" in f:  # its word on an earlier finding
            if f.get("n") not in known:
                raise CriticError(f"the re-check names finding {f.get('n')}, which isn't in the review")
            if f["status"] not in RECHECK:
                raise CriticError(f"a re-check says fixed, not fixed or partly, not {f['status']!r}")
            known[f["n"]]["recheck"] = {"round": rnd, "status": f["status"], "note": f.get("what", "")}
            continue
        for k in ("where", "picture", "what", "severity"):
            if not f.get(k):
                raise CriticError(f"a finding without {k}: {f}")
        if f["severity"] not in SEVERITY:
            raise CriticError(f"severity is fix, improve or brief, not {f['severity']!r}")
        new.append(f)
    n = max(known, default=0)
    for f in new:
        n += 1
        review["findings"].append({"n": n, "round": rnd, "where": f["where"], "picture": f["picture"],
                                   "at": f.get("at"), "also": f.get("also", []), "what": f["what"],
                                   "why": f.get("why", ""), "severity": f["severity"], "sure": f.get("sure", ""),
                                   "status": "open", "how": "", "recheck": None})
    review["rounds"].append({"n": rnd, "date": datetime.date.today().isoformat(), "critic": critic or "",
                             "pictures": folder or "", "verdict": reply.get("verdict", "")})
    save(review)
    return review, len(new)


def mark(car, n, status, how):
    review = load(car)
    if status not in ("fixed", "left"):
        raise CriticError("a finding is marked fixed or left")
    for f in review["findings"]:
        if f["n"] == n:
            f["status"], f["how"] = status, how
            save(review)
            return f
    raise CriticError(f"{car}'s review has no finding {n}")


def show(car):
    review = load(car)
    if not review["rounds"]:
        return f"{car}: no review yet"
    lines = [f"{car}'s review, {len(review['rounds'])} round(s)"]
    for r in review["rounds"]:
        lines.append(f"  round {r['n']} ({r['date']}, {r['critic'] or 'the critic'}): {r['verdict']}")
    for f in review["findings"]:
        re_ = f" (critic, round {f['recheck']['round']}: {f['recheck']['status']})" if f.get("recheck") else ""
        lines.append(f"  {f['n']:>2} [{f['severity']}] {f['status']}{re_}: {f['where']}: {f['what']}")
        if f["how"]:
            lines.append(f"       {f['how']}")
    return "\n".join(lines)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    ap = argparse.ArgumentParser(prog="python -m tool.critic")
    if argv and argv[0] in ("pictures", "picture", "keep", "mark"):
        sub = ap.add_subparsers(dest="cmd")
        p = sub.add_parser("pictures")
        p.add_argument("car")
        p.add_argument("--sheets")
        p.add_argument("--out")
        p = sub.add_parser("picture")
        p.add_argument("car")
        p.add_argument("folder")
        p.add_argument("out")
        p.add_argument("--round", type=int)
        p.add_argument("--after")
        p = sub.add_parser("keep")
        p.add_argument("car")
        p.add_argument("reply")
        p.add_argument("--critic")
        p.add_argument("--pictures")
        p = sub.add_parser("mark")
        p.add_argument("car")
        p.add_argument("n", type=int)
        p.add_argument("status")
        p.add_argument("how")
    else:
        ap.add_argument("car")
    args = ap.parse_args(argv)
    try:
        if getattr(args, "cmd", None) == "pictures":
            pictures(args.car, args.sheets, args.out)
        elif getattr(args, "cmd", None) == "picture":
            picture(args.car, args.folder, args.out, args.round, args.after)
        elif getattr(args, "cmd", None) == "keep":
            text = Path(args.reply).read_text("utf-8")
            block = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)  # the reply's JSON, fenced or bare
            _, added = keep(args.car, json.loads(block[-1] if block else text), args.critic, args.pictures)
            print(f"{args.car}: round kept, {added} new finding(s)")
            print(show(args.car))
        elif getattr(args, "cmd", None) == "mark":
            f = mark(args.car, args.n, args.status, args.how)
            print(f"{args.car}: {f['n']} {f['status']}")
        else:
            print(show(args.car))
    except CriticError as e:
        sys.exit(f"critic: {e}")


if __name__ == "__main__":
    main()
