from typing import List

from cell import Cell
from cell_set import CellSet
from cell_set_counter import CellSetCounter
from board import Board, board_factory

from constants import *

    
def init_state():
    table_of_options = [
        [ALL,    ALL,     ALL,     ALL, ONE],
        [ALL,    ALL,     ALL,     ALL, ONE],
        [ALL,    ALL,     ALL,     ALL, ONE],
        [ALL,    ALL,     ALL,     ALL, ONE],
        [ONE,    TWO,     ONE,   THREE, ONE],
    ]
    row_totals = [ #top to bottom
        (3, 2),
        (6, 1),
        (4, 1),
        (3, 2),
        (8, 0)
    ]
    col_totals = [ #left to right
        (4, 2),
        (5, 1),
        (4, 2),
        (6, 1),
        (5, 0)
    ]
    row_cell_sets, col_cell_sets = board_factory(table_of_options, row_totals, col_totals)
    return Board(row_cell_sets, col_cell_sets)


if __name__ == '__main__':
    board = init_state()
    print(board)
