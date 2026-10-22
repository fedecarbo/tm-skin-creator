# How the AI sees the car: the exploration of 2026-10-22

The user: "things written in mds are prone to fail every now and then ... there has to be a better way for AI to
'see' the car without a written essay"; then: "I just want perfectly painted cars. The accuracy bit." The decision
taken: the car does the seeing, never the AI's eye (its reply of that day, and the road that follows).

Throwaway samples, drawn from the car's own mesh, not the tool (run from the repo root with the tool's Python). The
question sample became the tool's own: `PY -m tool.meshlines` and its questions (the road's step 14).

- `atlas.py`: the car drawn flat with its lines numbered and panels lettered, and a card per line with its course's
  start and end named (pictures in the work folder's `build/see_*.png` when drawn).
- The dry run sample (a design run against the car before any paint, every call's landing printed and sketched) became
  the tool's own, `PY -m tool.skin read` (the road's step 15). Its evidence: the 21 October mistake
  (`designs/wrongend_design.py`) caught in 12 s; the self-test's tour in 69 s and 5.7 GB (`control/dryrun_tour.txt`).

The quiz (`quiz/`): ten questions with the key computed from the mesh as the car answered on 2026-10-22 (since step
14 every course runs nose first, so Q2's stretch is the front one); eight fresh agents, two per way of seeing.
Today's footing 9 and 9 (both blind on which end a course starts at; one answered the 21 October mistake), the
atlas 10 and 10, the question tool 10 and 10, both 10 and 10 (`quiz/scores.md`; the answers in `quiz/answers/`).

The control test (`control/`): the same brief painted by two fresh agents, TSC_SeeControl on today's footing (three
paints, 13 blocks in the first) and TSC_SeeTest on the new (`control/test_footing.md`: one paint after three dry runs),
both in `skins/` until the user has looked, then deleted (git keeps them).
