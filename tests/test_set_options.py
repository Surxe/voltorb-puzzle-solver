"""v value across c cells with z voltorbs, when the cells are limited to set_options"""
from itertools import combinations, product

import pytest

from backend.cell_set import process_new_options, process_options_to_remove
from backend.constants import ALL, VOLTORB

def brute_force(v, c, z, set_options):
    arrangements = [a for a in product(set_options, repeat=c) if sum(a) == v and a.count(VOLTORB) == z]
    if not arrangements:
        return None
    return sorted({option for arrangement in arrangements for option in arrangement})

@pytest.mark.parametrize(('v', 'c', 'z', 'set_options', 'expected'), [
    # a 3 and a 1, or a 2 and a 2: without 3's only 2 and 2 is left
    (4, 2, 0, [0, 1, 2], [2]),
    (4, 2, 0, [0, 1, 2, 3], [1, 2, 3]),
    # two 2's somewhere, but 2+2+1+1 can be arranged any way
    (6, 4, 0, [0, 1, 2], [1, 2]),
    (6, 3, 0, [0, 1, 2], [2]),
    (5, 3, 0, [0, 1, 2], [1, 2]),
    (3, 1, 0, [0, 1, 2], None),
    (7, 3, 0, [0, 1, 2], None),
    # scratch.txt: (6, 5, 1, [0,1,2]) -> (6, 4, 0, [0,1,2]) -> at least two 2's, still any of 0/1/2 per cell
    (6, 5, 1, [0, 1, 2], [0, 1, 2]),
    (6, 4, 0, [0, 1, 2], [1, 2]),
    (3, 3, 0, [1], [1]),
    (3, 2, 0, [1], None),
    (2, 3, 1, [0, 1], [0, 1]),
    (3, 2, 1, [1, 2, 3], None), # a voltorb that can't be placed
    (6, 3, 1, [0, 3], [0, 3]),
    (5, 2, 0, [0, 2, 3], [2, 3]),
    (9, 3, 0, [1, 2, 3], [3]),
    (0, 2, 2, [0, 1, 2, 3], [0]),
    (0, 2, 0, [0, 1, 2, 3], None), # two non-voltorbs hold at least 2
    (0, 0, 0, [0, 1, 2, 3], []), # nothing left to place
])
def test_limited_set_options(v, c, z, set_options, expected):
    assert process_new_options(v, c, z, set_options) == expected

@pytest.mark.parametrize(('v', 'c', 'z', 'set_options', 'removed'), [
    (4, 2, 0, [0, 1, 2], [0, 1]),
    (6, 4, 0, [0, 1, 2], [0]),
    (3, 2, 0, [1], [1]), # impossible, so nothing remains
    (3, 3, 1, [0, 1, 2, 3], [3]),
])
def test_options_to_remove(v, c, z, set_options, removed):
    assert process_options_to_remove(v, c, z, set_options) == removed

SUBSETS = [list(subset) for size in range(1, len(ALL) + 1) for subset in combinations(ALL, size)]

@pytest.mark.parametrize('set_options', SUBSETS, ids=[''.join(map(str, s)) for s in SUBSETS])
def test_matches_brute_force(set_options):
    for c in range(0, 6):
        for z in range(0, c + 1):
            for v in range(0, 3 * c + 2):
                assert process_new_options(v, c, z, set_options) == brute_force(v, c, z, set_options), (v, c, z)
