"""Two of the rules as checks that hold whether Claude remembers them or not. Hooks in
.claude/settings.json run this file as a script, perhaps on the Mac's own python3: it stays
standard library only.

    python tool/guard.py folder    before a shell command (PreToolUse): refuse one that names the
                                   game's skin folder
    python tool/guard.py pushed    when Claude would end its turn (Stop): hold it while work isn't on
                                   GitHub

The game's skin folder holds the user's own skins (CLAUDE.md). Only tool/install.py writes there and
its path lives only in that file, so the install command never names it. A shell command that names
it (any spelling of Trackmania\\Skins or Skins\\Models, or install.py's GAME_SKINS or game_folder)
is refused before it runs, with the reason. The file tools are denied there by the permissions in
.claude/settings.json.

The other computer only has what's on GitHub, so a turn doesn't end with files changed and not
committed, or commits not pushed: Claude is sent back to commit and push. It's held once: a turn
that ends again with work still not on GitHub (a push that failed) ends, so a broken network can't
trap the session.

Each reads the hook's JSON on stdin, and says nothing when all is well. Anything it can't read lets
the command or the turn go: a broken guard must not stop the work.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

GAME_FOLDER = re.compile(r"trackmania[\\/]+skins|skins[\\/]+models|\bGAME_SKINS\b|\bgame_folder\b", re.I)


def _strings(value):
    """Every string in the tool's input: the command, whatever the tool calls it."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from _strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from _strings(v)


def folder(event):
    """The PreToolUse answer for a shell command: a refusal if it names the game's skin folder."""
    named = next((m.group(0) for s in _strings(event.get("tool_input")) for m in [GAME_FOLDER.search(s)] if m), None)
    if not named:
        return None
    return {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": (
            f"Refused: this command names the game's skin folder ({named}), which holds the user's own "
            "skins (CLAUDE.md). Only `PY -m tool.skin install <name>` puts a skin there. To search the "
            "repo's own text for that name, use the Grep tool; a commit message that names it goes in a "
            "file (git commit -F)."),
    }}


def _git(*args):
    return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True, timeout=20)


def pushed(event):
    """The Stop answer: hold the turn while the repo has changes not committed or commits not pushed."""
    if event.get("stop_hook_active"):
        return None  # held once already this turn
    status = _git("status", "--porcelain")
    if status.returncode:
        return None
    changed = len(status.stdout.splitlines())
    ahead = _git("rev-list", "--count", "@{u}..HEAD")
    unpushed = int(ahead.stdout.strip() or 0) if ahead.returncode == 0 else None
    if not changed and unpushed == 0:
        return None
    what = []
    if changed:
        what.append(f"{changed} file{'s' * (changed > 1)} changed and not committed")
    if unpushed is None:
        what.append("this branch isn't on GitHub")
    elif unpushed:
        what.append(f"{unpushed} commit{'s' * (unpushed > 1)} not pushed")
    return {"decision": "block", "reason": (
        f"Not on GitHub yet: {', '.join(what)}. The other computer only has what's on GitHub: commit "
        "what's finished, with a message that says what changed and why, and push. If the push fails, "
        "tell the user why.")}


def main(args):
    try:
        event = json.loads(sys.stdin.buffer.read().decode("utf-8", "replace") or "{}")
        answer = {"folder": folder, "pushed": pushed}[args[0]](event)
    except Exception:
        return
    if answer:
        print(json.dumps(answer))


if __name__ == "__main__":
    main(sys.argv[1:])
