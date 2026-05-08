import numba as nb
import numpy as np

from ...board import WMA, MOVES
from ...board.fast_eval import get_scores, fast_eval
from ...board import b2b
from ...board.symmetries import canonicalize, apply_inverse_symmetry

from .book.lookup import lookup_opening_moves

from ...clock import ctime

from .prandom import compute_hash

TT_SIZE = np.uint64(1) << 20
TT_MASK = TT_SIZE - 1

EXACT = np.uint8(0)
LOWER = np.uint8(1)
UPPER = np.uint8(2)

INF = np.int64(1) << 60
BB_64_ONES = sum([np.uint64(1) << k for k in range(64)], start=np.uint(0))
K = 5


@nb.njit
def bb2m(bb):
    """Convert a bitboard into a list of (i, j) move positions.

    Args:
        bb: A bitboard representing positions.

    Returns:
        A list of tuples (i, j) for each set bit in the bitboard.
    """
    b = np.uint64(1)
    for i in range(8):
        for j in range(8):
            if bb & b:
                return (i, j)
            b <<= 1

@nb.njit
def tt_probe(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags,
             key, depth, alpha, beta):
    idx = key & TT_MASK

    if TT_keys[idx] != key:
        return False, 0, np.uint64(0), alpha, beta

    stored_depth = TT_depths[idx]
    stored_score = TT_scores[idx]
    stored_flag = TT_flags[idx]
    stored_move = TT_moves[idx]

    if stored_depth >= depth:
        if stored_flag == EXACT:
            return True, stored_score, stored_move, alpha, beta

        elif stored_flag == LOWER:
            if stored_score >= beta:
                return True, stored_score, stored_move, alpha, beta
            alpha = max(alpha, stored_score)

        elif stored_flag == UPPER:
            if stored_score <= alpha:
                return True, stored_score, stored_move, alpha, beta
            beta = min(beta, stored_score)

    return False, 0, stored_move, alpha, beta


@nb.njit
def tt_store(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags,
             key, depth, score, flag, best_move):
    idx = key & TT_MASK

    if TT_keys[idx] == 0 or TT_depths[idx] <= depth:
        TT_keys[idx] = key
        TT_moves[idx] = best_move
        TT_depths[idx] = depth
        TT_scores[idx] = score
        TT_flags[idx] = flag


@nb.njit
def is_winning(bb_current) -> bool:
    WMA_LOCAL = WMA

    for k in range(96):
        m = WMA_LOCAL[k]
        if (bb_current & m) == m:
            return True

    return False


@nb.njit
def is_dead_draw(bb_current, bb_opponent):
    bb_open = ~(bb_current | bb_opponent)
    return not is_winning(bb_current | (bb_open & BB_64_ONES)) and not is_winning(bb_opponent | (bb_open & BB_64_ONES))


@nb.njit
def sort_moves(move_scores):
    MOVES_LOCAL = MOVES

    moves = np.zeros(64, dtype=np.uint64)
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


@nb.njit
def move_to_front(moves, mv_nb, target_move):
    if target_move == np.uint64(0):
        return

    for i in range(mv_nb):
        if moves[i] == target_move:
            # swap with first position
            tmp = moves[0]
            moves[0] = moves[i]
            moves[i] = tmp
            return


@nb.njit
def pvs(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags,
        bb_current, bb_opponent, depth, alpha, beta):

    key = compute_hash(bb_current, bb_opponent)

    # --- TT PROBE ---
    hit, tt_score, tt_move, alpha, beta = tt_probe(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags,
                                                   key, depth, alpha, beta)
    if hit:
        return tt_score

    # if is_winning(bb_opponent):  # Opponent cannot be winning with this search
    #     return -INF + depth

    if is_winning(bb_current):
        return INF - depth

    if is_dead_draw(bb_current, bb_opponent):
        return 0

    if depth == 0:
        return fast_eval(bb_current, bb_opponent)

    move_scores = get_scores(bb_current, bb_opponent)
    ordered_moves, mv_nb = sort_moves(move_scores)

    # --- HASH MOVE FIRST ---
    move_to_front(ordered_moves, mv_nb, tt_move)

    best = -INF
    best_move = np.uint64(0)

    alpha_orig = alpha
    first = True

    for i in range(min(K, mv_nb)):
        move = ordered_moves[i]

        bb_current ^= move

        if first:
            score = -pvs(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags,
                         bb_opponent, bb_current, depth - 1, -beta, -alpha)
            first = False
        else:
            score = -pvs(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags,
                         bb_opponent, bb_current, depth - 1, -alpha - 1, -alpha)

            if alpha < score and score < beta:
                score = -pvs(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags,
                             bb_opponent, bb_current, depth - 1, -beta, -score)

        bb_current ^= move

        if score > best:
            best = score
            best_move = move

        if score > alpha:
            alpha = score

        if alpha >= beta:
            break

    # --- STORE IN TT ---
    if best <= alpha_orig:
        flag = UPPER
    elif best >= beta:
        flag = LOWER
    else:
        flag = EXACT

    tt_store(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags,
             key, depth, best, flag, best_move)

    return best


@nb.njit
def find_best_move(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags,
                   bb_current, bb_opponent, max_depth, time_limit):
    start_time = ctime()

    best_move = np.uint64(0)  # TODO: if no loop is run (time_limit), best_move is not valid by default
    pv_move = np.uint64(0)

    for depth in range(1, max_depth + 1):

        if ctime() - start_time >= time_limit:
            break

        move_scores = get_scores(bb_current, bb_opponent)
        ordered_moves, mv_nb = sort_moves(move_scores)

        # --- PV move first ---
        move_to_front(ordered_moves, mv_nb, pv_move)

        if mv_nb == 1:
            return ordered_moves[0]

        alpha = -INF
        beta = INF

        best_score = -INF
        best_move_depth = np.uint64(0)  # TODO: same than outer ?

        for i in range(min(K, mv_nb)):

            if ctime() - start_time >= time_limit:
                break

            move = ordered_moves[i]

            bb_current ^= move

            # --- PVS root ---
            if i == 0:
                score = -pvs(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags,
                             bb_opponent, bb_current, depth - 1, -beta, -alpha)
            else:
                score = -pvs(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags,
                             bb_opponent, bb_current, depth - 1, -alpha - 1, -alpha)

                if alpha < score and score < beta:
                    score = -pvs(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags,
                                 bb_opponent, bb_current, depth - 1, -beta, -score)

            bb_current ^= move

            if score > best_score:
                best_score = score
                best_move_depth = move

            if score > alpha:
                alpha = score

        # --- update PV ---
        if best_move_depth != np.uint64(0):
            best_move = best_move_depth
            pv_move = best_move_depth

        # Optional debug
        print(f"Depth {depth}, score {best_score}, move {best_move}")

    return best_move


# @nb.njit
def ab_tt_bot(position, current_player, timer, memory):
    if memory is None:
        TT_keys = np.zeros(TT_SIZE, dtype=np.uint64)  # TODO: implement a 2-bucket TT
        TT_moves = np.zeros(TT_SIZE, dtype=np.uint64)
        TT_depths = np.zeros(TT_SIZE, dtype=np.uint8)
        TT_scores = np.zeros(TT_SIZE, dtype=np.int64)  # TODO: reduce space taken by scores !
        TT_flags = np.zeros(TT_SIZE, dtype=np.uint8)
        memory = TT_keys, TT_moves, TT_depths, TT_scores, TT_flags
    else:
        TT_keys, TT_moves, TT_depths, TT_scores, TT_flags = memory

    move_time = timer["times"][current_player] / 20 + timer["increments"][current_player] / 2
    # move_time = 0.8 * timer["times"][current_player]

    bitboards = b2b(position)
    bb_current = np.uint64(bitboards[current_player])
    bb_opponent = np.uint64(bitboards[1 - current_player])

    bb_current_cr, bb_opponent_cr, s_idx = canonicalize(bb_current, bb_opponent)
    bb_current_cr = np.uint64(bb_current_cr)
    bb_opponent_cr = np.uint64(bb_opponent_cr)
    print(bb_current_cr, bb_opponent_cr)

    move_cr = lookup_opening_moves(bb_current_cr, bb_opponent_cr)
    if move_cr is None:
        move_cr = find_best_move(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags,
                                bb_current_cr, bb_opponent_cr, max_depth=12, time_limit=move_time)

    move = apply_inverse_symmetry(move_cr, s_idx)
    move_ij = bb2m(move)

    print(f"Move: {move_ij}")

    return move_ij, memory
