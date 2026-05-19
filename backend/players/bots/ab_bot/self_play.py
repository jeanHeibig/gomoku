import numpy as np

from .data import ZOBRIST, LOG2

from .board import compute_hash, idx_to_ij
from .canonicalization import get_symmetry_mask
from .tactics import get_forced_moves
from .heuristics import monte_carlo_heuristic
from .search import pvs
from .ordering import sort_moves, move_to_front

I8 = np.int8
U8 = np.uint8
U64 = np.uint64


ZB = np.array(ZOBRIST, dtype=U64)
ZOBRIST_SIDE = U64(0x9E3779B97F4A7C15)
INF = I8(0x7f)
FATHER = np.array(LOG2, dtype=I8)
MOVES = U64(1) << np.arange(64, dtype=U64)
K = 8


def find_best_move_self_play(
    TT,
    bb_current,
    bb_opponent,
    side_to_move,
    hash_,
    max_depth,
) -> U8:
    bb_open = ~(bb_current | bb_opponent)
    tactics = get_forced_moves(bb_current, bb_opponent, bb_open)
    symmetries = get_symmetry_mask(bb_current, bb_opponent)
    move_scores = monte_carlo_heuristic(bb_current, bb_opponent, tactics & bb_open & symmetries)
    move_indices, mv_nb = sort_moves(move_scores, tactics & bb_open & symmetries)
    pv_move = move_indices[0]

    if mv_nb == 1:
        return move_indices[0]

    for depth in range(1, max_depth + 1):

        alpha = -INF
        beta = INF
        best_score = -INF
        best_move_depth = pv_move
        move_to_front(move_indices, mv_nb, pv_move)

        limit = min(K, mv_nb)
        for i in range(limit):

            cell = move_indices[i]
            move = MOVES[cell]

            bb_current ^= move
            hash_ ^= ZB[side_to_move, cell]
            hash_ ^= ZOBRIST_SIDE
            side_to_move = U8(1) - side_to_move
            child_depth = depth - FATHER[mv_nb]

            # --- PVS root ---
            if i == 0:
                score = -pvs(
                    TT,
                    bb_opponent,
                    bb_current,
                    side_to_move,
                    hash_,
                    child_depth,
                    FATHER[mv_nb],
                    -beta,
                    -alpha
                )
            else:
                score = -pvs(
                    TT,
                    bb_opponent,
                    bb_current,
                    side_to_move,
                    hash_,
                    child_depth,
                    FATHER[mv_nb],
                    -alpha - 1,
                    -alpha
                )

                if alpha < score and score < beta:
                    score = -pvs(
                        TT,
                        bb_opponent,
                        bb_current,
                        side_to_move,
                        hash_,
                        child_depth,
                        FATHER[mv_nb],
                        -beta,
                        -alpha
                    )

            side_to_move = U8(1) - side_to_move
            hash_ ^= ZB[side_to_move, cell]
            hash_ ^= ZOBRIST_SIDE
            bb_current ^= move

            if score > best_score:
                best_score = score
                best_move_depth = cell

            if score > alpha:
                alpha = score

        # --- update PV ---
        pv_move = best_move_depth

        if (best_score >= I8(100)) or (best_score <= I8(-100)):
            return pv_move

    return pv_move


def alpha_beta_bot_self_play(bb_current, bb_opponent, current_player, max_depth, tt):

    hash_ = compute_hash(bb_current, bb_opponent, current_player)
    move_idx = find_best_move_self_play(
        tt,
        bb_current,
        bb_opponent,
        current_player,
        hash_,
        max_depth=max_depth,
    )
    move_ij = idx_to_ij(move_idx)

    return move_ij, tt
