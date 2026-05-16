import numba as nb
import numpy as np
import numpy.typing as npt

from .hyperparameters import CACHE


I8 = np.int8
U8 = np.uint8
U64 = np.uint64


MOVES = U64(1) << np.arange(64, dtype=U64)


@nb.njit(
    "Tuple((u1[:], u1))(u1[:], u8)",
    inline="always", cache=CACHE,
)
def sort_moves(move_scores: npt.NDArray[U8], allowed_moves: U64) -> tuple[npt.NDArray[U8], U8]:
    """Return move indexes sorted by descending heuristic score."""

    move_indices = np.empty(64, dtype=U8)
    scores = np.empty(64, dtype=U8)

    mv_nb = U8(0)

    # Collect valid moves
    for k in range(64):

        s = move_scores[k]

        if s and (allowed_moves & MOVES[k]):

            move_indices[mv_nb] = U8(k)
            scores[mv_nb] = s

            mv_nb += U8(1)

    # Insertion sort (descending)
    for i in range(1, mv_nb):

        idx = move_indices[i]
        s = scores[i]

        j = i - 1

        while j >= 0 and scores[j] < s:

            move_indices[j + 1] = move_indices[j]
            scores[j + 1] = scores[j]

            j -= 1

        move_indices[j + 1] = idx
        scores[j + 1] = s

    return move_indices, mv_nb


@nb.njit("void(u1[:], u1, u1)", inline="always", cache=CACHE)
def move_to_front(
    move_indices: npt.NDArray[U8],
    mv_nb: U8,
    tt_move_idx: U8,
) -> None:
    """Move target move to front of move list."""
    for i in range(mv_nb):

        if move_indices[i] == tt_move_idx:

            # Swap move indices  # TODO: insertion sort rather than swap
            tmp_idx = move_indices[0]
            move_indices[0] = move_indices[i]
            move_indices[i] = tmp_idx

            return
