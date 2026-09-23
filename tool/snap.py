"""Claude's snapshots of a skin in the viewer: six views on one sheet, taken by a hidden Edge.

    python -m tool.snap TSC_Test          -> build/TSC_Test_views.png
    python -m tool.snap TSC_Test --size 1280x960

Look at the sheet before showing a skin to the user. Playwright drives the Edge installed on
this PC (no browser download). The GPU line it prints says which renderer drew the pictures.
"""

import argparse
import io
import time

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

from tool import paths, view

# (label, view, night, hidden parts). A view is a name from viewer.js's VIEWS, or
# {"dir": [x, y, z], "dist": metres, "target": [x, y, z]} for a close look.
SHOTS = (("front three-quarter", "front", False, []), ("rear three-quarter", "rear", False, []),
         ("left side", "left", False, []), ("right side", "right", False, []),
         ("top", "top", False, []), ("night", "front", True, []))
EDGE_ARGS = ["--use-angle=d3d11", "--enable-gpu", "--ignore-gpu-blocklist"]


def snap(name, out=None, size=(960, 720), shots=SHOTS, query=""):
    """query: extra page settings, e.g. "exposure=0.9&coat=0.5" (TUNE in viewer.js)."""
    view.prepare(name)
    server = view.start_server(0)
    url = f"http://127.0.0.1:{server.server_address[1]}/?skin={name}&snap=1" + (f"&{query}" if query else "")
    tiles, errors = [], []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge", headless=True, args=EDGE_ARGS)
            page = browser.new_page(viewport={"width": size[0], "height": size[1]})
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: errors.append(str(e)))
            start = time.time()
            page.goto(url)
            page.wait_for_function("window.viewer && (window.viewer.ready || window.viewer.error)",
                                   timeout=180_000)
            if page.evaluate("window.viewer.error"):
                raise RuntimeError(page.evaluate("window.viewer.error"))
            print(f"GPU: {page.evaluate('viewer.gpu()')}; loaded in {time.time() - start:.1f} s")
            for label, view_spec, night, hidden in shots:
                page.evaluate("([v, n, h]) => viewer.show(v, n, h)", [view_spec, night, hidden])
                tiles.append((label, Image.open(io.BytesIO(page.screenshot()))))
            browser.close()
    finally:
        server.shutdown()
    for e in errors:
        print(f"page error: {e}")
    out = out or paths.BUILD / f"{name}_views.png"
    cols = 3
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * size[0], rows * size[1]))
    font = ImageFont.truetype("arialbd.ttf", 24)
    for k, (label, tile) in enumerate(tiles):
        d = ImageDraw.Draw(tile)
        d.text((14, 10), label, fill=(255, 255, 255), font=font, stroke_width=3, stroke_fill=(0, 0, 0))
        sheet.paste(tile.convert("RGB"), ((k % cols) * size[0], (k // cols) * size[1]))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    print(f"sheet: {out}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--size", default="960x720")
    args = ap.parse_args()
    w, h = (int(v) for v in args.size.split("x"))
    snap(args.name, size=(w, h))


if __name__ == "__main__":
    main()
