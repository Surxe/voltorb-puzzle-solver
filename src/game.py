class Game:
    def __init__(self, current_board, answer_board):
        self.current_board = current_board
        self.answer_board = answer_board

    def __str__(self):
        return str(self.current_board)

    def update(self):
        # Update board
        self.current_board.update()

    def flip(self):
        # Flip cells that can't be a voltorb
        for i in range(len(self.current_board.rows)):
            row = self.current_board.rows[i]
            for j in range(len(row.core_cells)):
                cell = row.core_cells[j]
                if 0 not in cell.options:
                    self.flip_cell(i, j)

    def flip_cell(self, i, j):
        """Reveal the content of a cell by replacing it's current options with the answer options, a list of len 1"""
        self.current_board.set_cell(i, j, self.answer_board.rows[i].core_cells[j].options)