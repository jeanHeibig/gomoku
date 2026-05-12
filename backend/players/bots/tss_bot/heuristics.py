import numba as nb
import numpy as np
import numpy.typing as npt

from .data import WIN_MASKS_ALL_BOARD, WIN_MASKS_INDEXES, RANDOM_GAMES


U8 = np.uint8
U64 = np.uint64


WMA = np.array(WIN_MASKS_ALL_BOARD, dtype=U64)
WMI = np.array(WIN_MASKS_INDEXES, dtype=U64)
RG = np.array(RANDOM_GAMES, dtype=U64)
MOVES = U64(1) << np.arange(64, dtype=U64)


@nb.njit("u1[:](u8, u8, u8)")
def fast_statistics(bb_current: U64, bb_opponent: U64, bb_open: U64) -> npt.NDArray[U8]:
    """Compute a heuristic score grid for each empty tile on the board.

    The function evaluates every random fill scenario from the precomputed
    RG table and awards points for potential winning tile contributions.
    """
    scores = np.zeros(64, dtype=U8)

    # Monte-Carlo evaluation
    for t in range(255):
        bb_current_completed = bb_current | (RG[t] & bb_open)
        bb_opponent_completed = bb_opponent | (~RG[t] & bb_open)

        # Compute winning tiles for the random position
        for k in range(96):
            m = WMA[k]
            if ((bb_current_completed & m) == m) or ((bb_opponent_completed & m) == m):
                for wt_idx in WMI[k]:
                    scores[wt_idx] += 1

                    # if scores[wt_idx] == 255:  # Debug
                    #     raise ValueError("score overflow")

    for idx in range(64):
        bb_idx = MOVES[idx]
        if ~bb_open & bb_idx:
            scores[idx] = 0

    # print(scores.reshape((8,8)))
    return scores
