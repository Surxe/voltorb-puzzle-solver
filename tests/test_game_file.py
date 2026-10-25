import pytest

from backend.game_file import parse_answer, parse_counts

def test_parse_counts():
    rows, cols = parse_counts("5,1\n4,1\n\n2,3\n6,1\n")
    assert rows == [(5, 1), (4, 1)]
    assert cols == [(2, 3), (6, 1)]

def test_parse_counts_needs_both_blocks():
    with pytest.raises(ValueError):
        parse_counts("5,1\n4,1\n")

def test_parse_answer():
    assert parse_answer("021\n103\n") == [[0, 2, 1], [1, 0, 3]]
