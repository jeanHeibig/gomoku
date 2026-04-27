"""
Bot that takes winning moves in one turn, otherwise plays randomly.

This bot checks if there are any moves that immediately lead to a win
for the current player. If found, it plays one randomly. If not, or if
time is low, it falls back to random moves.
"""

import random

import numpy as np

from ...board.masks.board_tiles import BOARD_TILES
from ...board.bitboard import board_to_bitboards, open_spots, winning_tiles, bb_to_moves

_MIN_TIME = 1  # Seconds allowed to do the search. Otherwise, play random.

BT = np.array(BOARD_TILES, dtype=np.uint64)  # TODO import directly from a numpy precomputed masks library
MOVES = np.uint64(1) << np.arange(64, dtype=np.uint64)


@np.vectorize
def get_winning_moves(bb_player, bb_open):
    return np.bitwise_or.reduce(bb_open & winning_tiles(bb_player | (BT & bb_open)))


def take_win_in_one_bot(position, current_player, timer, _):
    """Bot that prioritizes immediate winning moves, else random.

    Args:
        position: 8x8 board matrix (0=empty, 1=player1, 2=player2).
        timer: Timer object with method.

    Returns:
        Tuple (i, j) of the chosen move.
    """
    # Get all possible moves (empty spots)
    bitboards = board_to_bitboards(position)
    times = timer["times"]
    remaining_time = times[current_player]

    if remaining_time > _MIN_TIME:
        # Convert board to bitboards and find winning moves
        winning_moves = get_winning_moves(np.uint64(bitboards[current_player]), open_spots(bitboards))
        if winning_moves:
            return random.choice(winning_moves), None

    # Fallback to random move if no winning move or low time
    moves = [(i, j) for i in range(8) for j in range(8) if position[i][j]==0]
    return random.choice(moves), None
