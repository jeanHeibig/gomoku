from backend.players.bots.ab_bot.board import move_to_square

from self_play.board import move_names_to_raw_position
from self_play.book import load_opening_book
from self_play.book_query import query_position
from self_play.self_play import U8, OpeningBook, self_play_loop
#

try:
    opening_book = load_opening_book(
        "self_play/book/opening_book.npz"
    )

except FileNotFoundError:
    print("No book found. Creating empty book.")

    opening_book: OpeningBook = {}

self_play_loop(opening_book, 100_000)


# def prettyprint(bb, reverse=True, h=False, end='\n') -> None:
#     """Print pretty string for bitboard."""
#     if bb < 0:
#         bb += 2**64
#     s = bin(bb)[2:]
#     s = ((64 - len(s)) * '0' + s).replace('0', '.')
#     p = '\n'.join([s[i:i+8] for i in range(0, 64, 8)])

#     if h:
#         h = hex(bb)[2:]
#         h = '0x' + (16 - len(h)) * '0' + h
#         print(h)

#     if reverse:
#         print(p[::-1], end=end)
#     else:
#         print(p, end=end)


# while True:
#     game = input("Enter moves (comma separated): ")
#     if game:
#         move_names = game.split(',')
#     else:
#         move_names = []

#     # print("Move names:")
#     # print(move_names)

#     raw_position = move_names_to_raw_position(move_names)

#     # prettyprint(raw_position.current)
#     # print()
#     # prettyprint(raw_position.opponent)
#     # print()

#     list_move_statistics = query_position(opening_book, raw_position)
#     # print(list_move_statistics)

#     print()
#     print('=' * 80)
#     print(f"Book positions: {len(opening_book)}.")
#     print()

#     print("Root move statistics:")
#     print()

#     for rank, move_statistics in enumerate(list_move_statistics):

#         print(
#             f"{rank + 1:2d}. "
#             f"move={move_to_square(U8(move_statistics.move))}  "
#             f"visits={move_statistics.visits:7d}  "
#             f"W/D/L=({move_statistics.wins:6d}/{move_statistics.draws:6d}/{move_statistics.losses:6d})  "
#             f"value={move_statistics.value:.4f}"
#         )

#     print('=' * 80)
