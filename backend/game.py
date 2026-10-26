from enum import Enum
from math import prod

from backend.analysis import BoardOdds, analyze
from backend.board import Board, Counts, board_from_counts
from backend.constants import VOLTORB
from backend.errors import Contradiction
from backend.levels import LEVELS, TRACKED, BoardConfig, free_multipliers, level_weights
from backend.strategy import Recommendation, SafeFirst, Strategy, candidates

class Status(Enum):
    PLAYING = "playing"
    WON = "won" # every 2 and 3 has been flipped
    LOST = "lost" # a voltorb was flipped

class Game:
    """
    One round: flip results go in through reveal(), and recommend() narrows the board and says what to flip next.
    Guesses are weighed by how likely the game is to deal each board from the configs in levels (None just counts
    boards); certainties never depend on them.
    """
    def __init__(self, current_board: Board, strategy: Strategy | None = None,
                 levels: list[list[BoardConfig]] | None = LEVELS):
        self.current_board = current_board
        self.strategy = strategy or SafeFirst()
        self.levels = levels
        self.certain: BoardOdds | None = None
        self.likely: BoardOdds | None = None

    def __str__(self):
        return str(self.current_board)

    @classmethod
    def from_counts(cls, row_counts: Counts, col_counts: Counts, **kwargs) -> 'Game':
        return cls(board_from_counts(row_counts, col_counts), **kwargs)

    @classmethod
    def from_state(cls, row_counts: Counts, col_counts: Counts, revealed: list[list[int | None]], **kwargs) -> 'Game':
        """A game resumed from its counters and the flip results so far (None for cards still face down)"""
        game = cls.from_counts(row_counts, col_counts, **kwargs)
        for i, row in enumerate(revealed):
            for j, value in enumerate(row):
                if value is not None:
                    game.reveal(i, j, value)
        return game

    def reveal(self, i, j, value):
        """Reveal the content of a cell: the card at (i, j) was flipped and showed value"""
        self.current_board.reveal(i, j, value)

    def update(self, do_log=False):
        """Narrows every cell as far as the rows/cols allow, then as far as whole boards allow, and re-weighs them"""
        self.current_board.update(do_log=do_log)
        self.certain = analyze(self.current_board)
        self.certain.narrow(self.current_board)
        self.likely = self.certain
        if self.levels:
            voltorbs = sum(row.cell_set_counter.voltorbs for row in self.current_board.rows)
            free = free_multipliers(self.current_board)
            weights = level_weights(voltorbs, self.current_board.size, self.levels, free)
            try:
                self.likely = analyze(self.current_board, TRACKED, weights) if weights else self.certain
            except Contradiction: # a board the level tables don't cover, so just count boards
                pass

    @property
    def status(self) -> Status:
        board = self.current_board
        if any(cell.revealed and cell.options == [VOLTORB] for _, _, cell in board.cells()):
            return Status.LOST
        if not candidates(board):
            return Status.WON
        return Status.PLAYING

    @property
    def coins(self) -> int:
        """Coins the flipped cards are worth: their product, or 0 once a voltorb is flipped"""
        revealed = [cell.options[0] for _, _, cell in self.current_board.cells() if cell.revealed]
        return prod(revealed) if revealed else 0

    def recommend(self, do_log=False) -> Recommendation:
        """The next batch of cards to flip; empty once the round is over (the board is still narrowed, to show it)"""
        self.update(do_log=do_log)
        if self.status is not Status.PLAYING:
            return Recommendation()
        return self.strategy.recommend(self.current_board, self.certain, self.likely)

    def snapshot(self) -> dict:
        """JSON-ready state of every cell; call after recommend()"""
        def cell_state(i, j, cell):
            state = {"options": cell.options, "revealed": cell.revealed}
            if self.likely is not None:
                odds = self.likely.cell(i, j)
                state["voltorb"] = odds.probability(VOLTORB)
                state["multiplier"] = odds.probability(2, 3)
            return state
        return {
            "status": self.status.value,
            "coins": self.coins,
            "boards": self.certain.total if self.certain is not None else None,
            "cells": [
                [cell_state(i, j, cell) for j, cell in enumerate(row.core_cells)]
                for i, row in enumerate(self.current_board.rows)
            ],
        }
