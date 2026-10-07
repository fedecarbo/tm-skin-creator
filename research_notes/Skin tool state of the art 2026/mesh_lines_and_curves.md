# Mesh feature lines, curves on surfaces, and tapes painted into a texture (state of the art, October 2026)

Scope: how to read a game mesh's own lines, lay clean curves/offsets/tapes on the surface, and paint them per texel;
which libraries do it today on Python 3.14 (Mac Apple Silicon + Windows); what fixes the tool's three measured
failures. Sources are web pages fetched on 2026-10-07, PyPI metadata queried the same day, plus three measurements
taken on the tool's own car mesh with the libraries already installed in the tool's venv (marked "measured locally";
scripts in the session scratchpad, not in the repo).

Context read from the repo (so the recommendations land on the real code):
- The tape today: `tool/course.py` `_zone()` finds each texel's nearest course point with a `cKDTree` (Euclidean),
  measures "across" as the 3D distance, takes the side from `N x T` at that nearest point, and keeps a texel only if
  `dot(texel normal, course facing N[i]) >= FACING` with `FACING = 0.5` ("within 60 degrees", `course.py` line 67).
  `N` comes from the car map's smoothed facing averaged over `SMOOTH = 2.5` cm.
- Picked lines: `tool/meshlines.py` `smooth()` fits a centripetal Catmull-Rom curve **in 3D** through the clicked
  path, then puts each point back on the body with `_closest()` (closest point on the mesh).
- Offsets: `Course.offset()` walks points sideways in 3D a step at a time, re-projects, least-squares fits, and
  projects again.
- The bake (`tool/bake.py`) already stores, per texel, the FBX **triangle id**; `tool/raster.py` computes the
  **barycentric weights** per texel (not cached, recomputable). So any per-vertex field on the mesh can be
  interpolated exactly onto texels.
- `potpourri3d 1.4.0` and `libigl 2.6.3` are **already installed** in the tool's venv (Python 3.14.7, numpy 2.5.3,
  scipy 1.18.1) but no file in `tool/` imports either today.

---

## 1. Feature line extraction on meshes (2025–2026), robustness on game meshes with rolled edges, and libraries on Python 3.14

### Takeaway
For a fixed low/mid-poly game mesh, the robust lines are still the **artist-authored** ones: dihedral-angle creases,
hard edges (split normals), UV cuts and panel gaps, chained along mesh edges. Curvature ridges/valleys are a weak,
noisy fallback on coarse meshes, and view-dependent lines (suggestive contours, apparent ridges) do not belong in a
texture at all. A **rolled (bevelled) edge** has no single crease edge, so it must be treated as a *strip* (fillet)
and its line defined as a smooth level set across the strip (its crown or a bisector of its two boundary lines),
not picked from one of its many parallel edge loops. Every library needed is current and has Python 3.14 wheels
except CGAL's Python bindings, pygeodesic and Blender's `bpy`.

### Cited Findings
**Line types (the canonical survey and the classic definitions)**
- Bénard & Hertzmann's tutorial "Line Drawings from 3D Models" covers occluding contours, suggestive contours,
  ridges/valleys and apparent ridges: suggestive contours are "surface points that are occluding contours in nearby
  views"; ridges and valleys are "local extrema of surface curvature along one of the principal curvature
  directions" and "might be considered a generalization of sharp creases to smooth surfaces"; apparent ridges are
  "extrema of a view-dependent curvature that takes foreshortening into account" — [Bénard & Hertzmann, arXiv 1810.01175](https://arxiv.org/pdf/1810.01175)
- Apparent ridges (Judd, Durand, Adelson) are defined from a view-dependent curvature — [Apparent Ridges for Line Drawing](https://people.csail.mit.edu/tjudd/apparentLines.pdf)
- Learned line drawing ("Neural Contours: Learning to Draw Lines from 3D Shapes", 2020) learns view-based drawings
  from rendered images — [arXiv 2003.10333](https://arxiv.org/pdf/2003.10333)
- CAD-style robust crest-line extraction on triangle meshes integrates learning into a global minimization to
  detect crest lines on 2-manifold CAD meshes — [Robust feature line extraction on CAD triangular meshes (HAL)](https://hal.archives-ouvertes.fr/hal-01158033)
- Feature detection commonly combines dihedral angle, angle defect and normal-voting tensor; one approach extends
  seed edges greedily into feature paths — [Bachelor thesis, Univ. Bern CGG (feature detection survey/implementation)](https://cgg.unibe.ch/media/resource_files/bachelor_thesis_lukas_seeholzer.pdf) (summary via search snippet; PDF not read in full)
- Fillets (rolled edges) as a recognised problem: a 2024 patent application detects whether a mesh region is a
  fillet by tracing curves along maximal-curvature directions, fitting each with circles and deciding from the
  statistics — [EP 4345673 A1](https://data.epo.org/gpi/EP4345673A1)
- "Smooth Feature Lines on Surface Meshes" (Eurographics DL) addresses feature lines that are jagged when taken
  along mesh edges — [Eurographics DL](https://diglib.eg.org/items/860abe10-40fd-4436-bae1-7db8f05df494/full)
  (page returned 403; title verified from the listing only; attribution to Hildebrandt, Polthier & Wardetzky, SGP
  2005, is from prior knowledge, not re-verified)

**What the car mesh actually is (measured locally, Skin set, 2026-10-07)**
- 17,710 FBX vertices / 27,184 triangles; welded by position (0.01 cm) to 14,678 vertices; **156 exact duplicate
  triangles**, **156 non-manifold edges** (edge shared by >2 faces), 2,254 boundary edges, 38–39 separate connected
  pieces; edge length median 2.17 cm, 90th percentile 7.6 cm, max 24.3 cm. (measured locally with the tool's
  `fbx.meshes()` and numpy)
- After dropping duplicate faces and `igl.split_nonmanifold(F)`, the surface is manifold: 14,681 vertices, 27,028
  faces, 39 pieces; geometry-central's manifold solvers then build (see §2). (measured locally)

**Libraries (versions and Python 3.14 wheels from PyPI JSON, 2026-10-07)**
- **potpourri3d 1.4.0**, released 2026-03-25, MIT, wheels cp39–**cp314** for macOS/Windows/Linux — [PyPI](https://pypi.org/project/potpourri3d/); release note: "Rebuild with latest dependencies. Publish wheels for py3.9 - py3.14." — [GitHub releases](https://github.com/nmwsharp/potpourri3d/releases)
- **libigl (Python) 2.6.3**, released 2026-09-01, ships `cp312-abi3` wheels for macOS arm64 and Windows (stable ABI,
  so they load on 3.14) — [PyPI](https://pypi.org/project/libigl/); verified: imports on the tool's Python 3.14.7 and
  exposes `sharp_edges`, `dihedral_angles`, `principal_curvature`, `exact_geodesic`, `heat_geodesics_precompute/solve`,
  `cut_mesh`, `split_nonmanifold`, `upsample`, `unique_edge_map`, `signed_distance` (measured locally via `dir(igl)`).
  PyPI's licence field is empty; libigl is MPL-2.0 per its project (prior knowledge, not re-verified).
- **trimesh 5.1.1**, released 2026-10-02, MIT, pure-Python `py3` wheel — [PyPI](https://pypi.org/project/trimesh/)
- **PyMeshLab 2025.7.post1**, uploaded 2026-01-30, **GPL-3**, cp310–cp314 wheels — [PyPI](https://pypi.org/project/pymeshlab/)
- **Open3D 0.20.0**, released 2026-09-16, MIT, cp310–cp314 wheels — [PyPI](https://pypi.org/project/open3d/)
- **CGAL Python bindings 6.0.1**, last upload 2024-10-25, wheels only cp38–cp312 (no macOS/Windows cp314) — [PyPI](https://pypi.org/project/cgal/) — effectively stale for this tool
- **polyscope 2.6.1** (viewer for debugging curves/fields on meshes), 2026-02-26, MIT, cp314 — [PyPI](https://pypi.org/project/polyscope/)
- **gpytoolbox 0.3.8**, 2026-10-06, MIT, cp314 — [PyPI](https://pypi.org/project/gpytoolbox/)
- **robust-laplacian 1.1.0** (Laplacian for non-manifold meshes and point clouds), 2026-03-25, MIT, cp314 — [PyPI](https://pypi.org/project/robust-laplacian/)
- **pygeodesic 0.1.11** (exact geodesics), last release 2024-11-26, no cp314 wheels — [PyPI](https://pypi.org/project/pygeodesic/) — superseded here by libigl's `exact_geodesic`
- **bpy 5.2.2** (Blender as a module), 2026-09-15, GPL-3, `requires_python ==3.13.*` — [PyPI](https://pypi.org/project/bpy/) — cannot be imported into the tool's 3.14 venv
- Blender Geometry Nodes: the **Shortest Edge Paths** node finds paths along mesh edges with a user-defined edge
  cost (Dijkstra) and feeds **Edge Paths to Curves** — [Blender manual](https://docs.blender.org/manual/it/dev/modeling/geometry_nodes/mesh/read/shortest_edge_paths.html)

### Inferences
- View-dependent lines (suggestive contours, apparent ridges, occluding contours) change with the camera, so a
  painted texture cannot use them; the useful classes are view-independent: creases, hard edges, UV cuts, panel
  gaps, and (weakly) curvature ridges.
- On a rolled edge, each edge loop across the bevel turns only a few degrees, so a dihedral threshold either misses
  the roll or returns several parallel loops (which is what the tool's `rolls()` reports: "its lines side by side
  across it"). Picking one of those loops and reading its "facing" is inherently ambiguous; that ambiguity is the
  root of failure 1. Treat the roll as a fillet strip with two boundary lines (where the turning starts and ends) and
  define its centre as a smooth scalar level set across the strip — e.g. the zero set of `d1 - d2` (geodesic distance
  to each boundary line), or the zero set of `n·(a - b)` with `a`, `b` the flanking faces' normals — extracted with
  `marching_triangles`. Such a level set is one continuous polyline lying exactly on the mesh, with no per-point
  normal to flip.
- Jagged ("zig-zag") feature lines appear where a true feature crosses triangles diagonally and is approximated by a
  chain of edges; chaining at valence-2 junctions with the smallest turn (what Blender's edge-path nodes do with a
  cost) then straightening between pinned corners (FlipOut, §2) is the cheap fix.
- The FBX's per-corner normals (`tri_normal`) encode the artist's hard edges; edges whose welded corners carry
  different normals are the model's own "hard lines" and are a cleaner signal than any curvature estimate.
- For this tool potpourri3d + libigl (both installed, both 3.14-ready, MIT/MPL) cover everything; PyMeshLab is GPL
  (fine for a tool that isn't redistributed in binary form, but adds nothing needed); CGAL's Python route is stale.

### Gaps
- No 2025–2026 paper was found that targets feature lines specifically on low-poly game meshes with bevels; recent
  learned "edge/curve" methods target CAD point clouds or multi-view images (not verified in depth).
- geometry-central's own latest C++ release number was not checked (potpourri3d 1.4.0 bundles it).
- The full text of the "Smooth Feature Lines on Surface Meshes" paper and of the fillet patent were not readable.

---

## 2. Curves on surfaces: geodesic paths, exact geodesics, tracing, offset curves, smoothing on the surface, snapping strokes to features

### Takeaway
The state of the art keeps a curve **intrinsic** — a sequence of surface points (face + barycentric, or points on
edges) — and never smooths in 3D then projects back. Shortest paths: FlipOut edge-flip geodesics (exact-ish, very
fast). Smooth curves: geodesic Bézier/B-spline subdivision on the surface (FlipOut's `bezierSubdivide`, b/Surf), or
distance-based smoothing (SGP 2024). Offsets ("a line beside a line"): isolines of a (signed) geodesic distance
field via marching triangles. Snapping strokes: shortest paths over a feature-weighted edge graph ("intelligent
scissors") or snakes that relax onto features. All of the core operations are in potpourri3d 1.4.0, and they run in
milliseconds on the car once the mesh is made manifold (measured).

### Cited Findings
**Geodesic paths by edge flips (FlipOut, Sharp & Crane 2020)**
- `FlipEdgeNetwork` "takes as input a path (or loop/network of paths) along the edges of a triangle mesh" and
  "straightens that path to be a geodesic"; it can be built from a Dijkstra path, a piecewise Dijkstra path through
  several vertices, or a marked edge set, and supports `extraMarkedVerts` to pin vertices — [geometry-central: flip geodesics](https://geometry-central.net/surface/algorithms/flip_geodesics/)
- `bezierSubdivide(nRounds)` builds geodesic Bézier curves with "a de Casteljau-style subdivision scheme"; control
  points must be marked vertices and the input "a single path"; `delaunayRefine()` improves the triangulation while
  "preserving the geodesics"; `getPathPolyline()` returns surface points, `getPathPolyline3D()` 3D points — [geometry-central: flip geodesics](https://geometry-central.net/surface/algorithms/flip_geodesics/)
- potpourri3d exposes `EdgeFlipGeodesicSolver.find_geodesic_path(v_start, v_end)`, `find_geodesic_path_poly(v_list)`
  (path through a vertex sequence) and `find_geodesic_loop(v_list)`, returning "Nx3 numpy arrays"; it finds "very
  short geodesic" but is "not guaranteed to generate a globally-shortest geodesic" — [potpourri3d README](https://github.com/nmwsharp/potpourri3d)
- potpourri3d does **not** expose `bezierSubdivide` (verified: its `EdgeFlipGeodesicSolver` has only the three methods
  above — measured locally via `dir()`).
- Measured locally: on the raw welded car mesh the solver refuses to build ("duplicate edge in list" — the 156
  non-manifold edges); after dropping duplicate faces and `igl.split_nonmanifold`, it builds in 0.01 s and a 35 cm
  geodesic path (41 points) takes <1 ms. Paths between different pieces fail ("vertices lie on disconnected
  components of the surface").

**Geodesic tracing (straightest continuation)**
- `GeodesicTracer.trace_geodesic_from_vertex(start_vert, direction_xyz)` / `trace_geodesic_from_face(start_face,
  bary_coords, direction_xyz)` trace a geodesic from a point and direction and return an "Nx3 numpy array of
  positions" — [potpourri3d README](https://github.com/nmwsharp/potpourri3d); added in v1.1.0 ("geodesic tracing") — [releases](https://github.com/nmwsharp/potpourri3d/releases)

**Exact geodesics**
- libigl's `exact_geodesic` is present in the 3.14-compatible wheel (measured locally); pygeodesic has no 3.14 wheel
  (PyPI, above).

**Distance fields to curves (the basis of offsets and tapes)**
- Heat method (Crane, Weischedel, Wardetzky): geodesic distance from heat flow — [Geodesics in Heat (PDF)](https://ddg.math.uni-goettingen.de/pub/heat-method-ACM.pdf)
- **Signed Heat Method** (Feng & Crane, ACM TOG 43(4), SIGGRAPH 2024): "diffuses normal vectors rather than a scalar
  distribution"; robust to "holes, noise, or self-intersections"; can "simultaneously fit multiple level sets",
  gives "a notion of distance for geometry that does not topologically bound any region", and can "mix and match
  signed and unsigned distance" — [SIGGRAPH archive](https://history.siggraph.org/?p=164194), [NSF PAR](https://par.nsf.gov/biblio/10553558)
- geometry-central's SHM computes "signed and unsigned distance to possibly broken geometry using heat flow";
  curves are ordered surface points, and "each mesh edge crossed by an input curve should be explicitly represented
  by a SurfacePoint"; "the robustness of the heat method should fill in small gaps"; options `levelSetConstraint`,
  `preserveSourceNormals`, `softLevelSetWeight`, `tCoef`; the page does not state which side is positive — [geometry-central: signed heat method](https://geometry-central.net/surface/algorithms/signed_heat_method/)
- potpourri3d `MeshSignedHeatSolver.compute_distance(curves, curve_signs=[], points=[], preserve_source_normals=False,
  level_set_constraint="ZeroSet", soft_level_set_weight=-1)`, each curve "a list of tuples (element_indices,
  barycentric_coords)"; `MeshFastMarchingDistanceSolver.compute_distance(curves, distances=[], sign=False)`;
  `marching_triangles(V, F, u, isoval=0.)` returns "list of lists of barycentric points" — [potpourri3d README](https://github.com/nmwsharp/potpourri3d)
  (signatures confirmed in the installed source); added in v1.2.2: "Signed Heat Method, signed Fast Marching Method,
  marching triangles contouring, and heat solvers for polygon meshes" — [releases](https://github.com/nmwsharp/potpourri3d/releases)
- Measured locally on the repaired car mesh, curve = a 21-vertex edge chain on the largest piece (5,506 vertices):
  signed FMM 0.007 s; Signed Heat 0.07 s (build 0.01 s); `marching_triangles` isoline at 3 cm: 3 components, 180
  points, 0.007 s; heat-method distance on the mesh subdivided twice (`igl.upsample`, 432,448 triangles): build 0.66 s,
  solve 0.03 s. Constraints hit: SHM rejects a curve whose consecutive points do not share a face ("Each curve
  segment must be contained within a single face"), signed FMM likewise; FMM refuses non-manifold meshes ("handling
  of nonmanifold mesh not yet implemented"); SHM failed to factorize on the unrepaired mesh. With `sign=True`, FMM
  returned only non-negative values for this open chain, while SHM returned both signs (67% of the piece negative) —
  i.e. SHM gives a side for open curves, FMM (as called) did not.
- New (March 2026, revised Sept 2026): "Convex Quadratic Distance Field Computation" (Ruan, Chern, Li, Subr,
  Vaxman) represents distance fields piecewise-quadratically because "the squared distance is exactly quadratic" on
  such domains, for triangle surfaces and tet volumes, with non-manifold connectivity support; no code link on the
  abstract page — [arXiv 2603.03231](https://arxiv.org/abs/2603.03231)

**Smooth curves on surfaces**
- b/Surf (Mancinelli, Nazzaro, Pellacini, Puppo; IEEE TVCG 29(7), 2022/23): direct manifold extensions of de
  Casteljau and Bernstein evaluation "are fragile and prone to discontinuities when control polygons become large",
  while subdivision-based approaches (recursive de Casteljau bisection, open-uniform Lane–Riesenfeld) "are robust";
  interactive on meshes with millions of triangles; "All computations occur in the intrinsic geodesic metric" — [project page](https://ggg.dibris.unige.it/papers/TVCG22_bSurf/TVCG22.html), [arXiv 2102.05921](https://arxiv.org/pdf/2102.05921)
- Older "Geodesic Bézier curves on triangle meshes" (Morera, Carvalho, Velho) — [SIGGRAPH archive](https://history.siggraph.org/?p=139477) — superseded by b/Surf's subdivision schemes and FlipOut's `bezierSubdivide` per the robustness finding above.
- "Distance-Based Smoothing of Curves on Surface Meshes" (Pawellek, Rössl, Lawonn; SGP 2024, CGF 43(5)): smooths a
  discrete surface curve by finding geodesics in a **lifted surface** (a penalty potential as a 4th coordinate)
  projected back to the mesh; "guaranteed convergence and good approximation of the initial curve", one parameter
  trading smoothness against similarity — [Eurographics DL](https://diglib.eg.org/handle/10.1111/cgf15135) (abstract via search; PDF returned 403)
- A survey "Splines on manifolds" (Mancinelli & Puppo, CAGD 2024) is listed on the authors' group site — [GGG Genoa](https://ggg.dibris.unige.it) (not read)

**Snapping user strokes to features**
- Intelligent mesh scissoring with 3D snakes: an open user contour is completed into a loop and relaxed as a 3D
  geometric snake using curvature and centricity until it settles on the cut, following the minima rule (parts
  divide along concave discontinuities) — [Intelligent Mesh Scissoring Using 3D Snakes](https://faculty.runi.ac.il/arik/site/mesh-scissor-snake.asp)
- Blender's Shortest Edge Paths node (Dijkstra with arbitrary per-edge cost) is the node-graph version of
  feature-weighted snapping — [Blender manual](https://docs.blender.org/manual/it/dev/modeling/geometry_nodes/mesh/read/shortest_edge_paths.html)

### Inferences
- Failure 2 ("leaves the mesh where short lines meet — steps") is the textbook symptom of 3D smoothing + closest-point
  projection: near a fold, the closest point jumps between faces, so a smooth 3D curve becomes a stepped surface
  curve. Intrinsic methods cannot produce it, because every point is created on a face.
- "A line beside a line" is exactly an **isoline of the signed distance** to the model's line:
  `marching_triangles(V, F, d, isoval=offset)`. It is on the mesh by construction, parallel in the geodesic sense
  (constant surface distance — what a real tape edge does), handles bends without the "points crowd and cross on the
  inside" problem the current `offset()` docstring describes, and costs ~10 ms. Around an open curve the isoline also
  wraps the curve's ends ("stadium" shape) and may have stray components; keep only the stretch whose nearest curve
  point is interior (an arc-length field, §4).
- Smoothing that stays on the surface, cheapest first: (a) don't smooth model lines — they are the model's; (b) for
  zig-zag edge chains, FlipOut between pinned corners; (c) for free strokes through clicks, `find_geodesic_path_poly`
  then smooth by taking the zero isoline of a heat/SHM field with a larger `t_coef` (heat diffusion is itself a
  smoother) — untested idea; (d) geodesic Bézier via geometry-central C++ (`bezierSubdivide`) or b/Surf (yocto-gl,
  C++) — would need bindings; (e) Distance-Based Smoothing (SGP 2024) — code availability unknown.
- Snapping: the user's rule "one of the model's lines whole, or a line beside one" maps cleanly onto: snap each click
  to the nearest model line (graph of feature chains), take the model's own chain between snapped clicks (no
  smoothing at all), and, for "beside", an isoline of its distance.

### Gaps
- potpourri3d returns flip-geodesic paths as 3D points, not (face, barycentric) surface points; converting them back
  to surface points (each lies on an edge) needs a small locator — not found as a built-in.
- The sign convention of SHM on surfaces (which side is positive vs curve direction and normal) is not documented on
  the geometry-central page; must be fixed empirically once.
- Why signed FMM returned no negative values for an open chain was not resolved (it may require closed/oriented
  curves).
- No 2025–2026 Python package for geodesic Bézier/B-splines on meshes was found.

---

## 3. Drawing a constant-width band/tape along a surface curve: distance fields, side, rolled edges, wrap vs one face, anti-aliasing, UV seams

### Takeaway
The robust way is to make the tape a **level band of a geodesic (signed) distance field to the curve, computed on
the welded 3D surface and interpolated per texel through the bake's triangle id + barycentrics**: membership,
width and side come from surface connectivity, not from comparing normals, so rolled edges cannot make it hop, thin
panels' far sides are geodesically far, and both sides of a UV seam read the same value. "Wrap the edge" vs "stay on
one face" becomes a choice of band (`|d| <= w/2` vs `0 <= ±d <= w`) and of domain (cut the mesh along a hard crease
to stop the tape there). Industry tools (Substance 3D Painter's Path/Ribbon tools) likewise work "only in 3D space on
the surface of the geometry".

### Cited Findings
- Substance 3D Painter's Path tools (paint along path, **Ribbon** path, filled path, erase/smudge along path) "only
  works in 3D space on the surface of the geometry" — [Adobe: Path tool overview](https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/painting/path-tools/path)
- Painter 11.1 (2025-11-18) added the Ribbon tool, which will "transform and repeat a texture along a path without
  any cuts, with extra control for the start and the end, as well as options for sharp corners", used for stitches,
  zippers, welds, text along paths and "trims to wrap around a mesh" — [Adobe blog](https://blog.adobe.com/en/publish/2025/11/18/substance-3d-painter-update-adds-ribbon-tool-real-world-displacement), [Painter 11.1 release notes](https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/release-notes/version-11-1)
- Licensing: Painter is Adobe subscription, or a yearly **perpetual Steam licence** (e.g. "Substance 3D Painter
  2026"): you keep that version forever; updates stop when the next yearly version ships — [Adobe community](https://community.adobe.com/t5/substance-3d-painter-discussions/how-do-steam-perpetual-licenses-work-exactly/td-p/15536613), [Steam store page](https://store.steampowered.com/app/3366290/?cc=us) (an external app; reference for the method, not a dependency)
- Signed Heat Method: robust to broken input, can mix signed and unsigned curves, defines distance for curves that
  bound no region — [SIGGRAPH archive](https://history.siggraph.org/?p=164194); geometry-central's implementation
  "should fill in small gaps" — [geometry-central SHM](https://geometry-central.net/surface/algorithms/signed_heat_method/)
- potpourri3d's heat distance has `use_robust=True` by default (robust Laplacian, tolerant of non-manifold input) — [potpourri3d README](https://github.com/nmwsharp/potpourri3d); robust-laplacian also handles point clouds — [PyPI](https://pypi.org/project/robust-laplacian/)
- potpourri3d also offers `PointCloudHeatSolver` with `compute_signed_distance`, `compute_log_map`,
  `extend_scalar`, `transport_tangent_vectors` (measured locally via `dir()`), i.e. the same fields on a point set
  with no mesh connectivity.
- Seams: visual artifacts at UV seams come from the parameterization (texels on both sides of a seam are filtered
  independently); "Seamless" (Liu, Ferguson, Jacobson, Gingold, SIGGRAPH Asia 2017) characterises seam-free textures
  as the null space of a linear operator and erases seam artifacts, with open-source code — [project page](https://cragl.cs.gmu.edu/seamless/)
- Measured locally (§2): the heat distance on a 16x-subdivided body (432k triangles) builds in 0.66 s and solves in
  0.03 s; Signed Heat on the base mesh solves in 0.07 s — negligible next to a paint.

### Inferences
- **Why failure 1 happens and why the field fixes it.** The current rule keeps a texel if its normal is within 60°
  of the curve's facing at the *Euclidean*-nearest curve point. On a roll the nearest point and its smoothed facing
  swing between the side and the underside, so the 60° cone swings with them (20 flips over 30°). A geodesic band
  has no cone: a texel belongs to the tape iff the shortest path *along the surface* to the curve is ≤ w/2. The
  underside is reached only by going round the roll, so its distance grows continuously and the band edge is a
  smooth isoline — no hops. The same property removes the reason for the facing filter (the far side of a thin
  panel is near in 3D but far along the surface).
- **Width correctness on a roll.** A real vinyl tape keeps its width measured along the surface; Euclidean (chord)
  distance under-measures across a tight roll, so the tape looks narrower there. Geodesic distance is the faithful
  one.
- **Wrap vs one face (IMPROVEMENTS H.1).** With a signed distance `d` to the edge's line: wrap = `|d| <= w/2`; on one
  face with the tape's edge on the line = `0 <= d <= w` (or `-w <= d <= 0` for the other face). To make a tape *stop*
  at a hard crease instead of folding over, compute the field on the mesh **cut along that crease**
  (`igl.cut_mesh`): distance cannot cross a cut, so "which face it belongs to" is decided by topology, never by a
  normal.
- **Side.** Take the side from SHM's sign near the curve (fix its convention once), magnitude from the unsigned heat
  or FMM distance if SHM's near-source accuracy proves soft. Far from an open curve the "generalized" sign is not
  meaningful, so restrict to the tape's reach.
- **Resolution.** Fields are per vertex, linear inside each triangle. Distance to a straight curve along a mesh edge
  is affine inside a flat neighbouring triangle, so model lines that *are* edges are reproduced exactly; curved or
  free curves crossing big faces (p90 edge 7.6 cm, max 24 cm) are not. Fix: subdivide (geometry-preserving midpoint
  `igl.upsample`; 1 level = 4x, 2 levels = 16x triangles) before solving; a texel's sub-triangle and barycentrics
  follow in closed form from its original triangle's barycentrics. The 2026 quadratic distance-field paper targets
  exactly this error but has no code yet.
- **UV seams.** A field defined on the welded 3D surface and sampled per texel through (FBX triangle id,
  barycentrics) gives *identical* values to the two texels that sit on either side of a UV seam at the same 3D point,
  so a band cannot break at a UV seam by construction (failure 3, UV part). What remains is texture filtering: pad
  (dilate) each island's colours outward a few texels — enough for the mip levels and 4x4 block compression the game
  uses — so bilinear/mip sampling at the seam doesn't pull in background.
- **Panel seams / gaps between pieces** (the car has ~39 pieces): a surface field cannot cross a gap. Options:
  (a) weld across hairline gaps with a tolerance; (b) solve per piece with the curve split into its per-piece
  stretches, the band staying continuous because the curve is continuous in 3D; (c) `PointCloudHeatSolver` over a
  dense sample of all pieces bridges gaps by proximity — but it would also bridge the two sides of a thin panel, so
  only on a selected region.
- **Anti-aliasing in texture space.** Coverage = clamp(0.5 + (w/2 − |d|) / p) with p the texel's own pitch in cm
  (from the bake's position derivatives), so every edge is exactly one texel soft regardless of how much an island
  is stretched.
- **Mirrored/shared texels** (bake `count > 1`): a field evaluated on one copy paints both; the tool's existing
  mirror logic must decide the band on the owning side.

### Gaps
- No source was found giving a recommended padding width for BC-compressed DDS mips on this game; the number must
  be measured on the tool's own textures.
- How accurate SHM/heat distances are within ~1 mm of the source on this mesh (vs exact geodesics) was not measured;
  `igl.exact_geodesic` can serve as ground truth.
- Whether geometry-central's SHM requires a manifold mesh is undocumented; on the raw mesh it failed to factorize
  (measured), on the repaired mesh it worked.

---

## 4. Decals and stickers along curves: projection, exponential/log maps, vector heat, and libraries

### Takeaway
A decal or a repeated pattern on a curved surface is placed through a **local surface parameterization**: the
logarithmic map around a point (decals, roundels) or a **ribbon chart (s, b)** along a curve — s the arc length of
the nearest curve point, b the signed geodesic distance (dashes, ticks, chevrons, text along a line). The current
best log map is the **Affine Heat Method** (SGP 2025 best paper), already the default in potpourri3d ≥1.3. Planar
projective decals smear on curvature and are superseded for this use.

### Cited Findings
- Discrete exponential map decals (Schmidt, Grimm, Wyvill, SIGGRAPH 2006): decal parameterizations via a discrete
  approximation of the exponential map computed in O(N log N) with one extra step in Dijkstra; decals can contain
  holes, combine with conformal parameterization, work on any point set, and stick to deforming surfaces — [Interactive Decal Compositing with Discrete Exponential Maps](https://prism.ucalgary.ca/handle/1880/46212)
- Vector Heat Method (Sharp, Soliman, Crane, SIGGRAPH 2019): parallel transport by a short-time heat flow of the
  connection Laplacian, used to invert the exponential map (log map), extend values by nearest geodesic neighbour,
  etc.; the log map is useful "for applications such as texture decaling" — [arXiv 1805.09170](https://arxiv.org/pdf/1805.09170), [geometry-central: vector heat](https://geometry-central.net/surface/algorithms/vector_heat_method/)
- **Affine Heat Method** (Soliman & Sharp, CGF 2025, SGP 2025 Best Paper): a connection Laplacian with a homogeneous
  coordinate for translation; short-time heat flow gives "both the direction and distance from the source, along
  shortest geodesics"; a localized variant allows pre-computation for fast repeated solves, an adaptive variant
  "resolves the map even near the cut locus"; "improves accuracy compared to past approaches" — [Eurographics DL](https://diglib.eg.org/handle/10.1111/cgf70205), [project page](https://www.yousufsoliman.com/projects/the-affine-heat-method.html)
- potpourri3d v1.3.0 "Introduced Affine Heat Method" and made the Vector Heat Method use intrinsic triangulations by
  default — [releases](https://github.com/nmwsharp/potpourri3d/releases); `MeshVectorHeatSolver.compute_log_map(v_ind,
  strategy='AffineLocal')` with strategies 'VectorHeat', 'AffineLocal', 'AffineAdaptive'; `extend_scalar(v_inds,
  values)` "nearest-geodesic-neighbor interpolate values"; `transport_tangent_vectors`; `get_tangent_frames` — [potpourri3d README](https://github.com/nmwsharp/potpourri3d) (default `AffineLocal` confirmed in the installed source)
- Measured locally: `MeshVectorHeatSolver` refuses the raw welded car mesh (non-manifold), builds in 0.01 s on the
  repaired one, and a log map takes 0.17 s.
- Newest (2026-09-09, arXiv): **iLogMap** (Banduc, Pezzuto, Sahli Costabal) reformulates the angular part of the log
  map as a ground-state magnetic-Laplacian eigenproblem, reporting "competitive angular accuracy and reduced metric
  distortion relative to heat-based methods, with improved performance on surfaces with boundary"; no code mentioned — [arXiv 2609.10503](https://arxiv.org/abs/2609.10503)
- Industry precedent for patterns along a path: Substance Painter's Ribbon tool repeats or stretches an image along a
  surface path "without any cuts", with sharp-corner options — [Adobe blog](https://blog.adobe.com/en/publish/2025/11/18/substance-3d-painter-update-adds-ribbon-tool-real-world-displacement)

### Inferences
- Ribbon chart for marks along a line: b = signed geodesic distance (§3); s = `extend_scalar(curve_vertex_ids,
  arc_lengths)` (each point takes the arc length of its geodesically nearest curve vertex — piecewise constant, so
  for crisp dash ends refine s inside a cell from the local tangent) — or, on a point set, `PointCloudHeatSolver
  .extend_scalar`. Dashes = band ∩ (s mod period < dash), ticks = band at s_k, text = glyphs in (s, b). Because both
  coordinates are intrinsic, a dash wraps a roll with its true length.
- Single decals (a roundel, a number) = log map around the centre (`AffineLocal`, or `AffineAdaptive` if it nears
  the cut locus), then sample the image at the log-map coordinates per texel (interpolated through tri + barycentrics).
  Decals larger than the region where geodesics stay unique will distort; check the area distortion before showing.
- The tool's existing lettering problem ("lettering has never come out well on this car's curves", RULES.md) is a
  parameterization problem as much as a design one; the log map / ribbon chart is the standard remedy, but per the
  rules words go on only when asked.

### Gaps
- No Python package found that implements geodesic "ribbon" coordinates along a curve directly; it has to be composed
  from the solvers above.
- AHM's measured accuracy versus VHM on this specific low-poly mesh was not tested.

---

## 5. Automatic quality checks for a painted line (width evenness, gaps, kinks, curvature continuity, seams)

### Takeaway
No standard library ships "tape QA"; the checks are built from the same intrinsic quantities. The ones that name
the user's actual failures: side flips along the line (must be 0), band coverage per station (gaps, width
evenness), off-surface distance (must be 0 by construction), discrete geodesic curvature and its jumps (steps,
kinks), and agreement across every UV seam the band crosses. Each is milliseconds on this mesh. Per the project's
rules, these are gates for accidents; the user's eye still decides.

### Cited Findings
- The Signed Heat Method's output is a field whose level sets are the curve and its offsets (multiple level sets can
  be fitted at once) — [SIGGRAPH archive](https://history.siggraph.org/?p=164194); level sets are extracted as
  barycentric polylines by `marching_triangles` — [potpourri3d README](https://github.com/nmwsharp/potpourri3d)
- Distance-based smoothing exposes a single parameter trading smoothness against similarity to the input curve, a
  natural "how far did smoothing move the line" measure — [Eurographics DL](https://diglib.eg.org/handle/10.1111/cgf15135)
- b/Surf notes that direct manifold de Casteljau/Bernstein evaluation produces discontinuities for large control
  polygons — the failure a continuity check must catch — [b/Surf](https://ggg.dibris.unige.it/papers/TVCG22_bSurf/TVCG22.html)
- Path tools in commercial painters expose "options for sharp corners" — corners are a designed property, not
  noise, which a kink check must respect — [Adobe blog](https://blog.adobe.com/en/publish/2025/11/18/substance-3d-painter-update-adds-ribbon-tool-real-world-displacement)

### Inferences (proposed checks; none is a published standard)
- **Flip count:** walk the curve in 0.5 cm stations; at each, record which side (SHM sign) and which face region the
  band occupies; count changes. The current method's measured "20 flips over 30°" becomes a hard 0 gate.
- **Gaps / width evenness:** per station slab of length Δs, effective width = (sum of covered texel areas in cm²,
  from the bake's pitch) / Δs; flag stations below ~95% of w or above ~105%. Works on the texture actually painted,
  so it also catches rasterization holes.
- **On-surface:** curves stored as (face, barycentric) are on the surface exactly; for any curve carried as 3D points,
  `igl.signed_distance`/point-to-mesh distance must be ~0 everywhere (a "step" shows as a spike).
- **Kinks / curvature continuity:** discrete geodesic curvature at each polyline vertex = turning angle measured in
  the surface after unfolding the adjacent faces (the Polthier–Schmies "straightest geodesics" notion — prior
  knowledge, not fetched here); flag turning above a per-cm threshold, and flag jumps in it between neighbours
  (curvature discontinuity) except at corners the design asks for.
- **Seams:** for every UV seam edge the band crosses, sample the coverage on both islands at the same 3D points
  (same welded edge, same parameter): the difference must be within the anti-aliasing tolerance.
- **Model-line fidelity:** for "a model line whole", the Hausdorff distance between the painted line's centre and the
  model's edge chain; for "a line beside one", the spread of its distance to the source line (should be ~0 around the
  intended offset).

### Gaps
- No published benchmark or metric suite for "tapes on game meshes" was found; thresholds must be set on the tool's
  own cars against the user's judgement.

---

## Applicability to this tool (the three failures, and a concrete, small implementation)

### Takeaway
Replace the Euclidean nearest-point + 60° facing filter with **intrinsic fields on the welded, repaired car surface,
sampled per texel through the bake's triangle id and barycentrics**; build lines as surface-point polylines (model
edge chains, level sets, flip geodesics) and never smooth in 3D. Everything needed is already installed
(potpourri3d 1.4.0, libigl 2.6.3, both on Python 3.14), MIT/MPL, no GPU, and measured at well under a second per
line on the car — so it does not add a cost every skin pays in any meaningful amount.

### Cited Findings (the specific functions, all verified present in the tool's venv)
- `igl.split_nonmanifold`, `igl.upsample`, `igl.cut_mesh`, `igl.sharp_edges`, `igl.dihedral_angles`,
  `igl.principal_curvature`, `igl.exact_geodesic`, `igl.signed_distance` — libigl 2.6.3 [PyPI](https://pypi.org/project/libigl/) (presence measured locally)
- `pp.MeshSignedHeatSolver.compute_distance`, `pp.MeshHeatMethodDistanceSolver.compute_distance(_multisource)`,
  `pp.MeshFastMarchingDistanceSolver.compute_distance(curves, sign=...)`, `pp.marching_triangles`,
  `pp.EdgeFlipGeodesicSolver.find_geodesic_path(_poly|_loop)`, `pp.GeodesicTracer.trace_geodesic_from_face`,
  `pp.MeshVectorHeatSolver.compute_log_map / extend_scalar / transport_tangent_vectors`,
  `pp.PointCloudHeatSolver.compute_signed_distance` — potpourri3d 1.4.0 [README](https://github.com/nmwsharp/potpourri3d), [PyPI](https://pypi.org/project/potpourri3d/)
- Requirements found by measurement: manifold input (drop 156 duplicate faces + `split_nonmanifold`); curves for
  SHM / signed FMM given with every edge crossing explicit (consecutive points share a face); one connected piece per
  solve. Timings: solver builds ≤0.04 s; SHM solve 0.07 s; FMM 0.007 s; isoline 0.007 s; log map 0.17 s; heat on
  the 16x-subdivided body 0.69 s total (measured locally, Mac).
- Signed Heat Method robustness to gaps and broken curves — [geometry-central SHM](https://geometry-central.net/surface/algorithms/signed_heat_method/), [SIGGRAPH 2024](https://history.siggraph.org/?p=164194)

### Inferences — what fixes each failure
**Failure 1 — the band hops between side and underside on a rolled edge (60° facing filter flips 20 times).**
- Cause: membership decided by comparing the texel's normal with a per-point "facing" of a line on a roll, where
  that facing is ill-defined.
- Fix: (1) define the roll's line once as a level set across the fillet strip (crown or bisector, `marching_triangles`),
  so the line itself is one smooth surface curve; (2) tape = `|d| <= w/2` (wrap) or `0 <= ±d <= w` (one face, H.1) of
  the signed geodesic distance `d` to that line; (3) delete the facing filter — thin-panel far sides are excluded
  because they are geodesically far; (4) where a tape must stop at a hard crease, solve on the mesh cut along it.
  Gate: flip count = 0, width per station within ±5%.

**Failure 2 — picked lines leave the mesh where the model's short lines meet (steps).**
- Cause: Catmull-Rom in 3D, then closest-point projection (`meshlines.smooth`) and the 3D walk + least squares +
  projection in `Course.offset`.
- Fix: (1) snap each click to the nearest model line and take the model's own edge chain between snapped clicks —
  the user's "one of the model's lines whole" needs no smoothing; (2) chain short feature segments into maximal lines
  at junctions with the smallest turn before anything else; (3) straighten zig-zag chains with
  `EdgeFlipGeodesicSolver.find_geodesic_path_poly` through pinned corner vertices; (4) "a line beside one" =
  `marching_triangles(V, F, d, isoval=offset)` of the signed distance to the model line (no walking, no crossing on
  the inside of bends); (5) free curves = `find_geodesic_path_poly` through the clicks, smoothed only intrinsically
  (zero set of a smoother heat/SHM field, or geodesic Bézier in C++ later); (6) extend a line past its end with
  `GeodesicTracer.trace_geodesic_from_face` (straightest continuation, e.g. "carry the tape on to the rear"). Gate:
  on-surface distance 0, geodesic-curvature jump below threshold except designed corners.

**Failure 3 — a band crossing a UV seam or a panel seam breaks.**
- UV seams: the field lives on the welded 3D surface; each texel reads it through its FBX triangle id + barycentrics
  (`bake.py` already stores the id; `raster.rasterise` gives the weights), so both sides of a UV seam get the same
  value by construction; then pad each island outward by a measured number of texels for mips/compression. Gate:
  coverage difference across every crossed seam edge within the AA tolerance.
- Panel seams (separate pieces, ~39 on the body): weld hairline gaps with a tolerance; otherwise split the curve per
  piece and solve each piece, the band staying continuous because the curve is continuous in 3D; SHM tolerates small
  gaps in the *curve*. Point-cloud heat bridges pieces but also thin panels — use only on a selected region.

**Order of work (smallest step the user can see first, per RULES.md):**
1. A surface module: weld (0.01 cm), drop duplicate faces, `split_nonmanifold`, keep the map back to FBX triangles,
   per-piece solvers cached per car (rebuilt in ~0.05 s).
2. One tape on the roll that fails today, painted from `|d| <= w/2` with texel-pitch anti-aliasing, shown close up
   beside the current one with the flip count and width-per-station numbers.
3. Then offsets as isolines, snapping clicks to model lines, and the seam/flip/width gates in `checks.py`.
- The self-test will show every car with a tape changing byte-for-byte; per RULES.md the commit must say which and
  why.

### Gaps
- Not yet measured on the tool's own failing roll: whether SHM's near-source accuracy gives a crisp 1-texel band
  edge at 4096 px without subdivision, and how many subdivision levels the narrowest tapes need.
- The exact padding the game needs at seams, and how the 39 pieces' gaps are distributed (hairline vs real), are
  unmeasured.
- Windows timings were not measured (Mac only); the solvers are CPU sparse solves, so no GPU dependence is expected.
