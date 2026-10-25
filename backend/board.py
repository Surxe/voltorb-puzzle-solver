from collections.abc import Iterator

from backend.cell import Cell
from backend.cell_set import CellSet
from backend.cell_set_counter import CellSetCounter
from backend.constants import ALL
from backend.utils import log

Counts = list[tuple[int, int]] # (value, voltorbs) per row or per column

class Board:
    # rows and cols are CellSets over the same Cells, so narrowing a cell through its row is seen by its column
    def __init__(self, _row_cell_sets: list[CellSet], _col_cell_sets: list[CellSet]):
        self.rows = _row_cell_sets
        self.cols = _col_cell_sets
        self.size = len(_row_cell_sets)

    def __str__(self):
        contents = ""
        # core table + row counters
        for row in self.rows:
            contents += str(row) + '\n'
        for col in self.cols:
            contents += str(col.cell_set_counter) + ' '

        return f"Board:\n{contents}\n"

    @property
    def lines(self) -> list[CellSet]:
        return self.rows + self.cols

    def cell(self, i, j) -> Cell:
        return self.rows[i].core_cells[j]

    def cells(self) -> Iterator[tuple[int, int, Cell]]:
        for i, row in enumerate(self.rows):
            for j, cell in enumerate(row.core_cells):
                yield i, j, cell

    def set_cell(self, i, j, new_options):
        self.cell(i, j).set(new_options)

    def reveal(self, i, j, value):
        self.cell(i, j).reveal(value)

    def update(self, do_log=False) -> int:
        """Updates every row and col until none of them can narrow a cell any further; returns the # of passes"""
        passes = 0
        changed = True
        while changed:
            passes += 1
            log(f"update() pass {passes}", do_log=do_log)
            changed = False
            for line in self.lines:
                changed |= line.update(do_log=do_log)
        log(self, do_log=do_log)
        return passes


def board_factory(table: list) -> Board:
    """
    Builds a Board from a table of n rows of [options per cell..., (value, voltorbs)],
    followed by a final row of the column counters [(value, voltorbs) per column..., None]
    """
    size = len(table) - 1
    # one Cell per position, shared by the row and the column that intercept there
    cells = [[Cell(list(table[i][j])) for j in range(size)] for i in range(size)]
    rows = [CellSet(cells[i], CellSetCounter(*table[i][size])) for i in range(size)]
    cols = [CellSet([cells[i][j] for i in range(size)], CellSetCounter(*table[size][j])) for j in range(size)]
    return Board(rows, cols)

def board_from_counts(row_counts: Counts, col_counts: Counts, options=ALL) -> Board:
    """A fresh Board where every cell may be any of options"""
    size = len(row_counts)
    if len(col_counts) != size:
        raise ValueError(f"{size} row counters but {len(col_counts)} column counters")
    table = [[options] * size + [row_counts[i]] for i in range(size)]
    table.append(list(col_counts) + [None])
    return board_factory(table)
