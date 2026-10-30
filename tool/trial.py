"""The trial: a fresh Claude session paints a throwaway car from a few words with nothing but the instructions, so what
fails any AI painting with the tool is found by one (the user, 2026-10-30: "the tools are optimised so that any agent
can use them with efficiency and efficacy").

    python -m tool.trial "<a few words>" [--car TSC_Trial<MMDD>] [--model <model>]

It runs `claude -p --agent trial-painter` (.claude/agents/trial-painter.md) as a session of its own, not an agent of
the session that starts it: only a session can start the agents the craft's passes ask for, and it gets the hooks and
gates any painting session gets. The user's memory is off in it, so it knows only the repo. Its log (stream-json) goes in
the work folder, trials/<car>/, a job in the Lab while it runs; then its numbers (minutes, turns, tool calls and which,
the calls that failed, the agents it started, the cost, the gate on the car), beside the last trial's, and the
painter's report. Heavy: it paints, so nothing else does while it runs. The words: what a user might say, picked to
try what changed since the last trial.

Then, in the session that ran it: the car shown to the user in the Lab, as any car is; each finding of the report put
where it prevents the mistake (a docstring, the skill, under WORDS) or kept as the tool's for the steward
(`ledger.miss(car, "the trial painter", what)`); committed with `Upkeep: trial-painter` as the message's last line
(tool/doctor.py dates the next trial from it); on the user's look, the car deleted.
"""

import argparse
import json
import os
import shutil
import subprocess
import time
from collections import Counter
from pathlib import Path

from tool import gate, paths, progress

TOOLS = "Bash,Read,Edit,Write,Glob,Grep,Agent,Skill"  # what a painting session uses, allowed without asking


def _claude():
    found = shutil.which("claude") or next((str(p) for p in (Path.home() / ".local/bin/claude",
                                                              Path.home() / ".local/bin/claude.exe") if p.exists()), None)
    if not found:
        raise SystemExit("Claude Code's command isn't here: install it (claude.com/claude-code), then again")
    return found


def numbers(log):
    """The run's numbers, from its stream-json log."""
    by, failed, result = Counter(), 0, {}
    for line in log.read_text(encoding="utf-8").splitlines():
        try:
            e = json.loads(line)
        except ValueError:  # a line that isn't an event: the session's own words
            continue
        content = (e.get("message") or {}).get("content")
        for c in content if isinstance(content, list) else ():
            if e["type"] == "assistant" and c.get("type") == "tool_use":
                by[c["name"]] += 1
            failed += e["type"] == "user" and c.get("type") == "tool_result" and bool(c.get("is_error"))
        if e.get("type") == "result":
            result = e
    return {"minutes": round(result.get("duration_ms", 0) / 60000, 1), "turns": result.get("num_turns"),
            "calls": sum(by.values()), "failed": failed, "agents": by["Agent"] + by["Task"],
            "cost": round(result.get("total_cost_usd") or 0, 2), "by": dict(by.most_common()),
            "report": result.get("result", "(no report: the session ended without one)")}


def _line(n, gated):
    return (f"{n['minutes']} minutes, {n['turns']} turns, {n['calls']} tool calls ({n['failed']} failed), "
            f"{n['agents']} agents, ${n['cost']}; the gate: {gated}")


def run(words, car, model=None):
    folder = paths.WORK / "trials" / car
    if (paths.SKINS / car).exists():
        raise SystemExit(f"{car} exists already: a trial paints a new car (--car another name)")
    folder.mkdir(parents=True, exist_ok=True)
    cmd = [_claude(), "-p", f"The car: {car}. The user's words: {words}", "--agent", "trial-painter",
           "--output-format", "stream-json", "--verbose", "--permission-mode", "acceptEdits", "--allowedTools", TOOLS]
    env = {**os.environ, "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"}
    with progress.job(f"A trial: a fresh session paints {car}", skin=car, done="Trial painted"), \
            open(folder / "log.jsonl", "w", encoding="utf-8") as log, open(folder / "errors.txt", "w") as err:
        progress.stage("Painting from the instructions alone")
        p = subprocess.Popen(cmd + (["--model", model] if model else []), cwd=paths.REPO, env=env, text=True,
                             encoding="utf-8", stdout=subprocess.PIPE, stderr=err)
        calls = 0
        for line in p.stdout:
            log.write(line)
            log.flush()
            if '"tool_use"' in line:
                calls += 1
                progress.detail(f"{calls} tool calls")
        p.wait()
    n = numbers(folder / "log.jsonl")
    gated = "; ".join(line for _, line in gate.wrong(car)) or "passes"
    last = max((f for f in (paths.WORK / "trials").glob("*/numbers.json") if f.parent.name != car),
               key=lambda f: f.stat().st_mtime, default=None)
    (folder / "numbers.json").write_text(json.dumps({"car": car, "words": words, "when": time.strftime("%Y-%m-%d %H:%M"),
                                                      "gate": gated, **n}, indent=1), encoding="utf-8")
    print(f"{car}: {_line(n, gated)}")
    print(f"  the calls: {', '.join(f'{k} {v}' for k, v in n['by'].items())}")
    if last:
        o = json.loads(last.read_text(encoding="utf-8"))
        print(f"the last trial, {o['car']} ({o['when']}): {_line(o, o['gate'])}")
    print(f"\nThe painter's report:\n{n['report']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("words")
    ap.add_argument("--car", default=f"TSC_Trial{time.strftime('%m%d')}")
    ap.add_argument("--model")
    a = ap.parse_args()
    run(a.words, a.car, a.model)


if __name__ == "__main__":
    main()
