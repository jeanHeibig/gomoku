from dataclasses import dataclass

from self_play.canonicalization import (
    BB,
    RawPosition,
    canonicalize_position,
    get_canonical_legal_moves,
    uncanonicalize_move,
)
from self_play.book import OpeningBook, BookKey, move_value


@dataclass(slots=True)
class MoveStatistics:
    """Human-readable move statistics."""

    move: int

    visits: int

    wins: int
    draws: int
    losses: int

    value: float


def query_position(
    opening_book: OpeningBook,
    raw_position: RawPosition,
) -> list[MoveStatistics]:

    # Canonicalize
    canonical_position, transform = canonicalize_position(raw_position)

    # Lookup entry
    key = BookKey(
        (
            canonical_position.current,
            canonical_position.opponent,
        )
    )

    entry = opening_book.get(key)

    if entry is None:
        return []

    # Legal canonical moves
    canonical_legal_moves = get_canonical_legal_moves(canonical_position)

    # statistics
    results: list[MoveStatistics] = []

    for canonical_move in canonical_legal_moves:
        visits = int(entry.visits[canonical_move])

        wins = int(entry.wins[canonical_move])
        draws = int(entry.draws[canonical_move])
        losses = int(entry.losses[canonical_move])

        value = move_value(
            wins,
            draws,
            losses,
        )

        # transform back to raw moves
        raw_move = uncanonicalize_move(
            canonical_move,
            transform,
        )

        # sorted human readable results
        results.append(
            MoveStatistics(
                move=int(raw_move),

                visits=visits,

                wins=wins,
                draws=draws,
                losses=losses,

                value=value,
            )
        )

    results.sort(
        key=lambda stat: (
            stat.value,
            stat.visits,
        ),
        reverse=True,
    )

    return results
