import numba as nb
import numpy as np
import numpy.typing as npt

from .hyperparameters import CACHE
from .data import WIN_MASKS_ALL_BOARD, WIN_MASKS_INDEXES, RANDOM_GAMES


I8 = np.int8
U8 = np.uint8
U32 = np.uint32
U64 = np.uint64


WMA = np.array(WIN_MASKS_ALL_BOARD, dtype=U64)
WMI = np.array(WIN_MASKS_INDEXES, dtype=U64)
N_GAMES = 128
RG = np.array(RANDOM_GAMES, dtype=U64)
HZM = WMA[:32]
VTM = WMA[32:64]
DGM = WMA[64:80]
ADM = WMA[80:]
MOVES = U64(1) << np.arange(64, dtype=U64)


@nb.njit("u1[:](u8, u8, u8)", cache=CACHE)
def monte_carlo_heuristic(bb_current: U64, bb_opponent: U64, bb_open: U64) -> npt.NDArray[U8]:
    """Compute a heuristic score grid for each empty tile on the board.

    The function evaluates every random fill scenario from the precomputed
    RG table and awards points for potential winning tile contributions.
    """
    count = np.zeros(64, dtype=U8)

    # Monte-Carlo evaluation
    for t in range(N_GAMES):
        bb_current_completed = bb_current | (RG[t] & bb_open)
        bb_opponent_completed = bb_opponent | (~RG[t] & bb_open)

        # Compute winning tiles for the random position
        for k in range(96):
            m = WMA[k]
            if ((bb_current_completed & m) == m) or ((bb_opponent_completed & m) == m):
                for wt_idx in WMI[k]:
                    count[wt_idx] += U8(1)

    return count


@nb.njit("u1[:](u8, u8, u8)", cache=CACHE)
def tactical_heuristic(bb_current: U64, bb_opponent: U64, bb_open: U64) -> npt.NDArray[U8]:
    """Compute a heuristic score based on free directions."""
    scores = np.zeros(64, dtype=U8)

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

    for cell in range(64):
        if ~bb_open & MOVES[cell]:  # Do not count occupied cells
            continue

        threat_current_number = U8(0)
        threat_opponent_number = U8(0)

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

        if threat_current_number == U8(2):
            scores[cell] += U8(21)
        elif threat_current_number == U8(3):
            scores[cell] += U8(63)
        elif threat_current_number == U8(4):
            scores[cell] += U8(126)

        if threat_opponent_number == U8(2):
            scores[cell] += U8(13)
        elif threat_opponent_number == U8(3):
            scores[cell] += U8(39)
        elif threat_opponent_number == U8(4):
            scores[cell] += U8(78)

    # print(scores.reshape((8,8)))
    return scores
