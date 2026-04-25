"""
Game module for managing Gomoku game state and logic.

This module provides the Game class which handles the core game mechanics
including move validation, win detection, and game state management for
an 8x8 Gomoku board.
"""

from .bitboard import is_last_move_winning, set_bit
from .player import Player
from .timer import Timer


class Game:
    """A class representing a Gomoku game."""

    def __init__(self, players: list[Player], timer: Timer):
        """Initialize the game with a list of players and a timer.

        Args:
            players (list[Player]): List of two players.
            timer (Timer): Timer for managing game time.
        """
        self.players = players
        self.timer = timer

        self.board = [[0]*8 for _ in range(8)]
        self.bitboards = [0, 0]
        self.ply = 0

        self.current_player = 0
        self.finished = False
        self.draw = False
        self.winner = None  # 0: P1, 1: P2

    def _opponent(self):
        return 1 - self.current_player

    def _win_game(self, winner):
        self.finished = True
        self.winner = winner

    def _draw_game(self):
        self.finished = True
        self.draw = True

    def play(self, i: int, j: int) -> bool:
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
