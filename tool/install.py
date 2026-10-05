"""Put a built skin zip into the game, safely.

    python -m tool.install <name> [<name> ...]              put built zips in the game
    python -m tool.install remove <name> [<name> ...]       take our own zips out of it
    python -m tool.install remove --deleted                 ... every one whose design is gone from skins/

This is the only code that writes into the game's skin folder, and the folder's path lives only
here. It never lists that folder. It checks just its exact target file:
  - the name is free: copy the zip there;
  - the name is taken by a file this tool installed (listed in skins/installed.json) and still
    unchanged (same sha256): replace it, or remove it when asked to;
  - anything else: refuse, and leave the file alone.
skins/installed.json keeps an entry while its zip may be in the game: the sha256 is the only proof
this tool may touch that file. An entry whose design is gone from skins/ is what `remove --deleted`
takes out (the session-start check, tool/doctor.py, counts them).
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
    paths.write(paths.INSTALLED_MANIFEST, json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def game_folder():
    """The game's skin folder, or a plain error on a computer without the game (the Mac)."""
    if not GAME_SKINS.is_dir():
        raise SystemExit(f"The game isn't on this computer (no {GAME_SKINS}): install from the Windows PC.")
    return GAME_SKINS


def install(zip_path):
    zip_path = Path(zip_path)
    if " " in zip_path.name:
        raise ValueError(f"{zip_path.name}: no spaces allowed in skin names")
    game_folder()
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


def deleted():
    """The manifest's zips whose design is gone from skins/."""
    return [key for key in load_manifest() if not (paths.SKINS / key.removesuffix(".zip") / "design.py").exists()]


def remove(names):
    """Take our own zips out of the game: each name's exact target, only when it is the file this
    tool installed (the manifest's sha256), and its manifest entry with it. A file changed since is
    left alone and said; a name no longer in the game just leaves the manifest."""
    game_folder()
    manifest = load_manifest()
    for name in names:
        key = name if name.endswith(".zip") else f"{name}.zip"
        ours = manifest.get(key)
        if not ours:
            print(f"{key}: not in the game's list")
            continue
        target = GAME_SKINS / key
        if not target.exists():
            print(f"{key}: no longer in the game; forgotten")
        elif sha256(target) != ours["sha256"]:
            print(f"{key}: changed since we installed it: left alone")
            continue
        else:
            target.unlink()
            print(f"{key}: taken out of the game")
        del manifest[key]
    save_manifest(manifest)


def main(argv):
    if argv[:1] == ["remove"]:
        names = deleted() if argv[1:] == ["--deleted"] else argv[1:]
        if not names:
            sys.exit("remove which? names, or --deleted for every zip whose design is gone from skins/")
        remove(names)
        return
    for name in argv:
        target = install(paths.BUILD / f"{name}.zip")
        print(f"installed {target.name} ({target.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main(sys.argv[1:])
