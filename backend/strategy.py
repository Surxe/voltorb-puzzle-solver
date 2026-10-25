"""Which cards to flip next, given what the game knows for certain and how likely each board is"""
from dataclasses import dataclass, field
from typing import Protocol

from backend.analysis import BoardOdds
from backend.board import Board
from backend.constants import VOLTORB

Position = tuple[int, int]

@dataclass(frozen=True)
class Recommendation:
    flips: list[Position] = field(default_factory=list)
    safe: bool = True # every flip is certainly not a voltorb
    risk: float = 0.0 # chance the riskiest flip is a voltorb

class Strategy(Protocol):
    def recommend(self, board: Board, certain: BoardOdds, likely: BoardOdds) -> Recommendation:
        """
        certain counts every board that matches the counters and flips;
        likely weighs those boards by how often the game deals them
        """
        ...

def candidates(board: Board) -> list[Position]:
    """Unflipped cards that may still be a 2 or 3: the only ones worth flipping"""
    return [(i, j) for i, j, cell in board.cells() if not cell.revealed and cell.could_multiply()]

class SafeFirst:
    """
    Flip every card that can't be a voltorb and may still be a 2 or 3, all in one batch.
    With none left, guess the single card least likely to be a voltorb, preferring the one most likely to multiply.
    """
    def recommend(self, board: Board, certain: BoardOdds, likely: BoardOdds) -> Recommendation:
        positions = candidates(board)
        safe = [(i, j) for i, j in positions if certain.cell(i, j).probability(VOLTORB) == 0]
        if safe:
            return Recommendation(safe)
        if not positions:
            return Recommendation()

        def odds(position):
            cell = likely.cell(*position)
            return cell.probability(VOLTORB), -cell.probability(2, 3)
        guess = min(positions, key=odds)
        return Recommendation([guess], safe=False, risk=likely.cell(*guess).probability(VOLTORB))
