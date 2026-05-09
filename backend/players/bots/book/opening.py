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
    # # Start
    (0x0000000000000000, 0x0000000000000000): (Square.D5, 64, Outcome.DRAW),

    # # D5
    # (0x0000000000000000, 0x0000000008000000): (Square.E5, 15, Outcome.UNKNOWN),
    # # # (0x0000000000000000, 0x0000000008000000): (Square.E4, 12, Outcome.UNKNOWN),

    # # D5-D6
    # (0x0000000008000000, 0x0000000000080000): (Square.E4, 18, Outcome.UNKNOWN),

    # # D5-E5-D4-C5
    # (0x0000000810000000, 0x0000000028000000): (Square.C3, 18, Outcome.UNKNOWN),

    # # D5-E5-D4-C5-F3-G2
    # (0x0000000810200000, 0x0000001400004000): (Square.D5, 19, Outcome.UNKNOWN),

    # # D5-E5
    # (0x0000000008000000, 0x0000000010000000): (Square.D3, 12, Outcome.UNKNOWN),

    # # D5-E5-D3
    # (0x0000000008000000, 0x0000002800000000): (Square.E4, 13, Outcome.UNKNOWN),

    # # D5-E5-D3-D4
    # (0x0000000014000000, 0x0000001008000000): (Square.F4, 12, Outcome.UNKNOWN),

    # # D5-E5-D3-D4-E6
    # (0x0000000810000000, 0x0000000428000000): (Square.C3, 13, Outcome.UNKNOWN),

    # # D5-E5-D3-D4-E6-F6
    # (0x0000000428000000, 0x0000040810000000): (Square.F6, 14, Outcome.UNKNOWN),

    # # D5-E5-D3-D4-E6-F6-C3
    # (0x0000000810200000, 0x0000041420000000): (Square.D3, 14, Outcome.UNKNOWN),

    # # D5-E5-D3-D4-E6-F6-C3-C4
    # (0x0000000428200000, 0x0000040810100000): (Square.F4, 12, Outcome.UNKNOWN),

    # # D5-E5-D3-D4-E6-F6-C3-C4-E3
    # (0x0000000c10200000, 0x00001c0008100000): (Square.F3, 14, Outcome.UNKNOWN),

    # # D5-E5-D3-D4-E6-F6-C3-C4-E3-F3
    # (0x0000002414040000, 0x0000241008080000): (Square.D3, 8, Outcome.UNKNOWN),  # K = 64 unrestricted

    # # D5-E4
    # (0x0000000008000000, 0x0000001000000000): (Square.E5, 12, Outcome.UNKNOWN),

    # # D5-E4-E5
    # (0x0000000008000000, 0x0000001010000000): (Square.D4, 12, Outcome.UNKNOWN),

    # # D5-E4-E5-D4
    # (0x0000000018000000, 0x0000001800000000): (Square.B4, 4, Outcome.UNKNOWN),  # Might have bugged

    # # D5-E4-E5-D4-B4
    # (0x0000000018000000, 0x0000001802000000): (Square.C5, 9, Outcome.UNKNOWN),

    # # D5-E4-E5-D4-B4-C4
    # (0x0000000218000000, 0x0000001c00000000): (Square.C5, 12, Outcome.UNKNOWN),

    # # D5-E4-E5-D4-B4-C4-C5
    # (0x000000001c000000, 0x0000001c02000000): (Square.B4, 12, Outcome.UNKNOWN),

    # # D5-E4-F5
    # (0x0000000008000000, 0x0000001000100000): (Square.D4, 13, Outcome.UNKNOWN),

    # # --- RANDOM GAMES ---

    # # XC6D6C5D5E5C4-OE6B5D4E4F4C3
    # (0x000000041c0c0000, 0x0000043802100000): (Square.E7, 16, Outcome.UNKNOWN),

    # --- HANDICAP ---
    (134217728, 0): (Square.E4, 0, Outcome.UNKNOWN),
    (34628173824, 134217728): (Square.E4, 64, Outcome.WIN),
    (34762391552, 69256347648): (Square.D3, 64, Outcome.WIN),
    (35299262464, 8865886240768): (Square.F6, 64, Outcome.WIN),
}
