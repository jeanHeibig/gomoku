import numba as nb
import numpy as np

from .hyperparameters import CACHE


I8 = np.int8
U8 = np.uint8
U64 = np.uint64


MOVES = U64(1) << np.arange(64, dtype=U64)


@nb.njit(
    "Tuple((u8[:], u1[:], u1))(u1[:], u8)",
    inline="always", cache=CACHE,
)
def sort_moves(move_scores, allowed_moves: U64):
    """Return moves sorted by descending heuristic score."""

    moves = np.empty(64, dtype=U64)
    move_indices = np.empty(64, dtype=U8)
    scores = np.empty(64, dtype=U8)

    mv_nb = U8(0)

    # Collect valid moves
    for k in range(64):

        s = move_scores[k]

        if s and (allowed_moves & MOVES[k]):

            moves[mv_nb] = MOVES[k]
            move_indices[mv_nb] = U8(k)
            scores[mv_nb] = s

            mv_nb += U8(1)

    # Insertion sort (descending)
    for i in range(1, mv_nb):

        m = moves[i]
        idx = move_indices[i]
        s = scores[i]

        j = i - 1

        while j >= 0 and scores[j] < s:

            moves[j + 1] = moves[j]
            move_indices[j + 1] = move_indices[j]
            scores[j + 1] = scores[j]

            j -= 1

        moves[j + 1] = m
        move_indices[j + 1] = idx
        scores[j + 1] = s

    return moves, move_indices, mv_nb


@nb.njit("void(u8[:], u1[:], u1, u1)", inline="always", cache=CACHE)
def move_to_front(
    moves,
    move_indices,
    mv_nb: U8,
    tt_move_idx: U8,
):
    """Move target move to front of move list."""
    tt_move_bb = U64(1) << tt_move_idx

    for i in range(mv_nb):

        if moves[i] == tt_move_bb:

            # Swap move bitboards
            tmp_move = moves[0]
            moves[0] = moves[i]
            moves[i] = tmp_move

            # Swap move indices
            tmp_idx = move_indices[0]
            move_indices[0] = move_indices[i]
            move_indices[i] = tmp_idx

            return
