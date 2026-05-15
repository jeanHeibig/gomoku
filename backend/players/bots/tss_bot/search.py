import numba as nb
import numpy as np
import numpy.typing as npt

from .data import ZOBRIST, LOG2

from .board import is_winning, is_dead_draw, popcount
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
FRACTIONNAL_PLY = np.array(LOG2, dtype=I8)


@nb.njit("i1(u8[:], u8, u8, u1, u8, i1, i1, i1, i1)", cache=True)
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
    if tactics == U64(0xffffffffffffffff):  # No tactics found
        move_scores = tactical_heuristic(bb_current, bb_opponent, bb_open)
    else:
        move_scores = monte_carlo_heuristic(bb_current, bb_opponent, bb_open)

    ordered_moves, move_indices, mv_nb = sort_moves(move_scores, tactics & bb_open)
    if move_hit:  # hash move first
        move_to_front(ordered_moves, move_indices, mv_nb, tt_move_idx)

    if mv_nb == 0:
        return I8(0)

    # --- ALPHA-BETA ---
    best_score = -INF
    best_move_idx = U8(0)
    first = True
    child_depth = depth - FRACTIONNAL_PLY[mv_nb]
    if mv_nb < 4:  # Reimbursement of threat moves
        child_depth += father - I8(1)

    # if tactics == U64(0xffffffffffffffff):  # No tactics found
    #     limit = min(K, mv_nb)
    # else:
    #     limit = mv_nb

    for i in range(mv_nb):
        move = ordered_moves[i]
        cell = move_indices[i]

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
