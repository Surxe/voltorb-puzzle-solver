# voltorb-puzzle-solver

Solver for Voltorb Flip, the Game Corner card game in Pokemon HeartGold/SoulSilver. You type in each
row's and column's counters (points, Voltorbs). It tells you which cards to flip, one batch per game
iteration, and takes the results before working out the next batch. A round ends when every 2 and 3
is flipped, or when you say you've found them all.

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt        # requirements-dev.txt for the tests
```

The art is original, not taken from the game: `scripts/make_sprites.py` draws every sprite in code
and writes the PNGs to `frontend/static/sprites/`. Re-run it after changing the art; a test fails if
the checked-in PNGs fall out of date. The pixel font is [Silkscreen](https://github.com/googlefonts/silkscreen)
(SIL Open Font License), vendored in `frontend/static/fonts/`.

## Web UI
```bash
python -m frontend.app    # http://127.0.0.1:5000
```
1. Type each row's points and Voltorbs, then each column's. **Tab** cycles through just those 20 boxes,
   and **Enter** solves. Optionally put the level shown in game in the `Lv.` box.
2. The cards to flip get a red frame. Flip them in game and type what each showed (`1`-`3`, or `0`
   for a Voltorb), then press **Enter** for the next batch. **Tab** cycles through just those cards.
   The box or card you're typing into is gold.
3. If no card is certainly safe, the solver marks the single card least likely to be a Voltorb and shows
   the risk. See [Why it sometimes guesses](#why-it-sometimes-guesses).

Corner marks on a face-down card show what it can still be. The number on it is the chance it's a
Voltorb. Clicking a face-down card lets you enter a flip the solver didn't ask for. **Back** undoes the
last batch. **Found all 2s & 3s** ends the round.

## CLI
```bash
python -m backend.main
```
It asks for each row's and then each column's counter (`5,1`), then for every card it says to flip.
Add `--level N` to weigh guesses by that level's boards only, or `--no-levels` to weigh every matching
board the same.

## How it solves
Each layer only narrows what the layer before left open:

| Layer | Module | What it does |
| --- | --- | --- |
| Line | `backend/cell_set.py` | `CellSet.update()` keeps the options that appear in at least one arrangement matching the row or column counter (`supported_options`). That covers the "a 3 and a 1 or a 2 and a 2, but no 3's, so 2 and 2" case. `process_new_options(v, c, z, set_options)` is the same rule for c alike cells. |
| Board | `backend/board.py` | `Board.update()` repeats every row and column update until nothing changes. Rows and columns share `Cell`s, so narrowing in one line is seen by the lines crossing it. |
| Whole boards | `backend/analysis.py` | `analyze()` counts every complete board that fits all counters and flips. It goes row by row, tracking what each column still needs, and memoizes, so it takes milliseconds. The result is exact per-cell odds, plus deductions no single line can see. |
| Level tables | `backend/levels.py` | How the game deals boards, from the [pokeheartgold decompilation](https://github.com/pret/pokeheartgold/blob/6988158691eb6178cff697cda0428045ddcba5fb/src/voltorb_flip/voltorb_flip_game.c). Each level picks one of 10 configs (Voltorbs, 2's, 3's) at random. The game re-deals any board with too many free 2's and 3's, meaning ones in a row or column with no Voltorbs. `level_weights()` weighs each matching board by how likely the game is to deal it. This only ranks guesses: a card is called safe only when no matching board puts a Voltorb there. |
| Strategy | `backend/strategy.py` | `SafeFirst` flips every surely-safe card that could still be a 2 or 3, all in one batch. With none left, it guesses the card least likely to be a Voltorb. `Strategy` is a protocol, so other strategies can be swapped in. |
| Game | `backend/game.py` | `Game` holds a round: `reveal()` takes a flip result, `recommend()` gives the next batch, and `snapshot()` returns the state as JSON. |

The web UI (`frontend/app.py`) is stateless. Each request sends the counters and every flip so far
to `POST /api/solve`.

## Why it sometimes guesses
The counters don't always pin down one board. These two boards show the same counter on every row
and column:

```
1 1 0 1 2      1 1 2 1 0
1 1 2 2 0      1 1 0 2 2
1 1 1 1 1      1 1 1 1 1
1 1 0 0 0      1 1 0 0 0
3 2 1 1 0      3 2 1 1 0
```

They differ only in the 0/2 rectangle in the top right. Every other card is the same in both, so
flipping those cards can never tell the boards apart. To win you must flip the 2's in that rectangle,
and each of its four cards is a Voltorb in one of the two boards. That's a 50/50 no method can avoid
(`tests/test_guessing.py`).

How often this happens doesn't depend on the order of safe flips: flipping every surely-safe card
always reaches the same point. On boards dealt the way the game deals them, 60% of Lv. 1 boards and
95% of Lv. 7-8 boards force at least one guess (table below).

## Win odds
`scripts/win_odds.py` deals boards the way the game does and plays each one by flipping exactly what
the solver recommends. Results from 2000 boards per level (±2% at 95% confidence):

| Level | Win, Lv. entered | Win, Lv. blank | Win, no level tables | Boards that need a guess | Guesses per board |
| --- | --- | --- | --- | --- | --- |
| 1 | 82.3% | 82.3% | 82.5% | 60.0% | 0.97 |
| 2 | 66.3% | 66.3% | 67.0% | 81.7% | 2.09 |
| 3 | 54.5% | 54.5% | 53.8% | 88.8% | 2.91 |
| 4 | 46.5% | 46.1% | 45.0% | 91.8% | 3.28 |
| 5 | 36.0% | 35.8% | 34.9% | 94.2% | 3.87 |
| 6 | 35.4% | 35.0% | 35.0% | 93.3% | 3.70 |
| 7 | 26.1% | 25.8% | 25.1% | 95.3% | 4.22 |
| 8 | 29.1% | 28.7% | 26.5% | 95.1% | 4.16 |

The level tables only re-rank guesses, so they move the win rate by about 0-3 points. Nearly all of
each loss comes from boards where the counters leave a real coin toss.

```bash
python scripts/win_odds.py --boards 2000   # about 5 minutes on 16 cores
```

## Tests
```bash
python -m pytest            # everything
python -m pytest -m "not browser"
```
- `test_manual_assertions.py`: the hand-worked v/c/z table in `tests/manual_assertions.txt`, with
  every cell allowed any option
- `test_set_options.py`, `test_cell_set.py`: limited `set_options` and per-cell options, including the
  [3,1] -> [2,2] cases, each checked against brute force
- `test_analysis.py`: board odds and level weights against brute-force enumeration
- `test_game.py`: simulated games at every level. A safe flip is never a Voltorb, and a loss only
  comes from a guess.
- `test_e2e_game1.py`: the game in progress when this was written, played against its answer through
  the backend and the CLI
- `test_guessing.py`: the two boards above, showing the solver ends on a 50/50
- `test_sprites.py`: the checked-in sprites match `scripts/make_sprites.py`
- `test_app.py`, `test_browser.py`: the API, then the real page in Chrome via Playwright, driven by
  keyboard. Browser tests skip if Playwright or a Chrome/Chromium is missing.
