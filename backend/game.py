"""
Game module for managing Gomoku game state and logic.

This module provides the Game class which handles the core game mechanics
including move validation, win detection, and game state management for
an 8x8 Gomoku board.
"""

from .board import Board
# from .board.bitboard import is_last_move_winning, set_bit, board_to_bitboards, winning_tiles_from_last_move, bb_to_moves
from .players.player import Player
from .clock.timer import Timer
# from .clock.timeout import run_with_timeout


class Game:
    """A class representing a Gomoku game."""

    def __init__(self, gid: str, players: list[Player], timer: Timer, starting_position=None, move_list=None, current_player=0):
        """Initialize the game with a list of players and a timer.

        Args:
            players (list[Player]): List of two players.
            timer (Timer): Timer for managing game time.
        """
        self.gid = gid
        self.players = players
        self.timer = timer
        self.board = Board(starting_position, current_player)
        self.memory = [None, None]

        if move_list is None:
            self.moves = []
        else:
            self.moves = move_list
        self.finished = False
        self.draw = False
        self.winner = None  # 0: P1, 1: P2
        self.winningTiles = []

    def __repr__(self):
        s = f"Game {self.gid} - ply {self.board.ply}\n"
        s += str(self.timer)
        s += '\n-----------------------\n'
        s += str(self.board)
        s += '\n-----------------------'
        return s

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
            self._win_game(self.board.opponent())

    def play_move(self, i: int, j: int):
        """Make a move at position (i, j).

        Args:
            i (int): Row index of the move.
            j (int): Column index of the move.
        """
        flagged = self.timer.move_begin()

        if flagged or (self.board[i][j] != 0):  # game lost if illegal move
            self._win_game(self.board.opponent())
            return

        # update board
        self.moves.append((i, j))
        if self.board.add_move(i, j):
            self._win_game(self.board.current_player)
            self.winningTiles = self.board.get_winning_tiles(i, j)
            return

        # Test draws
        if self.board.is_full() or self.board.is_dead():
            self._draw_game()
            return

        # game continues
        self.board.switch_player()
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
        memory = self.memory[self.board.current_player]
        move, memory = self.players[self.board.current_player].move_fn(self.board, self.board.current_player, self.timer.get_times(), memory)
        self.memory[self.board.current_player] = memory
        return move

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
