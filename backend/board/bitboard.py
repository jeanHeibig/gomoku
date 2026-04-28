"""
Bitboard utilities for Gomoku game evaluation.

This module provides functions for manipulating bitboards and checking for
winning conditions in a Gomoku game using precomputed winning masks.
"""
import numba as nb
import numpy as np


from . import BT, WMA, MOVES

@nb.njit
def bitwise_count(bb):  # np.bitwise_count not implemented yet in numba
    """
    Count the number of set bits (1s) in a 64-bit integer using bitwise operations.

    This function implements a bit counting algorithm that iterates through each set bit
    by clearing the least significant set bit in each iteration.

    Args:
        bb (np.uint64): The 64-bit integer to count bits in.

    Returns:
        int: The number of set bits in the input.
    """
    c = 0
    while bb != 0:
        bb &= bb - np.uint64(1)
        c +=1
    return c


@nb.njit
def get_winning_tiles_bb(bb):
    """
    Find all tiles that are part of winning combinations for the given bitboard.

    This function checks all precomputed winning masks against the current bitboard
    and returns a bitboard containing all tiles that belong to winning lines.

    Args:
        bb (np.uint64): Bitboard representing current stone positions.

    Returns:
        np.uint64: Bitboard with bits set for tiles that are part of winning combinations.
    """
    WMA_LOCAL = WMA
    res = np.uint64(0)

    for i in range(96):
        m = WMA_LOCAL[i]
        if (bb & m) == m:
            res |= m

    return res


@nb.njit
def wm_bb(bb_current, bb_open):
    """
    Find moves that would create an immediate win for the current player.

    This function checks each possible move in open positions and determines
    if placing a stone there would complete a winning combination.

    Args:
        bb_current (np.uint64): Bitboard of current player's stones.
        bb_open (np.uint64): Bitboard of open positions on the board.

    Returns:
        np.uint64: Bitboard with bits set for winning moves.
    """
    BT_LOCAL = BT
    res = np.uint64(0)

    for k in range(5):  # 5 non-concurrent masks
        move = BT_LOCAL[k] & bb_open
        bb_after = bb_current | move

        wt = get_winning_tiles_bb(bb_after)

        if wt != 0:
            res |= (wt & move)

    return res


@nb.njit
def dt_bb(bb_current, bb_open):
    """
    Find moves that create multiple winning opportunities (double threats).

    A double threat is a move that creates two or more different winning
    combinations simultaneously, making it very difficult for the opponent to block.

    Args:
        bb_current (np.uint64): Bitboard of current player's stones.
        bb_open (np.uint64): Bitboard of open positions on the board.

    Returns:
        np.uint64: Bitboard with bits set for double threat moves.
    """
    MOVES_LOCAL = MOVES
    res = np.uint64(0)

    for k in range(64):
        move = MOVES_LOCAL[k]

        if (move & bb_open) != 0:
            bb_after = bb_current | move
            bb_remaining = bb_open ^ move

            wm = wm_bb(bb_after, bb_remaining)

            if bitwise_count(wm) > 1:
                res |= move

    return res


@nb.njit
def cm_bb(bb_current, bb_open):
    """
    Find moves that counter the opponent's threats.

    This function prioritizes moves that either create immediate counter-attacks
    or prevent the opponent from creating double threats.

    Args:
        bb_current (np.uint64): Bitboard of current player's stones.
        bb_open (np.uint64): Bitboard of open positions on the board.

    Returns:
        np.uint64: Bitboard with bits set for counter moves.
    """
    MOVES_LOCAL = MOVES
    res = np.uint64(0)

    bb_opponent = ~bb_open ^ bb_current

    for k in range(64):
        move = MOVES_LOCAL[k]

        if (move & bb_open) != 0:
            bb_after = bb_current | move
            bb_remaining = bb_open ^ move

            # Counter-attack
            if wm_bb(bb_after, bb_remaining) != 0:
                res |= move

            # Otherwise, prevent double threats
            else:
                odt = dt_bb(bb_opponent, bb_remaining)
                if odt == 0:
                    res |= move

    return res


@nb.njit
def add_bits_to_scores(scores, bb):
    """
    Add the bit values from a bitboard to corresponding score indices.

    For each set bit in the bitboard, increment the corresponding score
    in the scores array. This is used to accumulate Monte Carlo simulation results.

    Args:
        scores (np.ndarray): Array of scores for each board position (length 64).
        bb (np.uint64): Bitboard containing positions to score.
    """
    for k in range(64):
        scores[k] += (bb >> k) & 1


@nb.njit
def mc_bb(bb_current, bb_open, rs):
    """
    Select the best move using Monte Carlo simulation.

    This function runs multiple random game simulations from the current position
    and scores each possible move based on how often it leads to winning positions.
    The move with the highest score is selected.

    Args:
        bb_current (np.uint64): Bitboard of current player's stones.
        bb_open (np.uint64): Bitboard of open positions on the board.
        rs (np.ndarray): Array of random uint64 values for simulations.

    Returns:
        np.uint64: Bitboard with the single best move selected.
    """
    MOVES_local = MOVES
    N = rs.shape[0]

    scores = np.zeros(64, dtype=np.int64)
    for t in range(N):
        bb_random = bb_current | (rs[t] & bb_open)

        wt = get_winning_tiles_bb(bb_random) & bb_open

        add_bits_to_scores(scores, wt)

    best_k = -1
    best_score = -1

    for k in range(64):  # TODO: return multiple moves in case of tie
        move = MOVES_local[k]

        if (move & bb_open) != 0:
            s = scores[k]
            if s > best_score:
                best_score = s
                best_k = k

    return np.uint64(1) << np.uint64(best_k)
