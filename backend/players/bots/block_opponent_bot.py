import time
import random

import numpy as np

from ...board import b2b, bb2m  #, prettyprint
from ...board.bitboard import wm_bb


MIN_TIME = 1


def block_opponent_bot(position, current_player, timer, _):
    """
    A basic defensive bot that plays Gomoku by blocking opponent wins.

    This bot evaluates the board position and selects moves in the following order:
    1. Win immediately if possible.
    2. Block opponent's immediate winning moves.
    3. Fall back to a random valid move.

    The bot respects time constraints and will play a random move if time is running low.

    Args:
        position (list of list): 8x8 board representation where 0 is empty, 1 is player 1, 2 is player 2.
        current_player (int): The current player (0 or 1).
        timer (dict): Timer information with 'times' key containing remaining time for each player.
        _ : Unused parameter.

    Returns:
        tuple: A tuple containing the selected move as (row, col) and None.
    """
    moves = [(i, j) for i in range(8) for j in range(8) if position[i][j] == 0]

    remaining_time = timer["times"][current_player]
    start_total = time.time()

    if remaining_time - (time.time() - start_total) <= MIN_TIME:
        return random.choice(moves), None

    bitboards = b2b(position)
    bb_current = np.uint64(bitboards[current_player])
    bb_opponent = np.uint64(bitboards[1 - current_player])
    bb_open = ~(bb_current | bb_opponent)

    # 1. Win immediately
    winning_moves = wm_bb(bb_current, bb_open)
    if winning_moves:
        # print("Find winning moves:", time.time() - start_total)
        # prettyprint(winning_moves)
        return random.choice(bb2m(winning_moves)), None

    if remaining_time - (time.time() - start_total) <= MIN_TIME:
        return random.choice(moves), None

    # 2. Block opponent immediate win
    opponent_winning_moves = wm_bb(bb_opponent, bb_open)
    if opponent_winning_moves:
        # print("Block threats:", time.time() - start_total)
        # prettyprint(opponent_winning_moves)
        return random.choice(bb2m(opponent_winning_moves)), None

    # print("Default:", time.time() - start_total)
    # prettyprint(movemc)
    return random.choice(moves), None
