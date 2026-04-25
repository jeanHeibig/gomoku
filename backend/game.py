"""
Game module for managing Gomoku game state and logic.

This module provides the Game class which handles the core game mechanics
including move validation, win detection, and game state management for
an 8x8 Gomoku board.
"""

from .bitboard import is_last_move_winning, set_bit, board_to_bitboard
from .players.player import Player
from .clock.timer import Timer
from .clock.timeout import run_with_timeout


class Game:
    """A class representing a Gomoku game."""

    def __init__(self, gid: str, players: list[Player], timer: Timer, board=None):
        """Initialize the game with a list of players and a timer.

        Args:
            players (list[Player]): List of two players.
            timer (Timer): Timer for managing game time.
        """
        self.gid = gid
        self.players = players
        self.timer = timer

        if board is None:
            board = [[0]*8 for _ in range(8)]
        self.board = board
        self.bitboards = board_to_bitboard(self.board)
        self.ply = len([(i, j) for i in range(8) for j in range(8) if self.board[i][j]])
        self.current_player = self.ply % 2

        self.finished = False
        self.draw = False
        self.winner = None  # 0: P1, 1: P2

    def __repr__(self):
        s = str(self.timer)
        s += '\n-----------------------\n'
        lines = []
        for i in range(8):
            l = ""
            for j in range(8):
                if self.board[i][j] == 1:
                    l += 'x'
                elif self.board[i][j] == 2:
                    l += 'o'
                else:
                    l += '.'
            lines.append(l)
        s += '\n'.join(lines)
        s += '\n-----------------------'
        return s

    def _opponent(self):
        return 1 - self.current_player

    def _win_game(self, winner):
        self.finished = True
        self.winner = winner

    def _draw_game(self):
        self.finished = True
        self.draw = True

    def play_move(self, i: int, j: int) -> bool:
        """Make a move at position (i, j). Return True if the game continues, False if it ends.

        Args:
            i (int): Row index of the move.
            j (int): Column index of the move.

        Returns:
            bool: True if the game continues, False if the game ends.
        """
        flagged = self.timer.move_begin()

        if flagged or (self.board[i][j] != 0):  # game lost if illegal move
            self._win_game(self._opponent())
            return False

        # update board
        self.board[i][j] = self.current_player + 1
        self.ply += 1
        self.bitboards[self.current_player] = set_bit(self.bitboards[self.current_player], i, j)

        if is_last_move_winning(self.bitboards[self.current_player], i, j):
            self._win_game(self.current_player)
            return True

        # Test draws
        if self.ply == 64:
            self._draw_game()
            return True

        # game continues
        self.current_player = self._opponent()
        self.timer.move_end()

        return True

    # def get_move(self):
    #     """Wait for player to send their move."""
    #     try:
    #         move = run_with_timeout(
    #             func=self.players[self.current_player].move_fn,
    #             args=(self.board, self.timer),
    #             timeout=self.timer.get_timeout() + 0.2
    #         )

    #         return move
    #     except RuntimeError:  # In case of timeout, return no move
    #         return None, None
    #     except Exception as e:
    #         raise RuntimeError(f"Exception during function execution: {e}") from e

    def get_move(self):
        return self.players[self.current_player].move_fn(self.board, self.timer)

    def run(self):
        while not self.finished:
            # print(str(self))
            move = self.get_move()
            self.play_move(*move)
        # if self.draw:
        #     print("Draw.")
        # else:
        #     print(f"Player {self.winner} wins !")
        # print(str(self))
        if self.draw:
            return 0.5
        return self.winner
