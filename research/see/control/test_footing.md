# The new footing: the car does the seeing (read this before painting)

`SEE` is /private/tmp/claude-501/-Users-fcarbo-Developer-personal-tm-skin-creator/d6323ffa-b930-4235-8278-bb2973c2c74f/scratchpad/see
and `PY` the tool's Python, /Users/fcarbo/Developer/personal/tm-skin-creator/.venv/bin/python, run from the repo root.

1. **Ask the car, don't read about it.** Do not open `car/anatomy.md` or `car/map/model.jpg`. Every fact about the
   car's shape comes from `PY $SEE/ask.py ...` (run it with no arguments for its questions: `line`, `panel`, `part`,
   `at x y z`, `paint <where>`, `flat <part>`, `stretch <line> nose|tail <cm>`, `find <word>`, `list`). Its answers
   are exact and come from the mesh. Ask before every call that names a line, a panel, a part or a point; when a
   line's course runs tail first, it tells you and gives the call to write. The paint skill, the paint box's
   docstring and the tools' docstrings are read as usual.
2. **Check before you paint.** Before every `PY -m tool.skin show <name>`, run
   `PY $SEE/dryrun.py skins/<name>/design.py` (about 15 to 70 s). It runs the design against the car without painting
   anything anyone sees and prints, call by call, where each stroke lands (z front to back, y, x, the parts under
   it, its area, the receipt) and draws a sketch (`$SEE/out/dryrun_<name>.png`: look at it). Read every line against
   the brief: a stretch at the wrong end, a zone on the wrong parts, a stroke that lands nowhere, a part left in clay.
   Fix the design and dry-run again until every stroke lands where the brief says. Only then `show`.
3. **Your eye on a picture is never the check.** Do not use the six views or the close looks' pictures to decide a
   stroke is right: the dry run's numbers, the judge's verdict and the close looks' measured findings decide. You
   may look at the pictures, but every claim in your report must cite a number (the dry run, a receipt, the verdict).
