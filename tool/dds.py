"""DDS files the way Trackmania wants them: legacy D3D9 headers and a full mip chain.

Every block comes from our own numpy encoders. Colour blocks (BC1, and the colour half of BC3)
from bc1_blocks: endpoints on each block's principal axis, refined by least squares; Pillow's
"bcn" encoder was 5 dB worse and put visible fringes round sticker outlines (2026-09-24).
Single-channel blocks (BC4, both halves of BC5, the alpha half of BC3) from bc4_blocks, which
keeps Details_I glow codes exact. Each block is encoded on its own, so each distinct block is
encoded once and copied wherever it repeats: a car is mostly flat paint, and only 2 % of a
body's 4x4 blocks differ from all the others, so this is the same
file, many times faster. The header is written here, copying the layout of
Nadeo's reference files (flags 0xA1007, caps 0x401008, "A2XY" in the ATI2 bit-count field).
Nadeo's ATI2 files store the first block = channel 0 (normal X, roughness), confirmed in the game.

Arrays are images: row 0 is the top of the texture (image row = 1 - v).
"""

import io
import struct

import numpy as np
from PIL import Image

from tool import gpu, paths

# FourCC -> bytes per 4x4 block
BLOCK_BYTES = {
    "DXT1": 8,   # BC1, RGB
    "DXT5": 16,  # BC3, RGBA: a BC4 block for the alpha, then a BC1 block
    "ATI1": 8,   # BC4, one channel
    "ATI2": 16,  # BC5, two channels, stored first block = channel 0
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
    out = []
    while True:  # each level to bytes as it's made, only the one before kept in floats
        out.append(np.clip(np.rint((linear_to_srgb(level) if srgb else level) * 255), 0, 255).astype(np.uint8))
        if level.shape[:2] == (1, 1):
            return out
        nxt = halve(level)
        if codes_in_alpha:
            prev = level[..., 3]
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
        level = nxt


def _to565(c):
    r = np.clip(np.rint(c[..., 0] / 255 * 31), 0, 31).astype(np.uint16)
    g = np.clip(np.rint(c[..., 1] / 255 * 63), 0, 63).astype(np.uint16)
    b = np.clip(np.rint(c[..., 2] / 255 * 31), 0, 31).astype(np.uint16)
    return (r << 11) | (g << 5) | b


def _from565(v):
    r = ((v >> 11) & 31).astype(np.float32) * 255 / 31
    g = ((v >> 5) & 63).astype(np.float32) * 255 / 63
    b = (v & 31).astype(np.float32) * 255 / 31
    return np.stack([r, g, b], -1)


def _palette(q0, q1):
    e0, e1 = _from565(q0), _from565(q1)
    return np.stack([e0, e1, (2 * e0 + e1) / 3, (e0 + 2 * e1) / 3], 1)


def _sum16(a):
    """a's 16 texels (axis 1) summed one by one, in order: the kernel's order (BC1)."""
    s = a[:, 0]
    for k in range(1, 16):
        s = s + a[:, k]
    return s


def _errors(px, pal):
    """Each texel's squared error against each palette colour, (n, 16, 4)."""
    d = px[:, :, None, :] - pal[:, None, :, :]
    d = d * d
    return (d[..., 0] + d[..., 1]) + d[..., 2]


def _block_error(px, q0, q1):
    return _sum16(_errors(px, _palette(q0, q1)).min(-1))


def _local_search(px, q0, q1, rounds=1):
    """Nudge each endpoint one step up and down in each of r, g, b, keeping any change that
    lowers the block's error. One round is worth +2 dB on a skin (2026-09-24); a second
    round adds only 0.03 dB."""
    err = _block_error(px, q0, q1)
    for _ in range(rounds):
        for which in (0, 1):
            for step, top in ((1 << 11, 31), (1 << 5, 63), (1, 31)):
                for sign in (1, -1):
                    q = q0 if which == 0 else q1
                    chan = (q // step) % (top + 1)
                    can = (chan < top) if sign > 0 else (chan > 0)
                    q = np.where(can, q.astype(np.int32) + sign * step, q).astype(np.uint16)
                    t0, t1 = (q, q1) if which == 0 else (q0, q)
                    e = _block_error(px, t0, t1)
                    better = (t0 >= t1) & (e < err)  # and stay in 4-colour mode
                    q0, q1, err = np.where(better, t0, q0), np.where(better, t1, q1), np.where(better, e, err)
    return q0, q1


CHUNK = 1 << 16  # distinct blocks encoded at once: the encoders' temporaries stay in tens of MB


def _blocks(image):
    """A uint8 image (h, w) or (h, w, c) as its 4x4 blocks, each a row of texels row by row (and
    channels within a texel), the sides padded to whole blocks by repeating the edge (the
    smallest mips)."""
    image = image[..., None] if image.ndim == 2 else image
    h, w, c = image.shape
    if h % 4 or w % 4:
        image = np.pad(image, ((0, -h % 4), (0, -w % 4), (0, 0)), mode="edge")
        h, w = image.shape[:2]
    return image.reshape(h // 4, 4, w // 4, 4, c).transpose(0, 2, 1, 3, 4).reshape(-1, 16 * c)


def _each_distinct(blocks, encode):
    """encode() run once per distinct block, a chunk at a time, its result copied to every block
    that's the same. blocks: (n, k); encode: (m, k) -> (m, 8) uint8."""
    blocks = np.ascontiguousarray(blocks)
    rows = blocks.view(np.dtype((np.void, blocks.shape[1] * blocks.itemsize))).ravel()
    distinct, where = np.unique(rows, return_inverse=True)
    distinct = distinct.view(blocks.dtype).reshape(-1, blocks.shape[1])
    out = np.concatenate([encode(distinct[k:k + CHUNK]) for k in range(0, len(distinct), CHUNK)])
    return out[where.ravel()]


def bc1_blocks(rgb, iters=3, search=1):
    """Our own BC1 encoder for a uint8 (h, w, 3) image. Returns (n_blocks, 8) uint8, every block
    in 4-colour mode (color0 > color1, or equal with all indices 0), so no texel turns
    transparent. Endpoints start at the ends of each block's principal axis, are refined by
    least squares against the chosen indices (3 passes: more don't help), then a local search
    nudges them a step at a time (`search` rounds). Quality over build time: the user's call
    (2026-09-24). On the graphics chip (tool/gpu.py) where the computer has one: BC1, below, the
    same arithmetic in the same order, the same bytes."""
    def encode(b):
        if gpu.ON:
            return gpu.run("bc1", BC1_HEADER, BC1, {"blocks": b, "n": np.uint32([len(b), iters, search])},
                           {"out": ((len(b), 8), np.uint8)}, len(b))[0]
        return _bc1(b.reshape(-1, 16, 3).astype(np.float32), iters, search)
    return _each_distinct(_blocks(rgb), encode)


WEIGHTS = np.array([1, 0, 2 / 3, 1 / 3], np.float32)  # each index's share of color0


def _bc1(px, iters, search):
    """BC1 blocks (n, 8) for the blocks' texels, px (n, 16, 3) float32. Every sum over a block's texels is _sum16's."""
    n = len(px)
    mean = _sum16(px) / np.float32(16)
    cen = px - mean[:, None]
    cov = {(i, j): _sum16(cen[..., i] * cen[..., j]) for i in range(3) for j in range(i, 3)}
    c = [[cov[min(i, j), max(i, j)] for j in range(3)] for i in range(3)]
    v = [np.full(n, 1 / np.sqrt(3), np.float32)] * 3
    for _ in range(8):  # power iteration: the principal axis
        w = [(c[i][0] * v[0] + c[i][1] * v[1]) + c[i][2] * v[2] for i in range(3)]
        norm = np.maximum(np.sqrt((w[0] * w[0] + w[1] * w[1]) + w[2] * w[2]), np.float32(1e-6))
        v = [x / norm for x in w]
    proj = (cen[..., 0] * v[0][:, None] + cen[..., 1] * v[1][:, None]) + cen[..., 2] * v[2][:, None]
    v = np.stack(v, 1)
    c0 = mean + v * proj.min(1)[:, None]
    c1 = mean + v * proj.max(1)[:, None]
    for _ in range(iters):
        wa = WEIGHTS[_errors(px, _palette(_to565(c0), _to565(c1))).argmin(-1)]
        wb = 1 - wa
        aa, ab, bb = _sum16(wa * wa), _sum16(wa * wb), _sum16(wb * wb)
        ra, rb = _sum16(wa[..., None] * px), _sum16(wb[..., None] * px)
        det = aa * bb - ab * ab
        good = np.abs(det) > 1e-3
        d = np.where(good, det, 1)[:, None]
        n0 = (bb[:, None] * ra - ab[:, None] * rb) / d
        n1 = (aa[:, None] * rb - ab[:, None] * ra) / d
        c0 = np.where(good[:, None], np.clip(n0, 0, 255), c0)
        c1 = np.where(good[:, None], np.clip(n1, 0, 255), c1)
    q0, q1 = _to565(c0), _to565(c1)
    swap = q0 < q1
    q0, q1 = np.where(swap, q1, q0), np.where(swap, q0, q1)
    if search:
        q0, q1 = _local_search(px, q0, q1, search)
    idx = _errors(px, _palette(q0, q1)).argmin(-1).astype(np.uint32)
    idx[q0 == q1] = 0
    bits = np.zeros(n, np.uint32)
    for k in range(16):
        bits |= idx[:, k] << np.uint32(2 * k)
    blocks = np.zeros((n, 8), np.uint8)
    blocks[:, 0] = q0 & 255
    blocks[:, 1] = q0 >> 8
    blocks[:, 2] = q1 & 255
    blocks[:, 3] = q1 >> 8
    blocks[:, 4:] = bits.astype("<u4").view(np.uint8).reshape(n, 4)
    return blocks


# _bc1 and the functions it calls, operation for operation, on the graphics chip: one block a thread
BC1_HEADER = r'''
inline uint to565(float3 c) {
    float r = clamp(rint(c.x / 255.0f * 31.0f), 0.0f, 31.0f), g = clamp(rint(c.y / 255.0f * 63.0f), 0.0f, 63.0f);
    return (uint(r) << 11) | (uint(g) << 5) | uint(clamp(rint(c.z / 255.0f * 31.0f), 0.0f, 31.0f));
}
inline float3 from565(uint v) {
    return float3(float((v >> 11) & 31u) * 255.0f / 31.0f, float((v >> 5) & 63u) * 255.0f / 63.0f, float(v & 31u) * 255.0f / 31.0f);
}
inline void palette(uint q0, uint q1, thread float3 *pal) {
    float3 e0 = from565(q0), e1 = from565(q1);
    pal[0] = e0; pal[1] = e1; pal[2] = (2.0f * e0 + e1) / 3.0f; pal[3] = (e0 + 2.0f * e1) / 3.0f;
}
inline uint nearest(float3 p, thread const float3 *pal, thread float &best) {  // the first of the least errors
    uint j = 0;
    for (uint k = 0; k < 4; k++) {
        float3 d = p - pal[k];
        d = d * d;
        float e = (d.x + d.y) + d.z;
        if (k == 0 || e < best) { best = e; j = k; }
    }
    return j;
}
inline float block_error(thread const float3 *px, uint q0, uint q1) {
    float3 pal[4];
    palette(q0, q1, pal);
    float s = 0.0f, e;
    for (uint k = 0; k < 16; k++) { nearest(px[k], pal, e); s = k ? s + e : e; }
    return s;
}
'''
BC1 = r'''
if (i >= n[0]) return;
const float W[4] = {1.0f, 0.0f, %W2, %W3};
float3 px[16], cen[16], mean;
for (uint k = 0; k < 16; k++) {
    px[k] = float3(float(blocks[48 * i + 3 * k]), float(blocks[48 * i + 3 * k + 1]), float(blocks[48 * i + 3 * k + 2]));
    mean = k ? mean + px[k] : px[k];
}
mean = mean / 16.0f;
float c00, c01, c02, c11, c12, c22;
for (uint k = 0; k < 16; k++) {
    float3 c = cen[k] = px[k] - mean;
    c00 = k ? c00 + c.x * c.x : c.x * c.x; c01 = k ? c01 + c.x * c.y : c.x * c.y; c02 = k ? c02 + c.x * c.z : c.x * c.z;
    c11 = k ? c11 + c.y * c.y : c.y * c.y; c12 = k ? c12 + c.y * c.z : c.y * c.z; c22 = k ? c22 + c.z * c.z : c.z * c.z;
}
float3 v = float3(%R3);
for (uint it = 0; it < 8; it++) {
    float3 w = float3((c00 * v.x + c01 * v.y) + c02 * v.z, (c01 * v.x + c11 * v.y) + c12 * v.z, (c02 * v.x + c12 * v.y) + c22 * v.z);
    v = w / max(precise::sqrt((w.x * w.x + w.y * w.y) + w.z * w.z), %EPS);
}
float lo = INFINITY, hi = -INFINITY;
for (uint k = 0; k < 16; k++) { float p = (cen[k].x * v.x + cen[k].y * v.y) + cen[k].z * v.z; lo = min(lo, p); hi = max(hi, p); }
float3 c0 = mean + v * lo, c1 = mean + v * hi, pal[4];
for (uint it = 0; it < n[1]; it++) {
    palette(to565(c0), to565(c1), pal);
    float aa, ab, bb, e;
    float3 ra, rb;
    for (uint k = 0; k < 16; k++) {
        float wa = W[nearest(px[k], pal, e)], wb = 1.0f - wa;
        aa = k ? aa + wa * wa : wa * wa; ab = k ? ab + wa * wb : wa * wb; bb = k ? bb + wb * wb : wb * wb;
        ra = k ? ra + wa * px[k] : wa * px[k]; rb = k ? rb + wb * px[k] : wb * px[k];
    }
    float det = aa * bb - ab * ab;
    if (fabs(det) > %DET) {
        c0 = clamp((bb * ra - ab * rb) / det, 0.0f, 255.0f);
        c1 = clamp((aa * rb - ab * ra) / det, 0.0f, 255.0f);
    }
}
uint q0 = to565(c0), q1 = to565(c1);
if (q0 < q1) { uint t = q0; q0 = q1; q1 = t; }
for (uint r = 0; r < n[2]; r++) {
    float err = block_error(px, q0, q1);
    for (uint which = 0; which < 2; which++) for (uint s = 0; s < 3; s++) for (int sign = 1; sign >= -1; sign -= 2) {
        uint step = s == 0 ? 2048u : (s == 1 ? 32u : 1u), top = s == 1 ? 63u : 31u;
        uint q = which ? q1 : q0, chan = (q / step) % (top + 1);
        if (sign > 0 ? chan < top : chan > 0) q = sign > 0 ? q + step : q - step;
        uint t0 = which ? q0 : q, t1 = which ? q : q1;
        float e = block_error(px, t0, t1);
        if (t0 >= t1 && e < err) { q0 = t0; q1 = t1; err = e; }
    }
}
palette(q0, q1, pal);
uint bits = 0;
float e;
if (q0 != q1) for (uint k = 0; k < 16; k++) bits |= nearest(px[k], pal, e) << (2 * k);
uint4 word = uint4(q0 | (q1 << 16), bits, 0, 0);
for (uint k = 0; k < 8; k++) out[8 * i + k] = uchar((word[k / 4] >> (8 * (k % 4))) & 255);
'''
BC1 = BC1.replace("%W2", gpu.f32(2 / 3)).replace("%W3", gpu.f32(1 / 3)).replace("%R3", gpu.f32(1 / np.sqrt(3)))
BC1 = BC1.replace("%EPS", gpu.f32(1e-6)).replace("%DET", gpu.f32(1e-3))


def bc4_blocks(channel):
    """Our own BC4 encoder for one uint8 channel (h, w). Returns (n_blocks, 8) uint8.

    Pillow's is loose: it moves ~1 % of Details_I glow codes onto a neighbouring code. Here
    each block tries both BC4 modes with min/max endpoints and keeps the one with less error:
    8 steps between the extremes, or 6 steps between the extremes other than 0 and 255, which
    stay exact. Blocks with up to two values, or two values plus 0 and 255, come out exact.
    """
    return _each_distinct(_blocks(channel), lambda b: _bc4(b.astype(np.float64)))


def _bc4(v):
    """BC4 blocks (n, 8) for the blocks' 16 values each, v (n, 16) float."""
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
    if level.ndim == 2:
        level = level[..., None]
    if fourcc == "DXT1":
        return bc1_blocks(level[..., :3]).tobytes()
    if fourcc == "DXT5":
        return np.concatenate([bc4_blocks(level[..., 3]), bc1_blocks(level[..., :3])], 1).tobytes()
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


def texture(image, fourcc, srgb=False, normal=False, codes_in_alpha=False):
    """The whole DDS file, as bytes, for a float image 0..1, (h, w) or (h, w, c)."""
    if image.ndim == 2:
        image = image[..., None]
    return encode(build_mips(image, srgb=srgb, normal=normal, codes_in_alpha=codes_in_alpha), fourcc)


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
    block = BLOCK_BYTES[fourcc]
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


def stock(name, size=None, resample=Image.BILINEAR):
    """Nadeo's stock texture, decoded, as float 0..1, resized to (w, h) if given."""
    a = decode(paths.MODEL_SOURCE / f"{name}.dds")
    if size and (a.shape[1], a.shape[0]) != size:
        chans = [Image.fromarray(a[..., c] if a.ndim == 3 else a).resize(size, resample)
                 for c in range(a.shape[2] if a.ndim == 3 else 1)]
        a = np.stack([np.asarray(c) for c in chans], -1)
    return a.astype(np.float32) / 255
