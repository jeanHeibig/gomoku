import numba as nb
import numpy as np


def prettyprint(bb, reverse=True, end='\n') -> None:
    """Print pretty string for bitboard."""
    if bb < 0:
        bb += 2**64
    s = bin(bb)[2:]
    s = (64 - len(s)) * '0' + s
    p = '\n'.join([s[i:i+8] for i in range(0, 64, 8)])
    if reverse:
        print(p[::-1], end=end)
    else:
        print(p, end=end)


@nb.njit
def rot90(bb):
    # rotate clockwise 8x8 bitboard 90°
    res = np.uint64(0)
    for r in range(8):
        for c in range(8):
            if (bb >> (r*8 + c)) & np.uint64(1):
                nr, nc = c, 7 - r
                res |= np.uint64(1) << (nr*8 + nc)
    return res


@nb.njit
def mirror(bb):
    # flip along diagonal
    res = np.uint64(0)
    for r in range(8):
        for c in range(8):
            if (bb >> (r*8 + c)) & np.uint64(1):
                nr, nc = c, r
                res |= np.uint64(1) << (nr*8 + nc)
    return res


# TODO: instead of recomputing via loops -> precompute bit permutation maps
@nb.njit
def get_all_symmetries(bb):
    res = np.empty(8, dtype=np.uint64)
    res[0] = bb
    for i in range(3):
        res[1 + i] = rot90(res[i])
    for i in range(4):
        res[4 + i] = mirror(res[i])
    return res


@nb.njit
def canonicalize(bb_current, bb_opponent):
    symmetries_current = get_all_symmetries(bb_current)
    symmetries_opponent = get_all_symmetries(bb_opponent)

    best_idx = 0
    best_key_current = np.uint64(bb_current)
    best_key_opponent = np.uint64(bb_opponent)

    for i in range(1, 8):
        bc = symmetries_current[i]
        bo = symmetries_opponent[i]

        if (bc < best_key_current) or (bc == best_key_current and bo < best_key_opponent):
            best_key_current = bc
            best_key_opponent = bo
            best_idx = i

    return best_key_current, best_key_opponent, best_idx


@nb.njit
def apply_inverse_symmetry(bb, s_idx):  # TODO: improve with prcomputed arrays
    INV_SYM = np.array([0, 3, 2, 1, 4, 5, 6, 7])
    rev_idx = INV_SYM[s_idx]

    symmetries_current = get_all_symmetries(bb)

    return symmetries_current[rev_idx]


@nb.njit
def compute_stabilizers(bb_current, bb_opponent):
    symmetries_current = get_all_symmetries(bb_current)
    symmetries_opponent = get_all_symmetries(bb_opponent)

    mask = np.uint8(0)  # 8-bit mask

    for i in range(8):
        if symmetries_current[i] == bb_current and symmetries_opponent[i] == bb_opponent:
            mask |= (np.uint8(1) << i)

    return mask
