"""
Why the solver sometimes has to guess: the counters can't always tell two boards apart.

These two Lv. 1 boards differ only in a rectangle of 0's and 2's, which leaves every row and column counter
the same. Every other card matches, so flipping them can't tell the boards apart. To win you must flip the
2's in that rectangle, and each of its four cards is a Voltorb in one of the two boards.
"""
from backend.constants import VOLTORB
from backend.game import Game
from backend.levels import counts_of
from backend.strategy import candidates

BOARD_A = [
    [1, 1, 0, 1, 2],
    [1, 1, 2, 2, 0],
    [1, 1, 1, 1, 1],
    [1, 1, 0, 0, 0],
    [3, 2, 1, 1, 0],
]
BOARD_B = [
    [1, 1, 2, 1, 0],
    [1, 1, 0, 2, 2],
    [1, 1, 1, 1, 1],
    [1, 1, 0, 0, 0],
    [3, 2, 1, 1, 0],
]
RECTANGLE = {(0, 2), (0, 4), (1, 2), (1, 4)}

def test_both_boards_show_the_same_counters():
    assert counts_of(BOARD_A) == counts_of(BOARD_B)
    differ = {(i, j) for i in range(5) for j in range(5) if BOARD_A[i][j] != BOARD_B[i][j]}
    assert differ == RECTANGLE
    for i, j in RECTANGLE:
        assert {BOARD_A[i][j], BOARD_B[i][j]} == {VOLTORB, 2}

def play_safe_flips(answer):
    """Flips every card the solver is sure of, until it has to guess"""
    game = Game.from_counts(*counts_of(answer))
    while (recommendation := game.recommend()).safe and recommendation.flips:
        for i, j in recommendation.flips:
            game.reveal(i, j, answer[i][j])
    return game, recommendation

def test_safe_flips_end_in_a_coin_toss():
    for answer in (BOARD_A, BOARD_B):
        game, recommendation = play_safe_flips(answer)
        assert game.certain.total == 2 # exactly these two boards still fit
        assert set(candidates(game.current_board)) == RECTANGLE
        for i, j in RECTANGLE:
            assert game.certain.cell(i, j).probability(VOLTORB) == 0.5
        assert recommendation.safe is False and recommendation.risk == 0.5
        assert recommendation.flips[0] in RECTANGLE
