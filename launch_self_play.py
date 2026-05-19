from self_play.book import load_opening_book
from self_play.self_play import OpeningBook, self_play_loop


try:
    opening_book = load_opening_book(
        "self_play/book/opening_book.npz"
    )

    print("Book found.")

except FileNotFoundError:
    opening_book: OpeningBook = {}

    print("No book found. Creating empty book.")

self_play_loop(opening_book, 200_000)
