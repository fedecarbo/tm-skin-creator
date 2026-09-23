"""Put a built skin zip into the game, safely.

    python -m tool.install TSC_Test [TSC_Test_Sharp ...]

This is the only code that writes into the game's skin folder, and the folder's path lives only
here. It never lists that folder. It checks just its exact target file:
  - the name is free: copy the zip there;
  - the name is taken by a file this tool installed (listed in skins/installed.json) and still
    unchanged (same sha256): replace it;
  - anything else: refuse, and leave the file alone.
"""

import datetime
import hashlib
import json
import shutil
import sys
from pathlib import Path

from tool import paths

GAME_SKINS = Path(r"C:\Users\fedec\OneDrive\Documents\Trackmania\Skins\Models\CarSport")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_manifest():
    if paths.INSTALLED_MANIFEST.exists():
        return json.loads(paths.INSTALLED_MANIFEST.read_text(encoding="utf-8"))
    return {}


def save_manifest(manifest):
    paths.INSTALLED_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    paths.INSTALLED_MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def install(zip_path):
    zip_path = Path(zip_path)
    if " " in zip_path.name:
        raise ValueError(f"{zip_path.name}: no spaces allowed in skin names")
    if not GAME_SKINS.is_dir():
        raise FileNotFoundError(f"The game's skin folder isn't there: {GAME_SKINS}")
    manifest = load_manifest()
    target = GAME_SKINS / zip_path.name
    if target.exists():
        ours = manifest.get(zip_path.name)
        if not ours or sha256(target) != ours["sha256"]:
            raise PermissionError(f"{target.name} is already in the game folder and isn't ours "
                                  "(or was changed since we installed it). Leaving it alone.")
    shutil.copyfile(zip_path, target)
    digest = sha256(target)
    if digest != sha256(zip_path):
        raise OSError(f"{target.name}: the copy doesn't match the built zip")
    manifest[zip_path.name] = {
        "sha256": digest,
        "bytes": target.stat().st_size,
        "installed": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    save_manifest(manifest)
    return target


def main(names):
    for name in names:
        target = install(paths.BUILD / f"{name}.zip")
        print(f"installed {target.name} ({target.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main(sys.argv[1:])
