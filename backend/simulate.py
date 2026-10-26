"""Plays a game against a known answer board, flipping exactly what the solver recommends"""
from dataclasses import dataclass, field

from backend.game import Game, Status
from backend.levels import Grid
from backend.strategy import Recommendation

@dataclass
class Playthrough:
    status: Status
    iterations: list[Recommendation] = field(default_factory=list)

    @property
    def guesses(self) -> int:
        return sum(not recommendation.safe for recommendation in self.iterations)

def play(game: Game, answer: Grid, max_iterations=50) -> Playthrough:
    playthrough = Playthrough(game.status)
    for _ in range(max_iterations):
        recommendation = game.recommend()
        if not recommendation.flips:
            break
        playthrough.iterations.append(recommendation)
        for i, j in recommendation.flips:
            game.reveal(i, j, answer[i][j])
    else:
        raise RuntimeError(f"no result after {max_iterations} iterations")
    playthrough.status = game.status
    return playthrough
