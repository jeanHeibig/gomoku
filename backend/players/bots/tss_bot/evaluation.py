import numba as nb
import numpy as np

from .hyperparameters import CACHE
from .data import WIN_MASKS_ALL_BOARD

I8 = np.int8
U64 = np.uint64


HZM = np.array(WIN_MASKS_ALL_BOARD[:32], dtype=U64)
VTM = np.array(WIN_MASKS_ALL_BOARD[32:64], dtype=U64)
DGM = np.array(WIN_MASKS_ALL_BOARD[64:80], dtype=U64)
ADM = np.array(WIN_MASKS_ALL_BOARD[80:], dtype=U64)
MOVES = U64(1) << np.arange(64, dtype=U64)


@nb.njit("i1(u8, u8)", cache=CACHE)
def fast_evaluation(bb_current: U64, bb_opponent: U64) -> I8:
    """Estimate the net game score for a board position."""
    bb_current_filled = ~bb_opponent
    bb_opponent_filled = ~bb_current

    bb_current_horizontal = U64(0)
    for mask in HZM:
        if (bb_current_filled & mask) == mask:
            bb_current_horizontal |= mask
    bb_current_vertical = U64(0)
    for mask in VTM:
        if (bb_current_filled & mask) == mask:
            bb_current_vertical |= mask
    bb_current_diagonal = U64(0)
    for mask in DGM:
        if (bb_current_filled & mask) == mask:
            bb_current_diagonal |= mask
    bb_current_antidiag = U64(0)
    for mask in ADM:
        if (bb_current_filled & mask) == mask:
            bb_current_antidiag |= mask

    bb_opponent_horizontal = U64(0)
    for mask in HZM:
        if (bb_opponent_filled & mask) == mask:
            bb_opponent_horizontal |= mask
    bb_opponent_vertical = U64(0)
    for mask in VTM:
        if (bb_opponent_filled & mask) == mask:
            bb_opponent_vertical |= mask
    bb_opponent_diagonal = U64(0)
    for mask in DGM:
        if (bb_opponent_filled & mask) == mask:
            bb_opponent_diagonal |= mask
    bb_opponent_antidiag = U64(0)
    for mask in ADM:
        if (bb_opponent_filled & mask) == mask:
            bb_opponent_antidiag |= mask

    score = I8(0)
    for cell in range(64):
        threat_current_number = I8(0)
        threat_opponent_number = I8(0)

        if bb_current_horizontal & MOVES[cell]:
            threat_current_number += 1
        if bb_current_vertical & MOVES[cell]:
            threat_current_number += 1
        if bb_current_diagonal & MOVES[cell]:
            threat_current_number += 1
        if bb_current_antidiag & MOVES[cell]:
            threat_current_number += 1

        if bb_opponent_horizontal & MOVES[cell]:
            threat_opponent_number += 1
        if bb_opponent_vertical & MOVES[cell]:
            threat_opponent_number += 1
        if bb_opponent_diagonal & MOVES[cell]:
            threat_opponent_number += 1
        if bb_opponent_antidiag & MOVES[cell]:
            threat_opponent_number += 1

        if threat_current_number == I8(2):
            score += I8(1)
        elif threat_current_number >= I8(3):
            score += I8(3)

        if threat_opponent_number == I8(2):
            score -= I8(1)
        elif threat_opponent_number >= I8(3):
            score -= I8(3)

    return score
