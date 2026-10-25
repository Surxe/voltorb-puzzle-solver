from src.cell import Cell
from src.cell_set import CellSet
from src.cell_set_counter import CellSetCounter

class Board:
    def __init__(self, _row_cell_sets: list[CellSet], _col_cell_sets: list[CellSet]):
        self.rows = _row_cell_sets
        self.cols = _col_cell_sets
        self.size = len(_row_cell_sets)

    def __str__(self):
        string = ""
        # core 5x5 table + row total
        for row in self.rows:
            string += str(row) + '\n'
        for col in self.cols:
            string += str(col.cell_set_counter) + ' '
        return string

def board_factory(table: list) -> Board:
    size = len(table)
    row_cell_sets = []
    col_cell_sets = []

    # create rows first
    for i in range(size-1):
        core_rows = []
        for j in range(size-1):
            core_rows.append(Cell(table[i][j]))
        row_cell_sets.append(CellSet(core_rows, CellSetCounter(table[i][j+1][0], table[i][j+1][1])))

    # create cols next
    for i in range(size-1):
        core_cols = []
        for j in range(size-1):
            core_cols.append(Cell(table[j][i]))
        col_cell_sets.append(
            CellSet(core_cols[j], 
                CellSetCounter(
                    table[j+1][i][0], 
                    table[j+1][i][1]
                    )
            )
        )
        
    return Board(row_cell_sets, col_cell_sets)