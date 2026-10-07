"""A car's visual language, shown as a page before any paint (the user, 2026-10-07: "develop sort of a visual
language first, kind of like a brand book"; its layout, A of three, the brand book: a section per heading, top to
bottom). The routine around it is in .claude/skills/skin/language.md.

    python -m tool.language <name>             check skins/<name>/language.json, write its page, open it
    python -m tool.language <name> --no-open   just check and write

skins/<name>/language.json holds the car's answers to the same headings for every car. Each says how the car's
world looks and behaves, never where a thing goes on the car:

    idea, world        one sentence, and the world it comes from
    is, isnt           a few words for what it is, a few for what it isn't
    signature          {"says", "svg"}: the one move you'd recognise from far, and how it behaves on a body
    dna                {"says", "svg"}: the shape rules every mark is made from (lines, angles, corners,
                       proportions, line widths at three sizes, rhythm)
    colours, meet      [{"name", "colour" ("#rrggbb"), "share" (percent, all adding up to 100), "job"}], and how
                       two colours meet
    surfaces, ageing   [{"finish" (a Lab code, "PA-03", or a finish's name), "colour" (optional), "job"}], and
                       the texture and how it ages (or doesn't)
    sizes, fullness    {"large", "medium", "small"}: each {"what", "svg"}, the kind of thing that lives at that
                       size; and how full the car gets
    never              [what this language never does]
    lettering          optional: only when the user asked for words

Each svg is drawn flat, in the language's own colours, never on the car: a viewBox, any size (the page sets its
width). The page goes to the work folder (<work>/viewer/language/<name>.html, http://localhost:8765/data/language/
<name>.html); its surfaces are balls drawn from each finish's own numbers (tool/finishes.py), a hint: the finishes
are judged on the car.
"""

import argparse
import html
import json
import re
import sys

from tool import finishes, paths, server, view

FOLDER = view.DATA / "language"
HEX = re.compile(r"#[0-9a-fA-F]{6}")
SVG = re.compile(r"\s*<svg\b.*</svg>\s*", re.S)
UNSAFE = re.compile(r"<script|\son\w+\s*=|javascript:", re.I)
TEXT = ("idea", "world", "meet", "ageing", "fullness")


def page_url(name):
    return f"http://localhost:{server.PORT}/data/language/{name}.html"


def check(lang):
    """What's missing or wrong in a language, as lines; none when it's whole."""
    bad = [f"{key}: empty" for key in TEXT if not str(lang.get(key) or "").strip()]
    for key in ("is", "isnt", "never"):
        if not lang.get(key) or not all(str(w).strip() for w in lang[key]):
            bad.append(f"{key}: a list of a few words")
    for key in ("signature", "dna"):
        part = lang.get(key) or {}
        if not str(part.get("says") or "").strip():
            bad.append(f"{key}: says nothing")
        bad += _svg(f"{key}'s svg", part.get("svg"))
    colours = lang.get("colours") or []
    if not 2 <= len(colours) <= 8:
        bad.append("colours: two to eight")
    for c in colours:
        if not str(c.get("name") or "").strip() or not HEX.fullmatch(str(c.get("colour"))):
            bad.append(f"colours: {c.get('name')!r} needs a name and a #rrggbb")
        if not str(c.get("job") or "").strip():
            bad.append(f"colours: {c.get('name')!r} has no job")
    shares = [c.get("share") for c in colours]
    if not all(isinstance(s, (int, float)) and s > 0 for s in shares) or abs(sum(shares) - 100) > 1:
        bad.append(f"colours: the shares add up to 100 ({shares})")
    for s in lang.get("surfaces") or [{}]:
        try:
            finishes.get(str(s.get("finish") or ""))
        except KeyError:
            bad.append(f"surfaces: no finish {s.get('finish')!r} (a Lab code or a finish's name)")
        if s.get("colour") and not HEX.fullmatch(str(s["colour"])):
            bad.append(f"surfaces: {s.get('finish')!r}'s colour isn't #rrggbb")
        if not str(s.get("job") or "").strip():
            bad.append(f"surfaces: {s.get('finish')!r} has no job")
    sizes = lang.get("sizes") or {}
    for size in ("large", "medium", "small"):
        one = sizes.get(size) or {}
        if not str(one.get("what") or "").strip():
            bad.append(f"sizes: {size} says nothing")
        bad += _svg(f"sizes: {size}'s svg", one.get("svg"))
    return bad


def _svg(what, svg):
    if not isinstance(svg, str) or not SVG.fullmatch(svg):
        return [f"{what}: one <svg>…</svg>"]
    if UNSAFE.search(svg):
        return [f"{what}: no scripts or event handlers"]
    return []


def _ball(finish, colour):
    """A finish's ball in CSS: the highlight as tight and bright as its roughness allows, a metal's tinted."""
    rgb = tuple(int(colour[k:k + 2], 16) for k in (1, 3, 5))
    r, m = finish.roughness, finish.metalness
    glint = 0.12 + 0.8 * (1 - r) * (1 - 0.4 * m)
    light = ", ".join(str(round(c + (255 - c) * 0.6)) for c in rgb) if m > 0.5 else "255, 255, 255"
    dark = "#{:02x}{:02x}{:02x}".format(*(round(c * (0.35 if m > 0.5 else 0.5)) for c in rgb))
    return (f"radial-gradient(circle at 34% 30%, rgba({light}, {glint:.2f}) 0%, rgba({light}, 0) {3 + 30 * r:.0f}%), "
            f"radial-gradient(circle at 40% 36%, {colour} {10 + 25 * r:.0f}%, {dark} 100%)")


def render(name, lang):
    e = html.escape

    def sec(title, body):
        return f'<section><h2 class="teko">{title}</h2><div>{body}</div></section>'

    def ps(*texts):
        return "".join(f"<p>{e(str(t))}</p>" for t in texts if str(t or "").strip())

    ratio = "".join(f'<i style="flex:{c["share"]};background:{c["colour"]}"></i>' for c in lang["colours"])
    colours = "".join(f'<div class="row"><i style="background:{c["colour"]}"></i><b>{e(c["name"])}</b>'
                      f'<span>{c["share"]:g} % · {e(c["job"])}</span></div>' for c in lang["colours"])
    surfaces = ""
    for s in lang["surfaces"]:
        f = finishes.get(s["finish"])
        colour = s.get("colour") or ("#{:02x}{:02x}{:02x}".format(*(round(255 * c) for c in f.colour)) if f.colour
                                     else "#8c8f94")
        label = f"{f.code} {finishes.title(f)}" if f.code else finishes.title(f)
        surfaces += (f'<div class="surf"><i style="background:{_ball(f, colour)}"></i><b>{e(label)}</b>'
                     f'<span>{e(s["job"])}</span></div>')
    sizes = "".join(f'<div class="size">{lang["sizes"][k]["svg"]}<b class="teko">{k.title()}</b>'
                    f'<span>{d}: {e(lang["sizes"][k]["what"])}</span></div>'
                    for k, d in (("large", "from far"), ("medium", "from the chase camera"), ("small", "up close")))
    never = "".join(f"<li>{e(str(n))}</li>" for n in lang["never"])
    body = (sec("The idea", f'<p class="big">{e(lang["idea"])}</p>' + ps(lang["world"]))
            + sec("Character", f'<p><b>Is</b> {e(" · ".join(lang["is"]))}</p>'
                               f'<p><b>Isn’t</b> {e(" · ".join(lang["isnt"]))}</p>')
            + sec("The signature", f'<div class="wide">{lang["signature"]["svg"]}</div>' + ps(lang["signature"]["says"]))
            + sec("The DNA", f'<div class="wide">{lang["dna"]["svg"]}</div>' + ps(lang["dna"]["says"]))
            + sec("Colour", f'<div class="ratio">{ratio}</div><div class="list">{colours}</div>' + ps(lang["meet"]))
            + sec("Surfaces", f'<div class="surfs">{surfaces}</div>' + ps(lang["ageing"]))
            + sec("Three sizes", f'<div class="sizes">{sizes}</div>' + ps(lang["fullness"]))
            + (sec("Lettering", ps(lang["lettering"])) if str(lang.get("lettering") or "").strip() else "")
            + sec("Never", f"<ul>{never}</ul>"))
    title = e(name.removeprefix("TSC_"))
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Visual language</title><link rel="icon" href="data:,">
<style>
  @font-face {{ font-family: Teko; src: url("/lib/fonts/Teko-Variable.ttf") format("truetype"); font-weight: 300 700; }}
  :root {{ --ground: #0d0f12; --text: #f2f4f7; --acc: #e8ff47; }}
  html, body {{ margin: 0; background: var(--ground); }}
  body {{ font: 14px/1.4 "Segoe UI", system-ui, -apple-system, sans-serif; color: var(--text); }}
  main {{ max-width: 1200px; margin: 0 auto; padding: 34px 40px 60px; box-sizing: border-box; }}
  .teko {{ font-family: Teko, Bahnschrift, "DIN Condensed", sans-serif; text-transform: uppercase; letter-spacing: 0.03em; line-height: 1; }}
  h1 {{ margin: 0 0 26px; font-size: 52px; font-weight: 600; transform: skewX(-9deg); }}
  h1 span {{ font-weight: 400; opacity: .55; }}
  section {{ display: grid; grid-template-columns: 240px 1fr; gap: 24px; padding: 26px 0; border-top: 1px solid rgba(255,255,255,.1); }}
  h2 {{ margin: 0; font-size: 30px; font-weight: 500; }}
  p {{ margin: 8px 0 0; color: rgba(242,244,247,.78); max-width: 640px; }}
  b {{ color: var(--text); font-weight: 600; }}
  .big {{ font-size: 20px; line-height: 1.3; color: var(--text); margin-top: 0; }}
  svg {{ display: block; width: 100%; height: auto; }}
  .wide {{ max-width: 560px; }}
  .ratio {{ display: flex; height: 56px; }}
  .list {{ margin-top: 12px; display: grid; gap: 6px; }}
  .row {{ display: grid; grid-template-columns: 18px 150px 1fr; gap: 10px; align-items: center; }}
  .row i {{ width: 18px; height: 18px; }}
  .row span, .surf span, .size span {{ color: rgba(242,244,247,.6); font-size: 13px; }}
  .surfs {{ display: flex; gap: 22px; flex-wrap: wrap; }}
  .surf {{ display: grid; justify-items: start; align-content: start; gap: 4px; width: 130px; }}
  .surf i {{ width: 64px; height: 64px; border-radius: 50%; margin-bottom: 4px; }}
  .sizes {{ display: flex; gap: 20px; flex-wrap: wrap; }}
  .size {{ display: grid; align-content: start; gap: 6px; width: 260px; }}
  .size b {{ font-size: 22px; font-weight: 500; }}
  ul {{ margin: 0; padding-left: 18px; color: rgba(242,244,247,.78); }}
  li {{ margin: 3px 0; }}
  @media (max-width: 760px) {{ main {{ padding: 24px 16px 40px; }} section {{ grid-template-columns: 1fr; gap: 12px; }} }}
</style></head>
<body><main><h1 class="teko">{title} <span>· Visual language</span></h1>
{body}
</main></body></html>
"""


def build(name):
    """Check the car's language and write its page; returns the page's path."""
    src = paths.SKINS / name / "language.json"
    if not src.is_file():
        raise SystemExit(f"no {src.relative_to(paths.REPO)}: write the car's language first (.claude/skills/skin/language.md)")
    lang = json.loads(src.read_text(encoding="utf-8"))
    bad = check(lang)
    if bad:
        raise SystemExit(f"{name}'s language isn't whole:\n  " + "\n  ".join(bad))
    out = FOLDER / f"{name}.html"
    paths.write(out, render(name, lang))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m tool.language", description=__doc__.split("\n\n")[0])
    ap.add_argument("name")
    ap.add_argument("--no-open", action="store_true", help="just check and write the page")
    args = ap.parse_args(argv)
    build(args.name)
    if args.no_open:
        print(f"{args.name}'s visual language: {page_url(args.name)}")
    elif server.ours():
        server.serve(f"data/language/{args.name}.html", f"{args.name}'s visual language")
    else:
        print(f"{args.name}'s visual language: {page_url(args.name)} (the Lab's server isn't up: "
              "`PY -m tool.doctor server`)")


if __name__ == "__main__":
    sys.exit(main())
