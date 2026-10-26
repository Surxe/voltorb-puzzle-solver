import pytest

# The game in progress when the solver was written: its counters and the board it turned out to be
GAME1_ROWS = [(5, 1), (4, 1), (5, 1), (5, 1), (5, 2)]
GAME1_COLS = [(2, 3), (6, 1), (8, 0), (3, 2), (5, 0)]
GAME1_ANSWER = [
    [0, 2, 1, 1, 1],
    [0, 1, 1, 1, 1],
    [1, 0, 2, 1, 1],
    [1, 2, 1, 0, 1],
    [0, 1, 3, 0, 1],
]

@pytest.fixture
def game1():
    return GAME1_ROWS, GAME1_COLS, GAME1_ANSWER
