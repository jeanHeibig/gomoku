import os
import uuid
import random

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.clock.timer import Timer
from backend.game import Game
from backend.players.human import human
from backend.players.online_bot import online_bot
from backend.players.player import Player

app = FastAPI()

games = {}
player1 = Player("Alice", False, human)
player2 = Player("Bob", True, online_bot)


app.mount("/static", StaticFiles(directory="./frontend"), name="static")


@app.get("/")
def serve_game():
    return FileResponse(os.path.join(".", "frontend", "game.html"))


@app.get("/new_game")
def new_game():
    gid = str(uuid.uuid4())

    human_starts = random.randint(0, 1)
    if human_starts:  # random choice for the side
        players = [player1, player2]
    else:
        players = [player2, player1]

    timer = Timer(3.0, 1.0)
    game = Game(gid, players, timer)

    if not human_starts:  # if bot starts
        game.move()

    games[gid] = game
    return serialize(game)


@app.post("/move")
def play_move(gid: str, i: int, j: int):
    game = games[gid]

    if game.finished:
        return serialize(game)

    # human move
    game.play_move(i, j)

    if not game.finished:
        game.move()

    return serialize(game)


@app.post("/flag")
def flag(gid: str):
    game = games[gid]
    game.flag_check()

    return serialize(game)


@app.get("/state")
def get_state(gid: str):
    return serialize(games[gid])


def serialize(game: Game):
    return {
        "gid": game.gid,
        "players": game.players,
        "board": game.board,
        "times": game.timer.get_times(),
        "clockPly": game.timer.ply,
        "currentPlayer": game.current_player,
        "finished": game.finished,
        "winner": game.winner,
    }
