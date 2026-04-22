"""
Bitboard utilities for Gomoku game evaluation.

This module provides functions for manipulating bitboards and checking for
winning conditions in a Gomoku game using precomputed winning masks.
"""

from precomputed_masks import WIN_MASKS_BY_CELL


def has_five(bb: int, last_i: int, last_j: int) -> bool:
    """Check if the last move results in five in a row.

    Args:
        bb: The bitboard representing the current game state.
        last_i: The row index of the last move.
        last_j: The column index of the last move.

    Returns:
        True if five consecutive pieces are aligned, False otherwise.
    """
    k = last_i * 8 + last_j
    for mask in WIN_MASKS_BY_CELL[k]:
        if (bb & mask) == mask:
            return True
    return False


def set_bit(bb: int, i: int, j: int) -> int:
    """Set the bit at position (i, j) in the bitboard.

    Args:
        bb: The current bitboard.
        i: The row index.
        j: The column index.

    Returns:
        The updated bitboard with the bit set.
    """
    return bb | (1 << (i * 8 + j))
