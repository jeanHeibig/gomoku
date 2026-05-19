from dataclasses import dataclass


from backend.players.bots.ab_bot.board import move_to_square

from self_play.canonicalization import (
    U8,
    BB,
    RawPosition,
    CanonicalPosition,
    RawMove,
    CanonicalMove,
    canonicalize_position,
    uncanonicalize_move,
    get_canonical_legal_moves,
)
from self_play.book import (
    OpeningBook,
    Outcome,
    WIN,
    DRAW,
    LOSS,
    get_or_create_entry,
    update_book_entry,
    get_move_values,
    select_move_from_book,
    save_opening_book,
)
from self_play.board import (
    is_winning,
    is_dead_draw,
)
from self_play.bot import (
    TT,
    create_empty_tt,
    basic_bot,
    alpha_beta_bot,
)

PLY_MAX = 16

ALPHA_BETA = False

MAX_DEPTH = 14
TT_BITS = 32

ROOT_POSITION = CanonicalPosition(
    current=(BB(1) << 27),
    opponent=(BB(1) << 36),
)

@dataclass(slots=True)
class SelfPlayTraceItem:
    """One visited book position during self-play."""

    canonical_position: CanonicalPosition
    canonical_move: CanonicalMove


SelfPlayTrace = list[SelfPlayTraceItem]


@dataclass(slots=True)
class SelfPlayResult:
    """Result of one self-play game."""

    trace: SelfPlayTrace
    outcome: Outcome


def backpropagate_game(
    opening_book: OpeningBook,
    result: SelfPlayResult,
) -> None:
    """
    Backpropagate a finished self-play game.

    Outcome is from the perspective of the first trace item.
    """

    current_outcome = result.outcome

    for item in result.trace:

        entry = get_or_create_entry(
            opening_book,
            item.canonical_position,
        )

        update_book_entry(
            entry,
            item.canonical_move,
            current_outcome,
        )

        current_outcome = -current_outcome


def choose_book_move(
    opening_book: OpeningBook,
    raw_position: RawPosition,
) -> tuple[RawMove, SelfPlayTraceItem]:
    """
    Choose a move using the opening book.

    Returns:
        raw_move:
            Move to actually play on the real board.

        trace_item:
            Canonical position + canonical move to update later.
    """

    canonical_position, transform = canonicalize_position(raw_position)
    canonical_legal_moves = get_canonical_legal_moves(canonical_position)

    entry = get_or_create_entry(opening_book, canonical_position)
    values = get_move_values(entry, canonical_legal_moves)

    canonical_chosen_move = select_move_from_book(
        canonical_legal_moves,
        values,
    )

    raw_chosen_move = uncanonicalize_move(
        canonical_chosen_move,
        transform,
    )

    trace_item = SelfPlayTraceItem(
        canonical_position,
        canonical_chosen_move,
    )

    return raw_chosen_move, trace_item


def choose_bot_move(
    raw_position: RawPosition,
    current_player: U8,
    tt: TT,
) -> tuple[RawMove, TT]:

    if ALPHA_BETA:
        chosen_bot_move, tt = alpha_beta_bot(
            raw_position.current,
            raw_position.opponent,
            current_player,
            U8(MAX_DEPTH),
            tt,
        )
    else:
        chosen_bot_move = basic_bot(
            raw_position.current,
            raw_position.opponent,
        )

    return chosen_bot_move, tt


def self_play_game(
    opening_book: OpeningBook,
    initial_ply: int = 0,
) -> SelfPlayResult:
    """
    Play one self-play game.

    Returns:
        outcome from the perspective of the initial player.
    """

    raw_position = RawPosition(
        current=ROOT_POSITION.current,
        opponent=ROOT_POSITION.opponent,
    )

    trace: SelfPlayTrace = []

    if ALPHA_BETA:
        tt = create_empty_tt(TT_BITS)
    else:
        tt = create_empty_tt(0)

    ply = initial_ply

    while True:

        if ply < PLY_MAX:
            raw_move, trace_item = choose_book_move(
                opening_book,
                raw_position,
            )

            trace.append(trace_item)
        else:
            raw_move, tt = choose_bot_move(
                raw_position,
                U8(ply % 2),
                tt,
            )

        raw_position = RawPosition(
            raw_position.opponent,
            raw_position.current | (BB(1) << raw_move)
        )

        ply += 1

        if is_dead_draw(raw_position.current, raw_position.opponent):

            result = SelfPlayResult(
                trace,
                DRAW,
            )
            return result

        if is_winning(raw_position.opponent):

            if (ply - initial_ply) % 2:
                outcome = WIN
            else:
                outcome = LOSS

            result = SelfPlayResult(
                trace,
                outcome,
            )
            return result


def self_play_loop(
    opening_book: OpeningBook,
    game_count: int,
) -> None:

    print("Starting self play.")

    for game_index in range(game_count):

        result = self_play_game(opening_book)

        # print(f"Game {game_index + 1}: {result.outcome}.")

        backpropagate_game(
            opening_book,
            result,
        )

        if (game_index + 1) % 20_000 == 0:

            save_opening_book(
                opening_book,
                "self_play/book/opening_book.npz",
            )

        # --- DEBUG ---
        if (game_index + 1) % 2_000 == 0:

            root_position = ROOT_POSITION

            root_entry = get_or_create_entry(
                opening_book,
                root_position,
            )

            print()
            print('=' * 80)
            print(f"Games played  : {game_index + 1}.")
            print(f"Book positions: {len(opening_book)}.")
            print()

            root_visits = int(root_entry.visits.sum())

            print(f"Root visits   : {root_visits}.")
            print()

            played_moves = root_entry.visits.nonzero()[0]

            if len(played_moves) == 0:

                print("No root moves played yet.")

            else:

                values = get_move_values(
                    root_entry,
                    played_moves.astype(CanonicalMove)
                )

                order = values.argsort()[::-1]

                print("Root move statistics:")
                print()

                for rank, idx in enumerate(order):

                    move = int(played_moves[idx])

                    visits = int(root_entry.visits[move])

                    wins = int(root_entry.wins[move])
                    draws = int(root_entry.draws[move])
                    losses = int(root_entry.losses[move])

                    value = float(values[idx])

                    print(
                        f"{rank + 1:2d}. "
                        f"move={move_to_square(U8(move))}  "
                        f"visits={visits:7d}  "
                        f"W/D/L=({wins:6d}/{draws:6d}/{losses:6d})  "
                        f"value={value:.4f}"
                    )

            print('=' * 80)
