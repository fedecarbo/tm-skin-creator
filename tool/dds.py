"""DDS files the way Trackmania wants them: legacy D3D9 headers and a full mip chain.

Colour blocks (BC1, and the colour half of BC3) come from Pillow's "bcn" encoder. Single-channel
blocks (BC4, both halves of BC5, the alpha half of BC3) come from our own encoder, bc4_blocks,
which keeps Details_I glow codes exact. The header is written here, copying the layout of
Nadeo's reference files (flags 0xA1007, caps 0x401008, "A2XY" in the ATI2 bit-count field).
Nadeo's ATI2 files store the first block = channel 0 (normal X, roughness): see CHECKLIST.md.

Arrays are images: row 0 is the top of the texture (image row = 1 - v).
"""

import io
import struct

import numpy as np
from PIL import Image

# FourCC -> (Pillow bcn mode, bytes per 4x4 block, channels taken from the source array)
FORMATS = {
    "DXT1": (1, 8, 3),  # BC1, RGB
    "DXT5": (3, 16, 4),  # BC3, RGBA
    "ATI1": (5, 8, 1),  # BC4, one channel (the red half of a BC5 block)
    "ATI2": (5, 16, 2),  # BC5, two channels, stored first block = channel 0
}
FLAGS = 0xA1007  # CAPS | HEIGHT | WIDTH | PIXELFORMAT | MIPMAPCOUNT | LINEARSIZE
CAPS = 0x401008  # COMPLEX | TEXTURE | MIPMAP
A2XY = struct.unpack("<I", b"A2XY")[0]


def mip_sizes(width, height):
    sizes = [(width, height)]
    while sizes[-1] != (1, 1):
        w, h = sizes[-1]
        sizes.append((max(1, w // 2), max(1, h // 2)))
    return sizes


def srgb_to_linear(x):
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(x):
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(np.maximum(x, 0), 1 / 2.4) - 0.055)


def halve(a):
    """2x2 box filter. Handles odd or 1-pixel dimensions."""
    h, w = a.shape[:2]
    if h > 1:
        a = a[: h - h % 2]
        a = (a[0::2] + a[1::2]) / 2
    if w > 1:
        a = a[:, : w - w % 2]
        a = (a[:, 0::2] + a[:, 1::2]) / 2
    return a


def build_mips(image, srgb=False, normal=False, codes_in_alpha=False):
    """image: float array in 0..1, shape (h, w, c). Returns a list of uint8 arrays, one per level.

    srgb: average colour in linear light. normal: channels 0 and 1 hold X and Y of a unit
    normal; they're re-normalised after each halving. codes_in_alpha: the alpha holds codes
    (Details_I glow behaviours), so it is point-sampled, never averaged into another code.
    """
    level = srgb_to_linear(image) if srgb else image.astype(np.float64)
    levels = [level]
    while levels[-1].shape[:2] != (1, 1):
        nxt = halve(levels[-1])
        if codes_in_alpha:
            prev = levels[-1][..., 3]
            nxt[..., 3] = prev[:: 2 if prev.shape[0] > 1 else 1, :: 2 if prev.shape[1] > 1 else 1][
                : nxt.shape[0], : nxt.shape[1]
            ]
        if normal:
            xy = nxt[..., :2] * 2 - 1
            z = np.sqrt(np.clip(1 - (xy**2).sum(-1, keepdims=True), 0, 1))
            n = np.concatenate([xy, z], -1)
            n /= np.linalg.norm(n, axis=-1, keepdims=True)
            nxt = nxt.copy()
            nxt[..., :2] = n[..., :2] * 0.5 + 0.5
        levels.append(nxt)
    out = []
    for lv in levels:
        if srgb:
            lv = linear_to_srgb(lv)
        out.append(np.clip(np.rint(lv * 255), 0, 255).astype(np.uint8))
    return out


def fix_bc1(blocks):
    """Keep every BC1 block in 4-colour mode (color0 > color1), so no texel turns transparent.

    Equal endpoints can't be ordered; there every texel is color0 anyway, so indices become 0.
    """
    b = np.frombuffer(blocks, dtype=np.uint8).reshape(-1, 8).copy()
    c0 = b[:, 0].astype(np.uint16) | (b[:, 1].astype(np.uint16) << 8)
    c1 = b[:, 2].astype(np.uint16) | (b[:, 3].astype(np.uint16) << 8)
    idx = b[:, 4:8].view("<u4")[:, 0]
    swap = c0 < c1
    if swap.any():
        # Swapping endpoints maps index 0<->1 and 2<->3: flip the low bit of every 2-bit index.
        b[swap, 0:2], b[swap, 2:4] = b[swap, 2:4].copy(), b[swap, 0:2].copy()
        idx = idx.copy()
        idx[swap] ^= np.uint32(0x55555555)
    idx = np.where(c0 == c1, np.uint32(0), idx)
    b[:, 4:8] = idx.astype("<u4").view(np.uint8).reshape(-1, 4)
    return b.tobytes()


def bc4_blocks(channel):
    """Our own BC4 encoder for one uint8 channel (h, w). Returns (n_blocks, 8) uint8.

    Pillow's is loose: it moves ~1 % of Details_I glow codes onto a neighbouring code. Here
    each block tries both BC4 modes with min/max endpoints and keeps the one with less error:
    8 steps between the extremes, or 6 steps between the extremes other than 0 and 255, which
    stay exact. Blocks with up to two values, or two values plus 0 and 255, come out exact.
    """
    h, w = channel.shape
    ph, pw = -h % 4, -w % 4
    a = np.pad(channel, ((0, ph), (0, pw)), mode="edge").astype(np.float64)
    bh, bw = a.shape[0] // 4, a.shape[1] // 4
    v = a.reshape(bh, 4, bw, 4).transpose(0, 2, 1, 3).reshape(-1, 16)  # texels row by row

    hi, lo = v.max(1), v.min(1)
    steps8 = np.arange(1, 7) / 7
    pal8 = np.concatenate([hi[:, None], lo[:, None], hi[:, None] * (1 - steps8) + lo[:, None] * steps8], 1)

    inner = (v > 0) & (v < 255)
    lo6 = np.where(inner, v, np.inf).min(1)
    hi6 = np.where(inner, v, -np.inf).max(1)
    empty = ~inner.any(1)
    lo6[empty], hi6[empty] = 0, 0
    steps6 = np.arange(1, 5) / 5
    pal6 = np.concatenate([lo6[:, None], hi6[:, None], lo6[:, None] * (1 - steps6) + hi6[:, None] * steps6,
                           np.zeros((len(v), 1)), np.full((len(v), 1), 255.0)], 1)

    def fit(pal):
        err = np.abs(v[:, :, None] - pal[:, None, :])
        idx = err.argmin(2)
        return idx, (np.take_along_axis(err, idx[..., None], 2)[..., 0] ** 2).sum(1)

    idx8, err8 = fit(pal8)
    idx6, err6 = fit(pal6)
    use6 = err6 < err8
    a0 = np.where(use6, lo6, hi).astype(np.uint8)
    a1 = np.where(use6, hi6, lo).astype(np.uint8)
    idx = np.where(use6[:, None], idx6, idx8).astype(np.uint64)
    bits = (idx << (np.arange(16, dtype=np.uint64) * 3)).sum(1)
    out = np.zeros((len(v), 8), np.uint8)
    out[:, 0], out[:, 1] = a0, a1
    for k in range(6):
        out[:, 2 + k] = (bits >> np.uint64(8 * k)) & np.uint64(0xFF)
    return out


def encode_level(level, fourcc):
    mode = FORMATS[fourcc][0]
    if level.ndim == 2:
        level = level[..., None]
    if fourcc == "DXT1":
        im = Image.fromarray(np.ascontiguousarray(level[..., :3]), "RGB")
        return fix_bc1(im.tobytes("bcn", mode))
    if fourcc == "DXT5":
        # Pillow's colour half, our alpha half.
        im = Image.fromarray(np.ascontiguousarray(level[..., :4]), "RGBA")
        blocks = np.frombuffer(im.tobytes("bcn", mode), dtype=np.uint8).reshape(-1, 16).copy()
        blocks[:, :8] = bc4_blocks(level[..., 3])
        return blocks.tobytes()
    if fourcc == "ATI1":
        return bc4_blocks(level[..., 0]).tobytes()
    return np.concatenate([bc4_blocks(level[..., 0]), bc4_blocks(level[..., 1])], 1).tobytes()


def header(width, height, mips, fourcc, top_size):
    bitcount = A2XY if fourcc == "ATI2" else 0
    return (
        b"DDS "
        + struct.pack("<7I", 124, FLAGS, height, width, top_size, 0, mips)
        + struct.pack("<11I", *([0] * 11))
        + struct.pack("<2I4s5I", 32, 0x4, fourcc.encode(), bitcount, 0, 0, 0, 0)
        + struct.pack("<5I", CAPS, 0, 0, 0, 0)
    )


def encode(levels, fourcc):
    """levels: uint8 arrays from build_mips. Returns the whole DDS file as bytes."""
    data = [encode_level(lv, fourcc) for lv in levels]
    h, w = levels[0].shape[:2]
    return header(w, h, len(levels), fourcc, len(data[0])) + b"".join(data)


def write(path, image, fourcc, srgb=False, normal=False, codes_in_alpha=False):
    """image: float array 0..1, (h, w) or (h, w, c). Writes the DDS and returns its levels."""
    if image.ndim == 2:
        image = image[..., None]
    levels = build_mips(image, srgb=srgb, normal=normal, codes_in_alpha=codes_in_alpha)
    blob = encode(levels, fourcc)
    with open(path, "wb") as f:
        f.write(blob)
    return levels


# ---- Reading, for self-tests and for reading Nadeo's files ----


def read(path):
    """Returns (fourcc, [(w, h, block bytes) per mip level])."""
    blob = open(path, "rb").read()
    if blob[:4] != b"DDS ":
        raise ValueError(f"{path}: not a DDS file")
    height, width, _, _, mips = struct.unpack("<5I", blob[12:32])
    fourcc = blob[84:88].decode()
    if fourcc == "DX10":
        raise ValueError(f"{path}: DX10 header; the game needs legacy headers")
    block = FORMATS[fourcc][1]
    offset, levels = 128, []
    for w, h in mip_sizes(width, height)[: max(mips, 1)]:
        size = max(1, (w + 3) // 4) * max(1, (h + 3) // 4) * block
        levels.append((w, h, blob[offset : offset + size]))
        offset += size
    if offset != len(blob):
        raise ValueError(f"{path}: {len(blob) - offset} unexpected trailing bytes")
    return fourcc, levels


def decode_level(fourcc, w, h, data):
    """Decode one level through Pillow. ATI2 comes back as (h, w, 2): channel 0 = first block."""
    single = header(w, h, 1, fourcc, len(data)) + data
    im = Image.open(io.BytesIO(single))
    im.load()
    a = np.asarray(im)
    if fourcc == "DXT1":
        return a[..., :3]
    if fourcc == "ATI1":
        return a if a.ndim == 2 else a[..., 0]
    if fourcc == "ATI2":
        return a[..., :2]
    return a


def decode(path, level=0):
    fourcc, levels = read(path)
    w, h, data = levels[level]
    return decode_level(fourcc, w, h, data)
