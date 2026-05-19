import numpy as np

from .hyperparameters import TT_SIZE, K
from .data import ZOBRIST, LOG2

from .board import board_to_bitboards, bitboard_to_ij, compute_hash, idx_to_ij, move_to_square, prettyprint
from .clock import ctime
from .canonicalization import canonicalize, get_symmetry_mask, apply_inverse_symmetry
from .tactics import get_forced_moves
from .heuristics import monte_carlo_heuristic, tactical_heuristic
from .search import extract_pv, pvs
from .ordering import sort_moves, move_to_front
from .openings import lookup_opening_move


I8 = np.int8
U8 = np.uint8
U64 = np.uint64


ZB = np.array(ZOBRIST, dtype=U64)
ZOBRIST_SIDE = U64(0x9E3779B97F4A7C15)
INF = I8(0x7f)
FATHER = np.array(LOG2, dtype=I8)
MOVES = U64(1) << np.arange(64, dtype=U64)

VERBOSE = False


# @nb.njit
def find_best_move(
    TT,
    bb_current,
    bb_opponent,
    side_to_move,
    hash_,
    max_depth,
    time_limit
) -> U8:
    start_time = ctime()

    bb_open = ~(bb_current | bb_opponent)
    if VERBOSE:
        print("Looking for tactics...", end='')
    tactics = get_forced_moves(bb_current, bb_opponent, bb_open)
    if VERBOSE:
        if tactics != U64(0xffffffffffffffff):
            print(" tactics found! Filtering with this mask:")
            prettyprint(tactics)
        else:
            print(" no tactics found.")

    if VERBOSE:
        print("Figuring out symmetries...", end='')
    symmetries = get_symmetry_mask(bb_current, bb_opponent)
    if VERBOSE:
        if symmetries != U64(0xffffffffffffffff):
            print(" symmetry found! Filtering with this mask:")
            prettyprint(symmetries)
        else:
            print(" no symmetry found.")

    if VERBOSE:
        print("Heuristic evaluation...", end='')
    # if tactics == U64(0xffffffffffffffff):  # No tactics found
    #     move_scores = tactical_heuristic(bb_current, bb_opponent, bb_open & symmetries)
    # else:
    move_scores = monte_carlo_heuristic(bb_current, bb_opponent, tactics & bb_open & symmetries)

    if VERBOSE:
        print(" scores:")
        print(move_scores.reshape((8, 8)))

    move_indices, mv_nb = sort_moves(move_scores, tactics & bb_open & symmetries)

    pv_move = move_indices[0]

    if mv_nb == 1:
        if VERBOSE:
            print(f"Only move found: {move_to_square(pv_move)}! Playing it immediately.")
        return move_indices[0]
    else:
        if VERBOSE:
            print(f"Found {mv_nb} moves: {' '.join(move_to_square(idx) for idx in move_indices[:mv_nb])}.")

    for depth in range(1, max_depth + 1):

        if ctime() - start_time >= time_limit:
            break

        alpha = -INF
        beta = INF

        best_score = -INF
        best_move_depth = pv_move

        move_to_front(move_indices, mv_nb, pv_move)

        limit = min(K, mv_nb)
        for i in range(limit):

            if ctime() - start_time >= time_limit:
                break

            cell = move_indices[i]
            move = MOVES[cell]

            bb_current ^= move
            hash_ ^= ZB[side_to_move, cell]
            hash_ ^= ZOBRIST_SIDE
            side_to_move = U8(1) - side_to_move
            child_depth = depth - FATHER[mv_nb]

            # --- PVS root ---
            if i == 0:
                score = -pvs(
                    TT,
                    bb_opponent,
                    bb_current,
                    side_to_move,
                    hash_,
                    child_depth,
                    FATHER[mv_nb],
                    -beta,
                    -alpha
                )
            else:
                score = -pvs(
                    TT,
                    bb_opponent,
                    bb_current,
                    side_to_move,
                    hash_,
                    child_depth,
                    FATHER[mv_nb],
                    -alpha - 1,
                    -alpha
                )

                if alpha < score and score < beta:
                    score = -pvs(
                        TT,
                        bb_opponent,
                        bb_current,
                        side_to_move,
                        hash_,
                        child_depth,
                        FATHER[mv_nb],
                        -beta,
                        -alpha
                    )

            side_to_move = U8(1) - side_to_move
            hash_ ^= ZB[side_to_move, cell]
            hash_ ^= ZOBRIST_SIDE
            bb_current ^= move

            if score > best_score:
                best_score = score
                best_move_depth = cell

            if score > alpha:
                alpha = score

        # --- update PV ---
        pv_move = best_move_depth

        pv = extract_pv(TT, U8(1) - side_to_move, hash_ ^ ZB[side_to_move, pv_move] ^ ZOBRIST_SIDE)

        move_names = [move_to_square(pv_move)]
        for move_idx in pv:
            mv_name = move_to_square(move_idx)
            move_names.append(mv_name)
        mv_side = side_to_move
        for i in range(len(move_names)):
            if mv_side:
                move_names[i] = move_names[i].lower()
            mv_side = 1 - mv_side
        pv_str = " ".join(move_names)


        if VERBOSE:
            print(
                f"Depth {depth} ({(depth - 1) // 12}), "
                f"score {-best_score if side_to_move else best_score}, "
                f"pv {pv_str}"
            )

        if (best_score >= I8(100)) or (best_score <= I8(-100)):
            return pv_move

    return pv_move


# @nb.njit
def ab_bot(position, current_player, timer, TT):
    bitboards = board_to_bitboards(np.array(position, dtype=U8))
    current_player = U8(current_player)
    if TT is None:
        TT = np.zeros(TT_SIZE, dtype=U64)  # TODO: implement a 2-bucket TT
        if VERBOSE:
            print("No memory found: TT created.")
    else:
        if VERBOSE:
            print("TT Loaded from memory.")

    move_time = timer["times"][current_player] / 10 + timer["increments"][current_player] / 2
    if VERBOSE:
        print(f"Move time: {move_time:.2f}s.")
        print(f"Playing {'white' if current_player else 'black'}.")

    bb_current = U64(bitboards[current_player])
    bb_opponent = U64(bitboards[1 - current_player])

    if VERBOSE:
        print("Canonicalisation...", end='')
    bb_current_cr, bb_opponent_cr, symmetry = canonicalize(bb_current, bb_opponent)
    bb_current_cr = U64(bb_current_cr)
    bb_opponent_cr = U64(bb_opponent_cr)
    if VERBOSE:
        sym_names = [
            'identity',
            'vertical flip',
            '180° rotation',
            'horizontal flip',
            'counter-clockwise rotation',
            'diagonal flip',
            'clockwise rotation',
            'antidiagonal flip'
        ]
        print(f" with {sym_names[int(np.log2(symmetry))]}.")
        print(f"Current bb ({bb_current_cr}):")
        prettyprint(bb_current_cr)
        print(f"Opponent bb ({bb_opponent_cr}):")
        prettyprint(bb_opponent_cr)

    move_cr = lookup_opening_move(bb_current_cr, bb_opponent_cr)
    if move_cr:
        move = apply_inverse_symmetry(move_cr, symmetry)  # TODO: opening book should contain indexes too
        move_ij = bitboard_to_ij(move)
        i, j = move_ij
        if VERBOSE:
            print(f"Opening move found: {move_to_square(8 * i + j)}.")
    else:
        if VERBOSE:
            print("No opening move found. Looking for best_move...")
        hash_ = compute_hash(bb_current, bb_opponent, current_player)
        if VERBOSE:
            print(f"Zobrist: {hash_}.")
            print("Starting `find_best_move` routine...")
        move_idx = find_best_move(
            TT,
            bb_current,
            bb_opponent,
            current_player,
            hash_,
            max_depth=INF - I8(1),
            time_limit=move_time
        )
        if VERBOSE:
            print(f"Ending `find_best_move` routine. Move found: {move_to_square(move_idx)}.")
        move_ij = idx_to_ij(move_idx)  # TODO: find_best_move should return ij directly

    return move_ij, TT
