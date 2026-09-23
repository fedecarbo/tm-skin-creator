"""Check the official zips against official/SOURCES.md and unpack them into the work folder.

Run: python -m tool.prepare
The zips are never modified. Unpacking again is safe: it replaces the extracted copies.
"""

import hashlib
import re
import shutil
import sys
import zipfile

from tool import paths

ZIPS = {
    "CarSport-Template.zip": paths.TEMPLATE,
    "CarSport-Model.zip": paths.MODEL,
}
NESTED = "source/StadiumCAR2020_OffsetFix.zip"


def expected_hashes() -> dict[str, str]:
    """Read '## <zip name>' sections and their '**sha256:** `...`' lines from SOURCES.md."""
    text = (paths.OFFICIAL / "SOURCES.md").read_text(encoding="utf-8")
    hashes = {}
    for section in re.split(r"^## ", text, flags=re.M)[1:]:
        name = section.splitlines()[0].strip()
        found = re.search(r"sha256:\*\*\s*`([0-9a-f]{64})`", section)
        if found:
            hashes[name] = found.group(1)
    return hashes


def sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def unpack(zip_path, dest):
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(dest)


def main():
    hashes = expected_hashes()
    for name, dest in ZIPS.items():
        zip_path = paths.OFFICIAL / name
        if not zip_path.exists():
            sys.exit(f"Missing {zip_path}. Download it from the link in official/SOURCES.md.")
        actual = sha256(zip_path)
        if actual != hashes.get(name):
            sys.exit(f"{name}: sha256 {actual} does not match official/SOURCES.md")
        unpack(zip_path, dest)
        print(f"{name}: sha256 ok, unpacked to {dest}")
    unpack(paths.MODEL / NESTED, paths.MODEL_SOURCE)
    print(f"{NESTED}: unpacked to {paths.MODEL_SOURCE}")


if __name__ == "__main__":
    main()
