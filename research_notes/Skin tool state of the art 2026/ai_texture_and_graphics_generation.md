# AI generation for 3D textures, decals, graphics and lettering (as of 7 October 2026)

Scope: what AI can do today to paint a fixed game mesh (Trackmania 2020 CarSport, fixed UV layout), and to make the graphics, decals, patterns, lettering and mood boards a livery is built from. The question behind it is which approaches fit a tool where Claude writes the design and the tool paints it.

Reliability note: many 2026 facts come from secondary aggregators (pricing resellers, blogs). Where a primary page was fetched (arXiv, GitHub, Hugging Face, Google/OpenAI/Meshy docs, Artificial Analysis), it is preferred and named. Conflicts are flagged inline.

## 1. Text-to-texture on a given mesh (2024–2026)

### Takeaway
Texturing a user-supplied mesh is a real, fast-moving research and product area. The usual pipeline is multi-view diffusion, then projection and baking to UV, and the newest work moves generation into UV, texture or 3D space to escape seams and view inconsistency. Open models that do it on your own mesh (Hunyuan3D-2.1 Paint, TRELLIS.2 texturing, StableGen in Blender) need 16–24 GB of NVIDIA VRAM or Linux. Some carry licence traps: Hunyuan excludes the EU, UK and South Korea, and TRELLIS.2's texture mode depends on non-commercial NVIDIA libraries. Cloud "retexture" APIs (Meshy, Tripo) cost about 10 credits a model and sit behind subscriptions. Meshy can keep the original UVs. None of them offers livery-level layout control, crisp graphics or correct lettering, and reviewers name a "real ceiling on hard-surface quality".

### Cited Findings
**Research lineage (older methods, superseded):**
- TEXTure, Text2Tex, Paint3D, SyncMVD and FlashTex (2023–2024) are now used as baselines that MV-Adapter is compared against. — [MV-Adapter (arXiv 2412.03632)](https://arxiv.org/pdf/2412.03632)
- SyncMVD synchronises multi-view diffusion through overlapping regions in UV texture space, "using UV mapping as a pre-established connection among all views" (2023). — [SyncMVD (arXiv 2311.12891)](https://arxiv.org/pdf/2311.12891)
- RomanTex (2025) adds 3D-aware rotary positional embedding and decoupled attention for cross-view coherence before baking to UV. — [search summary of RomanTex; via arXiv listing](https://arxiv.org/pdf/2504.02762)
- 2025 PBR-focused work includes MaterialMVP ("illumination-invariant material generation via multi-view PBR diffusion"), MVPainter, LumiTex (PBR "with illumination context"), MatLat (material latent space) and SeqTex (mesh textures generated "in video sequence"). — [MaterialMVP 2503.10289](https://arxiv.org/pdf/2503.10289); [MVPainter 2505.12635](https://arxiv.org/pdf/2505.12635); [LumiTex 2511.19437](https://arxiv.org/pdf/2511.19437); [MatLat 2512.17302](https://arxiv.org/pdf/2512.17302); [SeqTex 2507.04285](https://arxiv.org/pdf/2507.04285)

**2026 research:**
- Survey "Advances in Neural 3D Mesh Texturing" (Perla, Zhang, Mahdavi-Amiri; submitted 28 May 2026). It covers texture synthesis, transfer and completion, from GANs to diffusion pipelines, and notes that polygon meshes remain foundational in industry pipelines. — [arXiv 2606.00137](https://arxiv.org/abs/2606.00137)
- UniTEX (CVPR 2026) first adapts large 2D DiTs with LoRA for multi-view texture synthesis. It then bypasses UV mapping with a "Large Texturing Model" that regresses textures as Texture Functions in 3D space, independent of topology. Its stated reason: "UV-based models in the second stage… introduce challenges related to topological ambiguity." Code: github.com/YixunLiang/UniTEX. — [CVPR 2026 poster](https://cvpr.thecvf.com/virtual/2026/poster/37750); [arXiv 2505.23253](https://arxiv.org/html/2505.23253v1)
- MV2UV (16 March 2026) is a UV-space generative model that inpaints unseen parts of multi-view images. It names the failures of projection texturing as "multiview inconsistency", "missing textures on unseen parts", and UV-inpainting methods that "do not generalize well due to insufficient UV data". — [arXiv 2603.15436](https://arxiv.org/abs/2603.15436)
- Texture Space Material Diffusion (Munkberg, Kocsis, Hasselgren; 29 Sept 2026, revised 1 Oct 2026) fine-tunes a video diffusion transformer to generate materials "entirely in texture space", which "avoids the view consistency issues inherent in video and multi-view diffusion models". It handles 100+ input views and scales to 8K. — [arXiv 2609.37654](https://arxiv.org/abs/2609.37654v1)
- GeoCache (Aug 2026) is a training-free method that speeds up multi-view texture diffusion. — [arXiv 2608.13255](https://arxiv.org/pdf/2608.13255)

**Open models you can run on your own mesh:**
- Hunyuan3D 2.0 (21 Jan 2025) includes Hunyuan3D-Paint, which textures "either generated or hand-crafted meshes". — [arXiv 2501.12202](https://arxiv.org/abs/2501.12202v1)
- Hunyuan3D-2.1 was released 13 June 2025. Paint-v2-1 is 2B parameters and generates PBR textures (albedo, metallic, roughness). Texture generation needs **21 GB VRAM**. Generation works at 512 px. The pipeline accepts a user mesh: `paint_pipeline(mesh_path, image_path=...)`, so it is **image-conditioned**. The README lists macOS, Windows and Linux. — [GitHub Tencent-Hunyuan/Hunyuan3D-2.1](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1); PBR channels also in [arXiv 2506.15442](https://arxiv.org/html/2506.15442v1)
- **Hunyuan licence:** "Territory shall mean the worldwide territory, excluding the territory of the European Union, United Kingdom and South Korea." Use above 1M MAU needs a licence. Outputs placed in public must be "expressly and conspicuously" identified as machine-generated. Outputs may not be used to improve other AI models. — [Hunyuan3D-2.1 LICENSE](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1/blob/main/LICENSE)
- Hunyuan3D 2.5, 3.0 (Sept 2025) and PolyGen are **closed** and available only through the Tencent Cloud API. — [atlascloud summary](https://www.atlascloud.ai/de/models/tencent/hunyuan3d-pro/text-to-3d) (secondary source)
- TRELLIS.2 (Microsoft, 4B) published weights on HF on 30 Nov 2025 and its paper on 16 Dec 2025. — [comfyui-wiki](https://comfyui-wiki.com/news/2025-12-18-microsoft-trellis2-3d-generation); [trellis2.app](https://trellis2.app/blog/when-did-trellis-2-come-out)
  - Code and weights are MIT. It ships "shape-conditioned texture generation" for existing shapes (`example_texturing.py`, `app_texturing.py`) with Base Color, Roughness, Metallic and Opacity, GLB export up to 4096. It needs an **NVIDIA GPU with ≥24 GB** and is "tested only on Linux". — [GitHub microsoft/TRELLIS.2](https://github.com/microsoft/TRELLIS.2)
  - The fetched GitHub summary gave "December 2024", which is the date of TRELLIS v1; the dates above are preferred.
  - TRELLIS.2 texturing is conditioned on a **reference image**, not text, and can output textures up to 4096. — [Scenario help](https://help.scenario.com/articles/8823711245-trellis-2-the-essentials)
  - StableGen's README warns that TRELLIS.2's texture mode uses NVIDIA nvdiffrast/nvdiffrec, which is "restricted to non-commercial research use". — [GitHub sakalond/StableGen](https://github.com/sakalond/StableGen)
- StableGen is a GPL-3.0 Blender add-on (Blender 4.2–4.5 or 5.1+, ComfyUI backend, repo updated 12 June 2026, ~936 stars). Its texturing:
  - Models: SDXL, FLUX.1-dev, **FLUX.2 Klein** (experimental) and Qwen Image Edit.
  - Method: "Generate textures viewpoint by viewpoint on each mesh, using inpainting and visibility masks", with ControlNet depth, normal and canny, IPAdapter style transfer, and optional UV inpainting of untextured areas.
  - Hardware: Apple Silicon is supported. It needs ≥8 GB VRAM for SDXL and ≥16 GB for FLUX.1-dev.
  - Limits: lighting is baked into the textures.
  — [GitHub sakalond/StableGen](https://github.com/sakalond/StableGen); [80.lv](https://80.lv/articles/a-new-ai-powered-blender-add-on-for-creating-seamless-textures/)

**Cloud "retexture" APIs:**
- Meshy Retexture API:
  - Cost: 10 credits at 2K/4K and 15 at 8K.
  - Input: text style prompt (≤800 chars), a style image, or 1–4 multi-view images (meshy-7).
  - Options: `enable_pbr` adds metallic, roughness, normal and emission maps.
  - **`enable_original_uv`** is false by default: "Keep the model's existing UV layout instead of generating a new one."
  - Accepts .glb, .gltf, .obj, .fbx and .stl.
  — [Meshy Retexture docs](https://docs.meshy.ai/en/api/retexture); [Meshy API pricing](https://docs.meshy.ai/en/api/pricing)
- Meshy API credits are prepaid and "purchased from your subscription settings". The legacy meshy-5 model retires 10 Oct 2026. — [Meshy API pricing](https://docs.meshy.ai/en/api/pricing)
  - Plan prices conflict between sources: "Pro $20/month"; another source says "Pro $10/month (annual) delivers 1,000 credits… commercial rights and API access", which implies roughly $0.10 per retexture. **This is a subscription.** — [search summary of meshy.ai/pricing & costbench](https://costbench.com/software/ai-3d-generation/meshy/) (secondary source, conflicting)
- Tripo re-textures an existing model via API (text, reference image or style presets, PBR) for 10 credits. Plans: Pro 3,000 credits for $19.90/mo, Max 25,000 credits for $89.90/mo. Rodin (Hyper3D) Creator is $30/mo for about 60 models. **All are subscriptions.** — [apicostcalc comparison](https://apicostcalc.com/meshy-vs-tripo3d-vs-rodin-3d-model-cost-calculator.html); [layer.ai Tripo Retexture](https://layer.ai/docs/models/tripo3d-retexture) (secondary sources)

**Quality evidence on hard surfaces:**
- A Meshy review rates it 3.5/5: "great pipeline breadth, real ceiling on hard-surface quality." — [stacksheriff Meshy review](https://stacksheriff.com/ai-tools/meshy-ai-review/)
- A 2026 four-tool comparison (Meshy 7, Tripo V3.1, Rodin V2, Hunyuan 3D V3) on generated meshes found "merged geometry with no logical structure, so there is no correct UV layout and therefore no controllable texturing". Colourways had "no clean place to apply them". — [ufo3d](https://ufo3d.com/?p=11629)

### Inferences
- The car has a fixed, clean UV layout, which removes the failure ufo3d names. The other known failures remain: baked lighting, view seams, 512-px-per-view blur (Hunyuan 2.1), and no notion of a livery layout or exact graphic edges.
- Image-conditioned texturing (Hunyuan Paint, TRELLIS.2) needs a concept image of the car first, so it adds a step rather than removing one.
- The PC's card has 16 GB (per `tool/pictures.py` docstring). That is below Hunyuan Paint 2.1's 21 GB and TRELLIS.2's 24 GB; StableGen with FLUX.1-dev or FLUX.2 Klein is the only open route that fits it.
- Licences rule out Hunyuan3D for a user in the EU or UK, and TRELLIS.2 texturing for anything beyond research. Hunyuan also requires labelling public outputs as machine-generated.
- Whole-mesh AI texturing has no deterministic re-run. That clashes with the tool's self-test (every car's game files identical byte for byte).

### Gaps
- No public benchmark or practitioner test of any 2026 texturing method on a **vehicle livery** specifically (stripes, numbers, sponsor layout). Quality claims are on generic assets.
- Not verified whether the Hunyuan3D-2.1 paint pipeline keeps the input mesh's UVs or re-unwraps.
- No official per-credit dollar price was found on Meshy's own pages; plan prices conflict between sources.
- UniTEX licence, VRAM and speed not checked.

## 2. Image models for graphics, decals and patterns (2026)

### Takeaway
On blind human preference in October 2026, the frontier is closed API models: GPT Image 2/2.5, xAI Grok Imagine, Microsoft MAI-Image, Google's Nano Banana family, Qwen-Image 3.0 and Seedream 5. They cost about $0.01–0.21 an image and render short text well. GPT Image 2.x and Ideogram 4 are the strongest at lettering; Ideogram 4 also offers layout boxes. Transparent output is native in GPT Image (gpt-image-2 since 20 Aug 2026, preview), Ideogram 3/4 and Qwen-Image 2.1; it is not documented for Gemini. Among open weights, only FLUX.2 [klein] 4B (Apache 2.0) is cleanly free for skins shared online. Qwen-Image 2.1 is research-only; FLUX.2 [dev] and [klein] 9B are non-commercial. FLUX 3 Image arrived on 1 Oct 2026, and its open weights are still "to follow".

### Cited Findings
**Leaderboard (Artificial Analysis, AA-Image-T2I v2.0, fetched 7 Oct 2026):**

| Rank | Model | Elo | Released | $/1k images |
|---|---|---|---|---|
| 1 | GPT Image 2.5 Sunburst (max) | 1198 | Sep 2026 | $210.7 |
| 2 | GPT Image 2.5 Flare (max) | 1191 | Sep 2026 | $210.7 |
| 3 | GPT Image 2 (high) | 1172 | Apr 2026 | $211 |
| 4 | Grok Imagine Image 2.0 | 1156 | — | $60 |
| 5 | MAI-Image-2.6 | 1151 | — | $38.9 |
| 6 | Nano Banana 2 (Gemini 3.1 Flash) | 1126 | Feb 2026 | $67 |
| 7 | Muse Image | 1115 | — | $10 |
| 11 | Nano Banana Pro (Gemini 3 Pro) | 1102 | Nov 2025 | $134 |
| 13 | Nano Banana 2 Lite | 1095 | — | $33.6 |
| 14 | Qwen-Image-3.0-Pro | 1088 | — | $40 |
| 15 | Seedream 5.0 Pro | 1081 | — | $90 |
| 18 | Qwen-Image-2.1 | 1035 | — | open weights, no API |
| 22 | FLUX.2 [flex] | 1027 | Nov 2025 | $60 |

— [Artificial Analysis leaderboard](https://artificialanalysis.ai/image/leaderboard/text-to-image)
- **Conflict:** secondary sources quote GPT Image 2 at "1,339 Elo" (June 2026) and Nano Banana 2 at 1,260. That is likely an earlier or different scale before AA's v2.0 board. — [fal.ai](https://fal.ai/learn/tools/best-text-to-image-apis-2026); [techsy](https://techsy.io/en/blog/best-ai-image-models)

**OpenAI:**
- gpt-image-2 launched 21 April 2026. It has a reasoning pass, and OpenAI cites >95% text accuracy across Latin, CJK, Hindi, Bengali and Arabic scripts. — [neurohive](https://neurohive.io/en/news/chatgpt-images-2-0-openai-launches-image-generation-model-with-reasoning-2k-resolution-and-multilingual-text/)
- OpenAI's docs now list **gpt-image-2.5-sunburst** ("editing precision") and **gpt-image-2.5-flare** ("fast… everyday"). Both take `background: "transparent"` with PNG or WebP output. Edits accept multiple reference images (4 in the examples) plus alpha masks. Custom sizes go up to a 3840-px edge and 8.3 MP.
  - Stated limits: complex prompts "may take up to 2 minutes"; text "remains challenging"; consistency for "recurring characters or brand elements"; "precise element placement".
  — [OpenAI image generation guide](https://developers.openai.com/api/docs/guides/image-generation)
- gpt-image-2 transparent backgrounds have been in preview since 20 Aug 2026. — [ecorpit](https://ecorpit.com/gpt-image-2-transparent-background-preview-no-token-table-2026/)
- gpt-image-2 prices: $8/M input tokens and $30/M output tokens, which works out to about $0.006 (low), $0.053 (medium) and $0.211 (high) for a 1024² image. — [segmind](https://www.segmind.com/models/gpt-image-2/pricing) (secondary; consistent with AA's $211/1k)

**Google:**
- The Gemini API now documents five image models:
  - `gemini-nano-banana-2.1` (current primary): $0.0336 at 1K, $0.0504 at 2K, $0.113 at 4K; batch half price.
  - `gemini-3.1-flash-image` (Nano Banana 2): $0.067 at 1K, $0.151 at 4K.
  - `gemini-3.1-flash-lite-image`: $0.0336 at 1K.
  - `gemini-3-pro-image` (Pro).
  - `gemini-2.5-flash-image` (legacy).
  - No free tier for image models.
  - References: Nano Banana 2.1 and 3.1 Flash take up to 10 object, 4 character and 3 style references; Pro takes 6 object references.
  - All outputs carry a SynthID watermark. Transparent backgrounds are not documented.
  — [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing); [Gemini image generation docs](https://ai.google.dev/gemini-api/docs/image-generation)
- **Conflict:** on 29 Sept 2026 TestingCatalog reported Nano Banana 2.1 "not officially available… in the Gemini API". The Google docs fetched on 7 Oct list it with prices, so it probably launched in between. — [testingcatalog](https://testingcatalog.com/new-google-flow-build-now-points-to-nano-banana-2-1)
- Nano Banana Pro (Gemini 3 Pro Image) costs $0.134 at 1K/2K and $0.24 at 4K, with batch at 50% off. It is the strongest text renderer of the Nano Banana family. — [search summary of Google pricing](https://www.myarchitectai.com/blog/nano-banana-api-pricing) (secondary)

**Black Forest Labs:**
- FLUX.2 [klein] 4B (released 15 Jan 2026) is **Apache 2.0**. [klein] 9B uses the FLUX Non-Commercial License. FLUX.2 [dev] (32B) self-hosting needs a paid BFL licence for commercial deployment. FLUX.2 [pro] is API-only. — [invideo licence guide (Aug 2026)](https://invideo.io/blog/flux-ai-image-generator/); [vercel](https://vercel.com/ai-gateway/models/flux-2-klein-4b/about)
- The klein 4B model card:
  - Does text-to-image and multi-reference editing in one model.
  - Inference "in as low as under a second" on RTX 3090/4070+ at 4 steps, 1024², about 13 GB VRAM.
  - Stated limitation: "Text rendered may be inaccurate or subject to distortion."
  — [HF FLUX.2-klein-4B](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B)
- BFL's API now lists FLUX 3 Image, FLUX.2 [flex], [pro], [max] and [klein] 4B/9B, with "No subscriptions… only pay for what you generate". — [bfl.ai/pricing](https://bfl.ai/pricing)
- FLUX 3 was announced 23 July 2026 as a multimodal image, video, audio and action model. FLUX 3 Image was released 1 Oct 2026, with open-weight versions "to follow". — [datanorth](https://datanorth.ai/news/black-forest-labs-releases-flux-3) (secondary)
  - On OpenRouter it takes up to 10 reference images, resolutions from 768 to 4K, and one image per request. — [OpenRouter FLUX 3 Image](https://openrouter.ai/black-forest-labs/flux-3-image)
  - Price and text-rendering quality: not found.

**Others:**
- Qwen-Image-2.1 (20 Sept 2026) has a 7B generator and does generation and editing in one model.
  - It outputs **transparent PNGs** natively and edits with up to 10 references, with better typography.
  - **Licence: Qwen Research License, commercial use needs a separate agreement**, unlike earlier open Qwen image models.
  — [datanorth](https://datanorth.ai/news/qwen-releases-qwen-image-2-1); [rohitraj notes](https://rohitraj.tech/notes/qwen-image-2-1-commercial-license-alternatives-2026) (secondary)
- Ideogram prices:
  - 3.0: Turbo $0.03, Default $0.06, Quality $0.09.
  - 4.0: Turbo $0.03, Default $0.06, Quality $0.10.
  - "Generate w/ Transparent" on 4.0 costs $0.03–$0.42 per image across 1K–8K.
  — [puter Ideogram pricing (Jun 2026)](https://developer.puter.com/tutorials/ideogram-api-pricing/); [Ideogram API pricing page](https://ideogram.ai/features/api-pricing)

**Text rendering:**
- Text-rendering comparison (Aug 2026; blind designer evaluations by ContraLabs plus arena scores):
  - Ideogram 4 wins **layout control**: JSON bounding boxes, 16 hex colours, named typefaces, 47.9% blind designer win rate. It drops or duplicates diacritics and degrades past about 25–30 words.
  - GPT Image 2 wins multilingual text, but "cannot pin headlines to coordinates".
  - Recraft V4.1 is "reliable at logo length (~1–5 words)".
  - "Body copy beyond approximately 25–30 words fails on every model."
  — [invideo: best AI model for text in images](https://invideo.io/blog/best-ai-model-text-in-images/)
- A separate text leaderboard (Gradually): MAI-Image-2.5 Flash 76.6/100, GPT Image 2 71, MAI-Image-2.5 67.6, Ideogram 4.0 51.9 (rank 16). — [gradually.ai](https://www.gradually.ai/en/ai-models/ideogram-4/) (methodology not verified)

**Tileable patterns:**
- Circular padding of the convolutions and the VAE makes edges wrap. ComfyUI nodes (SeamlessVae, Texturaizer) do this. — [runcomfy SeamlessVae](https://runcomfy.com/comfyui-nodes/ComfyUI_Seamless_Patten/SeamlessVae)
- A public Replicate model pairs FLUX.2-klein-4B with "toroidal-RoPE and circular VAE" for pixel-wrap tiles with per-axis control. — [Replicate mindprint-flux2-klein](https://replicate.com/okgodoit-repos/mindprint-flux2-klein)
- The tool's picture maker already makes tiles by rolling the latent every step, so it draws on a torus. — `tool/pictures.py` (local)

**Real-world use on a race car:**
- An FIA Formula E team (NEOM McLaren) showed a "world first" AI-generated livery. Fans' ideas were turned into prompts, and text-to-image made the artwork that was applied to the car. — [FIA Formula E](https://fiaformulae.com/en/news/473979)

### Inferences
- For decals and illustrations shared online, FLUX.2 [klein] 4B (local, Apache) is the only licence-clean open option. Paying APIs (OpenAI, Google, Ideogram, BFL) are pay-per-image with no subscription, at about 1–21 cents an image.
- AI pixel text is a raster image, and the 2026 best case is "logo length". Small sponsor text, numbers and long words still need checking. Text that must be exact belongs in real fonts or vector.
- Style consistency across decals of one car is best served by multi-reference editing: klein multi-ref, GPT Image edits, Nano Banana's 3 style refs, FLUX 3's 10 refs.

### Gaps
- OpenAI's and Google's output-ownership terms for commercial or online sharing were not fetched; Ideogram's API terms were not checked either.
- FLUX 3 Image's price, licence and quality on text are unknown.
- Seedream 5.0 and Qwen-Image 3.0 licences and transparent support were not checked.
- AA's release-date columns were partly missing for some rows.

## 3. Vector graphics generation (SVG)

### Takeaway
LLMs writing SVG directly is now strong. On Design Arena's blind-preference SVG board (October 2026), Claude Opus 5.5 ranks #2 (1335) behind GPT-6 Astra (1436). Claude can therefore write crisp emblems, numbers, roundels and geometric marks itself. Dedicated SVG models (OmniSVG, StarVector) are research-grade, aimed at icons, and heavy. Recraft V4/V4.1 is the commercial native-SVG generator: about $0.04–0.30 an image, paid plan needed for ownership. vtracer (MIT, colour) and potrace (black and white) turn AI rasters into vectors.

### Cited Findings
- Design Arena SVG board, Oct 2026, "vector graphics as code, judged by blind human preference":

  | Rank | Model | Elo |
  |---|---|---|
  | 1 | GPT-6 Astra | 1436 |
  | 2 | Claude Opus 5.5 | 1335 |
  | 3 | GPT-5.6 Sol | 1324 |
  | 4 | Claude Opus 5 | 1317 |
  | 5 | Muse Spark 1.3 | 1307 |

  Claude Fable 5.1 and Fable 5 sit at #7 and #8. — [modelgrep (Design Arena SVG board)](https://modelgrep.com/best/svg)
  - **Conflict:** a slightly earlier snapshot had GPT-5.6 Sol #1 at 1366 and Claude Fable 5 at 1353. Rankings move monthly. — [search summary of modelgrep](https://modelgrep.com/best/svg/stealth)
- SVGenius benchmark (2,377 queries across understanding, editing and generation). — [arXiv 2506.03139](https://arxiv.org/pdf/2506.03139)
- OmniSVG-3B is built on Qwen2.5-VL-3B. The model is Apache 2.0 but its MMSVG dataset is CC BY-NC-SA. It needs 17 GB GPU and takes 4 s (256 tokens) to 83 s (4096 tokens). It does text-to-SVG and image-to-SVG, from icons to "anime characters". Its last update was 21 July 2025. — [HF OmniSVG](https://huggingface.co/OmniSVG/OmniSVG)
- StarVector (CVPR 2025) handles image-to-SVG and text-to-SVG, and introduced the SVG-Bench and SVG-Stack datasets. — [CVPR 2025 paper](https://openaccess.thecvf.com/content/CVPR2025/papers/Rodriguez_StarVector_Generating_Scalable_Vector_Graphics_Code_from_Images_and_Text_CVPR_2025_paper.pdf)
- Recraft V4/V4.1 "output true native SVG — real vector paths and structured layers". — [invideo Recraft guide](https://invideo.io/blog/recraft-ai-image-generator/)
  - OpenRouter prices: V4/V4.1 Vector $0.08, Pro Vector $0.30. — [OpenRouter](https://openrouter.ai/models/recraft/recraft-v4-vector)
  - Another source gives official V4.1 API prices of $0.035 (standard) and $0.21 (Pro) after 20 June 2026. — [invideo](https://invideo.io/blog/best-ai-model-text-in-images/) (sources conflict)
- Recraft ownership: free-plan images are owned by Recraft, public, and not for commercial use. Paid-plan images are fully owned with commercial rights, even after the subscription ends. **Paid means a subscription.** No Recraft output may be used to train AI. — [Recraft ownership FAQ](https://recraft.ai/blog/ownership-and-commercial-use-faq)
- VTracer (MIT, 1.0.0-alpha.4, Python `pip install vtracer`) handles **colour** images, where potrace is black and white. It offers spline, polygon or pixel curve fitting, and a "stacking" mode that avoids shapes with holes. — [GitHub visioncortex/vtracer](https://github.com/visioncortex/vtracer)

### Inferences
- For numbers, roundels, chevrons, crests and logotypes, Claude writing SVG, or drawing with the tool's own shapes and fonts, is near the frontier at no cost and is exactly repeatable. That fits "all in words" and the byte-identical self-test.
- AI raster art, such as a tiger head, can be made crisp at any scale by vtracer with a small palette, after cut-out. This also removes BiRefNet halo pixels.
- OmniSVG and StarVector add a 17 GB-class model for icon-level output that Claude already matches. Not worth it.

### Gaps
- No benchmark specifically on SVG **lettering** or wordmarks by LLMs. Claude's typographic SVG quality (kerning, letterforms without a font) is unmeasured; using real font files avoids the question.
- Recraft's official API price page was not fetched directly.

## 4. Mood boards and visual language with AI

### Takeaway
In 2026 designers use AI mainly to speed up the research and direction phase. Tools include Google Mixboard (Nano Banana-based, natural-language board edits), Adobe Firefly Boards, Midjourney V8.2 moodboards and personalisation, Miro AI, and niche palette and font-pairing tools (Ideatum). Hard evidence is thin: most sources are vendor or blog content. The pattern is images plus palette plus type plus a few direction words, with AI used to regenerate variations ("more like this") rather than to decide.

### Cited Findings
- Google Labs launched **Mixboard** on 24 Sept 2025 as a US public beta. Users start from text prompts, then edit by natural language ("make this brighter", "combine these two elements") and branch with "regenerate" or "more like this". It runs on Nano Banana. — [TechCrunch](https://techcrunch.com/2025/09/24/google-launches-an-ai-powered-mood-board-app-mixboard)
- Midjourney V8.2 (24 July 2026) focuses on aesthetics and personalisation. "Moodboards let a creator communicate a broader visual world rather than overloading a prompt with adjectives"; personalisation reflects learned taste. Its Edit Model works from up to four reference images. — [jackrighteous creator guide](https://jackrighteous.com/blogs/ai-art-visuals-creatives/midjourney-for-creators) (secondary)
- Listed 2026 moodboard tools include Inspo AI, Adobe Firefly Boards, Miro AI and Venngage AI. Ideatum makes "mood boards and style guides" from text, with colour palettes and font pairings exportable to Figma and Webflow. — [inspoai blog](https://www.inspoai.io/blogs/ai-moodboard-builder); [G2 Ideatum](https://ai.g2.com/marketplace/tools/ideatum); [Adobe Firefly moodboard use cases](https://www.adobe.com/uk/products/firefly/discover/ai-mood-board-use-cases.html)
- Practitioner framing: AI moodboards "accelerate the research phase" and do not replace judgement. Boards that took 4–8 hours now take minutes, and AI makes it cheap to show "three distinct directions". — [inspoai](https://www.inspoai.io/blogs/ai-generated-moodboard) (vendor blog; claims unverified)
- Gemini image models accept up to 3 **style** reference images (Nano Banana 2.1 and 3.1 Flash). That is a mechanism for carrying a board's look into later images. — [Gemini image docs](https://ai.google.dev/gemini-api/docs/image-generation)

### Inferences
- The tool already has a "language page" (IMPROVEMENTS F, `tool.language`). AI images could fill its mood section: material close-ups, a pattern swatch, an emblem sketch. Palette and type can then be drawn by the tool from real colours and fonts, so the board is exactly reproducible on the car. The board's AI images, palette swatches and font specimens can become the style references for every decal of that car.
- The project's rules forbid loading designs with "past cars or examples". AI mood images generated fresh from the user's words for each car respect that; a stock library of references would not.

### Gaps
- No rigorous study of AI mood boards improving design outcomes was found; sources are vendor blogs.
- Midjourney pricing and API availability not verified (historically subscription-only, no public API: unconfirmed here).
- Adobe Firefly Boards pricing and model licensing not checked.

## 5. Which approach fits: (a) procedural, (b) AI decals/patterns, (c) whole-car AI texturing, (d) hybrid

### Takeaway
The evidence points to **(d), a hybrid led by (a)**. Claude composes the livery procedurally on the fixed UV: layout, colour fields, lines from the mesh, real-font lettering and SVG emblems. AI images come in only as **content inside shapes the tool places**: illustrations, prints and tiles, grunge or material masks, and mood images. Whole-car AI texturing (c) is the worst fit. It loses layout control and exact edges, bakes lighting, seams and blurs at view resolution, garbles text, is non-deterministic, needs more VRAM than the PC has, and carries licence traps.

### Cited Findings
- Projection and multi-view texturing failures are stated by the 2026 papers themselves: "multiview inconsistency", "missing textures on unseen parts" (MV2UV), and "view consistency issues inherent in… multi-view diffusion" (Texture Space Material Diffusion). — [arXiv 2603.15436](https://arxiv.org/abs/2603.15436); [arXiv 2609.37654](https://arxiv.org/abs/2609.37654v1)
- Lighting is baked into textures in projection tools such as StableGen; PBR-separation research (MaterialMVP, LumiTex) exists because of it. — [StableGen](https://github.com/sakalond/StableGen); [MaterialMVP](https://arxiv.org/pdf/2503.10289)
- Hard-surface ceiling: Meshy rated 3.5/5. "No controllable texturing" without a logical UV layout. — [stacksheriff](https://stacksheriff.com/ai-tools/meshy-ai-review/); [ufo3d](https://ufo3d.com/?p=11629)
- Image models' own stated limits: FLUX.2 klein says text "may be inaccurate or subject to distortion". OpenAI lists text, brand-element consistency and "precise element placement" as weak spots. Every model fails past about 25–30 words. — [HF klein](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B); [OpenAI guide](https://developers.openai.com/api/docs/guides/image-generation); [invideo](https://invideo.io/blog/best-ai-model-text-in-images/)
- The professional AI livery example (NEOM McLaren) used text-to-image to make **artwork** that was then applied as a livery. It did not use whole-car 3D texturing. — [FIA Formula E](https://fiaformulae.com/en/news/473979)
- The tool already lays marks, text and decals "in the body's own unfolding… so it follows the panel's curve as a cut sticker does". — `tool/marks.py` docstring (local)
- Claude's SVG skill is near the top of blind-preference rankings. — [modelgrep / Design Arena](https://modelgrep.com/best/svg)

### Inferences
- **(a) Procedural, by Claude**
  - Strengths: exact edges, layout and mesh-following lines; deterministic, so the self-test works; fast; free; all in words.
  - Weaknesses: illustrative richness (organic art, painterly or camo prints, wear) can look like programmer art.
  - Failure modes: the tape and line problems already in IMPROVEMENTS H. These are geometry problems that AI texturing would not fix.
- **(b) AI images as decals and patterns, placed by the tool**
  - Strengths: rich art in the places the design chose. Klein runs locally, is licence-clean and takes about a second per image on a 16 GB card.
  - Failure modes:
    - Wrong or garbled text: never use it for words that must be exact.
    - Style drift between decals: fix by multi-reference conditioning on the mood board.
    - Cut-out halos: fix by vectorising or alpha-cleaning.
    - Resolution: 1–4 MP is sharp enough for one decal, not for a whole car.
    - Tile seams: already solved with the torus.
  - Determinism: keep the PNG with its prompt and seed (the tool already does) so rebuilds are byte-identical.
- **(c) Whole-car AI texturing, then cleanup**
  - Cleanup would mean repainting most of the car, since edges, layout and text are all wrong.
  - It contradicts the project's own rules: follow the car's flow from the mesh, no words the user didn't ask for, judge close up.
  - Possible narrow use: a throw-away **concept render** for the mood board, never the final texture. Even there, the language page plus (b) images covers it more cheaply.
- **(d) Hybrid**
  - Claude decides structure and writes it.
  - AI supplies textures and illustrations into masks the tool made: zones, marks, stripes.
  - Lettering stays in fonts and SVG.
  - This keeps the self-test (art files are inputs, like fonts) and adds only per-asset cost when a design asks for art. It does not add a step every skin pays for.

### Gaps
- No head-to-head study of these four strategies for game liveries exists. The recommendation rests on the stated failure modes and the tool's constraints.
- Not tested: whether AI-made grunge, carbon and other material masks look better in the game than procedural noise (`tool/noise.py`).

## 6. Running locally (Apple Silicon) vs the PC's GPU vs cloud

### Takeaway
FLUX.2 [klein] 4B runs on the Mac through mflux (MLX). That gives about 32 s per 1024² image (4 steps) on an M1 Max, and about 9 s at 512² with a 4-bit quant (4 GB instead of 16 GB). On an NVIDIA card it runs in about a second. Cloud APIs take seconds up to about 2 minutes for complex GPT Image prompts and cost about 1–21 cents an image, with no subscription for OpenAI, Google, BFL or Ideogram pay-as-you-go. The Mac route makes the picture maker usable where design happens; the PC stays the faster box.

### Cited Findings
- FLUX.2 klein 4B on an M1 Max with 64 GB, 4 steps:

  | Tool | Resolution | Wall time | Inference |
  |---|---|---|---|
  | mflux 0.17.5 | 1024² | 31.7 s | 21.4 s |
  | mflux 0.17.5 | 512² | 23.7 s | — |
  | iris.c | 1024² | 41.5 s | — |

  The test found image-to-image edits kept identity, with small details drifting. — [lilting.ch benchmark](https://lilting.ch/en/articles/flux2-klein-4b-mflux-iris-m1-max)
- A 4-bit mflux klein-4B runs about 9 s per 512² image at 4 steps and is about 4 GB on disk, against 16 GB in BF16. — [HF ar9av/FLUX.2-klein-4B-mflux-4bit](https://huggingface.co/ar9av/FLUX.2-klein-4B-mflux-4bit)
- **Conflict:** one aggregator claims about 85 s per 1024² image on an M4 Max and 12–18 s on an RTX 4090. That disagrees with the measured M1 Max figure above and with BFL's "under a second" on RTX 3090/4070+, and may refer to the 9B model or other settings. Low confidence. — [search summary (aicybr/lilting)](https://lilting.ch/en/articles/flux2-klein-apple-silicon); [HF klein card](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B)
- Other Mac ports exist: a Swift MLX port of FLUX.2 (flux-2-swift-mlx) and OminiX-MLX klein. — [GitHub flux-2-swift-mlx](https://github.com/VincentGourbin/flux-2-swift-mlx); [OminiX-MLX docs](https://www.mintlify.com/OminiX-ai/OminiX-MLX/image/flux-klein)
- StableGen supports Apple Silicon. Hunyuan3D-2.1 lists macOS but needs 21 GB for texturing. TRELLIS.2 is Linux and NVIDIA only (≥24 GB). — [StableGen](https://github.com/sakalond/StableGen); [Hunyuan3D-2.1](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1); [TRELLIS.2](https://github.com/microsoft/TRELLIS.2)
- Cloud latency: OpenAI says complex prompts "may take up to 2 minutes". — [OpenAI guide](https://developers.openai.com/api/docs/guides/image-generation)
- Pricing models: BFL is "No subscriptions, no seat fees". Gemini image models have no free tier, with batch at half price. Meshy, Tripo, Rodin and Recraft (for ownership) are subscriptions. — [bfl.ai/pricing](https://bfl.ai/pricing); [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing); [Meshy API pricing](https://docs.meshy.ai/en/api/pricing); [Recraft FAQ](https://recraft.ai/blog/ownership-and-commercial-use-faq)
- The PC has 16 GB RAM and a 16 GB card. The tool loads klein's text encoder and transformer (8 GB each) one after the other. — `tool/pictures.py` docstring (local)

### Inferences
- A Mac port of the picture maker via mflux (4-bit or 8-bit klein 4B) is realistic at roughly 10–30 s per image. That closes the "What the Mac lacks" item without changing the model, so the same Apache licence and the same outputs apply.
  - Bit-identical outputs between MLX and CUDA are **not** expected. Keep the kept PNG as the source of truth, not the seed.
- Cloud APIs make sense only per asset, for jobs klein does badly: exact-ish stylised wordmarks (GPT Image 2.x or Ideogram 4 with transparency) and high-fidelity illustrations. That means pennies per image, but sending the user's words out, which `pictures.py` currently promises it never does.

### Gaps
- The Mac's exact chip and RAM are unknown, so speed may differ from the M1 Max figure.
- mflux's current release number and date were not fetched directly (the benchmark used 0.17.5).
- Draw Things' FLUX.2 support, speed and price were not verified.

## Applicability to this tool

### Takeaway
Keep Claude-composed procedural design as the core, and keep the local FLUX.2 [klein] 4B picture maker but use it only inside shapes the design places. Add a Mac (mflux) path for it. Do lettering with real fonts and Claude-written SVG, never AI pixels. Drop whole-car AI texturing, Hunyuan3D, TRELLIS.2, OmniSVG and StarVector for this tool. Use AI images to populate the visual-language (brand book) page from the user's words. Any cloud model is an opt-in per asset, discussed with the user first because it sends their words out.

### Cited Findings
- Licence facts that decide it:
  - klein 4B is Apache 2.0. — [HF](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B)
  - Hunyuan excludes the EU, UK and South Korea and requires labelling outputs. — [LICENSE](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1/blob/main/LICENSE)
  - TRELLIS.2 texturing depends on non-commercial nvdiffrast. — [StableGen](https://github.com/sakalond/StableGen)
  - Qwen-Image 2.1 is research-only. — [datanorth](https://datanorth.ai/news/qwen-releases-qwen-image-2-1)
  - Recraft ownership needs a paid plan. — [Recraft](https://recraft.ai/blog/ownership-and-commercial-use-faq)
- Hardware facts: the PC's 16 GB card is below Hunyuan Paint's 21 GB and TRELLIS.2's 24 GB. — `tool/pictures.py`; [Hunyuan3D-2.1](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1); [TRELLIS.2](https://github.com/microsoft/TRELLIS.2)
- Text facts: every model fails past about 25–30 words, and the best is "logo length". — [invideo](https://invideo.io/blog/best-ai-model-text-in-images/)
- Claude is near the top on SVG. — [modelgrep](https://modelgrep.com/best/svg)

### Inferences
**Keep or strengthen**
1. **Procedural core (a).** Layout, colour fields, mesh-following lines, marks, `s.text` with real fonts, `s.mark` shapes.
   - Whole-car AI texturing would not solve the open problems (tape gaps, lines on edges): they are mesh geometry problems.
   - This keeps the byte-identical self-test.
2. **Local picture maker (FLUX.2 klein 4B + BiRefNet).** Keep it as the only default AI source.
   - It is licence-clean for skins shared online and needs no subscription.
   - Use it for illustrations, prints and tiles (torus tiling already works), and possibly material masks (grime, scuffs, camo) inside zones the design chose.
   - Make each car's decals look like one set by passing the language page's images as **multi-reference** inputs to klein, which supports multi-ref editing in the same model.
3. **Mac path.** Port the picture maker to mflux, 4-bit or 8-bit klein 4B. Expect about 10–30 s per image. Look up mflux's latest release first, per the project's rules.
4. **Lettering.** Keep words in real fonts, laid in the unfolding as the tool does now, plus Claude-written SVG for emblems, numbers and roundels.
   - AI-generated lettering only makes sense for a stylised wordmark the user asks for that no font can give (graffiti, hand-lettered). Then use one cloud call (GPT Image 2.x with `background: "transparent"`, or Ideogram 4 Transparent), check the spelling by eye or OCR, and vectorise with **vtracer** before placing.
5. **Visual language page.** Generate its mood images from the user's words, fresh each car, with the local klein. Draw palette and type specimens from the tool's own colours and fonts, so the board and the car share exact values. This is one optional step, paid only when a new car starts, so it does not cost every change.
6. **vtracer (MIT, pip).** Optional, to turn cut-out AI decals into clean flat-colour vectors, removing halo pixels and giving any-resolution edges.

**Drop or don't adopt**
- Whole-car AI texturing: Hunyuan3D Paint, TRELLIS.2 texturing, StableGen, Meshy, Tripo and Rodin retexture.
  - Reasons: no livery layout control, baked lighting and seams, garbled text, non-deterministic, VRAM above the PC's card.
  - Licences: Hunyuan excludes the EU/UK, TRELLIS.2 texturing is non-commercial, Meshy, Tripo and Rodin are subscriptions.
  - If ever wanted, Meshy's `enable_original_uv` is the one cloud option that keeps the game's UVs, at about 10 credits a try.
- OmniSVG and StarVector: icon-level, 17 GB-class, and Claude's own SVG matches or beats them.
- Qwen-Image 2.1 (research licence), FLUX.2 [dev] and [klein] 9B (non-commercial): not for skins shared online.
- Recraft: native SVG is attractive, but ownership needs a paid plan, which is a subscription. Discuss with the user first; Claude's SVG covers most needs.
- Gemini (Nano Banana 2.1, $0.034 an image) is cheap and good with references, but has no documented transparent output and carries a SynthID watermark. Fine for mood images, weaker for decals.

**Watch**
- FLUX 3 Image (1 Oct 2026). If its promised open weights arrive under Apache, re-evaluate against klein 4B.
- Texture-space generation research (NVIDIA's Texture Space Material Diffusion, MV2UV, UniTEX). If a release offers text- or image-conditioned **material and wear** generation directly in a given UV layout, it could fill the "finish" layer under procedural graphics. It is not ready as of October 2026.

### Gaps
- The user's country was not established; it decides whether Hunyuan-licensed models are usable at all.
- The cost in time of a mood-image step on the Mac has not been measured on the user's actual chip.
- The OpenAI, Google and Ideogram output terms for skins shared online need a direct read before any cloud use.
