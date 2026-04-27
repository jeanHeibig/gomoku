"""
Board module for Gomoku game state management.

This module provides the core Board class for representing and manipulating
the 8x8 Gomoku game board. It handles game state, move validation, win detection,
and player switching using efficient bitboard operations for performance.

The Board class integrates with the bitboard module for fast win detection
and move generation, providing a clean interface for game logic while
maintaining both 2D array representation and bitboard optimization.

Key Features:
    - 8x8 board representation with 2D array and bitboard duality
    - Efficient win detection using bitboard operations
    - Move validation and game state tracking
    - Player switching and turn management
    - Winning tile highlighting for UI display

Classes:
    Board: Main game board class with move handling and win detection

Constants:
    BOARD_SIZE: Fixed board dimension (8x8)
"""

from .bitboard import board_to_bitboards, ij_to_bit, is_last_move_winning, bb_to_moves, winning_tiles_from_last_move

BOARD_SIZE = 8


class Board:
    """
    Represents the 8x8 Gomoku game board with move handling and win detection.

    This class manages the game state using both a 2D array representation
    for easy access and bitboards for efficient win detection and move analysis.
    It tracks the current player, move count, and provides methods for making
    moves and checking game status.

    Attributes:
        position (list[list[int]]): 8x8 grid where 0=empty, 1=player1, 2=player2
        ply (int): Current move number (0-based)
        current_player (int): Current player index (0 or 1)
        bitboards (list[int]): Bitboard representations for both players

    Game Rules:
        - 8x8 board grid
        - Players alternate placing stones
        - First to get 5 in a row wins
        - No draws possible (board fills completely)

    Example:
        >>> board = Board()  # Empty board
        >>> board.add_move(3, 3)  # Player 1 places at center
        >>> board.switch_player()  # Switch to player 2
        >>> board.add_move(3, 4)  # Player 2 places adjacent
        >>> print(board)  # Display board state
    """

    def __init__(self, starting_position=None, current_player=None):
        """
        Initialize the game board with optional starting position.

        Creates a new board instance with the specified starting position
        and current player. If no position is provided, starts with an
        empty board. The current player is automatically determined from
        the number of pieces on the board if not specified.

        Args:
            starting_position (list[list[int]], optional): 8x8 grid with
                0 for empty, 1 for player 1, 2 for player 2. Defaults to empty board.
            current_player (int, optional): Current player (0 or 1). If None,
                determined from piece count (even ply = player 0, odd ply = player 1).

        Example:
            >>> # Empty board
            >>> board = Board()
            >>> # Board with some pieces
            >>> position = [[0]*8 for _ in range(8)]
            >>> position[3][3] = 1  # Player 1 piece
            >>> board = Board(position, current_player=1)
        """
        if starting_position is None:
            starting_position = [[0]*BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.position = starting_position

        self.ply = len(self.get_taken_spots())

        if current_player is None:
            current_player = self.ply % 2
        self.current_player = current_player

        self.bitboards = board_to_bitboards(self.position)

    def __repr__(self):
        """
        Return string representation of the board.

        Creates a visual representation of the board using characters:
        - 'x': Player 1 pieces
        - 'o': Player 2 pieces
        - '.': Empty squares

        Returns:
            str: Multi-line string showing the board layout.

        Example:
            >>> board = Board()
            >>> board.add_move(0, 0)
            >>> print(board)
            x.......
            ........
            ........
            ........
            ........
            ........
            ........
            ........
        """
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
        """
        Get a row from the board position.

        Allows indexing the board like a 2D array to access rows.

        Args:
            key (int): Row index (0-7).

        Returns:
            list[int]: The specified row as a list of 8 integers.

        Example:
            >>> board = Board()
            >>> row_3 = board[3]  # Get fourth row
            >>> print(row_3)  # [0, 0, 0, 0, 0, 0, 0, 0]
        """
        return self.position[key]

    def get_taken_spots(self):
        """
        Get list of all occupied positions on the board.

        Returns coordinates of all squares that contain player pieces.

        Returns:
            list[tuple[int, int]]: List of (row, col) tuples for occupied squares.

        Example:
            >>> board = Board()
            >>> board.add_move(0, 0)
            >>> board.add_move(1, 1)
            >>> taken = board.get_taken_spots()
            >>> print(taken)  # [(0, 0), (1, 1)]
        """
        return [
            (i, j)
            for i in range(BOARD_SIZE)
            for j in range(BOARD_SIZE)
            if self.position[i][j]
        ]

    def add_move(self, i, j):
        """
        Add a move to the board at the specified position.

        Places the current player's piece at (i, j), updates the ply count,
        and updates the bitboard representation. Checks if this move creates
        a winning condition.

        Args:
            i (int): Row index (0-7).
            j (int): Column index (0-7).

        Returns:
            bool: True if this move creates a win (5 in a row), False otherwise.

        Note:
            Does not validate if the position is empty - assumes valid move.
            Automatically updates bitboards for efficient win detection.

        Example:
            >>> board = Board()
            >>> is_win = board.add_move(3, 3)  # Place at center
            >>> print(is_win)  # False (single piece can't win)
        """
        self.position[i][j] = self.current_player + 1
        self.ply += 1
        self.bitboards[self.current_player] |= ij_to_bit(i, j)
        return is_last_move_winning(self.bitboards[self.current_player], i, j)

    def get_winning_tiles(self, i, j):
        """
        Get the tiles that form the winning line for a move at (i, j).

        For a winning move, returns all positions that contribute to the
        5-in-a-row. For non-winning moves, returns empty list.

        Args:
            i (int): Row index of the move (0-7).
            j (int): Column index of the move (0-7).

        Returns:
            list[tuple[int, int]]: List of (row, col) tuples forming the win,
                or empty list if move doesn't win.

        Note:
            Used for highlighting winning moves in the UI.

        Example:
            >>> # Assuming a winning position exists
            >>> winning_tiles = board.get_winning_tiles(3, 3)
            >>> print(winning_tiles)  # [(3,1), (3,2), (3,3), (3,4), (3,5)]
        """
        bb_tiles = winning_tiles_from_last_move(self.bitboards[self.current_player], i, j)
        return bb_to_moves(bb_tiles)

    def is_full(self):
        """
        Check if the board is completely full.

        Determines if all 64 squares contain pieces, making the game a draw

        Returns:
            bool: True if board is full (64 pieces), False otherwise.

        Example:
            >>> board = Board()
            >>> # ... fill all squares ...
            >>> print(board.is_full())  # True when 64 moves played
        """
        return self.ply == BOARD_SIZE * BOARD_SIZE

    def switch_player(self):
        """
        Switch to the other player.

        Changes the current player from 0 to 1 or 1 to 0.

        Example:
            >>> board = Board()
            >>> print(board.current_player)  # 0
            >>> board.switch_player()
            >>> print(board.current_player)  # 1
        """
        self.current_player = self.opponent()

    def opponent(self):
        """
        Get the opponent player index.

        Returns the index of the player who is not currently active.

        Returns:
            int: Opponent player index (0 or 1).

        Example:
            >>> board = Board()
            >>> board.current_player = 0
            >>> print(board.opponent())  # 1
            >>> board.current_player = 1
            >>> print(board.opponent())  # 0
        """
        return 1 - self.current_player
