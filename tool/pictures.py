"""The picture maker: illustrations, decals and repeating prints from words, made on this PC.

The model is FLUX.2 [klein] 4B by Black Forest Labs (Apache 2.0: free for any use, including a
skin other players see online), run through Hugging Face diffusers on the graphics card. Its
weights (16 GB) live in the work folder's models/ (HF_HOME). The background cutter is BiRefNet
(MIT) through rembg. Everything runs locally; nothing is sent anywhere.

    python -m tool.pictures setup                        download the weights (16 GB), once
    python -m tool.pictures decal "a roaring tiger head" [--style sticker] [-n 4] [--seed 1]
    python -m tool.pictures tile "small bananas on cream" [--style print] [-n 4] [--seed 1]
        -> build/pictures/<slug>/<k>.png and one sheet build/pictures/<slug>.png to look at
    python -m tool.pictures keep <slug> <k> <skin> <name>
        -> skins/<skin>/art/<name>.png (the prompt and seed are kept inside the PNG)

In a design:
    s.decal(s.art("tiger"), "left side", width=30)     a kept decal on the car
    s.print("bananas", scale=25)                       a kept tile becomes the finish "bananas"
    s.paint("body", "bananas")                         ... 25 cm per repeat

A decal is asked for on a plain white background, cut out, and cropped to what's left. A tile is
asked for as a seamless pattern, then its seams are mended: the picture is rolled half a turn
so the old edges meet in the middle, and that cross is drawn again by the model with the rest
pinned, so the result repeats without a join.

Memory: this PC has 16 GB of RAM and a 16 GB card, and the model's two halves (the text
encoder and the image transformer) are 8 GB each, so they're loaded straight onto the card one
after the other: every prompt is encoded first, then the encoder is dropped and the
transformer generates all the pictures.
"""

import argparse
import gc
import os
import re
import time

import numpy as np
from PIL import Image, PngImagePlugin

from tool import paths

MODELS = paths.WORK / "models"
os.environ.setdefault("HF_HOME", str(MODELS))
os.environ.setdefault("U2NET_HOME", str(MODELS / "rembg"))
os.environ.setdefault("HF_HUB_OFFLINE", "1")  # never phone home once the weights are here
MODEL = "black-forest-labs/FLUX.2-klein-4B"
CUTTER = "birefnet-general"
OUT = paths.BUILD / "pictures"

# how a decal should look, by the user's taste (2026-09-24: illustrations, prints and decals,
# not photographs); the words are added after the user's own
STYLES = {
    "sticker": "bold flat vector illustration, clean crisp outlines, flat colours, high contrast, die-cut sticker with a white border",
    "flat": "bold flat vector illustration, clean crisp outlines, flat colours, high contrast, no border",
    "print": "flat illustrated print, limited palette, clean shapes",
    "painted": "hand-painted illustration, visible brush strokes, rich colour",
    "line art": "black ink line art on white, single colour, no shading",
    "retro": "vintage screen-print poster style, limited palette, slight halftone grain",
    "photo": "photograph, realistic, studio lighting",
    "none": "",
}
DECAL_FRAME = ("A single subject, centred, isolated on a plain flat pure white background, nothing else in the "
               "picture, no text, no shadow, no border.")
TILE_FRAME = ("Seamless repeating pattern that tiles perfectly, flat and evenly lit, the pattern fills the whole "
              "picture edge to edge, no border, no frame, no text, seen straight on.")

_pipe = None  # the generating half, kept while the process lives


def slug(words):
    return re.sub(r"[^a-z0-9]+", "-", words.lower()).strip("-")[:48] or "picture"


def prompt_for(kind, words, style):
    style_words = STYLES.get(style, style)
    frame = DECAL_FRAME if kind == "decal" else TILE_FRAME
    return f"{words}. {style_words}. {frame}" if style_words else f"{words}. {frame}"


# ---- the model ----

def _cuda():
    import torch
    import diffusers.utils.logging as dl
    import huggingface_hub.utils.logging as hl
    dl.set_verbosity_error()  # quiet the "can't reach the Hub" note: we work offline on purpose
    hl.set_verbosity_error()
    if not torch.cuda.is_available():
        raise RuntimeError("the picture maker needs the graphics card (CUDA), and PyTorch can't see it")
    return torch


def encode(prompts):
    """Text -> the model's embeddings, loading only the text encoder (8 GB on the card)."""
    torch = _cuda()
    from diffusers import Flux2KleinPipeline
    t0 = time.time()
    pipe = Flux2KleinPipeline.from_pretrained(MODEL, transformer=None, vae=None, dtype=torch.bfloat16, device_map="cuda")
    out = []
    with torch.inference_mode():
        for p in prompts:
            emb, _ = pipe.encode_prompt(p, device="cuda")
            out.append(emb)
    del pipe
    gc.collect()
    torch.cuda.empty_cache()
    print(f"pictures: {len(prompts)} prompt(s) encoded in {time.time() - t0:.0f} s", flush=True)
    return out


def generator_pipe():
    """The image half (transformer + VAE, 8 GB on the card), loaded once per process."""
    global _pipe
    if _pipe is None:
        torch = _cuda()
        from diffusers import Flux2KleinPipeline
        t0 = time.time()
        _pipe = Flux2KleinPipeline.from_pretrained(MODEL, text_encoder=None, tokenizer=None, dtype=torch.bfloat16, device_map="cuda")
        print(f"pictures: image model loaded in {time.time() - t0:.0f} s", flush=True)
    return _pipe


def generate(embeds, seed, size=(1024, 1024), steps=4):
    torch = _cuda()
    pipe = generator_pipe()
    g = torch.Generator("cuda").manual_seed(int(seed))
    with torch.inference_mode():
        return pipe(prompt_embeds=embeds, width=size[0], height=size[1], num_inference_steps=steps, guidance_scale=1.0, generator=g).images[0]


def generate_tile(embeds, seed, size=(1024, 1024), steps=8):
    """A tile that repeats without a join, drawn on a torus: after every denoising step the
    picture is rolled by a random amount, so every edge spends most of the steps as an interior
    and the model draws across it. The picture is decoded from a 2x2 repeat of the result and
    the middle cut out, so the decoder's own edges don't show either."""
    torch = _cuda()
    pipe = generator_pipe()
    g = torch.Generator("cuda").manual_seed(int(seed))
    w, h = size
    lh, lw = h // 16, w // 16
    rng = np.random.default_rng(int(seed))

    def roll(p, i, t, kw):
        lat = kw["latents"].reshape(1, lh, lw, -1)
        dy, dx = int(rng.integers(0, lh)), int(rng.integers(0, lw))
        lat = torch.roll(lat, (dy, dx), (1, 2))
        return {"latents": lat.reshape(1, lh * lw, -1)}

    with torch.inference_mode():
        lat = pipe(prompt_embeds=embeds, width=w, height=h, num_inference_steps=steps, guidance_scale=1.0, generator=g,
                   callback_on_step_end=roll, output_type="latent").images
        big = torch.cat([torch.cat([lat, lat], 3)] * 2, 2)  # 2x2 repeat of the latent
        pipe.vae.enable_tiling()
        img = pipe.vae.decode(big, return_dict=False)[0]
        img = pipe.image_processor.postprocess(img, output_type="pil")[0]
    return img.crop((w // 2, h // 2, w // 2 + w, h // 2 + h))


def mend_seams(image, embeds, seed, steps=8, band=0.24):
    """Make a tile repeat without a join: roll it half a turn so its edges meet in the middle,
    then have the model draw that cross again with everything else pinned to the picture."""
    torch = _cuda()
    pipe = generator_pipe()
    w, h = image.size
    rolled = Image.fromarray(np.roll(np.asarray(image.convert("RGB")), (h // 2, w // 2), (0, 1)))
    with torch.inference_mode():
        x = pipe.image_processor.preprocess(rolled, height=h, width=w).to("cuda", torch.bfloat16)
        g = torch.Generator("cuda").manual_seed(int(seed))
        x0 = pipe._encode_vae_image(x, g)  # (1, 128, h/16, w/16), normalised as the model wants
        noise = torch.randn(x0.shape, generator=g, device="cuda", dtype=x0.dtype)
        lh, lw = x0.shape[-2:]
        yy, xx = np.mgrid[0:lh, 0:lw]
        dy = np.abs(yy - (lh - 1) / 2) / (lh / 2)
        dx = np.abs(xx - (lw - 1) / 2) / (lw / 2)
        soft = 2.0 / lh  # feather about two latents wide
        m = np.maximum(np.clip((band - dy) / soft + 0.5, 0, 1), np.clip((band - dx) / soft + 0.5, 0, 1))
        mask = torch.tensor(m.reshape(1, lh * lw, 1), device="cuda", dtype=x0.dtype)

        def pin(p, i, t, kw):
            s = p.scheduler.sigmas[i + 1]
            known = pipe._pack_latents((1 - s) * x0 + s * noise)
            return {"latents": mask * kw["latents"] + (1 - mask) * known}

        out = pipe(prompt_embeds=embeds, latents=noise, width=w, height=h, num_inference_steps=steps, guidance_scale=1.0,
                   callback_on_step_end=pin).images[0]
    return out


def seam_score(image):
    """How visible the join is: the mean colour jump across the wrap edges, against the jump
    between neighbouring pixels inside. Near 1 is seamless; several times that is a visible line."""
    a = np.asarray(image.convert("RGB"), np.float32)
    inside = (np.abs(np.diff(a, axis=0)).mean() + np.abs(np.diff(a, axis=1)).mean()) / 2
    edge = (np.abs(a[0] - a[-1]).mean() + np.abs(a[:, 0] - a[:, -1]).mean()) / 2
    return float(edge / max(inside, 1e-3))


# ---- the cutter ----

def cut_out(image, margin=0.03):
    """Remove the background and crop to the subject. Returns RGBA."""
    from rembg import new_session, remove
    t0 = time.time()
    rgba = remove(image.convert("RGB"), session=new_session(CUTTER), post_process_mask=True).convert("RGBA")
    a = np.asarray(rgba)[..., 3]
    ys, xs = np.nonzero(a > 8)
    if not len(ys):
        return rgba
    mh, mw = int(rgba.height * margin), int(rgba.width * margin)
    box = (max(0, xs.min() - mw), max(0, ys.min() - mh), min(rgba.width, xs.max() + 1 + mw), min(rgba.height, ys.max() + 1 + mh))
    print(f"pictures: background cut in {time.time() - t0:.0f} s, subject {box[2] - box[0]}x{box[3] - box[1]} px", flush=True)
    return rgba.crop(box)


# ---- candidates and the sheet ----

def make(kind, words, style=None, n=4, seed=None, size=(1024, 1024)):
    """Make n candidates and a sheet to look at. Returns (sheet path, [candidate paths])."""
    style = style or ("sticker" if kind == "decal" else "print")
    prompt = prompt_for(kind, words, style)
    seed = int(time.time()) % 100000 if seed is None else int(seed)
    folder = OUT / slug(words)
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("*.png"):
        old.unlink()
    embeds = encode([prompt])[0]
    paths_out = []
    t0 = time.time()
    for k in range(n):
        s = seed + k
        if kind == "tile":
            img = generate_tile(embeds, s, size)
            print(f"pictures: tile {k + 1}: seam {seam_score(img):.1f}", flush=True)
        else:
            img = cut_out(generate(embeds, s, size))
        info = PngImagePlugin.PngInfo()
        info.add_text("prompt", prompt)
        info.add_text("seed", str(s))
        info.add_text("kind", kind)
        info.add_text("model", MODEL)
        p = folder / f"{k + 1}.png"
        img.save(p, pnginfo=info)
        paths_out.append(p)
        print(f"pictures: {kind} {k + 1}/{n} (seed {s}) in {time.time() - t0:.0f} s", flush=True)
        t0 = time.time()
    sheet = OUT / f"{slug(words)}.png"
    make_sheet(paths_out, sheet, kind)
    return sheet, paths_out


def make_sheet(files, out, kind, cell=512):
    """Candidates side by side, numbered. A decal sits on a checkerboard (it's transparent), a
    tile is shown repeated 2x2 so any join shows."""
    from PIL import ImageDraw
    n = len(files)
    cols = min(n, 4)
    rows = (n + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell, rows * cell), (40, 40, 40))
    d = ImageDraw.Draw(sheet)
    for k, f in enumerate(files):
        im = Image.open(f).convert("RGBA")
        x0, y0 = (k % cols) * cell, (k // cols) * cell
        if kind == "tile":
            t = im.convert("RGB").resize((cell // 2, cell // 2), Image.LANCZOS)
            for i in range(2):
                for j in range(2):
                    sheet.paste(t, (x0 + i * cell // 2, y0 + j * cell // 2))
        else:
            im.thumbnail((cell - 24, cell - 24), Image.LANCZOS)
            board = Image.new("RGB", (cell, cell), (200, 200, 200))
            bd = ImageDraw.Draw(board)
            for i in range(0, cell, 32):
                for j in range(0, cell, 32):
                    if (i // 32 + j // 32) % 2:
                        bd.rectangle([i, j, i + 31, j + 31], fill=(160, 160, 160))
            board.paste(im, ((cell - im.width) // 2, (cell - im.height) // 2), im)
            sheet.paste(board, (x0, y0))
        d.rectangle([x0, y0, x0 + 30, y0 + 24], fill=(0, 0, 0))
        d.text((x0 + 8, y0 + 4), str(k + 1), fill=(255, 255, 255))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return out


def keep(slug_, k, skin, name):
    """Pick candidate k of a sheet as skins/<skin>/art/<name>.png."""
    src = OUT / slug_ / f"{k}.png"
    dst = paths.SKINS / skin / "art" / f"{name}.png"
    dst.parent.mkdir(parents=True, exist_ok=True)
    im = Image.open(src)
    info = PngImagePlugin.PngInfo()
    for key, value in im.info.items():
        if isinstance(value, str):
            info.add_text(key, value)
    im.save(dst, pnginfo=info)
    print(f"kept {src} as {dst}")
    return dst


def art_path(skin, name):
    return paths.SKINS / skin / "art" / f"{name}.png"


def about(path):
    """The prompt, seed and kind kept inside a picture."""
    im = Image.open(path)
    return {k: v for k, v in im.info.items() if isinstance(v, str)}


def setup():
    """Download the model's weights (16 GB) into the work folder, once."""
    os.environ["HF_HUB_OFFLINE"] = "0"
    from huggingface_hub import snapshot_download
    path = snapshot_download(MODEL, ignore_patterns=["flux-2-klein-4b.safetensors"])  # the root file is ComfyUI's copy
    print(f"pictures: weights at {path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("setup", help="download the model's weights (16 GB), once")
    for kind in ("decal", "tile"):
        a = sub.add_parser(kind)
        a.add_argument("words")
        a.add_argument("--style", default=None, help=", ".join(STYLES))
        a.add_argument("-n", type=int, default=4)
        a.add_argument("--seed", type=int, default=None)
        a.add_argument("--size", type=int, default=1024)
    k = sub.add_parser("keep")
    k.add_argument("slug")
    k.add_argument("k", type=int)
    k.add_argument("skin")
    k.add_argument("name")
    args = ap.parse_args()
    if args.cmd == "setup":
        setup()
    elif args.cmd in ("decal", "tile"):
        sheet, files = make(args.cmd, args.words, args.style, args.n, args.seed, (args.size, args.size))
        print(f"sheet: {sheet}")
    else:
        keep(args.slug, args.k, args.skin, args.name)


if __name__ == "__main__":
    main()
