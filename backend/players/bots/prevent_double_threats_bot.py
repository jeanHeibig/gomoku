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
    M_local = MOVES
    res = np.uint64(0)

    for k in range(64):
        move = M_local[k]

        if (move & bb_open) != 0:
            bb_after = bb_current | move
            bb_remaining = bb_open ^ move

            wm = get_winning_moves_bb(bb_after, bb_remaining)

            if bitwise_count(wm) > 1:
                res |= move

    return res


@nb.njit
def get_counter_moves_bb(bb_current, bb_open):
    M_local = MOVES
    res = np.uint64(0)

    bb_opponent = ~bb_open ^ bb_current

    for k in range(64):
        move = M_local[k]

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


def prevent_double_threats_bot(position, current_player, timer, _):
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

    print("Default:", time.time() - start_total)
    return random.choice(moves), None
