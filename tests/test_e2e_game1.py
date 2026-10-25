"""The game in progress when the solver was written, played start to finish against its known answer"""
import subprocess
import sys
from pathlib import Path

from backend.constants import VOLTORB
from backend.game import Game, Status
from backend.levels import counts_of
from backend.simulate import play

REPO = Path(__file__).resolve().parent.parent

def test_counters_match_the_answer(game1):
    rows, cols, answer = game1
    assert counts_of(answer) == (rows, cols)

def test_solves_without_guessing(game1):
    rows, cols, answer = game1
    game = Game.from_counts(rows, cols)
    playthrough = play(game, answer)
    assert playthrough.status is Status.WON
    assert playthrough.guesses == 0
    assert [recommendation.flips for recommendation in playthrough.iterations] == [
        [(0, 2), (2, 2), (3, 2), (4, 2)], # column 2 is (8, 0): no voltorbs, and only (1, 2) is surely a 1
        [(0, 1), (3, 1)],
    ]
    assert game.coins == 24 # 3 twos and a three: this board's maximum
    for i, j, cell in game.current_board.cells():
        if cell.revealed:
            assert answer[i][j] != VOLTORB

def test_solves_without_level_tables(game1):
    rows, cols, answer = game1
    playthrough = play(Game.from_counts(rows, cols, levels=None), answer)
    assert playthrough.status is Status.WON and playthrough.guesses == 0

def run_cli(stdin):
    return subprocess.run(
        [sys.executable, '-m', 'backend.main'],
        cwd=REPO, input=stdin, capture_output=True, text=True, timeout=60, check=True,
    ).stdout

def counters_input(game1):
    rows, cols, _ = game1
    return ''.join(f'{value},{voltorbs}\n' for value, voltorbs in [*rows, *cols])

def test_cli_prompts_for_counters_then_each_flip(game1):
    _, _, answer = game1
    results = [answer[0][2], answer[2][2], answer[3][2], answer[4][2], answer[0][1], answer[3][1]]
    out = run_cli(counters_input(game1) + ''.join(f'{value}\n' for value in results))
    assert 'flip (0,2), (2,2), (3,2), (4,2)' in out
    assert 'flip (0,1), (3,1)' in out
    assert out.count('showed') == len(results)
    assert out.strip().endswith('won with 24 coins')

def test_cli_reprompts_a_bad_counter(game1):
    out = run_cli('5;1\n' + counters_input(game1) + 'done\n')
    assert 'e.g. 5,1' in out

def test_cli_stops_when_told_done(game1):
    out = run_cli(counters_input(game1) + '1\ndone\n')
    assert out.strip().endswith('playing with 1 coins')
