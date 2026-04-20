import random

def random_bot(position, pendule):
    moves = [(i, j) for i in range(8) for j in range(8) if position[i][j]==0]
    return random.choice(moves)
