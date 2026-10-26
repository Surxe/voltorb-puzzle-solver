"""The checked-in sprites are exactly what scripts/make_sprites.py draws, and the page only asks for those"""
import re
import struct
from pathlib import Path

from scripts import make_sprites

FRONTEND = Path(__file__).resolve().parent.parent / 'frontend'

def test_checked_in_sprites_are_up_to_date():
    assert make_sprites.stale() == [], "run: python scripts/make_sprites.py"

def test_sprites_are_valid_pngs_of_the_drawn_size():
    for name, draw in make_sprites.SPRITES.items():
        data = (make_sprites.DEST / f'{name}.png').read_bytes()
        assert data.startswith(b'\x89PNG\r\n\x1a\n')
        canvas = draw()
        assert struct.unpack('>II', data[16:24]) == (canvas.width, canvas.height)

def test_every_sprite_the_page_uses_exists():
    template = (FRONTEND / 'templates' / 'index.html').read_text(encoding='utf-8')
    script = (FRONTEND / 'static' / 'solver.js').read_text(encoding='utf-8')
    used = set(re.findall(r"sprites/(\w+)\.png", template))
    used |= {f'memo_{k}' for k in range(4)} # the template builds these names in a loop
    used |= set(re.findall(r"sprite\('(\w+)'\)", script)) | set(re.findall(r"'(card_\d)'", script))
    assert used <= set(make_sprites.SPRITES)
    assert {'card_back', 'card_0', 'card_3', 'cursor', 'bomb_small', 'favicon'} <= used
