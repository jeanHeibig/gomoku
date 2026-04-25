"""
Bitboard utilities for Gomoku game evaluation.

This module provides functions for manipulating bitboards and checking for
winning conditions in a Gomoku game using precomputed winning masks.
"""

from .masks.precomputed_masks_all_board import WIN_MASKS_ALL_BOARD
from .masks.precomputed_masks_by_cell import WIN_MASKS_BY_CELL


def is_winning(bb: int) -> bool:
    """Check if the bitboard represents a winning position.

    Args:
        bb: The bitboard representing a player's stones.

    Returns:
        True if there are five consecutive stones in any direction, False otherwise.
    """
    return any((bb & mask) == mask for mask in WIN_MASKS_ALL_BOARD)


def winning_tiles(bb: int) -> int:
    """Return a bitboard of all tiles that are part of winning lines.

    Args:
        bb: The bitboard representing a player's stones.

    Returns:
        A bitboard where bits are set for tiles in winning five-in-a-row lines.
    """
    wt = 0
    for mask in WIN_MASKS_ALL_BOARD:
        if (bb & mask) == mask:
            wt |= mask
    return wt


def is_last_move_winning(bb: int, last_i: int, last_j: int) -> bool:
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


def winning_tiles_from_last_move(bb: int, last_i: int, last_j: int) -> int:
    """Return winning tiles that include the last move position.

    Args:
        bb: The bitboard representing a player's stones.
        last_i: The row index of the last move.
        last_j: The column index of the last move.

    Returns:
        A bitboard of tiles in winning lines that pass through the last move.
    """
    k = last_i * 8 + last_j

    wt = 0
    for mask in WIN_MASKS_BY_CELL[k]:
        if (bb & mask) == mask:
            wt |= mask

    return wt


def ij_to_bit(i: int, j: int) -> int:
    """Convert row and column indices to a bitboard bit position.

    Args:
        i: The row index (0-7).
        j: The column index (0-7).

    Returns:
        An integer with the bit set at position i*8 + j.
    """
    return (1 << (i * 8 + j))


def set_bit(bb: int, i: int, j: int) -> int:
    """Set the bit at position (i, j) in the bitboard.

    Args:
        bb: The current bitboard.
        i: The row index.
        j: The column index.

    Returns:
        The updated bitboard with the bit set.
    """
    return bb | ij_to_bit(i, j)


def board_to_bitboard(position: list[list[int]]) -> list[int]:
    """Convert a 2D board matrix into two bitboards.

    The returned list contains two integers: the first integer encodes
    player 1 stones and the second encodes player 2 stones. Each board
    cell maps to a bit at position `i * 8 + j` for row `i` and column
    `j`.

    Args:
        position: An 8x8 matrix of integers where 0 means empty, 1 means
            player 1, and 2 means player 2.

    Returns:
        A list of two bitboards `[player1_bb, player2_bb]`.
    """
    bb = [0, 0]
    for i in range(8):
        for j in range(8):
            if position[i][j] == 1:
                bb[0] = set_bit(bb[0], i, j)
            if position[i][j] == 2:
                bb[1] = set_bit(bb[1], i, j)
    return bb


def bitboard_to_board(bb: list[int]) -> list[list[int]]:
    """Convert two bitboards back into a 2D board matrix.

    Args:
        bb: A list of two bitboards `[player1_bb, player2_bb]`.

    Returns:
        An 8x8 matrix where 0 means empty, 1 means player 1, and 2 means player 2.
    """
    board = [[0]*8 for _ in range(8)]
    for i in range(8):
        for j in range(8):
            b = ij_to_bit(i, j)
            if bb[0] & b:
                board[i][j] = 1
            if bb[1] & b:
                board[i][j] = 2
    return board


def bitboard_to_moves(bb: int) -> list[list[tuple[int, int]]]:
    """Convert a bitboard into a list of (i, j) move positions.

    Args:
        bb: A bitboard representing positions.

    Returns:
        A list of tuples (i, j) for each set bit in the bitboard.
    """
    moves = []
    for i in range(8):
        for j in range(8):
            b = ij_to_bit(i, j)
            if bb & b:
                moves.append((i, j))
    return moves


def taken_spots(bb: list[int]) -> int:
    """Return a bitboard representing positions occupied by both players.

    Args:
        bb: A list of two bitboards `[player1_bb, player2_bb]`.

    Returns:
        A bitboard where bits are set only for positions occupied by either
        player 1 or player 2.
    """
    return bb[0] | bb[1]


def open_spots(bb: list[int]) -> int:
    """Return a bitboard of positions that are not taken.

    Args:
        bb: A list of two bitboards `[player1_bb, player2_bb]`.

    Returns:
        A bitboard where bits are set for empty positions.
    """
    return ~taken_spots(bb)
