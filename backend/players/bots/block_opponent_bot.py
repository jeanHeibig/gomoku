import time
import random

from ...masks.board_tiles import BOARD_TILES
from ...bitboard import board_to_bitboards, open_spots, winning_tiles, bb_to_moves

_MIN_TIME = 2  # Seconds allowed to do the search. Otherwise, play random.


def _get_winning_moves(bb_player, bb_open):
    """Get moves that would complete a five-in-a-row for the player.

    Args:
        bb_player: Bitboard of the current player's stones.
        bb_open: Bitboard of open spots on the board.

    Returns:
        List of (i, j) tuples representing winning moves.
    """
    wm = 0
    for bb_check in BOARD_TILES:
        wm |= bb_open & winning_tiles(bb_player | (bb_check & bb_open))
    return bb_to_moves(wm)


def block_opponent_bot(position, timer):
    # Get all possible moves (empty spots)
    moves = [(i, j) for i in range(8) for j in range(8) if position[i][j]==0]
    current_player = len(moves) % 2  # Determine current player (0 or 1)
    times = timer.get_times()["times"]
    remaining_time = times[current_player]

    start_time = time.time()
    if remaining_time > _MIN_TIME:
        # Convert board to bitboards and find winning moves
        bb = board_to_bitboards(position)
        winning_moves = _get_winning_moves(bb[current_player], open_spots(bb))
        if winning_moves:
            return random.choice(winning_moves)

        elapsed = time.time() - start_time
        if remaining_time - elapsed > _MIN_TIME:
            opponent_winning_moves = _get_winning_moves(bb[1 - current_player], open_spots(bb))
            if opponent_winning_moves:
                return random.choice(opponent_winning_moves)

    # Fallback to random move if no winning move or low time
    return random.choice(moves)
