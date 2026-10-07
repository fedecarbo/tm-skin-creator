# Lay every graphic on the car's surface

The tool's overall design is what 2026 practice recommends, and nothing on the market can replace it. Claude writes code against the tool's own paint box; a home-made painter works from a baked map of the car; the tool writes its own game files and shows the result in a three.js Lab. That is the "few high-level tools plus a check the agent can run" shape Anthropic's guidance describes ([Anthropic](https://www.anthropic.com/engineering/writing-tools-for-agents), [Claude Code docs](https://code.claude.com/docs/en/best-practices)). Every external painter examined either can't lay a stroke along a path from a script or adds a second application on two computers. The three pains have specific, fixable causes:

- **Graphics that should follow the car break**, and the user's tapes are the measured case. The tool places what it paints *near* the body rather than *on* it: the nearest point in open space plus a facing test, a smooth curve drawn in space and pushed back onto the body, a flat piece of the texture, or a sticker kept off every fold. The 2024–2026 standard is **one foundation for any graphic**: a repaired surface of the car, with every line, distance, offset and decal position measured along that surface ([geometry-central](https://geometry-central.net/surface/algorithms/signed_heat_method/)). A line on an edge, a line beside a line, bands and stripes, fills bounded by the car's lines, decals on curved panels, lettering along a path: each becomes one case of it. The two libraries that provide it, potpourri3d 1.4.0 and libigl 2.6.3, are **already installed in the tool's Python and unused** ([PyPI](https://pypi.org/project/potpourri3d/)). On this car they ran in hundredths of a second, once 156 broken edges in its mesh were repaired.
- **The checkers missed what the user saw** because none of them measured a graphic where it actually landed. Vision models are documented to be weakest at exactly these few-pixel gaps and steps ([VDiff-Bench](https://huggingface.co/papers/2609.06245)).
- **Paints on the 16 GB Mac are slow** most likely because the machine runs out of memory, not because the maths is slow. So a profile and memory fixes come before GPU work. Separately, one fused GPU program ran the tool's noise about **280 times faster** than numpy.

The recommended order:

1. Put the user's line complaints into the record and profile one paint.
2. Build the foundation: one repaired surface of the car, with its distance and line solvers.
3. Move every graphic onto it: lines and bands first (shown on the StealthBomber's tapes), then fills, decals and lettering.
4. Add one judge that measures every graphic where it lands, close looks along lines and over decals, and gates that refuse "done".
5. Then memory, GPU and better wear.
6. Let the foundation replace the paint box's several hand-written ways of placing things, so the code shrinks.

## Most jobs already match 2026 practice; three have a defect with a known cure

The table compares each job of the tool with how it is done in October 2026. Most rows say "keep". The changes cluster in three places: placing graphics, judging and memory.

| Job | How it is done in October 2026 | This tool today | Verdict |
|---|---|---|---|
| Reading the car | Repair the mesh before any surface maths: weld, drop duplicate faces, make it manifold ([libigl](https://pypi.org/project/libigl/)) | Own FBX reader. The mesh has 156 duplicate triangles, 156 non-manifold edges and 38–39 separate pieces (measured locally) | Keep the reader; add a one-time repaired surface |
| Naming parts | Editors highlight each paintable area ([GT7 guide](https://coachdaveacademy.com/tutorials/how-to-use-the-gt7-livery-editor/)); agent tools take identifiers, not raw coordinates ([Anthropic](https://www.anthropic.com/engineering/writing-tools-for-agents)) | `car/parts.json`, some inner names guessed | Keep; make the names typed identifiers the paint box checks |
| The car's shape, and placing graphics on it | Curves, distances and decal positions kept on the surface (signed heat method, flip geodesics, log maps) ([SIGGRAPH 2024](https://history.siggraph.org/?p=164194)) | Several separate ways: nearest point in space plus a 60° facing filter; smoothing in space, then projecting back; flat texture pieces; stickers kept off every fold | **Replace** with one surface foundation |
| Painting and materials | Layers and masks driven by baked curvature, ambient occlusion, position and normal maps ([Adobe](https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/effects/generators/metal-edge-wear)) | numpy per texel on a cached bake; wear from direction and height rules | Keep the engine; fix memory; add curvature and occlusion maps |
| Judging a painted car | Measurement first, a separate verifier, and a vision model on zoomed crops only as a second opinion ([3DHarnessBench](https://arxiv.org/html/2609.06535)) | Three checkers plus six whole-car views, run by the agent that painted | **Rebuild** as one judge that measures every graphic where it lands, with gates |
| Building the game files | Nadeo's BC1/BC3/BC4/BC5 formats with D3D9 headers ([Nadeo spec](https://devtrackers.gg/trackmania/p/3490d99c-stadium-car-ressources-all-you-need-to-create-skins-for-the-stadium-cars)) | Own encoder with exact headers; gaps between UV islands filled from the nearest texels | Keep; compare once against a reference encoder |
| The Lab and viewer | three.js r186, calibrated against the game's own screenshots ([three.js](https://github.com/mrdoob/three.js/releases)) | Already on r186, physical materials, measured camera FOVs | Keep; calibrate; show the decoded game files |
| Upkeep | Few high-level tools, hooks as gates, tripwires against duplicated code ([GitClear](https://www.gitclear.com/the_ai_code_quality_maintainability_gap)) | 17,452 lines in 56 files; rules being turned into gates | Narrow the paint box; add tripwires |

Two things this table shows are worth saying plainly.

First, the expensive-looking parts of the engine are small. Baking, rasterising and noise together come to about 250 lines (local count). Swapping them for a commercial engine would save almost nothing. The bulk of the code is domain logic no engine provides: tyres (1,236 lines), the paint box (1,139), lines (`course.py` 943, `meshlines.py` 739) and marks (794).

Second, the code that places graphics is exactly where a library can replace hand-written geometry. So the foundation that fixes placement is also the main way to make the code smaller.

## Graphics break because the tool places them near the body, not on it

**The measured case is the tape.** For each texel, the tool asks which point of the line is nearest in a straight line through space. It then keeps the texel only if it faces within 60 degrees of the line's own facing there (`course._zone`, `FACING = 0.5`). On a rolled edge, "the line's facing" has no single answer. Measured on the StealthBomber's skirt, it flipped **20 times over 30 degrees**, so the tape hopped between the side and the underside. Those hops are the gaps.

**Picked lines fail the mirror-image way.** A smooth curve is fitted through the clicks in open space (Catmull-Rom in `meshlines.smooth`), and each point is then pushed onto the nearest bit of body (`meshlines._closest`). Where the model's short lines meet at a fold, "the nearest bit" jumps from one face to another, and the smooth curve turns into a staircase. Those are the StealthBomber's steps. Lines laid beside another line (`Course.offset`) walk sideways through space and project back, with the same risk, and their points crowd and cross on the inside of bends.

**The cause is general, not about tapes.** The paint box places graphics in at least five separate ways (read from the code):

- **Nearest point plus a facing test.** Strips, dashes, blocks and ticks along a line (`Course.strip`, `dashes`, `blocks`, `ticks`) use the same nearest point and 60° test.
- **Flat pieces of the texture.** Inked strips and colour edges moved onto a line (`Course.inked`, `inked_edge`) are drawn one flat piece of the texture at a time.
- **Kept off every fold.** Marks, decals, words, placards and scattered stickers (`Skin.mark`, `decal`, `text`, `placard`, `scatter`) are laid flat within a cone of one facing and kept off every fold. A decal or a word therefore can't sit across a crease or follow a curve even when the design wants it to.
- **Projection.** A projected picture (`marks.project`) lands on the nearest surface facing it.
- **Straight lines through space.** Zones (`shapes`) are measured in straight lines through space. That is right for a stripe seen straight from above, but it can't give a band that follows the body.

Each of these is a different approximation of the same surface, with its own thresholds and its own failure.

**How it is done in October 2026.** The research consensus is to keep every curve made of points that sit on the surface's own triangles, measure every distance along the surface, and never smooth in space and project back.

- Shortest lines come from flipping mesh edges until a path straightens (FlipOut) ([geometry-central](https://geometry-central.net/surface/algorithms/flip_geodesics/)).
- Smooth curves come from subdivision done on the surface. b/Surf found that the direct methods "are fragile and prone to discontinuities", while subdivision "is robust" ([b/Surf](https://ggg.dibris.unige.it/papers/TVCG22_bSurf/TVCG22.html)).
- Distances to a line come from the **Signed Heat Method** (SIGGRAPH 2024). It is robust to "holes, noise, or self-intersections", gives a side even for an open curve, and its implementation "should fill in small gaps" ([SIGGRAPH](https://history.siggraph.org/?p=164194), [geometry-central](https://geometry-central.net/surface/algorithms/signed_heat_method/)).
- Decal positions come from a local surface map around a point. The current best method is the **Affine Heat Method**, the SGP 2025 best paper, already the default in potpourri3d ([Eurographics](https://diglib.eg.org/handle/10.1111/cgf70205), [potpourri3d](https://github.com/nmwsharp/potpourri3d)).

Industry tools agree. Substance Painter's path tools "only work in 3D space on the surface of the geometry", and its November 2025 Ribbon tool lays a texture along such a path "without any cuts" ([Adobe](https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/painting/path-tools/path), [Adobe 11.1](https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/release-notes/version-11-1)). Tools that project flat shapes onto the car show the same breakage this tool has. Ailivery, the nearest AI livery product, lists "A stripe can land crooked where two body pieces meet" as a known limit, and its workaround keeps graphics inside one piece ([Ailivery](https://www.ai-livery.com/)). GT7 gives players angle and depth limits on how far a sticker wraps ([GT7 guide](https://coachdaveacademy.com/tutorials/how-to-use-the-gt7-livery-editor/)). The step at a piece boundary is built into projection; it is not one tool's bug.

**The foundation has six pieces**, built once and shared by every graphic:

1. **A repaired surface of the car.** Welded, duplicates dropped, broken edges split (`igl.split_nonmanifold`), one solver per connected piece, and a map back to the model's own triangles.
2. **Distances measured along the surface** from any line or point (`MeshSignedHeatSolver`, `MeshFastMarchingDistanceSolver`), with a side for open lines.
3. **Lines that lie on the surface.** The model's own edge chains, shortest paths straightened by edge flips (`EdgeFlipGeodesicSolver`), and the straightest continuation of a line (`GeodesicTracer`).
4. **Contours of a distance** (`marching_triangles`). These are lines beside lines, and the edges of fills.
5. **Two kinds of local coordinates on the surface.** A local map around a point, for decals and emblems (`MeshVectorHeatSolver.compute_log_map`, Affine Heat). Along-and-across coordinates for anything laid along a path, such as dashes, ticks and words (distance travelled along a line, signed distance across it).
6. **Per-texel sampling** through the triangle and position-in-triangle the bake already stores (`bake.py` keeps the triangle id; `raster.py` gives the weights). Edges are softened by exactly one texel, using each texel's own size in cm.

**Why it works.** Membership, width and side come from how the surface is connected, never from comparing facings. The far side of a thin panel is close in space but far along the surface, so it is excluded without any 60-degree rule. Widths stay true on a tight roll, where straight-line distance under-measures. Because everything lives on the welded model and every texel reads it the same way, **the two sides of a UV seam read the same value by construction**, so no graphic can break at a seam.

**What each kind of graphic becomes, and which paint-box pieces sit on it:**

| Graphic | On the foundation | Paint-box pieces that sit on it |
|---|---|---|
| A line on an edge, or anywhere | The model's own edge chain whole, or a straightened surface path through points; a rolled edge's line defined once as the middle of the rounded strip | `meshlines.line`, `meshlines.picked`, `meshlines.path`, `Course` |
| A line beside a line | A contour of the distance at the offset; it can't cross itself on a bend | `Course.offset`, `Course.extended` |
| Bands, stripes and tapes along a line | Distance within half the width either side (`\|d\| <= w/2`, wrapping the edge), or from 0 to the width on one side (`0 <= ±d <= w`, one face, H.1's case); to stop at a hard crease, the distance is computed on the mesh cut along it (`igl.cut_mesh`) | `Course.strip`, `tape`, `inked`, `dashes`, `blocks`, `ticks`; `shapes.polyline` |
| Shapes and fills bounded by the car's lines | The region on one side of a line's contour, its edge exactly on the model line | `meshlines.panel`, `Course.inked_edge`; `shapes` zones meant to follow the body (straight-from-above zones stay as they are, a design choice) |
| Decals and emblems on curved panels | A local surface map around the centre, so a decal can cross a crease or a panel gap on purpose, with its stretch measured | `Skin.mark`, `Skin.decal`, `marks.project` |
| Lettering and patterns along a path | Along-and-across coordinates of one chosen line | `Skin.text`, `Skin.placard`, `Skin.emboss`; dashes and ticks |
| Patterns spread over the body | Spacing measured along the surface | `Skin.scatter` |
| Wear and dirt | Curvature and occlusion baked once on the same repaired surface | `Skin.wear`, `Skin.peel`, `Skin.dirt` |

So **one fix serves every graphic**. A line placed on the mesh, a band, a fill edge, a decal and a word all read the same surface, and each piece of the paint box keeps its name while losing its private approximation.

**Measured on this car (2026-10-07, Mac, locally).** The solvers refuse the raw mesh because of its 156 duplicate triangles and 156 edges shared by more than two faces. After dropping the duplicates and splitting those edges (`igl.split_nonmanifold`):

| Step | Time |
|---|---|
| Build a solver | 0.01 s |
| Signed heat distance | 0.07 s |
| Fast-marching distance | 0.007 s |
| An offset line (`marching_triangles`) | 0.007 s |
| A decal's local map | 0.17 s |
| Heat distance on the body subdivided 16 times | 0.69 s |

These costs are negligible next to a paint, so **every skin pays almost nothing** for this, which satisfies the rule against steps every skin pays for.

**How it relates to H.1.** H.1's `Course.tape`, built and awaiting the user's OK, already measures across the surface rather than through space. It does so through a grid of texels on the body texture only. It joins texels across seams by closeness (`TAPE_SEAM = 0.3` cm) and by facing (`TAPE_FOLD`, within 120 degrees). It is a step the right way, but it is one piece's private answer. The foundation does the same job where seams don't exist, so those two thresholds disappear. It is also identical for every texture set, and the same surface serves offsets, fills, decals and the judge. The fair test is the user's eye: paint the foundation's band beside H.1's tape on the same failing roll, with the flip count and width every half centimetre shown beside each.

**Lines placed on the mesh follow the user's own rule**: "one of the model's lines whole, or a line beside one".

- **Snap and take the whole line.** Snap each click to the nearest model line and take the model's own chain of edges between the snapped clicks, with no smoothing at all.
- **Join short pieces.** Chain short feature pieces at each junction by the smallest turn.
- **Straighten zig-zags.** Straighten a zig-zag chain with flip geodesics between pinned corners (`EdgeFlipGeodesicSolver.find_geodesic_path_poly`).
- **Lay a line beside a line.** Take the line of constant distance from it (`marching_triangles(V, F, d, isoval=offset)`).
- **Carry a line on.** Extend it by the straightest path along the surface (`GeodesicTracer.trace_geodesic_from_face`).
- **Rolled edges.** A rolled edge has no single crease, so its line is defined once as the middle of the rounded strip (a level set across it), which leaves no facing to flip.

**What isn't settled yet:**

- **Which side counts as positive.** The signed heat method's sign convention is undocumented, so it has to be fixed once by test.
- **Converters are needed.** The solver wants curves whose every edge crossing is explicit, and the flip solver returns points in space. Each needs a small converter.
- **Separate pieces.** Each solve works on one connected piece, and the car has about 39. Hairline gaps must be welded, or a line split per piece.
- **Large triangles.** The model's triangles are large in places (90th-percentile edge 7.6 cm, longest 24 cm). Curved free lines need the mesh subdivided before solving.
- **Decal size limits.** A decal larger than the region where surface paths stay unique will stretch, so its stretch has to be measured before it is shown.
- **Not yet measured:** whether a crisp one-texel edge comes out at 4096 px without subdivision, and how long any of this takes on Windows.

**Words keep their own rule.** Professional wrap practice still keeps text off compound curves ([3M tips via signs101](https://www.signs101.com/threads/five-tips-for-designing-a-great-vehicle-wrap.89714)), or lays it deliberately along one chosen curve ([Adobe 11.1](https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/release-notes/version-11-1)). For this tool that means a "flat enough for words" check per panel computed from the mesh, or words along one chosen line using its along-and-across coordinates. Words still go on only when the user asks for them.

## The checkers missed the gaps because nothing measured a graphic where it landed

**The record shows the blind spot.** `tool/record.json` holds 45 recorded flaws. Only 5 can be painted again and scored, and the "5 of 5" score comes from those. Twenty-five of the 45 are of kind `line`, the user's most common complaint, and none of the five scorable ones is a line or a gap. The StealthBomber tape notes are not in the set. Anthropic's eval guidance is blunt about this: start with "20–50 simple tasks drawn from real failures", and "an eval at 100% tracks regressions but provides no signal for improvement" ([Anthropic](https://anthropic.com/engineering/demystifying-evals-for-ai-agents)).

**Vision models are weak at exactly these defects.**

- In BlenderGym, vision verifiers agreed with humans 66% of the time on pairs of renders, against 79% between humans ([BlenderGym](https://arxiv.org/html/2504.01786v1)).
- On 3D-DefectBench (October 2026), the best model scored 0.298 against 0.519 for humans on geometry defects ([3D-DefectBench](https://www.alphaxiv.org/abs/2607.10826)).
- The newest fine-difference benchmark still finds "persistent failures on subtle low-level changes" ([VDiff-Bench](https://huggingface.co/papers/2609.06245)).
- Model accuracy depends causally on how large the thing in question is in the frame, and cropping in fixes much of it ([ICLR 2025](https://arxiv.org/abs/2502.17422)).

Claude sees images in 28-pixel patches, up to 2,576 px on the long edge ([Claude docs](https://platform.claude.com/docs/en/build-with-claude/vision)). Assuming a car about 4 m long fills that frame, a 1 cm gap is about 6 pixels, a fifth of one patch. A whole-car view was the wrong instrument. The research also finds that six oblique views match 14 for whole-object review ([3D-DefectBench](https://www.alphaxiv.org/abs/2607.10826)), so the snapshot count is fine; their scale is the problem.

**Self-judging is a documented weak point too.** Models "struggle to self-correct their reasoning without external feedback" ([ICLR 2024](https://arxiv.org/html/2310.01798v2)), and agents grading their own work "tend to respond by confidently praising the work" ([Anthropic](https://www.anthropic.com/engineering/harness-design-long-running-apps)). The strongest 2026 result points the other way from more looking: giving Claude Opus 5 explicit measurements beside the images cut geometric error by **44%** ([3DHarnessBench](https://arxiv.org/html/2609.06535)).

**The fix is one judge that measures every graphic where it landed.** All checkers report into one findings list with one severity scale: block, warn or note. That is the pattern static analysers converged on (SARIF's `level` and `suppressions`; [OASIS SARIF](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html)). The judge has these parts:

- **A placement check (new; blocks), for every graphic the design places:**
  - **Lines, bands and stripes.** A station every 0.25–0.5 cm along the line, measuring:
    - painted width on the face the user sees;
    - gaps (width under half the target);
    - evenness (starting tolerance ±5%);
    - steps (the centre jumping sideways by more than about a quarter of the width in one station);
    - kinks (turning sharper than the model line's own turning);
    - face hops (the surface under the centre turning more than about 60°);
    - pieces (a graphic meant to be one piece must be one, counted across UV seams).
  - **Fills bounded by the car's lines.** How far the painted edge sits from the line it should follow, and its spread.
  - **Decals, emblems and words.** Wholeness: the share of the intended footprint actually painted, one piece across seams, and not cut by a crease or an edge unless the design says so. Stretch: how much the local surface map distorts it.

  The foundation from the previous section supplies "along", "across" and the local maps for free. **The same surface that places a graphic measures it.**
- **Close looks along every line and over every decal (H.4).** Square to the visible face, at about 20 px per cm, rendered twice: shaded for the eye, and as a flat mask that the same width and gap measures run on. That catches what texel arithmetic can't, such as texture filtering in the viewer. A pixel comparison against the previous version's close looks (pixelmatch-style, threshold ~0.1) also flags changes outside the area the edit meant to touch ([pixelmatch](https://github.com/mapbox/pixelmatch)).
- **The current checkers.** The reach measurer and flaw checks (`measure.py`, `checks.py`) keep their kinds. A deliberate crossing becomes a recorded waiver instead of silence. The placement eye (`eye.py`) stays advisory until the record shows a kind is precise.
- **A vision model on crops (advisory only).** A fresh agent that never painted the car answers narrow yes/no/unknown questions with a position ("is there anywhere along this line where the body shows through?"). A "yes" triggers a measurement at that spot. It never clears a measured block.

**Gates make the judge bite.** The judge writes its verdict with a hash of the design, so an old pass can't cover a new change. `tool.notes done`, `tool.sets open`, the start of a pass and `install` refuse on a block or a stale verdict (H.5). The existing Stop hook (`tool/guard.py`) holds a turn once with the top findings, and uses `stop_hook_active` to let the turn end honestly on the repeat. Claude Code caps such holds at 8 in a row ([hooks reference](https://code.claude.com/docs/en/hooks)).

Each change gets a budget of about three judge-and-fix rounds. Then the best attempt is shown with the open findings named in plain words. That matches the 2–5 round budgets of current render-and-refine systems, which also "revert unsuccessful edits when visual feedback indicates a regression" ([Thinking in Blender](https://arxiv.org/html/2606.02580)).

**Calibrate on the record before trusting any threshold.**

- **Positives:** add the StealthBomber notes 1–9 as repaintable flaws, pinned to the commit the user saw.
- **Negatives:** add every region the user OK'd up close, where a blocking check must stay silent.
- **Tuning:** set the gap, step, kink, hop and stretch limits by sweeping them on this set, not by feel.
- **Don't adopt aesthetic reward models.** HPSv3, ImageReward and the LAION predictor score whole pictures against generic taste. They barely move for a 1 cm gap and would pull designs toward sameness ([HPSv3](https://arxiv.org/html/2508.03789v2)).

**Not yet measured:** how long the placement check and the travelling close looks add to a paint. Both must be timed on the self-test car before they become part of every show.

## Paints are slow from memory pressure, and fusion beats raw GPU speed

**Where the memory goes.** At 4096², one float channel is 64 MiB. One cached bake set loads about **496 MiB** into RAM (triangle id, position, normal, counts), because the caches are saved as compressed `.npz`, which numpy can't memory-map ([numpy docs](https://numpy.org/doc/stable/reference/generated/numpy.load.html)). Only 60.5% of the body canvas and 70.9% of the details canvas is actually covered (measured locally). Yet the painter computes on whole canvases, and several modules still compute in double precision. The Mac (Apple M5, 16 GB) had 0.5 GB free and 2.1 GB of swap in use when measured. The likely explanation for 20 seconds on one paint and 17 minutes on another is therefore swapping, not arithmetic. No whole-car profile exists yet, and the project's own rule is to measure slowness before fixing it.

**What the GPU measurements show** (one run each, locally on the M5, the tool's own fbm noise at 4096²):

| Method | Time | Peak memory |
|---|---|---|
| numpy | 2.4–2.5 s | — |
| MLX compiled | 316 ms | 5.8 GB |
| PyTorch on the Mac GPU | 1.52 s | — |
| **One hand-fused Metal kernel** (`mx.fast.metal_kernel`) | **8.9 ms** | **336 MB** |

The win comes from fusing the many small steps into one program, which avoids writing and re-reading dozens of temporary arrays. MLX exposes this as hand-written Metal kernels on its arrays ([MLX docs](https://ml-explore.github.io/mlx/build/html/dev/custom_metal_kernels.html)). Merely running the same steps on the GPU gave only about 1.5 times. A blur on a 2048² colour image took 287 ms in scipy and 9 ms on PyTorch's Mac GPU backend (also measured locally).

**Which GPU libraries fit both computers** (October 2026, all with Python 3.14 wheels):

- **Usable:**
  - MLX 0.32 (Metal; Mac only in practice).
  - PyTorch 2.14 (Mac GPU and CUDA; already on the PC).
  - wgpu-py 0.32 (one shader for Metal, DX12 and Vulkan; a plain pip wheel).
  - SlangPy 0.43 (Metal and CUDA, but it needs Xcode 16 or later on the Mac) ([PyPI mlx](https://pypi.org/project/mlx/), [PyPI wgpu](https://pypi.org/project/wgpu/), [SlangPy](https://slangpy.shader-slang.org/en/latest/)).
- **Ruled out:**
  - NVIDIA Warp: no Metal ([PyPI](https://pypi.org/project/warp-lang/)).
  - JAX: no Mac GPU ([JAX](https://docs.jax.dev/en/latest/installation.html)).
  - Taichi: no Python 3.14 wheels ([PyPI](https://pypi.org/project/taichi/)).
  - nvdiffrast: CUDA only, and licensed for "research or evaluation purposes only" ([licence](https://github.com/NVlabs/nvdiffrast/blob/main/LICENSE.txt)).

**The recommended order is memory first.**

1. Save bake and coverage caches as plain `.npy` files and load them memory-mapped.
2. Work on the packed list of covered texels, in chunks of 1–2 million.
3. Keep float32 for maths and float16 or uint8 for stored layers.
4. Free each part's arrays once it is composited.
5. Add "repaint only the map that changed", already queued in IMPROVEMENTS, since every `show` repaints the whole car even when a note touched only the tyres.

Then GPU, only for what the profile shows dominates. Use MLX's fused kernels on the Mac first, since that is measured and pip-only. If the PC also proves slow, move the kernels to wgpu-py rather than SlangPy, which would need Xcode on the Mac. Use PyTorch for blurs and other dense filters on both machines. Keep numpy as the reference everywhere.

**Better wear comes from the same once-per-car maps.** Professionals drive edge wear from baked **curvature** (convex edges chip), **ambient occlusion** (crevices collect dirt and are spared wear), position and world-space normal ([Adobe](https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/effects/generators/metal-edge-wear)). The tool's wear uses facing, height and sun direction. libigl already provides `principal_curvature`, `ambient_occlusion` and `signed_distance`, so these maps can be baked once per mesh on the foundation's repaired surface, cached like the bake, and cost nothing per skin.

Three smaller quality gains:

- **Cleaner part edges.** Anti-aliased part edges from a distance-to-edge field, the standard since Valve's 2007 method ([Valve](https://steamcdn-a.akamaihd.net/apps/valve/2007/SIGGRAPH2007_AlphaTestedMagnification.pdf)).
- **A second photo-texture source.** Poly Haven, also CC0 ([Poly Haven](https://polyhaven.com/license)).
- **Less visible repetition.** Hex tiling (Mikkelsen 2022) hides repetition in photo textures ([JCGT](https://jcgt.org/published/0011/03/05/)).

The body texture has no normal map in Nadeo's format, so any raised detail on the body can only be painted. Real relief belongs on the Details set ([Nadeo spec](https://devtrackers.gg/trackmania/p/3490d99c-stadium-car-ressources-all-you-need-to-create-skins-for-the-stadium-cars)).

## The game files and the Lab need yardsticks, not new engines

**The game-file encoder should stay.** No established encoder fits two computers with Python access:

| Encoder | Problem |
|---|---|
| Pillow | Can't save BC4, which the tool needs for the coat and dirt maps ([Pillow](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html)); the tool's own test found it 5 dB worse |
| Microsoft's texconv | Windows only ([DirectXTex](https://github.com/microsoft/DirectXTex)) |
| NVIDIA Texture Tools 3 | Windows and Linux only ([NVIDIA](https://developer.nvidia.com/gpu-accelerated-texture-compression)) |
| AMD Compressonator | No release since January 2024 ([GitHub](https://github.com/GPUOpen-Tools/compressonator)) |
| Intel's ISPC compressor | Archived ([GitHub](https://github.com/GameTechDev/ISPCTextureCompressor)) |

The tool's encoder is the same family of algorithm as the best open one, rgbcx. The last independent benchmark found "very little quality variance" among good BC1/BC3 encoders ([Aras](https://aras-p.info/blog/2020/12/08/Texture-Compression-in-2020/)).

**Worth an hour, once:**

- Encode the self-test car with `quicktex` (rgbcx, on the Mac) and texconv (`-dx9`, on the PC), and compare quality per map and at sticker edges ([quicktex](https://pypi.org/project/quicktex/)).
- Keep `texture2ddecoder` as an independent check that the tool's files decode as intended ([PyPI](https://pypi.org/project/texture2ddecoder/)).

**Settled questions:**

- **No BC7.** BC7 can't be written with the D3D9 headers Nadeo requires ([texconv](https://github.com/microsoft/DirectXTex/wiki/texconv)).
- **Island padding already meets the standard.** The tool fills the gaps between UV islands from the nearest texels (`raster.fill_holes`), which is the "infinite dilation" professionals use for clean mipmaps ([Adobe](https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/technical-support/workflow-issues/export-issues/texture-dilation-or-padding)).
- **Optional crisper distance.** The one optional change is a sharper mip filter than the current 2×2 box. It only matters at a distance in the game, and it changes every car's files.

**The viewer needs calibration, not a new engine.** three.js r186 (September 2026) is current, and the Lab already uses it with physical materials, clearcoat, HDR environments and switchable tone mapping ([three.js](https://github.com/mrdoob/three.js/releases)). Nadeo hasn't published the game's tone curve, sky or car shader, so the remaining mismatch can only be fitted against the user's own F12 screenshots.

- **Compare pictures properly.** NVIDIA's FLIP (`flip-evaluator`, BSD, Mac and Windows wheels) scores a matched viewer render against a screenshot, and its heat map is itself a picture the user can judge ([FLIP](https://github.com/NVlabs/flip)).
- **Fit only a few global settings.** Exposure, environment strength, tone mapper and clearcoat strength per mood. More than that would overfit one screenshot. Khronos PBR Neutral is the tone mapper that reproduces base colours exactly in the mid range ([Khronos](https://github.com/KhronosGroup/ToneMapping/blob/main/PBR_Neutral/README.md)).
- **Avoid pyiqa.** Its licence is non-commercial ([PyPI](https://pypi.org/project/pyiqa/)).
- **Show the decoded game files.** three.js can't load BC4/BC5 DDS files ([DDSLoader](https://github.com/mrdoob/three.js/blob/dev/examples/jsm/loaders/DDSLoader.js)). The judge's close looks should use the tool's own decoding of the built files (the viewer can already show a built skin), so compression artefacts are judged as the game will show them.

**The Lab already does what 2026 design products sell.** It has point-and-edit notes on the car (Figma Make's "Ask for changes" on a selected element) and side-by-side options ([Banani](https://www.banani.co/blog/figma-ai-features-review)). Three additions are worth making:

- **Guaranteed local edits.** A gate diffs the new textures against the old and flags changes outside the area pointed at.
- **Visible lineage of takes**, so "back to the earlier one" is one click.
- **One change per iteration.** Ailivery found that bundled refinement requests are "often" only partly applied ([Ailivery](https://www.ai-livery.com/)). That matches H.6's "one change, its close looks, then the reply". Trading Paints insists previews be real in-sim captures because AI renders "distort" cars ([Trading Paints](https://help.tradingpaints.com/showroom/is-ai-generated-content-allowed/)), which supports the rule of checking the viewer against the game.

## A narrower paint box and tripwires stop the code from growing

**"Random mistakes" have two separate sources**, and neither is cured by more instructions.

- **Too many valid-looking ways to express one intent.** Anthropic's tool guidance is to consolidate into fewer, higher-level, hard-to-misuse tools. One example: changing a tool to require absolute paths made the model use it "flawlessly" ([Anthropic](https://www.anthropic.com/engineering/building-effective-agents), [Anthropic](https://www.anthropic.com/engineering/writing-tools-for-agents)). For the paint box that means:
  - **One verb per intent.** "Along model line X", "beside line X at d cm", "bounded by lines X and Y", "a decal centred here on the surface", with face choice, crossings and continuity handled by the foundation, so a stitched line or a hand-placed decal can't even be written.
  - **Identifiers instead of coordinates.** Part names and line ids as typed values that fail with a "did you mean" list.
  - **A type check on every design script** from a PostToolUse hook, timed first against the every-skin rule.
  - **A short receipt from every verb.** What it painted, what it refused and any accident found.
  - **Merged overlapping verbs** (`text`, `placard`, `emboss` and `decal` are candidates).

  The paint box's basic shape, Claude writing code against a domain API instead of chaining tool calls, is already what Anthropic recommends: in its example that cut context from 150,000 to 2,000 tokens ([Anthropic](https://www.anthropic.com/engineering/code-execution-with-mcp)).
- **Accidents the model can't see.** These are caught only by checks that compute them, which is the judge above.

**Code growth is a measured industry trend, so it needs tripwires, not good intentions.** GitClear's analysis of 623 million changes found duplicated blocks up 81% since 2023, and refactored code down from 13% to 3.8% of changed lines. AI-assisted code is about five times more likely to duplicate than to refactor ([GitClear](https://www.gitclear.com/the_ai_code_quality_maintainability_gap)). For this repo the risk sits in the overlapping line, shape and mark helpers (`course`, `meshlines`, `marks`, `shapes`: about 3,000 lines). These hold the five separate placement methods the foundation replaces with library calls (walking, smoothing, offsetting, facing cones, flat-piece drawing). Add to the self-test:

- a duplicate-block detector;
- a search for error-hiding patterns (`except Exception: pass`);
- a line-count budget a commit may exceed only by saying why.

Pure refactors keep every car's files byte-identical, which the self-test already proves.

**Sessions and models.**

- **Start fresh after repeated failures.** The Claude Code docs' rule applies: after two failed corrections on the same issue, the context is cluttered with failed approaches, so start fresh ([Claude Code docs](https://code.claude.com/docs/en/best-practices)).
- **Use a separate reviewer.** A visual review should come from a fresh agent that never saw the designer's reasoning.
- **Choose the reviewer by quality, not price.** Six full-size images cost about $0.11 on Opus 5.5 ($4/$20 per million tokens) or $0.29 on Fable 5.1 ($10/$50) ([BenchLM](https://benchlm.ai/anthropic/api-pricing)), negligible given that cost is "no object". Cheaper models suit only mechanical summaries.

**The design process already matches professional practice.** Professionals start from what the client does *not* want, set a design language, narrow rough whole-car directions in rounds (Mercedes F1: about 60, then 30, 10 and 1), and leave details and logos to last ([Jalopnik](https://www.jalopnik.com/how-a-race-car-gets-its-paint-job-1752512826/), [Mercedes-AMG F1](https://www.mercedesamgf1.com/news/insight-how-to-design-an-f1-car-livery)). Alpine designed for how the car rotates past the camera ([Motor Sport](https://www.motorsportmagazine.com/articles/single-seaters/f1/how-alpine-designed-its-striking-new-f1-livery/)). The tool's language page and passes (IMPROVEMENTS F) already follow this. The one addition the research supports is the chase camera as a named Lab view to compose for.

**AI pictures stay inside shapes the design places (secondary).** Whole-car AI texturing doesn't fit, for four reasons:

- **Hardware.** Hunyuan3D-2.1's painter needs 21 GB of video memory and TRELLIS.2 needs 24 GB on Linux, both above the PC's 16 GB card ([Hunyuan](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1), [TRELLIS.2](https://github.com/microsoft/TRELLIS.2)).
- **Licences.** Hunyuan's licence excludes the EU and UK ([licence](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1/blob/main/LICENSE)).
- **Subscriptions.** Cloud retexturing (Meshy, Tripo) is subscription-based ([Meshy](https://docs.meshy.ai/en/api/pricing)).
- **Quality and repeatability.** All of them bake in lighting, blur edges and can't re-run identically, which breaks the self-test.

What to do instead:

- **Keep the local picture maker** (FLUX.2 [klein] 4B, Apache 2.0) for illustrations and prints inside zones the design chose ([Hugging Face](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B)).
- **Port it to the Mac through mflux.** That measured about 32 s per 1024² image on an M1 Max, and about 9 s at 512² with a 4-bit version ([benchmark](https://lilting.ch/en/articles/flux2-klein-4b-mflux-iris-m1-max), [4-bit](https://huggingface.co/ar9av/FLUX.2-klein-4B-mflux-4bit)).
- **Keep words in real fonts and Claude-written vector shapes.** Opus 5.5 ranks second on blind preference for SVG ([Design Arena](https://modelgrep.com/best/svg)), and every image model fails past about 25–30 words of text ([invideo](https://invideo.io/blog/best-ai-model-text-in-images/)).

## Every external application was looked at and ruled out

The user excluded external applications. The research reached the same verdict on the merits. The operation the user needs, any graphic laid along a line or placed on a curved panel from code, is either interactive-only or undocumented in every candidate.

| Application | What it could do | Why ruled out |
|---|---|---|
| Substance 3D Painter ($199.99 on Steam, or subscription) | Smart materials, wear generators, baking, export from Python | "Strokes are not accessible from the Python API"; Path and Ribbon need clicks; the app must be open ([Adobe](https://experienceleague.adobe.com/en/docs/substance-3d-dev/painter-python/api/substancepainter-package/layerstack-module/layers-and-effects/paint), [Adobe](https://experienceleague.adobe.com/en/docs/substance-3d-dev/painter-python/tutorials/remote-control)); the command-line toolkit is Enterprise-only ([Adobe community](https://community.adobe.com/questions-46/sbsbaker-exe-missing-from-substance-designer-11-2-2-631171)) |
| Marmoset Toolbag 5 ($399) | Decal projectors, wear layers, baking from a launch script | No call to paint a stroke; `importStroke` format undocumented ([Marmoset](https://marmoset.co/python/reference5.html)) |
| ArmorPaint ($19) | Headless command line, path layers | Path points placed by clicking; script API unverified ([manual](https://armorpaint.org/manual)) |
| 3DCoat (€379) | Painting, node texturing | No scripted painting, baking or export documented ([Pilgway](https://pilgway.com/files/3dcoat/PythonAPI/index.html)) |
| InstaMAT (free under $100k) | Node-graph materials, command line | A material engine, not a path painter; a second runtime ([InstaMAT](https://www.instamaterial.com/)) |
| Houdini Indie | Fully scriptable curves and baking | Subscription; duplicates free geodesic libraries ([SideFX](https://www.sidefx.com/buy/)) |
| Blender and its AI connectors | Headless baking and renders | `bpy` is pinned to Python 3.13 against the tool's 3.14 ([PyPI](https://pypi.org/project/bpy/)); a large second runtime; AI control of Blender is weak at precise placement ("LLMs are language models, not spatial reasoning engines") and runs unsandboxed code ([review](https://chatforest.com/reviews/blender-mcp-server/)) |
| DECALmachine (~$49.99) | Decals shrink-wrapped onto curves | Interactive Blender add-on ([Superhive](https://superhivemarket.com/products/decalmachine)) |
| Rhino 8 ($995) | Curves on surfaces | CAD with no texture painting ([renderahouse](https://www.renderahouse.com/blog/rhino-pricing)) |

Every useful idea these tools contain can be done in-process with the foundation's libraries. That includes surface paths (potpourri3d), curvature and occlusion bakes (libigl), and decals on curved panels (local surface maps). Each would also have added a second source of truth on two computers.

## The order of work

The steps follow the project's own road (IMPROVEMENTS H first) and its rules: measure before fixing, one step shown before the next, every game-file change declared. Effort is a rough estimate of Claude's working time. "Changes cars" means the self-test will show those cars' game files changing, and the commit must name them and say why.

| # | Step | Effort | What it fixes | Self-test effect | Cost every skin pays |
|---|---|---|---|---|---|
| 1 | Add StealthBomber notes 1–9 to the record as repaintable `line` flaws, plus OK'd regions as must-stay-silent cases; profile one whole-car paint on the Mac (and PC) | ~1 day | Gives the placement and speed work measured targets | No game files change; the record score drops below 5 of 5 by design | None |
| 2 | The foundation: one repaired surface of the car (weld, drop duplicate faces, `igl.split_nonmanifold`, map back to the model's triangles), its distance and line solvers cached per piece, per-texel sampling through the bake | ~1 day | Prerequisite for every graphic below | Identical | About 0.05 s, once per car |
| 3 | Bands along a line from the distance along the surface (wrap, one face, stop at a crease): the foundation's first use, shown on the StealthBomber's tapes beside H.1's, with flip counts and widths | 1–2 days | The gaps; breaks at UV seams | Changes cars with tapes, strips or bands | Milliseconds per graphic |
| 4 | Lines anywhere on the mesh: snap to model lines, take chains whole, straighten with flip geodesics, offsets as contours; then move strips, dashes, ticks, inked edges and fills bounded by model lines off their private methods onto the foundation | 2–3 days | The steps; offsets crossing on bends; fill edges off their line (H.2) | Changes cars with picked lines, offsets, strips or line-bounded fills | Milliseconds per line |
| 5 | Decals, emblems and words on the foundation: local surface maps for marks and decals (allowed across a crease when the design says so), along-and-across coordinates for words and patterns along a path, a "flat enough for words" check | 2–3 days | Decals and words that can't cross a fold or follow a curve; unmeasured stretch | Changes cars with marks, decals, text or scatter | Under 0.2 s per decal |
| 6 | One judge: the placement check for every graphic (lines, fills, decals, words) plus the three checkers in one findings list, blocking first | 2–3 days | Checkers blind to how graphics land (H.3) | No game files change; record should name every line flaw | Seconds; time it first |
| 7 | Close looks travelling along every line and over every decal, a measured mask pass, a pixel diff against the previous version | ~2 days | Defects only rendering shows; unintended edits (H.4) | Snapshot sheets only | Renders per graphic; time it first |
| 8 | Gates in `done`, `open`, the next pass and `install`, plus the Stop hook holding once | ~1 day | "Randomly makes mistakes" reaching the user (H.5) | None | None |
| 9 | Memory: `.npy` memory-mapped caches (with a cache version bump), covered texels in chunks, float32/16, repaint only the changed map | 1–2 days | 17-minute swapping paints | Designed identical; any texel that moves is declared | Saves time |
| 10 | GPU: fused noise kernels (MLX on the Mac), PyTorch filters, only where step 1's profile points | 1–2 days | The remaining paint time | One declared re-baseline of all cars (~1e-6 drift) | Saves time |
| 11 | Curvature, occlusion and thickness maps on the repaired surface; wear and dirt driven by them; anti-aliased part edges | 2–3 days | Wear that lands where real cars wear | Changes cars with wear | None (baked once per car) |
| 12 | Paint-box grain (line ids, typed names, receipts, merged verbs) and retiring the private placement methods the foundation replaced; duplicate, error-hiding and size tripwires | About a day per merge | Code growth; ambiguous ways to say one thing | Identical for refactors | Seconds for the type check |
| 13 | Yardsticks: one-off encoder comparison; viewer calibration with FLIP when the user shares F12 screenshots | Hours; ~1 day | Confidence in the game files; the viewer matching the game | Snapshot sheets only, unless an encoder wins | None |
| 14 | Secondary: picture maker on the Mac via mflux; `vtracer` for clean decal edges | 0.5–1 day | "What the Mac lacks" | None for existing cars | Only when a design asks for art |

Steps 2 to 8 build the foundation, move every kind of graphic onto it and put the judge and gates on top. They come to roughly two and a half weeks of working time. Each step is shown before the next starts: lines and bands on the StealthBomber's tapes, decals and words on a car that uses them. Steps 9 and 10 can move earlier if the profile shows paint time hurting more than placement, but not before step 1.

## Conclusion

The common thread under all three pains is approximation where an exact answer is cheap. The tool approximates the car in several private ways (nearest point in space, a cone of facings, a curve drawn in the air and pushed back, a flat texture piece, a sticker kept off every fold). It approximates its judgement (a whole-car photo for a centimetre defect, the painter grading itself). It approximates its memory (whole canvases held at once on a 16 GB machine). In each case, the exact version is now a library call or a measurement costing milliseconds to seconds. The most valuable consequence is that **one surface foundation both places any graphic and measures it**. A line on an edge, a band, a fill, a decal and a word stop being separate problems with separate failures. The fix for the gaps and the fix for the blind checker are the same piece of work, which is also why this is the right place to start shrinking the code.

The research also reframes "it cannot randomly make mistakes". A model working through a broad interface fails at some rate that instructions don't move. The rate falls when the interface allows only one way to say each thing, when every accident the tool can compute is computed, and when "done" is a verdict the tool issues rather than one the agent claims. That is the user's own "gates, not rules", now backed by Anthropic's agent guidance and by every 2025–2026 render-and-refine study. One condition goes with it: a gate is only as good as the record it was tuned on, so the record must grow with every complaint the judge misses.
