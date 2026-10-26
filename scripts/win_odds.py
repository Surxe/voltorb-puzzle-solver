"""
Estimates the solver's odds per level: deals boards the way the game does, plays each one by flipping exactly
what the solver recommends, and tallies wins, losses and forced guesses.

    python scripts/win_odds.py [--boards 2000] [--seed 0] [--jobs N]

Each board is played three ways: with the Lv. entered (what the UI does when you fill in the Lv. box), with the
level unknown, and with no level tables at all. Certain flips are the same in all three; only guesses differ.
"""
import argparse
import os
import random
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from math import sqrt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.game import Game, Status
from backend.levels import LEVELS, counts_of, deal
from backend.simulate import play

PRIORS = { # name: the levels a game is told to weigh guesses by, given the board's level
    'Lv. known': lambda level: [LEVELS[level - 1]],
    'Lv. unknown': lambda level: LEVELS,
    'no tables': lambda level: None,
}

@dataclass
class Tally:
    boards: int = 0
    wins: int = 0
    forced: int = 0 # boards that needed at least one guess
    guesses: int = 0

    def add(self, other: 'Tally'):
        self.boards += other.boards
        self.wins += other.wins
        self.forced += other.forced
        self.guesses += other.guesses

def play_boards(level: int, seed: int, boards: int) -> dict[str, Tally]:
    rng = random.Random(f'{level}-{seed}')
    tallies = {name: Tally() for name in PRIORS}
    for _ in range(boards):
        answer = deal(rng.choice(LEVELS[level - 1]), rng)
        for name, levels in PRIORS.items():
            playthrough = play(Game.from_counts(*counts_of(answer), levels=levels(level)), answer)
            tally = tallies[name]
            tally.boards += 1
            tally.wins += playthrough.status is Status.WON
            tally.forced += playthrough.guesses > 0
            tally.guesses += playthrough.guesses
    return tallies

def percent(part, whole):
    return f"{part / whole:.1%}"

def margin(part, whole):
    """95% margin of error of the proportion part/whole"""
    p = part / whole
    return f"±{1.96 * sqrt(p * (1 - p) / whole):.1%}"


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument('--boards', type=int, default=2000, help="boards per level")
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--jobs', type=int, default=os.cpu_count())
    args = parser.parse_args()

    chunk = 50
    work = [
        (level, f'{args.seed}-{start}', min(chunk, args.boards - start))
        for level in range(1, len(LEVELS) + 1) for start in range(0, args.boards, chunk)
    ]
    results = {level: {name: Tally() for name in PRIORS} for level in range(1, len(LEVELS) + 1)}
    with ProcessPoolExecutor(args.jobs) as pool:
        for (level, _, _), tallies in zip(work, pool.map(play_boards, *zip(*work))):
            for name, tally in tallies.items():
                results[level][name].add(tally)

    print(f"{args.boards} boards per level, dealt like the game (seed {args.seed})\n")
    print("| Level | Win, Lv. known | Win, Lv. unknown | Win, no tables | Needs a guess | Guesses per board |")
    print("| --- | --- | --- | --- | --- | --- |")
    for level, tallies in results.items():
        known = tallies['Lv. known']
        wins = [f"{percent(t.wins, t.boards)} {margin(t.wins, t.boards)}" for t in tallies.values()]
        print(f"| {level} | {' | '.join(wins)} | {percent(known.forced, known.boards)} | {known.guesses / known.boards:.2f} |")
