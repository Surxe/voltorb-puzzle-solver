import sys
sys.path.append(".")

from src.cell import Cell
from src.cell_set import CellSet
from src.cell_set_counter import CellSetCounter
from src.constants import GRID_SIZE
from src.utils import log

class Board:
    def __init__(self, _row_cell_sets: list[CellSet], _col_cell_sets: list[CellSet]):
        self.rows = _row_cell_sets
        self.cols = _col_cell_sets
        self.size = len(_row_cell_sets)

    def __str__(self):
        contents = ""
        # core 5x5 table + row total
        for row in self.rows:
            contents += str(row) + '\n'
        for col in self.cols:
            contents += str(col.cell_set_counter) + ' '

        return f"Board:\n{contents}\n"

    def set_cell(self, i, j, new_options):
        self.rows[i].core_cells[j].set(new_options)
        self.cols[j].core_cells[i].set(new_options)

    def update(self, do_log=True):
        # Update each Cell
        log("rows update()", do_log=do_log)
        for i, row in enumerate(self.rows):
            log(f"row {i}", do_log=True)
            row.update()
        log(self, do_log=do_log)

        log("cols update()", do_log=do_log)
        for j, col in enumerate(self.cols):
            log(f"col {j}", do_log=True)
            col.update()
        log(self, do_log=do_log)
                    


def add_cell_to_set(existing_cells_table, existing_core_cells, input_table, i, j):
    # if the cell already exists, use it
    existing_cell = existing_cells_table[i][j]
    if existing_cell is not None:
        the_cell = existing_cell
    # else make one
    else:
        the_cell = Cell(input_table[i][j])
        # and register it
        existing_cells_table[i][j] = the_cell

    # add Cell to row
    existing_core_cells.append(the_cell)
    return existing_core_cells

def cell_set_factory(row_cell_sets, core_rows, input_table, i, j) -> list[CellSet]:
    row_cell_sets.append(
        CellSet(core_rows, 
            CellSetCounter(
                input_table[i][j][0], 
                input_table[i][j][1]
            )
        )
    )
    return row_cell_sets

def board_factory(table: list) -> Board:
    size = len(table)
    row_cell_sets = []
    col_cell_sets = []
    cells_table = [[None for x in range(GRID_SIZE)] for y in range(GRID_SIZE)] # only used during processing so when a row and cell intercept they share the Cell instead of having separate copies

    # create rows first
    for i in range(size-1):
        core_rows = []
        for j in range(size-1):
            add_cell_to_set(cells_table, core_rows, table, i, j)
        row_cell_sets = cell_set_factory(row_cell_sets, core_rows, table, i, j+1)

    # create cols next
    for i in range(size-1):
        core_cols = []
        for j in range(size-1):
            add_cell_to_set(cells_table, core_cols, table, j, i)
        col_cell_sets = cell_set_factory(col_cell_sets, core_cols, table, j+1, i)
        
    return Board(row_cell_sets, col_cell_sets)