from enum import IntEnum
from time import time

# import numba as nb
import numpy as np

from .data import BOARD_TILES, WIN_MASKS_ALL_BOARD, WIN_MASKS_INDEXES, RANDOM_GAMES, REP_MASKS, ZOBRIST, LOG2
from .canonicalization import canonicalize, apply_inverse_symmetry

U8 = np.uint8
U64 = np.uint64


TT_SIZE = U64(1) << 20
TT_MASK = TT_SIZE - 1
K = 12

BT = np.array(BOARD_TILES, dtype=U64)
WMA = np.array(WIN_MASKS_ALL_BOARD, dtype=U64)
WMI = np.array(WIN_MASKS_INDEXES, dtype=U64)
RG = np.array(RANDOM_GAMES, dtype=U64)
MOVES = U64(1) << np.arange(64, dtype=U64)
RM = np.array(REP_MASKS, dtype=U64)
ZB = np.array(ZOBRIST, dtype=U64)
EXACT = U8(0)
LOWER = U8(1)
UPPER = U8(2)
ONES = U64(0xffffffffffffffff)
INF = np.int64(0x7fffffffffffffff)
LOG2 = np.array(LOG2, dtype=U8)


class Square(IntEnum):
    A8 = 0
    B8 = 1
    C8 = 2
    D8 = 3
    E8 = 4
    F8 = 5
    G8 = 6
    H8 = 7
    A7 = 8
    B7 = 9
    C7 = 10
    D7 = 11
    E7 = 12
    F7 = 13
    G7 = 14
    H7 = 15
    A6 = 16
    B6 = 17
    C6 = 18
    D6 = 19
    E6 = 20
    F6 = 21
    G6 = 22
    H6 = 23
    A5 = 24
    B5 = 25
    C5 = 26
    D5 = 27
    E5 = 28
    F5 = 29
    G5 = 30
    H5 = 31
    A4 = 32
    B4 = 33
    C4 = 34
    D4 = 35
    E4 = 36
    F4 = 37
    G4 = 38
    H4 = 39
    A3 = 40
    B3 = 41
    C3 = 42
    D3 = 43
    E3 = 44
    F3 = 45
    G3 = 46
    H3 = 47
    A2 = 48
    B2 = 49
    C2 = 50
    D2 = 51
    E2 = 52
    F2 = 53
    G2 = 54
    H2 = 55
    A1 = 56
    B1 = 57
    C1 = 58
    D1 = 59
    E1 = 60
    F1 = 61
    G1 = 62
    H1 = 63


class Outcome(IntEnum):
    UNKNOWN = 0
    WIN = 1
    DRAW = 2
    LOSS = 3


OPENING_BOOK = {
    # --- START ---
    (0, 0): (Square.D5, 64, Outcome.DRAW),
    (134217728, 34628173824): (Square.F6, 60, Outcome.UNKNOWN),

    # --- HANDICAP ---
    (134217728, 0): (Square.E4, 0, Outcome.UNKNOWN),
    (34628173824, 134217728): (Square.E4, 64, Outcome.WIN),
    (34762391552, 69256347648): (Square.D3, 64, Outcome.WIN),
    (35299262464, 8865886240768): (Square.F6, 64, Outcome.WIN),
}


# @nb.njit
def fill_forced_squared(scores, bb_occupied, mask):
    MOVES_LOCAL = MOVES

    for idx in range(64):
        bb_idx = MOVES_LOCAL[idx]

        if bb_occupied & bb_idx:
            scores[idx] = -1
        elif mask & bb_idx:
            scores[idx] = 1
        else:
            scores[idx] = -2

    # print(scores.reshape((8,8)))


# @nb.njit
def bitwise_count(bb):  # np.bitwise_count not implemented yet in numba
    """
    Count the number of set bits (1s) in a 64-bit integer using bitwise operations.

    This function implements a bit counting algorithm that iterates through each set bit
    by clearing the least significant set bit in each iteration.

    Args:
        bb (U64): The 64-bit integer to count bits in.

    Returns:
        int: The number of set bits in the input.
    """
    c = 0
    while bb != 0:
        bb &= bb - U64(1)
        c +=1
    return c


# @nb.njit
def get_winning_tiles_bb(bb):
    """
    Find all tiles that are part of winning combinations for the given bitboard.

    This function checks all precomputed winning masks against the current bitboard
    and returns a bitboard containing all tiles that belong to winning lines.

    Args:
        bb (U64): Bitboard representing current stone positions.

    Returns:
        U64: Bitboard with bits set for tiles that are part of winning combinations.
    """
    WMA_LOCAL = WMA  # pylint: disable=invalid-name
    res = U64(0)

    for i in range(96):
        m = WMA_LOCAL[i]
        if (bb & m) == m:
            res |= m

    return res


# @nb.njit
def wm_bb(bb_current, bb_open):
    """
    Find moves that would create an immediate win for the current player.

    This function checks each possible move in open positions and determines
    if placing a stone there would complete a winning combination.

    Args:
        bb_current (U64): Bitboard of current player's stones.
        bb_open (U64): Bitboard of open positions on the board.

    Returns:
        U64: Bitboard with bits set for winning moves.
    """
    BT_LOCAL = BT  # pylint: disable=invalid-name
    res = U64(0)

    for k in range(5):  # 5 non-concurrent masks
        move = BT_LOCAL[k] & bb_open
        bb_after = bb_current | move

        wt = get_winning_tiles_bb(bb_after)

        if wt != 0:
            res |= (wt & move)

    return res


# @nb.njit
def dt_bb(bb_current, bb_open):
    """
    Find moves that create multiple winning opportunities (double threats).

    A double threat is a move that creates two or more different winning
    combinations simultaneously, making it very difficult for the opponent to block.

    Args:
        bb_current (U64): Bitboard of current player's stones.
        bb_open (U64): Bitboard of open positions on the board.

    Returns:
        U64: Bitboard with bits set for double threat moves.
    """
    MOVES_LOCAL = MOVES
    res = U64(0)

    for k in range(64):
        move = MOVES_LOCAL[k]

        if (move & bb_open) != 0:
            bb_after = bb_current | move
            bb_remaining = bb_open ^ move

            wm = wm_bb(bb_after, bb_remaining)

            if bitwise_count(wm) > 1:
                res |= move

    return res


# @nb.njit
def cm_bb(bb_current, bb_open):
    """
    Find moves that counter the opponent's threats.

    This function prioritizes moves that either create immediate counter-attacks
    or prevent the opponent from creating double threats.

    Args:
        bb_current (U64): Bitboard of current player's stones.
        bb_open (U64): Bitboard of open positions on the board.

    Returns:
        U64: Bitboard with bits set for counter moves.
    """
    MOVES_LOCAL = MOVES
    res = U64(0)

    bb_opponent = ~bb_open ^ bb_current

    for k in range(64):
        move = MOVES_LOCAL[k]

        if (move & bb_open) != 0:
            bb_after = bb_current | move
            bb_remaining = bb_open ^ move

            # Counter-attack
            if wm_bb(bb_after, bb_remaining) != 0:
                res |= move

            # Otherwise, prevent double threats
            else:
                odt = dt_bb(bb_opponent, bb_remaining)
                if odt == 0:
                    res |= move

    return res


# @nb.njit
def st_bb(bb_current, bb_open):
    MOVES_LOCAL = MOVES

    res = U64(0)

    for k in range(64):
        move = MOVES_LOCAL[k]

        if (move & bb_open) and (wm_bb(bb_current | move, bb_open ^ move) or dt_bb(bb_current | move, bb_open ^ move)):
            res |= move

    return res


# @nb.njit
def get_scores(bb_current, bb_opponent):
    """Compute a heuristic score grid for each empty tile on the board.

    The function evaluates every random fill scenario from the precomputed
    RG table and awards points for potential winning tile contributions.

    Args:
        bb_current (numpy.uint64): Bitboard of the current player's stones.
        bb_opponent (numpy.uint64): Bitboard of the opponent's stones.

    Returns:
        numpy.ndarray: An 8x8 int64 array of heuristic scores for each board cell.
            Occupied cells are assigned a score of -1.
    """
    WMA_LOCAL = WMA
    WMI_LOCAL = WMI
    RG_LOCAL = RG
    BT_LOCAL = BT
    MOVES_LOCAL = MOVES
    N = RG_LOCAL.shape[0]

    bb_occupied = (bb_current | bb_opponent)
    bb_open = ~bb_occupied
    scores = np.zeros(64, dtype=np.int64)

    # Winning moves:
    res_current = U64(0)
    res_opponent = U64(0)

    for k in range(5):  # 5 non-concurrent masks
        move = BT_LOCAL[k] & bb_open
        bb_current_after = bb_current | move
        bb_opponent_after = bb_opponent | move

        wtc = U64(0)
        wto = U64(0)

        for i in range(96):
            m = WMA_LOCAL[i]
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
    double_threat_moves = dt_bb(bb_current, bb_open)
    if double_threat_moves:
        fill_forced_squared(scores, bb_occupied, double_threat_moves)
        return scores

    # Block opponent double threats
    opponent_double_threats = dt_bb(bb_opponent, bb_open)
    if opponent_double_threats:
        counter_moves = cm_bb(bb_current, bb_open)
        if counter_moves:
            fill_forced_squared(scores, bb_occupied, counter_moves)
            return scores

    # Monte-Carlo evaluation
    for t in range(N):
        bb_current_completed = bb_current | (RG_LOCAL[t] & bb_open)
        bb_opponent_completed = bb_opponent | (~RG_LOCAL[t] & bb_open)

        # Compute winning tiles for the random position
        for k in range(96):
            m = WMA_LOCAL[k]
            if (bb_current_completed & m) == m:
                for wt_idx in WMI_LOCAL[k]:
                    scores[wt_idx] += 5
            if (bb_opponent_completed & m) == m:
                for wt_idx in WMI_LOCAL[k]:
                    scores[wt_idx] += 3

    # Improve the score of threat moves
    threats = st_bb(bb_current, bb_open)

    for idx in range(64):
        bb_idx = MOVES_LOCAL[idx]
        if bb_occupied & bb_idx:
            scores[idx] = -1
        elif bb_idx:
            if threats & bb_idx:
                scores[idx] += np.int64(1) << 32
        else:
            scores[idx] = -2

    # print(scores.reshape((8,8)))
    return scores


# @nb.njit
def fast_eval(bb_current, bb_opponent):
    """Estimate the net game score for a board position.

    This function simulates each random completion scenario and increments the
    score when the current player can complete a winning pattern, while
    decrementing it when the opponent can do the same.

    Args:
        bb_current (numpy.uint64): Bitboard of the current player's stones.
        bb_opponent (numpy.uint64): Bitboard of the opponent's stones.

    Returns:
        numpy.int64: The aggregated score difference across all simulated fills.
            Positive values favor the current player, negative values favor the
            opponent.
    """
    WMA_LOCAL = WMA
    RG_LOCAL = RG
    N = RG_LOCAL.shape[0]

    bb_occupied = (bb_current | bb_opponent)
    bb_open = ~bb_occupied
    score = np.int64(0)

    for t in range(N):
        bb_current_completed = bb_current | (RG_LOCAL[t] & bb_open)
        bb_opponent_completed = bb_opponent | (~RG_LOCAL[t] & bb_open)

        # Compute winning tiles for the random position
        for k in range(96):
            m = WMA_LOCAL[k]
            if (bb_current_completed & m) == m:
                score += 1
            if (bb_opponent_completed & m) == m:
                score -= 1

    return score


def move_to_bb(i: int, j: int) -> int:
    """Convert row and column indices to a bitboard bit position.

    Args:
        i: The row index (0-7).
        j: The column index (0-7).

    Returns:
        An integer with the bit set at position i*8 + j.
    """
    return 1 << (i * 8 + j)


def board_to_bitboards(position: list[list[int]]) -> list[int]:
    """Convert a 2D board matrix into two bitboards.

    The returned list contains two integers: the first integer encodes
    player 1 stones and the second encodes player 2 stones. Each board
    cell maps to a bit at position `i * 8 + j` for row `i` and column
    `j`.

    Args:
        position: An 8x8 matrix of integers where 0 means empty, 1 means
            player 1, and 2 means player 2.

    Returns:
        A list of two bitboards `[player1_bb, player2_bb]`.
    """
    bitboards = [0, 0]
    for i in range(8):
        for j in range(8):
            if position[i][j] == 1:
                bitboards[0] |= move_to_bb(i, j)
            if position[i][j] == 2:
                bitboards[1] |= move_to_bb(i, j)
    return bitboards


def lookup_opening_moves(bb_current, bb_opponent):  # TODO: be precise with typing
    """Return opening move if position is in book, else None."""
    entry = OPENING_BOOK.get((bb_current, bb_opponent))

    if entry is None:
        return None

    move_cr = U64(1 << entry[0])
    return move_cr


# @nb.njit
def ctime():
    return time()
    # with nb.objmode(t="float64"):
    #     t = time()
    # return t


# @nb.njit
def compute_hash(bb_current, bb_opponent):  # TODO: incrementalize
    h = U64(0)

    bbc = bb_current
    bbo = bb_opponent
    idx = 0
    while bbc or bbo:
        if bbc & U64(1):
            h ^= ZB[0, idx]
        elif bbo & U64(1):
            h ^= ZB[1, idx]
        bbc >>= 1
        bbo >>= 1
        idx += 1

    return h


# @nb.njit
def bb2m(bb):
    """Convert a bitboard into a list of (i, j) move positions.

    Args:
        bb: A bitboard representing positions.

    Returns:
        A list of tuples (i, j) for each set bit in the bitboard.
    """
    b = U64(1)
    for i in range(8):
        for j in range(8):
            if bb & b:
                return (i, j)
            b <<= 1

# @nb.njit
def tt_probe(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags,
             key, depth, alpha, beta):
    idx = key & TT_MASK

    if TT_keys[idx] != key:
        return False, 0, U64(0), alpha, beta

    stored_depth = TT_depths[idx]
    stored_score = TT_scores[idx]
    stored_flag = TT_flags[idx]
    stored_move = TT_moves[idx]

    if stored_depth >= depth:
        if stored_flag == EXACT:
            return True, stored_score, stored_move, alpha, beta

        elif stored_flag == LOWER:
            if stored_score >= beta:
                return True, stored_score, stored_move, alpha, beta
            alpha = max(alpha, stored_score)

        elif stored_flag == UPPER:
            if stored_score <= alpha:
                return True, stored_score, stored_move, alpha, beta
            beta = min(beta, stored_score)

    return False, 0, stored_move, alpha, beta


# @nb.njit
def tt_store(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags,
             key, depth, score, flag, best_move):
    idx = key & TT_MASK

    if TT_keys[idx] == 0 or TT_depths[idx] <= depth:
        TT_keys[idx] = key
        TT_moves[idx] = best_move
        TT_depths[idx] = depth
        TT_scores[idx] = score
        TT_flags[idx] = flag


# @nb.njit
def is_winning(bb_current) -> bool:
    WMA_LOCAL = WMA

    for k in range(96):
        m = WMA_LOCAL[k]
        if (bb_current & m) == m:
            return True

    return False


# @nb.njit
def is_dead_draw(bb_current, bb_opponent):  # TODO: those draws should then be save in a LUT
    bb_open = ~(bb_current | bb_opponent)
    return not is_winning(bb_current | (bb_open & ONES)) and not is_winning(bb_opponent | (bb_open & ONES))


# @nb.njit
def sort_moves(move_scores):
    MOVES_LOCAL = MOVES

    moves = np.zeros(64, dtype=U64)
    scores = np.zeros(64, dtype=np.int64)

    mv_nb = 0

    # Collect valid moves
    for k in range(64):
        s = move_scores[k]
        if s >= 0:
            moves[mv_nb] = MOVES_LOCAL[k]
            scores[mv_nb] = s
            mv_nb += 1

    # Insertion sort (descending order)
    for i in range(1, mv_nb):
        m = moves[i]
        s = scores[i]

        j = i - 1
        while j >= 0 and scores[j] < s:
            moves[j + 1] = moves[j]
            scores[j + 1] = scores[j]
            j -= 1

        moves[j + 1] = m
        scores[j + 1] = s

    return moves, mv_nb


# @nb.njit
def move_to_front(moves, mv_nb, target_move):
    if target_move == U64(0):
        return

    for i in range(mv_nb):
        if moves[i] == target_move:
            # swap with first position
            tmp = moves[0]
            moves[0] = moves[i]
            moves[i] = tmp
            return


# @nb.njit
def pvs(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags,
        bb_current, bb_opponent, depth, father, alpha, beta):
    # TODO: Put back the TT probe at the beginning, and add the mv_nb info in the TT and pass the father arg to probe

    # if is_winning(bb_opponent):  # Opponent cannot be winning with this search  # TODO assert False inside that to check
    #     return -INF + depth

    if is_winning(bb_current):
        return INF - depth

    if is_dead_draw(bb_current, bb_opponent):
        return 0

    move_scores = get_scores(bb_current, bb_opponent)
    ordered_moves, mv_nb = sort_moves(move_scores)

    # --- FRACTIONNAL PLY: search deeper for threats ---
    # TODO: Already got a st_bb function, use it somewhere wisely
    if mv_nb < 5:  # Threats yield usually 2 or 3 moves, and sometime there is one or two counter-attacks
        depth += father - 2

    if depth <= 0:
            return fast_eval(bb_current, bb_opponent)

    key = compute_hash(bb_current, bb_opponent)

    # --- TT PROBE ---
    hit, tt_score, tt_move, alpha, beta = tt_probe(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags,
                                                   key, depth, alpha, beta)
    if hit:
        return tt_score

    # --- HASH MOVE FIRST ---
    move_to_front(ordered_moves, mv_nb, tt_move)

    best_score = -INF
    best_move = U64(0)

    alpha_orig = alpha
    first = True

    for i in range(min(K, mv_nb)):
        move = ordered_moves[i]

        bb_current ^= move

        if first:
            score = -pvs(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags,
                         bb_opponent, bb_current, depth - LOG2[mv_nb], LOG2[mv_nb], -beta, -alpha)
            first = False
        else:
            score = -pvs(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags,
                         bb_opponent, bb_current, depth - LOG2[mv_nb], LOG2[mv_nb], -alpha - 1, -alpha)

            if alpha < score and score < beta:
                score = -pvs(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags,
                             bb_opponent, bb_current, depth - LOG2[mv_nb], LOG2[mv_nb], -beta, -score)

        bb_current ^= move

        if score > best_score:
            best_score = score
            best_move = move

        if score > alpha:
            alpha = score

        if alpha >= beta:
            break

    # --- STORE IN TT ---
    if best_score <= alpha_orig:
        flag = UPPER
    elif best_score >= beta:
        flag = LOWER
    else:
        flag = EXACT

    tt_store(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags,
             key, depth, best_score, flag, best_move)

    return best_score


# @nb.njit
def find_best_move(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags,
                   bb_current, bb_opponent, max_depth, time_limit):
    start_time = ctime()

    best_move = U64(0)  # TODO: if no loop is run (time_limit), best_move is not valid by default
    pv_move = U64(0)

    for depth in range(1, max_depth + 1):

        if ctime() - start_time >= time_limit:
            break

        move_scores = get_scores(bb_current, bb_opponent)
        ordered_moves, mv_nb = sort_moves(move_scores)

        # --- PV move first ---
        move_to_front(ordered_moves, mv_nb, pv_move)

        if mv_nb == 1:
            return ordered_moves[0]

        alpha = -INF
        beta = INF

        best_score = -INF
        best_move_depth = U64(0)  # TODO: same than outer ?

        for i in range(min(K, mv_nb)):

            if ctime() - start_time >= time_limit:
                break

            move = ordered_moves[i]

            bb_current ^= move

            # --- PVS root ---
            if i == 0:
                score = -pvs(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags,
                             bb_opponent, bb_current, depth - LOG2[mv_nb], LOG2[mv_nb], -beta, -alpha)
            else:
                score = -pvs(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags,
                             bb_opponent, bb_current, depth - LOG2[mv_nb], LOG2[mv_nb], -alpha - 1, -alpha)

                if alpha < score and score < beta:
                    score = -pvs(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags,
                                 bb_opponent, bb_current, depth - LOG2[mv_nb], LOG2[mv_nb], -beta, -score)

            bb_current ^= move

            if score > best_score:
                best_score = score
                best_move_depth = move

            if score > alpha:
                alpha = score

        # --- update PV ---
        if best_move_depth != U64(0):
            best_move = best_move_depth
            pv_move = best_move_depth

        # Optional debug
        print(f"Depth {depth} ({depth // 12}), score {best_score}, move {best_move}")

    return best_move


# @nb.njit
def tss_bot(position, current_player, timer, memory):
    if memory is None:
        TT_keys = np.zeros(TT_SIZE, dtype=U64)  # TODO: implement a 2-bucket TT
        TT_moves = np.zeros(TT_SIZE, dtype=U64)
        TT_depths = np.zeros(TT_SIZE, dtype=U8)
        TT_scores = np.zeros(TT_SIZE, dtype=np.int64)  # TODO: reduce space taken by scores !
        TT_flags = np.zeros(TT_SIZE, dtype=U8)
        memory = TT_keys, TT_moves, TT_depths, TT_scores, TT_flags
    else:
        TT_keys, TT_moves, TT_depths, TT_scores, TT_flags = memory

    move_time = timer["times"][current_player] / 20 + timer["increments"][current_player] / 2
    # move_time = 0.5 * timer["times"][current_player]

    bitboards = board_to_bitboards(position)
    bb_current = U64(bitboards[current_player])
    bb_opponent = U64(bitboards[1 - current_player])

    bb_current_cr, bb_opponent_cr, s_idx = canonicalize(bb_current, bb_opponent)
    bb_current_cr = U64(bb_current_cr)
    bb_opponent_cr = U64(bb_opponent_cr)
    print(bb_current_cr, bb_opponent_cr)

    move_cr = lookup_opening_moves(bb_current_cr, bb_opponent_cr)
    if move_cr is None:
        move_cr = find_best_move(TT_keys, TT_moves, TT_depths, TT_scores, TT_flags,
                                bb_current_cr, bb_opponent_cr, max_depth=64, time_limit=move_time)

    move = apply_inverse_symmetry(move_cr, s_idx)
    move_ij = bb2m(move)

    print(f"Move: {move_ij}")

    return move_ij, memory
