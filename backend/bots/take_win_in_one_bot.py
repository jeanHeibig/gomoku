"""
Bot that takes winning moves in one turn, otherwise plays randomly.

This bot checks if there are any moves that immediately lead to a win
for the current player. If found, it plays one randomly. If not, or if
time is low, it falls back to random moves.
"""

import random

from ..bitboard import board_to_bitboard, open_spots, winning_tiles, bitboard_to_moves

_MIN_TIME = 2  # Seconds allowed to do the search. Otherwise, play random.


def _get_winning_moves(bb_player, bb_open):
    """Get moves that would complete a five-in-a-row for the player.

    Args:
        bb_player: Bitboard of the current player's stones.
        bb_open: Bitboard of open spots on the board.

    Returns:
        List of (i, j) tuples representing winning moves.
    """
    wt = winning_tiles(bb_player | bb_open)
    return bitboard_to_moves(wt)


def take_win_in_one_bot(position, timer):
    """Bot that prioritizes immediate winning moves, else random.

    Args:
        position: 8x8 board matrix (0=empty, 1=player1, 2=player2).
        timer: Timer object with get_times() method.

    Returns:
        Tuple (i, j) of the chosen move.
    """
    # Get all possible moves (empty spots)
    moves = [(i, j) for i in range(8) for j in range(8) if position[i][j]==0]
    current_player = len(moves) % 2  # Determine current player (0 or 1)
    times = timer.get_times()["times"]
    remaining_time = times[current_player]

    if remaining_time > _MIN_TIME:
        # Convert board to bitboards and find winning moves
        bb = board_to_bitboard(position)
        winning_moves = _get_winning_moves(bb[current_player], open_spots(bb))
        if winning_moves:
            return random.choice(winning_moves)

    # Fallback to random move if no winning move or low time
    return random.choice(moves)
