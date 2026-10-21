# Game texture compression, Trackmania 2020 skin requirements, and a viewer that matches the game (October 2026)

Versions and dates below were read from GitHub's releases API and PyPI's JSON API on 2026-10-07, not from memory.

## 1. BCn encoders in 2026: who is maintained, what they do, where they run

### Takeaway
For BC1/BC3/BC4/BC5 with legacy D3D9 headers, no single established encoder covers both computers with Python access. DirectXTex/texconv (MIT) is active but builds only for Windows (or WSL). NVTT 3 runs on Windows and Linux only, under a proprietary SDK. Compressonator has had no release since January 2024. ISPC Texture Compressor is archived. Pillow can save BC1/BC3/BC5 but not BC4. The strongest open BC1-5 quality reference that runs on a Mac with Python is Rich Geldreich's rgbcx (in bc7enc_rdo), wrapped by `quicktex`.

### Cited Findings

**Pillow**
- The current Pillow is 12.3.0, uploaded 2026-07-01 (MIT-CMU licence). — [PyPI Pillow](https://pypi.org/project/Pillow/)
- Pillow's DDS docs (12.3.0): "Added in version 11.2.1: DXT1, DXT3, DXT5, BC2, BC3 and BC5 pixel formats can be saved: `im.save(out, pixel_format="DXT1")`". Reading covers DXT1/3/5, DX10, BC5S/BC5U, ATI1/ATI2 and uncompressed. **BC4 save and BC7 save are not listed**, and the save docs say nothing about mipmaps. — [Pillow image file formats, DDS](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html)
- The DDS BCn encoder arrived in Pillow 11.2.0 with a write buffer overflow (CVE-2025-48379) when writing large (>64k encoded) DDS images. It was fixed in 11.3.0 (2025-07-01). — [Pillow 11.3.0 release notes](https://hugovk-pillow.readthedocs.io/en/latest/releasenotes/11.3.0.html); [OSV GHSA-xg8h-j46f-w952](https://osv.dev/vulnerability/GHSA-xg8h-j46f-w952)
- (Project fact) The tool's own measurement (2026-09-24) found Pillow's "bcn" encoder 5 dB worse than the in-house encoder, with visible fringes round sticker outlines. — `/Users/fcarbo/Developer/personal/tm-skin-creator/tool/dds.py` docstring

**Microsoft DirectXTex / texconv**
- Latest release: "May 7, 2026" (tag may2026, published 2026-05-08), a bug-fix release (HDR reader out-of-bounds fix, CMake updates). It is on NuGet as 2026.5.8 and installs with `winget install Microsoft.DirectXTex.Texconv`. MIT licence; the repo was still active on 2026-10-06. — [DirectXTex releases](https://github.com/microsoft/DirectXTex/releases)
- Platforms: it builds with Visual Studio 2022/2026, clang for Windows or MinGW, and "can also be built for Windows Subsystem for Linux using GCC 11 or later". There is **no macOS build**. — [DirectXTex README](https://github.com/microsoft/DirectXTex)
- texconv options that matter here:
  - `-dx9` "Forces DDS file output to always use legacy DX9 headers. This will fail for BC6, BC7, UINT, and SINT formats. SRGB formats will be written using non-SRGB formats."
  - `-srgb/-srgbi/-srgbo` control sRGB-correct conversion.
  - `-bc u` (uniform rather than perceptual weighting, BC1-3), `-bc d` (dithering), `-bc x` (BC7 maximum).
  - `--reconstruct-z` for BC5 normals.
  - `-if` mip/resize filters: POINT, LINEAR, CUBIC, FANT, BOX, TRIANGLE and dithered variants (**no Kaiser**).
  - Special `-f BC3n`/`DXT5nm` and `-f RXGB -dx9` legacy normal-map variants.
  - [texconv wiki](https://github.com/microsoft/DirectXTex/wiki/texconv)

**NVIDIA Texture Tools 3 (NVTT 3)**
- Platforms: Windows 10/11 64-bit, Linux x86_64 and Linux AArch64. macOS is not listed. It is CUDA-accelerated "with CPU fallbacks", and supports BC1-7 and LDR ASTC. — [NVIDIA Texture Tools 3 product page](https://developer.nvidia.com/gpu-accelerated-texture-compression)
- The latest public release found is NVTT 3.2.5.1 / Texture Tools Exporter 2024.1.1 (2024-08-15). Its notes include "A2D5 and A2XY swizzle code reading for DDS files" and "BC5U DDS writing without DXT10 extension". These match Trackmania's legacy ATI2 files carrying "A2XY" (see section 2). — [NVIDIA forum release post](https://forums.developer.nvidia.com/t/nvidia-texture-tools-exporter-2024-1-1-nvtt-3-2-5-1-released/303437)
- There is no NVTT package on PyPI. `pynvtt` 0.0.2 (2025-06-30, CC0) is a small third-party wrapper that needs the NVTT 3 SDK installed. — [PyPI pynvtt](https://pypi.org/project/pynvtt/)
- The open-source NVTT 2 (castano/nvidia-texture-tools) has been archived since its last release, 2.1.2 (2020). — [castano/nvidia-texture-tools](https://github.com/castano/nvidia-texture-tools)
- Nadeo's own doc recommends the NVIDIA Texture Tools Exporter (a Photoshop plugin and standalone app) for authoring .dds, because it "automatically creates mipmaps". — [doc.trackmania.com texture mods](https://doc.trackmania.com/create/texture-mods/mods/)

**AMD Compressonator**
- The latest release is V4.5.52 (2024-01-31), and the last push was 2024-06-19. It "supports Microsoft Windows® and Linux builds" (no macOS). The licence is MIT-style ("Permission is hereby granted, free of charge…", © 2024 AMD). The CMP_Core SDK exposes per-block BC1-5 encoders with channel weights. There is no Python package on PyPI. — [Compressonator GitHub](https://github.com/GPUOpen-Tools/compressonator); [Compressonator revision history](https://compressonator.readthedocs.io/en/stable/revisions.html)

**Rich Geldreich: bc7enc_rdo / rgbcx / bc7e / bc7f**
- bc7enc_rdo provides "Fast BC1-7 GPU texture encoders with Rate Distortion Optimization (RDO)". BC1-5 encoding/decoding is in `rgbcx.cpp/.h`. RDO trades quality for 10-50% smaller LZ-compressed size. The repo was pushed 2026-07-31; GitHub could not detect its licence (NOASSERTION), so check the LICENSE file before vendoring. — [bc7enc_rdo README](https://github.com/richgel999/bc7enc_rdo)
- The README notes a newer real-time analytical BC7 encoder, "bc7f" (January 2026), and a plain C++ port of bc7e.ispc in basis_universal. — [bc7enc_rdo README](https://github.com/richgel999/bc7enc_rdo)
- `quicktex` 0.3.1 (2024-10-17) is a Python library "based on the RGBCX encoder… one of the highest quality S3TC encoders available". It has a CLI (`quicktex encode bc1 file.png`) and wheels, and needs OpenMP from Homebrew on macOS. — [PyPI quicktex](https://pypi.org/project/quicktex/)

**Aras Pranckevičius, "Texture Compression in 2020"** (the most-cited independent benchmark; older, but no newer equivalent was found)
- For DXTC (BC1/BC3) there is "very little quality variance" among good encoders. ISPC "has been the go-to compressor for some years", and rgbcx/icbc give marginal quality gains. For BC7, bc7e is "a clear winner". BC4/BC5 were not benchmarked. — [aras-p.info 2020](https://aras-p.info/blog/2020/12/08/Texture-Compression-in-2020/)

**ISPC Texture Compressor**
- The GitHub repo is archived (last push 2024-09-23), MIT. — [GameTechDev/ISPCTextureCompressor](https://github.com/GameTechDev/ISPCTextureCompressor)

**etcpak and Python wrappers**
- etcpak 2.1 (2026-02-22) fixed BCn DDS load/write and mip sizes for non-power-of-two textures. Benchmarks on an Apple M3 Max: BC1 3255 Mpx/s single-threaded and BC7 5.47 Mpx/s ST. Its author says it is "best suited for rapid assets preparation during development, when graphics quality is not a concern". — [etcpak README/releases](https://github.com/wolfpld/etcpak)
- The Python `etcpak` 0.9.15 (2025-08-11, MIT, Win/Mac/Linux wheels) exposes compress_bc1/bc1_dither/bc3 and ETC. — [PyPI etcpak](https://pypi.org/project/etcpak/)
- `texture2ddecoder` 1.0.6 (2026-01-16, MIT, Win/Mac/Linux) is decode-only: BC1, BC3, BC4, BC5, BC6, ETC, ASTC and more. It is useful as an independent decoder for checking the tool's output. — [PyPI texture2ddecoder](https://pypi.org/project/texture2ddecoder/)

**Basis Universal / KTX2**
- basis_universal v2.50 (2026-08-03): "XUASTC with in-loop deblocking, XUBC7, DDS support". The library "can write .basis, .KTX2, .DDS…". Its transcoder reads DX9 and DX10 .DDS (BC1-7, with mips). "Full Python support… is now available… but is still in the early stages". Apache-2.0. — [basis_universal README](https://github.com/BinomialLLC/basis_universal); [releases](https://github.com/BinomialLLC/basis_universal/releases)
- KTX-Software v5.0.0-rc2 (2026-08-17); last stable v4.4.2 (2025-10-04). `pyktx` 4.4.2 is on PyPI. — [KTX-Software releases](https://github.com/KhronosGroup/KTX-Software/releases); [PyPI pyktx](https://pypi.org/project/pyktx/)

### Inferences
- **No established encoder is clearly better for this job.** Aras found little quality spread among good BC1/BC3 encoders. The tool's own encoder (principal axis plus least-squares refinement and local search) is the same family of algorithm as rgbcx/ISPC. The likely remaining gain is a fraction of a dB, not the 5 dB lost to Pillow. This needs measuring (see Gaps).
- **The established options don't fit the two-computer setup:**
  - texconv and NVTT are Windows-only (NVTT also runs on Linux); neither runs on the Mac where design and preview happen.
  - Compressonator and ISPC are stale or archived.
  - Pillow lacks BC4 save, which the tool needs for CoatR and DirtMask, and gives no mip-filter control.
  - Switching would add a platform split, a binary dependency, and a byte-for-byte change to every car's files (the self-test rule).
- **Header compatibility is something the tool already solved.** NVTT 3.2.5's release notes call out A2XY swizzle reading and BC5U without a DX10 header. That suggests Nadeo's reference files came from NVIDIA's tool chain, which the tool's header already copies (flags 0xA1007, caps 0x401008, "A2XY").
- **Mip filtering:** the tool uses a 2×2 box filter in linear light for colour. That is gamma-correct, but a box filter is the softest standard choice. A wider kernel (Kaiser or Lanczos) gives crisper distant mips. That matters only in-game at distance, and only the game shows it.
- **BC5 normals:** good practice is to renormalise XY per mip and reconstruct Z. The tool's `normal=True` path does this in its mip builder. texconv `--reconstruct-z` confirms Z is never stored in BC5.

### Gaps
- No published 2025-2026 PSNR/SSIM benchmark of BC4/BC5 encoders (Aras excluded them), and no 2024+ cross-encoder BC1/BC3 benchmark was found. The only way to know whether rgbcx (quicktex) or texconv beats the in-house encoder on these cars is to run them on the self-test car's textures.
- Whether NVTT 3's mipmap filters include Kaiser could not be confirmed from current NVIDIA pages. NVTT 2's API had one, but no NVTT 3 source was fetched.
- No NVTT 3 licence text was retrieved. The product page did not state cost terms.

## 2. Trackmania 2020 skin technical requirements

### Takeaway
The only authoritative spec is still Nadeo's 2020 forum post (Ubi-Alinoa, 2020-08-06). It names every texture and its BC format, requires "D3D9 presets and not DX10+", and specifies OpenGL (Y+) normals and roughness=R, metalness=G. Nothing official documents size limits, resolution, sRGB, BC7 acceptance, or custom skins for the newer cars. No 2025-2026 change to the skin format was found.

### Cited Findings
- **Nadeo's stadium-car skin spec** (Ubi-Alinoa, Ubisoft forums, 2020-08-06; it links a template download on Google Drive):

  | Group | File | Format | Role |
  |---|---|---|---|
  | Skin | `Skin_B` | BC1 | basecolour |
  | Skin | `Skin_R` | BC5 | R roughness, G metalness |
  | Skin | `Skin_CoatR` | BC4 | varnish/clearcoat layer, greyscale |
  | Skin | `Skin_DirtMask` | BC4 | dirt mask |
  | Details | `Details_B` | BC1 | basecolour |
  | Details | `Details_R` | BC5 | R roughness, G metalness |
  | Details | `Details_I` | BC3 | self-illumination; alpha sets the RGB's role |
  | Details | `Details_N` | BC5 | normal, OpenGL Y+ |
  | Details | `Details_DirtMask` | BC4 | dirt mask |
  | Wheels | `Wheels_B` | BC1 | basecolour |
  | Wheels | `Wheels_R` | BC5 | R roughness, G metalness |
  | Wheels | `Wheels_N` | BC5 | normal |
  | Wheels | `Wheels_DirtMask` | BC4 | dirt mask |
  | Glass | `Glass_D` | BC1 | tint and opacity |
  | Glass | `Glass_I` | BC5 | self-illumination |
  | Package | `Icon.tga` | — | required |

  Other points in the post:
  - "use D3D9 presets and not DX10+".
  - "_I maps (ex: Details_I) use specific greyscale values in the alpha channel to define a role for the RGB channels". The table of values is an embedded image, not text.
  - AO is handled separately by the shader.

  — [Nadeo post via devtrackers.gg](https://devtrackers.gg/trackmania/p/3490d99c-stadium-car-ressources-all-you-need-to-create-skins-for-the-stadium-cars)
- **Nadeo's texture-mod doc:** textures are .dds. PNG works but "it's strongly recommended to stick to .dds - .png does not support mipmaps, which significantly improve how textures are shown/filtered at a distance". The NVIDIA Texture Tools Exporter is recommended. — [doc.trackmania.com, texture mods](https://doc.trackmania.com/create/texture-mods/mods/)
- **Nadeo's texture list** (for environment mods, same conventions):
  - _D: BC1, or BC3 when transparent.
  - _N: BC5.
  - _R: BC5, "Red channel is used for roughness, green channel is used for metallic".
  - _I: "Self-illumination, texture glows but doesn't emit light".
  - _H and _M: BC1.
  - BC6U for cubemaps.
  - — [doc.trackmania.com, texture list](https://doc.trackmania.com/create/texture-mods/texture-list/)
- **Install and share:**
  - Skins live in `Documents\Trackmania\Skins\Models\CarSport`.
  - Uploading to a club's Skin Uploads activity is "only available on PC".
  - — [doc.trackmania.com, skin uploads](https://doc.trackmania.com/club/activities/skin-uploads/)
- **Size limit:** none is documented. When a user couldn't upload a skin to a club, Nadeo staff replied "Maybe your skin file is too heavy… give it a try with a lighter skin". — [devtrackers, can't upload skins to club](https://devtrackers.gg/trackmania/p/370d4cf3-can-t-upload-skins-to-club)
  - Commercial skins sold online are listed at roughly 7.5-17.7 MB with 4K maps. This comes from search-result snippets of sellers' pages, so treat it as weak. — [tmskins gumroad](https://tmskins.gumroad.com/l/dTfIY); [norglace gumroad](https://norglace.gumroad.com/l/ZosZh)
- **Light codes in _I alpha, ManiaPlanet era (TM2, not TM2020):** rear lights #000000 (fully on when braking), brake heat #404040, front lights #808080 (on with vehicle lights). Other snippets give headlights #676767 and brake lights #030303. These are search-result snippets about the older game, not verified for TM2020. — [ManiaPlanet forum, SkyLights tutorial](https://forum.maniaplanet.com/viewtopic.php?t=6121); [doc.maniaplanet.com, custom lights](https://doc.maniaplanet.com/nadeo-importer/how-to-set-up-custom-lights)
- **2026 updates:** the 2026-01-26 "Prestige Skins" update changed only seasonal/ranked prestige skin progression (rank tiers Bronze/Silver/Gold/Author with level caps 7/9/11/13). Nothing about custom skin files. — [Trackmania blog, 2026-01-26](https://blog.trackmania.com/2026/01/26/trackmania-prestige-skins-update-whats-new/)
- **Community tooling:**
  - Blendermania is the Blender add-on for Trackmania 2020/ManiaPlanet content. — [blender-addons.org, Blendermania](https://blender-addons.org/blendermania/)
  - Skin makers commonly show Cycles renders next to in-game screenshots; some publish TM2020 skins on Sketchfab. — [Sketchfab, TM2020 custom skin](https://sketchfab.com/3d-models/trackmania-2020-custom-skin-france-5dc0ffcfb761405695d726f6dc672c9c); [norglace gumroad](https://norglace.gumroad.com/l/ynTDs)

### Inferences
- **BC7 is effectively excluded.** Nadeo requires D3D9 presets, and legacy DX9 DDS headers cannot express BC7: texconv's `-dx9` "will fail for BC6, BC7" ([texconv wiki](https://github.com/microsoft/DirectXTex/wiki/texconv)). BC7 would need a DX10 header, which Nadeo says not to use. The tool's format set (BC1/BC3/BC4/BC5) matches Nadeo's table exactly.
- **sRGB vs linear:** legacy D3D9 FourCCs carry no sRGB flag, and texconv writes "SRGB formats… using non-SRGB formats" under `-dx9`. So the game must decide per slot. By PBR convention, _B/_D/_I colour is sRGB and _R/_N/masks are linear. The tool treats the colour slots as sRGB (sRGB-correct mips) and the rest as linear, which matches the viewer's `COLOUR_SLOTS` handling. Nadeo hasn't stated this; the evidence is convention plus the tool's own in-game checks.
- **Size budget:** without a published limit, the tool's own zip budget is the safest stance. Nadeo's only guidance is "lighter".

### Gaps
- No official file-size limit for online or club skins, and no official resolution limit, was found.
- The TM2020 `Details_I` alpha-code table is only in an image in Nadeo's post. The ManiaPlanet values above may differ, though the tool already encodes "glow codes" exactly.
- No source confirms whether custom skins are supported for CarSnow, CarRally or CarDesert, or what their template names would be.
- No source documents how the game uses `Glass_I` (BC5) or `Skin_CoatR`'s glitter beyond "clearcoat and glitter paint effect".
- The in-game skin editor/painter was not researched (no source found within budget).

## 3. Making a three.js preview match the game

### Takeaway
three.js r186 (2026-09-24) is the current release. It already has the needed pieces: physical material with clearcoat, PMREM with HDR environments, and AgX, Khronos PBR Neutral and ACES tone mappers. The project's viewer is already on r186 and uses these. The gap to the game is calibration (tone curve, exposure, environment, material response), not missing engine features. No community reproduction of Trackmania's renderer in three.js or Blender was found. model-viewer and Babylon.js offer no matching advantage.

### Cited Findings
- **three.js releases:** r186 (2026-09-24), r185 (2026-07-01), r184 (2026-04-16); MIT. — [three.js releases](https://github.com/mrdoob/three.js/releases)
  - r184 fixed MeshPhysicalMaterial's sync with `renderer.outputColorSpace` and `renderer.toneMapping`.
  - r185 fixed environment rotation/intensity checks and documented PMREMGenerator's minimum texture sizes.
  - r186 replaced separable blur with spiral blur in PMREM, added environment lighting for retroreflective materials, and added a Gaussian-splat renderer.
- **Tone mappers:** three.js defines `AgXToneMapping = 6` and `NeutralToneMapping = 7` alongside Linear, Reinhard, Cineon and ACESFilmic. — [three.js src/constants.js](https://github.com/mrdoob/three.js/blob/dev/src/constants.js)
- **Khronos PBR Neutral:** within 0.08–0.8 per channel, "the base color will be exactly reproduced in the output render" under standard lighting. "No hue shifts", and highlights are progressively desaturated. — [Khronos PBR Neutral README](https://github.com/KhronosGroup/ToneMapping/blob/main/PBR_Neutral/README.md)
- **DDS in three.js:**
  - `DDSLoader` handles only DXT1/DXT3/DXT5/ETC1 FourCCs plus DX10 BC6H. It has **no ATI1/ATI2 (BC4/BC5) support**, so Trackmania's _R/_N/CoatR/DirtMask files can't be loaded directly. — [three.js DDSLoader.js](https://github.com/mrdoob/three.js/blob/dev/examples/jsm/loaders/DDSLoader.js)
  - `KTX2Loader` does map BC1/BC3/BC4/BC5/BC7 (UNORM/SRGB/SNORM) Vulkan formats. — [three.js KTX2Loader.js](https://github.com/mrdoob/three.js/blob/dev/examples/jsm/loaders/KTX2Loader.js)
- **Colour management (Don McCurdy):**
  - Colour textures (map, emissiveMap) are sRGB; non-colour textures are linear.
  - Lighting maths happens in Linear-sRGB.
  - With a gamma workflow, "light and color values brought from other PBR programs would not match as expected", and the parameters become "just a random set of numbers that happen to produce an OK looking image for that particular scene".
  - (Written for the older `encoding` API; current three.js uses `colorSpace` with the same rules.)
  - — [Don McCurdy, Color management in three.js](https://www.donmccurdy.com/2020/06/17/color-management-in-threejs/)
- **The project's viewer** (`/Users/fcarbo/Developer/personal/tm-skin-creator/viewer/viewer.js`, vendored three.js REVISION '186'):
  - `HDRLoader` environments per mood.
  - `MeshPhysicalMaterial` for Skin, with clearcoat from `Skin_Coat`, and for glass.
  - Colour slots set to `SRGBColorSpace` and others to `NoColorSpace`.
  - Tone mapping defaults to Linear, with `?tone=aces|neutral|agx` switches.
  - Per-mood exposure.
  - Camera presets with measured FOVs (cam1 72.8°, cam1alt 75.0°, cam2 74.1°, cam2alt 69.9°).
- **WebGPU:** the 2026 secondary write-ups say WebGPURenderer is a drop-in swap (since around r171) and WebGPU ships in Chrome, Firefox and Safari. Their release dating is inconsistent with GitHub's, so treat them as indicative only. — [utsubo, three.js in 2026](https://www.utsubo.com/blog/threejs-2026-what-changed); [utsubo, WebGPU migration guide](https://www.utsubo.com/blog/webgpu-threejs-migration-guide)
- **model-viewer** v4.3.1 (2026-06-04, Apache-2.0), a three.js-based web component:
  - `tone-mapping` options include none, linear, neutral, agx, plus `tone-mapping-exposure`.
  - Its default neutral environment is "roughly calibrated to render colors at nearly their baseColorMap RGB values".
  - It takes glTF models only.
  - — [model-viewer releases](https://github.com/google/model-viewer/releases); [modelviewer.dev tone mapping](https://modelviewer.dev/examples/tone-mapping); [modelviewer.dev lighting & env](https://modelviewer.dev/examples/lightingandenv/)
- **Babylon.js** 9.29.0 (2026-10-01, Apache-2.0) is active, with weekly releases. — [Babylon.js releases](https://github.com/BabylonJS/Babylon.js/releases)
- **No community viewer:** no web 3D skin viewer reproducing Trackmania's look was found. The community previews skins in Blender (Cycles) and in-game screenshots. — [Sketchfab TM2020 skin](https://sketchfab.com/3d-models/trackmania-2020-custom-skin-france-5dc0ffcfb761405695d726f6dc672c9c); [Blendermania](https://blender-addons.org/blendermania/)

### Inferences
- **Calibration, not a new engine.** The viewer already uses every relevant three.js feature. Remaining mismatch comes from:
  - the tone curve (the game's is unknown; Linear default versus AgX/Neutral/ACES);
  - the environment (the HDRs are not the game's stadium sky or lighting);
  - the game's own shader terms, which a generic three.js material doesn't model: dirt mask, the _I codes, glitter in CoatR, the separate AO.

  These are tuned against the game's own output, F12 screenshots, rather than taken from documentation. None exists.
- **Moving engines is churn.** Babylon and model-viewer have the same physically-based model and tone-mapper options, and model-viewer has fewer controls and needs glTF.
- **Preview the game's actual pixels.** Because three.js can't load BC4/BC5 DDS, the viewer is presumably fed pre-decoded images. Decoding the built DDS (the tool's own decoder, or `texture2ddecoder` as a cross-check) shows block artefacts as the game will. KTX2 could carry BC4/BC5 to the GPU, but the game's files would still be DDS.
- **Camera:** the viewer already stores measured FOVs. Trackmania's own FOV setting/default was not found in public sources, so continue measuring from screenshots.

### Gaps
- No public documentation of Trackmania 2020's tone mapping, exposure, sky/IBL, or car shader (clearcoat model, glitter, dirt, emissive intensity) was found. Nadeo hasn't published it, and the game's files must not be taken apart.
- No default in-game camera FOV values were found.
- The three.js colour-management manual page could not be fetched (404 at the guessed URL). Don McCurdy's guide was used instead.

## 4. Automated viewer-vs-game screenshot comparison

### Takeaway
The practical stack is: align a viewer render to an F12 screenshot (same camera preset, same crop), then score the pair with NVIDIA FLIP (BSD-3, pip wheels for Mac and Windows) and SSIM (scikit-image). Fit only a few global knobs (exposure, environment intensity, tone mapper, clearcoat strength) by minimising that score.

### Cited Findings
- **NVIDIA FLIP** is "A tool for visualizing and communicating the errors in rendered images", with LDR-FLIP and HDR-FLIP modes. It models errors as seen when flipping between images. Install with `pip install flip-evaluator`, run with `flip -r reference.png -t test.png`. BSD 3-Clause. — [NVlabs/flip](https://github.com/NVlabs/flip)
  - `flip-evaluator` 1.7 (2025-11-07) has wheels for macOS arm64, Windows amd64 and Linux. — [PyPI flip-evaluator](https://pypi.org/project/flip-evaluator/)
- **scikit-image** 0.26.0 (2025-12-20), with macOS arm64 and Windows wheels, provides SSIM. — [PyPI scikit-image](https://pypi.org/project/scikit-image/)
- **pyiqa** 0.1.16 (2026-07-08) has many IQA metrics but a PolyForm-Noncommercial licence. — [PyPI pyiqa](https://pypi.org/project/pyiqa/)
- **lpips** 0.1.4 was last released in 2021 and needs PyTorch. — [PyPI lpips](https://pypi.org/project/lpips/)

### Inferences
- **What to compare.** Use the user's own F12 screenshots as references (the project rules allow this). Compare masked crops of the car only, because backgrounds differ. Compare at the camera presets the viewer has already matched.
- **What to fit.** A small grid or least-squares search over 3–5 global parameters is cheap and keeps the viewer honest. Per-material fitting would overfit a single screenshot.
- **Where the score fits.** FLIP's heat map is also a picture the user can judge, consistent with "the user's eye decides". The score backs the eye; it doesn't replace it.

### Gaps
- No published example of anyone calibrating a web viewer against Trackmania screenshots was found.

## Applicability to this tool

**Encoder: keep the home-made one.** Use established encoders as one-off yardsticks.
- **It fits the setup.**
  - It runs the same on Mac and PC with only numpy.
  - It writes Nadeo's exact legacy headers ("A2XY", flags and caps copied from reference files).
  - It keeps `Details_I` codes exact in BC4/BC3-alpha.
  - Block deduplication makes it fast on mostly flat paint.
- **Every alternative has a disqualifier:**

  | Alternative | Problem |
  |---|---|
  | Pillow | can't save BC4; measured 5 dB worse |
  | texconv | Windows/WSL only |
  | NVTT 3 | Windows/Linux only, proprietary SDK, no official Python |
  | Compressonator | no release since Jan 2024 |
  | ISPC | archived |
  | etcpak | speed over quality |

  Adopting any of them would split the build by computer and change every car's bytes.
- **Worth doing once (minutes, not a per-skin cost):** encode the self-test car's textures with `quicktex` (rgbcx, Mac) and texconv (PC, `-dx9`). Compare PSNR per map, and look at sticker edges, against the in-house encoder.
  - If rgbcx wins by a clear margin on BC1 edges, port its refinement ideas (or call quicktex) rather than swap toolchains.
  - Keep `texture2ddecoder` as an independent decoder to check the tool's files.
- **Don't add BC7:** D3D9 headers can't carry it, and Nadeo says D3D9 presets.
- **Possible quality gain:** a sharper mip filter (Kaiser or Lanczos instead of the 2×2 box, still in linear light) for distant crispness. Judge it in-game only.

**Viewer: keep the home-made three.js viewer (already r186).** Make it match the game by calibration, not a new engine.
- three.js has every needed feature. Babylon and model-viewer offer nothing the game-match problem needs; model-viewer also forces glTF and gives fewer controls.
- **Next steps, in order:**
  1. Feed the viewer the decoded built DDS (what the game will sample) rather than the pre-compression images, since three.js's DDSLoader can't read BC4/BC5.
  2. Add a small calibration script. Render the viewer at a matched camera preset, mask the car, and compare with the user's F12 screenshots using FLIP and SSIM. Fit exposure, environment intensity, the tone mapper (Linear/AgX/Neutral/ACES) and clearcoat strength per mood. Show the user the FLIP heat map next to the pair.
  3. Model the game-specific terms the generic material lacks (dirt mask, `_I` glow codes, CoatR glitter) only where the screenshots show a visible gap. Each is a guess until compared against the game.
- **Cost and licences:**
  - All suggested additions are free: FLIP (BSD-3), scikit-image (BSD), quicktex (rgbcx-based), texture2ddecoder (MIT).
  - Avoid pyiqa: its licence is non-commercial.
  - NVTT 3 is a proprietary NVIDIA SDK; its terms were not retrieved.
