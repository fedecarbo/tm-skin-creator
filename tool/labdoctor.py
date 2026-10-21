"""The Lab's doctor: the Lab's server up and current at a session's start, and where every skin stands.

    python tool/labdoctor.py session   what the SessionStart hook runs after tool/doctor.py: the Lab's server (started,
                                       or restarted when it runs old code), then where every skin stands (tool/notes.py)
    python -m tool.labdoctor server    start the Lab's server, or restart it when it runs old code

The server: tool/server.py answers /api/health with its pid and the newest modification time of the tool's code when
it started. Code on disk newer than that (a pull, an edit) means the Lab shows an old tool, so the server is stopped
and started again, detached from the session, its output in the work folder's server.log. A port held by something
that isn't Python is only named. Standard library only (the hook may run it with the Mac's own python3), as
tool/doctor.py is.
"""

import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
from tool import doctor, paths  # noqa: E402

PORT = 8765
HEALTH = f"http://127.0.0.1:{PORT}/api/health"
LOG = paths.WORK / "server.log"


def code_stamp():
    """The newest modification time of the tool's code, as tool/server.py reports it."""
    return max((p.stat().st_mtime for p in (REPO / "tool").glob("*.py")), default=0.0)


def _health():
    """The server's /api/health: its document, {"status": code} for an answer that isn't it, None
    when nothing answers."""
    try:
        with urllib.request.urlopen(HEALTH, timeout=2) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        return {"status": e.code}
    except (OSError, ValueError):  # nothing answers, or not JSON
        return None


def _port_held():
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", PORT)) == 0


def _holder():
    """(pid, command) of the process listening on PORT, or (None, None)."""
    try:
        if os.name == "nt":
            out = subprocess.run(["netstat", "-ano", "-p", "tcp"], capture_output=True, text=True, timeout=20).stdout
            m = re.search(rf"TCP\s+\S+:{PORT}\s+\S+\s+LISTENING\s+(\d+)", out)
            if not m:
                return None, None
            pid = int(m.group(1))
            t = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                               capture_output=True, text=True, timeout=20).stdout
            return pid, (t.split(",")[0].strip().strip('"') if "," in t else None)
        out = subprocess.run(["lsof", f"-tiTCP:{PORT}", "-sTCP:LISTEN"], capture_output=True, text=True, timeout=10).stdout.split()
        if not out:
            return None, None
        pid = int(out[0])
        cmd = subprocess.run(["ps", "-o", "comm=", "-p", str(pid)], capture_output=True, text=True, timeout=10).stdout.strip()
        return pid, cmd or None
    except (OSError, ValueError, subprocess.SubprocessError):
        return None, None


def _kill(pid):
    """Stop a process of ours and wait for the port to free. True when it did."""
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, timeout=20)
        else:
            os.kill(pid, 15)
        for _ in range(20):
            if not _port_held():
                return True
            time.sleep(0.25)
    except (OSError, subprocess.SubprocessError):  # gone already
        pass
    return not _port_held()


def _start():
    """Start the Lab's server (tool/swatches.py paints any material not painted yet, then serves)
    detached from this process, so it outlives the hook and the session; its output goes to LOG."""
    paths.WORK.mkdir(parents=True, exist_ok=True)
    if LOG.exists() and LOG.stat().st_size > 1 << 20:
        LOG.write_text("", encoding="utf-8")
    with open(LOG, "a", encoding="utf-8") as log:
        log.write(f"\n--- {time.strftime('%Y-%m-%d %H:%M:%S')} started by tool/labdoctor.py with {sys.executable}\n")
        log.flush()
        if os.name == "nt":
            flags = {"creationflags": subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP}
        else:
            flags = {"start_new_session": True}
        subprocess.Popen([sys.executable, "-m", "tool.swatches", "--no-tab"], cwd=REPO,
                         stdin=subprocess.DEVNULL, stdout=log, stderr=log, **flags)


def server_state(can_start=True):
    """The Lab's server: up and current, restarted when its code is old or it has no health check,
    started when off. can_start: False when the tool doesn't import (it would fail at once)."""
    h = _health()
    if h and h.get("ok"):
        if code_stamp() - float(h.get("code") or 0) > 1:
            if can_start and _kill(h["pid"]):
                _start()
                return "the Lab's server restarted (its code was old)", []
            return "the Lab's server runs old code", [f"The Lab's server (pid {h['pid']}) runs old code and couldn't be restarted: `PY -m tool.labdoctor server`."]
        return f"the Lab's server up and current (pid {h['pid']})", []
    if _port_held():
        pid, cmd = _holder()
        if pid and cmd and "python" in cmd.lower() and can_start and _kill(pid):
            _start()
            return "the Lab's server restarted (it had no health check)", []
        return "the Lab's server unknown", [f"Port {PORT} is held by pid {pid} ({cmd or 'unknown'}), not the tool's server: stop it, then `PY -m tool.labdoctor server`."]
    if not can_start:
        return "the Lab's server off", ["The Lab's server is off; it wasn't started because the tool doesn't import."]
    _start()
    return "the Lab's server starting (server.log in the work folder)", []


def server():
    """Start the Lab's server afresh (stopping ours if it runs) and wait until it answers."""
    doctor.with_stdout_utf8()
    h = _health()
    if h and h.get("ok"):
        _kill(h["pid"])
    elif _port_held():
        pid, cmd = _holder()
        if not (pid and cmd and "python" in cmd.lower() and _kill(pid)):
            sys.exit(f"port {PORT} is held by pid {pid} ({cmd or 'unknown'}), not the tool's server: stop it first")
    _start()
    for _ in range(120):  # the first start paints the materials: minutes on a fresh computer
        time.sleep(0.5)
        h = _health()
        if h and h.get("ok"):
            print(f"the Lab: http://localhost:{PORT}/ (pid {h['pid']}; its log: {LOG})")
            return
    sys.exit(f"the Lab's server hasn't answered after a minute: see {LOG}")


def session():
    """The block the session-start hook prints after the tool's own (tool/doctor.py)."""
    doctor.with_stdout_utf8()
    try:
        line, todo = server_state()
    except Exception as e:  # a check that fails never stops the session
        line, todo = "", [f"(the Lab's server couldn't be checked: {e})"]
    print(f"The Lab: {line}." if line else "The Lab:")
    for t in todo:
        print(f"- {t}")
    print()
    try:
        from tool import notes
        notes.standing()
    except Exception as e:
        print(f"(Where the skins stand couldn't be read: {e})")


def main(args):
    if args == ["session"]:
        try:
            session()
        except Exception as e:  # the session starts anyway
            print(f"(The Lab's doctor couldn't run: {e})")
    elif args == ["server"]:
        server()
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
