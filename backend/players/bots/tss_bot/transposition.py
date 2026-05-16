import numba as nb
import numpy as np
import numpy.typing as npt

from .hyperparameters import CACHE, TT_MASK


I8 = np.int8
U8 = np.uint8
U64 = np.uint64


EXACT = U8(0)
LOWER = U8(1)
UPPER = U8(2)


@nb.njit("u8(u8, u1, u1, i1, i1)", inline="always", cache=CACHE)
def tt_pack(signature: U64, move: U8, flag: U8, score: I8, depth: I8) -> U64:
    """Return the packed data."""
    return (
          (    signature  << U64(24))
        | (U64(move)      << U64(18))
        | (U64(flag)      << U64(16))
        | (U64(U8(score)) << U64(8) )
        |  U64(U8(depth))
    )


@nb.njit("Tuple((u8, u1, u1, i1, i1))(u8)", inline="always", cache=CACHE)
def tt_unpack(entry: U64) -> tuple[U64, U8, U8, I8, I8]:
    """Return signature, move, flag, score, depth."""
    return (
        U64( entry >> U64(24))               ,
        U8(  entry >> U8(18)) & U8(0b111111),
        U8(  entry >> U8(16)) & U8(0b11)    ,
        I8( (entry >> U8(8))  & U8(0xff))   ,
        I8(  entry            & U8(0xff))
    )


@nb.njit(
    "Tuple((b1, b1, i1, u1, i1, i1))"
    "(u8[:], u8, i1, i1, i1)",
    inline="always", cache=CACHE,
)
def tt_probe(
    TT: npt.NDArray[U64],
    key: U64,
    depth: I8,
    alpha: I8,
    beta: I8,
) -> tuple[bool, bool, I8, U8, I8, I8]:
    """Probe transposition table."""
    idx = key & TT_MASK
    signature = key >> U64(24)

    stored_signature, stored_move, stored_flag, stored_score, stored_depth = tt_unpack(TT[idx])

    if (stored_signature != signature):  # No hit
        return False, False, I8(0), U8(0), alpha, beta

    if stored_depth >= depth:

        if stored_flag == EXACT:
            return True, True, stored_score, stored_move, alpha, beta

        elif stored_flag == LOWER:

            if stored_score >= beta:
                return True, True, stored_score, stored_move, alpha, beta

            alpha = max(alpha, stored_score)

        elif stored_flag == UPPER:

            if stored_score <= alpha:
                return True, True, stored_score, stored_move, alpha, beta

            beta = min(beta, stored_score)

    return False, True, I8(0), stored_move, alpha, beta


@nb.njit(
    "void(u8[:], u8, i1, i1, u1, u1)",
    inline="always", cache=CACHE,
)
def tt_store(
    TT: npt.NDArray[U64],
    key: U64,
    depth: I8,
    score: I8,
    flag: U8,
    best_move: U8,
):
    """Store entry in transposition table."""

    idx = key & TT_MASK
    signature = key >> U64(24)

    stored_signature, _, _, _, stored_depth = tt_unpack(TT[idx])

    if (stored_signature == U64(0)) or stored_depth <= depth:

        TT[idx] = tt_pack(signature, best_move, flag, score, depth)


@nb.njit(
    "void(u8[:], u8, i1, i1, i1, i1, u1)",
    inline="always", cache=CACHE,
)
def tt_store_search_result(
    TT: npt.NDArray[U64],
    key: U64,
    depth: I8,
    score: I8,
    alpha_orig: I8,
    beta: I8,
    best_move: U8,
):
    """Store search result in transposition table."""

    if score <= alpha_orig:
        flag = UPPER

    elif score >= beta:
        flag = LOWER

    else:
        flag = EXACT

    tt_store(
        TT,
        key,
        depth,
        score,
        flag,
        best_move,
    )
