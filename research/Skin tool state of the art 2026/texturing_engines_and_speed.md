# Texturing engines and speed: what a small Python skin painter can use or copy (October 2026)

Scope: procedural texturing / texture-painting engines and GPU libraries a ~17k-line numpy tool
(Python 3.14, Mac M-series for design, Windows PC with an NVIDIA GPU for the game) could use or
copy, how pros make smart materials and curvature/AO-driven wear, and whether to keep numpy, move
parts to the GPU, or build on an existing engine.

Note on "local measurement" sources: some numbers below were measured on 2026-10-07 on the
project's Mac (Apple M5, 10 cores, 16 GB RAM; about 0.5 GB free and 2.1 GB of swap in use at
the time, so under memory pressure) with a throwaway script
(`/private/tmp/claude-501/-Users-fcarbo-Developer-personal-tm-skin-creator/8edfddd8-8d18-417e-b745-274b5d893c1c/scratchpad/bench.py`, `bench2.py`, `bench3.py`) that imports the tool's own `tool/noise.py` read-only. They are one machine and one run each (best of 1–5 repeats), not a published benchmark.

## 1. Substance 3D Painter/Designer in 2026: automation, licensing, headless use; MaterialX and OpenPBR

### Takeaway
Substance can't be scripted headlessly by an individual for a sensible price. Painter's Python API only drives a running GUI app. The command-line engine (sbsrender/sbsbaker/pysbs, the Automation Toolkit) comes only with an Enterprise licence. The Steam perpetual edition ($199.99, one year of updates) is fine for a human artist but gives a Python tool nothing it can call. MaterialX 1.39.5 (Python 3.14 wheels, with a Metal/GLSL texture baker) and OpenPBR 1.1.1 are the open standards. They are useful as vocabulary and for interchange, not as a replacement engine for this tool.

### Cited Findings
- **Painter Python API**: "The Python API gives you the ability to manipulate Painter in many ways: create and export projects, configure resource locations"; current docs are for API 0.3.5, with updates for Painter 12.1.0 (e.g., geometry masks) — [Adobe Experience League, Painter Python API](https://experienceleague.adobe.com/en/docs/substance-3d-dev/painter-python/substance-3d-painter-python); [API overview 0.3.5](https://experienceleague.adobe.com/en/docs/substance-3d-dev/painter-python/api/api-overview)
- **Remote control is not headless**: Painter must be launched with `"Adobe Substance 3D painter.exe" --enable-remote-scripting`. Scripts are sent as HTTP POSTs to port 60041, and "Make sure the application is up and running with this command before running any scripts". The page documents no GUI-less mode — [Remote control / headless tutorial](https://experienceleague.adobe.com/en/docs/substance-3d-dev/painter-python/tutorials/remote-control)
- **Steam perpetual edition**: "Substance 3D Painter 2026" sells for $199.99 USD. "If you purchase the Standalone perpetual version, you will get free feature updates until March 2027. After that date, you will get to keep this version." Minimum specs: macOS 12 on an Apple M1 with 16 GB; Windows 11 with an RTX 2060 Super — [Steam store page](https://store.steampowered.com/app/4329260/?cc=us). Regional prices are C$259.99 / A$289.95 / £167.99 — [gg.deals](https://gg.deals/application/substance-3d-painter-2026/). (Steam's page showed a release date of "March 11, 2025", while another listing gave March 17, 2026 for the 2026 edition — [gamersunchained](https://www.gamersunchained.com/game/substance-3d-painter-2026). The date is uncertain; the price and update window are consistent.)
- **Subscription**: the Substance 3D Texturing plan (Painter, Designer, Sampler, Assets) went "from $19.99 to $24.99 per month and from $219.88 to $249.88 for annual pre-paid plans", effective March 25, 2025. The Collection plan is $59.99/month — [Adobe blog, 2025-02-20](https://blog.adobe.com/en/publish/2025/02/20/substance-3d-innovations-pricing-updates)
- **Substance Automation Toolkit (SAT)** = command-line tools (sbsrender renders maps from .sbsar; sbsbaker bakes mesh maps; sbscooker) + pysbs (Python API for .sbs files). The latest listed version is 15.0.1 / 2025.0.1 (2025-07-22), adding USD/STL/PLY/glTF resource linking to pysbs — [SAT release notes](https://helpx.adobe.com/substance-3d-sat/release-notes.html); [Command line tools](https://helpx.adobe.com/substance-3d-sat/command-line-tools.chromeless.html)
- **SAT is Enterprise-only**: Adobe staff wrote "sbsbaker is no longer available with SD since at least 2015... Sbsbaker is part of SAT... today, the only way to get SAT is to have an Enterprise subscription". A "light" SAT for indies was mentioned with no ETA — [Adobe community, 2021](https://community.adobe.com/questions-46/sbsbaker-exe-missing-from-substance-designer-11-2-2-631171). Users report the Enterprise licence costs more than 5× an individual one — [Adobe community thread](https://community.adobe.com/questions-50/is-there-any-update-on-automation-toolkit-for-indies-and-teams-accounts-625610)
- **Other node-graph tools**: Material Maker 1.5 (January 20, 2026) is MIT-licensed, runs on Windows/Linux/macOS, has 3D texture painting, added "10 new nodes, including seven SDF nodes", and "reinstates the command-line interface, making it possible to bulk-export materials from the command line" — [CG Channel](https://www.cgchannel.com/2026/01/check-out-free-material-authoring-software-material-maker-1-5/); [Digital Production](https://digitalproduction.com/2026/01/26/material-maker-1-5-adds-dds-fbx-cli-10-new-nodes/). InstaMAT's free Pioneer licence applies while the client's revenue/funding stays under USD 100k (Indie: 250k cap; Pro: no cap) — [Abstract community](https://community.abstract3d.com/t/question-regards-instamat-pioneer-license-for-freelancers/2078)
- **OpenPBR**: "OpenPBR Surface specification v1.1.1, 2026-04-17"; "We also provide a reference implementation in MaterialX" — [OpenPBR spec (ASWF)](https://academysoftwarefoundation.github.io/OpenPBR/). OpenPBR 1.1 is available in MaterialX 1.39.2 and OpenUSD 25.02 — [MaterialX TAC update 2026](https://tac.aswf.io/meetings/2026-02-04/MaterialX_TAC_Update_2026_Final.pdf) (via search summary). NVIDIA Omniverse Kit 110.0 (March 2026) added an OpenPBR Surface material template — [Omniverse materials release notes](https://docs.omniverse.nvidia.com/materials-and-rendering/latest/materials_release-notes.html)
- **MaterialX 1.39.4** added hex-tiled images, WebGPU shading language, NanoColor names, lat-long images and animated materials — [releasealert summary of MaterialX releases](https://releasealert.dev/github/AcademySoftwareFoundation/MaterialX)
- **MaterialX on PyPI**: 1.39.5 (2026-05-22), with cp39–cp314 wheels for macOS arm64, Windows amd64 and Linux — [PyPI MaterialX](https://pypi.org/project/MaterialX/). The wheel ships shader generators for GLSL, MSL, Slang, MDL and OSL, render modules for GLSL/MSL/OSL, and `_scripts/baketextures.py`. That script is described as "Generate a baked version of each material in the input document, using the TextureBaker class", defaults to the Metal backend on macOS and has `--width/--height/--hdr` options (local inspection of the 1.39.5 cp314 macOS wheel) — [PyPI MaterialX files](https://pypi.org/project/MaterialX/#files)

### Inferences
- Substance can't become this tool's engine. The only one-time-payment route (Steam, $199.99, updates for about a year) has no command-line renderer or baker, and Painter's API needs the GUI app open. The scriptable route (SAT) needs an Enterprise contract, which is far outside "free or one-time payment".
- Even with Painter, the user's loop (Claude edits code → paint → show in the Lab) would gain a second heavy app on two machines, and its project files would replace code the tool already owns.
- Material Maker (MIT, with a CLI) and MaterialX can bake 2D/UV-space procedural graphs to textures. But this tool's patterns are drawn in 3D on the car's baked positions, so seams don't break them. A UV-space graph baker doesn't natively do that (see Gaps). They are a source of ideas: node vocabulary, SDF nodes, hex tiling, OpenPBR parameter names. They are not a drop-in.

### Gaps
- No primary source found on whether Painter can run with no window at all, or whether the Steam edition includes the Python API (it's the same app, so presumably yes, but not confirmed).
- No public 2026 price for Substance Enterprise / SAT, and no sign the promised "light" SAT for individuals has shipped.
- It isn't verified whether MaterialX's TextureBaker can sample 3D object-space position on an arbitrary mesh, as opposed to rendering the graph in UV space. That decides whether it could replace 3D-on-the-bake painting. InstaMAT's scripting/API terms weren't found.

## 2. Blender as a headless engine (bpy, baking, painting, Cycles GPU)

### Takeaway
Blender 5.2 LTS (July 2026) is current and 5.3 is in development. `pip install bpy` works on macOS arm64 and Windows but is pinned to Python 3.13, so it can't be imported into the tool's Python 3.14 process: it would need a second runtime. Cycles can bake AO, position, normal, emit and so on to images with "Extend" or "Adjacent Faces" margins. It has no curvature or thickness bake type.

### Cited Findings
- **Versions**: 5.0 released November 18, 2025; 5.1 on March 17, 2026; 5.2 LTS on July 14, 2026 ("maintained for two years"); 5.3 in alpha; 4.5 LTS supported until July 2027. "Every Blender release is supported until its successor, approximately every four months" — [Blender release notes index](https://developer.blender.org/docs/release_notes/). 5.3 was "in alpha until September 30, 2026" — [5.3 notes](https://developer.blender.org/docs/release_notes/5.3/)
- **bpy on PyPI**: 5.2.2 (2026-09-15), `requires_python ===3.13.*`, wheels for macOS 11 arm64, Windows amd64, Windows arm64 and Linux x86_64, licence GPL-3.0. "Each Blender release supports one Python version, and the package is only compatible with that version" — [PyPI bpy](https://pypi.org/project/bpy/)
- **5.2 Python API**: added "GPU initialization for background mode" and "Buffer methods & context manager for pixel data access" (buffer protocol for images; grey/RGB/RGBA; read/write file types) — [5.2 Python API notes](https://developer.blender.org/docs/release_notes/5.2/python_api/)
- **5.2 Cycles**: a new texture cache that "significantly reduces memory usage and startup time"; "The minimum driver version for OptiX is now 575" — [5.2 Cycles notes](https://developer.blender.org/docs/release_notes/5.2/cycles/)
- **5.3 texture painting**: "Undo and redo has been optimized for high resolution images and UDIMs"; "Efficient update of image textures and mipmaps is now supported in material draw mode and EEVEE". No texture/paint layers are listed — [5.3 Sculpt, Paint, Texture notes](https://developer.blender.org/docs/release_notes/5.3/sculpt/). A third-party blog claims "Blender 5.3 texture layers" — [StraySpark blog](https://www.strayspark.studio/blog/blender-5-3-texture-layers-baking-game-developers). The official 5.3 notes don't confirm it (conflict, so treat it as unconfirmed).
- **Cycles bake types**: Combined, Ambient Occlusion, Shadow, Position, Normal, UV, Roughness, Emit, Environment, Diffuse, Glossy, Transmission (plus Normal/Displacement/Vector Displacement from Multires). Margin is either "Extend: Extend border pixels outwards" or "Adjacent Faces: Fill margin using pixels from adjacent faces across UV seams". Selected-to-Active has a cage, cage extrusion and max ray distance. Output goes to Image Textures or the Active Color Attribute. The manual lists no curvature or thickness bake — [Blender 5.2 manual, Render Baking](https://docs.blender.org/manual/en/latest/render/cycles/baking.html)

### Inferences
- Using Blender means running a separate Python 3.13 venv or the Blender binary as a subprocess (`blender -b --python`), with files on disk as the interface. That adds a second runtime (a full Blender build) on both machines and a second Python version to keep in step every year. That cost would land on every skin if painting moved there.
- What Blender would add over the current numpy bake is ray-traced AO and selected-to-active baking. AO and thickness can also be computed in-process (libigl `ambient_occlusion`, embreex rays; see §3), once per mesh and cached.
- The usual Blender procedural-wear recipe (Bevel/AO/Pointiness nodes → bake Emit) works, but the result goes through a node graph. It doesn't fit "Claude writes code and paints".

### Gaps
- No official statement was found on whether the PyPI `bpy` wheels include Cycles GPU backends (Metal/CUDA/OptiX), or on Cycles bake timings at 4096² on Apple Silicon versus an RTX GPU.
- Not checked: Blender's Pointiness (Cycles-only, per-vertex curvature) docs, or whether Geometry Nodes can write image textures directly in 5.2/5.3.

## 3. GPU array computing from Python on Apple Silicon and NVIDIA (Python 3.14 wheels)

### Takeaway
As of October 2026, three things run on the GPU on both machines with Python 3.14 wheels:
- **PyTorch 2.14** (MPS on the Mac, CUDA on the PC). It's already a dependency on the PC.
- **WebGPU via wgpu-py 0.32** (Metal on the Mac; Vulkan/DX12 on the PC).
- **SlangPy 0.43** (Metal on the Mac; CUDA/D3D12/Vulkan on the PC).

Dr.Jit 1.5 also JITs to Metal or CUDA. MLX 0.32 is the strongest Mac-only option: Metal, with a custom-kernel API. Its CUDA backend is documented for Linux only. NVIDIA Warp, CuPy and nvdiffrast are CUDA-only (Warp and CuPy are CPU-only or absent on the Mac). nvdiffrast is also research/evaluation-only. Taichi has no Python 3.14 wheels; JAX has no GPU on the Mac and no native GPU on Windows. In a local test, one fused Metal kernel ran the tool's own fbm noise at 4096² in about 9 ms instead of about 2.5 s.

### Cited Findings
Latest versions and wheels as listed on PyPI on 2026-10-07 (JSON API):

| Library | Version (date) | Py 3.14 wheel | Mac GPU | Windows NVIDIA GPU | Licence | Source |
|---|---|---|---|---|---|---|
| torch | 2.14.1 (2026-09-30) | yes (cp310–cp314) | MPS | CUDA | BSD-3 (not re-checked) | [PyPI torch](https://pypi.org/project/torch/) |
| mlx | 0.32.3 (2026-09-29) | yes (cp310–cp314) | Metal | CUDA documented for Linux (`pip install mlx[cuda]`); win_amd64 wheels exist | MIT | [PyPI mlx](https://pypi.org/project/mlx/) |
| warp-lang | 1.18.0 (2026-10-05) | yes (py3) | **no** ("macOS wheels support CPU execution but not Metal acceleration") | CUDA 13.4, R580+ driver, Turing+ | Apache-2.0 | [PyPI warp-lang](https://pypi.org/project/warp-lang/) |
| wgpu (wgpu-py) | 0.32.0 (2026-07-19) | yes (py3) | Metal (via wgpu-native) | Vulkan/DX12 | BSD-2 | [PyPI wgpu](https://pypi.org/project/wgpu/) |
| slangpy | 0.43.1 (2026-07-16) | yes (cp39–cp314) | Metal (wheel tagged macOS 26 arm64; needs Xcode ≥ 16 for the Metal compiler) | CUDA, D3D12, Vulkan | not checked | [PyPI slangpy](https://pypi.org/project/slangpy/); [SlangPy docs](https://slangpy.shader-slang.org/en/latest/) |
| drjit / mitsuba | 1.5.0 / 3.9.1 (2026-08-07) | yes (cp39–cp314) | Metal JIT | CUDA JIT; LLVM on CPU | not checked | [PyPI drjit](https://pypi.org/project/drjit/) |
| cupy-cuda12x/13x | 14.2.0 (2026-08-20) | yes | **no macOS wheels** | CUDA | MIT (not re-checked) | [PyPI cupy-cuda13x](https://pypi.org/project/cupy-cuda13x/) |
| jax | 0.11.2 (2026-09-17) | yes (py3, ≥3.12) | "JAX is not supported on Mac/OSX GPU" (jax-metal last 0.1.1, Oct 2024) | Windows NVIDIA "no"; WSL2 experimental | Apache-2.0 | [JAX install](https://docs.jax.dev/en/latest/installation.html); [PyPI jax-metal](https://pypi.org/project/jax-metal/) |
| taichi | 1.7.4 (2025-07-31) | **no** (cp39–cp313 only) | Metal | CUDA | Apache-2.0 | [PyPI taichi](https://pypi.org/project/taichi/) |
| numba | 0.68.0 (2026-09-30) | yes (cp310–cp315) | CPU JIT only | CPU JIT (CUDA target separate) | BSD | [PyPI numba](https://pypi.org/project/numba/) |
| nvdiffrast | v0.4.0 (2025-12-08), not on PyPI | builds from source | **no** | CUDA only | NVIDIA Source Code License: "non-commercially" = "research or evaluation purposes only" | [GitHub release](https://github.com/NVlabs/nvdiffrast/releases); [LICENSE](https://github.com/NVlabs/nvdiffrast/blob/main/LICENSE.txt) |
| pytorch3d | 0.7.4 on PyPI (2023-05) | **no** (cp38–cp310, macOS x86 only) | — | — | BSD | [PyPI pytorch3d](https://pypi.org/project/pytorch3d/) |
| embreex | 4.4.0 (2026-04-22) | yes | CPU ray tracing (macOS arm64) | CPU (win_amd64) | not checked | [PyPI embreex](https://pypi.org/project/embreex/) |
| libigl (python) | 2.6.3 (already in the tool's venv) | yes | CPU | CPU | not checked | local `dir(igl)`: `ambient_occlusion`, `principal_curvature`, `gaussian_curvature`, `signed_distance`, `fast_winding_number`, `ray_mesh_intersect` |

- **nvdiffrast 0.4.0** "Removed the OpenGL backend -- the library now always uses a CUDA-based rasterizer"; it builds at `pip install` time — [nvdiffrast v0.4.0 release](https://github.com/NVlabs/nvdiffrast/releases/tag/v0.4.0)
- **SlangPy** is "built for portability, with support for D3D12, Vulkan, Metal, and CUDA". Requirements: "Xcode >= 16... (on macOS, the metal compiler is required for acceleration on a Metal 3.1+ capable device)"; CUDA Toolkit ≥ 11.8 on Windows/Linux — [SlangPy docs](https://slangpy.shader-slang.org/en/latest/)
- **Dr.Jit** "just-in-time (JIT) compiles this graph into fused kernels targeting GPUs, using either Metal on macOS or CUDA on other platforms. It can also target the host's CPU... via LLVM" — [PyPI drjit](https://pypi.org/project/drjit/)
- **MLX custom kernels**: `mx.fast.metal_kernel` runs a hand-written Metal kernel on MLX arrays — [MLX custom Metal kernels docs](https://ml-explore.github.io/mlx/build/html/dev/custom_metal_kernels.html). Windows CUDA builds were being added to MLX's CI in 2026 — [MLX repository mirror](https://upd.dev/ml-explore/mlx) (via search summary; not an official release statement)
- **Local measurement, the tool's fbm noise** (`tool.noise.fbm`, 5 octaves, value noise, uint32 hash), 2048² = 4.19 M points:
  - numpy: 587 ms
  - MLX eager: 411 ms; MLX `mx.compile`: 81 ms
  - PyTorch MPS eager: 376 ms

  MLX and PyTorch outputs were **bit-identical** to numpy (max |diff| = 0.0) — [local measurement, bench.py](file:///private/tmp/claude-501/-Users-fcarbo-Developer-personal-tm-skin-creator/8edfddd8-8d18-417e-b745-274b5d893c1c/scratchpad/bench.py)
- **Local measurement, 4096² = 16.8 M points**:
  - numpy fbm: 2.42–2.52 s
  - MLX `mx.compile`: 316 ms (7.7×), but MLX's peak memory was **5.8 GB**
  - PyTorch MPS eager: 1.52 s
  - **One fused Metal kernel** (`mx.fast.metal_kernel`, same hash and maths): **8.9 ms (about 280×), peak 336 MB** (input plus output only); max |diff| vs numpy 1.5e-6 (float rounding, so not bit-identical)

  — [local measurement, bench2.py/bench3.py](file:///private/tmp/claude-501/-Users-fcarbo-Developer-personal-tm-skin-creator/8edfddd8-8d18-417e-b745-274b5d893c1c/scratchpad/bench3.py)
- **Local measurement, Worley F1** (27 neighbours) at 2048²: numpy 1,552 ms; MLX eager 617 ms (2.5×) — [local measurement, bench.py](file:///private/tmp/claude-501/-Users-fcarbo-Developer-personal-tm-skin-creator/8edfddd8-8d18-417e-b745-274b5d893c1c/scratchpad/bench.py)
- **Local measurement, Gaussian blur** σ = 6 px on an RGBA float32 2048² image: `scipy.ndimage.gaussian_filter` 287 ms; PyTorch MPS separable conv 9.0 ms (about 32×); MLX conv2d 59 ms — [local measurement, bench.py](file:///private/tmp/claude-501/-Users-fcarbo-Developer-personal-tm-skin-creator/8edfddd8-8d18-417e-b745-274b5d893c1c/scratchpad/bench.py)
- **PyTorch on the PC**: the tool's PC side already uses torch with CUDA (`tool/pictures.py` loads a Flux2 Klein pipeline with `dtype=torch.bfloat16, device_map="cuda"`) — local code read, `tool/pictures.py` lines 97/117

### Inferences
- The big speed-up comes from **fusion**, not from "being on the GPU". Array-at-a-time GPU code (MLX eager, PyTorch eager) was only about 1.4–1.6× faster than numpy on noise. The arithmetic is cheap and the time goes into writing and reading dozens of temporaries. One fused kernel per pattern removes those temporaries, and that is what cuts memory from GBs to MBs. That matters more on a 16 GB Mac than raw speed does.
- To write a kernel once and run it on both machines, there are two good choices:
  - **SlangPy**: one Slang source, Metal on the Mac and CUDA or D3D12 on the PC, Python 3.14 wheels. Its macOS wheel is tagged macOS 26, and it needs Xcode ≥ 16 on the Mac.
  - **wgpu-py**: WGSL compute shaders, Metal/DX12/Vulkan, a pure-py3 wheel, BSD-2.

  Dr.Jit is a third option, tracing Python code into Metal/CUDA kernels. MLX custom kernels are Mac-only in practice; the PC could keep numpy, since it's already fast there.
- PyTorch is the simplest choice for blurs, convolutions, resampling and other dense image filters on both machines: MPS on the Mac, CUDA on the PC, already installed on the PC. Its eager elementwise noise is slow, though.
- nvdiffrast, PyTorch3D, Warp (GPU), CuPy and JAX are ruled out for a two-machine tool whose design machine is a Mac. nvdiffrast is also licensed for research/evaluation only.
- **The self-test**: the GPU path matches numpy exactly only if it does the same float32 operations in the same order (eager MLX/PyTorch did). A fused kernel with FMA or different evaluation order drifts by about 1e-6, which can flip an occasional 8-bit texel. That would break the rule "every car's game files stay identical, byte for byte" unless the change re-baselines once and says so in the commit.

### Gaps
- No published benchmark of 4096² texture synthesis on Apple Silicon GPUs versus an RTX GPU was found. The figures above are one local run on an M5 under memory pressure. The PC wasn't measured.
- MLX's Windows CUDA status isn't confirmed by official docs. SlangPy and Dr.Jit licences weren't checked.

## 4. Standard techniques: mesh-map baking, curvature/AO wear, triplanar, stochastic tiling, padding, anti-aliased masks

### Takeaway
Pros drive "smart" wear from a small set of baked mesh maps (curvature, AO, position, world-space normal, thickness), combined with noise or grunge. Substance's Metal Edge Wear generator, for example, needs position, curvature, AO and world-space normal, with "curvature weight" and "AO masking" sliders. Tiling photo textures uses triplanar projection plus stochastic hex tiling (Mikkelsen 2022, now a MaterialX node). Export pads UV islands by dilation so mipmaps don't bleed. Crisp, resolution-independent mask edges come from signed distance fields.

### Cited Findings
- **Substance's mesh-map bakers**: Curvature, Position, Thickness, World Space Normals, Ambient Occlusion, AO from Mesh, Bent Normals and others. The curvature baker "contains cavities and edges information... black values representing concave areas, white values representing convex areas, and gray values representing neutral areas". AO from mesh "is slower than the base ambient occlusion baker but produces more accurate results" — [Substance 3D bakers settings](https://helpx.adobe.com/substance-3d-bake/bakers-settings.html); [Curvature baker](https://helpx.adobe.com/substance-3d-bake/bakers-settings/curvature.html); [AO from mesh](https://helpx.adobe.com/substance-3d-bake/bakers-settings/ambient-occlusion-from-mesh.html)
- **Metal Edge Wear generator**: "creates the appearance of damage and wear on areas of your mesh that are most likely to be knocked or scratched". It needs "Baked position, curvature, ambient occlusion, and world space normal maps". "Curvature Weight" sets how far curvature defines the edges (too low leaves only grunge). "Ambient Occlusion Masking... prevent[s] occluded areas from receiving the weathering effect". There are Edges Smoothness and curvature modes Standard/Sobel/Smooth — [Experience League, Metal Edge Wear](https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/effects/generators/metal-edge-wear)
- **Padding/dilation**: "Padding (sometimes also called dilation) is a process that happens after the generation of a texture. Its purpose is to dilate the borders of the UV islands to fill empty areas with similar pixels". Painter offers infinite dilation ("a pixel will be stretched until it reaches another UV island or the borders of the texture"), dilation + transparent, and dilation + background colour. Good padding is important "to ensure good mipmaps generation" — [Experience League, Texture dilation or padding](https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/technical-support/workflow-issues/export-issues/texture-dilation-or-padding); [Export settings](https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/export/export-window/export-settings). Blender's equivalent margin modes are Extend and Adjacent Faces (§2).
- **Stochastic tiling**: Heitz & Neyret's by-example noise uses a histogram-preserving blending operator — [Heitz research page](https://eheitzresearch.wordpress.com/722-2/). Mikkelsen's "Practical Real-Time Hex-Tiling" (JCGT 11(2), 2022) samples each hexagon at a random offset and "replaces expensive histogram preservation with a highly efficient contrast ramp" — [JCGT paper](https://jcgt.org/published/0011/03/05/). MaterialX 1.39.4 added "hex-tiled images" (§1).
- **Texture bombing** (scattering decorations or cells over a surface procedurally) — [GPU Gems ch. 20, Texture Bombing](https://developer.nvidia.com/gpugems/gpugems/part-iii-materials/chapter-20-texture-bombing). **Triplanar projection** (blending three axis-aligned projections by the normal) as used for procedural terrain — [GPU Gems 3 ch. 1](https://developer.nvidia.com/gpugems/gpugems3/part-i-geometry/chapter-1-generating-complex-procedural-terrains-using-gpu)
- **SDF edges**: Valve's method stores a low-resolution signed distance field and thresholds it at render time for sharp, scalable, anti-aliased edges — [Green 2007, Improved Alpha-Tested Magnification (SIGGRAPH)](https://steamcdn-a.akamaihd.net/apps/valve/2007/SIGGRAPH2007_AlphaTestedMagnification.pdf). Inigo Quilez covers filtering procedural patterns analytically to avoid aliasing — [iquilezles.org, filtering](https://iquilezles.org/articles/filtering/)

### Inferences
- The tool's wear (`tool/wear.py`) uses heuristics: faces turned forward, height off the ground, sun-facing. The industry standard adds **curvature** (convex edges chip) and **AO** (crevices collect dirt; occluded areas are spared wear). Both are once-per-mesh bakes that fit the existing cached-bake pattern.
- On a low-poly game mesh, per-vertex curvature is coarse. A texel-level curvature computed from the baked normals across neighbouring texels (Substance's "Sobel" idea) would follow panel edges better. Either way it is computed once and cached.
- The tool deliberately makes hard one-texel cuts for wear (per the `wear.py` docstring). An SDF-based mask (distance to the cut, thresholded with about 1 texel of smoothing) keeps the look crisp while removing stair-stepping. That is a quality choice for the user's eye, not a rule.

### Gaps
- There's no published numeric recipe for Metal Edge Wear's internals: weights, how curvature and grunge are blended. Only the parameter descriptions are public.
- No source was fetched on Blender's "Pointiness" or on curvature from normal maps.

## 5. Free PBR material sources in 2026 and licences

### Takeaway
ambientCG (which the tool already uses) and Poly Haven are both CC0, free, need no attribution, and have public APIs. ShareTextures, cgbookcase and 3DTextures.me add more CC0 sets. FreePBR isn't CC0 for commercial use.

### Cited Findings
- **ambientCG**: CC0 1.0 Universal; "You can copy, modify, distribute and perform the assets, even for commercial purposes, all without asking permission"; attribution optional; API v1/v2/v3 with endpoints such as `/assets` — [ambientCG license docs](https://docs.ambientcg.com/license/)
- **Poly Haven**: CC0; "You can use our assets for any purpose, including commercial work"; "You do not need to give credit"; redistribution allowed. Logos and example renders are protected by its ToS — [Poly Haven license](https://polyhaven.com/license)
- **Counts and others**: Poly Haven has over 780 textures (and over 980 HDRIs); ambientCG over 2,000 materials. "Both public domain... both with free no-key APIs". 3DTextures.me, ShareTextures and cgbookcase are also CC0. FreePBR "is NOT CC0", with commercial use needing a one-time payment — [Cinevva guide, 2026](https://app.cinevva.com/guides/free-textures-hdris-materials) (aggregator; counts unverified at source)

### Inferences
- The tool's licence position is already clean, since CC0 sources need no credit, unlike the car model's CC-BY. Poly Haven is the natural second source for surfaces ambientCG lacks; its scans tend to be higher-fidelity.

### Gaps
- Exact current asset counts weren't checked at the primary sites.

## 6. How others keep such an engine small (node graphs vs layers + masks vs code)

### Takeaway
Pros keep texturing manageable with one model: **layers + masks** (fill layer = material; mask = generator built from mesh maps + noise). The graphs are serialised as node documents (.sbs/.sbsar, MaterialX .mtlx, Material Maker .ptex). For a tool whose author is Claude writing code, the closest equivalent is a few small primitives (bake maps → masks → layered finishes), with the graph living in Python. A second representation adds weight without saving any.

### Cited Findings
- Substance's generators are mask builders over baked maps. Metal Edge Wear outputs "a monochrome... texture... useful for generating masks to add edge wear details to a layer" — [Experience League, Metal Edge Wear](https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/effects/generators/metal-edge-wear)
- MaterialX documents materials as node graphs and generates shader code for GLSL/MSL/OSL/MDL/Slang from one description. It ships a TextureBaker that turns graphs into textures (§1) — [PyPI MaterialX](https://pypi.org/project/MaterialX/); [OpenPBR spec](https://academysoftwarefoundation.github.io/OpenPBR/)
- Material Maker uses visual node graphs exported through templates to engines, with a CLI for batch export — [CG Channel](https://www.cgchannel.com/2026/01/check-out-free-material-authoring-software-material-maker-1-5/)
- **The tool's own size, by local `wc -l`**: the engine core is small. `bake.py` 37 lines, `raster.py` 109, `noise.py` 102, `coverage.py` 184, `wear.py` 119, `relief.py` 262, `textures.py` 263, `looks.py` 631, `finishes.py` 388. The bulk of the 17,452 lines is elsewhere: `tyres.py` 1,236, `paintbox.py` 1,139, `course.py` 943, `marks.py` 794, `meshlines.py` 739, `checks.py` 697 — local repository read

### Inferences
- The premise "much of the code re-implements rasterising, baking, noise and masks" doesn't hold. Rasterising, baking and noise together are about 250 lines, and coverage another 184. Swapping them for an engine would save little code and add a dependency. The size is in tyres, the paint box, the course, marks and mesh lines, which are domain logic no engine provides.
- What keeps an engine small is a fixed set of mask inputs: the mesh maps (position, normal, curvature, AO, thickness, part ID), plus noise, plus SDF edges. Every finish then composes from those instead of carrying its own heuristics. That is the Substance model, with no Substance in it.

### Gaps
- No source was found comparing maintenance cost of code-defined versus graph-defined material libraries.

## 7. Performance: what's realistic for 4096² multi-map painting on Apple Silicon, and memory tips

### Takeaway
At 4096², one float32 channel is 64 MiB and one cached 4096² bake loads about 496 MiB into RAM. A whole-car paint holds several of those at once, which explains 20 s–17 min on a 16 GB Mac that is already swapping. The cheapest wins:
- stop materialising temporaries: fused GPU kernels, or chunking the covered texels;
- keep everything in float32/float16/uint8;
- store caches as `.npy`, so they can be memory-mapped;
- compute only on covered texels (60–71% of the canvas).

### Cited Findings
- **Bake cache size, local measurement**: `bake2_Details_4096x4096.npz` is 202 MiB on disk and 496 MiB in RAM:
  - tri: int32, 64 MiB
  - position: float32 × 3, 192 MiB
  - normal: float32 × 3, 192 MiB
  - count: int16, 32 MiB
  - sides: uint8, 16 MiB

  — local read of the work folder cache
- **Covered texels, local measurement**: 60.5% of the Skin canvas and 70.9% of the Details canvas at 4096² — local read of the bake caches
- **`.npz` can't be memory-mapped, local test with numpy 2.5.3**: `np.load(npz, mmap_mode="r")` returns a plain `ndarray` (fully read into RAM), while a `.npy` with `mmap_mode="r"` returns a `memmap`. The tool's `bake.py` loads with `dict(np.load(cache))` — local test; [numpy.load docs](https://numpy.org/doc/stable/reference/generated/numpy.load.html)
- **Temporaries dominate memory, local measurement**: MLX `mx.compile` fbm at 4096² peaked at 5.8 GB. A single fused Metal kernel peaked at 336 MB and was about 35× faster (316 ms → 8.9 ms). numpy fbm at 4096² took about 2.4–2.5 s per call. The machine was under memory pressure: 0.5 GB free, 2.1 GB swap used — §3 sources
- **float64 in the tool**: several modules still mention float64 (local `grep -c float64`: `course.py` 22, `marks.py` 19, `meshlines.py` 10, `relief.py` 7, `carmap.py` 6, `checks.py` 6, `view.py` 5). A float64 RGBA 4096² array is 512 MiB versus 256 MiB in float32 — local repository read; arithmetic
- Blender 5.2's Cycles texture cache "significantly reduces memory usage and startup time" at some performance cost. Production renderers make the same trade: tiled, cached textures over whole images in RAM — [5.2 Cycles notes](https://developer.blender.org/docs/release_notes/5.2/cycles/)

### Inferences
- Realistic targets on the M5 Mac:
  - per-pattern 3D noise over all covered texels: about 5–20 ms per pattern as a fused GPU kernel, versus about 1.5–2.5 s in numpy;
  - dense filters (blurs, dilation-like passes): about 10 ms on PyTorch MPS versus about 0.3 s in scipy at 2048² RGBA, scaling about 4× at 4096².

  So a paint that is mostly noise and filters could plausibly drop from about a minute to a few seconds on a good machine. The 17-minute worst case is swap thrash, which mainly needs the memory fixes. This is an inference from micro-benchmarks, not a measured whole-car paint (see Gaps).
- Memory tips, in order of payoff:
  1. Work on the packed list of covered texels (N × 3 positions) instead of full H × W canvases, and scatter back only at the end. That saves 30–40% of every intermediate.
  2. Process in chunks of about 1–2 M texels, so numpy temporaries stay around 100 MB.
  3. Save bakes and coverage as `.npy`, loaded with `mmap_mode="r"`.
  4. Keep float32 for maths, float16 for stored intermediate layers (colour and roughness need no more), and uint8 or bit-packed masks.
  5. Free per-part arrays as soon as each part is composited.

### Gaps
- Not measured: a whole-car paint profile (which steps take the minute), the PC's numbers, or float16 accuracy on the game's 8-bit DDS output. These need a profile run of the tool itself. Per RULES.md "Measure slowness before fixing it", that profile should come before any GPU port.

## Applicability to this tool

### Takeaway
**Keep the numpy engine and its own bake/raster/coverage.** They are small, cached, correct and seam-free by construction. No existing engine (Substance, Blender, Material Maker, MaterialX) fits a two-machine, Python 3.14, code-driven, 3D-on-the-bake painter at free or one-time cost. Make the speed and memory gains in place:
1. Profile one whole-car paint first.
2. Fix memory: covered texels only, chunking, `.npy` memmaps, float32/float16.
3. Move **noise** (and then the heaviest per-texel looks) to fused GPU kernels behind the same function names, with numpy kept as the reference.
4. Add **curvature/AO/thickness mesh maps** baked once per mesh, so wear and dirt follow the car the way Substance's generators do.

### Cited Findings
- See §1–§7 for the evidence behind each line below. In short:
  - Substance's automation needs Enterprise (§1).
  - bpy is pinned to Python 3.13 (§2).
  - Fused Metal noise is about 280× faster and about 17× lighter on peak memory than numpy-plus-temporaries, while eager GPU arrays are only about 1.5× faster (§3).
  - Pros drive wear from curvature + AO + position + world-normal maps (§4).
  - The bake caches cost about 0.5 GB each in RAM and can't be memory-mapped as `.npz` (§7).

### Inferences

Recommendations per piece, with effort as Claude's working time and gains as evidence supports:

| Piece | Recommendation | Why | Effort | Expected gain |
|---|---|---|---|---|
| **Bake** (`bake.py`, tri/position/normal) | **Keep** (numpy, cached). Change the cache from `.npz` to per-array `.npy` and load it memory-mapped. | Runs once per mesh. nvdiffrast is CUDA-only, research-licence, no Mac; Blender adds a Python 3.13 runtime. | 1–2 h | About 0.5 GB less resident RAM per 4096² set loaded; faster start (measured size, §7) |
| **New mesh maps** (curvature, AO, thickness, part ID) | **Add**, baked once per mesh and cached like the bake. Use libigl (already installed: `principal_curvature`, `ambient_occlusion`, `signed_distance`) or embreex rays, plus texel-level curvature from baked normals. | The industry inputs for edge wear and dirt (Metal Edge Wear needs exactly position + curvature + AO + world normal). Paid once per mesh, not per skin. | 1–2 days, shown to the user on the car before wear uses it | Quality (wear and dirt where real cars wear); no per-skin time cost |
| **Raster** (`raster.py`) | **Keep**. | 109 lines, used only by the bake and preview; cached. | — | — |
| **Coverage** (`coverage.py`) | **Keep**; optionally store a signed distance to each part's edge (scipy `distance_transform_edt`, once, cached) for anti-aliased part edges. | Sparse cache already avoids repeated rasterising; SDF edges are the standard for crisp AA masks (Valve 2007). | 0.5–1 day for SDF edges | Quality at part boundaries; no repeated cost |
| **Noise** (`noise.py`: value/fbm/worley/cell_id) | **Move to GPU** as fused kernels behind the same API, numpy kept as the reference/fallback. Two options: (a) **MLX `metal_kernel`** on the Mac with numpy on the PC (smallest; Mac-only); (b) **SlangPy or wgpu-py**, one kernel source for Metal (Mac) and CUDA/DX12 (PC). Avoid eager MLX/PyTorch for noise. | Measured: fbm at 4096² takes 2.4–2.5 s in numpy, 0.32 s in compiled MLX (5.8 GB peak), **8.9 ms as a fused Metal kernel (336 MB peak)**. Eager GPU is only about 1.5× faster. | (a) 0.5–1 day; (b) 1–3 days incl. both machines | Noise about 100–280× faster; peak memory GBs → hundreds of MB (local measurement). Self-test: fused kernels differ by about 1e-6, so expect a one-time re-baseline of the game files, declared in the commit |
| **Looks** (72 finishes, `looks.py`/`finishes.py`) | **Keep as code.** Speed comes for free once noise and filters are fast. Port only the heaviest finishes to kernels after profiling. Use OpenPBR/MaterialX names as vocabulary only. | Code is the tool's graph language. A MaterialX/Material Maker graph would add a second representation, and its UV-space bakers don't do 3D-on-the-bake natively (unverified). | Profiling 0.5 day; per-finish ports as needed | Unknown until profiled |
| **Filters** (blurs, dilation, padding, soft masks) | **Move dense image filters to PyTorch** (MPS on the Mac, CUDA on the PC; torch is already on the PC), numpy/scipy as fallback. | Measured: Gaussian blur on RGBA 2048² takes 287 ms in scipy vs 9 ms on MPS (about 32×). | 0.5–1 day | About 30× on filters (local measurement) |
| **Wear** (`wear.py`: fade, chips, scrapes, clear coat) | **Keep the approach**, but drive chips by curvature (convex edges), keep occluded areas clean by AO, and put dirt and grime in AO crevices, alongside the existing direction/height cues and 3D noise. Keep hard edges, anti-aliased by SDF threshold. | That is how Substance's Metal Edge Wear and dirt generators work. | 1 day after the mesh maps exist | Quality (wear lands where cars really wear) |
| **Relief** (`relief.py`, heights → Details normal map via 3D derivatives) | **Keep.** Optionally GPU-evaluate the height functions with the same kernels as noise. | Already precise across seams and mirrored twins; the cost is mostly evaluating the height function 3× per texel (texel + du + dv), the same pattern as noise. | Follows the noise port | Proportional to noise gains |
| **Textures** (ambientCG photo materials) | **Keep.** Add Poly Haven (CC0, API) as a second source. Use triplanar on the bake plus Mikkelsen hex tiling against repetition. Cache decoded textures as uint8/float16 `.npy` memmaps. | Both CC0, no attribution; hex tiling is the 2022 standard and is in MaterialX 1.39.4. | 0.5–1 day each | Quality (less visible repetition); lower RAM |
| **Export padding** | Use **infinite dilation** (Substance's default idea) or Blender-style "adjacent faces" for every map before DDS mipmaps, if not already done. | Needed for clean mipmaps. | Hours (scipy distance transform with nearest-index fill) | Quality at distance/mips |
| **Engines** | **Don't adopt.** Substance: subscription ($24.99/month) or Steam $199.99 per yearly edition, and **no** automation without Enterprise SAT. Blender `bpy`: Python 3.13-only, a second runtime on both machines, nothing the in-process route can't do. Material Maker (MIT, CLI): 2D graphs, no 3D-on-the-bake. nvdiffrast: CUDA-only and research-only. | §1–§3 | — | — |

- **Order of work** (each step shown before the next, per RULES.md):
  1. Profile one whole-car paint on the Mac and the PC.
  2. Memory fixes (`.npy` memmaps, float32/float16, covered-texel chunks), which are byte-identical by design.
  3. GPU noise behind the existing API, with one declared re-baseline.
  4. PyTorch filters.
  5. Mesh maps.
  6. Curvature/AO-driven wear, shown close up.
- **Cost of a GPU path**: the Mac needs MLX (MIT, Python 3.14 wheels) or SlangPy (needs Xcode ≥ 16 installed). The PC already has torch and CUDA. No subscriptions.

### Gaps
- No whole-car paint profile was run, so the share of time in noise versus looks versus I/O is unknown. The 7–280× gains apply only to the parts that are noise or filters.
- PC (RTX) numbers weren't measured.
- It is unverified whether MaterialX's TextureBaker or SlangPy's licence would raise any issue, and whether float16 storage changes any 8-bit DDS texel.
