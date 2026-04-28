import time
import random

import numpy as np

from ...board import b2b, bb2m  #, prettyprint
from ...board.bitboard import wm_bb, cm_bb, dt_bb, mc_bb


MIN_TIME = 1


def make_random_u64(N, rng=None):
    """
    Generate an array of random 64-bit unsigned integers.

    This function creates random uint64 values by combining two 32-bit random
    integers, which is necessary because numpy's random integer generation
    for uint64 is limited. This function is called outside of Numba-compiled
    functions since Numba doesn't support random number generation.

    Args:
        N (int): Number of random uint64 values to generate.
        rng (np.random.Generator, optional): Random number generator to use.
            If None, uses np.random.default_rng().

    Returns:
        np.ndarray: Array of N random uint64 values.
    """
    if rng is None:
        rng = np.random.default_rng()

    low = rng.integers(2**32, size=N, dtype=np.uint64)
    high = rng.integers(2**32, size=N, dtype=np.uint64)

    return (high << np.uint64(32)) | low


def mc_score_bot(position, current_player, timer, _):
    """
    Monte Carlo score-based bot for Gomoku (Five in a Row).

    This bot implements a hierarchical strategy for playing Gomoku:
    1. Win immediately if possible
    2. Block opponent's immediate win
    3. Create double threats (forks)
    4. Block opponent's double threats
    5. Use Monte Carlo simulation to evaluate positions

    The bot uses bitboard representations for efficient computation and
    time management to ensure moves are made within time limits.

    Args:
        position (list): 8x8 board state, where 0=empty, 1=player1, 2=player2.
        current_player (int): Current player (0 or 1).
        timer (dict): Timer information with remaining times for each player.
        _ : Unused parameter (for compatibility with other bot interfaces).

    Returns:
        tuple: ((row, col), None) - The chosen move coordinates and None for metadata.
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

    if remaining_time - (time.time() - start_total) <= MIN_TIME:
        return random.choice(moves), None

    # 3. Create double threat
    double_threat_moves = dt_bb(bb_current, bb_open)
    if double_threat_moves:
        # print("Find double threats:", time.time() - start_total)
        # prettyprint(double_threat_moves)
        return random.choice(bb2m(double_threat_moves)), None

    if remaining_time - (time.time() - start_total) <= MIN_TIME:
        return random.choice(moves), None

    # 4. Block opponent double threats
    opponent_double_threats = dt_bb(bb_opponent, bb_open)
    if opponent_double_threats:
        counter_moves = cm_bb(bb_current, bb_open)
        if counter_moves:
            # print("Block double threats:", time.time() - start_total)
            # prettyprint(counter_moves)
            return random.choice(bb2m(counter_moves)), None
        # Better block one threat than nothing
        # print("Block one of multiple threats:", time.time() - start_total)
        # prettyprint(opponent_double_threats)
        return random.choice(bb2m(opponent_double_threats)), None

    if remaining_time - (time.time() - start_total) <= MIN_TIME:
        return random.choice(moves), None

    # 5. Monte-Carlo
    N = 10000
    rs = make_random_u64(N)
    movemc = mc_bb(bb_current, bb_open, rs)
    # print("Monte Carlo:", time.time() - start_total)
    # prettyprint(movemc)
    return random.choice(bb2m(movemc)), None
