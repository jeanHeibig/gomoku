import numpy as np
from numpy.typing import NDArray

from self_play.canonicalization import U8, U64, BB, RawMove
from backend.players.bots.basic_bots import basic_bot_self_play
from backend.players.bots.ab_bot.self_play import alpha_beta_bot_self_play

TTPackedEntry = U64
TT = NDArray[TTPackedEntry]


MC_NB_SIMULATIONS = 10000
MAX_DEPTH = 25


def basic_bot(bb_current: BB, bb_opponent: BB) -> RawMove:
    """Return the move given by the basic bot with limited tactics and heuristics."""
    i, j = basic_bot_self_play(bb_current, bb_opponent)
    index = RawMove(8 * i + j)
    return index


def create_empty_tt(tt_bits: int) -> TT:
    """Return an empty transposition table."""
    tt: TT = np.zeros(1 << tt_bits, dtype=TTPackedEntry)
    return tt


def alpha_beta_bot(
    bb_current: BB,
    bb_opponent: BB,
    current_player: U8,
    max_depth: U8,
    tt: TT
) -> tuple[RawMove, TT]:
    """Return the move given by alpha-beta explorer with transposition table."""

    (i, j), tt = alpha_beta_bot_self_play(
        bb_current,
        bb_opponent,
        current_player,
        max_depth,
        tt,
    )

    index = RawMove(8 * i + j)
    return index, tt
