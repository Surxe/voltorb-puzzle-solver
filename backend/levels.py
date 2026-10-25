"""
How the game deals boards, taken from the HeartGold/SoulSilver decompilation:
https://github.com/pret/pokeheartgold/blob/6988158691eb6178cff697cda0428045ddcba5fb/src/voltorb_flip/voltorb_flip_game.c
(sBoardConfigs, sBoardIdDistribution, VoltorbFlipGameState_GenerateBoard, VoltorbFlipGameState_RetryBoardGen)

Each level picks one of its 10 configs with equal chance and scatters that many voltorbs, 2's and 3's at random
over a board of 1's. It re-deals, up to 1000 times, while the board gives away too many free multipliers:
2's and 3's in a row or column with no voltorbs, which can be flipped without any risk.
"""
import random
from collections import defaultdict
from dataclasses import dataclass
from functools import cache
from itertools import combinations
from math import comb

from backend.board import Board, Counts
from backend.constants import GRID_SIZE, VOLTORB

@dataclass(frozen=True)
class BoardConfig:
    voltorbs: int
    twos: int
    threes: int
    max_free_per_line: int | None = None # re-dealt if any row or column has this many free multipliers
    max_free_total: int | None = None # or if the whole board has this many

    @property
    def multipliers(self):
        return self.twos + self.threes

# sBoardConfigs, Lv. 1-8: (voltorbs, 2's, 3's, max free per row/column, max free in all)
LEVELS = [[BoardConfig(*row) for row in level] for level in [
    [(6, 3, 1, 3, 3), (6, 0, 3, 2, 2), (6, 5, 0, 3, 4), (6, 2, 2, 3, 3), (6, 4, 1, 3, 4),
     (6, 3, 1, 3, 3), (6, 0, 3, 2, 2), (6, 5, 0, 3, 4), (6, 2, 2, 3, 3), (6, 4, 1, 3, 4)],
    [(7, 1, 3, 2, 3), (7, 6, 0, 3, 4), (7, 3, 2, 2, 3), (7, 0, 4, 2, 3), (7, 5, 1, 3, 4),
     (7, 1, 3, 2, 2), (7, 6, 0, 3, 3), (7, 3, 2, 2, 2), (7, 0, 4, 2, 2), (7, 5, 1, 3, 3)],
    [(8, 2, 3, 2, 3), (8, 7, 0, 3, 4), (8, 4, 2, 3, 4), (8, 1, 4, 2, 3), (8, 6, 1, 4, 3),
     (8, 2, 3, 2, 2), (8, 7, 0, 3, 3), (8, 4, 2, 3, 3), (8, 1, 4, 2, 2), (8, 6, 1, 3, 3)],
    [(8, 3, 3, 4, 3), (8, 0, 5, 2, 3), (10, 8, 0, 4, 5), (10, 5, 2, 3, 4), (10, 2, 4, 3, 4),
     (8, 3, 3, 3, 3), (8, 0, 5, 2, 2), (10, 8, 0, 4, 4), (10, 5, 2, 3, 3), (10, 2, 4, 3, 3)],
    [(10, 7, 1, 4, 5), (10, 4, 3, 3, 4), (10, 1, 5, 3, 4), (10, 9, 0, 4, 5), (10, 6, 2, 4, 5),
     (10, 7, 1, 4, 4), (10, 4, 3, 3, 3), (10, 1, 5, 3, 3), (10, 9, 0, 4, 4), (10, 6, 2, 4, 4)],
    [(10, 3, 4, 3, 4), (10, 0, 6, 3, 4), (10, 8, 1, 4, 5), (10, 5, 3, 4, 5), (10, 2, 5, 3, 4),
     (10, 3, 4, 3, 3), (10, 0, 6, 3, 3), (10, 8, 1, 4, 4), (10, 5, 3, 4, 4), (10, 2, 5, 3, 3)],
    [(10, 7, 2, 4, 5), (10, 4, 4, 4, 5), (13, 1, 6, 3, 4), (13, 9, 1, 5, 6), (10, 6, 3, 4, 5),
     (10, 7, 2, 4, 4), (10, 4, 4, 4, 4), (13, 1, 6, 3, 3), (13, 9, 1, 5, 5), (10, 6, 3, 4, 4)],
    [(10, 0, 7, 3, 4), (10, 8, 2, 5, 6), (10, 5, 4, 4, 5), (10, 2, 6, 4, 5), (10, 7, 3, 5, 6),
     (10, 0, 7, 3, 3), (10, 8, 2, 5, 5), (10, 5, 4, 4, 4), (10, 2, 6, 4, 4), (10, 7, 3, 5, 5)],
]]

Grid = list[list[int]]
TRACKED = (2, 3) # what a config fixes besides voltorbs; key order of level_weights()

@dataclass(frozen=True)
class FreeCount:
    """Free multipliers per row and per column: 2's and 3's in a line with no voltorbs"""
    per_row: tuple[int, ...]
    per_col: tuple[int, ...]

    @property
    def total(self):
        return sum(self.per_row)

def too_generous(config: BoardConfig, free: FreeCount) -> bool:
    """True when the game would re-deal a board that gives these multipliers away for free"""
    if config.max_free_total is not None and free.total >= config.max_free_total:
        return True
    return config.max_free_per_line is not None and max(free.per_row + free.per_col) >= config.max_free_per_line

def free_cells(row_voltorbs: list[int], col_voltorbs: list[int]) -> list[tuple[int, int]]:
    return [
        (i, j) for i, row in enumerate(row_voltorbs) for j, col in enumerate(col_voltorbs)
        if row == 0 or col == 0
    ]

def count_free(values: dict[tuple[int, int], int], size: int) -> FreeCount:
    """Tallies the multipliers among free cells' values"""
    per_row, per_col = [0] * size, [0] * size
    for (i, j), value in values.items():
        if value > 1:
            per_row[i] += 1
            per_col[j] += 1
    return FreeCount(tuple(per_row), tuple(per_col))

def free_multipliers(board: Board) -> FreeCount | None:
    """
    The board's free multipliers, or None while a free cell's value is still open. Free cells can't be voltorbs,
    so the solver flips every one that could be a 2 or 3 before it ever has to guess.
    """
    cells = free_cells(
        [row.cell_set_counter.voltorbs for row in board.rows],
        [col.cell_set_counter.voltorbs for col in board.cols],
    )
    if any(len(board.cell(i, j).options) != 1 for i, j in cells):
        return None
    return count_free({(i, j): board.cell(i, j).options[0] for i, j in cells}, board.size)

def deal(config: BoardConfig, rng: random.Random, size=GRID_SIZE, tries=1000) -> Grid:
    """A random answer board, dealt the way the game deals one"""
    for _ in range(tries):
        positions = rng.sample(range(size * size), config.voltorbs + config.multipliers)
        flat = [1] * (size * size)
        for n, position in enumerate(positions):
            flat[position] = VOLTORB if n < config.voltorbs else 2 if n < config.voltorbs + config.twos else 3
        grid = [flat[i * size:(i + 1) * size] for i in range(size)]
        rows, cols = counts_of(grid)
        cells = free_cells([voltorbs for _, voltorbs in rows], [voltorbs for _, voltorbs in cols])
        if not too_generous(config, count_free({(i, j): grid[i][j] for i, j in cells}, size)):
            break
    return grid

def covering_placements(height: int, width: int, voltorbs: int) -> int:
    """Ways to place voltorbs in a height x width grid with at least one in every row and column"""
    return sum(
        (-1) ** (i + j) * comb(height, i) * comb(width, j) * comb((height - i) * (width - j), voltorbs)
        for i in range(height + 1) for j in range(width + 1)
    )

@cache
def capped_subsets(size: int, free_rows: int, free_cols: int, k: int, cap: int | None) -> int:
    """
    Ways to put k multipliers on the free cells when the first free_rows rows and free_cols columns have no
    voltorbs, with fewer than cap in any one row or column
    """
    cells = [(i, j) for i in range(size) for j in range(size) if i < free_rows or j < free_cols]
    if cap is None:
        return comb(len(cells), k)
    count = 0
    for subset in combinations(cells, k):
        rows, cols = [0] * size, [0] * size
        for i, j in subset:
            rows[i] += 1
            cols[j] += 1
        count += max(rows + cols) < cap
    return count

@cache
def valid_deals(config: BoardConfig, size=GRID_SIZE) -> int:
    """
    # of distinct boards the config can end up as: placements of its voltorbs, 2's and 3's that the game
    doesn't re-deal. Grouped by how many rows and columns have no voltorbs, since that decides the free cells.
    """
    most_free = config.multipliers if config.max_free_total is None else config.max_free_total - 1
    total = 0
    for free_rows in range(size + 1):
        for free_cols in range(size + 1):
            height, width = size - free_rows, size - free_cols
            voltorb_ways = covering_placements(height, width, config.voltorbs)
            if not voltorb_ways:
                continue
            free = size * size - height * width
            risky = height * width - config.voltorbs # cells outside the free ones left for 1's, 2's and 3's
            multiplier_ways = sum(
                capped_subsets(size, free_rows, free_cols, k, config.max_free_per_line) * comb(risky, config.multipliers - k)
                for k in range(min(config.multipliers, free, most_free) + 1)
            )
            total += comb(size, free_rows) * comb(size, free_cols) * voltorb_ways * multiplier_ways
    return total * comb(config.multipliers, config.twos)

def level_weights(voltorbs: int, size=GRID_SIZE, levels=LEVELS, free: FreeCount | None = None) -> dict[tuple[int, int], float]:
    """
    How likely the game is to deal one specific board, by its (# of 2's, # of 3's), given its total voltorbs:
    every config of the levels is equally likely, and each deals every board it doesn't re-deal equally often.
    Once the free multipliers are known (free), configs that would have re-dealt this board are ruled out.
    For analysis.analyze(board, TRACKED, weights)
    """
    weights = defaultdict(float)
    for config in (config for level in levels for config in level):
        if config.voltorbs == voltorbs and (free is None or not too_generous(config, free)):
            weights[(config.twos, config.threes)] += 1 / valid_deals(config, size)
    return dict(weights)

def counts_of(answer: Grid) -> tuple[Counts, Counts]:
    """The (value, voltorbs) counters the game would show for an answer board"""
    def count(line):
        return (sum(line), sum(1 for value in line if value == VOLTORB))
    return [count(row) for row in answer], [count(col) for col in zip(*answer)]
