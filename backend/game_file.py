"""
Game files under input/:
    counts: one "value,voltorbs" line per row, a blank line, then one per column
    answer: one line of digits per row, 0 for a voltorb
"""
from pathlib import Path

from backend.board import Counts
from backend.levels import Grid

def parse_counts(text: str) -> tuple[Counts, Counts]:
    blocks = text.strip().split('\n\n')
    if len(blocks) != 2:
        raise ValueError("expected the row counters, a blank line, then the column counters")
    def parse(block):
        return [tuple(int(n) for n in line.split(',')) for line in block.split('\n') if line.strip()]
    return parse(blocks[0]), parse(blocks[1])

def parse_answer(text: str) -> Grid:
    return [[int(digit) for digit in line.strip()] for line in text.strip().split('\n')]

def load_counts(path) -> tuple[Counts, Counts]:
    return parse_counts(Path(path).read_text(encoding='utf-8'))

def load_answer(path) -> Grid:
    return parse_answer(Path(path).read_text(encoding='utf-8'))
