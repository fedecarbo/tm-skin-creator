"""The viewer's web server: Python's own, on this computer only (ES modules don't load from file://).

  /        the repo's viewer/ folder: the pages and three.js
  /data/   the work folder's viewer/ folder: the car, the lighting, the skins (tool/view.py)
  /api/notes   the Lab's notes on the car (tool/notes.py)
  /api/sets    each car's sets of options and what was said about them (tool/sets.py)
  /api/lines   the car's lines as the user pins them (tool/lines.py)
  /api/levels  the levels the user draws from the side (tool/levels.py), and painting them on the car
  /api/progress   what the tool is doing, a job at a time (tool/progress.py)
  /api/health     alive: its pid and the age of the code it runs (tool/doctor.py restarts an old one)
  /sets/<car>/<n>/<letter>.png, /notes/<skin>-<n>.jpg   the pictures those keep

serve() is how the tool opens a page for the user: it serves on PORT unless a server of ours
already answers there (/api/health; it reads the same folders), and opens the page. The Lab's
server is started detached, and restarted after a change to the tool, by `PY -m tool.doctor server`
(tool/doctor.py), its output in the work folder's server.log.
"""

import http.server
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
import webbrowser

from tool import levels, lines, notes, paths, progress, sets, view

PORT = 8765
STARTED = time.time()
# the tool's code as this server loaded it: tool/doctor.py restarts a server older than the code on disk
CODE = max((p.stat().st_mtime for p in (paths.REPO / "tool").glob("*.py")), default=0.0)


class Handler(http.server.SimpleHTTPRequestHandler):
    # Windows can map .js to text/plain in the registry, and browsers refuse modules served that way.
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      ".js": "text/javascript", ".json": "application/json", ".html": "text/html",
                      ".png": "image/png", ".bin": "application/octet-stream", ".hdr": "application/octet-stream",
                      ".ttf": "font/ttf"}

    def translate_path(self, path):
        path = urllib.parse.urlsplit(path).path
        if path.startswith("/data/"):
            self.directory, path = str(view.DATA), path[len("/data"):]
        else:
            self.directory = str(paths.REPO / "viewer")
        return super().translate_path(path)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    # The Lab's notes (tool/notes.py): GET /api/notes?skin=<name> (the ones not done, for the car's tags),
    # and POST a new one ({"skin", "text", "part", "at", "normal", "drawn", "picture", "view", "answer"}) or
    # {"skin", "remove": n}.
    # They reach Claude's context, so only this computer's own pages may write them: the Host must
    # be localhost (no DNS rebinding), an Origin must match it, and the body must be JSON, which a
    # page elsewhere can't send here without a CORS preflight this server never answers.
    def _local(self):
        host = self.headers.get("Host", "")
        origin = self.headers.get("Origin")
        return (host.split(":")[0] in ("localhost", "127.0.0.1")
                and (origin is None or origin in (f"http://{host}", f"https://{host}")))

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # The Lab's timeline: GET /api/sets?skin=<name>, the car the skin is or is an option of, its sets of
    # options (tool/sets.py's lab(), from the repo's skins/ folder, which /data/ doesn't reach) and
    # everything said in the Lab about it and its options (`said`: tool/notes.py's timeline()).
    # The pictures a pick kept of each option: /sets/<car>/<n>/<letter>.png, from the repo's
    # skins/<car>/sets/ (tool/sets.py); a note's picture, /notes/<skin>-<n>.jpg, and a question's
    # choice's, /notes/<skin>-ask<k><key>.png or .jpg, from .notes/, for this computer's pages only.
    # Nothing else.
    SET_PICTURE = re.compile(r"/sets/([A-Za-z0-9_\-]+)/(\d{1,4})/([A-Z])\.png")
    NOTE_PICTURE = re.compile(r"/notes/([A-Za-z0-9_\-]+-(?:\d{1,5}\.jpg|ask\d{1,4}[A-F]\.(?:jpg|png)))")

    def do_GET(self):
        url = urllib.parse.urlsplit(self.path)
        m = self.SET_PICTURE.fullmatch(url.path)
        n = self.NOTE_PICTURE.fullmatch(url.path)
        if m or n:
            if n and not self._local():
                return self._json(403, {"error": "not from this computer"})
            f = sets.SKINS / m[1] / "sets" / m[2] / f"{m[3]}.png" if m else notes.HOME / n[1]
            if not f.is_file():
                return self._json(404, {"error": "no such picture"})
            data = f.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "image/png" if m or f.suffix == ".png" else "image/jpeg")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if url.path not in ("/api/notes", "/api/sets", "/api/lines", "/api/levels", "/api/progress", "/api/health"):
            return super().do_GET()
        if not self._local():
            return self._json(403, {"error": "not from this computer"})
        skin = urllib.parse.parse_qs(url.query).get("skin", [""])[0]
        try:
            if url.path == "/api/health":  # alive, and how old its code is (tool/doctor.py)
                return self._json(200, {"ok": True, "pid": os.getpid(), "started": STARTED, "code": CODE})
            if url.path == "/api/lines":  # the car's lines as pinned in the Lab's lines room (tool/lines.py)
                return self._json(200, lines.load())
            if url.path == "/api/levels":  # the levels as drawn in the Lab's levels room (tool/levels.py)
                return self._json(200, {**levels.load(), "painting": _painting()})
            if url.path == "/api/progress":  # the chat's progress widgets (viewer/lab-car.js)
                return self._json(200, progress.jobs())
            if url.path == "/api/sets":
                doc = sets.lab(skin)
                if not doc:
                    return self._json(400, {"error": f"not a skin's name: {skin!r}"})
                doc["said"] = notes.timeline({doc["car"], *(o["skin"] for s in doc["sets"] for o in s["options"])})
                return self._json(200, doc)
            self._json(200, {"notes": notes.of(skin), "next": notes.next_n(skin)})
        except (OSError, ValueError) as e:  # a file busy, or caught mid-write
            self._json(503, {"error": str(e)})

    # What a POST to /api/notes can do: the first of these keys in the body picks it, else a new note.
    NOTE_KEYS = ("skin", "text", "part", "at", "normal", "picture", "view", "answer", "drawn")
    ACTIONS = {
        "remove": lambda body: notes.remove(body.get("skin"), body["remove"]) or {"ok": True},
    }

    # The lines room (viewer/lab-lines.js): POST /api/lines with {"lines": [...]} keeps them all
    # (tool/lines.py, car/lines.json), and GET /api/lines reads them back. The levels room
    # (viewer/lab-levels.js): POST /api/levels with {"levels": [...]} keeps them (car/levels.json),
    # and with "paint": true also paints them on the clay car (tool/levels.py, a process of its own,
    # one at a time; the room watches data/levels/painted.json).
    def do_POST(self):
        path = urllib.parse.urlsplit(self.path).path
        if path not in ("/api/notes", "/api/lines", "/api/levels"):
            return self._json(404, {"error": "nothing here"})
        if not self._local() or self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            return self._json(403, {"error": "not from this computer"})
        try:
            body = json.loads(self.rfile.read(min(int(self.headers.get("Content-Length", 0)), 10 << 20)) or b"{}")
            if not isinstance(body, dict):
                raise ValueError("expected a JSON object")
            if path == "/api/lines":
                return self._json(200, lines.save(body))
            if path == "/api/levels":
                doc = levels.save(body)
                return self._json(200, {**doc, "painting": _paint_levels() if body.get("paint") else _painting()})
            action = next((self.ACTIONS[k] for k in self.ACTIONS if k in body), None)
            self._json(200, action(body) if action else notes.add(**{k: body.get(k) for k in self.NOTE_KEYS}))
        except (ValueError, TypeError, KeyError) as e:
            self._json(400, {"error": str(e)})
        except OSError as e:  # the notes' lock or file busy past its tries (TimeoutError is one)
            self._json(503, {"error": str(e)})

    def log_request(self, code="-", size="-"):
        if str(code).isdigit() and int(code) >= 400:  # only what failed goes in the server's log
            self.log_message('"%s" %s', self.requestline, code)

    def log_message(self, fmt, *args):
        sys.stderr.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {fmt % args}\n")


_painter = None  # the levels' paint, while it runs


def _painting():
    return _painter is not None and _painter.poll() is None


def _paint_levels():
    """Start painting the levels (python -m tool.levels) unless it's painting already."""
    global _painter
    if not _painting():
        _painter = subprocess.Popen([sys.executable, "-m", "tool.levels"], cwd=paths.REPO,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return True


class Server(http.server.ThreadingHTTPServer):
    # Windows lets a second server bind a port in use when the address is reused, so there the bind
    # must fail: two servers never run different code on PORT. The Mac keeps its fast restarts.
    allow_reuse_address = os.name != "nt"


def start(port=PORT):
    """Serve in a background thread. port 0 picks a free one. Returns the server."""
    server = Server(("127.0.0.1", port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def ours():
    """Whether a server of ours already answers on PORT (its /api/health)."""
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/health", timeout=1) as r:
            return r.status == 200
    except OSError:
        return False


def serve(page, label, open_tab=True):
    """http://localhost:PORT/<page>, served from here until stopped (unless one of ours already
    answers on the port), and opened in the browser."""
    url = f"http://localhost:{PORT}/{page}"
    if ours():
        print(f"{label}: {url} (a server of ours is up already)", flush=True)
        if open_tab:
            webbrowser.open(url)
        return
    try:
        start(PORT)
    except OSError as e:
        raise SystemExit(f"port {PORT} is held by something that isn't the tool's server ({e}): "
                         "`PY -m tool.doctor server` sorts it out")
    print(f"{label}: {url} (pid {os.getpid()})", flush=True)
    if open_tab:
        webbrowser.open(url)
    threading.Event().wait()
