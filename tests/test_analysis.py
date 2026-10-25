import random
from collections import defaultdict
from itertools import product
from math import comb, isclose

import pytest

from backend.analysis import analyze
from backend.board import board_from_counts
from backend.constants import VOLTORB
from backend.errors import Contradiction
from backend.levels import LEVELS, TRACKED, BoardConfig, counts_of, deals, level_weights, random_answer

def small_board(rng, size=3, reveal=0.3):
    """A random size x size board with values 0-3 and some cells already flipped"""
    answer = [[rng.randint(0, 3) for _ in range(size)] for _ in range(size)]
    board = board_from_counts(*counts_of(answer))
    for i, j, _ in board.cells():
        if rng.random() < reveal:
            board.reveal(i, j, answer[i][j])
    return board, answer

def brute_force(board, weigh=lambda grid: 1):
    """Weight per cell per option, over every grid whose rows and columns match their counters"""
    total = 0
    weights = defaultdict(float)
    for grid in product(*(row.arrangements() for row in board.rows)):
        if all(
            sum(column) == col.cell_set_counter.value and column.count(VOLTORB) == col.cell_set_counter.voltorbs
            for column, col in zip(zip(*grid), board.cols)
        ):
            weight = weigh(grid)
            total += weight
            for i, row in enumerate(grid):
                for j, option in enumerate(row):
                    weights[(i, j, option)] += weight
    return total, weights

@pytest.mark.parametrize('seed', range(25))
def test_counts_match_brute_force(seed):
    board, answer = small_board(random.Random(seed))
    odds = analyze(board)
    total, weights = brute_force(board)
    assert odds.total == total
    for i, j, cell in board.cells():
        assert odds.cell(i, j).weights == {o: w for (a, b, o), w in weights.items() if (a, b) == (i, j) and w}
        assert answer[i][j] in odds.cell(i, j).options

@pytest.mark.parametrize('seed', range(10))
def test_weights_match_brute_force(seed):
    rng = random.Random(seed)
    board, _ = small_board(rng)
    # a random weight per (# of 2's, # of 3's), leaving some tallies out (weight 0)
    tallies = {(twos, threes): rng.random() for twos in range(10) for threes in range(10) if rng.random() < 0.7}
    def weigh(grid):
        return tallies.get(tuple(sum(row.count(o) for row in grid) for o in TRACKED), 0)
    total, weights = brute_force(board, weigh)
    if not total:
        with pytest.raises(Contradiction):
            analyze(board, TRACKED, tallies)
        return
    odds = analyze(board, TRACKED, tallies)
    assert isclose(odds.total, total)
    for i, j, _ in board.cells():
        for option in range(4):
            assert isclose(odds.cell(i, j).weights.get(option, 0), weights.get((i, j, option), 0), abs_tol=1e-12)

def test_weights_that_rule_out_every_board_raise():
    board = board_from_counts([(3, 0)] * 3, [(3, 0)] * 3) # all 1's: no 2's or 3's
    with pytest.raises(Contradiction):
        analyze(board, TRACKED, {(1, 0): 1.0})

def test_contradiction():
    board = board_from_counts([(3, 0), (3, 0), (3, 0)], [(3, 0), (3, 0), (2, 1)])
    with pytest.raises(Contradiction):
        analyze(board)

def test_answer_always_fits_on_real_boards():
    rng = random.Random(1)
    for level in LEVELS:
        for config in level:
            answer = random_answer(config, rng)
            board = board_from_counts(*counts_of(answer))
            board.update()
            certain = analyze(board)
            likely = analyze(board, TRACKED, level_weights(config.voltorbs))
            for i, j, _ in board.cells():
                assert answer[i][j] in certain.cell(i, j).options
                assert answer[i][j] in likely.cell(i, j).options

def test_narrow_keeps_only_used_options(game1):
    rows, cols, answer = game1
    board = board_from_counts(rows, cols)
    board.update()
    lines_only = [[cell.options for cell in row.core_cells] for row in board.rows]
    odds = analyze(board)
    odds.narrow(board)
    for i, j, cell in board.cells():
        assert set(cell.options) <= set(lines_only[i][j])
        assert answer[i][j] in cell.options
    assert odds.narrow(board) is False

def test_probabilities_sum_to_one(game1):
    rows, cols, _ = game1
    odds = analyze(board_from_counts(rows, cols))
    for row in odds.cells:
        for cell in row:
            assert isclose(cell.probability(0, 1, 2, 3), 1)

def test_deals_counts_boards():
    config = BoardConfig(twos=3, threes=1, voltorbs=6)
    assert deals(config) == comb(25, 6) * comb(19, 3) * comb(16, 1)
    assert deals(BoardConfig(0, 0, 0), size=2) == 1

def test_level_weights_favor_configs_with_fewer_deals():
    weights = level_weights(6) # Lv. 1 is the only level with 6 voltorbs
    assert set(weights) == {(3, 1), (0, 3), (5, 0), (2, 2), (4, 1)}
    # one specific (5, 0) board is 4/3 as likely as one (3, 1) board: fewer ways to deal 5 twos and no threes
    assert isclose(weights[(5, 0)] / weights[(3, 1)], deals(BoardConfig(3, 1, 6)) / deals(BoardConfig(5, 0, 6)))
    assert isclose(weights[(5, 0)] / weights[(3, 1)], 4 / 3)
    assert level_weights(9) == {}

def test_level_weights_by_level():
    assert set(level_weights(10, levels=[LEVELS[7]])) == {(0, 7), (8, 2), (5, 4), (2, 6), (7, 3)}
    assert level_weights(6, levels=[LEVELS[7]]) == {}
