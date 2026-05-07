from enum import IntEnum


from .squares import Square


class Outcome(IntEnum):
    UNKNOWN = 0
    WIN = 1
    DRAW = 2
    LOSS = 3


# key: (bb_current, bb_opponent)  # (canonical representation)
# value: (move, depth, outcome)
OPENING_BOOK = {
    # Start
    (0x0000000000000000, 0x0000000000000000): (Square.D5, 64, Outcome.DRAW),

    # D5
    (0x0000000000000000, 0x0000000008000000): (Square.E4, 12, Outcome.UNKNOWN),

    # D5-E4
    (0x0000000008000000, 0x0000001000000000): (Square.E5, 12, Outcome.UNKNOWN),

    # D5-E4-E5
    (0x0000000008000000, 0x0000001010000000): (Square.D4, 12, Outcome.UNKNOWN),

    # D5-E4-E5-D4
    (0x0000000018000000, 0x0000001800000000): (Square.B4, 4, Outcome.UNKNOWN),  # Might have bugged

    # D5-E4-E5-D4-B4
    (0x0000000018000000, 0x0000001802000000): (Square.C5, 9, Outcome.UNKNOWN),

    # D5-E4-E5-D4-B4-C4
    (0x0000000218000000, 0x0000001c00000000): (Square.C5, 12, Outcome.UNKNOWN),

    # D5-E4-E5-D4-B4-C4-C5
    (0x000000001c000000, 0x0000001c02000000): (Square.B4, 12, Outcome.UNKNOWN),

    # --- RANDOM GAMES ---

    # XC6D6C5D5E5C4-OE6B5D4E4F4C3
    (0x000000041c0c0000, 0x0000043802100000): (Square.E7, 16, Outcome.UNKNOWN),
}
