"""Search routines for the TSS Gomoku bot.

This module implements the principal windowed principal variation search (PVS)
used by the TSS bot, including transposition table lookups and move ordering
logic for opponent and current board bitboards.
"""

import numba as nb
import numpy as np
import numpy.typing as npt

from .hyperparameters import CACHE, TT_MASK, K
from .data import ZOBRIST, LOG2

from .board import is_winning, is_dead_draw, popcount
from .tactics import get_forced_moves
from .heuristics import monte_carlo_heuristic, tactical_heuristic
from .evaluation import fast_evaluation
from .ordering import sort_moves, move_to_front
from .transposition import tt_unpack, tt_probe, tt_store_search_result


I8 = np.int8
U8 = np.uint8
U64 = np.uint64


ZB = np.array(ZOBRIST, dtype=U64)
ZOBRIST_SIDE = U64(0x9E3779B97F4A7C15)
INF = I8(0x7f)
FRACTIONNAL_PLY = np.array(LOG2, dtype=I8)
MOVES = U64(1) << np.arange(64, dtype=U64)


def extract_pv(
    TT: npt.NDArray[U64],
    side_to_move: U8,
    key: U64,
    max_len=32
) -> list[U8]:
    pv = []

    for _ in range(max_len):

        idx = key & TT_MASK
        signature = key >> U64(24)

        stored_signature, stored_move, _, _, _ = tt_unpack(TT[idx])

        if (stored_signature != signature):  # No hit
            break

        pv.append(stored_move)

        key ^= ZB[side_to_move, stored_move]
        key ^= ZOBRIST_SIDE
        side_to_move = U8(1) - side_to_move

    return pv


@nb.njit("i1(u8[:], u8, u8, u1, u8, i1, i1, i1, i1)", cache=CACHE)
def pvs(
    TT: npt.NDArray[U64],
    bb_current: U64,
    bb_opponent: U64,
    side_to_move: U8,
    hash_key: U64,
    depth: I8,
    father: I8,
    alpha: I8,
    beta: I8
) -> I8:
    """Perform principal variation search for the TSS bot.

    Args:
        TT: Transposition table array storing past search entries.
        bb_current: Bitboard of the current player.
        bb_opponent: Bitboard of the opponent.
        side_to_move: Side to move encoded as 0 or 1.
        hash_key: Zobrist hash of the current position.
        depth: Remaining search depth in fractional plies.
        father: Reduction amount from the parent node.
        alpha: Alpha bound for alpha-beta pruning.
        beta: Beta bound for alpha-beta pruning.

    Returns:
        Best evaluation score from the recursive search.
    """
    if is_winning(bb_opponent):
        return -INF + popcount(bb_opponent) - I8(5)

    if is_dead_draw(bb_current, bb_opponent):
        return I8(0)

    if depth <= 0 and not side_to_move:
    # if depth <= 0:
        return fast_evaluation(bb_current, bb_opponent)

    # --- TT PROBE ---
    hit, move_hit, tt_score, tt_move_idx, alpha, beta = tt_probe(
        TT,
        hash_key,
        depth,
        alpha,
        beta
    )
    if hit:
        return tt_score

    alpha_orig = alpha

    # --- MOVE GENERATION ---
    bb_open = ~(bb_current | bb_opponent)

    tactics = get_forced_moves(bb_current, bb_opponent, bb_open)
    # if tactics == U64(0xffffffffffffffff):  # No tactics found
    #     move_scores = tactical_heuristic(bb_current, bb_opponent, bb_open)
    # else:
    move_scores = monte_carlo_heuristic(bb_current, bb_opponent, bb_open)

    move_indices, mv_nb = sort_moves(move_scores, tactics & bb_open)
    if move_hit:  # hash move first
        move_to_front(move_indices, mv_nb, tt_move_idx)

    if mv_nb == 0:
        return I8(0)

    # --- ALPHA-BETA ---
    best_score = -INF
    best_move_idx = U8(0)
    first = True
    child_depth = depth - FRACTIONNAL_PLY[mv_nb]
    if mv_nb < 4:  # Reimbursement of threat moves
        child_depth += father - I8(1)

    limit = min(K, mv_nb)
    for i in range(limit):
        cell = move_indices[i]
        move = MOVES[cell]

        # --- MAKE MOVE ---
        bb_current ^= move
        hash_key ^= ZB[side_to_move, cell]
        hash_key ^= ZOBRIST_SIDE
        side_to_move = U8(1) - side_to_move

        # --- RECURSIVE SEARCH ---
        if first:
            score = -pvs(
                TT,
                bb_opponent,
                bb_current,
                side_to_move,
                hash_key,
                child_depth,
                FRACTIONNAL_PLY[mv_nb],
                -beta,
                -alpha
            )
            first = False
        else:
            score = -pvs(
                TT,
                bb_opponent,
                bb_current,
                side_to_move,
                hash_key,
                child_depth,
                FRACTIONNAL_PLY[mv_nb],
                -alpha - 1,
                -alpha
            )
            if alpha < score and score < beta:
                score = -pvs(
                    TT,
                    bb_opponent,
                    bb_current,
                    side_to_move,
                    hash_key,
                    child_depth,
                    FRACTIONNAL_PLY[mv_nb],
                    -beta,
                    -alpha
                )

        # --- UNMAKE MOVE ---
        side_to_move = U8(1) - side_to_move
        hash_key ^= ZOBRIST_SIDE
        hash_key ^= ZB[side_to_move, cell]
        bb_current ^= move

        if score > best_score:
            best_score = score
            best_move_idx = cell

        if score > alpha:
            alpha = score

        if alpha >= beta:
            break

    tt_store_search_result(
        TT,
        hash_key,
        depth,
        best_score,
        alpha_orig,
        beta,
        best_move_idx,
    )

    return best_score
