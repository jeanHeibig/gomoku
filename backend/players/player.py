class Player:
    def __init__(self, nickname, player_type: str, move_fn):
        self.nickname = nickname
        self.player_type = player_type  # TODO: change to is_bot bool
        self.move_fn = move_fn
