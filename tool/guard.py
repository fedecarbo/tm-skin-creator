"""The rules that must hold whether Claude remembers them or not, as hooks in .claude/settings.json. They run this
file as a script, perhaps on the Mac's own python3: it stays standard library only (and tool.gate and tool.paths,
which are too).

    python tool/guard.py folder    before a shell command (PreToolUse): refuse one that names the
                                   game's skin folder
    python tool/guard.py agent     before an agent starts (PreToolUse): refuse a pass on a car the
                                   judge hasn't passed
    python tool/guard.py turn      when the user sends a message (UserPromptSubmit): the turn starts
    python tool/guard.py stop      when Claude would end its turn (Stop): hold it while a car changed
                                   in the turn isn't passed, or work isn't on GitHub

The game's skin folder holds the user's own skins (CLAUDE.md). Only tool/install.py writes there and
its path lives only in that file, so the install command never names it. A shell command that names
it (any spelling of Trackmania\\Skins or Skins\\Models, or install.py's GAME_SKINS or game_folder)
is refused before it runs, with the reason. The file tools are denied there by the permissions in
.claude/settings.json.

A car built in passes (it has a language: .claude/skills/skin/language.md) gets each pass's agent only once the judge
has passed it as it is and the close looks have seen it (tool/gate.py): an agent whose brief names it is refused
until then, so no pass starts on a broken car.

A turn doesn't end with a car changed in it (its design, its verdict or what was let go) that the gates don't pass, or
with files changed and not committed, or commits not pushed (the other computer only has what's on GitHub): Claude is
sent back with what's wrong. Each thing is held once a turn (the work folder's turns/<session>.json, from the turn's
start): a turn that ends again with it still there (the user told plainly, a push that failed) ends, so nothing can
trap the session.

Each reads the hook's JSON on stdin, and says nothing when all is well. Anything it can't read lets
the command or the turn go: a broken guard must not stop the work.
"""

import json
import re
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:  # run as a file
    sys.path.insert(0, str(REPO))

GAME_FOLDER = re.compile(r"trackmania[\\/]+skins|skins[\\/]+models|\bGAME_SKINS\b|\bgame_folder\b", re.I)
KEEP = 7 * 86400  # seconds a session's turn file is kept


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


def _deny(reason):
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                   "permissionDecisionReason": reason}}


def folder(event):
    """The PreToolUse answer for a shell command: a refusal if it names the game's skin folder."""
    named = next((m.group(0) for s in _strings(event.get("tool_input")) for m in [GAME_FOLDER.search(s)] if m), None)
    if not named:
        return None
    return _deny(
        f"Refused: this command names the game's skin folder ({named}), which holds the user's own "
        "skins (CLAUDE.md). Only `PY -m tool.skin install <name>` puts a skin there. To search the "
        "repo's own text for that name, use the Grep tool; a commit message that names it goes in a "
        "file (git commit -F).")


def agent(event):
    """The PreToolUse answer for an agent: a refusal if its brief names a car built in passes that the gates
    don't pass."""
    from tool import gate, paths
    brief = "\n".join(_strings(event.get("tool_input")))
    cars = [p.parent.name for p in paths.SKINS.glob("*/language.json")
            if re.search(rf"(?<![\w-]){re.escape(p.parent.name)}(?![\w-])", brief)]
    refused = gate.refusal(cars, "a pass")
    if not refused:
        return None
    return _deny(refused + "\nA pass starts on a car the judge passes, close up: this session fixes it first.")


def _turn_file(event):
    sid = re.sub(r"[^A-Za-z0-9_-]", "", str(event.get("session_id") or ""))
    if not sid:
        return None
    from tool import paths
    return paths.WORK / "turns" / f"{sid}.json"


def turn(event):
    """The UserPromptSubmit answer: nothing to say; the turn's start kept for the Stop hook."""
    p = _turn_file(event)
    if p is None:
        return None
    p.parent.mkdir(parents=True, exist_ok=True)
    for old in p.parent.glob("*.json"):
        if time.time() - old.stat().st_mtime > KEEP:
            old.unlink()
    p.write_text(json.dumps({"start": time.time(), "held": []}))
    return None


def _git(*args):
    return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True, timeout=20)


def _pushed():
    """What isn't on GitHub, or None."""
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
    return (f"Not on GitHub yet: {', '.join(what)}. The other computer only has what's on GitHub: commit "
            "what's finished, with a message that says what changed and why, and push. A push refused because "
            "the other computer pushed first: `git pull --rebase`, then push again (a conflict in "
            "skins/installed.json keeps both sides' entries). If it still fails, tell the user why.")


def _cars(since):
    """Each car changed since `since` (its design, its art, what was let go, its verdict) that the gates don't pass:
    {(car, what): line}."""
    from tool import gate, paths
    out = {}
    for d in sorted(paths.SKINS.iterdir()):
        if not (d / "design.py").exists():
            continue
        touched = [d / "design.py", d / "despite.json", paths.BUILD / d.name / "verdict.json", *(d / "art").glob("*")]
        if any(p.exists() and p.stat().st_mtime > since for p in touched):
            for what, line in gate.wrong(d.name):
                out[f"{d.name}:{what}"] = line
    return out


def stop(event):
    """The Stop answer: hold the turn, once for each thing, while a car changed in it isn't passed or the work
    isn't on GitHub."""
    p = _turn_file(event)
    state = None
    if p is not None and p.exists():
        state = json.loads(p.read_text())
    wrong = _cars(state["start"]) if state else {}
    push = _pushed()
    if push:
        wrong["pushed"] = push
    if state is None:  # no turn kept (the hook didn't run): held once, as Claude Code says
        new = [] if event.get("stop_hook_active") else list(wrong)
    else:
        new = [k for k in wrong if k not in state["held"]]
        state["held"] += new
        p.write_text(json.dumps(state))
    if not new:
        return None
    cars = [wrong[k] for k in wrong if k != "pushed"]
    reason = []
    if cars:
        reason.append("A car changed in this turn isn't passed by the gates (tool/gate.py):\n"
                      + "\n".join(f"  {line}" for line in cars)
                      + "\nFix it and show it again; or, if it stays, tell the user plainly what's still wrong (what's "
                      "meant: `PY -m tool.gate <name> --despite \"<why>\"`, which says it in the Lab). Each of these "
                      "holds the turn once.")
    if push:
        reason.append(push)
    return {"decision": "block", "reason": "\n\n".join(reason)}


def main(args):
    try:
        event = json.loads(sys.stdin.buffer.read().decode("utf-8", "replace") or "{}")
        answer = {"folder": folder, "agent": agent, "turn": turn, "stop": stop}[args[0]](event)
    except Exception:
        return
    if answer:
        print(json.dumps(answer))


if __name__ == "__main__":
    main(sys.argv[1:])
