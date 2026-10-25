"""The game's board configurations per level, and a generator for random answer boards that follow them"""
import random
from collections import defaultdict
from dataclasses import dataclass
from math import factorial

from backend.board import Counts
from backend.constants import GRID_SIZE, VOLTORB

@dataclass(frozen=True)
class BoardConfig:
    twos: int
    threes: int
    voltorbs: int

    @property
    def max_coins(self):
        return 2 ** self.twos * 3 ** self.threes

# Lv. 1-8, five configurations each
LEVELS = [
    [BoardConfig(3, 1, 6), BoardConfig(0, 3, 6), BoardConfig(5, 0, 6), BoardConfig(2, 2, 6), BoardConfig(4, 1, 6)],
    [BoardConfig(1, 3, 7), BoardConfig(6, 0, 7), BoardConfig(3, 2, 7), BoardConfig(0, 4, 7), BoardConfig(5, 1, 7)],
    [BoardConfig(2, 3, 8), BoardConfig(7, 0, 8), BoardConfig(4, 2, 8), BoardConfig(1, 4, 8), BoardConfig(6, 1, 8)],
    [BoardConfig(3, 3, 8), BoardConfig(0, 5, 8), BoardConfig(8, 0, 10), BoardConfig(5, 2, 10), BoardConfig(2, 4, 10)],
    [BoardConfig(7, 1, 10), BoardConfig(4, 3, 10), BoardConfig(1, 5, 10), BoardConfig(9, 0, 10), BoardConfig(6, 2, 10)],
    [BoardConfig(3, 4, 10), BoardConfig(0, 6, 10), BoardConfig(8, 1, 10), BoardConfig(5, 3, 10), BoardConfig(2, 5, 10)],
    [BoardConfig(7, 2, 10), BoardConfig(4, 4, 10), BoardConfig(1, 6, 13), BoardConfig(9, 1, 13), BoardConfig(6, 3, 10)],
    [BoardConfig(0, 7, 10), BoardConfig(8, 2, 10), BoardConfig(5, 4, 10), BoardConfig(2, 6, 10), BoardConfig(7, 3, 10)],
]

Grid = list[list[int]]
TRACKED = (2, 3) # what a config fixes besides voltorbs; key order of level_weights()

def deals(config: BoardConfig, size=GRID_SIZE) -> int:
    """# of distinct boards the config can be dealt as: ways to place its voltorbs, 2's and 3's among the cells"""
    ones = size * size - config.voltorbs - config.twos - config.threes
    return factorial(size * size) // (
        factorial(config.voltorbs) * factorial(config.twos) * factorial(config.threes) * factorial(ones)
    )

def level_weights(voltorbs: int, size=GRID_SIZE, levels=LEVELS) -> dict[tuple[int, int], float]:
    """
    How likely the game is to deal one specific board, by its (# of 2's, # of 3's), given its total voltorbs:
    each config with that many voltorbs is equally likely, and so is every board within a config.
    For analysis.analyze(board, TRACKED, weights)
    """
    matching = [config for level in levels for config in level if config.voltorbs == voltorbs]
    weights = defaultdict(float)
    for config in matching:
        weights[(config.twos, config.threes)] += 1 / len(matching) / deals(config, size)
    return dict(weights)

def random_answer(config: BoardConfig, rng: random.Random, size=GRID_SIZE) -> Grid:
    """Scatters the config's voltorbs, 2's and 3's over a board of 1's"""
    values = [VOLTORB] * config.voltorbs + [2] * config.twos + [3] * config.threes
    values += [1] * (size * size - len(values))
    rng.shuffle(values)
    return [values[i * size:(i + 1) * size] for i in range(size)]

def counts_of(answer: Grid) -> tuple[Counts, Counts]:
    """The (value, voltorbs) counters the game would show for an answer board"""
    def count(line):
        return (sum(line), sum(1 for value in line if value == VOLTORB))
    return [count(row) for row in answer], [count(col) for col in zip(*answer)]
