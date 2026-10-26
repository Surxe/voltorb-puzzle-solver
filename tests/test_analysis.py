import random
from collections import defaultdict
from itertools import product
from itertools import combinations
from math import comb, isclose

import pytest

from backend.analysis import analyze
from backend.board import board_from_counts
from backend.constants import VOLTORB
from backend.errors import Contradiction
from backend.levels import (
    LEVELS, TRACKED, BoardConfig, FreeCount, count_free, counts_of, deal, free_cells, free_multipliers, level_weights,
    too_generous, valid_deals,
)

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
            answer = deal(config, rng)
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

def multinomial(config, size=5):
    cells = size * size
    return comb(cells, config.voltorbs) * comb(cells - config.voltorbs, config.twos) * comb(cells - config.voltorbs - config.twos, config.threes)

def test_valid_deals_without_limits_counts_every_board():
    assert valid_deals(BoardConfig(6, 3, 1)) == multinomial(BoardConfig(6, 3, 1))
    assert valid_deals(BoardConfig(13, 9, 1)) == multinomial(BoardConfig(13, 9, 1))
    assert valid_deals(BoardConfig(0, 0, 0), size=2) == 1

@pytest.mark.parametrize('config', [BoardConfig(2, 2, 1, 2, 3), BoardConfig(1, 3, 0, 2, 2), BoardConfig(3, 1, 2, 1, 2)])
def test_valid_deals_match_brute_force(config):
    """Every placement on a 3x3 board, kept unless the game would re-deal it"""
    size, cells = 3, range(9)
    kept = 0
    for voltorbs in combinations(cells, config.voltorbs):
        rest = [c for c in cells if c not in voltorbs]
        for twos in combinations(rest, config.twos):
            for threes in combinations([c for c in rest if c not in twos], config.threes):
                flat = [VOLTORB if c in voltorbs else 2 if c in twos else 3 if c in threes else 1 for c in cells]
                grid = [flat[i * size:(i + 1) * size] for i in range(size)]
                rows, cols = counts_of(grid)
                free = free_cells([v for _, v in rows], [v for _, v in cols])
                kept += not too_generous(config, count_free({(i, j): grid[i][j] for i, j in free}, size))
    assert valid_deals(config, size) == kept

def test_dealt_boards_follow_the_rules():
    rng = random.Random(4)
    for config in LEVELS[0][:5] + LEVELS[7][:5]:
        for _ in range(50):
            answer = deal(config, rng)
            flat = [value for row in answer for value in row]
            assert (flat.count(VOLTORB), flat.count(2), flat.count(3)) == (config.voltorbs, config.twos, config.threes)
            rows, cols = counts_of(answer)
            free = free_cells([v for _, v in rows], [v for _, v in cols])
            assert not too_generous(config, count_free({(i, j): answer[i][j] for i, j in free}, 5))

def test_level_weights_favor_configs_with_fewer_valid_deals():
    weights = level_weights(6) # Lv. 1 is the only level with 6 voltorbs
    assert set(weights) == {(3, 1), (0, 3), (5, 0), (2, 2), (4, 1)}
    # one specific board is likelier from a config that can be dealt fewer ways
    three_one, five_zero = LEVELS[0][0], LEVELS[0][2]
    assert isclose(weights[(5, 0)] / weights[(3, 1)], valid_deals(three_one) / valid_deals(five_zero))
    assert level_weights(9) == {}

def test_level_weights_rule_out_configs_that_would_re_deal():
    # 3 free multipliers: Lv. 1 configs capped at 3 in all would have re-dealt this board
    free = FreeCount(per_row=(2, 1, 0, 0, 0), per_col=(1, 1, 1, 0, 0))
    assert set(level_weights(6, free=free)) == {(5, 0), (4, 1)}
    # 2 in one row: (0, 3) is capped at 2 per line
    free = FreeCount(per_row=(2, 0, 0, 0, 0), per_col=(1, 1, 0, 0, 0))
    assert (0, 3) not in level_weights(6, free=free)

def test_level_weights_by_level():
    assert set(level_weights(10, levels=[LEVELS[7]])) == {(0, 7), (8, 2), (5, 4), (2, 6), (7, 3)}
    assert level_weights(6, levels=[LEVELS[7]]) == {}

def test_free_multipliers_wait_for_every_free_card(game1):
    rows, cols, answer = game1 # columns 2 and 4 have no voltorbs
    board = board_from_counts(rows, cols)
    board.update()
    assert free_multipliers(board) is None # column 2 is still open
    for i in range(5):
        board.reveal(i, 2, answer[i][2])
    free = free_multipliers(board)
    assert free.per_col == (0, 0, 2, 0, 0) and free.per_row == (0, 0, 1, 0, 1) and free.total == 2
