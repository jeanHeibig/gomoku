"""
Simple bot that plays random moves.

This bot selects a random empty spot on the board for its move,
without any strategic consideration.
"""

import random


def random_bot(position, _, __, ___):
    """Return a random valid move on the board.

    Args:
        position: 8x8 board matrix (0=empty, 1=player1, 2=player2).
        _: current_player (ignored by this bot).
        __: Timer object (ignored by this bot).
        ___: memory (ignored by this bot).

    Returns:
        Tuple (i, j) of the randomly chosen move.
    """
    moves = [(i, j) for i in range(8) for j in range(8) if position[i][j]==0]
    return random.choice(moves), None
