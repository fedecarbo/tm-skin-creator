"""Where things live: the repo, and the work folder outside OneDrive (on the Mac, in Application
Support), plus the two computers' differences: the browser for snapshots and opening a file."""

import os
import subprocess
import sys
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


def open_file(path):
    """Opens a picture on the screen, as a double-click would."""
    if MAC:
        subprocess.run(["open", str(path)], check=False)
    else:
        os.startfile(path)
