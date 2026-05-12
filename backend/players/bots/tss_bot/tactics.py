import numba as nb
import numpy as np


from .data import MASKS_BY_CELL, MASK_BY_CELL_COUNT, NEIGHBORS, NEIGHBOR_COUNT


"""
Tactics module for TSS bot in Gomoku game.

This module provides optimized functions using Numba and bitboards to identify
tactical moves such as immediate wins, double threats, and counter moves.
Functions are designed for high-performance game tree search.
"""


U8 = np.uint8
U64 = np.uint64


MBC = np.array(MASKS_BY_CELL, dtype=U64)
MBC_COUNT = np.array(MASK_BY_CELL_COUNT, dtype=U8)
NBS = np.array(NEIGHBORS, dtype=U8)
NBS_COUNT = np.array(NEIGHBOR_COUNT, dtype=U8)
MOVES = U64(1) << np.arange(64, dtype=U64)


@nb.njit("b1(u8, u1)", inline="always")
def _has_align5_with_cell(bb: U64, cell: U8) -> bool:
    """Check if placing a piece at the given cell creates a 5-in-a-row alignment.

    Args:
        bb: Bitboard representing current pieces.
        cell: Cell index (0-63).

    Returns:
        True if placing at cell creates 5-in-a-row, False otherwise.
    """

    for move_nb in range(MBC_COUNT[cell]):
        mask = MBC[cell, move_nb]

        if (bb & mask) == mask:
            return True

    return False


@nb.njit("u8(u8, u8)", inline="always")
def _get_align5(bb_current: U64, bb_open: U64) -> U64:
    """Find moves that would create an immediate 5-in-a-row win for the current player.

    Args:
        bb_current: Bitboard of current player's pieces.
        bb_open: Bitboard of open positions.

    Returns:
        Bitboard of winning moves.
    """
    winning_moves = U64(0)

    for cell in range(64):
        move = MOVES[cell]

        if (bb_open & move) and _has_align5_with_cell(bb_current, cell):
            winning_moves |= move

    return winning_moves


@nb.njit("b1(u8, u8)", inline="always")
def _has_double_threat(bb_current: U64, bb_open: U64) -> bool:
    """Check if there exists a move that creates multiple winning threats.

    Args:
        bb_current: Bitboard of current player's pieces.
        bb_open: Bitboard of open positions.

    Returns:
        True if a double threat exists, False otherwise.
    """

    open_ = bb_open

    while open_:

        move = open_ & -open_
        open_ ^= move

        winning_moves = _get_align5(bb_current | move, bb_open ^ move)

        if winning_moves & (winning_moves - U64(1)):
            return True

    return False


@nb.njit("u8(u8, u8)", inline="always")
def _get_double_threats(bb_current: U64, bb_open: U64) -> U64:
    """Find moves that create multiple winning opportunities (double threats).

    Args:
        bb_current: Bitboard of current player's pieces.
        bb_open: Bitboard of open positions.

    Returns:
        Bitboard of moves that create double threats.
    """
    double_threats = U64(0)

    for cell in range(64):
        move = MOVES[cell]

        if bb_open & move:
            bb_current ^= move
            bb_open ^= move

            winning_moves = U64(0)
            for k in range(NBS_COUNT[cell]):
                cell2 = NBS[cell, k]

                m = MOVES[cell2]

                if (bb_open & m) and _has_align5_with_cell(bb_current, cell2):
                    winning_moves |= m

            bb_current ^= move
            bb_open ^= move

            if winning_moves & (winning_moves - U64(1)):  # if double threat
                double_threats |= move

    return double_threats


# @nb.njit
@nb.njit("u8(u8, u8, u8)", inline="always")
def _get_counter_moves(bb_current: U64, bb_opponent: U64, bb_open: U64) -> U64:
    """Find moves that counter the opponent's threats.

    Args:
        bb_current: Bitboard of current player's pieces.
        bb_opponent: Bitboard of opponent's pieces.
        bb_open: Bitboard of open positions.

    Returns:
        Bitboard of counter moves.
    """
    res = U64(0)

    open_ = bb_open

    while open_:

        move = open_ & -open_
        open_ ^= move

        bb_remaining = bb_open ^ move

        # Counter-attack
        if _get_align5(bb_current | move, bb_remaining):  # TODO: if has threat
            res |= move

        # Otherwise, prevent double threats
        else:
            if not _has_double_threat(bb_opponent, bb_remaining):  # TODO: only check odt bb (_opponent_still_has_double_threat)
                res |= move

    return res


@nb.njit("u8(u8, u8, u8)", inline="never")
def get_forced_moves(bb_current: U64, bb_opponent: U64, bb_open: U64) -> U64:
    """Return moves that are either forced (defense) or forcing (attacking).

    Args:
        bb_current: Bitboard of current player's pieces.
        bb_opponent: Bitboard of opponent's pieces.
        bb_open: Bitboard of open positions.

    Returns:
        Bitboard of forced moves.
    """

    # --- IMMEDIATE WIN ---
    a5 = _get_align5(bb_current, bb_open)
    if a5:
        return a5

    # --- OPPONENT WINNING THREAT ---
    o5 = _get_align5(bb_opponent, bb_open)
    if o5:
        return o5

    # --- DOUBLE THREATS ---
    dt = _get_double_threats(bb_current, bb_open)
    if dt:
        return dt

    # --- OPPONENT DOUBLE THREATS ---
    ot = _get_double_threats(bb_opponent, bb_open)
    if ot:
        # Either find a counter move
        cm = _get_counter_moves(bb_current, bb_opponent, bb_open)
        if cm:
            return cm

        return ot  # or atleast block one square

    # --- NOTHING FOUND ---
    return U64(0xffffffffffffffff)
