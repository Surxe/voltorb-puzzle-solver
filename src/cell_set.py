from cell import Cell
from cell_set_counter import CellSetCounter

class CellSet:
    # represents 5 core cells and its Counter
    def __init__(self, _core_cells: list[Cell], _cell_set_counter: CellSetCounter):
        self.core_cells = _core_cells
        self.cell_set_counter = _cell_set_counter
    def __str__(self): #always presented horizontally, so if a column is printed it will look like a row
        string = ""
        for core_cell in self.core_cells:
            string += str(core_cell) + ' '
        string += str(self.cell_set_counter)
        return string