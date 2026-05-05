import numba as nb
import numpy as np

from .zobrist import ZOBRIST

ZB = np.array(ZOBRIST, dtype=np.uint64)


def make_random_u64(size, rng=None):
    """
    Generate an array of random 64-bit unsigned integers.

    This function creates random uint64 values by combining two 32-bit random
    integers, which is necessary because numpy's random integer generation
    for uint64 is limited. This function is called outside of Numba-compiled
    functions since Numba doesn't support random number generation.

    Args:
        size: Size of random uint64 values to generate.
        rng (np.random.Generator, optional): Random number generator to use.
            If None, uses np.random.default_rng().

    Returns:
        np.ndarray: Array of N random uint64 values.
    """
    if rng is None:
        rng = np.random.default_rng()

    low = rng.integers(2**32, size=size, dtype=np.uint64)
    high = rng.integers(2**32, size=size, dtype=np.uint64)

    return (high << np.uint64(32)) | low


@nb.njit
def compute_hash(bb_current, bb_opponent):  # TODO: incrementalize
    h = np.uint64(0)

    bbc = bb_current
    bbo = bb_opponent
    idx = 0
    while bbc or bbo:
        if bbc & np.uint64(1):
            h ^= ZB[0, idx]
        elif bbo & np.uint64(1):
            h ^= ZB[1, idx]
        bbc >>= 1
        bbo >>= 1
        idx += 1

    return h
