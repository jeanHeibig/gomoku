from backend.game import Game
from backend.players.player import Player
from backend.clock.timer import Timer
from backend.players.human import human
from backend.players.bots.random_bot import random_bot
from backend.players.bots.take_win_in_one_bot import take_win_in_one_bot
from backend.players.bots.block_opponent_bot import block_opponent_bot

player1 = Player("Alice-human", "human", human)
player2 = Player("Bob-bot", "bot", random_bot)
player3 = Player("Charlie-bot", "bot", take_win_in_one_bot)
player4 = Player("Damian-bot", "bot", block_opponent_bot)

all_players = [player1, player2, player3, player4]

timer = Timer(60.0, 0.0)

start_position = None
# start_position = [
#     [0, 0, 0, 0, 0, 0, 0, 0],
#     [0, 0, 0, 0, 0, 0, 0, 0],
#     [0, 0, 0, 1, 2, 0, 0, 0],
#     [0, 0, 0, 1, 2, 0, 0, 0],
#     [0, 0, 0, 1, 2, 0, 0, 0],
#     [0, 0, 0, 1, 2, 0, 0, 0],
#     [0, 0, 0, 0, 0, 0, 0, 0],
#     [0, 0, 0, 0, 0, 0, 0, 0],
# ]

scores = {}
for i in range(1, 4):
    playerA = all_players[i]
    for j in range(1, 4):
        playerB = all_players[j]
        players = [playerA, playerB]
        print(f"Match {playerA.nickname} vs. {playerB.nickname}")
        s = 0
        for gid in range(1000):
            g = Game(f"test-gid-{i}-{j}-{gid}", players, timer, start_position)
            s += g.run()
            timer.restart()
        print(s)
        scores[(i, j)] = s

print(scores)
