"""The graphics chip, where a computer has one the tool can use (the Mac's, through MLX's Metal kernels; the PC runs
numpy until its own profile says otherwise).

A kernel is one fused program: each texel's or block's whole sum done in one pass, where numpy writes and reads back
dozens of temporary arrays (the noise of a 4096² map in milliseconds instead of seconds). numpy stays the reference:
each kernel repeats its numpy twin's arithmetic in the same order (the twins sit side by side, in tool/noise.py and
tool/dds.py), compiled with IEEE arithmetic (SAFE: no fused multiply-adds, each operation rounded as numpy's; a
library function, which SAFE leaves approximate, as its precise:: one, e.g. precise::sqrt), so it gives the same bits,
and the self-test checks that on every run (`selftest.chip`). TSC_GPU=0 turns the chip off,
to time the numpy or rule the chip out.

    run(name, header, source, inputs, outputs, n)   source's kernel on n threads (the thread's index is `i`):
                                                    inputs {name: numpy array}, outputs {name: (shape, dtype)}
    f32(x)                                          a float32 constant written so that Metal reads the same bits
"""

import contextlib
import os

import numpy as np

try:
    import mlx.core as mx
    ON = mx.metal.is_available() and os.environ.get("TSC_GPU") != "0"
except ImportError:
    mx, ON = None, False
if ON:
    mx.set_cache_limit(1 << 28)  # what MLX keeps of freed buffers for the next call: a paint needs its memory back

SAFE = "#pragma METAL fp math_mode(safe)\n#pragma METAL fp contract(off)\n"  # numpy's arithmetic, operation by operation
_kernels = {}


def run(name, header, source, inputs, outputs, n):
    k = _kernels.get(name)
    if k is None:
        k = _kernels[name] = mx.fast.metal_kernel(name=name, input_names=list(inputs), output_names=list(outputs),
                                                  header=SAFE + header,
                                                  source="uint i = thread_position_in_grid.x;\n" + source)
    got = k(inputs=[mx.array(np.ascontiguousarray(a)) for a in inputs.values()], grid=(n, 1, 1), threadgroup=(256, 1, 1),
            output_shapes=[s for s, _ in outputs.values()],
            output_dtypes=[getattr(mx, np.dtype(d).name) for _, d in outputs.values()])
    return [np.array(a) for a in got]


def f32(x):
    return repr(float(np.float32(x))) + "f"


@contextlib.contextmanager
def off():
    """numpy alone while inside (the self-test's reference)."""
    global ON
    was, ON = ON, False
    try:
        yield
    finally:
        ON = was
