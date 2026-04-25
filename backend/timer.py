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

    def get_time(self) -> float:
        """Get the current remaining time.

        Returns:
            The remaining time in seconds.
        """
        if self.running:
            return max(0.0, self.remaining_time - time.time() + self.start_time)
        return self.remaining_time


class Timer:
    def __init__(
                self,
                initial_time: float | list[float],
                increment: float | list[float],
                ):
        if isinstance(initial_time, float):
            initial_time = [initial_time] * 2
        if isinstance(increment, float):
            increment = [increment] * 2

        self.timers = [
            SingleTimer(initial_time[0], increment[0]),
            SingleTimer(initial_time[1], increment[1])
        ]

        self.ply_nb = 0

        self.current_player = 0
        self.flagged_player = None

        self.finished = False

    def _switch(self):
        self.current_player = 1 - self.current_player

    def _start(self):
        self.timers[self.current_player].start()

    def _stop(self):
        self.timers[self.current_player].stop()

    def pause(self):
        """Pause the game clock. Use resume to start the clock again."""
        self.timers[self.current_player].pause()

    def resume(self):
        """Resume the current player's timer."""
        self._start()

    def restart(self):
        """Reset all timers and game state."""
        for t in self.timers:
            t.restart()

        self.ply_nb = 0

        self.current_player = 0
        self.flagged_player = None

        self.finished = False

    def is_running(self):
        """Check if the current player's timer is running.

        Returns:
            True if the timer is running, False otherwise.
        """
        return self.timers[self.current_player].running

    def get_times(self):
        """Get the current times for both players.

        Returns:
            A dictionary with server time and player times.
        """
        return {
            "server_time": time.time(),
            "times": [t.get_time() for t in self.timers],
        }

    def first_move(self):
        """Handle the first move: add increment and switch players."""
        self.timers[self.current_player].add_increment()
        self._switch()
        self.ply_nb += 1
        if self.ply_nb > 1:
            self._start()

    def move_begin(self):
        """Stop the current player's timer and check for flag.

        Returns:
            False if the player has flagged (time out), True otherwise.
        """
        self._stop()
        if self.timers[self.current_player].flagged:
            self.flagged_player = self.current_player
            self.finished = True
            return False
        self.ply_nb += 1
        return True

    def move_end(self):
        """Switch to the opponent and start their timer."""
        self._switch()
        self._start()
