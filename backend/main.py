"""
Terminal solver. Run from repo root:
    python -m backend.main input/game1.txt                                  # prompts for each flip result
    python -m backend.main input/game1.txt --answer input/game1_answer.txt  # plays itself against the answer
"""
import argparse
import os

from backend.constants import OUTPUT_DIR
from backend.game import Game
from backend.game_file import load_answer, load_counts
from backend.simulate import play

def describe(recommendation) -> str:
    cards = ', '.join(f"({i},{j})" for i, j in recommendation.flips)
    if recommendation.safe:
        return f"flip {cards}"
    return f"no safe card left; guess {cards} ({recommendation.risk:.0%} voltorb risk)"

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
    parser.add_argument('counts', help="game file of row and column counters, e.g. input/game1.txt")
    parser.add_argument('--answer', help="answer file to play against instead of prompting for flips")
    parser.add_argument('--no-levels', action='store_true', help="don't weigh guesses by the game's level tables")
    args = parser.parse_args()

    game = Game.from_counts(*load_counts(args.counts), use_levels=not args.no_levels)
    if args.answer:
        playthrough = play(game, load_answer(args.answer))
        for n, recommendation in enumerate(playthrough.iterations, start=1):
            print(f"game loop #{n}: {describe(recommendation)}")
        print(game)
        print(f"{playthrough.status.value} with {game.coins} coins, {playthrough.guesses} guess(es)")
    else:
        play_interactively(game)
        print(f"{game.status.value} with {game.coins} coins")
    write_board_state(game)
