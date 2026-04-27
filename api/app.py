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
import time

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.clock import Timer
from backend.game import Game
from backend.players import human, online_bot, Player

app = FastAPI()

games = {}
player1 = Player("Alice", False, human)
player2 = Player("Bob", True, online_bot)


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
def new_game():
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

    human_starts = random.randint(0, 1)
    if human_starts:  # random choice for the side
        players = [player1, player2]
    else:
        players = [player2, player1]

    timer = Timer(900.0, 15.0)
    game = Game(gid, players, timer)

    if not human_starts:  # if bot starts
        game.move()

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
        r = 0.1 + 1 * random.random()
        time.sleep(r)
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
        "winningTiles": game.winningTiles,
        "times": game.timer.get_times(),
        "clockPly": game.timer.get_ply(),
        "currentPlayer": game.board.current_player,
        "finished": game.finished,
        "winner": game.winner,
    }
