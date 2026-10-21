"""The tool's web server: Python's own, on this computer only (ES modules don't load from file://). It serves a page
folder at / and the work folder's viewer data at /data/ (tool/view.py), answers /api/health, and nothing else: the
Lab's own routes are tool/labserver.py's, a handler built on this one.

  /        the page folder: the repo's viewer/ by default (the camera: index.html?skin=<name>&snap=1 for the tool's
           snapshots, tool/snap.py; the Lab's page too, served by tool/labserver.py)
  /data/   the work folder's viewer/ folder: the car, the lighting, the skins (tool/view.py)
  /api/health   alive: its pid and the age of the code it runs (tool/labdoctor.py restarts an old one)

start(0) serves on a free port for a hidden browser (tool/snap.py, tool/close.py, tool/tyresheet.py); serve() is how
the tool opens a page for the user: it serves on PORT unless a server of ours already answers there (/api/health; it
reads the same folders), and opens the page. Reads are open to any origin: a page from another folder (a concept's)
may read the data.
"""

import http.server
import json
import os
import sys
import threading
import time
import urllib.parse
import urllib.request
import webbrowser

from tool import paths, view

PORT = 8765
STARTED = time.time()
# the tool's code as this server loaded it: tool/labdoctor.py restarts a server older than the code on disk
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
            self.directory = str(self.server.root)
        return super().translate_path(path)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        if self.command == "GET":  # reads are open to a page from another origin; writes aren't
            self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if urllib.parse.urlsplit(self.path).path == "/api/health":  # alive, and how old its code is
            return self._json(200, {"ok": True, "pid": os.getpid(), "started": STARTED, "code": CODE})
        return super().do_GET()

    def log_request(self, code="-", size="-"):
        if str(code).isdigit() and int(code) >= 400:  # only what failed goes in the server's log
            self.log_message('"%s" %s', self.requestline, code)

    def log_message(self, fmt, *args):
        sys.stderr.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {fmt % args}\n")


class Server(http.server.ThreadingHTTPServer):
    # Windows lets a second server bind a port in use when the address is reused, so there the bind
    # must fail: two servers never run different code on PORT. The Mac keeps its fast restarts.
    allow_reuse_address = os.name != "nt"
    request_queue_size = 64  # a page may ask for every car's maps at once: none refused

    def __init__(self, address, handler, root):
        super().__init__(address, handler)
        self.root = root


def start(port=PORT, root=None, handler=Handler):
    """Serve in a background thread. port 0 picks a free one; root, the page folder (the camera's, viewer/, by
    default); handler, the routes (a concept's own). Returns the server."""
    server = Server(("127.0.0.1", port), handler, root or paths.REPO / "viewer")
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def ours():
    """Whether a server of ours already answers on PORT (its /api/health)."""
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/health", timeout=1) as r:
            return r.status == 200
    except OSError:  # nothing answers
        return False


def serve(page, label, open_tab=True, root=None, handler=Handler):
    """http://localhost:PORT/<page>, served from here until stopped (unless one of ours already
    answers on the port), and opened in the browser."""
    url = f"http://localhost:{PORT}/{page}"
    if ours():
        print(f"{label}: {url} (a server of ours is up already)", flush=True)
        if open_tab:
            webbrowser.open(url)
        return
    try:
        start(PORT, root, handler)
    except OSError as e:
        raise SystemExit(f"port {PORT} is held by something that isn't the tool's server ({e}): "
                         "`PY -m tool.labdoctor server` sorts it out")
    print(f"{label}: {url} (pid {os.getpid()})", flush=True)
    if open_tab:
        webbrowser.open(url)
    threading.Event().wait()
