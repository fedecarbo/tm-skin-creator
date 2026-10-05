"""What the tool is doing, for the Lab's chat: the user has no terminal, so every command that makes
them wait reports its job and its stages here, and the chat shows one widget per job (the user,
2026-10-04: "it would be nice to have progress indicators when it's doing something").

    with progress.job("Painting Snow", skin="TSC_Snow", done="Painted and photographed"):
        progress.stage("Painting")
        progress.detail("Reflective band")         # a smaller line under the stage
        progress.stage("Taking pictures", total=6)
        progress.tick()                            # 1 of 6 ...

Each job is a file in the work folder's progress/ folder, replaced whole at each change and every
BEAT seconds while it runs; the viewer's server reads them all (`jobs`, /api/progress). A job whose
file stops beating (its process killed) reads as stopped after STALE seconds, and a finished one
stays KEEP seconds as a single line, then its file goes. A job opened inside another in the same
process (a snapshot inside a show) adds no widget: its stages are the outer job's. Without a job
the calls do nothing, so the code under them runs the same from anywhere (the self-test's children).

A job can outlive its process (`hand_over`): the fresh eyes (tool/eyes.py) look at a car in Claude's
own session, after the command that took their pictures has ended. It runs on, unbeaten, until
`finish` or the car's next job ends it, or reads as stopped after PATIENCE seconds.

Standard library only (and tool.paths, which is too)."""

import contextlib
import json
import os
import re
import threading
import time

from tool import paths

FOLDER = paths.WORK / "progress"
BEAT = 5  # seconds between a running job's beats
STALE = 30  # seconds without a beat: the job stopped without finishing
PATIENCE = 600  # seconds a job handed over runs on without a beat
KEEP = 600  # seconds a finished job stays in the chat

_current = None


def title_of(name):
    """A skin's name as the Lab writes it (lab-common.js, titleOf): TSC_RedFlash -> Red Flash."""
    return re.sub(r"([a-z])(?=[A-Z])", r"\1 ", re.sub(r"^TSC_", "", name).replace("_", " "))


class Job:
    def __init__(self, title, skin, done):
        self.lock = threading.Lock()
        now = time.time()
        self.file = FOLDER / f"{int(now * 1000)}-{os.getpid()}.json"
        self.doc = {"title": title, "skin": skin, "started": now, "beat": now, "stage": "", "count": None,
                    "detail": "", "ended": None, "result": done or "Done", "failed": None}
        self.stop = threading.Event()
        self.handed = False

    def write(self, **changes):
        with self.lock:
            self.doc.update(changes, beat=time.time())
            try:
                paths.write(self.file, json.dumps(self.doc))
            except OSError:
                pass  # the chat misses one change; the job goes on

    def beat(self):
        while not self.stop.wait(BEAT):
            self.write()


@contextlib.contextmanager
def job(title, skin=None, done=None):
    """A job the user waits for, as one widget in the Lab's chat. title: what it is, in plain words
    ("Painting Snow"); skin: the car whose chat shows it (None: every car's); done: the line it
    settles into ("Painted and photographed"), the time taken added to it."""
    global _current
    if _current is not None:
        yield _current
        return
    if skin:
        finish(skin)  # the car's job handed over ends where its next one starts
    j = _current = Job(title, skin, done)
    j.write()
    threading.Thread(target=j.beat, daemon=True).start()
    try:
        yield j
    except KeyboardInterrupt:
        j.doc["failed"] = "Stopped"
        raise
    except SystemExit as e:
        if e.code not in (None, 0) and not j.doc["failed"]:
            j.doc["failed"] = str(e.code) if isinstance(e.code, str) else "Stopped with a problem"
        raise
    except Exception as e:
        j.doc["failed"] = f"Stopped: {type(e).__name__}"
        raise
    finally:
        j.stop.set()
        if not j.handed or j.doc["failed"]:
            j.write(ended=time.time())
        _current = None


def hand_over(text):
    """Leave the job running when this process ends, at the stage `text` (a pulse), for `finish`."""
    if _current:
        _current.handed = True
        _current.write(stage=text, count=None, detail="", handed=True)


def finish(skin, result=None):
    """End the car's job handed over, if one runs, settling it into `result` (else its own)."""
    for f in sorted(FOLDER.glob("*.json")) if FOLDER.is_dir() else ():
        try:
            doc = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if doc.get("handed") and doc.get("skin") == skin and not doc.get("ended"):
            now = time.time()
            doc.update(ended=now, beat=now, result=result or doc["result"])
            with contextlib.suppress(OSError):
                paths.write(f, json.dumps(doc))


def stage(text, total=None):
    """The job's next stage; total: how many there are to do, when known (a bar, ticked)."""
    if _current:
        _current.write(stage=text, count=[0, total] if total else None, detail="")


def tick(n=1):
    if _current and _current.doc["count"]:
        done, total = _current.doc["count"]
        _current.write(count=[min(done + n, total), total])


def detail(text):
    """A smaller line under the stage: the step being painted, the skin being checked."""
    if _current:
        _current.write(detail=text)


def result(text, failed=False):
    """The line the job settles into, decided while it runs (the self-test's verdict)."""
    if _current:
        _current.doc["failed" if failed else "result"] = text


def jobs():
    """Every job for the Lab, oldest first, each with its state: running, done, failed or stopped.
    Finished ones older than KEEP are deleted on the way."""
    now = time.time()
    out = []
    for f in sorted(FOLDER.glob("*.json")) if FOLDER.is_dir() else ():
        try:
            doc = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue  # being replaced: the next ask
        end = doc.get("ended") or (doc["beat"] if now - doc["beat"] > (PATIENCE if doc.get("handed") else STALE) else None)
        if end and now - end > KEEP:
            with contextlib.suppress(OSError):
                f.unlink()
            continue
        doc["state"] = ("failed" if doc.get("failed") else "done") if doc.get("ended") else "stopped" if end else "running"
        doc["id"] = f.stem
        out.append(doc)
    return {"now": now, "jobs": out}
