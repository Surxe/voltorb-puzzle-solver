from pathlib import Path

import pytest

from backend.game_file import load_answer, load_counts

REPO = Path(__file__).resolve().parent.parent

@pytest.fixture
def game1():
    """The game in progress when the solver was written: its counters and the board it turned out to be"""
    rows, cols = load_counts(REPO / 'input' / 'game1.txt')
    return rows, cols, load_answer(REPO / 'input' / 'game1_answer.txt')
