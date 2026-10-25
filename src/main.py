from typing import List

# Options remaining in a given cell
ALL = [0, 1, 2, 3]
ZERO = [0]
ONE = [1]
TWO = [2]
THREE = [3]


def list_to_str(_list): #make this an overload of List?
    combined_str = ""
    for str_ in [str(elem) for elem in _list]:
        combined_str += str_
    if combined_str is None:
        raise ValueError("idiot")
    return combined_str

def spaced_str(str, min_len):
    return str + ' ' * (min_len - len(str))

LEN_MAX_OPTIONS_AS_STRING = len(list_to_str(ALL))

class Cell:
    def __init__(self, options: list[int]):
        self.options = options
    def __str__(self):
        options_str = list_to_str(self.options)
        return spaced_str(options_str, LEN_MAX_OPTIONS_AS_STRING)
        
class CellSetCounter:
    # represents the sum value & voltorbs of either a row or a column
    #. e.g.. top row may contain exactly 2 voltorbs and exactly 3 value
    def __init__(self, _value: int, _voltorbs: int):
        self.value = _value
        self.voltorbs = _voltorbs
    def __str__(self):
        return spaced_str(f"{self.value},{self.voltorbs}", LEN_MAX_OPTIONS_AS_STRING)

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

        

def row_or_counter_factory(pairs_list):
    # pairs_list = [(value, voltorbs)]
    # returns [CellSetCounter(value, voltorbs)]
    return [CellSetCounter(pair[0], pair[1]) for pair in pairs_list]

def board_factory(table_of_options: list, row_totals: list[tuple], col_totals: list[tuple]) -> tuple[CellSet, CellSet]:
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
