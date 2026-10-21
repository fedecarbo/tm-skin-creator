# Visual QA and judges for AI-made 3D designs (state of practice, October 2026)

Scope: how AI systems automatically check rendered 3D/visual output (VLM judges, render-in-the-loop agents,
deterministic geometric/image checks, calibration to human judgement, verification gates), and what that means for
the skin tool, where three checkers (reach measurer, flaw checks, eye) and six-view snapshots all missed gaps and
steps in tapes that the user saw at once up close.

Local facts used below (read from the repo on 2026-10-07, not from the web): `tool/record.json` holds 45 recorded
flaws; only 5 can be painted again and scored (the "5 of 5" score); 25 of the 45 are of kind `line` ("a line that
isn't smooth or doesn't sit where it should"), and none of the 5 scorable ones is a `line` or `gap`; the
TSC_StealthBomber tape complaints are not in the set. `.claude/settings.json` already has a Stop hook
(`tool/guard.py pushed`) and a PreToolUse hook (`tool/guard.py folder`). IMPROVEMENTS.md H.3-H.5 already plan a line
check, travelling close looks and gates.

## 1. VLMs as judges of renders and designs: how reliable, and what helps

### Takeaway
Frontier VLMs are useful for ranking whole designs and for "does it match the brief" questions, but they are
systematically weak at exactly the class of defect that slipped through here: thin, low-level, local discrepancies
(a gap a few pixels wide, a small step, a slight kink). Their reliability rises sharply when the defect is made
large in the frame (crops/zoom along the feature), when they compare rather than score, and when they answer narrow
checklist questions; but even then they should be a second line behind measurement, not the gate.

### Cited Findings
**3D-specific VLM judges (benchmarks and evaluators)**
- GPTEval3D (CVPR 2024) used GPT-4V as a pairwise judge of text-to-3D assets: it is fed 120 RGB plus normal-map
  renders per asset, compares two assets against user-defined criteria, and turns the pairwise wins into Elo
  ratings; the authors report strong alignment with human preference across criteria —
  [CVPR 2024 paper](https://openaccess.thecvf.com/content/CVPR2024/papers/Wu_GPT-4Vision_is_a_Human-Aligned_Evaluator_for_Text-to-3D_Generation_CVPR_2024_paper.pdf); [arXiv 2401.04092](https://arxiv.org/pdf/2401.04092)
- 3DGen-Bench (2025) built a large multi-dimension human-preference dataset (public plus expert annotators) and
  trained 3DGen-Score, a CLIP-based scorer over prompt, RGB and normal-view embeddings (contrastive alignment, then
  preference fitting), which correlates with human ranks better than generic CLIP or aesthetic predictors; intended
  uses include RLHF rewards and "fine-grained sample-level diagnostic evaluation" —
  [arXiv 2503.21745](https://arxiv.org/html/2503.21745v2)
- Eval3D (CVPR 2025) argues that "existing 3D evaluation metrics often overlook the geometric quality ... or merely
  rely on black-box multimodal large language models for coarse assessment"; it instead measures
  *inconsistency among several foundation models and tools used as probes*, giving pixel-wise, 3D-localised
  feedback that aligns more closely with human judgement —
  [CVPR 2025 poster](https://cvpr.thecvf.com/virtual/2025/poster/35203); [code](https://github.com/eval3d/eval3d-codebase)
- Hi3DEval (NeurIPS 2025) adds part-level (not just object-level) evaluation and material checks (albedo,
  saturation, metallicness), using a hybrid of video-based and 3D-based representations, because image-based
  object-level metrics miss "spatial coherence, material authenticity, and high-fidelity local details" —
  [arXiv 2508.05609](https://arxiv.org/html/2508.05609v1)
- Superseded: GPT-4V-era single-VLM pairwise judging (GPTEval3D) has been overtaken for asset evaluation by
  trained or probe-based evaluators (3DGen-Score, Eval3D, Hi3DEval) that explicitly target local/part detail —
  same sources as above.

**Reliability studies of VLM-as-a-judge**
- BlenderGym (CVPR 2025): VLM verifiers comparing pairs of renders agreed with humans 0.66 of the time
  (Claude 3.5 Sonnet) against 0.79 human-human agreement over 7,950 pairwise judgements from 50 people; "even the
  state-of-the-art VLM system struggles with tasks relatively easy for human Blender users" —
  [arXiv 2504.01786](https://arxiv.org/html/2504.01786v1)
- "VLM Judges Can Rank but Cannot Score" (April 2026): judges (LLaVA-Critic-7B, Phi-4-reasoning-vision-15B,
  Gemini 2.5 Flash) show "ranking-scoring decoupling": decent ordering but 90% conformal intervals spanning roughly
  40% (aesthetics) to 70% (charts/maths) of the score range; Pearson 0.30-0.46 with humans overall; recommendation:
  prefer pairwise comparison where intervals are wide, and use conformal prediction (R2CCP) to know when a score can
  be trusted — [arXiv 2604.25235](https://arxiv.org/html/2604.25235v1)
- "Fooling the LVLM Judges" (2025): "all tested LVLM judges exhibit vulnerability across all domains, consistently
  inflating scores for manipulated images"; biases compound and "persist under prompt-based mitigation strategies";
  pairwise comparison is equally vulnerable — [arXiv 2505.15249](https://arxiv.org/abs/2505.15249)
- Informativeness bias: VLM judges favour more informative answers even when they conflict with the image
  (ACL 2026); a mitigation (BIRCH) reduces it by up to 17% —
  [ACL Anthology 2026.acl-long.703](https://aclanthology.org/2026.acl-long.703/)

**Fine visual defects: the known weakness**
- BlindTest ("Vision language models are blind", ACCV 2024): on seven trivially simple tasks (do two circles
  overlap, how many times do two lines intersect, ...) GPT-4o, Gemini-1.5 Pro, Claude 3 Sonnet and Claude 3.5
  Sonnet averaged 58.07%, best 77.84% (Claude 3.5 Sonnet), against an expected 100% for humans; linear probes on the
  vision encoders solve the tasks at >=99.47%, so the information is encoded but lost when decoded into language —
  [arXiv 2407.06581](https://arxiv.org/html/2407.06581v4). (Models are superseded; the failure class persists, see next.)
- VDiff-Bench (Sept 2026), fine-grained image-difference identification over 1,756 four-way questions and 10 change
  categories, 11 current MLLMs: best Gemini 3.1 Pro 89.6%, worst 34.5%; "persistent failures on subtle low-level
  changes like noises and textures"; smaller models answered "no difference" on 51.3-80.9% of low-level questions
  although every pair differed; "scale alone is insufficient" —
  [HF papers 2609.06245](https://huggingface.co/papers/2609.06245)
- MLLM accuracy is "very sensitive to the size of the visual subject of the question" (shown causally), and models
  "consistently know where to look, even when they provide the wrong answer"; training-free cropping (ViCrop, from
  attention/gradient maps) significantly improves small-detail perception (ICLR 2025) —
  [arXiv 2502.17422](https://arxiv.org/abs/2502.17422). Zoom-Refine (2025) is a similar training-free loop: find the
  task-relevant region, zoom, and refine the first answer with the detail —
  [arXiv 2506.01663](https://arxiv.org/abs/2506.01663)
- Claude's own documentation: images are seen as 28x28-pixel patches (visual tokens); Claude 4.7 and later get a
  high-resolution tier (2576 px long edge, 4784 tokens), other models 1568 px / 1568 tokens; larger images are
  downscaled; "Spatial reasoning: Claude's coordinate and localization outputs are approximate"; counting of many
  small objects may be inaccurate; "Do not use Claude for tasks requiring perfect precision ... without human
  oversight"; images work best placed before the text; label multiple images "Image 1:", "Image 2:" for comparison —
  [Claude vision docs](https://platform.claude.com/docs/en/build-with-claude/vision)

**Techniques that help (with evidence)**
- Pointwise checklists of validation questions: CADCodeVerify (ICLR 2025) has the VLM generate and answer
  validation questions about the rendered object, then correct deviations; 7.30% lower point-cloud distance and
  5.5% higher compile rate for GPT-4 versus prior work — [arXiv 2410.05340](https://arxiv.org/html/2410.05340v2)
- An explicit approval checklist ("a concrete, actionable todo list of visual discrepancies") fed back to the
  generator, plus arbitrary-view renders and isolating single objects for focused inspection (Thinking in Blender,
  June 2026, Claude Opus 4.7 as both generator and verifier) — [arXiv 2606.02580](https://arxiv.org/html/2606.02580)
- Multi-view: LL3M's critic renders 5 views; GPTEval3D uses 120 renders including normal maps —
  [arXiv 2508.08228](https://arxiv.org/html/2508.08228v1); [arXiv 2401.04092](https://arxiv.org/pdf/2401.04092)
- Inference-scaling the verifier (re-selecting several times) lets a small VLM (InternVL2-8B) beat unscaled GPT-4o
  and Claude 3.5 Sonnet as verifier; at high budgets (>100 queries) spending ~0.73 of compute on verification beat
  spending more on generation — [BlenderGym](https://arxiv.org/html/2504.01786v1)
- Separate, isolated judges per dimension, an "Unknown" escape hatch, and calibration against humans —
  [Anthropic, Demystifying evals for AI agents](https://anthropic.com/engineering/demystifying-evals-for-ai-agents)
- Combining measurements with images: in 3DHarnessBench (Sept 2026) giving Claude Opus 5 explicit global and
  part-level geometric measurements alongside images cut Chamfer distance from 0.0150 to 0.0084 (44%); "All
  measurement settings improve geometry over image-only input" — [arXiv 2609.06535](https://arxiv.org/html/2609.06535)

### Inferences
- The six full-car snapshots were the wrong instrument for 0.5-2 cm defects. Illustrative arithmetic (assumption:
  a car roughly 4 m long filling a 2576 px frame): ~0.16 cm per pixel, so a 1 cm gap is ~6 px, about a fifth of one
  28 px visual token, and less on the standard tier or in a foreshortened view. VDiff-Bench and the size-sensitivity
  result predict a strong "looks fine" bias at that scale. A close look at ~20 px/cm makes the same gap ~20 px.
- Ask the VLM narrow, falsifiable questions on crops ("Along this tape, from left to right, is there any place where
  the body colour shows through between the two edges? Answer yes/no/unknown and give the x position"), never "does
  this look good". Absolute 1-10 scores from a VLM are not trustworthy as thresholds (rank-but-cannot-score).
- A VLM answer can be cross-checked: when it gives a coordinate, the tool can measure there; disagreement between
  VLM and measurement is itself a signal worth showing.

### Gaps
- No published benchmark found that measures VLM recall specifically on thin painted bands/decals on curved 3D
  surfaces (livery-like content); the numbers above are from adjacent tasks.
- T3Bench and other 2023-24 text-to-3D benchmarks were not re-checked in this pass.
- No public number found for Claude Opus 5 / 5.5 on BlindTest-style or VDiff-style low-level tasks.

## 2. Render-in-the-loop agents: how critique and edit loops are structured

### Takeaway
The field has converged on generator + separate verifier loops over code that renders: render (multi-view), critique
into a concrete checklist, edit locally (not regenerate), re-render, verify each checklist item was fixed, and
revert when the render got worse; bounded by per-stage iteration budgets (typically 2-5 rounds). Every paper that
reports failure modes says the VLM critic still misses spatial artefacts, and the strongest 2026 result shows that
adding explicit measurements beats adding more looking.

### Cited Findings
- BlenderAlchemy (ECCV 2024): iteratively refines a Blender Python program with a vision-based edit generator and a
  state evaluator searching the design space; adds "visual imagination" (text-to-image) to turn a text goal into a
  visual target — [arXiv 2404.17672](https://arxiv.org/html/2404.17672v1)
- SceneCraft (ICML 2024): inner loop renders the scene and an "LLM-Reviewer with vision perception" criticises the
  render and updates the script; outer loop grows a reusable "spatial skill" library; plans a scene graph first and
  turns relations into numeric layout constraints — [arXiv 2403.01248](https://arxiv.org/html/2403.01248v1)
- LL3M (Aug 2025): six agents (planner, retrieval, coding, critic, verification, user proxy); the critic renders
  m=5 views and asks Gemini for "the visual issues and suggested fixes"; a separate verification agent re-renders,
  compares against previous renders and the critique list, and "verifies whether the proposed solutions of each
  critique have been successfully applied"; shared code context makes edits local (without it, the coder regenerates
  a different asset); limits: VLMs "may still struggle to accurately identify spatial artifacts" (a watering-can
  handle stayed disconnected after auto-refinement; placing an object in a hand took 3-4 user follow-ups) —
  [arXiv 2508.08228](https://arxiv.org/html/2508.08228v1)
- BlenderGym (CVPR 2025): generator = brainstormer (names visual differences between current and goal renders) +
  code editor, with breadth b and depth d; verifier does pairwise elimination between renders; verification compute
  is worth scaling — [arXiv 2504.01786](https://arxiv.org/html/2504.01786v1)
- CADCodeVerify (ICLR 2025): VLM-generated validation questions answered on renders drive correction —
  [arXiv 2410.05340](https://arxiv.org/html/2410.05340v2)
- Thinking in Blender / SEIG (June 2026): five stages (initialisation, geometry, material, composition, lighting)
  with round budgets of 5/3/3/2; verifier approves advance or returns an approval checklist; agents "revert
  unsuccessful edits when visual feedback indicates a regression"; when a budget runs out "the verifier must select
  the best attempt"; Claude Opus 4.7 was both generator and verifier — [arXiv 2606.02580](https://arxiv.org/html/2606.02580)
- 3DHarnessBench (Sept 2026): one generation + three render-and-refine iterations; refinement gains were "modest"
  compared with giving agents active viewing / full 3D interaction; Claude Fable 5 and Opus 5 were the strongest
  agents; Gemini 3.1 Pro "performed little inspection and tends to terminate early" (8.00 inspection calls on
  average); measurements gave the largest geometry gains (Chamfer -44% for Opus 5) — [arXiv 2609.06535](https://arxiv.org/html/2609.06535)
- 3DCodeBench (June 2026) uses a VLM "Visual Critic" comparing multi-view renders against the reference —
  [arXiv 2606.01057](https://arxiv.org/html/2606.01057v1)

### Inferences
- Patterns worth copying: (a) critique as a checklist of located items, each verified closed on the next render;
  (b) local edits with the whole design in context; (c) explicit regression detection with revert; (d) a fixed round
  budget per stage, then "best attempt" plus an honest report rather than another silent loop.
- Anti-pattern seen in the tool's latest car: a verifier that looks at the whole object from fixed views and is the
  same agent that made the edit. Every paper's failure list (missed disconnections, early termination) is the
  StealthBomber failure in other words.
- Regression detection is cheap for this tool because its renders are deterministic: diff the new close looks
  against the previous ones outside the region the change meant to touch.

### Gaps
- None of the papers report how often their verifier passed a design that humans then rejected (false-accept rate);
  only aggregate quality metrics are reported.
- VideoCAD and other CAD-agent papers were not examined in detail in this pass.

## 3. Deterministic geometric and image checks for thin defects

### Takeaway
For thin bands, gaps, steps and kinks, deterministic measurement on the paint as it actually lands (texels on the
mesh, or an ID/mask render) is far more reliable than any learned judge: sample along the line's arc length and
measure width, coverage, lateral offset and turning angle; count connected components; and diff renders between
versions at the pixel level. Perceptual metrics (LPIPS, DreamSim) and aesthetic scores are the wrong tools for
these defects.

### Cited Findings
- Local width along a shape: scikit-image's `medial_axis(..., return_distance=True)` returns the distance transform
  with the skeleton; multiplying the two gives "an estimate of the local width of the objects" at each skeleton
  point; `skeletonize` gives fewer branches — [scikit-image skeleton example](https://scikit-image.org/docs/stable/auto_examples/edges/plot_skeleton.html)
- Golden-image regression: Playwright's `toHaveScreenshot()` captures repeatedly "until two consecutive screenshots
  matched" before saving a baseline, compares with pixelmatch, accepts tolerances such as `maxDiffPixels`, and keeps
  baselines per platform/browser because "rendering, fonts and more" differ; `--update-snapshots` regenerates —
  [Playwright visual comparisons](https://playwright.dev/docs/test-snapshots)
- pixelmatch defaults: `threshold` 0.1 (perceptual colour difference, 0-1), `includeAA` false (pixels detected as
  anti-aliasing are not counted as differences), `diffMask`, `alpha`; colour difference in OKLab with the HyAB
  distance — [mapbox/pixelmatch](https://github.com/mapbox/pixelmatch)
- Perceptual similarity: DreamSim (NeurIPS 2023) matches human similarity judgements better than LPIPS and DINO/CLIP
  embeddings but "focuses heavily on foreground objects and semantic content" (layout, pose, semantics) —
  [DreamSim](https://proceedings.neurips.cc/paper_files/paper/2023/hash/9f09f316a3eaf59d9ced5ffaefe97e0f-Abstract.html);
  LPIPS, DISTS and Q-Align are packaged in pyiqa (`pyiqa.create_metric('lpips')`) — [pyiqa](https://pypi.org/project/pyiqa)
- Measurement beats images for geometry in agent loops (3DHarnessBench, -44% Chamfer with measurements) —
  [arXiv 2609.06535](https://arxiv.org/html/2609.06535)
- Eval3D's design principle: consistency among independent probes localised pixel-wise is more faithful than a
  black-box VLM score — [CVPR 2025](https://cvpr.thecvf.com/virtual/2025/poster/35203)

### Inferences
Concrete checks for a painted band (tape, stripe, outline) drawn along a known line on the mesh, computed in cm on
the surface (the tool already maps texels to cm and knows which graphic painted each texel last):
- **Coverage/gap**: at every arc-length step s (e.g. 0.25-0.5 cm), take the cross-section on the surface
  perpendicular to the line and measure the painted width of *this* graphic on the face(s) the user sees. A gap is
  any run where width < 50% of target; any gap at all on a tape is a failure.
- **Width evenness**: coefficient of variation of the width along the line, and max deviation over any 2 cm window.
- **Step**: the painted centreline's lateral offset from the intended line, differenced between consecutive samples;
  a jump larger than a fraction of the width (e.g. > 25%) within one step is a step.
- **Kink**: turning angle of the painted centreline (in 3D, projected on the surface) per cm; a spike well above the
  model line's own turning at that point is a kink the design added.
- **Face hop**: the surface normal under the painted centre between consecutive samples; a jump over ~60 degrees
  means the band moved to another face (the diagnosed cause of the StealthBomber gaps).
- **Topology**: connected components of the graphic's texels with adjacency across UV seams (texel neighbours in 3D,
  not in the image); a tape that should be one piece and has two or more components has a break.
- **Seam continuity**: width and offset on both sides of every UV seam the line crosses must match within tolerance.
- **Screen-space confirmation**: render a flat-colour ID/mask pass of the graphic (no lighting, no mipmaps) in each
  travelling close look and run the same width/gap/skeleton measures in pixels; this catches viewer/texture-filtering
  effects the texel measure cannot see.
- **Regression diff**: pixelmatch-style diff (threshold ~0.1, AA excluded) of each close look against the previous
  version's; changed pixels outside the edited graphic's footprint mean the change touched something it should not.
- Use LPIPS/DreamSim only for "did the overall look drift" between versions, never for thin defects: they are built
  to ignore exactly the low-level differences that matter here.

### Gaps
- No off-the-shelf library found that measures band width along a curve on a UV-mapped mesh; it has to be built from
  the tool's own texel-to-surface mapping (skeleton/distance tools work per UV island in 2D only, and UV distortion
  must be corrected with the per-texel cm scale).
- Chromatic's visual-review workflow was not examined.

## 4. Calibrating automated checks against human judgement; aesthetic reward models

### Takeaway
The standard practice in 2025-26 is to build a small eval set from real failures (20-50 items), keep growing it as
new complaints arrive (criteria drift is normal), measure each check's recall and false-alarm rate against it, and
calibrate any model-based judge by reading where it disagrees with the human. A set that scores 100% gives no
signal. Generic aesthetic/preference reward models (LAION aesthetics, ImageReward, HPSv3, Q-Align) are trained on
whole text-to-image pictures and are not suited to judging livery craft defects.

### Cited Findings
- "20-50 simple tasks drawn from real failures is a great start"; model-based graders need "clear, structured
  rubrics", "an isolated LLM-as-judge rather than using one to grade all dimensions", an "Unknown" escape, and close
  calibration with human experts; "You won't know if your graders are working well unless you read the transcripts
  and grades"; "An eval at 100% tracks regressions but provides no signal for improvement"; pass@k (at least one of k
  succeeds) versus pass^k (all k succeed; at k=10 pass^k can fall to 0 while pass@k nears 100%) —
  [Anthropic, Demystifying evals for AI agents](https://anthropic.com/engineering/demystifying-evals-for-ai-agents)
- Criteria drift (EvalGen, UIST 2024): "users need criteria to grade outputs, but grading outputs helps users define
  criteria"; some criteria only appear after seeing outputs; LLM-generated evaluators "inherit all the problems of
  the LLMs they evaluate" and need human validation; EvalGen asks the human to grade a subset and keeps the
  assertion implementations that agree — [arXiv 2404.12272](https://arxiv.org/pdf/2404.12272)
- Calibrating a skeptical evaluator: few-shot examples "with detailed score breakdowns", reading the evaluator's logs
  to "find examples where its judgment diverged from mine" and updating its prompt, and a "hard threshold" per
  criterion where "if any one fell below it, the sprint failed"; frontend design was graded on design quality,
  originality, craft and functionality; 5-15 generator-evaluator iterations per design —
  [Anthropic, Harness design for long-running apps](https://www.anthropic.com/engineering/harness-design-long-running-apps)
- Conformal prediction gives a judge an interval per score and tells when absolute scores are unusable; annotation
  quality changed interval width 4.5x for the same judge — [arXiv 2604.25235](https://arxiv.org/html/2604.25235v1)
- HPSv3 (ICCV 2025): VLM-based preference model trained on 1.08M text-image pairs and 1.17M pairwise comparisons
  (HPDv3), Spearman 0.94 with human model rankings, 76.9% pairwise accuracy (+19.3 points over HPSv2); used to pick
  the best image per refinement step (Chain-of-Human-Preference) — [arXiv 2508.03789](https://arxiv.org/html/2508.03789v2)
- 3DGen-Score: preference model for 3D assets, ~0.7-0.85 agreement with humans per the search summary of the paper —
  [arXiv 2503.21745](https://arxiv.org/html/2503.21745v2) (figure from a summary, not verified in the paper body)
- Q-Align is available in pyiqa as a no-reference quality and aesthetic metric built on a large VLM —
  [pyiqa](https://pypi.org/project/pyiqa); ImageReward (2023), "the first general-purpose text-to-image human
  preference reward model", is trained on 137k expert comparisons — [arXiv 2304.05977](https://arxiv.org/abs/2304.05977);
  the LAION aesthetic predictor is a linear layer on CLIP image embeddings (ViT-L-14 or ViT-B-32) —
  [LAION-AI/aesthetic-predictor](https://github.com/LAION-AI/aesthetic-predictor). Superseded for preference scoring
  by VLM-based models such as HPSv3 (above).

### Inferences
- The tool's record is saturated and blind where it matters most: 5 of 5 scorable flaws caught, but `line` is the
  most common complaint (25 of 45) and none of those can be repainted, and the StealthBomber tape notes are not in
  it. By Anthropic's own criterion, a 100% score on 5 items "provides no signal".
- Precision matters as much as recall for a gate: a check that cries wolf trains the agent (and the user) to waive
  it. The record therefore needs negatives too: cars or regions the user OK'd up close, on which a blocking check
  must stay silent.
- Aesthetic reward models: not useful as gates here. They score a whole 2D picture against a prompt, were trained on
  photos and art, and a 1 cm gap barely moves them; they also embody a generic "taste" the project's rules
  explicitly refuse. At most they could rank takes, which the user does by eye. Recommend not adopting.
- A VLM judge, if kept, should be calibrated the EvalGen/Anthropic way: run it on the record's crops, read every
  disagreement, and only promote a question to blocking when its precision on the record is high (e.g. no false
  alarm on any OK'd car) and recall is measured.

### Gaps
- No published aesthetic or quality model trained on vehicle liveries or game skins was found.
- No source found quantifying how many labelled complaints are needed before a per-user check's thresholds are
  stable; the 20-50 figure is Anthropic's general guidance for agent evals.

## 5. Verification gates in agentic workflows

### Takeaway
Self-verification by the same model, from instructions alone, is the documented weak point: LLMs rarely find their
own errors without external feedback and tend to praise their own work. Reliable loops put ground truth from tools
in the way: separate evaluators, hard thresholds, and harness-level gates (hooks, CI, commands that refuse) that
the agent cannot forget or talk past.

### Cited Findings
- "LLMs struggle to self-correct their reasoning without external feedback, and in most instances, performance after
  self-correction even deteriorates"; earlier positive results relied on oracle feedback (ICLR 2024) —
  [arXiv 2310.01798](https://arxiv.org/html/2310.01798v2)
- Agents asked to evaluate their own output "tend to respond by confidently praising the work—even when, to a human
  observer, the quality is obviously mediocre"; fix: a separate evaluator agent tuned to be skeptical, with hard
  per-criterion thresholds and a "sprint contract" agreeing in advance what "done" means —
  [Anthropic, Harness design for long-running apps](https://www.anthropic.com/engineering/harness-design-long-running-apps);
  [InfoQ summary](https://infoq.com/news/2026/04/anthropic-three-agent-harness-ai/)
- Evaluator-optimizer workflow: "one LLM call generates a response while another provides evaluation and feedback in
  a loop"; fits when feedback demonstrably improves results and the LLM can give it; agents need "ground truth" from
  the environment (tool results, code execution) and stopping conditions such as a maximum number of iterations —
  [Anthropic, Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
- Claude Code hooks: exit code 2 is a "blocking error" on events that support it; a Stop hook returning
  `{"decision": "block", "reason": ...}` (or exit 2) prevents Claude from ending its turn and feeds the reason back;
  `additionalContext` adds non-blocking feedback; PreToolUse can return `permissionDecision: "deny"`; TaskCompleted
  can block completion; `type: "prompt"` and `type: "agent"` hooks let a model or a tool-using subagent decide (agent
  hooks marked experimental) — [Claude Code hooks reference](https://code.claude.com/docs/en/hooks)
- Loop safety: "The `stop_hook_active` field is `true` when Claude Code is already continuing as a result of a stop
  hook"; Claude Code caps stop-hook continuations at 8 in a row (resets when Claude calls a tool; adjustable with
  `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`) — [Claude Code hooks reference](https://code.claude.com/docs/en/hooks)
- Known issue (2025): Stop hooks with exit code 2 failed to continue when installed via plugins, but worked from
  project settings — [anthropics/claude-code#10412](https://github.com/anthropics/claude-code/issues/10412)
- Hard threshold, any criterion failing fails the unit of work —
  [Anthropic, Harness design](https://www.anthropic.com/engineering/harness-design-long-running-apps); grade outcomes
  rather than prescribed tool-call paths, which make tests brittle —
  [Anthropic, Demystifying evals](https://anthropic.com/engineering/demystifying-evals-for-ai-agents)

### Inferences
- The strongest gate is in the tool's own commands (a command that refuses is a gate regardless of which agent or
  session runs it); hooks are the backstop that catches the turn ending without the command being run.
- A gate must key on freshness, not just on a pass: "the last judge run covers exactly this design" (hash of the
  design file and tool version stored with the verdict), otherwise an old pass lets a new change through.
- Use the Stop hook's `stop_hook_active` and the 8-continuation cap deliberately: block once with a precise reason
  (which finding, where, the close look's path), and on the repeat let the turn end with an explicit "not done:
  blocking findings remain" message to the user, so an unfixable case cannot trap the session (the project's
  `guard.py pushed` already follows this hold-once pattern).
- Rules in prose remain useful for intent, but per the project's own memory ("gates, not rules"), anything that can
  be checked should move into a refusal.

### Gaps
- The hooks page was only partly read (it is 250k characters); exact semantics of `type: "prompt"` hooks on the Stop
  event were not confirmed.
- No OpenAI or Google DeepMind primary guidance on agent verification gates was retrieved in this pass.

## 6. Consolidating overlapping checkers into one judge

### Takeaway
Mature checking systems (linters, static analysers, eval harnesses) converge on one findings schema shared by many
independent checks, each check isolated and responsible for one dimension, with a severity that decides blocking
versus advisory, explicit and recorded suppressions for intentional exceptions, and a single aggregator whose
verdict is the gate.

### Cited Findings
- Isolated graders per dimension, combined in one harness; code-based graders are "Fast, Cheap, Objective,
  Reproducible" but "Brittle to valid variations"; model-based graders are flexible but "Non-deterministic" and need
  calibration — [Anthropic, Demystifying evals](https://anthropic.com/engineering/demystifying-evals-for-ai-agents)
- Per-criterion hard thresholds, any one failing fails the whole —
  [Anthropic, Harness design](https://www.anthropic.com/engineering/harness-design-long-running-apps)
- SARIF 2.1.0 (OASIS standard for static-analysis results): each result has a `ruleId`, a `level` ("none", "note",
  "warning", "error"), locations, and optional `suppressions` with a justification, letting many tools report into
  one format — [OASIS SARIF 2.1.0](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html) (field names
  from the standard; the spec page was not re-read in this pass)
- ESLint configures each rule as "off", "warn" (which "doesn't affect exit code") or "error" (makes ESLint "exit
  with a non-zero exit code", hence usable as a CI or pre-commit gate) —
  [ESLint: configure rules](https://eslint.org/docs/latest/use/configure/rules)
- Eval3D combines several probes into one interpretable, spatially localised report —
  [CVPR 2025](https://cvpr.thecvf.com/virtual/2025/poster/35203)
- LL3M separates the critic (finds issues) from the verification agent (checks each issue closed) —
  [arXiv 2508.08228](https://arxiv.org/html/2508.08228v1)

### Inferences
- The tool's three checkers already share part of a schema (`checks.run` gives {check, kind, text, z, side, step};
  the eye keeps where and which way the body faces). Consolidation is mostly: one schema, one entry point, one
  severity policy, one verdict, and one place that records waivers.
- Keep the checks as separate functions (isolated graders), but stop letting each speak in its own channel; the user
  and Claude should see one ranked list, blocking first.

### Gaps
- No source found on consolidating 3D/visual-specific checkers; the patterns are borrowed from static analysis and
  agent evals.

## Applicability to this tool

### Takeaway
Make one judge, `tool.judge`, that every paint runs; give it a new deterministic **line-integrity** family that
measures each band where it actually lands (the family none of the three checkers has), plus travelling close looks
measured in screen space; make blocking findings stop `done`, `open`, the next pass and the end of a turn; and
make the record test set catch the user's most common complaint (`line`) with repaintable tape flaws and OK'd
negatives. The VLM eye on close-up crops stays advisory until the record shows it earns blocking.

### Design (inferences from the findings above)

**1. One findings schema** (a SARIF-like dict; every checker emits it):
`{id, family, check, kind (record.KINDS), severity: block|warn|note, graphic, where: {z, side, uv, xyz, normal},
measure: {value, limit, unit}, evidence: [close-look crop paths], source: measured|rendered|vlm,
waived_by: null|design-intent-id, design_hash, tool_version}`.
`id` is stable (graphic + check + z bucket) so a waiver or a fix can be tracked across paints.

**2. Families inside the one judge** (each an isolated function, merged by one aggregator):
- *Integrity of each graphic, measured on texels/mesh (new; deterministic; BLOCK).* For every band/tape/outline the
  design draws along a line: arc-length sampling every ~0.25-0.5 cm; width on the visible face; gaps (width < 50%
  target), evenness (CV, worst 2 cm window), steps (lateral offset jump), kinks (turning-angle spike beyond the model
  line's own), face hops (normal jump > ~60 degrees), components across UV seams (must be 1), seam continuity. This
  is IMPROVEMENTS H.3 made concrete; it measures the paint as landed, so it would have caught both diagnosed causes
  (the facing filter's flips: gaps and face hops; the smoothed pick leaving the mesh: steps/kinks).
- *Rendered close looks (deterministic; BLOCK for gaps/steps, WARN otherwise).* H.4's travelling cameras: square to
  the visible face, fixed scale (~20 px per cm), overlapping crops along every drawn line, rendered twice: shaded
  (for eyes) and as a flat ID/mask pass (for measurement). Run the same width/gap/skeleton measures in pixels
  (`medial_axis` distance on the mask). This catches what texel measures cannot (viewer filtering, seams that open
  only when rendered) and is the check "against the viewer" that RULES.md asks for.
- *Placement against the car's lines (today's `eye.py`; deterministic; WARN).* Slivers, closing gaps, near misses,
  shallow crossings: these are composition judgements; keep them advisory unless the record shows a kind has high
  precision, then promote that kind to BLOCK.
- *Reach and cuts (today's `measure.py` and `checks.py`; deterministic).* `short`, `gap`, `cut`, `spill`, `over`,
  `clear`: BLOCK when not waived by design intent (`across=True` becomes an explicit waiver id recorded in the
  findings, visible in the skin's notes, rather than silence).
- *Regression (deterministic; BLOCK).* Pixel-diff each close look against the previous version's (pixelmatch-style,
  threshold ~0.1, anti-aliasing excluded, per-machine baselines since Mac and PC render differently); changed pixels
  outside the footprint of the graphics the change meant to touch fail it. This is the "revert on regression"
  pattern of Thinking in Blender, at no extra rendering cost because the close looks exist anyway.
- *VLM questions on crops (model-based; NOTE/WARN only).* A separate fresh agent (never the one that painted) answers
  fixed yes/no/unknown questions per crop with a position ("Is there any place along this tape where the body shows
  through? where?"), crops labelled "Image 1..n", images before text, on the high-resolution tier. A VLM "yes" with
  a location triggers a targeted measurement there; disagreement is shown. It never clears a measured BLOCK.

**3. Gates (deterministic, in the tool first, hooks as backstop)**
- The judge writes its verdict to the work folder with `design_hash` and `tool_version`. Verdict = BLOCK if any
  unwaived BLOCK finding, or if the latest close looks are older than the design.
- `tool.notes done`, `tool.sets open`, the start of a new pass and `install` refuse on BLOCK or stale verdicts,
  printing the findings and crop paths (IMPROVEMENTS H.5).
- The existing Stop hook (`tool/guard.py`) gains a check: if a skin changed in this turn and its verdict is BLOCK or
  stale, return `{"decision":"block","reason": <top findings>}` once; when `stop_hook_active` is true, end the turn
  but require the reply to say the car is not done (the hold-once pattern `guard.py pushed` already uses; the 8-cap
  is the outer limit).
- Budget per change: up to ~3 judge-fix rounds (in line with 2-5 in the literature), then show the best attempt with
  the open findings named in words, never silently looping.
- Cost (RULES.md "say what a step costs"): the integrity family is texel arithmetic on graphics the paint already
  tracks; close looks add renders per drawn line. Measure both on the self-test car before adoption.

**4. Calibration on the user's recorded complaints**
- Make the record able to score `line` complaints: add the TSC_StealthBomber notes 1-9 (gaps, steps, uneven width)
  as flaws pinned to the commit the user saw, with z and side, so they are repaintable. Target before shipping the
  integrity family: all of them named as BLOCK at the right place.
- Add negatives: every car or region the user OK'd up close becomes a "must stay silent at BLOCK" case; report false
  alarms per car. A blocking check needs zero false blocks on OK'd cars; a warning may have some.
- Report per kind: recall at BLOCK, recall at any severity, false BLOCKs on OK'd cars, and what else was named. Never
  aim at a 100% that stops moving: when the set saturates, the next user complaint the judge missed is added first
  (test before fix), which is also how criteria drift gets absorbed.
- Thresholds (gap fraction, step size, kink angle, face-hop angle) are tuned by sweeping them on the record, not
  chosen by feel; the values chosen live in the code with the record score beside them.
- For the VLM questions: run each on the record's crops k=3 times; keep a question only if its answers are stable
  (pass^k) and it adds recall the measurements lack without false alarms on OK'd cars; read every disagreement with
  the user's verdict (Anthropic's "read the transcripts").
- Do not adopt aesthetic reward models (HPSv3, ImageReward, LAION, Q-Align) for this; they judge generic picture
  taste, not tape craft, and would pull designs toward sameness the project's rules forbid.

### Gaps
- Whether the travelling close looks' render time fits the "minutes from words to car" brief was not measured.
- Whether the viewer's rendering matches the game closely enough for screen-space measures to stand in for the game
  needs the check RULES.md already requires ("check the viewer against the game").
- No external evidence was found on how a single user's tolerance for gaps/steps maps to numeric thresholds; that
  can only come from the record.
