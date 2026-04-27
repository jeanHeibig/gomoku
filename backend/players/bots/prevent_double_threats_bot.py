import time
import random

from ...board.masks.board_tiles import BOARD_TILES
from ...board.bitboard import board_to_bitboards, open_spots, winning_tiles, bb_to_moves, set_bit, ij_to_bit

_MIN_TIME = 2  # Seconds allowed to do the search. Otherwise, play random.


def _get_winning_moves(bb_player, bb_open):
    """Get moves that would complete a five-in-a-row for the player.

    Args:
        bb_player: Bitboard of the current player's stones.
        bb_open: Bitboard of open spots on the board.

    Returns:
        List of (i, j) tuples representing winning moves.
    """
    wm = 0
    for bb_check in BOARD_TILES:
        wm |= bb_open & winning_tiles(bb_player | (bb_check & bb_open))
    return bb_to_moves(wm)


def _get_double_threat_moves(moves, bb_player, bb_open):
    dt = 0
    for (i, j) in moves:  # TODO: Do not look at all moves, only d <= 2
        current_bit = ij_to_bit(i, j)
        bb_threat = set_bit(bb_player, i, j)
        bb_remaining = bb_open ^ current_bit
        if len(_get_winning_moves(bb_threat, bb_remaining)) > 1:
            dt |= current_bit
    return bb_to_moves(dt)


def _get_counter_moves(moves, bb, currentPlayer):
    bb_open = open_spots(bb)
    cm = 0
    for (i, j) in moves:
        current_bit = ij_to_bit(i, j)
        bb_counter = set_bit(bb[currentPlayer], i, j)
        bb_remaining = bb_open ^ current_bit
        if _get_winning_moves(bb_counter, bb_remaining):
            # We found a counter-attack !
            cm |= current_bit
        else:
            # We need to prevent double threats
            dt = 0
            for (k, l) in moves:
                if (k, l) != (i, j):
                    current_bit2 = ij_to_bit(k, l)
                    bb_threat = set_bit(bb[1 - currentPlayer], k, l)
                    bb_remaining2 = bb_remaining ^ current_bit2
                    if len(_get_winning_moves(bb_threat, bb_remaining2)) > 1:
                        dt |= current_bit2
            if not dt:  # If there's no more double threat
                cm |= current_bit
    return bb_to_moves(cm)


def prevent_double_threats_bot(position, current_player, timer, _):
    # Get all possible moves (empty spots)
    moves = [(i, j) for i in range(8) for j in range(8) if position[i][j]==0]
    times = timer["times"]
    remaining_time = times[current_player]

    start_time = time.time()
    if remaining_time > _MIN_TIME:
        # Convert board to bitboards and find winning moves
        bb = board_to_bitboards(position)
        winning_moves = _get_winning_moves(bb[current_player], open_spots(bb))
        if winning_moves:
            return random.choice(winning_moves), None

    elapsed = time.time() - start_time
    start_time = time.time()
    if remaining_time - elapsed > _MIN_TIME:
        opponent_winning_moves = _get_winning_moves(bb[1 - current_player], open_spots(bb))
        if opponent_winning_moves:
            return random.choice(opponent_winning_moves), None

    elapsed += time.time() - start_time
    start_time = time.time()
    if remaining_time - elapsed > _MIN_TIME:
        double_threat_moves = _get_double_threat_moves(moves, bb[current_player], open_spots(bb))
        if double_threat_moves:
            return random.choice(double_threat_moves), None

    elapsed += time.time() - start_time
    start_time = time.time()
    if remaining_time - elapsed > _MIN_TIME:
        if _get_double_threat_moves(moves, bb[1 - current_player], open_spots(bb)):
            # Opponent has lethal threat !
            # We must counter that, either by having a threat or by removing double threats.
            counter_moves = _get_counter_moves(moves, bb, current_player)
            if counter_moves:  # if we did not find any counter, too bad...
                return random.choice(counter_moves), None

    # Fallback to random move if no winning move or low time
    return random.choice(moves), None
