"""
Draws the web UI's pixel-art sprites (original art, no game assets) into frontend/static/sprites/.
The PNGs are checked in; tests/test_sprites.py fails if they drift from what this script draws.

    python scripts/make_sprites.py [--check]
"""
import argparse
import struct
import sys
import zlib
from pathlib import Path

DEST = Path(__file__).resolve().parent.parent / 'frontend' / 'static' / 'sprites'

Color = tuple[int, int, int, int]

def rgb(hex_color: str) -> Color:
    return (int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16), 255)

CLEAR: Color = (0, 0, 0, 0)
INK = rgb('#2b2b33')
CARD_EDGE, CARD_FACE, CARD_LIGHT, CARD_SHADE = rgb('#6b4a2e'), rgb('#f2dfb8'), rgb('#fff5dc'), rgb('#d6bb8a')
BACK_EDGE, BACK_DARK, BACK_LIGHT, BACK_SHINE = rgb('#123d26'), rgb('#25804c'), rgb('#2f9a5c'), rgb('#4cbf7c')
BOMB_EDGE, BOMB_BODY, BOMB_SHINE = rgb('#16162a'), rgb('#3b4170'), rgb('#9aa2e6')
FUSE, SPARK, SPARK_HOT = rgb('#9a6a3a'), rgb('#ffd84a'), rgb('#ff6b3d')
MEMO = rgb('#ffd84a')
CURSOR, CURSOR_EDGE = rgb('#ff4d3a'), rgb('#7a1d12')

# digit bitmaps: '#' is ink
SMALL_DIGITS = { # 3x5, for the memo marks
    1: ['.#.', '##.', '.#.', '.#.', '###'],
    2: ['##.', '..#', '.#.', '#..', '###'],
    3: ['##.', '..#', '.#.', '..#', '##.'],
}
BIG_DIGITS = { # 5x7, drawn at 2x on card faces
    1: ['..#..', '.##..', '..#..', '..#..', '..#..', '..#..', '.###.'],
    2: ['.###.', '#...#', '....#', '...#.', '..#..', '.#...', '#####'],
    3: ['####.', '....#', '....#', '.###.', '....#', '....#', '####.'],
}

class Canvas:
    def __init__(self, width, height, fill: Color = CLEAR):
        self.width, self.height = width, height
        self.pixels = [[fill] * width for _ in range(height)]

    def put(self, x, y, color: Color):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.pixels[y][x] = color

    def rect(self, x, y, width, height, color: Color):
        for yy in range(y, y + height):
            for xx in range(x, x + width):
                self.put(xx, yy, color)

    def frame(self, x, y, width, height, color: Color, thickness=1):
        self.rect(x, y, width, thickness, color)
        self.rect(x, y + height - thickness, width, thickness, color)
        self.rect(x, y, thickness, height, color)
        self.rect(x + width - thickness, y, thickness, height, color)

    def bitmap(self, rows: list[str], x, y, color: Color, scale=1):
        for dy, row in enumerate(rows):
            for dx, char in enumerate(row):
                if char == '#':
                    self.rect(x + dx * scale, y + dy * scale, scale, scale, color)

    def disc(self, cx, cy, radius, fill: Color, edge: Color):
        """A filled circle centered between pixels at (cx, cy), with a 1px edge"""
        def inside(x, y):
            return (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= radius ** 2
        for y in range(self.height):
            for x in range(self.width):
                if inside(x, y):
                    on_edge = not all(inside(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                    self.put(x, y, edge if on_edge else fill)

    def paste(self, other: 'Canvas', x, y):
        for dy, row in enumerate(other.pixels):
            for dx, color in enumerate(row):
                if color[3]:
                    self.put(x + dx, y + dy, color)

    def png(self) -> bytes:
        def chunk(kind, data):
            return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
        raw = b''.join(b'\x00' + bytes(channel for color in row for channel in color) for row in self.pixels)
        header = struct.pack('>IIBBBBB', self.width, self.height, 8, 6, 0, 0, 0) # 8-bit RGBA
        return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', header) + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b'')

# ---------- sprites ----------

def bomb(size) -> Canvas:
    """A round bomb with a lit fuse: the Voltorb stand-in"""
    canvas = Canvas(size, size)
    radius = size * 0.36
    cx, cy = size * 0.45, size * 0.58
    canvas.disc(cx, cy, radius, BOMB_BODY, BOMB_EDGE)
    shine = max(1, size // 8)
    canvas.rect(round(cx - radius * 0.5), round(cy - radius * 0.55), shine, shine, BOMB_SHINE)
    # fuse from the top right of the body, ending in a spark
    top_x, top_y = round(cx + radius * 0.55), round(cy - radius * 0.85)
    fuse = max(1, size // 8)
    for step in range(fuse + 1):
        canvas.put(top_x + step, top_y - step, FUSE)
    spark_x, spark_y = top_x + fuse + 1, top_y - fuse - 1
    canvas.put(spark_x, spark_y, SPARK_HOT)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        canvas.put(spark_x + dx, spark_y + dy, SPARK)
    return canvas

def card_back() -> Canvas:
    canvas = Canvas(24, 24, BACK_EDGE)
    for y in range(1, 23):
        for x in range(1, 23):
            canvas.put(x, y, BACK_LIGHT if ((x - 1) // 4 + (y - 1) // 4) % 2 else BACK_DARK)
    canvas.rect(1, 1, 22, 1, BACK_SHINE)
    canvas.rect(1, 1, 1, 22, BACK_SHINE)
    return canvas

def card_face(value) -> Canvas:
    canvas = Canvas(24, 24, CARD_EDGE)
    canvas.rect(1, 1, 22, 22, CARD_FACE)
    canvas.rect(1, 1, 22, 1, CARD_LIGHT)
    canvas.rect(1, 1, 1, 22, CARD_LIGHT)
    canvas.rect(1, 22, 22, 1, CARD_SHADE)
    canvas.rect(22, 1, 1, 22, CARD_SHADE)
    if value == 0:
        canvas.paste(bomb(18), 3, 3)
    else:
        canvas.bitmap(BIG_DIGITS[value], 7, 5, INK, scale=2)
    return canvas

def memo(value) -> Canvas:
    """The corner mark for an option a card may still hold"""
    canvas = Canvas(5, 5)
    if value == 0:
        canvas.bitmap(['.###.', '#####', '#####', '#####', '.###.'], 0, 0, SPARK_HOT)
    else:
        canvas.bitmap(SMALL_DIGITS[value], 1, 0, MEMO)
    return canvas

def cursor() -> Canvas:
    """The frame around a card to flip"""
    canvas = Canvas(30, 30)
    canvas.frame(0, 0, 30, 30, CURSOR_EDGE)
    canvas.frame(1, 1, 28, 28, CURSOR, thickness=2)
    return canvas

def favicon() -> Canvas:
    canvas = Canvas(32, 32)
    canvas.paste(bomb(32), 0, 0)
    return canvas

SPRITES = {
    'card_back': card_back,
    **{f'card_{value}': (lambda value=value: card_face(value)) for value in range(4)},
    **{f'memo_{value}': (lambda value=value: memo(value)) for value in range(4)},
    'cursor': cursor,
    'bomb_small': lambda: bomb(10),
    'favicon': favicon,
}

def render() -> dict[str, bytes]:
    return {f'{name}.png': draw().png() for name, draw in SPRITES.items()}

def stale(dest=DEST) -> list[str]:
    """Sprites whose file is missing or differs from what this script draws"""
    return [name for name, data in render().items() if not (dest / name).is_file() or (dest / name).read_bytes() != data]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument('--check', action='store_true', help="only report sprites that are out of date")
    args = parser.parse_args()
    if args.check:
        outdated = stale()
        print('\n'.join(outdated) or 'sprites are up to date')
        sys.exit(1 if outdated else 0)
    DEST.mkdir(parents=True, exist_ok=True)
    for name, data in render().items():
        (DEST / name).write_bytes(data)
    print(f"wrote {len(SPRITES)} sprites to {DEST}")
