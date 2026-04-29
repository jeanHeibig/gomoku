"""Fast board evaluation helpers for the game engine.

This module provides optimized Numba-jitted board evaluation routines that compute
heuristic scores from a bitboard representation. It uses precomputed winning masks
and random fill generation tables to approximate move values and win/loss potential
for both the current player and the opponent.
"""

import numba as nb
import numpy as np


from . import WMA, WMI, RG


@nb.njit
def get_scores(bb_current, bb_opponent):
    """Compute a heuristic score grid for each empty tile on the board.

    The function evaluates every random fill scenario from the precomputed
    RG table and awards points for potential winning tile contributions.

    Args:
        bb_current (numpy.uint64): Bitboard of the current player's stones.
        bb_opponent (numpy.uint64): Bitboard of the opponent's stones.

    Returns:
        numpy.ndarray: An 8x8 int64 array of heuristic scores for each board cell.
            Occupied cells are assigned a score of 0.
    """
    WMA_LOCAL = WMA  # pylint: disable=invalid-name
    WMI_LOCAL = WMI  # pylint: disable=invalid-name
    RG_LOCAL = RG  # pylint: disable=invalid-name
    N = RG_LOCAL.shape[0]  # pylint: disable=invalid-name

    bb_occupied = (bb_current | bb_opponent)
    bb_open = ~bb_occupied
    scores = np.zeros(64, dtype=np.int64)

    for t in range(N):
        bb_current_completed = bb_current | (RG_LOCAL[t] & bb_open)
        bb_opponent_completed = bb_opponent | (~RG_LOCAL[t] & bb_open)

        # Compute winning tiles for the random position
        for k in range(96):
            m = WMA_LOCAL[k]
            if (bb_current_completed & m) == m:
                for wt_idx in WMI_LOCAL[k]:
                    scores[wt_idx] += 5
            if (bb_opponent_completed & m) == m:
                for wt_idx in WMI_LOCAL[k]:
                    scores[wt_idx] += 3


    for idx in range(64):
        if bb_occupied & (np.uint64(1) << idx):
            scores[idx] = 0

    return scores.reshape((8, 8))


@nb.njit
def fast_eval(bb_current, bb_opponent):
    """Estimate the net game score for a board position.

    This function simulates each random completion scenario and increments the
    score when the current player can complete a winning pattern, while
    decrementing it when the opponent can do the same.

    Args:
        bb_current (numpy.uint64): Bitboard of the current player's stones.
        bb_opponent (numpy.uint64): Bitboard of the opponent's stones.

    Returns:
        numpy.int64: The aggregated score difference across all simulated fills.
            Positive values favor the current player, negative values favor the
            opponent.
    """
    WMA_LOCAL = WMA  # pylint: disable=invalid-name
    RG_LOCAL = RG  # pylint: disable=invalid-name
    N = RG_LOCAL.shape[0]  # pylint: disable=invalid-name

    bb_occupied = (bb_current | bb_opponent)
    bb_open = ~bb_occupied
    score = np.int64(0)

    for t in range(N):
        bb_current_completed = bb_current | (RG_LOCAL[t] & bb_open)
        bb_opponent_completed = bb_opponent | (~RG_LOCAL[t] & bb_open)

        # Compute winning tiles for the random position
        for k in range(96):
            m = WMA_LOCAL[k]
            if (bb_current_completed & m) == m:
                score += 1
            if (bb_opponent_completed & m) == m:
                score -= 1

    return score
