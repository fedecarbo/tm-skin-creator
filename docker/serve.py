"""The viewer and gallery in a container, for machines other than the Windows PC.

    docker compose up --build      then open http://localhost:8765/gallery.html

On start it:
  - downloads Nadeo's template zip into official/ if it's missing;
  - checks and unpacks the official zips (tool.prepare) the first time;
  - serves the viewer on every interface (tool.view listens on 127.0.0.1 only, which Docker
    can't forward to);
  - paints the Lab's balls (tool.swatches) and every skin whose viewer data is missing or older
    than its design or art. No snapshots, so nothing in the repo is rewritten.

Without official/CarSport-Model.zip (a Sketchfab login is needed to download it), the gallery
shows the pictures already in the repo, with no 3D view. Snapshots (Edge), the picture maker
(an NVIDIA card) and installing into the game stay on the Windows PC.
"""

import http.server
import threading
import traceback
import urllib.request

from tool import gallery, paths, prepare, skin, swatches, view

TEMPLATE_URL = "https://nadeo-download.cdn.ubi.com/trackmania/website/resources/Trackmania-Skin-Details-2021-02-18.zip"
MODEL_PAGE = "https://sketchfab.com/3d-models/trackmania-2020-carsport-c8b80bfc1ed1427eb37f3eba8d1ecfbf"


def fetch_template():
    target = paths.OFFICIAL / "CarSport-Template.zip"
    if target.exists():
        return
    print("downloading Nadeo's template zip")
    with urllib.request.urlopen(TEMPLATE_URL, timeout=120) as r:
        data = r.read()
    target.write_bytes(data)  # tool.prepare checks its sha256


def serve():
    server = http.server.ThreadingHTTPServer(("0.0.0.0", view.PORT), view.Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"gallery: http://localhost:{view.PORT}/gallery.html")


def model_ready():
    if not (paths.OFFICIAL / "CarSport-Model.zip").exists():
        print("No official/CarSport-Model.zip, so the gallery shows pictures only. Copy it from the "
              f"Windows PC, or download it (original format) from {MODEL_PAGE}, then restart.")
        return False
    if not paths.FBX.exists():
        try:
            prepare.main()
        except SystemExit as e:
            print(e)
            return False
    return True


def stale(folder):
    made = view.DATA / "skins" / folder.name / "skin.json"
    sources = (folder / "design.py", *folder.glob("art/*.png"))
    return not made.exists() or made.stat().st_mtime < max(p.stat().st_mtime for p in sources)


def paint_all():
    folders = sorted(f for f in paths.SKINS.iterdir() if (f / "design.py").exists())
    todo = [f.name for f in folders if stale(f)]
    for i, name in enumerate(todo, 1):
        print(f"[{i}/{len(todo)}] {name}")
        try:
            skin.show(name, snapshot=False)
        except Exception:
            traceback.print_exc()
    print(f"{len(todo)} skins painted, {len(folders) - len(todo)} already up to date")


def main():
    fetch_template()
    gallery.refresh()
    serve()
    try:
        swatches.build()  # the Lab: http://localhost:8765/lab.html
    except Exception:
        traceback.print_exc()
    if model_ready():
        view.export_mesh()
        view.ensure_hdri()
        view.ensure_stock()
        paint_all()
    threading.Event().wait()


if __name__ == "__main__":
    main()
