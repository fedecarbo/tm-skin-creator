# Agent-driven creative tools: architecture, build vs buy, and gates (as of 2026-10-07)

Scope: how AI-agent-driven creative tools are built today, and what that means for a small Claude Code–driven
3D skin tool (Python "paint box" DSL + numpy painter + three.js Lab + hooks/gates). Local facts about the tool
were checked in the repo: `tool/` is 17,452 lines across 56 `.py` files; the paint box (`tool/paintbox.py`,
1,139 lines) exposes a `Skin` class with about 20 verbs (`paint`, `mark`, `peel`, `wear`, `glow`, `relief`,
`emboss`, `decal`, `scatter`, `text`, `placard`, ...) plus zone algebra in `shapes`/`marks`/`meshlines`; design
scripts (`skins/<name>/design.py`) are plain Python; the tool's venv runs Python 3.14.7 on the Mac and 3.14.2 on
the PC ([requirements.txt](../../requirements.txt)).

## 1. Current guidance on building agents and tools for agents (Anthropic, OpenAI), and Claude Code features in Oct 2026

### Takeaway
The consistent message from Anthropic (2024–2026) is: start with the simplest system, spend more effort on the
tool interface than on the prompt, make tools few, high-level and hard to misuse, keep context small and load
detail on demand, and close the loop with checks the agent can run itself, ideally graded by something other than
the agent that did the work. Claude Code in Oct 2026 has first-class machinery for exactly this (Stop hooks,
agent-type hooks, `/goal`, verification subagents, workflows, skills with progressive disclosure).

### Cited Findings
**Building effective agents (Dec 19, 2024)**
- "We recommend finding the simplest solution possible, and only increasing complexity when needed." Workflows (predefined code paths) are distinguished from agents (LLM directs its own process). — [Anthropic, Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
- Evaluator-optimizer pattern "is particularly effective when we have clear evaluation criteria, and when iterative refinement provides measurable value." — [same](https://www.anthropic.com/engineering/building-effective-agents)
- Agent-computer interface: "Put yourself in the model's shoes... A good tool definition often includes example usage, edge cases, input format requirements, and clear boundaries"; "Keep the format close to what the model has seen naturally occurring in text on the internet"; poka-yoke example: "We changed the tool to always require absolute filepaths—and we found that the model used this method flawlessly"; "We actually spent more time optimizing our tools than the overall prompt." — [same](https://www.anthropic.com/engineering/building-effective-agents)
- "Frameworks can help you get started quickly, but don't hesitate to reduce abstraction layers and build with basic components as you move to production." — [same](https://www.anthropic.com/engineering/building-effective-agents)

**Writing effective tools for agents (Sep 11, 2025)**
- Tools are "a contract between deterministic systems and non-deterministic agents"; "More tools don't always lead to better outcomes." Prefer consolidated tools: "Instead of implementing a `list_users`, `list_events`, and `create_event` tools, consider implementing a `schedule_event` tool"; "Instead of... `read_logs`... consider... `search_logs`... which only returns relevant log lines." — [Anthropic, Writing effective tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents)
- Namespacing related tools with common prefixes delineates boundaries. — [same](https://www.anthropic.com/engineering/writing-tools-for-agents)
- Return meaningful context; "eschew low-level technical identifiers (for example: `uuid`, `256px_image_url`, `mime_type`)"; offer a `response_format` enum (`"concise"`/`"detailed"`). — [same](https://www.anthropic.com/engineering/writing-tools-for-agents)
- Token efficiency: pagination, range selection, filtering, truncation with sensible defaults; Claude Code caps tool responses at "25,000 tokens by default"; when truncating or erroring, "steer agents with helpful instructions." — [same](https://www.anthropic.com/engineering/writing-tools-for-agents)
- Describe tools "to a new hire"; "clearly describ[e] (and enforc[e] with strict data models) expected inputs and outputs"; unambiguous names (`user_id` not `user`); "Even small refinements to tool descriptions can yield dramatic improvements." — [same](https://www.anthropic.com/engineering/writing-tools-for-agents)
- Evaluation-driven tool development: many realistic tasks (often needing dozens of tool calls), each with a verifiable outcome; track accuracy, runtime per tool call, number of tool calls, tokens, tool errors; read transcripts ("what agents omit in their feedback... can often be more important"); paste eval transcripts into Claude Code to refactor tools so "implementations and descriptions remain self-consistent." — [same](https://www.anthropic.com/engineering/writing-tools-for-agents)

**Effective context engineering (Sep 29, 2025)**
- Goal: "the smallest possible set of high-signal tokens that maximize the likelihood of some desired outcome"; context rot: performance degrades as context grows. — [Anthropic, Effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- System prompts at the "right altitude": avoid both "complex, brittle logic" and "vague, high-level guidance." Tools: avoid "bloated tool sets that cover too much functionality or lead to ambiguous decision points." Examples: "diverse, canonical examples" rather than a laundry list of edge cases. — [same](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- Just-in-time retrieval via "lightweight identifiers (file paths, stored queries, web links, etc.)"; compaction; structured note-taking outside the window; sub-agents return a "condensed, distilled summary of its work (often 1,000-2,000 tokens)." — [same](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)

**Code execution with MCP (Nov 4, 2025) — code vs many tool calls**
- Presenting tools as code APIs that the agent calls from code it writes cut one example from "150,000 tokens to 2,000 tokens—a time and cost saving of 98.7%"; benefits: progressive disclosure, filtering data in the execution environment, "familiar programming constructs replace chained tool calls," state persistence and reusable skills. Drawback: agent-written code needs "a secure execution environment with appropriate sandboxing, resource limits, and monitoring." — [Anthropic, Code execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp)

**Agent Skills (Oct 2025)**
- Skills are folders (SKILL.md + optional scripts/references/assets) loaded by progressive disclosure: metadata at startup, full SKILL.md when relevant, bundled files only as needed, so the bundled context is "effectively unbounded." — [Anthropic, Equipping agents for the real world with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) (via search summary)

**Demystifying evals for AI agents (Jan 9, 2026)**
- Grader types: code-based (fast, objective, "brittle to valid variations"), model-based (flexible, non-deterministic, need human calibration), human (gold standard, slow). Capability evals vs regression evals (regression held near 100%). — [Anthropic, Demystifying evals](https://anthropic.com/engineering/demystifying-evals-for-ai-agents)
- pass@k (at least one of k succeeds) vs pass^k (all k succeed); "grade what the agent produced, not the path it took"; "LLM-as-judge graders should be closely calibrated with human experts"; "You won't know if your graders are working well unless you read the transcripts"; start with "20-50 simple tasks drawn from real failures"; "An eval at 100% tracks regressions but provides no signal for improvement." — [same](https://anthropic.com/engineering/demystifying-evals-for-ai-agents)

**Claude Code best practices (docs as of Oct 2026)**
- "Give Claude a check it can run: tests, a build, a screenshot to compare... Without a check it can run, 'looks done' is the only signal available, and you become the verification loop." Four gating strengths: in one prompt; across a session with a `/goal` condition ("A separate evaluator re-checks it after every turn"); "As a deterministic gate: a Stop hook runs your check as a script and blocks the turn from ending until it passes"; "By a second opinion: a verification subagent or a dynamic workflow... has a fresh model try to refute the result, so the agent doing the work isn't the one grading it." — [Claude Code docs, Best practices](https://code.claude.com/docs/en/best-practices)
- "Have Claude show evidence rather than asserting success." — [same](https://code.claude.com/docs/en/best-practices)
- CLAUDE.md: "For each line, ask: 'Would removing this cause Claude to make mistakes?' If not, cut it. Bloated CLAUDE.md files cause Claude to ignore your actual instructions!"; "If Claude already does something correctly without the instruction, delete it or convert it to a hook"; `/doctor` proposes cuts for content derivable from the codebase. — [same](https://code.claude.com/docs/en/best-practices)
- "Unlike CLAUDE.md instructions which are advisory, hooks are deterministic and guarantee the action happens." — [same](https://code.claude.com/docs/en/best-practices)
- Adversarial review: a reviewer subagent "sees only the diff and the criteria you give it"; warning: "A reviewer prompted to find gaps will usually report some, even when the work is sound... Chasing every finding leads to over-engineering"; tell it to "flag only gaps that affect correctness or the stated requirements." — [same](https://code.claude.com/docs/en/best-practices)
- "If you've corrected Claude more than twice on the same issue in one session, the context is cluttered with failed approaches. Run /clear and start fresh." Writer/Reviewer pattern across sessions; "A fresh context improves code review since Claude won't be biased toward code it just wrote." — [same](https://code.claude.com/docs/en/best-practices)
- Features named in the Oct 2026 docs: auto mode (built-in starting permission mode from v2.1.283), `/goal`, `/verify`, `/code-review`, `/batch` (5–30 subagents in worktrees), `/btw`, `/rewind` checkpoints, plan mode, agent view (`claude agents`, research preview), agent teams (experimental, off by default), plugins and code-intelligence plugins ("automatic error detection after edits"), subagents with a `model:` field in `.claude/agents/*.md`. — [same](https://code.claude.com/docs/en/best-practices)

**Hooks reference (Oct 2026)**
- Events include SessionStart, UserPromptSubmit, PreToolUse (can block), PostToolUse (cannot block, but can replace tool output via `updatedToolOutput` or inject `additionalContext`), PostToolBatch, Stop (can block: "Prevents Claude from stopping, continues the conversation"), SubagentStop, FileChanged, InstructionsLoaded, PreCompact/PostCompact, TaskCompleted, etc. — [Claude Code docs, Hooks reference](https://code.claude.com/docs/en/hooks)
- Five handler types: `command`, `http`, `mcp_tool`, `prompt` (single-turn LLM evaluation, 30 s default timeout), and `agent` ("spawns a subagent that can use tools like Read, Grep, and Glob to verify conditions before returning a decision. Agent hooks are experimental and may change"). Blocking via exit code 2 or `decision: "block"` with a `reason`. — [same](https://code.claude.com/docs/en/hooks)

**OpenAI**
- OpenAI's practical guide recommends beginning with single-agent systems and moving to multi-agent only when necessary; agents = model + tools + instructions/guardrails; layered guardrails and human escalation when stuck. — [OpenAI, A practical guide to building agents (PDF)](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf) (via search summary; PDF not fetched)

**Structured, typed calls (Claude API, Oct 2026)**
- `strict: true` on a tool definition "guarantees `tool_use.input` validates exactly" against its JSON schema; structured outputs via `output_config.format`; on Opus 5.5 / Sonnet 5.5 forced `tool_choice` returns a 400, so use `auto` + `strict: true` or structured outputs. — [Anthropic claude-api skill reference bundled with Claude Code 2.1.292, model table cached 2026-09-25](/private/tmp/claude-501/bundled-skills/2.1.292/fe9b85447fda23239d2fe0666d23c293/claude-api/SKILL.md)

### Inferences
- The paint box is already in the shape Anthropic now recommends for heavy tool use: the agent writes code against a domain API rather than issuing dozens of separate tool calls (the "code execution with MCP" argument). The improvements are in the *grain* of that API (fewer, higher-level, poka-yoke verbs) and in what each call returns (concise, steering feedback), not in switching paradigms.
- "Random mistakes" maps to three documented causes: ambiguous tool surface (too many low-level ways to do one thing), context rot (long sessions with failed attempts), and self-grading (the agent judging its own output). Each has a documented remedy: consolidated poka-yoke verbs, fresh contexts/subagents, and an independent check (deterministic gate first, fresh-model review second).
- The project's existing rules ("repeated mistakes become hooks/gates", short CLAUDE.md, delete what's untrue) are fully aligned with the Oct 2026 Claude Code docs; the docs add Stop-hook gating and `agent`/`prompt` hook types the project may not be using yet.

### Gaps
- Google's agent guidance (e.g., Google's agents whitepaper / ADK docs) was not fetched; no claims made.
- Claude Code's default effort level for Opus 5.5 inside Claude Code was not confirmed (the API default is `medium`; see section 5).
- Exact semantics of `/goal` evaluation and dynamic workflows were not read beyond the best-practices summary.

## 2. Blender + AI agents: could Blender (headless `bpy` or MCP) replace the home-made 3D stack?

### Takeaway
LLM-driven Blender is real and active (two MCP servers including an official one from Blender Lab; research systems
like LL3M), but the evidence shows it is good at blocking out scenes and procedural assets, weak at precise spatial
placement, and unsandboxed; nothing found shows it doing precise livery painting on an existing UV-mapped car
better than a purpose-built tool. Blender's real value here would be narrow: baking (AO/curvature/masks), higher-
quality preview renders, and decal projection, run headless. It costs a large install and a Python version split
(bpy wheels need Python 3.13; the tool runs 3.14).

### Cited Findings
**blender-mcp (community, now "MCP for Blender")**
- Blender add-on + Python MCP server letting Claude control Blender; tools include `execute_blender_code`, `look` (viewport/camera/multi-angle views), `get_scene_info`, `generate_3d` (Tripo, Hunyuan3D, Hyper3D Rodin), asset search/import (Poly Haven, Sketchfab, Poly Pizza); Blender 3.0+, Python 3.10+, `uv`; macOS/Linux/Windows; MIT; PyPI `mcp-for-blender`; ~30.2k stars. Warning: "The `execute_blender_code` tool allows running arbitrary Python code in Blender... ALWAYS save your work before using it"; "Sometimes the first command won't go through"; complex operations need breaking into smaller steps. — [GitHub ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp)
- Tool counts conflict between sources: ~10 tools ([ChatForest review](https://chatforest.com/reviews/blender-mcp-server/)), 9 primary tools ([GitHub README](https://github.com/ahujasid/blender-mcp)), 36 tools ([StraySpark comparison](https://www.strayspark.studio/blog/official-blender-mcp-server-comparison-2026)); star count also differs (21.2k in an [AUR/aggregator snippet](https://aur.archlinux.org/packages/blender-mcp-git) vs 30.2k on GitHub). The project renamed itself on Sep 16, 2026 to avoid confusion with the official server. — [StraySpark](https://www.strayspark.studio/blog/official-blender-mcp-server-comparison-2026)
- Review (Aug 24, 2026): "For simple scenes — a table with objects on it, a basic landscape, architectural block-outs — the results can be surprisingly good"; screenshot feedback loop valuable; but "LLMs are language models, not spatial reasoning engines": struggles with precise positioning, proportions, complex geometry; coherence degrades with complexity; `execute_blender_code` uses unrestricted `exec()` "unchanged as of August 24, 2026"; socket on port 9876 can drop, timeouts on complex operations. Rated 4.0/5. — [ChatForest review](https://chatforest.com/reviews/blender-mcp-server/)
- StraySpark reports an opt-in safe mode (`BLENDER_MCP_SAFE_MODE=1`, blocks file access, subprocesses, network) and that the socket has no authentication or encryption — partly contradicting ChatForest's "no sandboxing" (possibly a later change). — [StraySpark](https://www.strayspark.studio/blog/official-blender-mcp-server-comparison-2026) vs [ChatForest](https://chatforest.com/reviews/blender-mcp-server/)

**Official Blender Lab MCP server**
- Lives at projects.blender.org/lab/blender_mcp; v1.0.0 on Apr 27, 2026, v1.0.3 on Sep 11, 2026 (screenshot fix). Anthropic announced nine creative-tool connectors on Apr 28, 2026: "The Blender developers have created an MCP connector, which is now officially available for Claude." — [StraySpark](https://www.strayspark.studio/blog/official-blender-mcp-server-comparison-2026); [a2a-mcp listing](https://a2a-mcp.org/entry/blender-lab-mcp-server)
- 26 tools: code execution, blend-file summaries, object/collection info, screenshots, viewport navigation, and search over bundled API reference and manual; six `_for_cli` variants that "open a `.blend` in a background Blender process"; executes code "without any guards", recommends a VM; requires Blender 5.1+; oriented to analysis rather than creation. — [StraySpark](https://www.strayspark.studio/blog/official-blender-mcp-server-comparison-2026)

**LL3M (UChicago, Aug 2025) — multi-agent LLMs writing Blender code**
- Six agents: planner (GPT-4o), retrieval over a Blender API RAG (GPT-4o), coder (Claude 3.5 Sonnet), critic and verifier (Gemini 2.0 Flash on 5 rendered views), user proxy. With RAG: 2.43 execution errors per asset vs 3.29 without (−26%), and 5.86× more complex Blender operations. — [LL3M, arXiv 2508.08228](https://arxiv.org/html/2508.08228v1); [code](https://github.com/threedle/ll3m)
- Timing: ~4 min initial creation + ~6 min auto-refinement; ~38 s per user-guided edit; 59% of single-prompt edits succeed, others need 3–4 follow-ups; refinement edits code locally rather than regenerating. Failure modes: VLM critique "occasionally misses spatial artifacts" (e.g., disconnected geometry), relative positioning needs several iterations. — [LL3M](https://arxiv.org/html/2508.08228v1)

**`bpy` as a Python module**
- Latest `bpy` 5.2.2 (Sep 15, 2026); releases 5.0.0 (Nov 2025) through 5.2.x (Jul–Sep 2026); requires "Python ==3.13.*"; wheels: macOS arm64 245.2 MB, Windows x86-64 338.2 MB, Linux 401.7 MB. Each Blender release supports one Python version; older versions drop off PyPI. — [PyPI bpy](https://pypi.org/project/bpy/)
- Local check: the tool's venv is Python 3.14.7 (Mac) / 3.14.2 (PC), so `bpy` cannot be imported into it; it would need a separate 3.13 venv or a Blender install driven with `blender --background --python`. — local check of the venv and [requirements.txt](../../requirements.txt)

**AI texturing on an existing model (the "buy" alternatives for painting)**
- StableGen: open-source Blender plugin projecting SDXL/FLUX.1-dev textures onto models via a ComfyUI backend, guided by ControlNet (depth) and IPAdapter (image style references). — [StableGen (GitHub)](https://github.com/Zaws77/StableGen); [CTU thesis record](https://dspace.cvut.cz/handle/10467/123567)
- Dream Textures (Stable Diffusion in Blender: tiling, depth-to-image projection) and Diffused-Texture-Addon exist as similar add-ons. — [SourcePulse: dream-textures](https://www.sourcepulse.org/projects/586194); [SourcePulse: diffused-texture-addon](https://www.sourcepulse.org/projects/26341409)
- Meshy-5 Retexture: text (max 600 characters) or image prompt → PBR textures on an uploaded model, can keep the original UVs; 3–5 minutes per job; paid API. — [fal.ai Meshy v5 Retexture](https://fal.ai/models/fal-ai/meshy/v5/retexture/api); [Meshy docs](https://docs.meshy.ai/en/webapp/guides/3d-model/ai-texturing)

**Trackmania community practice**
- Nadeo's official stadium-car resources contain UV maps per texture set, the 3D model, and baked maps; `_R` maps use red = roughness, green = metalness; Skin_CoatR handles clearcoat/glitter. Community creators commonly pair Substance Painter with Blender for previews; Blendermania is a Blender add-on for Trackmania content. — [devtrackers: stadium car resources](https://devtrackers.gg/trackmania/p/3490d99c-stadium-car-ressources-all-you-need-to-create-skins-for-the-stadium-cars); [Blendermania](https://blender-addons.org/blendermania/)
- The repo already contains `SkinTemplate2021_V2.1.spp` (a Substance Painter project); Substance Painter is an Adobe product (subscription or Steam licence; price not checked here). — local repo listing

### Inferences
- Blender MCP's core loop (LLM writes `bpy` code, looks at a screenshot, fixes) is the same loop the tool already runs with its own paint box and Lab, but with a general API that has thousands of entry points, version drift per release, and no domain knowledge of the CarSport's parts and lines. LL3M needed a dedicated API-RAG agent just to cut errors to ~2.4 per asset. For a single fixed car, a narrow domain API should produce fewer mistakes than general `bpy`, by the same "few high-level tools" argument as in section 1.
- Where Blender would genuinely save code: offline baking (AO, curvature, thickness, edge masks), Cycles/EEVEE turntable renders for review, and projecting decals; jobs that run once per car or once per mesh, not per brush stroke. Running these headless through Blender's own bundled Python (`blender -b -P script.py`) sidesteps the 3.13/3.14 split and keeps the main venv unchanged; cost is roughly a 250–400 MB install per machine plus Blender startup (seconds) per run, and keeping scripts working across Blender releases (5.0→5.2 in under a year).
- Diffusion texturing (StableGen, Meshy) is the wrong tool for crisp livery lines that must follow mesh features (projection seams, no exact edges, no control of where a line lands), but could feed the "art"/"print" layers where the tool already uses a picture maker (FLUX.2 klein on the PC).
- MCP servers in both forms are unsandboxed code execution in a GUI app; the official one recommends a VM. That's acceptable for a personal machine but should not be allowed to touch the game's skin folder (the existing guard hook would need to cover Blender scripts too).

### Gaps
- No published benchmark was found of LLM+Blender on *texture painting onto an existing UV-mapped model* (as opposed to modelling or procedural materials).
- Blender app download sizes and headless startup times on these two machines were not measured.
- Whether bpy wheels exist for Python 3.14 in a future Blender release (5.3/6.0) was not checked.

## 3. "AI designs, human picks by eye" products in 2026: interaction patterns

### Takeaway
The dominant patterns are: generate several directions at once and lay them side by side on a canvas; let the
person point at a region and ask for a change there (local edits, not regeneration); preserve the person's
structure/intent while varying the surface (sketch-to-render "listens to the designer"); and keep everything on one
infinite canvas or board. Users explicitly ask for versioning/branching of AI iterations. Most of these products are
subscriptions.

### Cited Findings
- Car designers in 2026 group AI tools into LLMs, text-to-image (Midjourney, Nano Banana), sketch-to-image (Vizcom, Krea iPad) and sketch-to-3D (Vizcom); "Vizcom is emerging as the clear winner in the automotive/industrial design field"; DAF's design director: "I am positively surprised with how well Vizcom listens to designers." Complaints are about fragmentation (wanting AI inside Alias, 2D→3D→VR continuity). (Mar 30, 2026) — [Car Design News, AI in car design 2026](https://www.cardesignnews.com/design-tools/ai-in-2026-cutting-through-the-confusion/2638055)
- Vizcom's selling point is control: sketch-to-render that preserves "edges, proportions, and designer intent," real-time rendering for proportion/surface/lighting, specified finishes (e.g., glossy automotive paint), and exportable 3D. — [Vizcom for Automotive](https://vizcom.com/solutions/automotive) (via search summary); reviews e.g. [Lipi AI review](https://lipiai.blog/vizcom-ai-review/)
- Figma Make "point and edit": select a specific element, an "Ask for changes" box opens, the prompt applies only there ("handy if you only want to tweak one card instead of all of them"). Figma's agent can "generate multiple layout directions from one prompt... right in the canvas." — [Banani, 2026 Figma AI review](https://www.banani.co/blog/figma-ai-features-review); [Figma variation generator](https://www.figma.com/solutions/variation-generator/)
- Figma forum users request "structured version control / iteration branching for AI workflows" in Figma Make (title of a feature request; content not read). — [Figma forum](https://forum.figma.com/suggest-a-feature-11/figma-make-structured-version-control-iteration-branching-for-ai-workflows-51303)
- Adobe Firefly Boards: infinite canvas to generate image variations, collect, arrange, align, annotate with text/shapes; Firefly plugin edits images in Figma with text prompts. Pricing (as of Sep 2026): $9.99/month (2,000 credits) to $199.99/month (50,000 credits) — subscription. — [Adobe Help, Firefly Boards](https://helpx.adobe.com/firefly/web/create-mood-boards/firefly-boards/add-artboards-to-the-canvas.html); pricing from [Krea's blog](https://www.krea.ai/blog/is-adobe-firefly-free-what-it-is-and-how-it-compares-in-2026) (a competitor; treat as indicative)
- Krea: real-time generation for fast visual exploration, with a Figma plugin. — [Figma resource library, AI design tools](https://www.figma.com/resource-library/ai-design-tools/) (via search summary)
- LL3M's research interface similarly mixes text-prompt edits and direct code-parameter edits, and keeps the code so edits are local. — [LL3M](https://arxiv.org/html/2508.08228v1)

### Inferences
- The Lab already implements the strongest of these patterns (notes/drawings placed on the car reaching Claude = point-and-edit; option sets = side-by-side variations). The gaps relative to products are: (a) edits that are guaranteed local (only the region/layer pointed at changes, everything else byte-identical), which is easy to enforce in a code DSL by diffing textures outside the pointed region; and (b) visible branching of takes (which version a take came from) so "back to the earlier one" is one click.
- Product evidence favours *control over surprise* for designers (Vizcom over Midjourney). For a non-technical user judging by eye, that argues for deterministic, repeatable paint operations with the creativity in Claude's choices, not stochastic texture generation.

### Gaps
- No credible, current hands-on reviews were fetched for Spline AI, Tripo Studio or Meshy's web studio interaction design; only Meshy's retexture API docs.
- No quantitative study found on how many side-by-side options are optimal for picking by eye.

## 4. Code health in AI-written codebases, and LLM "random" mistakes

### Takeaway
Industry data shows AI-heavy codebases drift toward duplication and away from refactoring, and errors get masked;
the practical counters are explicit consolidation budgets, automated tripwires (duplicate detection, error-masking
checks), typed/strict interfaces, regression tests as hard gates, and evals built from real failures. "Random"
mistakes are better treated as a reliability rate (pass^k) to be pushed up by narrowing the interface and gating
outputs deterministically, than as something more instructions can remove.

### Cited Findings
- GitClear (623M code changes, 2023–2026): duplicated blocks up 81% since 2023; copy/paste now 15.7% of changed lines (9.4% in 2022); error-masking constructs up 47%; two-week churn up 15%; cross-file function calls down 35%; refactored ("moved") code fell from 13% (2023) to 3.8% of changed lines by mid-2026; ~5× more likely to duplicate than refactor. Recommendations: budget for refactoring, "duplicate-block detection as automated tripwires," explicit error-masking reviews, measure structural health alongside velocity. (Page dated Jan 2026 but quotes mid-2026 figures, so it has been updated.) — [GitClear, The Maintainability Gap](https://www.gitclear.com/the_ai_code_quality_maintainability_gap)
- A study of 3.52M AI-generated C++ changes (Apr 2025–Apr 2026) found higher interface/coupling burdens and a reliance on explicit loops over standard APIs. — [arXiv 2608.06640](https://arxiv.org/pdf/2608.06640) (via search summary; not fetched)
- Productivity: METR's 2025 RCT found experienced developers 19% slower with AI while believing they were 20% faster; METR's 2026 update reports a directional shift to an ~18% speedup and internal Claude Code telemetry of 1.5×–13× time savings on assisted tasks. — [Birchtree summary of METR update](https://birchtree.me/blog/an-update-from-the-study-that-said-devs-were-actually-slower-with-coding-agents/) (secondary source; METR's own post not fetched)
- Evals: begin with 20–50 tasks from real failures; regression evals near 100%; combine code-based, model-based and human graders; use pass^k for reliability. — [Anthropic, Demystifying evals](https://anthropic.com/engineering/demystifying-evals-for-ai-agents)
- Strict schemas: `strict: true` guarantees tool inputs validate against the schema; structured outputs constrain response format. — [claude-api skill reference](/private/tmp/claude-501/bundled-skills/2.1.292/fe9b85447fda23239d2fe0666d23c293/claude-api/SKILL.md)
- Poka-yoke tool design (absolute paths) removed a class of model errors entirely. — [Anthropic, Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
- Claude Code docs: code-intelligence plugins give "automatic error detection after edits"; hooks guarantee actions that instructions only advise; reviewer subagents should flag only correctness/requirement gaps to avoid over-engineering. — [Claude Code best practices](https://code.claude.com/docs/en/best-practices)

### Inferences
- For this repo the GitClear pattern is the risk to watch: 56 files written in two weeks with 23 already retired means high churn; duplication between e.g. `marks`, `shapes`, `meshlines`, `course`, `seams`, `segment` is the likely place where parallel ways of doing the same thing grow (and parallel ways are exactly what makes the agent pick inconsistently).
- "Randomness" has two separable sources: (1) the model choosing among many valid-looking ways to express an intent (fixable by narrowing the API so only one way exists), and (2) execution accidents the model can't see (tape gaps, facing flips; fixable only by checks that compute them). Instructions address neither reliably; the docs and the project's own memory ("gates, not rules") agree.
- A byte-identical self-test is a strong regression gate for the *machinery* but says nothing about *design* quality; a small "failure eval" set (the cases the user rejected, each with a computed check) is the missing middle layer.

### Gaps
- No controlled study found specifically on AI-written *Python graphics/numpy* code health or on golden-image testing for agent output.
- The C++ study and METR update were read only via summaries.

## 5. Model choice and cost (Oct 2026), and cheaper models/subagents for checks

### Takeaway
Opus 5.5 ($4/$20 per M tokens, 1M context, high-resolution vision) is the current default and cheaper per solved task
than Opus 5; Fable 5.1 ($10/$50) is the most capable widely released model; Sonnet 5.5 ($2/$10) and Haiku 4.5
($1/$5, 200K context) are the cheaper tiers. Research on VLM judges shows even the best models trail trained humans
at spotting fine 3D defects and that the evaluation setup (views, rubric) matters as much as the model, so cheaper
models suit mechanical checks, not taste.

### Cited Findings
- Prices per million input/output tokens: Fable 5.1 $10/$50 (1M context); Opus 5.5 $4/$20 (1M); Opus 5 $5/$25; Sonnet 5.5 $2/$10 (1M); Sonnet 5 $2/$10; Haiku 4.5 $1/$5 (200K). Opus 5.5 launched Sep 22, 2026. — [claude-api skill reference, model table cached 2026-09-25](/private/tmp/claude-501/bundled-skills/2.1.292/fe9b85447fda23239d2fe0666d23c293/claude-api/SKILL.md); corroborated by [BenchLM pricing (Oct 2026)](https://benchlm.ai/anthropic/api-pricing) and [DevTk.AI](https://devtk.ai/en/blog/claude-api-pricing-guide-2026/)
- Opus 5.5: thinking always on, effort is the control, API default effort `medium` (one level below Opus 5's `high`); "On many coding, analysis, and vision tasks, Claude Opus 5.5 at its default effort matched or beat Claude Opus 5 while using fewer tokens... expect the cost per solved task to be significantly lower." — [claude-api skill, model-migration guide](/private/tmp/claude-501/bundled-skills/2.1.292/fe9b85447fda23239d2fe0666d23c293/claude-api/shared/model-migration.md)
- Vision (Opus 4.7 onward, incl. Opus 5/5.5, Sonnet 5): up to 2576 px on the long edge, up to ~4,784 image tokens per image, coordinates 1:1 with pixels. For Opus 5/5.5: "give it tools, not more thinking... giving it tools to iteratively analyze, crop, and visually verify its own work"; for the densest inputs a container with PIL/OpenCV or "a cropping tool alone still helps"; Opus 5.5 reads charts/diagrams/screenshots "considerably more precisely out of the box, so harness scaffolding built for visual inputs on earlier models may no longer be needed - re-test it." — [same](/private/tmp/claude-501/bundled-skills/2.1.292/fe9b85447fda23239d2fe0666d23c293/claude-api/shared/model-migration.md)
- Effort guidance: `low` for subagents or simple tasks; "lower effort on the newest models often matches or exceeds prior-generation performance at high effort"; caches are model-scoped, so multi-model cascades lose cache reuse; judge "cost per completed task, not per request." — [claude-api skill](/private/tmp/claude-501/bundled-skills/2.1.292/fe9b85447fda23239d2fe0666d23c293/claude-api/SKILL.md)
- Claude Code subagents can pin a model in their definition (`model: opus` in `.claude/agents/*.md`). — [Claude Code best practices](https://code.claude.com/docs/en/best-practices)
- 3D-DefectBench (12 VLMs incl. Claude Opus 4.7, Sonnet 4.6, Haiku 4.5, GPT-5.4, Gemini 3.1 Pro): best VLM 0.298 MCC on geometry defects vs 0.519 for humans; texture: best VLM 0.406 MCC on expert labels (dropping to 0.168 on noisier silver labels); a compact six-view oblique turntable matched 14-view protocols ("neither denser camera protocol earned its cost"); RGB essential; rubric-guided checklist prompts gave modest gains; treat VLM judges as "configurable measurement systems" calibrated to human labels. (arXiv v2, Oct 6, 2026) — [3D-DefectBench, arXiv 2607.10826](https://www.alphaxiv.org/abs/2607.10826)
- A cross-model VLM-judge protocol (fixed 24-view headless render rig, two judge families, position-bias correction) found inter-judge kappa 0.66; cheap proxies such as geometry validity or render-CLIP were weak (render-CLIP at chance). — [arXiv 2606.18451](https://arxiv.org/pdf/2606.18451) (via search summary)
- LL3M used a cheap fast VLM (Gemini 2.0 Flash) as critic and it "occasionally misses spatial artifacts." — [LL3M](https://arxiv.org/html/2508.08228v1)

### Inferences
- Cost of a visual review: six renders at the 4,784-token cap ≈ 28.7k input tokens ≈ $0.11 on Opus 5.5 or $0.29 on Fable 5.1 per review (plus output); negligible against the user's stated "cost no object", so model choice for visual critique should be by quality, not price. Time (tens of seconds) matters more than money.
- Use Haiku 4.5/Sonnet 5.5 only where the answer is mechanically checkable (parsing logs, summarising check output, routing). For "does this look wrong?" use the strongest available model in a fresh context, with crop/zoom, and treat its output as flags for the user/eye, not a pass/fail gate, given VLMs still trail humans on fine defects.
- Claude Code usage itself is normally via a Pro/Max subscription or API billing; the user's preference against subscriptions conflicts with nothing new here, since Claude cost is declared "no object".

### Gaps
- Claude Code's default effort for Opus 5.5 inside the CLI was not verified.
- No benchmark found that includes Opus 5.5 or Fable 5.1 as 3D-defect judges (3D-DefectBench's newest Claude is Opus 4.7).
- Claude Pro/Max plan prices in Oct 2026 were not checked.

## 6. Applicability to this tool

### Takeaway
Keep the custom core (paint box DSL, numpy painter, Lab, installer/guard): it is the shape current guidance
recommends, and nothing off the shelf paints precise liveries on this car. Change the *grain* of the paint box
(fewer, higher-level, mistake-proof verbs that return steering feedback), move "random mistakes" into a layered gate
stack (static types → in-API contracts → computed defect checks → fresh-context visual review → the user's eye), and
use Blender only as an optional headless baker/renderer if a specific need appears. Put a hard ceiling on code growth.

### Cited Findings
(Recommendations below rest on the findings in sections 1–5; key anchors repeated.)
- Few consolidated, poka-yoke tools; steering errors; concise/detailed responses. — [Writing tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents); [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
- Code-calling-an-API beats chains of tool calls for context and control flow. — [Code execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp)
- Stop hook as a deterministic gate; second-opinion subagent so the worker isn't the grader; show evidence. — [Claude Code best practices](https://code.claude.com/docs/en/best-practices); [Hooks reference](https://code.claude.com/docs/en/hooks)
- Evals from 20–50 real failures; pass^k for reliability. — [Demystifying evals](https://anthropic.com/engineering/demystifying-evals-for-ai-agents)
- Six-view RGB + rubric checklist is the cost-effective VLM-judge setup; VLMs trail humans. — [3D-DefectBench](https://www.alphaxiv.org/abs/2607.10826)
- Duplicate detection and error-masking checks as tripwires. — [GitClear](https://www.gitclear.com/the_ai_code_quality_maintainability_gap)
- bpy needs Python 3.13, 245–338 MB wheels; Blender MCP is unsandboxed and weak at precise placement. — [PyPI bpy](https://pypi.org/project/bpy/); [ChatForest](https://chatforest.com/reviews/blender-mcp-server/)

### Inferences (concrete recommendations, with trade-offs)

**A. What to keep custom**
1. *The paint box as a Python DSL that Claude writes against.* It matches the code-as-action pattern, keeps designs editable and diffable (LL3M's argument for code as the representation), and lets edits be local. Trade-off: Claude can still write any Python; the fix is to narrow what the API accepts (B), not to replace code with JSON tool calls.
2. *The numpy painter and texture packer* (DDS/format, `_R` channel conventions, install with sha256 guard). Nothing off the shelf targets CarSport's UV sets; Substance/Blender would add a second source of truth.
3. *The Lab.* It already implements the two strongest product patterns (point-and-edit notes on the car, side-by-side options). Add: (a) a "local edit" guarantee: when the user points at a region, a gate diffs the new textures against the old and flags changes outside that region/layer; (b) lineage of takes (which take each came from) so going back is one click.

**B. How to shape the paint box for an LLM caller**
1. *One verb per intent, no stitching.* Replace "build a line from pieces" with verbs that take an identifier of a whole model line (or "beside line X at d cm") and do face choice, edge crossing and continuity internally, so the stitched-line failure in the tape diagnosis can't be expressed. This is the `schedule_event` / absolute-path move.
2. *Identifiers, not coordinates.* Part names, zone names and line IDs come from `car/parts.json` / the mesh's line list as `Literal`/`Enum` types; free 3D coordinates only where the idea needs them. Wrong names fail at type-check time with a "did you mean" list.
3. *Typed public surface + a stub.* Full type hints (or a `.pyi`) on `Skin` and the zone/line helpers, and run pyright/mypy on `skins/*/design.py` from a PostToolUse hook on Write/Edit (seconds, every skin, so check its time against the "every skin pays" rule — it should be well under the paint time). Consider a Claude Code code-intelligence plugin for in-editor diagnostics.
4. *Every verb returns a short receipt.* What it painted (part, area in cm², texels), what it refused, and any accident found (gap, flip, off-mesh), phrased to steer ("tape left the mesh at the hood seam: use line `hood_edge_L` whole, or `beside=`"). `summary()` stays concise by default with a detailed mode.
5. *Fewer verbs, not more.* Every new verb is a new ambiguity for the model. When two verbs overlap (`text`/`placard`/`emboss`/`decal` are candidates), merge behind one verb with a parameter. Keep the skill's reference to signatures + 1–2 canonical examples per verb, loaded on demand (progressive disclosure), not a growing prose manual.

**C. How to structure gates (cheapest and most deterministic first)**
1. *Static* (seconds): type-check of the design script; banned constructs (e.g., raw coordinate stitching) via a PreToolUse/PostToolUse hook.
2. *In-API contracts* (free at run time): the paint box raises on accidents it can compute (tape gaps above N texels, facing flips along a band, marks crossing a seam unless `across=True`). "A check names an accident, never a design" stays the rule.
3. *Regression* (already strong): the byte-identical self-test for machinery changes. Add a small failure eval: each user-rejected defect (tape gaps, stepped seams, bolts-by-rule) becomes a fixture whose computed check must pass on every tool change; aim for ~20–50 over time, measured as pass^k across repeated design attempts, not one lucky run.
4. *Stop-hook gate on "shown"*: Claude can't end a turn that claims a skin is ready unless the build artefacts are newer than `design.py`, the checks ran, and their output is attached (evidence, not assertion). Mind the cap on consecutive Stop blocks.
5. *Fresh-context visual review* (tens of seconds, roughly $0.10–0.30 per review): a subagent (or experimental `agent` hook) on the strongest model gets six fixed oblique renders plus crop/zoom, a short rubric (gaps, seams, stretched decals, untouched parts, lines off the car's flow) and the user's words, never the designer's reasoning; it returns flags only. Run it on picked takes and the final car, not every take (matches "one paint and a look per take"). Calibrate the rubric against the user's past verdicts; never let it overrule the user's eye.
6. *The user's eye in the Lab* remains the only design gate.

**D. Blender: build vs buy**
- Don't replace the 3D stack with Blender/MCP: more surface area, version drift (5.0.0 in Nov 2025 to 5.2.0 in Jul 2026), Python 3.13 vs the tool's 3.14, 250–400 MB per machine, unsandboxed exec, and documented weakness at precise placement. Buying it would replace a narrow API the model handles well with a broad one it handles less well.
- Possible narrow use, only when a concrete need is shown to the user: a headless Blender job (`blender -b -P`, Blender's bundled Python, invoked by one tool command) to bake AO/curvature/edge masks once per mesh, or to render higher-quality review turntables. Cost: one install per machine and seconds per run; benefit only if those maps or renders visibly beat the current ones. Extend the game-folder guard to cover it.
- Diffusion texturing (StableGen, Meshy Retexture at 3–5 min/job, paid API) doesn't suit crisp, line-following liveries; at most a source for "art" layers next to the existing picture maker.

**E. Code size and coherence**
- Add tripwires as gates, not rules: a duplicate-block detector over `tool/` and a grep for error-masking patterns (bare `except`, `except Exception: pass`) run with the self-test; a size budget (e.g., `tool/` line count may not grow in a commit unless the commit message names why), so consolidation is the default move.
- Schedule consolidation passes in the queue (GitClear's "budget for refactoring"): merge overlapping modules (line/shape/mark helpers) behind the smaller paint-box surface from B. Trade-off: every merge must keep every car's game files byte-identical (the self-test already enforces this).

**F. Models and sessions**
- Main design session: Opus 5.5 at a raised effort for design turns (the API default is `medium`); consider Fable 5.1 for the visual reviewer or for hard first designs since cost is no object; Haiku 4.5/Sonnet 5.5 only for mechanical summarising. Keep one model per long session for cache reuse.
- Fight context rot structurally: after two failed corrections on the same defect, restart from a fresh session with the skin's notes (the docs' `/clear` rule), and keep investigation in subagents that return short summaries.

### Gaps
- None of the recommended gates has been measured on this repo's timings (type-check, duplicate scan, six-view render + review); per the project's rules each should be timed before adoption.
- Whether Blender bakes would visibly improve on the tool's current maps is unknown without a side-by-side on the car.
