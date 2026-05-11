import numba as nb
import numpy as np


from .data import BOARD_TILES, WIN_MASKS_ALL_BOARD, MASKS_BY_CELL, MASK_BY_CELL_COUNT, NEIGHBORS, NEIGHBOR_COUNT, WIN_MASKS_INDEXES


U8 = np.uint8
U64 = np.uint64


BT = np.array(BOARD_TILES, dtype=U64)
WMA = np.array(WIN_MASKS_ALL_BOARD, dtype=U64)
MBC = np.array(MASKS_BY_CELL, dtype=U64)
MBC_COUNT = np.array(MASK_BY_CELL_COUNT, dtype=U8)
NBS = np.array(NEIGHBORS, dtype=U8)
NBS_COUNT = np.array(NEIGHBOR_COUNT, dtype=U8)
WMI = np.array(WIN_MASKS_INDEXES, dtype=U64)
MOVES = U64(1) << np.arange(64, dtype=U64)


@nb.njit("b1(u8, u1)", inline="always")
def _has_align5_with_cell(bb: U64, cell: U8) -> bool:

    for move_nb in range(MBC_COUNT[cell]):
        mask = MBC[cell, move_nb]

        if (bb & mask) == mask:
            return True

    return False


@nb.njit("u8(u8, u8)", inline="always")
def _get_align5(bb_current: U64, bb_open: U64) -> U64:
    """Find moves that would create an immediate win for the current player."""
    winning_moves = U64(0)

    for cell in range(64):
        move = MOVES[cell]

        if (bb_open & move) and _has_align5_with_cell(bb_current, cell):
            winning_moves |= move

    return winning_moves


@nb.njit("b1(u8, u8)", inline="always")
def _has_double_threat(bb_current: U64, bb_open: U64) -> bool:

    open_ = bb_open

    while open_:

        move = open_ & -open_
        open_ ^= move

        winning_moves = _get_align5(bb_current | move, bb_open ^ move)

        if winning_moves & (winning_moves - U64(1)):
            return True

    return False


@nb.njit("u8(u8, u8)", inline="always")
def _get_double_threats(bb_current: U64, bb_open: U64) -> U64:
    """Find moves that create multiple winning opportunities (double threats)."""
    double_threats = U64(0)

    for cell in range(64):
        move = MOVES[cell]

        if bb_open & move:
            bb_current ^= move
            bb_open ^= move

            winning_moves = U64(0)
            for k in range(NBS_COUNT[cell]):
                cell2 = NBS[cell, k]

                m = MOVES[cell2]

                if (bb_open & m) and _has_align5_with_cell(bb_current, cell2):
                    winning_moves |= m

            bb_current ^= move
            bb_open ^= move

            if winning_moves & (winning_moves - U64(1)):  # if double threat
                double_threats |= move

    return double_threats


# @nb.njit
@nb.njit("u8(u8, u8, u8)", inline="always")
def _get_counter_moves(bb_current: U64, bb_opponent: U64, bb_open: U64) -> U64:
    """Find moves that counter the opponent's threats."""
    res = U64(0)

    open_ = bb_open

    while open_:

        move = open_ & -open_
        open_ ^= move

        bb_remaining = bb_open ^ move

        # Counter-attack
        if _get_align5(bb_current | move, bb_remaining):  # TODO: if has threat
            res |= move

        # Otherwise, prevent double threats
        else:
            if not _has_double_threat(bb_opponent, bb_remaining):  # TODO: only check odt bb (_opponent_still_has_double_threat)
                res |= move

    return res


@nb.njit("u8(u8, u8)", inline="never")
def get_forced_moves(bb_current: U64, bb_opponent: U64) -> U64:
    """Return moves either forced (defense) or forcing (attacking)."""
    bb_open = ~(bb_current | bb_opponent)

    # --- IMMEDIATE WIN ---
    a5 = _get_align5(bb_current, bb_open)
    if a5:
        return a5

    # --- OPPONENT WINNING THREAT ---
    o5 = _get_align5(bb_opponent, bb_open)
    if o5:
        return o5

    # --- DOUBLE THREATS ---
    dt = _get_double_threats(bb_current, bb_open)
    if dt:
        return dt

    # --- OPPONENT DOUBLE THREATS ---
    ot = _get_double_threats(bb_opponent, bb_open)
    if ot:
        # Either find a counter move
        cm = _get_counter_moves(bb_current, bb_opponent, bb_open)
        if cm:
            return cm

        return ot  # or atleast block one square

    return U64(0)
