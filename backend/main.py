import os
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
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
def new_game(time_control: int, increment: int):
    gid = len(games)

    game = Game()
    game.time = [time_control, time_control]
    game.increment = increment

    games[gid] = game

    return serialize_game(game) | {"game_id": gid}


@app.post("/move/{gid}")
def move(gid: int, i: int, j: int):
    game = games[gid]
    ok = game.play(i, j)

    # # si pas fini + bot joue
    # # TODO: je trouve ça maladroit d'avoir placé le move du bot ici, non ?
    # if ok and not game.finished:
    #     move = random_bot(game.board, None)
    #     if move:
    #         game.play(*move)

    return {"ok": ok} | serialize_game(game)


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
    return {"ok": True} | serialize_game(game)


def serialize_game(game):
    return {
        "board": game.board,
        "player_names": game.player_names,
        "player": game.player,
        "time": game.time,
        "started": game.started,
        "finished": game.finished,
        "winner": game.winner,
    }

# @app.websocket("/ws/{gid}")
# async def websocket_endpoint(ws: WebSocket, gid: int, name: str):
#     await ws.accept()

#     game = games[gid]

#     if game.player_names[0] is None:
#         role = 0
#         game.player_names[0] = name
#     elif game.player_names[1] is None:
#         role = 1
#         game.player_names[1] = name
#     else:
#         role = None  # spectateur

#     game.connections.append(ws)

#     await ws.sens_json(serialize_game(game))

#     try:
#         while True:
#             data = await ws.receive_json()

#             if data["type"] == "move":
#                 if role != game.player:
#                     continue

#                 ok = game.play(data["i", data["j"]])
#                 if not ok:
#                     continue

#                 payload = serialize_game(game)

#                 # broadcast
#                 alive = []
#                 for conn in game.connections:
#                     try:
#                         await conn.sens_json(payload)
#                         alive.append(conn)
#                     except:
#                         pass
#                 game.connections = alive

#     except WebSocketDisconnect:
#         game.connections.remove(ws)
