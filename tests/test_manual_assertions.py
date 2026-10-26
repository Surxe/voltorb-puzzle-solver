"""The hand-worked v value / c cells / z voltorbs table, where every cell may be any option"""
from pathlib import Path

import pytest

from backend.cell_set import get_option_decision
from backend.constants import ALL

LINES = (Path(__file__).parent / 'manual_assertions.txt').read_text(encoding='utf-8').splitlines()
CASES = [(v, c, z) for v in range(1, 4) for c in range(1, 6) for z in range(0, c + 1)]

def test_every_case_has_an_assertion():
    assert len(LINES) == len(CASES)

@pytest.mark.parametrize(('case', 'expectation'), list(zip(CASES, LINES)), ids=[f'{v}-{c}-{z}' for v, c, z in CASES])
def test_manual_assertion(case, expectation):
    # for this test we essentially ignore limiting factors across the set
    assert get_option_decision(*case, ALL) == expectation.replace(',', ', ')
