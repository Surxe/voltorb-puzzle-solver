# Run from repo root, not source

from typing import List
import os

from cell import Cell
from cell_set import CellSet
from cell_set_counter import CellSetCounter
from board import Board, board_factory
from constants import *
    
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
    print(board)
    path = os.path.join(OUTPUT_DIR, 'board_state.txt')
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(encoding='utf-8', mode='w', file=path) as f:
        f.write(str(board))
