# Run from repo root, not source
import sys
sys.path.append(".")

from typing import List
import os

from src.cell import Cell
from src.cell_set import CellSet, cache_to_disk
from src.cell_set_counter import CellSetCounter
from src.board import Board, board_factory
from src.game import Game
from src.constants import *
from src.utils import log
    
def init_game() -> Game:
    # initial_table_state = [
    #     [[0,1],   [0,1,2], ONE,     [0,1],    ONE,    (5, 1)],
    #     [[0,1],   [0,1],   ONE,     [0,1],    ONE,    (4, 1)],
    #     [[0,1],   ALL,     TWO,     [0,1],    ONE,    (5, 2)],
    #     [[0,1],   ALL,     ONE,     [0,1],    ONE,    (5, 2)],
    #     [[0,1],   ALL,     THREE,   [0,1],    ONE,    (5, 2)],
    #     [(2, 3),  (6, 1),  (8, 0),  (3, 2),   (5, 0), None]
    # ]
    current_board = board_factory([
        [ALL,    ALL,    ALL,    ALL,    ALL,    (5, 1)],
        [ALL,    ALL,    ALL,    ALL,    ALL,    (4, 1)],
        [ALL,    ALL,    ALL,    ALL,    ALL,    (5, 1)],
        [ALL,    ALL,    ALL,    ALL,    ALL,    (5, 1)],
        [ALL,    ALL,    ALL,    ALL,    ALL,    (5, 2)],
        [(2, 3), (6, 1), (8, 0), (3, 2), (5, 0), None]
    ])
    answer_board = board_factory([
        [ZERO,   TWO,    ONE,    ONE,    ONE,    (5, 1)],
        [ZERO,   ONE,    ONE,    ONE,    ONE,    (4, 1)],
        [ONE,    ZERO,   TWO,    ONE,    ONE,    (5, 1)],
        [ONE,    TWO,    ONE,    ZERO,   ONE,    (5, 1)],
        [ZERO,   ONE,    THREE,  ZERO,   ONE,    (5, 2)],
        [(2, 3), (6, 1), (8, 0), (3, 2), (5, 0), None]
    ])
    game = Game(current_board, answer_board)
    return game


if __name__ == '__main__':
    game = init_game()
    game_str = str(game)
    
    path = os.path.join(OUTPUT_DIR, 'board_state.txt')
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(encoding='utf-8', mode='w', file=path) as f:
        f.write(game_str)

    print(game)

    num_game_updates=0
    while True:
        print(f"game loop #{num_game_updates+1}")
        game.update()
        game.flip()
        print("flip()")
        print(game)

        num_game_updates += 1

        if num_game_updates==2:
            break

    cache_to_disk()

    # row_cell_set0 = board.rows[0]
    # col_cell_set0 = board.cols[0]

    # log(f"row_cell_set0 before: {row_cell_set0}", do_log=True)
    # log(f"col_cell_set0 before: {col_cell_set0}", do_log=True)

    # row_cell_set0.update()

    # log(f"row_cell_set0 after : {row_cell_set0}", do_log=True)
    # #this should have its first cell updated by rows[0] being updated because it overlaps
    # log(f"col_cell_set0 after : {col_cell_set0}", do_log=True)

    # row_cell_set0.update()
    # log(f"row_cell_set0 after : {row_cell_set0}", do_log=True)
