"""
Local web UI for the solver. Run from repo root:
    python -m frontend.app [--port 5000]

The API is stateless: the page sends the counters and every flip result so far, and gets back the narrowed
board and the next cards to flip.
"""
import argparse

from flask import Flask, jsonify, render_template, request

from backend.constants import ALL, GRID_SIZE
from backend.errors import Contradiction
from backend.game import Game
from backend.levels import LEVELS

def parse_counts(raw, name) -> list[tuple[int, int]]:
    if not isinstance(raw, list) or len(raw) != GRID_SIZE:
        raise ValueError(f"{name} needs {GRID_SIZE} counters")
    counts = []
    for n, counter in enumerate(raw):
        if not (isinstance(counter, list) and len(counter) == 2 and all(type(x) is int for x in counter)):
            raise ValueError(f"{name}[{n}] must be [value, voltorbs]")
        value, voltorbs = counter
        if not (0 <= voltorbs <= GRID_SIZE and 0 <= value <= max(ALL) * GRID_SIZE):
            raise ValueError(f"{name}[{n}] = {counter} is out of range")
        counts.append((value, voltorbs))
    return counts

def parse_revealed(raw) -> list[list[int | None]]:
    if raw is None:
        return [[None] * GRID_SIZE for _ in range(GRID_SIZE)]
    if not (isinstance(raw, list) and len(raw) == GRID_SIZE and all(isinstance(row, list) and len(row) == GRID_SIZE for row in raw)):
        raise ValueError(f"revealed must be {GRID_SIZE}x{GRID_SIZE}")
    for row in raw:
        for value in row:
            if value is not None and (type(value) is not int or value not in ALL):
                raise ValueError(f"a flipped card shows one of {ALL}, not {value!r}")
    return raw

def parse_levels(raw):
    """The level shown in game narrows the configs guesses are weighed by; unknown means any level"""
    if raw is None:
        return LEVELS
    if type(raw) is not int or not 1 <= raw <= len(LEVELS):
        raise ValueError(f"level must be 1-{len(LEVELS)}")
    return [LEVELS[raw - 1]]

def solve(body: dict) -> dict:
    game = Game.from_state(
        parse_counts(body.get('rows'), 'rows'),
        parse_counts(body.get('cols'), 'cols'),
        parse_revealed(body.get('revealed')),
        levels=parse_levels(body.get('level')),
    )
    recommendation = game.recommend()
    return {
        **game.snapshot(),
        'recommendation': {
            'flips': [list(position) for position in recommendation.flips],
            'safe': recommendation.safe,
            'risk': recommendation.risk,
        },
    }

def create_app() -> Flask:
    app = Flask(__name__)

    @app.get('/')
    def index():
        return render_template('index.html', size=GRID_SIZE, levels=len(LEVELS))

    @app.post('/api/solve')
    def api_solve():
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            return jsonify(error="expected a JSON object"), 400
        try:
            return jsonify(solve(body))
        except Contradiction as error:
            return jsonify(error=str(error)), 422
        except ValueError as error:
            return jsonify(error=str(error)), 400

    return app


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Voltorb Flip solver web UI")
    parser.add_argument('--port', type=int, default=5000)
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    create_app().run(host='127.0.0.1', port=args.port, debug=args.debug)
