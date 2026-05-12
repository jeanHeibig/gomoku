import numba as nb
import numpy as np

from .hyperparameters import K
from .data import ZOBRIST, LOG2

from .board import is_winning, is_dead_draw
from .tactics import get_forced_moves
from .heuristics import monte_carlo_heuristic, tactical_heuristic
from .evaluation import fast_evaluation
from .ordering import sort_moves, move_to_front
from .transposition import tt_probe, tt_store_search_result


I8 = np.int8
U8 = np.uint8
U64 = np.uint64


ZB = np.array(ZOBRIST, dtype=U64)
ZOBRIST_SIDE = U64(0x9E3779B97F4A7C15)
INF = I8(0x7f)
LOG2 = np.array(LOG2, dtype=U8)


@nb.njit("i1(u8[:], u8[:], u1[:], i8[:], u1[:], u8, u8, u1, u8, i1, i1, i1)")
def pvs(
    TT_keys,
    TT_moves,
    TT_depths,
    TT_scores,
    TT_flags,
    bb_current,
    bb_opponent,
    side_to_move,
    hash_,
    depth,
    alpha,
    beta
):
    if is_winning(bb_opponent):
        return -INF + depth

    if is_dead_draw(bb_current, bb_opponent):
        return 0

    if depth <= 0:
        return fast_evaluation(bb_current, bb_opponent)

    alpha_orig = alpha

    # --- TT PROBE ---
    hit, tt_score, tt_move, alpha, beta = tt_probe(
        TT_keys,
        TT_moves,
        TT_depths,
        TT_scores,
        TT_flags,
        hash_,
        depth,
        alpha,
        beta
    )
    if hit:
        return tt_score

    # --- MOVE GENERATION ---
    bb_open = ~(bb_current | bb_opponent)
    tactics = get_forced_moves(bb_current, bb_opponent, bb_open)
    move_scores = monte_carlo_heuristic(bb_current, bb_opponent, bb_open)
    ordered_moves, move_indices, mv_nb = sort_moves(move_scores, tactics)
    if tt_move:  # hash move first
        move_to_front(ordered_moves, move_indices, mv_nb, tt_move)

    # assert mv_nb > 0  # debug

    # --- ALPHA-BETA ---
    best_score = -INF
    best_move = U64(0)
    first = True
    child_depth = depth - LOG2[mv_nb]

    limit = mv_nb if tactics else min(K, mv_nb)

    for i in range(limit):
        move = ordered_moves[i]
        cell = move_indices[i]

        # --- MAKE MOVE ---
        bb_current ^= move
        hash_ ^= ZB[side_to_move, cell]
        hash_ ^= ZOBRIST_SIDE
        side_to_move = U8(1) - side_to_move

        # --- RECURSIVE SEARCH ---
        if first:
            score = -pvs(
                TT_keys,
                TT_moves,
                TT_depths,
                TT_scores,
                TT_flags,
                bb_opponent,
                bb_current,
                side_to_move,
                hash_,
                child_depth,
                -beta,
                -alpha
            )
            first = False
        else:
            score = -pvs(
                TT_keys,
                TT_moves,
                TT_depths,
                TT_scores,
                TT_flags,
                bb_opponent,
                bb_current,
                side_to_move,
                hash_,
                child_depth,
                -alpha - 1,
                -alpha
            )
            if alpha < score and score < beta:
                score = -pvs(
                    TT_keys,
                    TT_moves,
                    TT_depths,
                    TT_scores,
                    TT_flags,
                    bb_opponent,
                    bb_current,
                    side_to_move,
                    hash_,
                    child_depth,
                    -beta,
                    -alpha
                )

        # --- UNMAKE MOVE ---
        side_to_move = U8(1) - side_to_move
        hash_ ^= ZOBRIST_SIDE
        hash_ ^= ZB[side_to_move, cell]
        bb_current ^= move

        if score > best_score:
            best_score = score
            best_move = move

        if score > alpha:
            alpha = score

        if alpha >= beta:
            break

    tt_store_search_result(
        TT_keys,
        TT_moves,
        TT_depths,
        TT_scores,
        TT_flags,
        hash_,
        depth,
        best_score,
        alpha_orig,
        beta,
        best_move,
    )

    return best_score
