import math

def calculate_elo_change(rating_a, rating_b, score_a, k=32):
    """
    1 for win, 0.5 for draw, 0 for loss
    """
    expected_a = 1 / (1 + math.pow(10, (rating_b - rating_a) / 400))
    return round(k * (score_a - expected_a))

def update_elo(rating_a, rating_b, result):
    """
    'win', 'loss', or 'draw'
    Returns (new_rating_a, new_rating_b)
    """
    score_map = {'win': 1, 'draw': 0.5, 'loss': 0}
    change = calculate_elo_change(rating_a, rating_b, score_map[result])
    
    return rating_a + change, rating_b - change
