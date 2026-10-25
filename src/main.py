# Run from repo root, not source
import sys
sys.path.append(".")

from typing import List
import os

from src.cell import Cell
from src.cell_set import CellSet
from src.cell_set_counter import CellSetCounter
from src.board import Board, board_factory
from src.constants import *
from src.utils import log
    
def init_state() -> Board:
    return board_factory([
        [ALL,    ALL,    ALL,    ALL,    ONE,    (3, 2)],
        [ALL,    ALL,    ALL,    ALL,    ONE,    (6, 1)],
        [ALL,    ALL,    ALL,    ALL,    ONE,    (4, 2)],
        [ALL,    ALL,    ALL,    ALL,    ONE,    (3, 2)],
        [ONE,    TWO,    ONE,    THREE,  ONE,    (8, 0)],
        [(4, 2), (5, 1), (4, 2), (6, 1), (5, 0), None]
    ])

if __name__ == '__main__':
    board = init_state()
    board_str = str(board)
    print(board_str)
    path = os.path.join(OUTPUT_DIR, 'board_state.txt')
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(encoding='utf-8', mode='w', file=path) as f:
        f.write(board_str)

    

    row_cell_set0 = board.rows[0]
    col_cell_set0 = board.cols[0]

    log(f"row_cell_set0 before: {row_cell_set0}", do_log=True)
    log(f"col_cell_set0 before: {col_cell_set0}", do_log=True)

    row_cell_set0.update()

    log(f"row_cell_set0 after : {row_cell_set0}", do_log=True)
    #this should have its first cell updated by rows[0] being updated because it overlaps
    log(f"col_cell_set0 after : {col_cell_set0}", do_log=True)

    # row_cell_set0.update()
    # log(f"row_cell_set0 after : {row_cell_set0}", do_log=True)
