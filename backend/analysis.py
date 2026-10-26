"""
Board-wide reasoning. Rows and cols narrowing their own cells (Board.update) can't see constraints that only
show up when several lines are combined, so this weighs every complete board that matches all the counters
and revealed cells, and how much of that weight puts each option in each cell.
"""
from collections import defaultdict
from dataclasses import dataclass

from backend.board import Board
from backend.constants import VOLTORB
from backend.errors import Contradiction

ColumnState = tuple[tuple[int, int], ...] # (value, voltorbs) each column still needs from the rows below
Tally = tuple[int, ...] # how many of each tracked option a board holds, e.g. (# of 2's, # of 3's)

@dataclass(frozen=True)
class CellOdds:
    weights: dict[int, float] # option -> weight of the matching boards that put it in this cell
    total: float # weight of every matching board

    @property
    def options(self) -> list[int]:
        return sorted(option for option, weight in self.weights.items() if weight)

    def probability(self, *options: int) -> float:
        return sum(self.weights.get(option, 0) for option in options) / self.total

@dataclass(frozen=True)
class BoardOdds:
    total: float # weight of every matching board; their count when unweighted
    cells: list[list[CellOdds]]

    def cell(self, i, j) -> CellOdds:
        return self.cells[i][j]

    def narrow(self, board: Board) -> bool:
        """Removes options from the board's cells that no matching board uses; returns whether any changed"""
        changed = False
        for i, j, cell in board.cells():
            changed |= cell.set(self.cell(i, j).options)
        return changed


def analyze(board: Board, tracked: Tally = (), weights: dict[Tally, float] | None = None) -> BoardOdds:
    """
    Every matching board counts once, unless weights is given: then a board weighs weights[tally], where tally
    counts how many of each `tracked` option it holds (boards with an unlisted tally weigh 0).

    Walks the rows top to bottom, tracking what each column still needs. completions(i, state, tally) is the
    weight of the ways rows [i, n) can finish the board, so each row arrangement's share is
    (ways to reach state) * (completions after placing it).
    """
    n = board.size
    arrangements = [row.arrangements() for row in board.rows]
    options = {option for _, _, cell in board.cells() for option in cell.options}
    max_option = max(options, default=0)
    min_value = min((option for option in options if option != VOLTORB), default=0)
    start = tuple((col.cell_set_counter.value, col.cell_set_counter.voltorbs) for col in board.cols)

    def place(state: ColumnState, arrangement) -> ColumnState | None:
        needs = []
        for (value, voltorbs), option in zip(state, arrangement):
            value, voltorbs = value - option, voltorbs - (option == VOLTORB)
            if value < 0 or voltorbs < 0:
                return None
            needs.append((value, voltorbs))
        return tuple(needs)

    def add(tally: Tally, arrangement) -> Tally:
        return tuple(count + arrangement.count(option) for count, option in zip(tally, tracked))

    memo: dict[tuple[int, ColumnState, Tally], float] = {}
    def completions(i: int, state: ColumnState, tally: Tally) -> float:
        rows_left = n - i
        for value, voltorbs in state:
            # each column has rows_left cells left, voltorbs of which are 0 and the rest hold value
            if voltorbs > rows_left or not min_value * (rows_left - voltorbs) <= value <= max_option * (rows_left - voltorbs):
                return 0
        if i == n:
            return 1 if weights is None else weights.get(tally, 0)
        key = (i, state, tally)
        if key not in memo:
            memo[key] = sum(
                completions(i + 1, after, add(tally, arrangement))
                for arrangement in arrangements[i]
                if (after := place(state, arrangement)) is not None
            )
        return memo[key]

    start_tally = (0,) * len(tracked)
    total = completions(0, start, start_tally)
    if not total:
        raise Contradiction("no board matches every counter and flipped card")

    cell_weights = [[defaultdict(float) for _ in range(n)] for _ in range(n)]
    reached = {(start, start_tally): 1} # (state, tally) -> ways rows [0, i) reach it
    for i in range(n):
        next_reached = defaultdict(int)
        for (state, tally), ways_before in reached.items():
            for arrangement in arrangements[i]:
                after = place(state, arrangement)
                if after is None:
                    continue
                after_tally = add(tally, arrangement)
                ways_after = completions(i + 1, after, after_tally)
                if not ways_after:
                    continue
                for j, option in enumerate(arrangement):
                    cell_weights[i][j][option] += ways_before * ways_after
                next_reached[(after, after_tally)] += ways_before
        reached = next_reached

    return BoardOdds(total, [[CellOdds(dict(cell_weights[i][j]), total) for j in range(n)] for i in range(n)])
