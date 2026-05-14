# import numba as nb
import numpy as np

from .hyperparameters import K, TT_SIZE
from .data import ZOBRIST, LOG2

from .board import board_to_bitboards, bitboard_to_ij, compute_hash, prettyprint, move_to_square
from .clock import ctime
from .canonicalization import canonicalize, apply_inverse_symmetry
from .tactics import get_forced_moves
from .heuristics import mixed_heuristic
from .search import pvs
from .ordering import sort_moves, move_to_front
from .openings import lookup_opening_move


I8 = np.int8
U8 = np.uint8
U64 = np.uint64


ZB = np.array(ZOBRIST, dtype=U64)
ZOBRIST_SIDE = U64(0x9E3779B97F4A7C15)
INF = I8(0x7f)
LOG2 = np.array(LOG2, dtype=I8)


# @nb.njit
def find_best_move(
    TT_keys,
    TT_moves,
    TT_depths,
    TT_scores,
    TT_flags,
    bb_current,
    bb_opponent,
    side_to_move,
    hash_,
    max_depth,
    time_limit
):
    start_time = ctime()

    bb_open = ~(bb_current | bb_opponent)
    # print("Looking for tactics...")
    tactics = get_forced_moves(bb_current, bb_opponent, bb_open)
    # if tactics != U64(0xffffffffffffffff):
        # print("Tactics found:")
        # prettyprint(tactics)
    # else:
        # print("No tactics found")

    # print("Heuristic evaluation...")


    # move_scores = monte_carlo_heuristic(bb_current, bb_opponent, bb_open)
    move_scores = mixed_heuristic(bb_current, bb_opponent, bb_open)


    # print(move_scores.reshape((8, 8)))
    # print("Sorting moves...")
    ordered_moves, move_indices, mv_nb = sort_moves(move_scores, tactics)
    # print(f"Found {mv_nb} moves: {move_indices}")

    best_move = ordered_moves[0]
    pv_move = ordered_moves[0]

    for depth in range(1, max_depth + 1):

        # print(f"--- Depth {depth} ---")

        if ctime() - start_time >= time_limit:
            break

        # print("Moving PV move first")
        move_to_front(ordered_moves, move_indices, mv_nb, pv_move)

        if mv_nb == 1:
            # print("Only move found! Playing it immediately.")
            return ordered_moves[0]

        alpha = -INF
        beta = INF
        # print(f"Setting alpha={alpha} and beta={beta}")

        best_score = -INF
        best_move_depth = pv_move
        # print(f"Setting best_score={best_score} and best_move_{depth}:")
        # prettyprint(best_move_depth)

        limit = min(K, mv_nb)
        # print(f"Looping through {limit} moves")
        for i in range(limit):
            # print(f"--- MOVE {i}: cell {move_indices[i]} ---")

            if ctime() - start_time >= time_limit:
                break

            move = ordered_moves[i]
            cell = move_indices[i]

            # print("Making move...")
            bb_current ^= move
            hash_ ^= ZB[side_to_move, cell]
            hash_ ^= ZOBRIST_SIDE
            side_to_move = U8(1) - side_to_move
            child_depth = depth - LOG2[mv_nb]

            # print(f"Child depth: {child_depth}")
            # --- PVS root ---
            if i == 0:
                # print("Starting first PVS")
                score = -pvs(
                    TT_keys,
                    TT_moves,
                    TT_depths,
                    TT_scores,
                    TT_flags,
                    bb_opponent,
                    bb_current,
                    side_to_move,
                    hash_,
                    child_depth,
                    LOG2[mv_nb],
                    -beta,
                    -alpha
                )
                # print(f"Found score={score} with alpha={alpha} and beta={beta}")
            else:
                # print("Starting PVS with null window")
                score = -pvs(
                    TT_keys,
                    TT_moves,
                    TT_depths,
                    TT_scores,
                    TT_flags,
                    bb_opponent,
                    bb_current,
                    side_to_move,
                    hash_,
                    child_depth,
                    LOG2[mv_nb],
                    -alpha - 1,
                    -alpha
                )
                # print(f"Found score={score} with alpha={alpha} and beta={beta}")

                if alpha < score and score < beta:
                    # print("Restarting PVS with full window")
                    score = -pvs(
                        TT_keys,
                        TT_moves,
                        TT_depths,
                        TT_scores,
                        TT_flags,
                        bb_opponent,
                        bb_current,
                        side_to_move,
                        hash_,
                        child_depth,
                        LOG2[mv_nb],
                        -beta,
                        -alpha
                    )
                    # print(f"Found score={score} with alpha={alpha} and beta={beta}")

            # print("Unmaking move...")
            side_to_move = U8(1) - side_to_move
            hash_ ^= ZB[side_to_move, cell]
            hash_ ^= ZOBRIST_SIDE
            bb_current ^= move

            if score > best_score:
                # print(f"Found new best score={score} (old score={best_score}) with move:")
                # prettyprint(move)
                best_score = score
                best_move_depth = move

            if score > alpha:
                # print(f"Found new best alpha={score} (old alpha={alpha})")
                alpha = score

        # --- update PV ---
        # print("Updating PV...")
        # print("Old best move:")
        # prettyprint(best_move)
        # print("New best_move:")
        # prettyprint(best_move_depth)
        best_move = best_move_depth
        pv_move = best_move_depth

        # Optional debug
        print(f"Depth {depth} ({depth // 12}), score {-best_score if side_to_move else best_score}, move {move_to_square(best_move)}")

        # printer_answer = input("Waiting for enter: [y]/n")
        # if printer_answer == 'n':
        #     raise KeyboardInterrupt
        if best_score >= I8(100):
            return best_move

    return best_move


# @nb.njit
def tss_bot(board, current_player, timer, memory):
    position = np.array(board.position, dtype=U8)  # TODO: Ask for position argument to be an array
    current_player = U8(current_player)
    if memory is None:
        TT_keys   = np.zeros(TT_SIZE, dtype=U64)  # TODO: implement a 2-bucket TT
        TT_moves  = np.zeros(TT_SIZE, dtype=U64)
        TT_depths = np.zeros(TT_SIZE, dtype=U8)
        TT_scores = np.zeros(TT_SIZE, dtype=I8)  # TODO: reduce space taken by scores !
        TT_flags  = np.zeros(TT_SIZE, dtype=U8)
        memory = TT_keys, TT_moves, TT_depths, TT_scores, TT_flags
        # print("TT created")
    else:
        TT_keys, TT_moves, TT_depths, TT_scores, TT_flags = memory
        # print("TT loaded")

    move_time = timer["times"][current_player] / 20 + timer["increments"][current_player] / 2
    move_time = 5 * timer["times"][current_player]
    # print(f"Move time: {move_time:.2f}s")

    bitboards = board_to_bitboards(position)
    # print("--- BITBOARDS ---")
    # print("Black:")
    # prettyprint(bitboards[0])
    # print("White:")
    # prettyprint(bitboards[1])
    # print(f"Playing {'white' if current_player else 'black'}")
    bb_current = U64(bitboards[current_player])
    bb_opponent = U64(bitboards[1 - current_player])

    # print("--- OPPENING ---")
    # print("Canonicalisation...")
    bb_current_cr, bb_opponent_cr, symmetry = canonicalize(bb_current, bb_opponent)
    bb_current_cr = U64(bb_current_cr)
    bb_opponent_cr = U64(bb_opponent_cr)
    # print("Current:")
    # prettyprint(bb_current_cr)
    # print("Opponent:")
    # prettyprint(bb_opponent_cr)
    # print(f"Symmetry: {symmetry}")

    move_cr = lookup_opening_move(bb_current_cr, bb_opponent_cr)
    if move_cr:
        # print("Opening move found!")
        move = apply_inverse_symmetry(move_cr, symmetry)
        # prettyprint(move)
    else:
        # print("No opening move found. Looking for best_move...")
        hash_ = compute_hash(bb_current, bb_opponent, current_player)
        # print(f"Hash key: {hash_}")
        # print("Starting `find_best_move` routine...")
        move = find_best_move(
            TT_keys,
            TT_moves,
            TT_depths,
            TT_scores,
            TT_flags,
            bb_current,
            bb_opponent,
            current_player,
            hash_,
            max_depth=INF - I8(1),
            time_limit=move_time
        )
        # print("Ending `find_best_move` routine. Move found:")
        # prettyprint(move)

    move_ij = bitboard_to_ij(move)
    # print(f"Move coordinates: {move_ij}")

    return move_ij, memory
