import numpy as np

from .opening import OPENING_BOOK


def lookup_opening_moves(bb_current, bb_opponent):  # TODO: be precise with typing
    """Return opening move if position is in book, else None."""
    entry = OPENING_BOOK.get((bb_current, bb_opponent))

    if entry is None:
        return None

    move_cr = np.uint64(1 << entry[0])
    return move_cr
