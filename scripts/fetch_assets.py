"""
Downloads the HeartGold/SoulSilver Voltorb Flip sprites and DS fonts the frontend draws with, into
frontend/static/game/ (gitignored: they're Nintendo's art, ripped by others, so they're fetched rather than
checked in). Sources are pinned to exact commits so the files never shift under the layout.

    python scripts/fetch_assets.py [--force]
"""
import argparse
import urllib.request
from pathlib import Path

DEST = Path(__file__).resolve().parent.parent / 'frontend' / 'static' / 'game'

# GPL-3.0, sprites ripped from the game: https://github.com/samualtnorman/voltorb-flip
SPRITES = 'https://raw.githubusercontent.com/samualtnorman/voltorb-flip/cc0f30db5b4ec6c891efde57e368e4a02f6f98be/src/assets/'
# MIT, DS fonts: https://github.com/danielbWork/Voltorb-Flip
FONTS = 'https://raw.githubusercontent.com/danielbWork/Voltorb-Flip/2f569b2a4cb2293879760949cfa24e7652ce1c23/assets/fonts/'

ASSETS = {
    # dest path under DEST: source url
    'background.png': SPRITES + 'background.png',
    'favicon.png': SPRITES + 'favicon.png',
    **{f'tile/{name}.png': SPRITES + f'tile/{name}.png' for name in ('blank', 'voltorb', '1', '2', '3', 'hover')},
    **{f'memo/{n}.png': SPRITES + f'memo/{n}.png' for n in range(4)},
    **{f'number/{style}_{n}.png': SPRITES + f'number/{style}_{n}.png' for style in ('bold', 'big') for n in range(10)},
    **{f'number/thin_{n}.png': SPRITES + f'number/thin_{n}.png' for n in range(1, 9)},
    **{f'frame/{name}.png': SPRITES + f'frame/{name}.png' for name in ('frame', 'hover_0', 'hover_1', 'hover_2')},
    'fonts/pokemon-ds.ttf': FONTS + 'pokemon-ds-font.ttf',
}

MAGIC = {'.png': b'\x89PNG\r\n\x1a\n', '.ttf': b'\x00\x01\x00\x00'}

def missing(dest=DEST) -> list[str]:
    return [path for path in ASSETS if not (dest / path).is_file()]

def fetch(force=False, dest=DEST, log=print) -> int:
    """Downloads every asset not already present (all of them with force); returns how many were written"""
    written = 0
    for path, url in ASSETS.items():
        target = dest / path
        if target.is_file() and not force:
            continue
        with urllib.request.urlopen(url, timeout=30) as response:
            data = response.read()
        if not data.startswith(MAGIC[target.suffix]):
            raise ValueError(f"{url} is not a {target.suffix} file")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        written += 1
        log(f"fetched {path}")
    return written


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument('--force', action='store_true', help="re-download assets that are already present")
    args = parser.parse_args()
    count = fetch(force=args.force)
    print(f"{count} asset(s) written to {DEST}" if count else f"all {len(ASSETS)} assets already in {DEST}")
