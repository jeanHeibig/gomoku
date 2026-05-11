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


@nb.njit("b1(u8, u8)", inline="always")
def _has_double_threat(bb_current: U64, bb_open: U64) -> bool:

    open_ = bb_open

    while open_:

        move = open_ & -open_
        open_ ^= move

        winning_moves = get_align5(bb_current | move, bb_open ^ move)

        if winning_moves & (winning_moves - U64(1)):
            return True

    return False


@nb.njit("u8(u8, u8)", inline="always")
def get_align5(bb_current: U64, bb_open: U64) -> U64:
    """Find moves that would create an immediate win for the current player."""
    winning_moves = U64(0)

    for cell in range(64):
        move = MOVES[cell]

        if (bb_open & move) and _has_align5_with_cell(bb_current, cell):
            winning_moves |= move

    return winning_moves


@nb.njit("u8(u8, u8)", inline="always")
def get_double_threats(bb_current: U64, bb_open: U64) -> U64:
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
def get_counter_moves(bb_current: U64, bb_opponent: U64, bb_open: U64) -> U64:
    """Find moves that counter the opponent's threats."""
    res = U64(0)

    open_ = bb_open

    while open_:

        move = open_ & -open_
        open_ ^= move

        bb_remaining = bb_open ^ move

        # Counter-attack
        if get_align5(bb_current | move, bb_remaining):  # TODO: if has threat
            res |= move

        # Otherwise, prevent double threats
        else:
            if not _has_double_threat(bb_opponent, bb_remaining):  # TODO: only check odt bb
                res |= move

    return res


@nb.njit("u8(u8, u8)", inline="never")
def get_forced_moves(bb_current: U64, bb_opponent: U64) -> U64:
    """Return moves either forced (defense) or forcing (attacking)."""
    bb_occupied = (bb_current | bb_opponent)
    bb_open = ~bb_occupied
    scores = np.zeros(64, dtype=np.int64)

    # Winning moves:
    res_current = U64(0)
    res_opponent = U64(0)

    for k in range(5):  # 5 non-concurrent masks
        move = BT[k] & bb_open
        bb_current_after = bb_current | move
        bb_opponent_after = bb_opponent | move

        wtc = U64(0)
        wto = U64(0)

        for i in range(96):
            m = WMA[i]
            if (bb_current_after & m) == m:
                wtc |= m
            elif (bb_opponent_after & m) == m:
                wto |= m

        if wtc != 0:
            res_current |= (wtc & move)
        if wto != 0:
            res_opponent |= (wto & move)

    if res_current != 0:  # Win in one found
        fill_forced_squared(scores, bb_occupied, res_current)
        return scores

    if res_opponent != 0:  # Threat in one found
        fill_forced_squared(scores, bb_occupied, res_opponent)
        return scores

    # Create double threat
    double_threat_moves = get_double_threats(bb_current, bb_open)
    if double_threat_moves:
        fill_forced_squared(scores, bb_occupied, double_threat_moves)
        return scores

    # Block opponent double threats
    opponent_double_threats = get_double_threats(bb_opponent, bb_open)
    if opponent_double_threats:
        counter_moves = get_counter_moves(bb_current, bb_opponent, bb_open)
        if counter_moves:
            fill_forced_squared(scores, bb_occupied, counter_moves)
            return scores

    # Monte-Carlo evaluation
    for t in range(N):
        bb_current_completed = bb_current | (RG[t] & bb_open)
        bb_opponent_completed = bb_opponent | (~RG[t] & bb_open)

        # Compute winning tiles for the random position
        for k in range(96):
            m = WMA[k]
            if (bb_current_completed & m) == m:
                for wt_idx in WMI[k]:
                    scores[wt_idx] += 5
            if (bb_opponent_completed & m) == m:
                for wt_idx in WMI[k]:
                    scores[wt_idx] += 3

    # Improve the score of threat moves
    threats = st_bb(bb_current, bb_open)

    for idx in range(64):
        bb_idx = MOVES[idx]
        if bb_occupied & bb_idx:
            scores[idx] = -1
        elif bb_idx:
            if threats & bb_idx:
                scores[idx] += np.int64(1) << 32
        else:
            scores[idx] = -2

    # print(scores.reshape((8,8)))
    return scores
