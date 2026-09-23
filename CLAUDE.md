# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@BRIEF.md

## Where things stand

- **Phase: building the tool.** `CHECKLIST.md` tracks progress. Read it at the start of every
  session and carry on from the first unticked checkpoint. Building starts only after the user
  has reviewed it (checkpoint 0).
- There's no code yet, so there are no build, run or test commands. Add them here as soon as
  they exist.
- Record technical decisions in the repo (this file, `CHECKLIST.md` or the code), so the next
  cold session finds them.
- Before adding any tool or library, look up its latest release and use that version, then
  record it. If a paid option would be far better, tell the user and discuss it before using it.

## Talking to the user

- Use plain words. Leave code, file names, paths and jargon out of replies unless they ask.
- Show rather than describe. A preview picture beats a paragraph.

## Don't look in the game's skin folder

`C:\Users\fedec\OneDrive\Documents\Trackmania\Skins\Models\CarSport\`

- It holds skins the user made outside this project. They are **not** reference designs or
  examples of good practice. Never list, open, read, copy or unzip anything there by any
  means: tools, shell or scripts. Never let them shape a design or technical choice. Work
  from `official/`, Nadeo's documentation and your own research.
- `.claude/settings.json` denies Claude's file tools on that folder. That also stops the Write
  tool from creating files there. Shell commands and scripts aren't covered, so the rule
  above is what stops them. Don't work around the deny.
- The only thing that writes there is the tool's install step, which isn't built yet. It holds
  the folder path in its own code. It checks only whether its exact target file name is free,
  and it never overwrites or deletes a file this project didn't create.

## Source assets (`official/`)

Leave the zips unchanged: `official/SOURCES.md` records their sha256. Extract them to a working
folder and never edit them in place. They're git-ignored because the GitHub repo
(`fedecarbo/tm-skin-creator`) is public. A fresh clone downloads them from the links in
`SOURCES.md`.

- `CarSport-Template.zip` (from Nadeo): `ReadMe.txt` and the flat UV maps `UV_Skin.png`,
  `UV_Skin_Hollow.png` and `UV_Details_Hollow.png` (2048×2048), plus `UV_Details.png`. That one
  is **2018×2018**, so scale it before overlaying.
- `CarSport-Model.zip` is a community upload on Sketchfab. It is **CC-BY-4.0, so credit the
  author, amogusstrikesback2,** wherever you reuse the model. It holds `textures/*.png` and a
  nested `source/StadiumCAR2020_OffsetFix.zip`, which contains the FBX mesh and the unpainted
  DDS textures (`Skin_*`, `Details_*`, `Wheels_*`, `Glass_*`). The main textures are 2048×2048.

## Skin texture format (from Nadeo's `ReadMe.txt`)

DDS files are required. They must use legacy D3D9 headers (FourCC `DXT1`, `DXT5`, `ATI1` or
`ATI2`), not DX10 headers.

| File | Compression | Content |
|---|---|---|
| `Skin_B`, `Details_B` | BC1 / `DXT1` | Base colour, RGB |
| `Skin_R`, `Details_R` | BC5 / `ATI2` | R = roughness, G = metalness |
| `Skin_CoatR` | BC4 / `ATI1` | Varnish layer, greyscale |
| `Skin_DirtMask`, `Details_DirtMask` | BC4 / `ATI1` | Dirt mask, greyscale |
| `Details_I` | BC3 / `DXT5` | Self-illumination, RGB + alpha |
| `Details_N` | BC5 / `ATI2` | Normal map |

- The shaders blend ambient occlusion (AO) themselves. Don't bake AO into the textures.
- The alpha channel of `Details_I` picks how each glowing area behaves:

  | Alpha | Behaviour |
  |---|---|
  | 0 | Brake lights, on when braking |
  | 32 | Energy, tinted in game (team colour); the RGB must be grey |
  | 64 | Brake heat, on when braking hard |
  | 96 | Always glowing |
  | 128 | Front lights, bright at night |
  | 160 | Turbo colour; the RGB must be grey |
  | 192 | Exhaust heat, on during turbo |
  | 224 | Boost colour; the RGB must be grey |
  | 255 | Glowing at night only |

## Keeping this file useful

- It loads every session, so keep it under 200 lines and hold only what every session needs.
  Add a line when leaving it out caused a mistake or a repeated explanation. Delete lines that
  stop being true.
- Put instructions for one part of the code in `.claude/rules/*.md`, with `paths:` frontmatter.
  Put step-by-step procedures in a skill.
- Once the tool works end to end, move the chat loop (describe → preview → change → install)
  into a project skill in `.claude/skills/`. Then cut the build-phase parts of this file, and
  replace the `@BRIEF.md` import with the few lines of the brief that still apply when the tool
  runs. Plan that as a checkpoint.
