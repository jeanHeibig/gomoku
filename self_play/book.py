from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from self_play.canonicalization import (
    BB,
    CanonicalPosition,
    CanonicalMove,
    CanonicalMoveArray
)


U32 = np.uint32
F32 = np.float32

U32Array = NDArray[U32]
F32Array = NDArray[F32]

BookKey = tuple[BB, BB]  # (canonical_current, canonical_opponent)
Outcome = int


WIN = Outcome(1)
DRAW = Outcome(0)
LOSS = Outcome(-1)


BOOK_VERSION = 1


@dataclass(slots=True)
class BookEntry:
    """Opening-book statistics for a canonical position."""

    visits: U32Array

    wins: U32Array
    draws: U32Array
    losses: U32Array


def create_empty_book_entry() -> BookEntry:
    """Create an empty opening-book entry."""

    return BookEntry(
        visits=np.zeros(64, dtype=U32),
        wins=np.zeros(64, dtype=U32),
        draws=np.zeros(64, dtype=U32),
        losses=np.zeros(64, dtype=U32),
    )


def canonical_position_to_key(
    position: CanonicalPosition,
) -> BookKey:
    """Convert a canonical position into a dictionary key."""

    return (
        position.current,
        position.opponent,
    )


OpeningBook = dict[BookKey, BookEntry]


def get_or_create_entry(
    opening_book: OpeningBook,
    canonical_position: CanonicalPosition,
) -> BookEntry:
    """Get or create a book entry."""

    key = canonical_position_to_key(
        canonical_position,
    )

    entry = opening_book.get(key)

    if entry is None:
        entry = create_empty_book_entry()
        opening_book[key] = entry

    return entry


def update_book_entry(
    entry: BookEntry,
    canonical_move: CanonicalMove,
    outcome: Outcome,
) -> None:
    """
    Update a book entry after playing a move.

    Outcome is from the perspective of the player to move:
        WIN  =  1
        DRAW =  0
        LOSS = -1
    """
    entry.visits[canonical_move] += U32(1)

    if outcome == WIN:
        entry.wins[canonical_move] += U32(1)

    elif outcome == DRAW:
        entry.draws[canonical_move] += U32(1)

    else:
        entry.losses[canonical_move] += U32(1)


def move_value(
    wins: int,
    draws: int,
    losses: int,
    draw_value: float = 0.5,
    prior: float = 1.0,
) -> float:
    """
    Estimate the value of a move from current-player perspective.

    Return a number between 0 and 1:
        1 = winning
        0.5 = drawing
        0 = losing
    """

    total = wins + draws + losses

    return (
        wins + draw_value * draws + prior * 0.5
    ) / (
        total + prior
    )


def get_move_values(
    entry: BookEntry,
    canonical_legal_moves: CanonicalMoveArray,
) -> F32Array:
    """
    Compute values for legal canonical moves.

    Returns:
        values:
            Float values aligned with legal_moves.
    """

    values = np.empty(len(canonical_legal_moves), dtype=F32)

    for i, canonical_move in enumerate(canonical_legal_moves):

        # Recover statistics
        wins = int(entry.wins[canonical_move])
        draws = int(entry.draws[canonical_move])
        losses = int(entry.losses[canonical_move])

        values[i] = move_value(
            wins,
            draws,
            losses,
        )

    return values


def value_to_logit(
    value: float,
    eps: float = 1e-6,
) -> float:
    """Convert a probability-like value into a logit."""

    value = np.clip(value, eps, 1.0 - eps)

    return np.log(value / (1.0 - value))


def select_move_from_book(
    canonical_legal_moves: CanonicalMoveArray,
    values: F32Array,
    temperature: float = 1.0,
) -> CanonicalMove:

    logits = np.empty(len(values), dtype=F32)

    for i, value in enumerate(values):
        logits[i] = value_to_logit(float(value))

    logits /= temperature

    logits -= np.max(logits)

    probabilities = np.exp(logits)
    probabilities /= np.sum(probabilities)

    choice = np.random.choice(len(canonical_legal_moves), p=probabilities)

    return CanonicalMove(canonical_legal_moves[choice])


def save_opening_book(
    opening_book: OpeningBook,
    path: str,
) -> None:

    n = len(opening_book)

    positions_current = np.empty(n, dtype=BB)
    positions_opponent = np.empty(n, dtype=BB)

    visits = np.empty((n, 64), dtype=U32)

    wins = np.empty((n, 64), dtype=U32)
    draws = np.empty((n, 64), dtype=U32)
    losses = np.empty((n, 64), dtype=U32)

    for i, (key, entry) in enumerate(opening_book.items()):

        positions_current[i] = key[0]
        positions_opponent[i] = key[1]

        visits[i] = entry.visits

        wins[i] = entry.wins
        draws[i] = entry.draws
        losses[i] = entry.losses

    np.savez_compressed(
        path,

        positions_current=positions_current,
        positions_opponent=positions_opponent,

        visits=visits,

        wins=wins,
        draws=draws,
        losses=losses,

        version=np.array([BOOK_VERSION], dtype=U32)
    )

    print(
        f"Saved opening book with "
        f"{len(opening_book)} positions."
    )


def load_opening_book(
    path: str,
) -> OpeningBook:

    data = np.load(path)

    version = int(data["version"][0])

    if version != BOOK_VERSION:
        raise ValueError(
            f"Unsupported book version: "
            f"{version} != {BOOK_VERSION}"
        )

    positions_current = data["positions_current"]
    positions_opponent = data["positions_opponent"]

    visits = data["visits"]

    wins = data["wins"]
    draws = data["draws"]
    losses = data["losses"]

    n = len(positions_current)

    # --- SHAPE VALIDATION ---

    assert positions_opponent.shape == (n,)

    assert visits.shape == (n, 64)

    assert wins.shape == (n, 64)
    assert draws.shape == (n, 64)
    assert losses.shape == (n, 64)

    # --- REBUILD BOOK ---

    opening_book: OpeningBook = {}

    for i in range(n):

        key = (
            BB(positions_current[i]),
            BB(positions_opponent[i]),
        )

        entry = BookEntry(
            visits=visits[i].copy(),

            wins=wins[i].copy(),
            draws=draws[i].copy(),
            losses=losses[i].copy(),
        )

        opening_book[key] = entry

    print(
        f"Loaded opening book with "
        f"{len(opening_book)} positions."
    )

    return opening_book
