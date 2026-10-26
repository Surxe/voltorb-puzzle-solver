"""A row or column narrowing cells that each have their own options: the [2,2] or [3,1] -> [2,2] family"""
import random
from itertools import product

import pytest

from backend.cell import Cell
from backend.cell_set import CellSet, supported_options
from backend.cell_set_counter import CellSetCounter
from backend.constants import ALL, VOLTORB
from backend.errors import Contradiction

def cell_set(options, value, voltorbs):
    return CellSet([Cell(list(o)) for o in options], CellSetCounter(value, voltorbs))

def options_of(line):
    return [cell.options for cell in line.core_cells]

@pytest.mark.parametrize(('before', 'counter', 'after'), [
    # 4 across two cells that can't be 3: [3,1] is out, so [2,2]
    ([[0, 1, 2], [0, 1, 2]], (4, 0), [[2], [2]]),
    # with 3's allowed it could be [3,1], [2,2] or [1,3]
    ([[0, 1, 2, 3], [0, 1, 2, 3]], (4, 0), [[1, 2, 3], [1, 2, 3]]),
    # at least two 2's among four cells, but they can be any two
    ([[0, 1, 2]] * 4, (6, 0), [[1, 2]] * 4),
    # at least two 2's and only two cells can hold one: both are 2, the rest are 1
    ([[0, 1, 2], [0, 1, 2], [0, 1], [0, 1]], (6, 0), [[2], [2], [1], [1]]),
    # at least one 3 among 2 cells, the other being 1, 2 or 3
    ([[1, 2, 3], [1, 2, 3], [1]], (6, 0), [[2, 3], [2, 3], [1]]),
    ([[1, 2, 3]] * 3, (9, 0), [[3]] * 3),
    # scratch.txt: 6 value across 5 cells with 1 voltorb, 2's at most: nothing narrows
    ([[0, 1, 2]] * 5, (6, 1), [[0, 1, 2]] * 5),
    # solved cells count toward the counter: 4 value left over the 2 open cells
    ([[2], [0, 1, 2], [0, 1, 2], [0], [1]], (7, 1), [[2], [2], [2], [0], [1]]),
    # the voltorb is already found, so the open cells can't be one
    ([[0], [0, 1, 2, 3], [0, 1, 2, 3]], (3, 1), [[0], [1, 2], [1, 2]]),
    # every voltorb placed elsewhere: 0 leaves the cell's options
    ([[0, 1], [0, 1], [1, 2, 3]], (3, 2), [[0], [0], [3]]),
])
def test_update_narrows(before, counter, after):
    line = cell_set(before, *counter)
    assert line.update() is (before != after)
    assert options_of(line) == after

def test_update_is_idempotent():
    line = cell_set([[0, 1, 2], [0, 1, 2], [0, 1], [0, 1]], 6, 0)
    assert line.update() is True
    assert line.update() is False

@pytest.mark.parametrize(('options', 'counter'), [
    ([[1], [1]], (3, 0)),
    ([[0, 1, 2]] * 2, (5, 0)),
    ([[1, 2, 3]] * 2, (3, 1)),
])
def test_update_raises_when_nothing_fits(options, counter):
    with pytest.raises(Contradiction):
        cell_set(options, *counter).update()

def test_arrangements():
    line = cell_set([[0, 1, 2], [0, 1, 2], [1]], 3, 1)
    assert sorted(line.arrangements()) == [(0, 2, 1), (2, 0, 1)]

def test_current_options():
    assert cell_set([[0, 1], [2, 3], [1]], 0, 0).current_options() == [0, 1, 2, 3]

def test_supported_options_matches_brute_force():
    rng = random.Random(0)
    for _ in range(400):
        domains = [sorted(rng.sample(ALL, rng.randint(1, len(ALL)))) for _ in range(rng.randint(1, 5))]
        value, voltorbs = rng.randint(0, 3 * len(domains)), rng.randint(0, len(domains))
        arrangements = [a for a in product(*domains) if sum(a) == value and a.count(VOLTORB) == voltorbs]
        expected = [sorted({a[i] for a in arrangements}) for i in range(len(domains))] if arrangements else None
        assert supported_options(domains, value, voltorbs) == expected, (domains, value, voltorbs)
