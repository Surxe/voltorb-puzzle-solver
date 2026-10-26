import random

import pytest

from backend.analysis import analyze
from backend.board import board_from_counts
from backend.constants import VOLTORB
from backend.game import Game, Status
from backend.levels import LEVELS, counts_of, deal
from backend.simulate import play
from backend.strategy import Recommendation, SafeFirst, candidates

def test_safe_batch_is_every_certainly_safe_card_that_could_multiply(game1):
    rows, cols, _ = game1
    game = Game.from_counts(rows, cols)
    recommendation = game.recommend()
    assert recommendation.safe and recommendation.risk == 0
    for i, j, cell in game.current_board.cells():
        expected = cell.is_safe() and cell.could_multiply() and not cell.revealed
        assert ((i, j) in recommendation.flips) is expected

def test_certain_ones_are_never_flipped(game1):
    rows, cols, _ = game1
    game = Game.from_counts(rows, cols)
    flips = game.recommend().flips
    assert all(game.current_board.cell(i, 4).options == [1] for i in range(5))
    assert not any(j == 4 for _, j in flips)

def test_guesses_the_card_least_likely_to_be_a_voltorb():
    # every open card might be a voltorb, so the solver has to guess
    answer = [[1, 0, 2], [0, 3, 1], [2, 1, 0]]
    game = Game.from_counts(*counts_of(answer), levels=None)
    recommendation = game.recommend()
    assert recommendation.safe is False and len(recommendation.flips) == 1
    risks = {position: game.likely.cell(*position).probability(VOLTORB) for position in candidates(game.current_board)}
    assert recommendation.risk == min(risks.values()) == risks[recommendation.flips[0]]

def test_strategy_with_nothing_left_to_flip():
    board = board_from_counts([(3, 0)] * 3, [(3, 0)] * 3)
    board.update()
    odds = analyze(board)
    assert SafeFirst().recommend(board, odds, odds) == Recommendation()

def test_revealing_a_voltorb_loses(game1):
    rows, cols, _ = game1
    game = Game.from_counts(rows, cols)
    game.reveal(0, 0, VOLTORB)
    assert game.status is Status.LOST
    assert game.recommend() == Recommendation()
    assert game.coins == 0

def test_coins_are_the_product_of_flipped_cards(game1):
    rows, cols, _ = game1
    game = Game.from_counts(rows, cols)
    assert game.coins == 0
    game.reveal(0, 1, 2)
    game.reveal(4, 2, 3)
    game.reveal(0, 4, 1)
    assert game.coins == 6

def test_from_state_matches_reveals(game1):
    rows, cols, answer = game1
    revealed = [[None] * 5 for _ in range(5)]
    revealed[0][2], revealed[4][2] = answer[0][2], answer[4][2]
    resumed = Game.from_state(rows, cols, revealed)
    played = Game.from_counts(rows, cols)
    played.reveal(0, 2, answer[0][2])
    played.reveal(4, 2, answer[4][2])
    assert resumed.recommend() == played.recommend()
    assert resumed.snapshot() == played.snapshot()

def test_snapshot_shape(game1):
    rows, cols, _ = game1
    game = Game.from_counts(rows, cols)
    game.recommend()
    snapshot = game.snapshot()
    assert snapshot['status'] == 'playing' and snapshot['coins'] == 0 and snapshot['boards'] > 1
    cell = snapshot['cells'][0][4]
    assert cell == {'options': [1], 'revealed': False, 'voltorb': 0.0, 'multiplier': 0.0}

def test_level_tables_only_change_guesses():
    """Certainties come from every matching board, so the level tables can't make a voltorb look safe"""
    rng = random.Random(3)
    for level in LEVELS:
        answer = deal(rng.choice(level), rng)
        with_levels = Game.from_counts(*counts_of(answer))
        without = Game.from_counts(*counts_of(answer), levels=None)
        first, second = with_levels.recommend(), without.recommend()
        assert first.safe == second.safe
        if first.safe:
            assert first.flips == second.flips
        assert with_levels.snapshot()['cells'][0][0]['options'] == without.snapshot()['cells'][0][0]['options']

@pytest.mark.parametrize('level', range(1, len(LEVELS) + 1))
def test_simulated_games(level):
    """
    Plays random boards of each level: a 'safe' flip is never a voltorb, a win means every 2 and 3 was flipped,
    and a loss only ever comes from a guess
    """
    rng = random.Random(level)
    for _ in range(12):
        answer = deal(rng.choice(LEVELS[level - 1]), rng)
        game = Game.from_counts(*counts_of(answer))
        playthrough = play(game, answer)
        for recommendation in playthrough.iterations:
            if recommendation.safe:
                assert all(answer[i][j] != VOLTORB for i, j in recommendation.flips)
        if playthrough.status is Status.WON:
            assert all(game.current_board.cell(i, j).revealed for i in range(5) for j in range(5) if answer[i][j] > 1)
        else:
            assert playthrough.status is Status.LOST
            assert not playthrough.iterations[-1].safe
