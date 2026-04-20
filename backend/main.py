import os
import time

from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from game import Game
from bots.random_bot import random_bot

app = FastAPI()
games = {}

app.mount("/static", StaticFiles(directory="../frontend"), name="static")

@app.get("/")
def root():
    return {"status": "running"}

@app.get("/game")
def game_page():
    return FileResponse(os.path.join("..", "frontend", "index.html"))

@app.get("/new_game")
def new_game():
    gid = len(games)
    games[gid] = Game()
    game = games[gid]

    return {
        "game_id": gid,
        "board": game.board,
        "time": game.time,
        "player": game.player,
        "started": game.started,
        "finished": game.finished,
        "winner": game.winner,
    }

@app.post("/move/{gid}")
def move(gid: int, i: int, j: int):
    game = games[gid]
    ok = game.play(i, j)

    # si pas fini + bot joue
    # TODO: je trouve ça maladroit d'avoir placé le move du bot ici, non ?
    if ok and not game.finished:
        move = random_bot(game.board, None)
        if move:
            game.play(*move)

    return {
        "ok": ok,
        "board": game.board,
        "time": game.time,
        "player": game.player,
        "started": game.started,
        "finished": game.finished,
        "winner": game.winner,
    }

@app.post("/check_timeout/{gid}")
def check_timeout(gid: int):
    if gid not in games:
        return {"ok": False}

    game = games[gid]

    if game.finished:
        return {
            "finished": True,
            "winner": game.winner,
        }

    if game.last_move_time is None:
        return {"finished": False}

    # TODO: Serait plus propre de calculer les temps dans Game.
    now = time.time()
    elapsed = now - game.last_move_time

    if game.time[game.player] - elapsed <= 0:
        game.time[game.player] = 0.0
        game.finished = True
        game.winner = 1 - game.player

    # TODO mettre ce dico dans une fonction serialize_game
    return {
        "ok": True,
        "board": game.board,
        "time": game.time,
        "player": game.player,
        "started": game.started,
        "finished": game.finished,
        "winner": game.winner,
    }

@app.websocket("/ws/{gid}")
async def websocket_endpoint(ws: WebSocket, gid: int):
    await ws.accept()
    while True:
        await ws.send_json(games[gid].board)
