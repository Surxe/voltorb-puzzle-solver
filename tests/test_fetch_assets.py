"""The asset fetcher, with the network swapped for canned files"""
import io

import pytest

from scripts import fetch_assets

def fake_urlopen(payload_for):
    def urlopen(url, timeout):
        return io.BytesIO(payload_for(url))
    return urlopen

def valid_file(url):
    return fetch_assets.MAGIC['.ttf' if url.endswith('.ttf') else '.png'] + b'rest of file'

def test_fetches_everything_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(fetch_assets.urllib.request, 'urlopen', fake_urlopen(valid_file))
    assert fetch_assets.missing(tmp_path) == list(fetch_assets.ASSETS)
    assert fetch_assets.fetch(dest=tmp_path, log=lambda _: None) == len(fetch_assets.ASSETS)
    assert fetch_assets.missing(tmp_path) == []
    assert (tmp_path / 'tile' / 'voltorb.png').read_bytes().startswith(b'\x89PNG')
    # already present: nothing to do unless forced
    assert fetch_assets.fetch(dest=tmp_path, log=lambda _: None) == 0
    assert fetch_assets.fetch(force=True, dest=tmp_path, log=lambda _: None) == len(fetch_assets.ASSETS)

def test_rejects_files_that_are_not_what_they_claim(tmp_path, monkeypatch):
    monkeypatch.setattr(fetch_assets.urllib.request, 'urlopen', fake_urlopen(lambda url: b'<html>404</html>'))
    with pytest.raises(ValueError):
        fetch_assets.fetch(dest=tmp_path, log=lambda _: None)
    assert not any(tmp_path.rglob('*.png'))

def test_layout_assets_are_listed():
    """Every sprite the page draws comes from the manifest"""
    for path in ['background.png', 'tile/blank.png', 'tile/hover.png', 'frame/frame.png', 'fonts/pokemon-ds.ttf',
                 *(f'memo/{k}.png' for k in range(4)), *(f'number/bold_{n}.png' for n in range(10)),
                 *(f'number/big_{n}.png' for n in range(10)), *(f'number/thin_{n}.png' for n in range(1, 9))]:
        assert path in fetch_assets.ASSETS
