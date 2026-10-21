# Paid 3D texturing and mesh tools Claude could drive automatically (October 2026)

Scope: tools that Claude (shell plus Python on the user's Apple Silicon Mac and NVIDIA Windows PC) could run end to end: load the CarSport FBX with its UVs, build layers, masks and fills, paint a stroke or path along given 3D points, place a decal, apply smart materials or generators, bake mesh maps and export textures. The yardstick is the mechanics behind the user's complaints (tapes with gaps and steps, lettering on curves, decals on curved panels), compared with the home-made numpy painter that paints per texel from a bake (texel to 3D position and normal). Sibling notes already cover Substance's Enterprise-only command-line tools (`texturing_engines_and_speed.md` §1) and the Path and Ribbon tools as design practice (`livery_design_practice.md`, `mesh_lines_and_curves.md`). This note is about what can be **scripted**.

## 1. Substance 3D Painter: Steam edition vs subscription, what the Python API can do, paths, headless use

### Takeaway
Painter's Python API (0.3.x, documented for Painter 12.x, last updated September 2026) can script nearly everything *except painting*: creating a project from a mesh, fill, paint and group layers, masks, anchor points, smart materials, smart masks, generators, 3D projections (planar, triplanar, warp), baking and export. But "Strokes are not accessible from the Python API", and nothing in the API or in the third-party MCP servers creates Path or Ribbon strokes. So the tool that would fix tapes and lettering (Path/Ribbon) can't be driven by Claude. Remote control needs the GUI app running (`--enable-remote-scripting`, HTTP on port 60041); no headless flag is documented. The Steam perpetual edition ($199.99, updates until March 2027, Windows, macOS and Linux) appears to have the same application features, scripting presumably included, but no source states that outright.

### Cited Findings
**Licensing and editions**
- Substance 3D Painter 2026 on Steam is $199.99. The standalone perpetual version gets "free feature updates until March 2027. After that date, you will get to keep this version". Platforms listed: Windows, macOS and SteamOS + Linux. A Substance Indie monthly subscription option is shown at $24.99/month (**subscription**). — [gg.deals listing for Substance 3D Painter 2026](https://gg.deals/application/substance-3d-painter-2026/)
- The 2025 Steam page (now "no longer available") lists Windows, macOS and SteamOS + Linux. Unmetered Substance 3D Assets and generative AI features "are not included in the Steam version". macOS needs Apple M1 or later; the Windows minimum is an RTX 2060 Super / RX 5700 XT with 16 GB RAM. — [Steam: Substance 3D Painter 2025](https://store.steampowered.com/app/3366290/?cc=us)
- Adobe community manager (2025-01-16): the Steam licence is "a one time payment for lifetime access, but updates of the year of purchasing only". Steam lacks "Send to" and the Substance 3D Assets library, but "There's no downside in the application as properly said". — [Adobe community: Steam vs standard](https://community.adobe.com/t5/substance-3d-painter-discussions/steam-vs-standard-substance-painter-differences-and-payment/m-p/15093709/highlight/true)
- A *user* (not Adobe staff, 2021-09-07) describes the Steam purchase as a perpetual "Indie License" with "Revenue under $100K", and says Adobe support chat gave "no clear information". — [Adobe community thread 629574](https://community.adobe.com/questions-59/substance-painter-3d-on-steam-what-type-of-licence-is-there-indie-pro-629574)

**Remote control (how Claude would drive it)**
- "Substance 3D Painter supports remote control with scripting to execute JavaScript or Python commands." It needs the launch flag `"Adobe Substance 3D painter.exe" --enable-remote-scripting`, and "Make sure the application is up and running with this command before running any scripts". A helper `lib_remote.py` talks HTTP to port 60041. Returned Python objects must be converted to strings or JSON. — [Adobe: Remote control with scripting](https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/scripting-and-development/scripts-and-plugins/remote-control-with-scripting)
- The developer tutorial titled "Remote control / headless" (last updated 2026-07-09) documents only `--enable-remote-scripting` and calls like `Remote.execScript("import substance_painter", "python")`. It documents no `--headless` or no-UI flag. — [Adobe dev docs: Remote control / headless](https://experienceleague.adobe.com/en/docs/substance-3d-dev/painter-python/tutorials/remote-control)

**What the `substance_painter` API covers**
- Modules: application, async_utils, baking, colormanagement, display, event, exception, export, js, layerstack, logging, project, properties, resource, source, textureset, ui. The page is titled "Python API 0.3.5" and was last updated 2026-09-17. — [Adobe: API overview](https://experienceleague.adobe.com/en/docs/substance-3d-dev/painter-python/api/api-overview)
- Changelog: 0.3.6 (Painter 12.0.2) added `project.AutoUnwrapUVTilesSettings`. 0.3.7 (Painter 12.1.0) added `GeometryMaskMeshParams`, `GeometryMaskUVTilesParams` and `LayerNode.get/set_geometry_mask()`. Note the conflict: the overview page is titled 0.3.5 while the changelog lists 0.3.7. — [Adobe: API overview / changelog (search snippet)](https://experienceleague.adobe.com/en/docs/substance-3d-dev/painter-python/api/api-overview)
- Project creation from a mesh: `substance_painter.project.create(mesh_file_path=..., settings=...)`. The module opens, creates, saves and closes projects. — [Adobe: project module](https://experienceleague.adobe.com/en/docs/substance-3d-dev/painter-python/api/substancepainter-package/project)
- Layer-stack editing functions: `insert_paint`, `insert_fill`, `insert_generator_effect`, `insert_filter_effect`, `insert_levels_effect`, `insert_compare_mask_effect`, `insert_color_selection_effect`, `insert_group`, `instantiate`, `insert_anchor_point_effect`, `insert_smart_mask`, `insert_smart_material`, `delete_node`, `add_mask`, `set_material_source`. `ScopedModification` groups edits into one undo entry (updated 2026-09-17). — [Adobe: layerstack edition](https://experienceleague.adobe.com/en/docs/substance-3d-dev/painter-python/api/substancepainter-package/layerstack-module/edition)
- **Paint layers: "Strokes are not accessible from the Python API."** A paint node exposes only naming, blending and selection (updated 2026-09-17). — [Adobe: Paint layer and effect](https://experienceleague.adobe.com/en/docs/substance-3d-dev/painter-python/api/substancepainter-package/layerstack-module/layers-and-effects/paint)
- Fill layers can be positioned in 3D from a script: `set_projection_mode()` with `ProjectionMode.Fill`, `UV`, `Triplanar`, `Planar`, `Spherical`, `Cylindrical`, `Warp` and `UVSetToUVSet`. `set_projection_parameters()` takes `Projection3DParams` (offset, rotation, scale) and `ProjectionCullingParams` (depth and backface culling). `set_source()` takes a resource, a colour or an anchor point. — [Adobe: Fill layer and effect](https://experienceleague.adobe.com/en/docs/substance-3d-dev/painter-python/api/substancepainter-package/layerstack-module/layers-and-effects/fill)
- Baking: `BakingParameters`, `bake_async(texture_set)`, `bake_selected_textures_async()`, `CurvatureMethod.FromMesh/FromNormalMap`, and mesh-map usages including Normal, WorldSpaceNormal, ID, AO, Curvature, Position and Thickness. — [Adobe: baking module](https://experienceleague.adobe.com/en/docs/substance-3d-dev/painter-python/api/substancepainter-package/baking)
- Export: the export module "is the scripting equivalent of the 'Export textures' window" (`export_project_textures`). — [Adobe: export module](https://helpx.adobe.com/substance-3d-painter-python/api/substance-painter/export.html)
- Path tools are interactive: "Points can be placed by clicking on the surface of the 3D model within the 3D viewport. At least two points... are needed to create a path." — [Adobe: Path tool overview](https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/painting/path-tools/path)

**Real automation built on it (MCP servers Claude Code could use)**
- "MCP Pro for Painter": "$15 USD — one-time. Lifetime updates." Windows, macOS and Linux; needs Painter 11.0+, verified on 12.0.3 / API 0.3.5. It connects through `--enable-remote-scripting`. It has 179 tools across 33 modules: layer stacks, masks, smart materials, channels, baking, export presets, texture sets, symmetry, QA and undo. It **does not paint strokes or create paths**. — [itch.io: MCP Pro for Painter](https://y1uda.itch.io/painter-mcp-pro)
- Open-source `substance-painter-mcp`: it bakes mesh maps, stacks smart materials and tunes generator parameters. It needs "no launch flags and no --enable-remote-scripting", was developed against Painter 12.1.1 / API 0.3.5, and runs on Windows, macOS and Linux. — [glama.ai: substance-painter-mcp](https://glama.ai/mcp/servers/rx8ezffjo7)
- Other adapters: `dcc-mcp-substance3d-painter` on PyPI, and `elliezu/SubstancePainterMCP` packaged as a Claude Code skill. — [PyPI: dcc-mcp-substance3d-painter](https://pypi.org/project/dcc-mcp-substance3d-painter/); [GitHub: elliezu/SubstancePainterMCP](https://github.com/elliezu/SubstancePainterMCP)

### Inferences
- Claude could drive Painter end to end for *finishes*: project from the CarSport FBX, fills with smart materials, generator-driven edge wear from baked curvature/AO/position, planar-projected decals and export. That's possible on both Mac and PC with the app window open. It **can't** create the Path/Ribbon strokes that solve tapes and lettering without a person clicking in the viewport. The only workaround is clicking the viewport by screen coordinates (computer use), which is fragile: camera-dependent, with no API to read the path back. Ruled out for production.
- A tape "drawn" by Painter from a script would really be a mask image the home-made tool computes and Painter merely composites. That gives no gain on the gap and step mechanics.
- A planar-projected decal in Painter is the same maths the home-made painter can do per texel: project along a direction, cull by normal. It isn't a mechanical leap for decals on curved panels.
- The Steam edition very likely runs the same Python API, since Adobe says "no downside in the application" and the MCP tools list no Steam exclusion. Confirm on purchase.

### Gaps
- No Adobe page explicitly confirms that the Steam edition includes Python scripting and remote scripting. No source on whether one Steam purchase installs on both Mac and PC (Steam normally allows it for multi-platform apps, but unverified for this title). No official statement of the Steam edition's revenue cap; only a 2021 user post.
- Couldn't confirm whether Painter's export can write DDS with legacy D3D9 headers. The home-made exporter would stay either way.
- The macOS launch syntax for `--enable-remote-scripting` isn't documented (only the Windows `.exe` form). Likely `open -a … --args …`, unverified.
- No sign in the API docs or release notes that a future API version will expose paths or strokes.

## 2. 3DCoat 2026 (Pilgway): one-time licence, Python / Core API

### Takeaway
3DCoat 2026 costs €379 perpetual for individuals, with **subscription** (€20.80/month) and rent-to-own options. 3DCoatTextura (the texturing-only edition) is €159. It has an embedded Python API and a C++ Core API that "trigger UI commands, operate over the scene, and create new tools", but the documentation shows no function to paint a stroke along given points, place a decal, bake or export from a script. No headless mode is documented. It's the weakest case for automation.

### Cited Findings
- 3DCoat 2026 was declared production-ready with 3DCoat 2026.11 after a June 2026 public beta. Main additions are a "new GPU-accelerated node-based texturing system" and "30 material channels". Platforms are "Windows 7+, Ubuntu 20.04+ and macOS 10.13+". — [CG Channel, 2026-07-23](https://www.cgchannel.com/2026/07/pilgway-releases-3dcoat-2026-and-3dcoattextura-2026/)
- Prices (2026): individual perpetual €379; **subscription** €20.80/month or €169.85/year; rent-to-own €41.60/month × 11. Studio node-locked €539, floating €579. 3DCoatTextura individual perpetual €159 (up from €119), **subscription** €10.80/month. — [CG Channel, 2026-07-23](https://www.cgchannel.com/2026/07/pilgway-releases-3dcoat-2026-and-3dcoattextura-2026/)
- The Python API "is intended to trigger UI commands, operate over the scene, and create new tools" and is "very similar to the C++ Core API". Scripts are made via Scripts → Create Python Script, and output appears in Extensions → Show Python Console. — [3DCoat docs: Python API](https://3dcoat.com/documentation/?p=6212)
- Documented classes: `coat.io`, `coat.dialog`, `coat.Mesh`, `coat.Model`, `coat.uv`, `coat.Scene`, `coat.SceneElement`, `coat.Volume`, `coat.ui`, plus maths types. The fetched index documents no Paint-room stroke, decal or bake functions. — [Pilgway: 3DCoat Python API index](https://pilgway.com/files/3dcoat/PythonAPI/index.html)
- Paint layers *are* scriptable in the older scripting docs: add, rename and select layers, visibility, opacity. — [3DCoat scripting: paint layers](https://3dcoat.com/files/scriptdocs/A2DPaintLayers.html)
- Licence: the same serial may be installed on two computers if used at alternate times, and serials work on Windows, macOS or Linux. — [Pilgway licensing (search snippet)](https://pilgway.com/licensing/5)

### Inferences
- 3DCoat's automation is aimed at modelling, retopology and UI macros. Driving texture painting along 3D points would mean triggering UI tools by simulated input, which isn't reliable.

### Gaps
- The embedded Python version conflicts between sources: a docs snippet says 3.8.10, the API index says 3.11.9.
- No source on a command-line or headless mode, scripted baking, scripted export, or native Apple Silicon builds.

## 3. Marmoset Toolbag 5: Python `mset` API, texture projects, baking

### Takeaway
Toolbag 5 is **$399 perpetual** (all 5.x updates) or a **subscription** at $18.99/month, and runs natively on Apple M-series Macs and Windows. Its Python API is the most complete after Painter's for a texture project: import a model, create a texture project, add Paint, Vector, Fill, **Decal** and procedural layers (Curvature, Occlusion, Dirt, Scratch and others), set input maps, position a **projector** (position, rotation, scale, edge fade, normal weight), bake, export, and `quit()`. A script can run from the command line at launch. But there is no call to paint a stroke or draw a vector shape at given coordinates; only `importStroke(filename)` of an undocumented stroke file.

### Cited Findings
- Perpetual licence $399 (individual) or $1,299 (studio). **Subscriptions** $18.99/month (individual) or $49.99/month (studio). "Perpetual licenses require a one-time fee which grants indefinite access to version 5, with all version 5.x updates included free of charge." — [Marmoset shop (search snippet)](https://marmoset.co/shop)
- The API reference is "Build: 5.03". `importModel(filePath)`, `newScene()`, `loadScene()`, `saveScene()`, `bakeAll()` and `quit(returnCode=0)` ("Quits the application"). — [Marmoset: Module mset (Toolbag 5)](https://marmoset.co/python/reference5.html)
- On `TextureProjectObject`, `addLayer(layerType)` accepts 'Paint', 'Vector', 'Fill', 'Decal', 'Blur', 'Curves', 'Gradient Map', 'Hue / Saturation', 'Invert', 'Levels', 'Sharpen', 'Recolor', 'Color Selection', 'Curvature', 'Direction', 'Dirt', 'Height', 'Occlusion', 'Scratch', 'Thickness', 'Cellular', 'Checkered', 'Clouds', 'Gradient', 'Perlin', 'Tiles', 'Turbulence' and 'Voronoi'. Also `setInputMap(name, tex)`, `addOutputMap(...)`, `exportOutputMap(index)` and `exportAllOutputMaps()`. — [Marmoset: Module mset (Toolbag 5)](https://marmoset.co/python/reference5.html)
- `TextureProjectLayerDecal` has `material` and `projection`. The `Projector` type has `projectionMethod`, `tiling`, `clamp`, `uvRotation`, `edgeFade`, `normalWeight`, `position`, `scale`, `rotation` and `transform`. Every layer has `importStroke(filename: str)` and `clearContent()`. `TextureProjectLayerVector` has no documented members. — [Marmoset: Module mset (Toolbag 5)](https://marmoset.co/python/reference5.html)
- Baker scripting: `BakerObject` with `importModel()`, `addGroup()`, `loadPreset()`/`savePreset()`, `setTextureSetWidth/Height()`, `getAllMaps()`, `bake()` and the `outputPath`, `outputSamples` and `edgePadding` properties. — [Marmoset: Module mset (Toolbag 5)](https://marmoset.co/python/reference5.html)
- Scripts can start automatically "by including it in your command line arguments" (forum answer). — [Polycount thread](https://polycount.com/discussion/comment/2715498)
- macOS minimum is macOS 13.5 with Metal 3; Apple "M" series is recommended. — [Marmoset docs: System requirements](https://docs.marmoset.co/docs/system-requirements/)
- The docs index lists "Starting a Free Trial". — [Marmoset docs](https://docs.marmoset.co/docs/python-scripting/)

### Inferences
- Toolbag could take over decal placement (a projector with edge fade and normal weight on curved panels), curvature and occlusion-driven wear layers, and baking, all from a launch-time script that quits when done (a window flashes open). Tapes and lettering along 3D paths still aren't scriptable. `importStroke` might be a back door if the stroke file format can be written, but it's undocumented.
- 'Curves' in the layer list is a tonal-curve adjustment (it sits among Levels and Hue/Saturation), not a path along the surface.

### Gaps
- The stroke file format behind `importStroke` is undocumented, so it's unknown whether Claude could write strokes from 3D points.
- No official page found for command-line arguments or a no-window mode; only the forum answer.
- Licence seat count across two machines and DDS export options weren't found.

## 4. InstaMAT (Abstract): pricing, APIs, headless graphs

### Takeaway
InstaMAT Studio is **free** under the "Pioneer License" for individuals or businesses under $100k annual revenue, with attribution required for commercial use. Paid options are **subscriptions** (Indie $8/month billed annually) or perpetual Indie $489 with 2 years of updates. It runs on Windows, macOS and Linux. Headless automation is through InstaMAT Pipeline (command-line execution of Element Graphs) and a C++ SDK. No evidence was found of scripted painting along 3D points.

### Cited Findings
- "Free and unrestricted access to InstaMAT Studio, without any features cut or limited" via the Pioneer License (annual revenue under $100,000; attribution required for commercial use). **Subscriptions**: Indie $8/month billed annually (revenue under $250,000), Pro $36/month. Perpetual Indie $489 and Pro $989, each with 2 years of updates. — [InstaMAT site](https://www.instamaterial.com/)
- "InstaMAT Pipeline: Command-line execution of Element Graphs for CI/CD integration and batch processing". "InstaMAT SDK: C++ SDK for deep integration". Studio covers Windows, macOS and Linux, mesh projection, layer painting, procedural baking and UDIMs. — [InstaMAT site](https://www.instamaterial.com/)
- InstaMAT Pipeline exists on macOS (a community thread about its install location). — [Abstract community](https://community.abstract3d.com/t/instamat-pipeline-install-location-on-macos/1756)

### Inferences
- InstaMAT is a free, scriptable node-graph *material and mask* engine, a Substance Designer equivalent with a CLI. It could generate finish textures or wear masks from baked maps. It's not a path or ribbon painter, and it would add a second runtime that every skin pays for.

### Gaps
- Didn't find InstaMAT Pipeline docs saying whether graphs can take an FBX, bake it and project or paint along supplied 3D points. Whether a Python API exists beyond the C++ SDK and CLI is unconfirmed. The exact attribution wording for free skins shared online wasn't checked.

## 5. ArmorPaint (and ArmorLab): cheap, open source, command line

### Takeaway
ArmorPaint is **$19 one-time** (all updates included) or free to build from the open-source code. It runs on Windows, Linux and Apple-Silicon macOS and is the only candidate with a documented **headless** command line: `--background`, `--script <path>` and `--export-textures`. It has Path and Curve layers (control points placed by clicking), decals and a Text tool, but the plugin API documented by a secondary source exposes no layer creation, painting, decals, baking or export. Whether a script can place path control points is unknown, and `armorpaint --api` would answer it locally.

### Cited Findings
- Command line, verbatim: `--background  Run without displaying the window`; `--export-textures <type> <preset> <path>` (png, jpg, exr16, exr32); `--export-mesh`; `--export-material`; `--reload-mesh`; `--script <path>  Run script on the opened project`; `--api  Print the scripting API reference`. — [ArmorPaint manual](https://armorpaint.org/manual)
- Path and Curve layers: "Press left mouse button onto a mesh to add a new control point… Press delete key to remove the last selected control point." Brush ruler: hold SHIFT and click "to paint lines". There are a Decal tool and a Text tool ("active material as a text onto the surface"), and bakes for AO, curvature and normal. Imports .obj, .fbx, .blend, .stl, .gltf and .glb. "Plugins are written in a minimal interpreted C variant." — [ArmorPaint manual](https://armorpaint.org/manual)
- "Buy - $19"; "All updates are included for free"; desktop builds for "Windows, Linux and macOS (apple silicon)"; "ArmorPaint is an open-source project. Check out the full source code via git." — [ArmorPaint download](https://armorpaint.org/download)
- Secondary source (an AI-generated wiki, not official): plugin and script functions cover mesh and texture importers, material and brush node categories, and UI and console only. "The documentation does not expose functions for: layer creation, painting/brush strokes at specific coordinates, decals, text rendering, baking, or texture export." Scripts use the MiniC interpreter. — [mintlify.wiki: ArmorPaint plugin API](https://mintlify.wiki/armory3d/armorpaint/dev/plugin-api)

### Inferences
- ArmorPaint is the cheapest test of whether *any* off-the-shelf painter lets a script lay a surface path. Running `--api` on a downloaded or built binary shows the whole scripting surface in minutes. If path layers can be set from a script, ArmorPaint could rasterise tapes headlessly on both machines. If not, it offers nothing the home-made painter lacks.
- The risks are a small project with essentially one maintainer and a thin, changing scripting API.

### Gaps
- The full MiniC API (from `--api`) wasn't seen. The official site has no API reference, and the secondary wiki may be incomplete. ArmorLab's price and scripting weren't checked (it's an AI material generator, outside "mechanics").

## 6. Houdini (comparison only; Indie is a subscription)

### Takeaway
Houdini Indie is a **rental/subscription** for people under $100K a year, with batch (non-graphical) mode through Houdini Engine Indie. A secondary source puts it at $299/year or $449 for two years after the Houdini 21 price change. It's the one tool where curves on surfaces, baking and texturing are fully scriptable headless (`hython`), but for this tool's needs it duplicates free geometry libraries already installed, at a recurring cost.

### Cited Findings
- Indie is "designed for people making less than $100K USD per year" with a "Limit of 3 licenses per studio". It's rental-based. Houdini Engine Indie "can be used to run Houdini Indie in batch (non-graphical) mode". "With the release of Houdini 21, Indie prices have been adjusted". Apprentice is free but non-commercial and watermarked. — [SideFX: Buy](https://www.sidefx.com/buy/)
- Indie price: $299/year or $449 for 2 years (secondary). — [shade.inc: Houdini pricing 2026](https://shade.inc/blog/sidefx-houdini-pricing-2026-fx-core-indie-license-costs)

### Inferences
- The tape problem is a geometry problem (a continuous line on the mesh, then distance per texel). potpourri3d and libigl already give geodesics for free, so Houdini isn't worth a subscription here.

### Gaps
- The official Indie price wasn't on the fetched SideFX page. SideFX Labs' baker and Copernicus texturing weren't verified for this use.

## 7. Blender (bundled Python) and paid add-ons (DECALmachine)

### Takeaway
Blender itself is free and fully drivable headless with its *own* bundled Python (`blender --background --python script.py`), which sidesteps the pip `bpy` version clash with the tool's Python 3.14. DECALmachine (around $49.99, Blender 4.3–5.2) projects or shrinkwraps decals onto curved surfaces and bakes them, but it's an interactive add-on, and headless scripting of it is unverified.

### Cited Findings
- Blender 5.2 LTS manual: `--background  Run in background (often used for UI-less rendering)`; `--python <filepath>  Run the given Python script file`; `--python-expr <expression>`; `--factory-startup  Skip reading the startup.blend`. — [Blender manual: command line arguments](https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html)
- DECALmachine adds surface detail with mesh decals "in a very non-committal, non-destructive, UV-less way". It can "place Decals on flat surfaces and project or shrinkwrap them on curved ones", supports trim sheets and atlasing, bakes for game engines, and "2.17 works with Blender 4.3 to 5.2". Price shown as $49.99 on one marketplace. — [Superhive: DECALmachine](https://superhivemarket.com/products/decalmachine); [MACHIN3: DECALmachine](https://machin3.io/DECALmachine)

### Inferences
- Running Blender as a subprocess (its own Python) is a free way to bake extra maps (AO, curvature via Cycles) or to shrinkwrap a decal mesh onto the car and bake it to the skin's UVs. DECALmachine's operators are built for the viewport, so a script would more likely call Blender's own modifiers (Shrinkwrap, Data Transfer) and bake. That's a free path, not a paid one.

### Gaps
- No source on DECALmachine running in `--background` mode or having a scripting API. The Python version bundled with Blender 5.2 wasn't checked.

## 8. Other paid tools: Rhino 8 (+ Grasshopper), Plasticity

### Takeaway
Rhino 8 is a one-time $995 licence covering Windows and Mac. It's strong for curves on surfaces but is a NURBS CAD tool with no texture painting. For lines on a fixed, UV-mapped game mesh it would replace only the geometry step, which free libraries already cover. Plasticity is a modelling tool and wasn't researched.

### Cited Findings
- Rhino commercial licence $995, upgrades $595. "The Rhino license cost covers Windows and Mac in one purchase" (secondary). — [renderahouse: Rhino pricing 2026](https://www.renderahouse.com/blog/rhino-pricing)

### Inferences
- Not worth it. Rhino's curve-on-mesh tools would still need the home-made painter to rasterise into the UV atlas, which is where seams and steps arise.

### Gaps
- Rhino's headless/Compute scripting on Mac wasn't researched (out of scope given the verdict).

## 9. Licence terms that matter: sharing skins online, two computers, offline

### Takeaway
None of the sourced terms forbid using texture outputs in skins shared online. Two-computer use is explicitly allowed only for 3DCoat (alternate use, any OS) and Rhino (Win+Mac, secondary source). Elsewhere it's unverified. InstaMAT's free tier requires attribution for commercial use, and Houdini Indie and (reportedly) Painter's Steam edition cap revenue at $100K, which a free hobby skin doesn't approach.

### Cited Findings
- 3DCoat: one serial can be installed on two computers if used at alternate times, on any supported OS. — [Pilgway licensing (search snippet)](https://pilgway.com/licensing/5)
- InstaMAT Pioneer: free under $100k revenue, "Attribution is required for commercial use". — [InstaMAT site](https://www.instamaterial.com/)
- Houdini Indie: under $100K USD per year; Apprentice is non-commercial with a watermark. — [SideFX: Buy](https://www.sidefx.com/buy/)
- ArmorPaint is open source, and its updates are included. — [ArmorPaint download](https://armorpaint.org/download)
- Painter Steam: perpetual, keep the version after March 2027. The revenue cap ("under $100K") is claimed only by a user. — [gg.deals](https://gg.deals/application/substance-3d-painter-2026/); [Adobe community 629574](https://community.adobe.com/questions-59/substance-painter-3d-on-steam-what-type-of-licence-is-there-indie-pro-629574)

### Inferences
- Steam products generally install on any machine where the account logs in and run offline once activated. For Painter on both Mac and PC this is plausible but not confirmed by Adobe.

### Gaps
- Not found: Marmoset's seat terms (two machines), Painter Steam's cross-platform and offline terms, and any vendor clause on game-skin distribution.

## Applicability to this tool

### Takeaway
**None of these is worth buying to fix the tapes.** Across every candidate, the operation the user needs (a stroke, ribbon or lettering laid along a line on the car, placed from code) is either interactive-only (Painter's Path/Ribbon, ArmorPaint's Path/Curve layers, Marmoset's paint and vector layers) or undocumented (Marmoset `importStroke`, ArmorPaint's MiniC API). What paid tools *can* automate is finishes: smart materials, curvature/AO-driven wear, projected decals, baking and export. That's a different problem from the gaps and steps, which come from how the line is traced on the mesh and turned into texels; a script driving Painter would still be handing Painter a mask the tool computed. The gaps and steps have to be fixed in the home-made line maths (see `mesh_lines_and_curves.md`). The pieces of the current painter stay: bake, per-texel paint and DDS export.

### Ranked shortlist (only if the user wants to try something)
1. **ArmorPaint: $19 one-time, or free to build; Mac (Apple Silicon) and Windows; headless.** It *might* replace the tape rasteriser if its script API can place Path/Curve layer points, which is unknown. Risks: a one-person project and a thin API. Cheapest try: download or build, run `armorpaint --api` and `--background --script` on the CarSport FBX, which settles it in under an hour. [manual](https://armorpaint.org/manual), [download](https://armorpaint.org/download)
2. **Substance 3D Painter 2026 on Steam: $199.99 one-time (updates to March 2027); Mac and Windows; needs its window open.** It would replace finishes only: smart materials, edge wear from baked maps, planar-projected decals, bake and export, scriptable through the Python API or a ready-made MCP server (free `substance-painter-mcp`, or $15 MCP Pro). It wouldn't touch tapes or lettering: "Strokes are not accessible from the Python API", and no tool creates paths. Risks: a second source of truth beside the numpy painter, a GUI app that must be running, a version frozen after March 2027, and extra minutes on every skin (against "don't add a step that every skin pays for"). Cheap try: the user already has `SkinTemplate2021_V2.1.spp` in the repo (per a sibling note), so with a trial or purchase one finish stage could be scripted on the self-test car and compared by eye. Whether Adobe offers a trial for the Steam edition wasn't verified. [API: paint](https://experienceleague.adobe.com/en/docs/substance-3d-dev/painter-python/api/substancepainter-package/layerstack-module/layers-and-effects/paint), [MCP Pro](https://y1uda.itch.io/painter-mcp-pro)
3. **Marmoset Toolbag 5: $399 perpetual (or a $18.99/month subscription); native Apple Silicon and Windows; a script at launch, then `quit()`.** It would replace decal placement (projector with edge fade and normal weight) and procedural wear layers. It has no path or stroke API. Risk: the price, for capabilities the per-texel painter can mostly reproduce. Try first with Marmoset's free trial. [mset reference](https://marmoset.co/python/reference5.html)
4. **InstaMAT: free (Pioneer, under $100k, attribution if commercial) or $489 perpetual; Win, Mac and Linux; Pipeline CLI.** A possible free graph engine for finish and wear masks from baked maps, with no evidence of path painting. Try for free. [InstaMAT](https://www.instamaterial.com/)
5. **Not recommended:** 3DCoat (€379; no scripted painting, baking or export documented); Houdini Indie (a **subscription**, about $299/year; duplicates free geodesics); Blender add-ons such as DECALmachine (about $49.99; interactive, though Blender itself is a free headless option for extra bakes); Rhino 8 ($995; CAD, no painting).

### Gaps
- The make-or-break unknowns behind this ranking are whether ArmorPaint's script API can set path points, and whether Marmoset's stroke file format can be written. Both can be checked locally and cheaply before any purchase above $19.
