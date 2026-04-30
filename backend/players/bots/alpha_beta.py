import time
import random

import numba as nb
import numpy as np

from ...board import WMA, MOVES
from ...board.fast_eval import get_scores, fast_eval
from ...board import b2b, bb2m  #, prettyprint


INF = np.int64(1) << 60


# @nb.njit
def sort_moves(move_scores): # TODO: Add PV-search, Transposition table and History Killer Moves
    MOVES_LOCAL = MOVES
    moves = np.zeros(64, dtype=np.uint64)
    scores = np.zeros(64, dtype=np.uint64)

    mv_nb = 0
    for k in range(64):
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


# @nb.njit
def is_winning(bb_current) -> bool:
    WMA_LOCAL = WMA

    for k in range(96):
        m = WMA_LOCAL[k]
        if (bb_current & m) == m:
            return True

    return False


# @nb.njit
def negamax(bb_current, bb_opponent, depth, alpha, beta):
    if depth == 0:
        return fast_eval(bb_current, bb_opponent)

    if is_winning(bb_current):
        return INF

    move_scores = get_scores(bb_current, bb_opponent)
    ordered_moves, mv_nb = sort_moves(move_scores)

    if mv_nb == 0:
        return 0  # draw

    best = -INF

    for move in ordered_moves:
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
    start_time = time.time()

    for depth in range(1, max_depth + 1):
        print(f"Depth: {depth}")
        if time.time() - start_time >= time_limit:
            break  # Time limit reached, stop searching deeper

        best_score = -INF
        move_scores = get_scores(bb_current, bb_opponent)
        # print(move_scores.reshape((8, 8)))
        ordered_moves, mv_nb = sort_moves(move_scores)

        if mv_nb == 1:
            return bb2m(ordered_moves)[0]

        for move in ordered_moves:

            if time.time() - start_time >= time_limit:
                break  # Time limit reached, stop searching deeper

            bb_current ^= move  # play move
            score = -negamax(bb_opponent, bb_current, depth - 1, -INF, INF)
            bb_current ^= move  # undo move

            # from ...board import prettyprint
            # prettyprint(move)
            # print(score)

            if score > best_score:
                best_score = score
                best_move = move

        print(f"Best move: {best_score}")
        # prettyprint(best_move)

    print(best_move)
    return bb2m(best_move)[0]


def ab_bot(position, current_player, timer, _):
    moves = [(i, j) for i in range(8) for j in range(8) if position[i][j] == 0]

    remaining_time = timer["times"][current_player]
    move_time = 4 * remaining_time / (len(moves) + 1)
    start_total = time.time()

    if remaining_time - (time.time() - start_total) <= move_time:
        return random.choice(moves), None

    bitboards = b2b(position)
    bb_current = np.uint64(bitboards[current_player])
    bb_opponent = np.uint64(bitboards[1 - current_player])

    move = find_best_move(bb_current, bb_opponent, max_depth=64, time_limit=move_time)
    return move, None
