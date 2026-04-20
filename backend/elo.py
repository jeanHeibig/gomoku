def update_elo(R, R_opponent, score, K=32):
    expected = 1 / (1 + 10 ** ((R_opponent - R) / 400))
    return R + K * (score - expected)
