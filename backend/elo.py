def update_elo(R: float, R_opponent: float, score: float, K=32) -> float:
    """Update the Elo rating based on game outcome.

    Args:
        R (float): Current Elo rating of the player.
        R_opponent (float): Elo rating of the opponent.
        score (float): Game score (1 for win, 0.5 for draw, 0 for loss).
        K (int, optional): K-factor for rating update. Defaults to 32.

    Returns:
        float: Updated Elo rating.
    """
    expected = 1 / (1 + 10 ** ((R_opponent - R) / 400))
    return R + K * (score - expected)
