import pytest

from backend.board import board_factory, board_from_counts
from backend.constants import ALL, ONE, THREE, TWO, ZERO
from backend.errors import Contradiction

def test_rows_and_cols_share_cells():
    board = board_from_counts([(5, 1)] * 5, [(5, 1)] * 5)
    for i in range(5):
        for j in range(5):
            assert board.rows[i].core_cells[j] is board.cols[j].core_cells[i] is board.cell(i, j)

def test_set_cell_is_seen_by_its_column():
    board = board_from_counts([(5, 1)] * 5, [(5, 1)] * 5)
    board.set_cell(1, 3, [2])
    assert board.cols[3].core_cells[1].options == [2]
    assert board.cell(0, 0).options == ALL # cells don't share option lists

def test_factory_keeps_given_options(game1):
    _, _, answer = game1
    table = [[[value] for value in row] for row in answer]
    rows, cols = [(sum(r), r.count(0)) for r in answer], [(sum(c), c.count(0)) for c in zip(*answer)]
    board = board_factory([table[i] + [rows[i]] for i in range(5)] + [cols + [None]])
    assert [[cell.options for cell in row.core_cells] for row in board.rows] == table
    assert board.update() == 1 # already solved: one pass, nothing changes

def test_update_reaches_a_fixpoint(game1):
    rows, cols, answer = game1
    board = board_from_counts(rows, cols)
    assert board.update() >= 2
    assert board.update() == 1
    for i, j, cell in board.cells():
        assert answer[i][j] in cell.options
    # column 4 is (5, 0): five 1's; column 2 is (8, 0): no voltorbs
    assert all(board.cell(i, 4).options == ONE for i in range(5))
    assert all(0 not in board.cell(i, 2).options for i in range(5))

def test_update_propagates_between_rows_and_cols():
    # what one line settles feeds the lines crossing it, so this takes several passes
    board = board_from_counts(
        [(5, 0), (3, 3), (5, 1), (6, 0), (5, 2)],
        [(2, 3), (6, 0), (4, 2), (7, 1), (5, 0)],
    )
    assert board.update() == 4
    assert [[cell.options for cell in row.core_cells] for row in board.rows] == [
        [[1], [1], [1], [1], [1]],
        [[0], [2], [0], [0], [1]],
        [[0], [1], [1, 2], [1, 2], [1]],
        [[1], [1], [1, 2], [1, 2], [1]],
        [[0], [1], [0], [3], [1]],
    ]

def test_str_layout():
    board = board_factory([
        [ZERO, TWO, (2, 1)],
        [ONE, THREE, (4, 0)],
        [(1, 1), (5, 0), None],
    ])
    assert str(board) == "Board:\n0    2    2,1 \n1    3    4,0 \n1,1  5,0  \n"

def test_contradicting_counters():
    board = board_from_counts([(16, 0)] + [(5, 1)] * 4, [(5, 1)] * 5)
    with pytest.raises(Contradiction):
        board.update()

def test_counter_lengths_must_match():
    with pytest.raises(ValueError):
        board_from_counts([(5, 1)] * 5, [(5, 1)] * 4)
