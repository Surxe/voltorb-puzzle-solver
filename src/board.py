from cell import Cell
from cell_set import CellSet
from cell_set_counter import CellSetCounter

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

def board_factory(table_of_options: list, row_totals: list[tuple], col_totals: list[tuple]) -> tuple[list[CellSet], list[CellSet]]:
    # table_of_options: [[options, options, .. options]]
    # row_totals: [(value, voltorb)]
    # col_totals: [(value, voltorb)]
    # -> (row_cell_sets, col_cell_sets)
    size = len(table_of_options)
    row_cell_sets = []
    col_cell_sets = []

    # create rows first
    for i in range(size):
        core_rows = []
        for j in range(size):
            core_rows.append(Cell(table_of_options[i][j]))
        row_cell_sets.append(CellSet(core_rows, CellSetCounter(row_totals[i][0], row_totals[i][1])))

    # create cols next
    for i in range(size):
        core_cols = []
        for j in range(size):
            core_cols.append(Cell(table_of_options[j][i]))
        col_cell_sets.append(
            CellSet(core_cols[j], 
                CellSetCounter(
                    col_totals[j][0], 
                    col_totals[j][1]
                    )
            )
        )
        
    return row_cell_sets, col_cell_sets