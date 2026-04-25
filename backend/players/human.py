def human(*args):
    move = input("Move: ")
    i, j = [int(x) for x in move.split(',')]
    return i, j
