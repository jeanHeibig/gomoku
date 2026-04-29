from numpy import array, arange, uint64

from .board import Board
from .masks.board_tiles import BOARD_TILES
from .masks.precomputed_masks_all_board import WIN_MASKS_ALL_BOARD
from .masks.precomputed_masks_indexes import WIN_MASKS_INDEXES
from .masks.precomputed_masks_random_games import RANDOM_GAMES

b2b = Board.board_to_bitboards
bb2m = Board.bb_to_moves
prettyprint = Board.prettyprint

BT = array(BOARD_TILES, dtype=uint64)
WMA = array(WIN_MASKS_ALL_BOARD, dtype=uint64)
WMI = array(WIN_MASKS_INDEXES, dtype=uint64)
RG = array(RANDOM_GAMES, dtype=uint64)
MOVES = uint64(1) << arange(64, dtype=uint64)


__all__ = ["Board", "b2b", "bb2m", "prettyprint", "BT", "WMA", "WMI", "RG", "MOVES"]
