import random

import numba as nb
import numpy as np

from ...board import WMA, MOVES
from ...board.fast_eval import get_scores, fast_eval
from ...board import b2b, bb2m, prettyprint

from ...clock import ctime


INF = np.int64(1) << 60
BB_64_ONES = sum([np.uint64(1) << k for k in range(64)], start=np.uint(0))
K = 5


@nb.njit
def sort_moves(move_scores, best_move): # TODO: Add PV-search, Transposition table and History Killer Moves
    MOVES_LOCAL = MOVES
    moves = np.zeros(64, dtype=np.uint64)
    scores = np.zeros(64, dtype=np.uint64)

    mv_nb = 0
    for k in range(64):
        if MOVES_LOCAL[k] == best_move:
            score = INF
        else:
            score = move_scores[k]
        if score >= 0:  # score = -1 for occupied cells, -2 for undesired moves
            moves[mv_nb] = MOVES_LOCAL[k]
            scores[mv_nb] = score
            mv_nb += 1

    # insertion sort
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

    return moves[:mv_nb], mv_nb


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
def negamax(bb_current, bb_opponent, depth, alpha, beta):
    if is_winning(bb_current):
        return INF

    if is_dead_draw(bb_current, bb_opponent):
        return 0

    if depth == 0:
        return fast_eval(bb_current, bb_opponent)

    move_scores = get_scores(bb_current, bb_opponent)
    ordered_moves, _ = sort_moves(move_scores, None)

    best = -INF

    for move in ordered_moves[:K]:
        bb_current ^= move  # play move
        score = -negamax(bb_opponent, bb_current, depth - 1, -beta, -alpha)
        bb_current ^= move  # undo move

        if score > best:
            best = score

        if best > alpha:
            alpha = best

        if alpha >= beta:
            break  # alpha-beta pruning

    return best


# Use iterative deepening to find the best move within a time limit
def find_best_move(bb_current, bb_opponent, max_depth, time_limit):
    best_move = None
    start_time = ctime()

    for depth in range(1, max_depth + 1):
        # print(f"Depth: {depth}")

        best_score = -INF
        move_scores = get_scores(bb_current, bb_opponent)
        # print(move_scores.reshape((8, 8)))
        ordered_moves, mv_nb = sort_moves(move_scores, best_move)

        if mv_nb == 1:
            return bb2m(ordered_moves)[0]

        for move in ordered_moves[:K]:

            bb_current ^= move  # play move
            score = -negamax(bb_opponent, bb_current, depth - 1, -INF, INF)
            bb_current ^= move  # undo move

            # from ...board import prettyprint
            # prettyprint(move)
            # print(score)

            if score > best_score:
                # print("Best move update !")
                # print("Old best move:")
                # if best_move is None:
                #     print("None")
                # else:
                #     prettyprint(best_move)
                # print(f"Old best score: {best_score}")
                best_score = score
                best_move = move
                # print("New best move:")
                # prettyprint(best_move)
                # print(f"New best score: {best_score}")
            if ctime() - start_time >= time_limit:
                break  # Time limit reached, stop searching deeper

        # print(f"Best score: {best_score}")
        # prettyprint(best_move)
        if ctime() - start_time >= time_limit:
            break  # Time limit reached, stop searching deeper

    # print(best_move)
    return bb2m(best_move)[0]


def ab_bot(position, current_player, timer, _):
    moves = [(i, j) for i in range(8) for j in range(8) if position[i][j] == 0]

    remaining_time = timer["times"][current_player]
    # move_time = 10 * remaining_time / (len(moves) + 1)
    move_time = remaining_time / 200
    start_total = ctime()

    if remaining_time - (ctime() - start_total) <= move_time:
        return random.choice(moves), None

    bitboards = b2b(position)
    bb_current = np.uint64(bitboards[current_player])
    bb_opponent = np.uint64(bitboards[1 - current_player])

    move = find_best_move(bb_current, bb_opponent, max_depth=64, time_limit=move_time)

    return move, None
