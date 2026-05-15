import numba as nb
import numpy as np
import numpy.typing as npt

from .data import WIN_MASKS_ALL_BOARD, ZOBRIST


U8 = np.uint8
U64 = np.uint64


WMA = np.array(WIN_MASKS_ALL_BOARD, dtype=U64)
ZB = np.array(ZOBRIST, dtype=U64)
ZOBRIST_SIDE = U64(0x9E3779B97F4A7C15)
MOVES = U64(1) << np.arange(64, dtype=U64)


@nb.njit("b1(u8)", inline="always", cache=True)
def is_winning(bb_current: U64) -> bool:
    """Return whether the bitboard contains a 5-alignment."""

    for k in range(96):

        mask = WMA[k]

        if (bb_current & mask) == mask:
            return True

    return False


@nb.njit("b1(u8, u8)", inline="always", cache=True)
def is_dead_draw(bb_current: U64, bb_opponent: U64) -> bool:
    """Return whether no player can still form a 5-alignment."""

    return (
        not is_winning(~bb_opponent)
        and
        not is_winning(~bb_current)
    )


@nb.njit("u1(u8)", inline="always", cache=True)
def popcount(bb: U64) -> U8:
    """Return number of set bits in bitboard."""

    c = U8(0)

    while bb:
        bb &= bb - U64(1)
        c += U8(1)

    return c


@nb.njit("UniTuple(u8, 2)(u1[:, :])", cache=True)
def board_to_bitboards(position: npt.NDArray[U8]) -> tuple[U64, U64]:
    """Convert a 2D board matrix into two bitboards."""

    bb_current = U64(0)
    bb_opponent = U64(0)

    for i in range(8):
        for j in range(8):

            if position[i, j] == 1:
                bb_current |= MOVES[i * 8 + j]

            elif position[i, j] == 2:
                bb_opponent |= MOVES[i * 8 + j]

    return bb_current, bb_opponent


# @nb.njit("u1(u8)", inline="always", cache=True)
# def bitboard_to_index(bb: U64) -> U8:
#     """Return index of least significant set bit."""

#     idx = U8(0)

#     while not (bb & U64(1)):
#         bb >>= U64(1)
#         idx += U8(1)

#     return idx


@nb.njit("UniTuple(u1, 2)(u1)", inline="always", cache=True)
def idx_to_ij(idx: U8) -> tuple[U8, U8]:
    """Convert idx from [0, 63] to (i, j) coordinates."""
    return idx // U8(8), idx % U8(8)


@nb.njit("UniTuple(u1, 2)(u8)", inline="always", cache=True)
def bitboard_to_ij(bb: U64) -> tuple[U8, U8]:
    """Convert a single-bit bitboard into (i, j) coordinates."""

    idx = U8(0)

    while not (bb & U64(1)):
        bb >>= U64(1)
        idx += U8(1)

    return idx_to_ij(idx)


@nb.njit("u8(u8, u8, u1)", inline="always", cache=True)
def compute_hash(bb_current: U64, bb_opponent: U64, side_to_move: U8) -> U64:
    """Compute Zobrist hash from two bitboards."""

    h = U64(0)
    idx = U8(0)

    while bb_current or bb_opponent:

        if bb_current & U64(1):
            h ^= ZB[0, idx]

        elif bb_opponent & U64(1):
            h ^= ZB[1, idx]

        bb_current >>= U64(1)
        bb_opponent >>= U64(1)

        idx += U8(1)

    if side_to_move:
        h ^= ZOBRIST_SIDE

    return h


def prettyprint(bb: U64, reverse=True, h=False, end='\n') -> None:
    """Print pretty string for bitboard."""
    if bb < 0:
        bb += 2**64
    s = bin(bb)[2:]
    s = ((64 - len(s)) * '0' + s).replace('0', '.')
    p = '\n'.join([s[i:i+8] for i in range(0, 64, 8)])

    if h:
        h = hex(bb)[2:]
        h = '0x' + (16 - len(h)) * '0' + h
        print(h)

    if reverse:
        print(p[::-1], end=end)
    else:
        print(p, end=end)


def move_to_square(idx: U8) -> str:
    """Return square name from move bitboard."""
    i, j = idx // 8, idx % 8
    return {
        U8(0): "A",
        U8(1): "B",
        U8(2): "C",
        U8(3): "D",
        U8(4): "E",
        U8(5): "F",
        U8(6): "G",
        U8(7): "H",
    }[j] + {
        U8(0): "8",
        U8(1): "7",
        U8(2): "6",
        U8(3): "5",
        U8(4): "4",
        U8(5): "3",
        U8(6): "2",
        U8(7): "1",
    }[i]
