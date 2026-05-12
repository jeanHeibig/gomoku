# import numba as nb
import numpy as np

from .hyperparameters import K, TT_SIZE
from .data import ZOBRIST, LOG2

from .board import board_to_bitboards, bitboard_to_index, bitboard_to_ij, compute_hash
from .clock import ctime
from .canonicalization import canonicalize, apply_inverse_symmetry
from .tactics import get_forced_moves
from .heuristics import monte_carlo_heuristic, tactical_heuristic
from .search import pvs
from .ordering import sort_moves, move_to_front
from .openings import lookup_opening_move


I8 = np.int8
U8 = np.uint8
U64 = np.uint64


ZB = np.array(ZOBRIST, dtype=U64)
ZOBRIST_SIDE = U64(0x9E3779B97F4A7C15)
INF = I8(0x7f)
LOG2 = np.array(LOG2, dtype=I8)


# @nb.njit
def find_best_move(
    TT_keys,
    TT_moves,
    TT_depths,
    TT_scores,
    TT_flags,
    bb_current,
    bb_opponent,
    side_to_move,
    hash_,
    max_depth,
    time_limit
):
    start_time = ctime()

    best_move = U64(0)  # TODO: if no loop is run (time_limit), best_move is not valid by default
    pv_move = U64(0)

    for depth in range(1, max_depth + 1):

        if ctime() - start_time >= time_limit:
            break

        bb_open = ~(bb_current | bb_opponent)
        tactics = get_forced_moves(bb_current, bb_opponent, bb_open)
        move_scores = monte_carlo_heuristic(bb_current, bb_opponent, bb_open)
        ordered_moves, move_indices, mv_nb = sort_moves(move_scores, tactics)
        if pv_move:  # PV move first
            move_to_front(ordered_moves, move_indices, mv_nb, pv_move)

        if mv_nb == 1:
            return ordered_moves[0]

        alpha = -INF
        beta = INF

        best_score = -INF
        best_move_depth = U64(0)  # TODO: same than outer ?

        for i in range(min(K, mv_nb)):

            if ctime() - start_time >= time_limit:
                break

            move = ordered_moves[i]
            cell = bitboard_to_index(move)

            bb_current ^= move
            hash_ ^= ZB[side_to_move, cell]
            if side_to_move:
                hash_ ^= ZOBRIST_SIDE
            side_to_move = U8(1) - side_to_move
            child_depth = depth - LOG2[mv_nb]

            # --- PVS root ---
            if i == 0:
                score = -pvs(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags, bb_opponent, bb_current, side_to_move, hash_, child_depth, -beta, -alpha)
            else:
                score = -pvs(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags, bb_opponent, bb_current, side_to_move, hash_, child_depth, -alpha - 1, -alpha)

                if alpha < score and score < beta:
                    score = -pvs(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags, bb_opponent, bb_current, side_to_move, hash_, child_depth, -beta, -alpha)


            side_to_move = U8(1) - side_to_move
            hash_ ^= ZB[side_to_move, cell]
            if side_to_move:
                hash_ ^= ZOBRIST_SIDE
            bb_current ^= move

            if score > best_score:
                best_score = score
                best_move_depth = move

            if score > alpha:
                alpha = score

        # --- update PV ---
        if best_move_depth != U64(0):
            best_move = best_move_depth
            pv_move = best_move_depth

        # Optional debug
        print(f"Depth {depth} ({depth // 12}), score {best_score}, move {best_move}")

    return best_move


# @nb.njit
def tss_bot(board, current_player, timer, memory):
    position = np.array(board.position, dtype=U8)  # TODO: Ask for position argument to be an array
    current_player = U8(current_player)
    if memory is None:
        TT_keys   = np.zeros(TT_SIZE, dtype=U64)  # TODO: implement a 2-bucket TT
        TT_moves  = np.zeros(TT_SIZE, dtype=U64)
        TT_depths = np.zeros(TT_SIZE, dtype=U8)
        TT_scores = np.zeros(TT_SIZE, dtype=I8)  # TODO: reduce space taken by scores !
        TT_flags  = np.zeros(TT_SIZE, dtype=U8)
        memory = TT_keys, TT_moves, TT_depths, TT_scores, TT_flags
    else:
        TT_keys, TT_moves, TT_depths, TT_scores, TT_flags = memory

    move_time = timer["times"][current_player] / 20 + timer["increments"][current_player] / 2
    # move_time = 0.5 * timer["times"][current_player]

    bitboards = board_to_bitboards(position)
    bb_current = U64(bitboards[current_player])
    bb_opponent = U64(bitboards[1 - current_player])

    bb_current_cr, bb_opponent_cr, symmetry = canonicalize(bb_current, bb_opponent)
    bb_current_cr = U64(bb_current_cr)
    bb_opponent_cr = U64(bb_opponent_cr)
    print(bb_current_cr, bb_opponent_cr)

    move_cr = lookup_opening_move(bb_current_cr, bb_opponent_cr)
    if move_cr:
        move = apply_inverse_symmetry(move_cr, symmetry)
    else:
        hash_ = compute_hash(bb_current, bb_opponent, current_player)
        move = find_best_move(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags,
                                bb_current, bb_opponent, current_player, hash_, max_depth=INF - I8(1), time_limit=move_time)

    move_ij = bitboard_to_ij(move)

    print(f"Move: {move_ij}")

    return move_ij, memory
