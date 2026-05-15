import numba as nb
import numpy as np


U8 = np.uint8
U64 = np.uint64


@nb.njit("u8(u8)", inline="always", cache=True)
def _mirror_vertical(x: U64) -> U64:
    k1 = U64(0x00FF00FF00FF00FF)
    k2 = U64(0x0000FFFF0000FFFF)
    x = ((x >> U64(8))  & k1) | ((x & k1) << U64(8))
    x = ((x >> U64(16)) & k2) | ((x & k2) << U64(16))
    x =  (x >> U64(32))       |  (x       << U64(32))
    return x


@nb.njit("u8(u8)", inline="always", cache=True)
def _mirror_horizontal(x: U64) -> U64:
    k1 = U64(0x5555555555555555)
    k2 = U64(0x3333333333333333)
    k4 = U64(0x0F0F0F0F0F0F0F0F)
    x = ((x >> U64(1)) & k1) | ( U64(2) * (x & k1))
    x = ((x >> U64(2)) & k2) | ( U64(4) * (x & k2))
    x = ((x >> U64(4)) & k4) | (U64(16) * (x & k4))
    return x


@nb.njit("u8(u8)", inline="always", cache=True)
def _flip_diagonal(x: U64) -> U64:
    k1 = U64(0x5500550055005500)
    k2 = U64(0x3333000033330000)
    k4 = U64(0x0f0f0f0f00000000)
    t  = k4 & (x ^ (x << U64(28)))
    x ^=       t ^ (t >> U64(28))
    t  = k2 & (x ^ (x << U64(14)))
    x ^=       t ^ (t >> U64(14))
    t  = k1 & (x ^ (x << U64(7)))
    x ^=       t ^ (t >> U64(7))
    return x


@nb.njit("u8(u8)", inline="always", cache=True)
def _flip_anti_diagonal(x: U64) -> U64:
    k1 = U64(0xaa00aa00aa00aa00)
    k2 = U64(0xcccc0000cccc0000)
    k4 = U64(0xf0f0f0f00f0f0f0f)
    t  =       x ^ (x << U64(36))
    x ^= k4 & (t ^ (x >> U64(36)))
    t  = k2 & (x ^ (x << U64(18)))
    x ^=       t ^ (t >> U64(18))
    t  = k1 & (x ^ (x << U64(9)))
    x ^=       t ^ (t >> U64(9))
    return x


@nb.njit("Tuple((u8, u8, u1))(u8, u8)", cache=True)
def canonicalize(bb_current: U64, bb_opponent: U64) -> tuple[U64, U64, U8]:
    """Compute the representant of a position."""
    # --- IDENTITY ---
    bb_c = bb_current
    bb_o = bb_opponent

    best_bb_c = bb_c
    best_bb_o = bb_o
    best_t = U8(1)

    # --- VERTICAL FLIP ---
    bb_c = _mirror_vertical(bb_c)
    bb_o = _mirror_vertical(bb_o)
    if bb_c < best_bb_c or (bb_c == best_bb_c and bb_o < best_bb_o):
        best_bb_c = bb_c
        best_bb_o = bb_o
        best_t = U8(2)

    # --- 180° ROTATION ---
    bb_c = _mirror_horizontal(bb_c)
    bb_o = _mirror_horizontal(bb_o)
    if bb_c < best_bb_c or (bb_c == best_bb_c and bb_o < best_bb_o):
        best_bb_c = bb_c
        best_bb_o = bb_o
        best_t = U8(4)

    # --- HORIZONTAL FLIP ---
    bb_c = _mirror_vertical(bb_c)
    bb_o = _mirror_vertical(bb_o)
    if bb_c < best_bb_c or (bb_c == best_bb_c and bb_o < best_bb_o):
        best_bb_c = bb_c
        best_bb_o = bb_o
        best_t = U8(8)

    # --- COUNTER-CLOCKWISE ROTATION ---
    bb_c = _flip_diagonal(bb_c)
    bb_o = _flip_diagonal(bb_o)
    if bb_c < best_bb_c or (bb_c == best_bb_c and bb_o < best_bb_o):
        best_bb_c = bb_c
        best_bb_o = bb_o
        best_t = U8(16)

    # --- MAIN DIAGONAL FLIP ---
    bb_c = _mirror_vertical(bb_c)
    bb_o = _mirror_vertical(bb_o)
    if bb_c < best_bb_c or (bb_c == best_bb_c and bb_o < best_bb_o):
        best_bb_c = bb_c
        best_bb_o = bb_o
        best_t = U8(32)

    # --- CLOCKWISE ROTATION ---
    bb_c = _mirror_horizontal(bb_c)
    bb_o = _mirror_horizontal(bb_o)
    if bb_c < best_bb_c or (bb_c == best_bb_c and bb_o < best_bb_o):
        best_bb_c = bb_c
        best_bb_o = bb_o
        best_t = U8(64)

    # --- ANTI-DIAGONAL ROTATION ---
    bb_c = _mirror_vertical(bb_c)
    bb_o = _mirror_vertical(bb_o)
    if bb_c < best_bb_c or (bb_c == best_bb_c and bb_o < best_bb_o):
        best_bb_c = bb_c
        best_bb_o = bb_o
        best_t = U8(128)

    return best_bb_c, best_bb_o, best_t


@nb.njit("u8(u8, u1)", inline="always", cache=True)
def apply_inverse_symmetry(representant: U64, symmetry: U8) -> U64:
    """Revert a move to its original position on the board."""
    if symmetry == U8(1):  # I
        return representant
    if symmetry == U8(2):  # V
        return _mirror_vertical(representant)
    if symmetry == U8(4):  # R
        return _mirror_horizontal(_mirror_vertical(representant))
    if symmetry == U8(8):  # H
        return _mirror_horizontal(representant)
    if symmetry == U8(16):  # T
        return _flip_diagonal(_mirror_vertical(representant))
    if symmetry == U8(32):  # D
        return _flip_diagonal(representant)
    if symmetry == U8(64):  # C
        return _mirror_vertical(_flip_diagonal(representant))
    # A
    return _flip_anti_diagonal(representant)
