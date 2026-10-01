"""Where things live: the repo, and the work folder outside OneDrive (on the Mac, in Application
Support), plus the two computers' differences: the browser for snapshots and opening a file."""

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OFFICIAL = REPO / "official"
SKINS = REPO / "skins"
INSTALLED_MANIFEST = SKINS / "installed.json"

MAC = sys.platform == "darwin"
WORK = (Path.home() / "Library" / "Application Support" if MAC
        else Path(os.environ["LOCALAPPDATA"])) / "TrackmaniaSkinChallenge"
UNPACKED = WORK / "official"  # extracted copies of the official/ zips
TEMPLATE = UNPACKED / "template"  # Nadeo's ReadMe and UV maps
MODEL = UNPACKED / "model"  # the Sketchfab zip: textures/*.png, source/*.zip
MODEL_SOURCE = UNPACKED / "model_source"  # the nested zip: the FBX and the stock DDS files
FBX = MODEL_SOURCE / "StadiumCAR2020_OffsetFix.fbx"
CACHE = WORK / "cache"  # bakes and other rebuildable results
BUILD = WORK / "build"  # built textures and skin zips

# The Mac's snapshots use Playwright's own Chromium, kept in the work folder (`python -m playwright
# install chromium`); the PC's use the Edge installed on it. Set here so every playwright launch sees it.
if MAC:
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(WORK / "browsers"))


def launch(p):
    """A headless browser for the viewer's pictures, from a sync_playwright() `p`."""
    if MAC:  # WebGL through Metal
        return p.chromium.launch(headless=True, args=["--use-angle=metal", "--enable-gpu", "--ignore-gpu-blocklist"])
    return p.chromium.launch(channel="msedge", headless=True, args=["--use-angle=d3d11", "--enable-gpu", "--ignore-gpu-blocklist"])


def write(path, data):
    """Replace a file whole (text or bytes), never leaving it half-written: a page, the Lab or
    another process may be reading it. Windows refuses the replace while a reader holds the file,
    so it tries again for a second (the Lab's files; the picture open on the user's screen)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    binary = isinstance(data, bytes)
    with os.fdopen(fd, "wb" if binary else "w", encoding=None if binary else "utf-8") as f:
        f.write(data)
    for attempt in range(20):
        try:
            os.replace(tmp, path)
            return path
        except OSError:
            if attempt == 19:
                os.unlink(tmp)
                raise
            time.sleep(0.05)


def open_file(path):
    """Opens a picture on the screen, as a double-click would."""
    if MAC:
        subprocess.run(["open", str(path)], check=False)
    else:
        os.startfile(path)
