import numba as nb
import numpy as np

from .hyperparameters import CACHE
from .data import WIN_MASKS_ALL_BOARD, RANDOM_GAMES

I8 = np.int8
I16 = np.int16
I32 = np.int32
U64 = np.uint64


WMA = np.array(WIN_MASKS_ALL_BOARD, dtype=U64)
HZM = WMA[:32]
VTM = WMA[32:64]
DGM = WMA[64:80]
ADM = WMA[80:]
N_GAMES = 64
RG = np.array(RANDOM_GAMES[:N_GAMES], dtype=U64)
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

    score_current = I16(0)
    score_opponent = I16(0)
    for cell in range(64):
        threat_current_number = I16(0)
        threat_opponent_number = I16(0)

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

        if threat_current_number == I16(2):
            score_current += I16(1)
        elif threat_current_number >= I16(3):
            score_current += I16(3)

        if threat_opponent_number == I16(2):
            score_opponent += I16(1)
        elif threat_opponent_number >= I16(3):
            score_opponent += I16(3)

    total = score_current + score_opponent
    if not total:
        return I8(0)

    strategic_score = I8(((score_current - score_opponent) << I16(6)) // total)

    bb_open = ~(bb_current | bb_opponent)
    monte_carlo_count = I8(0)

    for t in range(N_GAMES):
        bb_current_completed = bb_current | (RG[t] & bb_open)
        bb_opponent_completed = bb_opponent | (~RG[t] & bb_open)

        # Compute winning tiles for the random position
        for k in range(96):
            m = WMA[k]
            if (bb_current_completed & m) == m:
                monte_carlo_count += I8(1)
            if (bb_opponent_completed & m) == m:
                monte_carlo_count -= I8(1)

    monte_carlo_count >>= I8(3)

    return strategic_score + monte_carlo_count
