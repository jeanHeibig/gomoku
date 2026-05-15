import numba as nb
import numpy as np


U8 = np.uint8
U64 = np.uint64


MOVES = U64(1) << np.arange(64, dtype=U64)


A8 = U8(0)
B8 = U8(1)
C8 = U8(2)
D8 = U8(3)
E8 = U8(4)
F8 = U8(5)
G8 = U8(6)
H8 = U8(7)
A7 = U8(8)
B7 = U8(9)
C7 = U8(10)
D7 = U8(11)
E7 = U8(12)
F7 = U8(13)
G7 = U8(14)
H7 = U8(15)
A6 = U8(16)
B6 = U8(17)
C6 = U8(18)
D6 = U8(19)
E6 = U8(20)
F6 = U8(21)
G6 = U8(22)
H6 = U8(23)
A5 = U8(24)
B5 = U8(25)
C5 = U8(26)
D5 = U8(27)
E5 = U8(28)
F5 = U8(29)
G5 = U8(30)
H5 = U8(31)
A4 = U8(32)
B4 = U8(33)
C4 = U8(34)
D4 = U8(35)
E4 = U8(36)
F4 = U8(37)
G4 = U8(38)
H4 = U8(39)
A3 = U8(40)
B3 = U8(41)
C3 = U8(42)
D3 = U8(43)
E3 = U8(44)
F3 = U8(45)
G3 = U8(46)
H3 = U8(47)
A2 = U8(48)
B2 = U8(49)
C2 = U8(50)
D2 = U8(51)
E2 = U8(52)
F2 = U8(53)
G2 = U8(54)
H2 = U8(55)
A1 = U8(56)
B1 = U8(57)
C1 = U8(58)
D1 = U8(59)
E1 = U8(60)
F1 = U8(61)
G1 = U8(62)
H1 = U8(63)


UNKNOWN = U8(0)
WIN = U8(1)
DRAW = U8(2)
LOSS = U8(3)


BOOK_BB_CURRENT = np.array([
    U64(0),
    U64(17582522368),
    # U64(34628173824),
    # U64(34762391552),
    # U64(35299262464),
], dtype=U64)

BOOK_BB_OPPONENT = np.array([
    U64(0),
    U64(103080263680),
    # U64(134217728),
    # U64(69256347648),
    # U64(8865886240768),
], dtype=U64)

BOOK_MOVES = np.array([
    D5,
    F5,
    # E4,
    # D3,
    # F6,
], dtype=U8)

BOOK_RESULTS = np.array([
    DRAW,
    UNKNOWN,
    # WIN,
    # WIN,
    # WIN,
], dtype=U8)


@nb.njit("u8(u8, u8)")
def lookup_opening_move(bb_current: U64, bb_opponent: U64) -> U64:

    for i in range(len(BOOK_MOVES)):

        if (BOOK_BB_CURRENT[i] == bb_current and
            BOOK_BB_OPPONENT[i] == bb_opponent):

            return MOVES[BOOK_MOVES[i]]

    return U64(0)
