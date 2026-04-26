"""
Test script for the timeout functionality.

This module tests the run_with_timeout function by executing a computationally
intensive function with a short timeout to verify timeout behavior and
exception handling.
"""

import time

from timeout import run_with_timeout


def heavy():
    """A computationally intensive function for testing timeouts."""
    print("Heavy function started")
    for i in range(1000):
        _ = i**2
    return i


if __name__ == "__main__":
    print("Launching heavy function with timeout...\n")

    start = time.time()

    result = run_with_timeout(
        heavy,
        timeout=0.2
    )

    elapsed = time.time() - start

    print("\n--- RESULT ---")
    print("Result:", result)
    print(f"Elapsed: {elapsed:.2f}s")
