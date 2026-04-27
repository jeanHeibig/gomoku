# from .bitboard import is_last_move_winning, set_bit, board_to_bitboards, winning_tiles_from_last_move, bb_to_moves
from .bitboard import board_to_bitboards, ij_to_bit, is_last_move_winning, bb_to_moves, winning_tiles_from_last_move

BOARD_SIZE = 8


class Board:
    def __init__(self, starting_position=None, current_player=None):
        if starting_position is None:
            starting_position = [[0]*BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.position = starting_position

        self.ply = len(self.get_taken_spots())

        if current_player is None:
            current_player = self.ply % 2
        self.current_player = current_player

        self.bitboards = board_to_bitboards(self.position)

    def __repr__(self):
        lines = []
        for i in range(8):
            l = ""
            for j in range(8):
                if self.position[i][j] == 1:
                    l += 'x'
                elif self.position[i][j] == 2:
                    l += 'o'
                else:
                    l += '.'
            lines.append(l)
        return '\n'.join(lines)

    def __getitem__(self, key):
        return self.position[key]

    def get_taken_spots(self):
        return [
            (i, j)
            for i in range(BOARD_SIZE)
            for j in range(BOARD_SIZE)
            if self.position[i][j]
        ]

    def add_move(self, i, j):
        self.position[i][j] = self.current_player + 1
        self.ply += 1
        self.bitboards[self.current_player] |= ij_to_bit(i, j)
        return is_last_move_winning(self.bitboards[self.current_player], i, j)

    def get_winning_tiles(self, i, j):
        bb_tiles = winning_tiles_from_last_move(self.bitboards[self.current_player], i, j)
        return bb_to_moves(bb_tiles)

    def is_full(self):
        return self.ply == BOARD_SIZE * BOARD_SIZE

    def switch_player(self):
        self.current_player = self.opponent()

    def opponent(self):
        return 1 - self.current_player
