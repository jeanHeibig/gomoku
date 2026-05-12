# import numba as nb
import numpy as np


from .hyperparameters import TT_SIZE
from .data import WIN_MASKS_ALL_BOARD, WIN_MASKS_INDEXES, RANDOM_GAMES, ZOBRIST, LOG2

from .board import is_winning, is_dead_draw, board_to_bitboards, bitboard_to_index, bitboard_to_ij, compute_hash
from .clock import ctime
from .canonicalization import canonicalize, apply_inverse_symmetry
from .tactics import get_forced_moves
from .heuristics import monte_carlo_heuristic, tactical_heuristic
from .evaluation import fast_evaluation
from .openings import lookup_opening_move
from .transposition import tt_probe, tt_store_search_result


U8 = np.uint8
U64 = np.uint64


K = 12

WMA = np.array(WIN_MASKS_ALL_BOARD, dtype=U64)
WMI = np.array(WIN_MASKS_INDEXES, dtype=U64)
RG = np.array(RANDOM_GAMES, dtype=U64)
MOVES = U64(1) << np.arange(64, dtype=U64)
ZB = np.array(ZOBRIST, dtype=U64)
ZOBRIST_SIDE = U64(0x9E3779B97F4A7C15)
INF = np.int64(0x7fffffffffffffff)
LOG2 = np.array(LOG2, dtype=U8)
BLACK = U8(0)
WHITE = U8(1)


# @nb.njit
def sort_moves(move_scores):
    MOVES_LOCAL = MOVES

    moves = np.zeros(64, dtype=U64)
    scores = np.zeros(64, dtype=np.int64)

    mv_nb = 0

    # Collect valid moves
    for k in range(64):
        s = move_scores[k]
        if s >= 0:
            moves[mv_nb] = MOVES_LOCAL[k]
            scores[mv_nb] = s
            mv_nb += 1

    # Insertion sort (descending order)
    for i in range(1, mv_nb):
        m = moves[i]
        s = scores[i]

        j = i - 1
        while j >= 0 and scores[j] < s:
            moves[j + 1] = moves[j]
            scores[j + 1] = scores[j]
            j -= 1

        moves[j + 1] = m
        scores[j + 1] = s

    return moves, mv_nb


# @nb.njit
def move_to_front(moves, mv_nb, target_move):
    if target_move == U64(0):
        return

    for i in range(mv_nb):
        if moves[i] == target_move:
            # swap with first position
            tmp = moves[0]
            moves[0] = moves[i]
            moves[i] = tmp
            return


# @nb.njit
def pvs(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags,
        bb_current, bb_opponent, side_to_move, hash_, depth, father, alpha, beta):
    # TODO: Put back the TT probe at the beginning, and add the mv_nb info in the TT and pass the father arg to probe

    # if is_winning(bb_opponent):  # Opponent cannot be winning with this search  # TODO assert False inside that to check
    #     return -INF + depth

    if is_winning(bb_current):
        return INF - depth

    if is_dead_draw(bb_current, bb_opponent):
        return 0

    bb_open = ~(bb_current | bb_opponent)

    tactics = get_forced_moves(bb_current, bb_opponent, bb_open)

    if not tactics:
        move_scores = monte_carlo_heuristic(bb_current, bb_opponent, bb_open)

    ordered_moves, mv_nb = sort_moves(move_scores)

    # --- FRACTIONNAL PLY: search deeper for threats ---
    # TODO: Already got a st_bb function, use it somewhere wisely
    if mv_nb < 5:  # Threats yield usually 2 or 3 moves, and sometime there is one or two counter-attacks
        depth += father - 2

    if depth <= 0:
            return fast_evaluation(bb_current, bb_opponent)

    # --- TT PROBE ---
    hit, tt_score, tt_move, alpha, beta = tt_probe(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags,
                                                   hash_, depth, alpha, beta)
    if hit:
        return tt_score

    # --- HASH MOVE FIRST ---
    move_to_front(ordered_moves, mv_nb, tt_move)

    best_score = -INF
    best_move = U64(0)

    alpha_orig = alpha
    first = True

    for i in range(min(K, mv_nb)):
        move = ordered_moves[i]
        cell = bitboard_to_index(move)

        bb_current ^= move  # TODO: wrap this in make unmake helpers (! non symmetric)
        hash_ ^= ZB[side_to_move, cell]
        if side_to_move == BLACK:
            hash_ ^= ZOBRIST_SIDE
        side_to_move = U8(1) - side_to_move

        if first:
            score = -pvs(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags,
                         bb_opponent, bb_current, side_to_move, hash_, depth - LOG2[mv_nb], LOG2[mv_nb], -beta, -alpha)
            first = False
        else:
            score = -pvs(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags,
                         bb_opponent, bb_current, side_to_move, hash_, depth - LOG2[mv_nb], LOG2[mv_nb], -alpha - 1, -alpha)

            if alpha < score and score < beta:
                score = -pvs(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags,
                             bb_opponent, bb_current, side_to_move, hash_, depth - LOG2[mv_nb], LOG2[mv_nb], -beta, -score)

        side_to_move = U8(1) - side_to_move
        hash_ ^= ZB[side_to_move, cell]
        if side_to_move == BLACK:
            hash_ ^= ZOBRIST_SIDE
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


# @nb.njit
def find_best_move(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags,
                   bb_current, bb_opponent, side_to_move, hash_, max_depth, time_limit):
    start_time = ctime()

    best_move = U64(0)  # TODO: if no loop is run (time_limit), best_move is not valid by default
    pv_move = U64(0)

    for depth in range(1, max_depth + 1):

        if ctime() - start_time >= time_limit:
            break

        bb_open = ~(bb_current | bb_opponent)

        move_scores = monte_carlo_heuristic(bb_current, bb_opponent, bb_open)
        ordered_moves, mv_nb = sort_moves(move_scores)

        # --- PV move first ---
        move_to_front(ordered_moves, mv_nb, pv_move)

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
            if side_to_move == BLACK:
                hash_ ^= ZOBRIST_SIDE
            side_to_move = U8(1) - side_to_move

            # --- PVS root ---
            if i == 0:
                score = -pvs(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags,
                             bb_opponent, bb_current, side_to_move, hash_, depth - LOG2[mv_nb], LOG2[mv_nb], -beta, -alpha)
            else:
                score = -pvs(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags,
                             bb_opponent, bb_current, side_to_move, hash_, depth - LOG2[mv_nb], LOG2[mv_nb], -alpha - 1, -alpha)

                if alpha < score and score < beta:
                    score = -pvs(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags,
                                 bb_opponent, bb_current, side_to_move, hash_, depth - LOG2[mv_nb], LOG2[mv_nb], -beta, -score)

            side_to_move = U8(1) - side_to_move
            hash_ ^= ZB[side_to_move, cell]
            if side_to_move == BLACK:
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
def tss_bot(position, current_player, timer, memory):
    if memory is None:
        TT_keys   = np.zeros(TT_SIZE, dtype=U64)  # TODO: implement a 2-bucket TT
        TT_moves  = np.zeros(TT_SIZE, dtype=U64)
        TT_depths = np.zeros(TT_SIZE, dtype=U8)
        TT_scores = np.zeros(TT_SIZE, dtype=np.int64)  # TODO: reduce space taken by scores !
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
    if move_cr is None:
        hash_ = compute_hash(bb_current, bb_opponent)
        move = find_best_move(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags,
                                bb_current, bb_opponent, current_player, hash_, max_depth=U8(255), time_limit=move_time)
    else:
        move = apply_inverse_symmetry(move_cr, symmetry)

    move_ij = bitboard_to_ij(move)

    print(f"Move: {move_ij}")

    return move_ij, memory
