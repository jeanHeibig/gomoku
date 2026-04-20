import time

from bitboard import has_five, set_bit

class Game:
    def __init__(self):
        self.board = [[0]*8 for _ in range(8)]
        self.bb = [0, 0]  # joueur 1, joueur 2
        self.player = 0

        self.time = [60.0, 60.0]
        self.last_move_time = None

        self.started = False
        self.finished = False
        self.winner = None

    def play(self, i, j):
        if self.finished:
            return False

        now = time.time()

        if self.last_move_time is None:
            # first move
            self.last_move_time = now
            self.started = True
        else:
            elapsed = now - self.last_move_time
            self.time[self.player] -= elapsed
            self.last_move_time = now

            if self.time[self.player] < 0:
                self.finished = True
                self.winner = 1 - self.player
                return True

        if self.board[i][j] != 0:
            return False

        self.board[i][j] = self.player + 1
        self.bb[self.player] = set_bit(self.bb[self.player], i, j)

        if has_five(self.bb[self.player], i, j):
            self.finished = True
            self.winner = self.player
            return True

        # Test match nul
        if all(self.board[i][j] != 0 for i in range(8) for j in range(8)):
            self.finished = True
            self.winner = None
            return True

        self.player = 1 - self.player
        return True
