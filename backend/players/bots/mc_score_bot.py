import time
import random

import numpy as np

from ...board.masks.board_tiles import BOARD_TILES
from ...board.bitboard import board_to_bitboards, open_spots, winning_tiles, bb_to_moves, set_bit, ij_to_bit

BT = np.array(BOARD_TILES, dtype=np.uint64)  # TODO import directly from a numpy precomputed masks library
MOVES = np.uint64(1) << np.arange(64, dtype=np.uint64)

_MIN_TIME = 1  # Seconds allowed to do the search. Otherwise, play random.


@np.vectorize
def get_winning_moves(bb_player, bb_open):
    return np.bitwise_or.reduce(bb_open & winning_tiles(bb_player | (BT & bb_open)))


@np.vectorize
def get_double_threat_moves(bb_player, bb_open):
    moves = MOVES[(MOVES & bb_open).astype(bool)]
    dt = np.bitwise_or.reduce(
        (np.bitwise_count(get_winning_moves(bb_player | moves, bb_open ^ moves)) > 1) * moves
    )
    return dt


def _get_counter_moves(moves, bb, currentPlayer):
    bb_open = np.uint64(open_spots(bb))
    cm = np.uint64(0)
    for (i, j) in moves:
        current_bit = np.uint64(ij_to_bit(i, j))
        bb_counter = np.uint64(set_bit(bb[currentPlayer], i, j))
        bb_remaining = bb_open ^ current_bit
        if get_winning_moves(bb_counter, bb_remaining):
            # We found a counter-attack !
            cm |= current_bit
        else:
            # We need to prevent double threats
            dt = np.uint64(0)
            for (k, l) in moves:
                if (k, l) != (i, j):
                    current_bit2 = np.uint64(ij_to_bit(k, l))
                    bb_threat = np.uint64(set_bit(bb[1 - currentPlayer], k, l))
                    bb_remaining2 = bb_remaining ^ current_bit2
                    if np.bitwise_count(get_winning_moves(bb_threat, bb_remaining2)) > 1:
                        dt |= current_bit2
            if not dt:  # If there's no more double threat
                cm |= current_bit
    return bb_to_moves(cm)


def _get_mc_score(moves, bb, current_player, N):
    scores = {(i, j): 0 for (i, j) in moves}
    bb_open = np.uint64(open_spots(bb))
    I64 = 2 ** 64 - 1
    for _ in range(N):
        r_current = np.uint64(random.randint(0, I64))
        bb_current = np.uint64(bb[current_player]) | (r_current & bb_open)
        movesCurrent = bb_to_moves(bb_open & winning_tiles(bb_current))
        for (i, j) in movesCurrent:
            scores[(i, j)] += 1

    return scores


def mc_score_bot(position, current_player, timer, _):
    # Get all possible moves (empty spots)
    moves = [(i, j) for i in range(8) for j in range(8) if position[i][j]==0]
    times = timer["times"]
    remaining_time = times[current_player]

    start_time = time.time()
    if remaining_time > _MIN_TIME:
        # Convert board to bitboards and find winning moves
        bb = board_to_bitboards(position)
        winning_moves = get_winning_moves(np.uint64(bb[current_player]), open_spots(bb))
        if winning_moves:
            elapsed = time.time() - start_time
            print("Find winning moves:", elapsed)
            return random.choice(bb_to_moves(winning_moves)), None

    elapsed = time.time() - start_time
    print("Find winning moves:", elapsed)
    start_time = time.time()
    if remaining_time - elapsed > _MIN_TIME:
        opponent_winning_moves = get_winning_moves(np.uint64(bb[1 - current_player]), open_spots(bb))
        if opponent_winning_moves:
            elapsed += time.time() - start_time
            print("Block threats:", elapsed)
            return random.choice(bb_to_moves(opponent_winning_moves)), None

    elapsed += time.time() - start_time
    print("Block threats:", elapsed)
    start_time = time.time()
    if remaining_time - elapsed > _MIN_TIME:
        double_threat_moves = get_double_threat_moves(np.uint64(bb[current_player]), open_spots(bb))
        if double_threat_moves:
            elapsed += time.time() - start_time
            print("Find double threats:", elapsed)
            return random.choice(bb_to_moves(double_threat_moves)), None

    elapsed += time.time() - start_time
    print("Find double threats:", elapsed)
    start_time = time.time()
    if remaining_time - elapsed > _MIN_TIME:
        if get_double_threat_moves(np.uint64(bb[1 - current_player]), open_spots(bb)):
            # Opponent has lethal threat !
            # We must counter that, either by having a threat or by removing double threats.
            counter_moves = _get_counter_moves(moves, bb, current_player)
            if counter_moves:  # if we did not find any counter, too bad...
                elapsed += time.time() - start_time
                print("Block double threats:", elapsed)
                return random.choice(counter_moves), None

    elapsed += time.time() - start_time
    print("Block double threats:", elapsed)
    start_time = time.time()
    if remaining_time - elapsed > _MIN_TIME:
        # We do a random evaluation function:
        N = 1000
        scores = _get_mc_score(moves, bb, current_player, N)

        imax, jmax, smax = None, None, -float("inf")
        for (i, j) in moves:
            if scores[(i, j)] > smax:
                imax, jmax, smax = i, j, scores[(i, j)]
        elapsed += time.time() - start_time
        print("Monte Carlo:", elapsed)
        return (imax, jmax), None


    # Fallback to random move if no winning move or low time
    return random.choice(moves), None
