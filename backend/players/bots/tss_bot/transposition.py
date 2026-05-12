import numba as nb
import numpy as np

from .hyperparameters import TT_MASK


U8 = np.uint8
U64 = np.uint64


EXACT = U8(0)
LOWER = U8(1)
UPPER = U8(2)


@nb.njit(
    "Tuple((b1, i8, u8, i8, i8))"
    "(u8[:], u8[:], u1[:], i8[:], u1[:], u8, u1, i8, i8)",
    inline="always",
)
def tt_probe(
    TT_keys,
    TT_moves,
    TT_depths,
    TT_scores,
    TT_flags,
    key: U64,
    depth: U8,
    alpha: np.int64,
    beta: np.int64,
):
    """Probe transposition table."""

    idx = key & TT_MASK

    if TT_keys[idx] != key:
        return False, 0, U64(0), alpha, beta

    stored_depth = TT_depths[idx]
    stored_score = TT_scores[idx]
    stored_flag = TT_flags[idx]
    stored_move = TT_moves[idx]

    if stored_depth >= depth:

        if stored_flag == EXACT:
            return True, stored_score, stored_move, alpha, beta

        elif stored_flag == LOWER:

            if stored_score >= beta:
                return True, stored_score, stored_move, alpha, beta

            alpha = max(alpha, stored_score)

        elif stored_flag == UPPER:

            if stored_score <= alpha:
                return True, stored_score, stored_move, alpha, beta

            beta = min(beta, stored_score)

    return False, 0, stored_move, alpha, beta

@nb.njit(
    "void(u8[:], u8[:], u1[:], i8[:], u1[:], u8, u1, i8, u1, u8)",
    inline="always",
)
def tt_store(
    TT_keys,
    TT_moves,
    TT_depths,
    TT_scores,
    TT_flags,
    key: U64,
    depth: U8,
    score: np.int64,
    flag: U8,
    best_move: U64,
):
    """Store entry in transposition table."""

    idx = key & TT_MASK

    if TT_keys[idx] == U64(0) or TT_depths[idx] <= depth:

        TT_keys[idx] = key
        TT_moves[idx] = best_move
        TT_depths[idx] = depth
        TT_scores[idx] = score
        TT_flags[idx] = flag


@nb.njit(
    "void(u8[:], u8[:], u1[:], i8[:], u1[:], "
    "u8, u1, i8, i8, i8, u8)",
    inline="always",
)
def tt_store_search_result(
    TT_keys,
    TT_moves,
    TT_depths,
    TT_scores,
    TT_flags,
    key,
    depth,
    score,
    alpha_orig,
    beta,
    best_move,
):
    """Store search result in transposition table."""

    if score <= alpha_orig:
        flag = UPPER

    elif score >= beta:
        flag = LOWER

    else:
        flag = EXACT

    tt_store(
        TT_keys,
        TT_moves,
        TT_depths,
        TT_scores,
        TT_flags,
        key,
        depth,
        score,
        flag,
        best_move,
    )
