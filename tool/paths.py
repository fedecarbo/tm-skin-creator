"""Where things live: the repo, and the work folder outside OneDrive."""

import os
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OFFICIAL = REPO / "official"
SKINS = REPO / "skins"
INSTALLED_MANIFEST = SKINS / "installed.json"

WORK = Path(os.environ["LOCALAPPDATA"]) / "TrackmaniaSkinChallenge"
VENV = WORK / "venv"
UNPACKED = WORK / "official"  # extracted copies of the official/ zips
TEMPLATE = UNPACKED / "template"  # Nadeo's ReadMe and UV maps
MODEL = UNPACKED / "model"  # the Sketchfab zip: textures/*.png, source/*.zip
MODEL_SOURCE = UNPACKED / "model_source"  # the nested zip: the FBX and the stock DDS files
FBX = MODEL_SOURCE / "StadiumCAR2020_OffsetFix.fbx"
CACHE = WORK / "cache"  # bakes and other rebuildable results
BUILD = WORK / "build"  # built textures and skin zips
