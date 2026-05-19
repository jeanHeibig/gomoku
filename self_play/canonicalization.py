from dataclasses import dataclass

import numba as nb
import numpy as np
from numpy.typing import NDArray


U8 = np.uint8
U64 = np.uint64

BB = U64
Cell = U8
RawMove = Cell
CanonicalMove = Cell
SymmetryTransform = U8

RawMoveArray = NDArray[RawMove]
CanonicalMoveArray = NDArray[CanonicalMove]


IDENTITY = SymmetryTransform(0)
CLOCKWISE_ROTATION = SymmetryTransform(1)
U_TURN = SymmetryTransform(2)
COUNTERCLOCKWISE_ROTATION = SymmetryTransform(3)
HORIZONTAL_FLIP = SymmetryTransform(4)
ANTIDIAGONAL_FLIP = SymmetryTransform(5)
VERTICAL_FLIP = SymmetryTransform(6)
DIAGONAL_FLIP = SymmetryTransform(7)

D8 = np.array([
    18446744073709551615,
    4294967295,
    1085102592571150095,
    9277662557957324543,
    72909780498219007,
    252645135,
    406617855,
    135007759
], dtype=BB)

DEBRUIJN64 = np.uint64(0x03F79D71B4CB0A89)
INDEX64 = np.array([
     0,  1, 48,  2, 57, 49, 28,  3,
    61, 58, 50, 42, 38, 29, 17,  4,
    62, 55, 59, 36, 53, 51, 43, 22,
    45, 39, 33, 30, 24, 18, 12,  5,
    63, 47, 56, 27, 60, 41, 37, 16,
    54, 35, 52, 21, 44, 32, 23, 11,
    46, 26, 40, 15, 34, 20, 31, 10,
    25, 14, 19,  9, 13,  8,  7,  6
], dtype=U8)

TRANSFORM_CELL = np.empty((8, 64), dtype=Cell)
TRANSFORM_MOVE = np.empty((8, 64), dtype=Cell)
INVERSE_TRANSFORM_MOVE = np.empty((8, 64), dtype=Cell)


@dataclass(slots=True)
class RawPosition:
    """Raw Gomoku position."""

    current: BB
    opponent: BB


@dataclass(slots=True)
class CanonicalPosition:
    """Canonical Gomoku position."""

    current: BB
    opponent: BB


def cell_to_ij(cell: int) -> tuple[int, int]:
    """Convert cell index to (row, col)."""

    return divmod(cell, 8)


def ij_to_cell(row: int, col: int) -> int:
    """Convert (row, col) to cell index"""

    return 8 * row + col


for cell in range(64):

    row, col = cell_to_ij(cell)

    # --- IDENTITY ---
    r, c = row, col
    TRANSFORM_CELL[IDENTITY, cell] = ij_to_cell(r, c)

    # --- 90° ROTATION (clockwise) ---
    r, c = col, 7 - row
    TRANSFORM_CELL[CLOCKWISE_ROTATION, cell] = ij_to_cell(r, c)

    # --- 180° ROTATION ---
    r, c = 7 - row, 7 - col
    TRANSFORM_CELL[U_TURN, cell] = ij_to_cell(r, c)

    # --- 270° ROTATION ---
    r, c = 7 - col, row
    TRANSFORM_CELL[COUNTERCLOCKWISE_ROTATION, cell] = ij_to_cell(r, c)

    # --- MIRROR (horizontal) ---
    r, c = row, 7 - col
    TRANSFORM_CELL[HORIZONTAL_FLIP, cell] = ij_to_cell(r, c)

    # --- MIRROR then 90° ROTATION ---
    r, c = 7 - col, 7 - row
    TRANSFORM_CELL[ANTIDIAGONAL_FLIP, cell] = ij_to_cell(r, c)

    # --- MIRROR then 180° ROTATION ---
    r, c = 7 - row, col
    TRANSFORM_CELL[VERTICAL_FLIP, cell] = ij_to_cell(r, c)

    # --- MIRROR then 270° ROTATION ---
    r, c = col, row
    TRANSFORM_CELL[DIAGONAL_FLIP, cell] = ij_to_cell(r, c)


TRANSFORM_MOVE = TRANSFORM_CELL.copy()

for transform in range(8):
    for cell in range(64):

        transformed = TRANSFORM_MOVE[transform, cell]

        INVERSE_TRANSFORM_MOVE[transform, transformed] = cell


@nb.njit("uint64(uint64)", inline="always")
def _mirror_vertical(x: BB) -> BB:
    k1 = BB(0x00FF00FF00FF00FF)
    k2 = BB(0x0000FFFF0000FFFF)
    x = ((x >> 8)  & k1) | ((x & k1) << 8)
    x = ((x >> 16) & k2) | ((x & k2) << 16)
    x =  (x >> 32)       |  (x       << 32)
    return x


@nb.njit("uint64(uint64)", inline="always")
def _mirror_horizontal(x: BB) -> BB:
    k1 = BB(0x5555555555555555)
    k2 = BB(0x3333333333333333)
    k4 = BB(0x0F0F0F0F0F0F0F0F)
    x = ((x >> 1) & k1) | ((x & k1) << 1)
    x = ((x >> 2) & k2) | ((x & k2) << 2)
    x = ((x >> 4) & k4) | ((x & k4) << 4)
    return x


@nb.njit("uint64(uint64)", inline="always")
def _flip_diagonal(x: BB) -> BB:
    k1 = BB(0x5500550055005500)
    k2 = BB(0x3333000033330000)
    k4 = BB(0x0f0f0f0f00000000)
    t  = k4 & (x ^ (x << 28))
    x ^=       t ^ (t >> 28)
    t  = k2 & (x ^ (x << 14))
    x ^=       t ^ (t >> 14)
    t  = k1 & (x ^ (x << 7))
    x ^=       t ^ (t >> 7)
    return x


@nb.njit("uint64(uint64)", inline="always")
def _flip_anti_diagonal(x: BB) -> BB:
    k1 = BB(0xaa00aa00aa00aa00)
    k2 = BB(0xcccc0000cccc0000)
    k4 = BB(0xf0f0f0f00f0f0f0f)
    t  =       x ^ (x << 36)
    x ^= k4 & (t ^ (x >> 36))
    t  = k2 & (x ^ (x << 18))
    x ^=       t ^ (t >> 18)
    t  = k1 & (x ^ (x << 9))
    x ^=       t ^ (t >> 9)
    return x


@nb.njit("Tuple((uint64, uint64, uint8))(uint64, uint64)")
def _canonicalize(bb_current: BB, bb_opponent: BB) -> tuple[BB, BB, SymmetryTransform]:
    """
    Compute the representant of a position.

    Canonical ordering rule:
        Choose the symmetry minimizing:
            (bb_current, bb_opponent)
        lexicographically.
    """
    # --- IDENTITY ---
    bb_c = bb_current
    bb_o = bb_opponent

    best_bb_c = bb_c
    best_bb_o = bb_o
    best_t = IDENTITY

    # --- VERTICAL FLIP ---
    bb_c = _mirror_vertical(bb_c)
    bb_o = _mirror_vertical(bb_o)
    if bb_c < best_bb_c or (bb_c == best_bb_c and bb_o < best_bb_o):
        best_bb_c = bb_c
        best_bb_o = bb_o
        best_t = VERTICAL_FLIP

    # --- 180° ROTATION ---
    bb_c = _mirror_horizontal(bb_c)
    bb_o = _mirror_horizontal(bb_o)
    if bb_c < best_bb_c or (bb_c == best_bb_c and bb_o < best_bb_o):
        best_bb_c = bb_c
        best_bb_o = bb_o
        best_t = U_TURN

    # --- HORIZONTAL FLIP ---
    bb_c = _mirror_vertical(bb_c)
    bb_o = _mirror_vertical(bb_o)
    if bb_c < best_bb_c or (bb_c == best_bb_c and bb_o < best_bb_o):
        best_bb_c = bb_c
        best_bb_o = bb_o
        best_t = HORIZONTAL_FLIP

    # --- COUNTERCLOCKWISE ROTATION ---
    bb_c = _flip_diagonal(bb_c)
    bb_o = _flip_diagonal(bb_o)
    if bb_c < best_bb_c or (bb_c == best_bb_c and bb_o < best_bb_o):
        best_bb_c = bb_c
        best_bb_o = bb_o
        best_t = COUNTERCLOCKWISE_ROTATION

    # --- MAIN DIAGONAL FLIP ---
    bb_c = _mirror_vertical(bb_c)
    bb_o = _mirror_vertical(bb_o)
    if bb_c < best_bb_c or (bb_c == best_bb_c and bb_o < best_bb_o):
        best_bb_c = bb_c
        best_bb_o = bb_o
        best_t = DIAGONAL_FLIP

    # --- CLOCKWISE ROTATION ---
    bb_c = _mirror_horizontal(bb_c)
    bb_o = _mirror_horizontal(bb_o)
    if bb_c < best_bb_c or (bb_c == best_bb_c and bb_o < best_bb_o):
        best_bb_c = bb_c
        best_bb_o = bb_o
        best_t = CLOCKWISE_ROTATION

    # --- ANTI-DIAGONAL ROTATION ---
    bb_c = _mirror_vertical(bb_c)
    bb_o = _mirror_vertical(bb_o)
    if bb_c < best_bb_c or (bb_c == best_bb_c and bb_o < best_bb_o):
        best_bb_c = bb_c
        best_bb_o = bb_o
        best_t = ANTIDIAGONAL_FLIP

    return best_bb_c, best_bb_o, best_t


@nb.njit("uint64(uint64, uint64)", inline="always")
def _get_symmetry_mask(bb_current: BB, bb_opponent: BB) -> BB:
    vc = _mirror_vertical(bb_current)
    vo = _mirror_vertical(bb_opponent)
    if vc == bb_current and vo == bb_opponent:  # stabilizes V
        if _flip_diagonal(bb_current) == bb_current and _flip_diagonal(bb_opponent) == bb_opponent:
            return D8[7]  # stabilizes also C -> stabilizes all group
        return D8[1]
    if _flip_diagonal(bb_current) == bb_current and _flip_diagonal(bb_opponent) == bb_opponent:
        if _flip_anti_diagonal(bb_current) == bb_current and _flip_anti_diagonal(bb_opponent) == bb_opponent:
            return D8[6]  # stabilizes subgroup
        return D8[3]
    if _mirror_horizontal(bb_current) == bb_current and _mirror_horizontal(bb_opponent) == bb_opponent:
        return D8[2]  # stabilizes only H
    if _flip_anti_diagonal(bb_current) == bb_current and _flip_anti_diagonal(bb_opponent) == bb_opponent:
        return D8[4]  # stabilizes only A
    if _mirror_horizontal(vc) == bb_current and _mirror_horizontal(vo) == bb_opponent:
        if _flip_diagonal(vc) == bb_current and _flip_diagonal(vo) == bb_opponent:
            return D8[5]  # stabilizes C
        return D8[1]  # stabilizes R
    return D8[0]


@nb.njit("uint8(uint64)", inline="always")
def _single_bit_bb_to_index(bb_move: BB) -> U8:
    """Use De Bruijn trick to convert SINGLE bit bitboard to move index."""
    return INDEX64[((bb_move * DEBRUIJN64) >> 58)]


@nb.njit("Tuple((uint8[:], uint8))(uint64)", inline="always")
def _bb_to_moves(bb_moves: BB) -> tuple[CanonicalMoveArray, U8]:
    """Convert a move bitboard into an array of move indices."""
    canonical_moves = np.empty(64, dtype=CanonicalMove)
    mv_nb = U8(0)

    bb_remaining = bb_moves

    while bb_remaining:
        bb_canonical_move = bb_remaining & -bb_remaining
        canonical_move = _single_bit_bb_to_index(bb_canonical_move)

        canonical_moves[mv_nb] = canonical_move

        bb_remaining ^= bb_canonical_move
        mv_nb += U8(1)

    return canonical_moves, mv_nb


@nb.njit("uint64(uint64, uint8)", inline="always")
def _apply_transform(bitboard: BB, transform: SymmetryTransform) -> BB:
    """Apply a transformation to a bitboard."""
    if transform == IDENTITY:
        return bitboard
    if transform == VERTICAL_FLIP:
        return _mirror_vertical(bitboard)
    if transform == U_TURN:
        return _mirror_horizontal(_mirror_vertical(bitboard))
    if transform == HORIZONTAL_FLIP:
        return _mirror_horizontal(bitboard)
    if transform == CLOCKWISE_ROTATION:
        return _flip_diagonal(_mirror_vertical(bitboard))
    if transform == DIAGONAL_FLIP:
        return _flip_diagonal(bitboard)
    if transform == COUNTERCLOCKWISE_ROTATION:
        return _mirror_vertical(_flip_diagonal(bitboard))

    return _flip_anti_diagonal(bitboard)  # ANTIDIAGONAL_FLIP


@nb.njit("uint64(uint64, uint8)", inline="always")
def _apply_inverse_transform(bitboard: BB, transform: SymmetryTransform) -> BB:
    """Revert a bitboard to its original position on the board."""
    if transform == IDENTITY:
        return bitboard
    if transform == VERTICAL_FLIP:
        return _mirror_vertical(bitboard)
    if transform == U_TURN:
        return _mirror_horizontal(_mirror_vertical(bitboard))
    if transform == HORIZONTAL_FLIP:
        return _mirror_horizontal(bitboard)
    if transform == COUNTERCLOCKWISE_ROTATION:
        return _flip_diagonal(_mirror_vertical(bitboard))
    if transform == DIAGONAL_FLIP:
        return _flip_diagonal(bitboard)
    if transform == CLOCKWISE_ROTATION:
        return _mirror_vertical(_flip_diagonal(bitboard))

    return _flip_anti_diagonal(bitboard)  # ANTIDIAGONAL_FLIP


def get_canonical_legal_moves(canonical_position: CanonicalPosition) -> CanonicalMoveArray:
    bb_symmetry_mask = _get_symmetry_mask(canonical_position.current, canonical_position.opponent)
    bb_open = ~(canonical_position.current | canonical_position.opponent)
    bb_canonical_legal_moves = bb_symmetry_mask & bb_open
    canonical_moves, mv_nb = _bb_to_moves(bb_canonical_legal_moves)
    return canonical_moves[:mv_nb]


def canonicalize_position(
    raw_position: RawPosition,
) -> tuple[CanonicalPosition, SymmetryTransform]:
    """
    Convert a raw position into its canonical representation.

    Returns:
        canonical_position:
            Canonicalized bitboards.

        transform:
            Transform mapping RAW coordinates -> CANONICAL coordinates.
    """
    bb_current, bb_opponent = raw_position.current, raw_position.opponent
    canonical_current, canonical_opponent, transform_index = _canonicalize(bb_current, bb_opponent)

    canonical_position = CanonicalPosition(canonical_current, canonical_opponent)
    transform = SymmetryTransform(transform_index)

    return canonical_position, transform


def uncanonicalize_position(
    canonical_position: CanonicalPosition,
    transform: SymmetryTransform,
) -> RawPosition:
    """
    Convert a canonical position back into the raw representation
    associated with the given RAW -> CANONICAL transform.

    Warning:
        A canonical position alone has no unique raw representative.
        The transform is mandatory.
    """
    raw_current = _apply_inverse_transform(canonical_position.current, transform)
    raw_opponent = _apply_inverse_transform(canonical_position.opponent, transform)

    raw_position = RawPosition(raw_current, raw_opponent)

    return raw_position


def canonicalize_move(
    raw_move: RawMove,
    transform: SymmetryTransform,
) -> CanonicalMove:
    """Transform a raw move into canonical coordinates."""

    return CanonicalMove(
        TRANSFORM_MOVE[
            transform,
            raw_move,
        ]
    )


def uncanonicalize_move(
    canonical_move: CanonicalMove,
    transform: SymmetryTransform,
) -> RawMove:
    """Transform a canonical move back into raw coordinates."""

    return RawMove(
        INVERSE_TRANSFORM_MOVE[
            transform,
            canonical_move,
        ]
    )
