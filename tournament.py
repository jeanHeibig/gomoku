from backend import Timer, Game, Player
from backend.players import human
from backend.players.bots import random_bot, take_win_in_one_bot, block_opponent_bot, double_threats_bot, prevent_double_threats_bot, ab_bot

player1 = Player("Alice-human", False, human)
player2 = Player("Bob-bot", True, random_bot)
player3 = Player("Charlie-bot", True, take_win_in_one_bot)
player4 = Player("Damian-bot", True, block_opponent_bot)
player5 = Player("Edgar-bot", True, double_threats_bot)
player6 = Player("Ferdinand-bot", True, prevent_double_threats_bot)
player7 = Player("Gaston-bot", True, ab_bot)
player8 = Player("Harry-bot", True, ...)

all_players = [player1, player2, player3, player4, player5, player6, player7, player8]

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
for i in range(6, 7):
    playerA = all_players[i]
    for j in range(6, 7):
        playerB = all_players[j]
        players = [playerA, playerB]
        print(f"Match {playerA.nickname} vs. {playerB.nickname}")
        score = 0
        for gid in range(4):
            timer = Timer(60.0, 2.0)
            g = Game(f"test-gid-{i}-{j}-{gid}", players, timer, start_position)
            score += g.run(verbose=True)
            print(f"Match {gid}: {score}")
        print(score)
        scores[(i, j)] = score

print(scores)
