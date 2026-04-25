class Player:
    def __init__(self, nickname, isBot: bool, move_fn):
        self.nickname = nickname
        self.isBot = isBot
        self.move_fn = move_fn
