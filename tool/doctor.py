"""The tool's doctor: one short block at a session's start that says what's wrong with the machinery
and fixes what's safe, so a cold start on either computer begins with a working tool.

    python tool/doctor.py session    what the SessionStart hook runs after the pull: GitHub, the
                                     tool's Python, the work folder, the game's list, the queue
                                     (the Lab's own doctor, tool/labdoctor.py, runs after it)

Each check prints only when something needs doing, and a check that fails says so and lets the rest
run: nothing here can stop a session. Standard library only (the hook may run it with the Mac's own
python3), as tool/paths.py is.

The work folder: the builds and the viewer's data of skins whose design is gone are deleted (git
keeps the designs; a show paints them again), the self-test keeps its KEEP_SELFTESTS newest commits,
the caches stay (minutes to rebuild, shared by both sides of the self-test).

The queue (IMPROVEMENTS.md): how many items and the oldest's date; "prune it" past QUEUE_MOST items
or QUEUE_DAYS days, so it never piles up or goes stale (the user, 2026-10-05).
"""

import datetime
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
from tool import paths  # noqa: E402

AUTHOR = ("Federico Carbo", "fede.carbo@gmail.com")  # one name on both computers' commits
KEEP_SELFTESTS = 5
QUEUE = REPO / "IMPROVEMENTS.md"
QUEUE_MOST, QUEUE_DAYS = 20, 30
ITEM = re.compile(r"^- \*\*(.+?)\*\*[^\n]*?(?:\((\d{4}-\d{2}-\d{2})|$)", re.M)  # an item: its title, and the date on its first line


def _git(*args, timeout=20):
    return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True, timeout=timeout)


def git_state():
    """GitHub: in sync or not, stale branches; one author identity and pruning set for this repo."""
    todo = []
    head = _git("rev-parse", "--short", "HEAD").stdout.strip() or "?"
    counts = _git("rev-list", "--left-right", "--count", "HEAD...@{u}")
    if counts.returncode == 0:
        ahead, behind = (int(x) for x in counts.stdout.split())
        if ahead or behind:
            todo.append(f"GitHub: {ahead} commit(s) here and not there, {behind} there and not here. "
                        "If the other computer pushed first: `git pull --rebase`, then push.")
    else:
        todo.append("GitHub: this branch isn't on GitHub (no upstream).")
    changed = len(_git("status", "--porcelain").stdout.splitlines())
    if changed:
        todo.append(f"{changed} file(s) changed and not committed.")
    stale = [b.strip() for b in _git("branch", "-r").stdout.splitlines()
             if b.strip() and b.strip() != "origin/main" and "->" not in b]
    if stale:
        todo.append("Stale branches on GitHub: " + ", ".join(stale)
                    + ". `git push origin --delete <name>` when they're superseded, then `git fetch --prune`.")
    for key, value in (("user.name", AUTHOR[0]), ("user.email", AUTHOR[1]), ("fetch.prune", "true")):
        if _git("config", "--get", key).stdout.strip() != value:
            _git("config", key, value)
    return (f"GitHub in sync ({head})" if not todo else f"GitHub ({head})"), todo


def tool_imports():
    """The tool's Python imports its packages and the tool, in a fresh process: a broken module is
    found here, not in the first paint."""
    code = "import numpy, PIL, scipy; from tool import paintbox, server, skin"
    try:  # from the work folder, not the repo: the tools must import from any folder (pyproject.toml)
        r = subprocess.run([sys.executable, "-c", code], cwd=paths.WORK, capture_output=True, text=True, timeout=90)
    except subprocess.TimeoutExpired:
        return "the tool imports (slowly)", []
    if r.returncode == 0:
        return "the tool imports", []
    last = (r.stderr.strip().splitlines() or ["no reason given"])[-1]
    return "the tool doesn't import", [
        f"The tool's Python ({sys.executable}) can't import the tool: {last}. "
        "Set it up as .claude/rules/tool.md says (the venv, pip install -r requirements.txt, pip install -e .)."]


def _size(path):
    if path.is_file():
        return path.stat().st_size
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:  # a file deleted while counting
                pass
    return total


def _gb(n):
    return f"{n / 1e9:.1f} GB" if n >= 1e8 else f"{n / 1e6:.0f} MB"


def _of_live(stem, live):
    """Whether a build's or a viewer folder's name belongs to a skin that exists: the skin's own name, or
    it plus a lower-case suffix (TSC_Snow_views, TSC_Snow_close_before). TSC_Snow_Glacier is another
    skin (takes are CamelCase), kept only when it exists itself."""
    for name in sorted(live, key=len, reverse=True):
        if stem == name:
            return True
        if stem.startswith(name + "_"):
            return bool(re.match(r"[a-z]", stem[len(name) + 1:]))
    return False


def prune():
    """The work folder: builds and viewer data of skins that no longer exist, old self-tests, the site."""
    live = {p.parent.name for p in (REPO / "skins").glob("*/design.py")}
    gone, freed = set(), 0

    def drop(path):
        nonlocal freed
        freed += _size(path)
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        else:
            path.unlink(missing_ok=True)

    for folder in (paths.BUILD, paths.WORK / "viewer" / "skins"):
        if folder.is_dir():
            for p in folder.iterdir():
                stem = p.name if p.is_dir() else p.name.split(".")[0]
                if stem.startswith("TSC_") and not _of_live(stem, live):
                    gone.add(re.sub(r"(_[a-z][a-z0-9]*)+$", "", stem))  # the skin's name, its build suffixes off
                    drop(p)
    tests = paths.WORK / "selftest"
    if tests.is_dir():
        commits = sorted((p for p in tests.iterdir() if p.is_dir() and re.fullmatch(r"[0-9a-f]{12}", p.name)),
                         key=lambda p: p.stat().st_mtime, reverse=True)
        for p in commits[KEEP_SELFTESTS:]:
            drop(p)
    if (paths.WORK / "site").is_dir():
        drop(paths.WORK / "site")
    total = _size(paths.WORK) if paths.WORK.is_dir() else 0
    ok = f"work folder {_gb(total)}"
    if freed:
        ok += f" ({_gb(freed)} freed: {len(gone)} skins that no longer exist, old self-tests)"
    return ok, []


def game_list():
    """The game's list of our skins (skins/installed.json) against the skins that exist."""
    manifest_file = REPO / "skins" / "installed.json"
    if not manifest_file.exists():
        return "", []
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    live = {p.parent.name for p in (REPO / "skins").glob("*/design.py")}
    stale = [n for n in manifest if n.removesuffix(".zip") not in live]
    if not stale:
        return "", []
    return "", [f"{len(manifest)} cars in the game's list, {len(stale)} of them deleted here: on the PC, "
                "`PY -m tool.install remove --deleted` takes them out of the game."]


def queue():
    """IMPROVEMENTS.md: how many items, the oldest; prune it past QUEUE_MOST or QUEUE_DAYS."""
    if not QUEUE.exists():
        return "", []
    items = ITEM.findall(QUEUE.read_text(encoding="utf-8"))
    if not items:
        return "the queue empty", []
    dates = sorted(datetime.date.fromisoformat(d) for _, d in items if d)
    undated = sum(1 for _, d in items if not d)
    oldest = dates[0] if dates else None
    ok = f"the queue {len(items)} items" + (f", the oldest from {oldest}" if oldest else "")
    why = []
    if len(items) > QUEUE_MOST:
        why.append(f"over {QUEUE_MOST} items")
    if oldest and (datetime.date.today() - oldest).days > QUEUE_DAYS:
        why.append(f"an item older than {QUEUE_DAYS} days")
    if undated:
        why.append(f"{undated} undated")
    todo = [f"The queue (IMPROVEMENTS.md) needs pruning with the user: {', '.join(why)}. "
            "Each item kept is re-dated in their words; the rest are done or deleted (git keeps them)."] if why else []
    return ok, todo


def session():
    """The block the session-start hook prints."""
    with_stdout_utf8()
    ok, todo = [], []
    for check in (git_state, tool_imports, prune, game_list, queue):
        try:
            line, more = check()
        except Exception as e:  # a check that fails never stops the session
            line, more = "", [f"({check.__name__} couldn't run: {e})"]
        if line:
            ok.append(line)
        todo += more
    print(f"Cold start, {'the Mac' if paths.MAC else 'the PC'}: " + "; ".join(ok) + ".")
    for t in todo:
        print(f"- {t}")
    print()


def with_stdout_utf8():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # the PC's pipes aren't UTF-8 otherwise
    except (AttributeError, ValueError):  # stdout isn't a console
        pass


def main(args):
    if args == ["session"]:
        try:
            session()
        except Exception as e:  # the session starts anyway
            print(f"(The doctor couldn't run: {e})")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
