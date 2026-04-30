from .basic_bots import random_bot
from .basic_bots import take_win_in_one_bot
from .basic_bots import block_opponent_bot
from .basic_bots import double_threats_bot
from .basic_bots import prevent_double_threats_bot
from .alpha_beta import ab_bot

basic_bots = [
    random_bot,
    take_win_in_one_bot,
    block_opponent_bot,
    double_threats_bot,
    prevent_double_threats_bot,
    ab_bot
]

__all__ = [
    "random_bot",
    "take_win_in_one_bot",
    "block_opponent_bot",
    "double_threats_bot",
    "prevent_double_threats_bot",
    "basic_bots",
    "ab_bot"
]
