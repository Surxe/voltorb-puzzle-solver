"""
Terminal solver, for when the web UI isn't handy. Run from repo root:
    python -m backend.main [--level N]
Prompts for each row's then each column's counter, then for every card it says to flip.
"""
import argparse
import os

from backend.constants import GRID_SIZE, OUTPUT_DIR
from backend.game import Game
from backend.levels import LEVELS

def describe(recommendation) -> str:
    cards = ', '.join(f"({i},{j})" for i, j in recommendation.flips)
    if recommendation.safe:
        return f"flip {cards}"
    return f"no safe card left; guess {cards} ({recommendation.risk:.0%} voltorb risk)"

def parse_counter(text: str) -> tuple[int, int]:
    """'5,1' or '5 1' -> (5, 1)"""
    value, voltorbs = (int(n) for n in text.replace(',', ' ').split())
    if not (0 <= voltorbs <= GRID_SIZE and 0 <= value <= 3 * GRID_SIZE):
        raise ValueError(text)
    return value, voltorbs

def ask_counter(name) -> tuple[int, int]:
    while True:
        try:
            return parse_counter(input(f"{name} (value,voltorbs): "))
        except ValueError:
            print("  e.g. 5,1")

def ask_result(i, j) -> int | None:
    while True:
        answer = input(f"  ({i},{j}) showed [0-3, or 'done' once every 2 and 3 is found]: ").strip()
        if answer == 'done':
            return None
        if answer in ('0', '1', '2', '3'):
            return int(answer)

def play_interactively(game: Game):
    num_game_updates = 0
    while True:
        recommendation = game.recommend()
        print(f"game loop #{num_game_updates + 1}")
        print(game)
        if not recommendation.flips:
            break
        print(describe(recommendation))
        for i, j in recommendation.flips:
            value = ask_result(i, j)
            if value is None:
                return
            game.reveal(i, j, value)
        num_game_updates += 1

def write_board_state(game: Game):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(encoding='utf-8', mode='w', file=os.path.join(OUTPUT_DIR, 'board_state.txt')) as f:
        f.write(str(game))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Voltorb Flip solver")
    parser.add_argument('--level', type=int, choices=range(1, len(LEVELS) + 1), help="the Lv. shown in game, to weigh guesses by")
    parser.add_argument('--no-levels', action='store_true', help="don't weigh guesses by the game's level tables")
    args = parser.parse_args()

    levels = None if args.no_levels else [LEVELS[args.level - 1]] if args.level else LEVELS
    row_counts = [ask_counter(f"row {n + 1}") for n in range(GRID_SIZE)]
    col_counts = [ask_counter(f"column {n + 1}") for n in range(GRID_SIZE)]
    game = Game.from_counts(row_counts, col_counts, levels=levels)
    play_interactively(game)
    print(f"{game.status.value} with {game.coins} coins")
    write_board_state(game)
