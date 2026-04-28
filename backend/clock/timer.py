"""
Timer module for managing game time controls in Gomoku.

This module provides classes for handling time limits and increments
for players in a turn-based game. It supports both single timers and
dual timers for two-player games with time controls.
"""
from __future__ import annotations

import time


class SingleTimer:
    """A timer for a single player with initial time and increment."""

    def __init__(self, initial_time: float, increment: float):
        """Initialize the timer with initial time and increment.

        Args:
            initial_time: The starting time in seconds.
            increment: The time increment per move in seconds.
        """
        self.initial_time = initial_time
        self.remaining_time = self.initial_time
        self.increment = increment
        self.start_time = None
        self.running = False
        self.flagged = False

    def start(self):
        """Start the timer."""
        self.running = True
        self.start_time = time.time()

    def stop(self):
        """Stop the timer and add increment if not flagged."""
        self.pause()
        if not self.flagged:
            self.add_increment()

    def pause(self):
        """Pause the timer and update remaining time."""
        self.remaining_time -= time.time() - self.start_time
        self.start_time = None
        self.running = False
        if self.remaining_time <= 0.0:
            self.remaining_time = 0.0
            self.flagged = True

    def restart(self):
        """Reset the timer to initial state."""
        self.remaining_time = self.initial_time
        self.start_time = None
        self.running = False
        self.flagged = False

    def add_increment(self):
        """Add the increment to the remaining time."""
        self.remaining_time += self.increment

    def get_remaining_time(self) -> float:
        """Get the current remaining time.

        Returns:
            The remaining time in seconds.
        """
        if self.running:
            return max(0.0, self.remaining_time - time.time() + self.start_time)
        return self.remaining_time


class Timer:
    """
    Dual-timer system for managing time in two-player turn-based games.

    This class manages time controls for both players in a game, handling
    turn switching, time tracking, and flagging detection. It uses two
    SingleTimer instances internally and provides high-level methods for
    game flow integration.

    Attributes:
        _timers (list[SingleTimer]): List of two SingleTimer instances for each player.
        _increments (list[float]): Time increments for each player.
        _current_player (int): Index of currently active player (0 or 1).
        _ply (int): Current move number (ply) in the game.

    Time Control Formats:
        - Single value: Timer([300.0], [5.0]) - same time for both players
        - Dual values: Timer([300.0, 600.0], [5.0, 10.0]) - different times per player

    Game Flow Integration:
        1. Call move_begin() when a player's turn starts
        2. Player makes their move
        3. Call move_end() when the turn ends
        4. Check has_flagged() to detect time losses

    Special First-Move Handling:
        - First two moves get automatic increment (setup time)
        - Normal timing begins after ply 2

    Example:
        >>> # Fischer time: 15 min + 10s increment
        >>> game_timer = Timer(900.0, 10.0)
        >>> game_timer.move_begin()  # Start player 1's timer
        >>> # ... player 1 makes move ...
        >>> game_timer.move_end()    # Switch to player 2
        >>> if game_timer.has_flagged():
        ...     print("Time violation detected!")
    """

    def __init__(
                self,
                initial_time: float | list[float],
                increment: float | list[float],
                ):
        """
        Initialize the dual-timer system.

        Creates a timer system for two players with the specified time controls.
        Accepts either single values (applied to both players) or lists for
        player-specific time controls.

        Args:
            initial_time (float | list[float]): Initial time allocation(s) in seconds.
                - float: Same initial time for both players
                - list[float]: [player1_time, player2_time]
            increment (float | list[float]): Time increment(s) per move in seconds.
                - float: Same increment for both players
                - list[float]: [player1_increment, player2_increment]

        Raises:
            ValueError: If time or increment values are invalid.

        Example:
            >>> # Same time for both: 10 min + 5s increment
            >>> timer = Timer(600.0, 5.0)
            >>> # Different times: P1 gets 15 min, P2 gets 10 min
            >>> timer = Timer([900.0, 600.0], 5.0)
        """
        if isinstance(initial_time, float):
            initial_time = [initial_time] * 2
        if isinstance(increment, float):
            increment = [increment] * 2

        self._timers = [
            SingleTimer(initial_time[0], increment[0]),
            SingleTimer(initial_time[1], increment[1])
        ]
        self._increments = increment
        self._current_player = 0

        self._ply = 0

    def __repr__(self):
        """
        Return string representation of current timer state.

        Returns a string showing the current remaining times for both players.

        Returns:
            str: String representation of player times.

        Example:
            >>> timer = Timer(300.0, 5.0)
            >>> print(timer)  # Shows current times
        """
        return str(self.get_times()["times"])

    def _switch(self):
        """
        Switch to the other player.

        Internal method that toggles the current player between 0 and 1.
        Called automatically during move transitions.

        Note:
            This is an internal method - use move_end() for proper turn handling.
        """
        self._current_player = 1 - self._current_player

    def _start(self):
        """
        Start the current player's timer.

        Internal method that starts the timer for the currently active player.
        Called automatically during move transitions.

        Note:
            This is an internal method - use move_begin() for proper turn handling.
        """
        self._timers[self._current_player].start()

    def _stop(self):
        """
        Stop the current player's timer.

        Internal method that stops the timer for the currently active player.
        Called automatically during move transitions.

        Note:
            This is an internal method - use move_end() for proper turn handling.
        """
        self._timers[self._current_player].stop()

    def _get_timeout(self):
        """
        Get the remaining time for the current player.

        Internal method that returns the current player's remaining time.

        Returns:
            float: Remaining time in seconds for current player.
        """
        return self._timers[self._current_player].get_remaining_time()

    def has_flagged(self):
        """
        Check if the current player has flagged (run out of time).

        Determines if the currently active player has exceeded their time limit.
        This should be checked after move_begin() to detect time violations.

        Returns:
            bool: True if current player has flagged, False otherwise.

        Note:
            Only valid after move_begin() has been called for the current turn.

        Example:
            >>> timer.move_begin()
            >>> if timer.has_flagged():
            ...     print("Player ran out of time!")
        """
        return (self._get_timeout() <= 0) and self.move_begin()

    def get_times(self):
        """
        Get the current times for both players and server time.

        Returns comprehensive timing information including server timestamp,
        player remaining times, and increment values.

        Returns:
            dict: Dictionary containing:
                - "server_time" (float): Current server time (time.time())
                - "times" (list[float]): [player1_time, player2_time] in seconds
                - "increments" (list[float]): [player1_increment, player2_increment]

        Example:
            >>> times = timer.get_times()
            >>> print(f"Player 1: {times['times'][0]:.1f}s")
            >>> print(f"Server time: {times['server_time']}")
        """
        return {
            "server_time": time.time(),
            "times": [t.get_remaining_time() for t in self._timers],
            "increments": self._increments,
        }  # TODO: Add clockPly

    def get_ply(self):
        """
        Get the current ply (move number) in the game.

        Returns the current move number, which affects timing behavior
        (special handling for first few moves).

        Returns:
            int: Current ply number (0-based).

        Example:
            >>> ply = timer.get_ply()
            >>> print(f"Move number: {ply + 1}")
        """
        return self._ply

    def move_begin(self):
        """
        Begin a player's move - stop previous timer and check for flagging.

        This method should be called at the start of a player's turn. It:
        1. Stops the previous player's timer (if ply > 1)
        2. Checks if the previous player flagged
        3. Increments the ply counter

        For the first two moves (ply 0 and 1), special timing rules apply:
        - No timer stopping occurs
        - Automatic increment is added later in move_end()

        Returns:
            bool: True if the PREVIOUS player has flagged (time violation),
                False otherwise.

        Note:
            Return value indicates if the opponent flagged, not current player.
            Use has_flagged() to check current player status.

        Example:
            >>> flagged = timer.move_begin()
            >>> if flagged:
            ...     print("Previous player lost on time!")
            >>> # Now current player can make their move
        """
        if self._ply > 1:  # Normal timing after first two moves
            self._stop()
            if self._timers[self._current_player].flagged:
                return True

        self._ply += 1
        return False

    def move_end(self):
        """
        End a player's move - switch players and start next timer.

        This method should be called at the end of a player's turn. It:
        1. Adds increment for first two moves (setup time)
        2. Switches to the next player
        3. Starts the next player's timer (if ply > 1)

        The timing behavior depends on the current ply:
        - ply < 3: Add increment (generous setup time)
        - ply > 1: Start next player's timer

        Example:
            >>> # After player makes move
            >>> timer.move_end()  # Switch to next player, start their timer
        """
        if self._ply < 3:  # Generous time for first two moves
            self._timers[self._current_player].add_increment()

        self._switch()
        if self._ply > 1:
            self._start()
