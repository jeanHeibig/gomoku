"""
Game module for managing Gomoku game state and logic.

This module provides the Game class which handles the core game mechanics
including move validation, win detection, and game state management for
an 8x8 Gomoku board.
"""

from .bitboard import is_last_move_winning, set_bit, board_to_bitboards, winning_tiles_from_last_move, bb_to_moves
from .players.player import Player
from .clock.timer import Timer
# from .clock.timeout import run_with_timeout


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
        self.bitboards = board_to_bitboards(self.board)
        self.ply = len([(i, j) for i in range(8) for j in range(8) if self.board[i][j]])
        self.current_player = self.ply % 2
        self.moves = []

        self.finished = False
        self.draw = False
        self.winner = None  # 0: P1, 1: P2
        self.winningTiles = []

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
        """Set the game as finished with the given winner.

        Args:
            winner (int): The index of the winning player (0 or 1).
        """
        self.finished = True
        self.winner = winner

    def _draw_game(self):
        """Set the game as finished with a draw."""
        self.finished = True
        self.draw = True

    def flag_check(self):
        """Check if any player has run out of time and end the game if so.

        If the timer indicates that the current player has flagged (run out of time),
        the game is ended with the opponent declared as the winner.
        """
        if self.timer.has_flagged():
            self._win_game(self._opponent())

    def play_move(self, i: int, j: int):
        """Make a move at position (i, j).

        Args:
            i (int): Row index of the move.
            j (int): Column index of the move.
        """
        flagged = self.timer.move_begin()

        if flagged or (self.board[i][j] != 0):  # game lost if illegal move
            self._win_game(self._opponent())
            return

        # update board
        self.board[i][j] = self.current_player + 1
        self.ply += 1
        self.bitboards[self.current_player] = set_bit(self.bitboards[self.current_player], i, j)
        self.moves.append((i, j))

        if is_last_move_winning(self.bitboards[self.current_player], i, j):
            self._win_game(self.current_player)
            self.winningTiles = bb_to_moves(winning_tiles_from_last_move(self.bitboards[self.current_player], i, j))
            return

        # Test draws
        if self.ply == 64:
            self._draw_game()
            return

        # game continues
        self.current_player = self._opponent()
        self.timer.move_end()

    def last_move(self):
        """Return the last move made. None if no move was made."""
        if self.moves:
            return self.moves[-1]
        return None

    def get_move(self):
        """Get the next move from the current player.

        Returns:
            tuple: A tuple (i, j) representing the row and column of the move.
        """
        return self.players[self.current_player].move_fn(self.board, self.timer)

    def move(self):
        """Execute one move in the game by getting and playing the current player's move."""
        move = self.get_move()
        self.play_move(*move)

    def run(self, verbose=False):
        """Run the complete game until completion.

        Returns:
            float: The game result (0.5 for draw, 0 or 1 for the winning player index).
        """
        while not self.finished:
            if verbose:
                print(str(self))
            self.move()

        if verbose:
            if self.draw:
                print("Draw.")
            else:
                print(f"Player {self.winner} wins !")
            print(str(self))

        return self.score()

    def score(self):
        """Return the game score.

        Returns:
            float: 0.5 for a draw, or the winning player index (0 or 1).
        """
        if self.draw:
            return 0.5
        return self.winner
