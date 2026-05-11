"""
Gomoku Game API Server

This module provides a FastAPI-based REST API for playing Gomoku (8x8) games
against an AI opponent. The API supports creating games, making moves, checking
time flags, and retrieving game state.

API Endpoints:
- GET /: Serve the game HTML interface
- POST /new_game: Create a new game with random player order
- POST /move: Make a move in an existing game
- POST /flag: Check for time violations in a game
- GET /state: Get current state of a game

Game Rules:
- 8x8 board
- First to get 5 in a row wins
- Time controls: 3 minutes + 1 second increment per move
- Human vs AI gameplay
"""

import os
import uuid
import random

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import numpy as np

from backend import Timer, Game, Player
from backend.board import b2b, bb2m
from backend.players import human, bots
from backend.players.bots.tss_bot.tactics import get_forced_moves

app = FastAPI()

games = {}
player1 = Player("Alice", False, human)
BOT_NAMES = ["Bob", "Charlie", "Damian", "Edgar", "Ferdinand", "Gaston", "Harry"]

app.mount("/static", StaticFiles(directory="./frontend"), name="static")


@app.get("/")
def serve_game():
    """Serve the main game HTML page.

    Returns the HTML file for the Gomoku game interface.

    Returns:
        FileResponse: The game.html file from the frontend directory.
    """
    return FileResponse(os.path.join(".", "frontend", "game.html"))


@app.post("/new_game")
def new_game(level: int, time: int, increment: int):
    """Create a new Gomoku game.

    Initializes a new game with random player order (human vs bot),
    sets up the timer, and makes the first move if the bot starts.

    Returns:
        dict: Serialized game state containing:
            - gid: Game ID (string)
            - players: List of player objects
            - board: 8x8 game board matrix
            - times: Dictionary with server time and player times
            - clockPly: Current ply number for timing
            - currentPlayer: Index of current player (0 or 1)
            - finished: Boolean indicating if game is over
            - winner: Winner index (0, 1) or None
    """
    gid = str(uuid.uuid4())

    player2 = Player(BOT_NAMES[level], True, bots[level])

    human_starts = random.randint(0, 1)
    if human_starts:  # random choice for the side
        players = [player1, player2]
    else:
        players = [player2, player1]

    timer = Timer(float(time), float(increment))

    game = Game(gid, players, timer)

    games[gid] = game
    return serialize(game)


@app.post("/submit_board")
def submit_board(req: dict):
    gid = str(uuid.uuid4())

    position = req["board"]
    move_list = req["moveList"]
    current_player = int(req["editorPlayer"])
    localPlayer = int(req["localPlayer"])
    level = int(req["level"])
    time = float(req["time"])
    increment = float(req["increment"])

    player2 = Player(BOT_NAMES[level], True, bots[level])

    timer = Timer(time, increment)

    players = [player2, player2]
    players[localPlayer] = player1

    game = Game(gid, players, timer, position, move_list, current_player)

    games[gid] = game
    return serialize(game)


@app.post("/move")
def play_move(gid: str, i: int, j: int):
    """Make a move in the specified game.

    Executes the human player's move at position (i, j), then makes
    the bot's move if the game continues.

    Args:
        gid (str): Game ID to make the move in.
        i (int): Row index of the move (0-7).
        j (int): Column index of the move (0-7).

    Returns:
        dict: Updated serialized game state (same format as /new_game).

    Note:
        If the game is already finished, returns the current state without changes.
        Invalid moves will result in game loss for the human player.
    """
    game = games[gid]

    if game.finished:
        return serialize(game)

    # human move
    game.play_move(i, j)

    if not game.finished:
        game.move()

    return serialize(game)


@app.post("/botMove")
def play_bot_move(gid: str):
    game = games[gid]

    if game.finished:
        return serialize(game)

    if not game.finished:
        game.move()

    return serialize(game)


@app.post("/flag")
def flag(gid: str):
    """Check for time flag in the specified game.

    Updates the game state to check if any player has run out of time.
    This should be called periodically to enforce time controls.

    Args:
        gid (str): Game ID to check for time flags.

    Returns:
        dict: Updated serialized game state (same format as /new_game).

    Note:
        If a player has flagged (run out of time), the game will be marked
        as finished with the other player as winner.
    """
    game = games[gid]
    game.flag_check()

    return serialize(game)


@app.get("/state")
def get_state(gid: str):
    """Get the current state of a game.

    Retrieves the complete current state of the specified game without
    making any changes.

    Args:
        gid (str): Game ID to retrieve state for.

    Returns:
        dict: Current serialized game state (same format as /new_game).
    """
    return serialize(games[gid])


def serialize(game: Game):
    """Serialize a Game object into a JSON-compatible dictionary.

    Converts the game state into a format suitable for API responses,
    including all necessary information for the frontend to display
    and manage the game.

    Args:
        game (Game): The game object to serialize.

    Returns:
        dict: Dictionary containing:
            - gid: Game ID (string)
            - players: List of player objects
            - board: 8x8 game board matrix (0=empty, 1=player1, 2=player2)
            - lastMove: (i, j) move last played or None
            - winningTiles: List of winning tiles
            - times: Dictionary with server time and player remaining times
            - clockPly: Current ply number for timing purposes
            - currentPlayer: Index of current player (0 or 1)
            - finished: Boolean indicating if game is over
            - winner: Winner index (0, 1) or None if game not finished
    """
    return {
        "gid": game.gid,
        "players": game.players,
        "board": game.board.position,
        "lastMove": game.last_move(),
        "moveList": game.moves,
        "winningTiles": game.winningTiles,
        "times": game.timer.get_times(),
        "clockPly": game.timer.get_ply(),
        "currentPlayer": game.board.current_player,
        "finished": game.finished,
        "winner": game.winner,
    }



@app.post("/tactics")
def api_tactics(req: dict):
    black, white = b2b(req["board"])

    if req["currentPlayer"] == 0:
        bb_current = np.uint64(black)
        bb_opponent = np.uint64(white)
    else:
        bb_current = np.uint64(white)
        bb_opponent = np.uint64(black)

    forced = get_forced_moves(bb_current, bb_opponent)
    moves = bb2m(forced)
    tactical_data = []
    for i in range(8):
        row = []
        for _ in range(8):
            row.append(False)
        tactical_data.append(row)

    for move in moves:
        i, j = move
        tactical_data[i][j] = True

    return tactical_data
