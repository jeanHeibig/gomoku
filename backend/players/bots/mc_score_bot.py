import time
import random

import numba as nb
import numpy as np

from ...board.masks.board_tiles import BOARD_TILES
from ...board.masks.precomputed_masks_all_board import WIN_MASKS_ALL_BOARD
from ...board.bitboard import board_to_bitboards, open_spots, bb_to_moves

BT = np.array(BOARD_TILES, dtype=np.uint64)
WMA = np.array(WIN_MASKS_ALL_BOARD, dtype=np.uint64)
MOVES = np.uint64(1) << np.arange(64, dtype=np.uint64)

MIN_TIME = 1

prettyprint = lambda bb: print('\n'.join([((66 - len(bin(bb))) * '0' + bin(bb)[2:])[i:i+8] for i in range(0, 64, 8)])[::-1])


@nb.njit
def bitwise_count(bb):  # np.bitwise_count not implemented yet in numba
    c = 0
    while bb != 0:
        bb &= bb - np.uint64(1)
        c +=1
    return c


@nb.njit
def get_winning_tiles_bb(bb):
    WMA_local = WMA
    res = np.uint64(0)

    for i in range(96):
        m = WMA_local[i]
        if (bb & m) == m:
            res |= m

    return res


@nb.njit
def get_winning_moves_bb(bb_current, bb_open):
    BT_local = BT
    res = np.uint64(0)

    for k in range(5):  # 5 non-concurrent masks
        move = BT_local[k] & bb_open
        bb_after = bb_current | move

        wt = get_winning_tiles_bb(bb_after)

        if wt != 0:
            res |= (wt & move)

    return res


@nb.njit
def get_double_threat_moves_bb(bb_current, bb_open):
    MOVES_local = MOVES
    res = np.uint64(0)

    for k in range(64):
        move = MOVES_local[k]

        if (move & bb_open) != 0:
            bb_after = bb_current | move
            bb_remaining = bb_open ^ move

            wm = get_winning_moves_bb(bb_after, bb_remaining)

            if bitwise_count(wm) > 1:
                res |= move

    return res


@nb.njit
def get_counter_moves_bb(bb_current, bb_open):
    MOVES_local = MOVES
    res = np.uint64(0)

    bb_opponent = ~bb_open ^ bb_current

    for k in range(64):
        move = MOVES_local[k]

        if (move & bb_open) != 0:
            bb_after = bb_current | move
            bb_remaining = bb_open ^ move

            # Counter-attack
            if get_winning_moves_bb(bb_after, bb_remaining) != 0:
                res |= move

            # Otherwise, prevent double threats
            else:
                odt = get_double_threat_moves_bb(bb_opponent, bb_remaining)
                if odt == 0:
                    res |= move

    return res


def make_random_u64(N, rng=None):
    """Generate random uint64 numbers outside Numba."""
    if rng is None:
        rng = np.random.default_rng()

    low = rng.integers(2**32, size=N, dtype=np.uint64)
    high = rng.integers(2**32, size=N, dtype=np.uint64)

    return (high << np.uint64(32)) | low


# @nb.njit
# def bit_count_u64(arr):
#     res = np.zeros(64, dtype=np.int64)

#     for x in arr:
#         for k in range(64):
#             res[k] += (x >> k) & 1

#     return res


# @nb.njit(parallel=True)
# def mc_scores(bb_current, bb_open, rs):
#     N = rs.shape[0]

#     scores = np.zeros(64, dtype=np.int64)
#     sims = np.empty(N, dtype=np.uint64)

#     for i in range(N):
#         sims[i] = bb_open & get_winning_tiles_bb(bb_current | (rs[i] & bb_open))

#     scores = bit_count_u64(sims)

#     return scores


@nb.njit
def add_bits_to_scores(scores, bb):
    for k in range(64):
        scores[k] += (bb >> k) & 1


@nb.njit
def get_mc_move_bb(bb_current, bb_open, rs):
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


def mc_score_bot(position, current_player, timer, _):
    moves = [(i, j) for i in range(8) for j in range(8) if position[i][j] == 0]

    remaining_time = timer["times"][current_player]
    start_total = time.time()

    if remaining_time - (time.time() - start_total) <= MIN_TIME:
        return random.choice(moves), None

    bitboards = board_to_bitboards(position)
    bb_current = np.uint64(bitboards[current_player])
    bb_opponent = np.uint64(bitboards[1 - current_player])
    bb_open = open_spots(bitboards)

    # 1. Win immediately
    winning_moves = get_winning_moves_bb(bb_current, bb_open)
    if winning_moves:
        print("Find winning moves:", time.time() - start_total)
        prettyprint(winning_moves)
        return random.choice(bb_to_moves(winning_moves)), None

    if remaining_time - (time.time() - start_total) <= MIN_TIME:
        return random.choice(moves), None

    # 2. Block opponent immediate win
    opponent_winning_moves = get_winning_moves_bb(bb_opponent, bb_open)
    if opponent_winning_moves:
        print("Block threats:", time.time() - start_total)
        prettyprint(opponent_winning_moves)
        return random.choice(bb_to_moves(opponent_winning_moves)), None

    if remaining_time - (time.time() - start_total) <= MIN_TIME:
        return random.choice(moves), None

    # 3. Create double threat
    double_threat_moves = get_double_threat_moves_bb(bb_current, bb_open)
    if double_threat_moves:
        print("Find double threats:", time.time() - start_total)
        prettyprint(double_threat_moves)
        return random.choice(bb_to_moves(double_threat_moves)), None

    if remaining_time - (time.time() - start_total) <= MIN_TIME:
        return random.choice(moves), None

    # 4. Block opponent double threats
    opponent_double_threats = get_double_threat_moves_bb(bb_opponent, bb_open)
    if opponent_double_threats:
        counter_moves = get_counter_moves_bb(bb_current, bb_open)
        if counter_moves:
            print("Block double threats:", time.time() - start_total)
            prettyprint(counter_moves)
            return random.choice(bb_to_moves(counter_moves)), None
        # Better block one threat than nothing
        print("Block one of multiple threats:", time.time() - start_total)
        prettyprint(opponent_double_threats)
        return random.choice(bb_to_moves(opponent_double_threats)), None

    if remaining_time - (time.time() - start_total) <= MIN_TIME:
        return random.choice(moves), None

    # 5. Monte-Carlo
    N = 10000
    rs = make_random_u64(N)
    movemc = get_mc_move_bb(bb_current, bb_open, rs)
    print("Monte Carlo", time.time() - start_total)
    prettyprint(movemc)
    return random.choice(bb_to_moves(movemc)), None

    print("Default:", time.time() - start_total)
    return random.choice(moves), None
