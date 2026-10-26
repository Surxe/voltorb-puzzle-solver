"""
The web UI driven in a real browser, keyboard first: Tab through the counters, Enter to solve, type each flip.
Skipped without playwright or a Chromium/Chrome to drive.
"""
import threading

import pytest

playwright = pytest.importorskip('playwright.sync_api')
from werkzeug.serving import make_server

from frontend.app import create_app

pytestmark = pytest.mark.browser

@pytest.fixture(scope='module')
def server():
    httpd = make_server('127.0.0.1', 0, create_app())
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f'http://127.0.0.1:{httpd.server_port}/'
    httpd.shutdown()

@pytest.fixture(scope='module')
def browser():
    with playwright.sync_playwright() as p:
        for launch in ({}, {'channel': 'chrome'}, {'channel': 'chromium'}):
            try:
                browser = p.chromium.launch(**launch)
                break
            except playwright.Error:
                continue
        else:
            pytest.skip('no Chromium/Chrome for playwright to drive')
        yield browser
        browser.close()

@pytest.fixture
def page(browser, server):
    context = browser.new_context(viewport={'width': 1100, 'height': 900})
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(error))
    page.goto(server)
    yield page
    context.close()
    assert not errors

def enter_counts(page, rows, cols):
    for value, voltorbs in [*rows, *cols]:
        page.keyboard.type(str(value))
        page.keyboard.press('Tab')
        page.keyboard.type(str(voltorbs))
        page.keyboard.press('Tab')

def pending(page):
    return page.eval_on_selector_all('.tile.pending', 'tiles => tiles.map(t => [+t.dataset.i, +t.dataset.j])')

def type_flips(page, answer, flips):
    for k, (i, j) in enumerate(flips):
        page.keyboard.type(str(answer[i][j]))
        if k < len(flips) - 1:
            page.keyboard.press('Tab')

def submit(page, key='Enter'):
    """Presses key and waits until the solver's answer is drawn"""
    with page.expect_response('**/api/solve'):
        page.keyboard.press(key)
    page.wait_for_selector('#app[aria-busy="false"]')

def message(page):
    return page.inner_text('#message')

def coins(page, id):
    return int(page.inner_text(f'#{id}'))

def focused(page):
    return page.evaluate('document.activeElement.getAttribute("aria-label") || document.activeElement.textContent')

def tab_cycle(page, presses, key='Tab'):
    """What gets focus over a run of key presses, starting with what has it now"""
    seen = [focused(page)]
    for _ in range(presses):
        page.keyboard.press(key)
        seen.append(focused(page))
    return seen

def assert_unobscured(page):
    """The focused element is on screen and is what a click at its center would hit"""
    hit = page.evaluate("""() => {
        const element = document.activeElement, box = element.getBoundingClientRect();
        const x = box.left + box.width / 2, y = box.top + box.height / 2;
        return x >= 0 && y >= 0 && x <= innerWidth && y <= innerHeight && document.elementFromPoint(x, y) === element;
    }""")
    assert hit, f'{focused(page)} is off screen or covered'

def test_tab_cycles_only_the_counters_at_the_start(page):
    seen = tab_cycle(page, 21)
    assert seen[:4] == ['Row 1 points', 'Row 1 Voltorbs', 'Row 2 points', 'Row 2 Voltorbs']
    assert seen[10:12] == ['Column 1 points', 'Column 1 Voltorbs']
    assert seen[19] == 'Column 5 Voltorbs'
    assert seen[20:] == ['Row 1 points', 'Row 1 Voltorbs'] # wraps instead of leaving for the menu or cards
    assert tab_cycle(page, 2, 'Shift+Tab')[1:] == ['Row 1 points', 'Column 5 Voltorbs']

def test_tab_cycles_only_the_cards_to_flip(page, game1):
    rows, cols, answer = game1
    enter_counts(page, rows, cols)
    submit(page)
    flips = pending(page)
    labels = [f'Row {i + 1} column {j + 1}: what the card showed (0 for a Voltorb)' for i, j in flips]
    assert tab_cycle(page, len(flips)) == labels + labels[:1]
    type_flips(page, answer, flips)
    submit(page)
    flips = pending(page)
    labels = [f'Row {i + 1} column {j + 1}: what the card showed (0 for a Voltorb)' for i, j in flips]
    assert tab_cycle(page, len(flips)) == labels + labels[:1]
    # a card clicked by hand joins the cycle
    page.click('.tile[data-i="0"][data-j="4"]')
    assert 'Row 1 column 5: what the card showed (0 for a Voltorb)' in tab_cycle(page, len(flips) + 1)

def test_tab_cycles_only_the_menu_once_the_round_is_over(page, game1):
    rows, cols, answer = game1
    enter_counts(page, rows, cols)
    submit(page)
    while flips := pending(page):
        type_flips(page, answer, flips)
        submit(page)
    assert tab_cycle(page, 2) == ['New game', 'Back', 'New game']

def test_what_has_focus_is_never_hidden(page, game1):
    rows, cols, answer = game1
    for _ in range(20):
        assert_unobscured(page)
        assert page.evaluate('getComputedStyle(document.activeElement).backgroundColor') == 'rgb(255, 216, 74)' # gold
        page.keyboard.press('Tab')
    enter_counts(page, rows, cols)
    submit(page)
    for _ in pending(page):
        assert_unobscured(page)
        tile = page.evaluate_handle('document.activeElement.parentElement')
        assert tile.evaluate('t => getComputedStyle(t.querySelector(".focus-cursor")).display') == 'block'
        page.keyboard.press('Tab')

def test_counters_keep_only_what_fits(page):
    page.keyboard.type('17') # a row holds at most 15 points
    assert page.evaluate('document.activeElement.value') == '7'
    page.keyboard.press('Tab')
    page.keyboard.type('9') # and at most 5 voltorbs
    assert page.evaluate('document.activeElement.value') == ''

def test_plays_game1_with_the_keyboard(page, game1):
    rows, cols, answer = game1
    enter_counts(page, rows, cols)
    submit(page)
    batches = []
    while flips := pending(page):
        batches.append(flips)
        assert 'Flip the' in message(page)
        type_flips(page, answer, flips)
        submit(page)
    assert batches == [[[0, 2], [2, 2], [3, 2], [4, 2]], [[0, 1], [3, 1]]]
    assert message(page).startswith('Game clear!')
    assert coins(page, 'current-coins') == 24
    assert coins(page, 'total-coins') == 24
    assert page.eval_on_selector_all('.tile.revealed', 'tiles => tiles.length') == 6

def test_back_undoes_the_last_batch(page, game1):
    rows, cols, answer = game1
    enter_counts(page, rows, cols)
    submit(page)
    first = pending(page)
    type_flips(page, answer, first)
    submit(page)
    assert pending(page) != first
    with page.expect_response('**/api/solve'):
        page.get_by_role('button', name='Back').click()
    page.wait_for_selector('#app[aria-busy="false"]')
    assert page.eval_on_selector_all('.tile.revealed', 'tiles => tiles.length') == 0
    assert pending(page) == first

def test_found_all_ends_the_round(page, game1):
    rows, cols, answer = game1
    enter_counts(page, rows, cols)
    submit(page)
    type_flips(page, answer, pending(page))
    submit(page)
    page.get_by_role('button', name='Found all 2s & 3s').click()
    assert message(page).startswith('Game clear!')
    assert pending(page) == []
    assert coins(page, 'total-coins') == coins(page, 'current-coins') == 1 * 2 * 1 * 3 # the first batch

def test_impossible_flip_is_reported_and_not_kept(page, game1):
    rows, cols, _ = game1
    enter_counts(page, rows, cols)
    submit(page)
    flips = pending(page)
    page.keyboard.type('3') # (0, 2) can only be 1 or 2
    for _ in flips[1:]:
        page.keyboard.press('Tab')
        page.keyboard.type('1')
    submit(page)
    assert message(page).startswith('No board fits')
    assert pending(page) == flips
    assert page.eval_on_selector_all('.tile.revealed', 'tiles => tiles.length') == 0

def test_missing_counter_is_pointed_out(page):
    enter_counts(page, [(5, 1), (4, 1)], [])
    page.keyboard.press('Enter')
    assert message(page) == "Enter row 3's points."
    assert page.evaluate('document.activeElement.getAttribute("aria-label")') == 'Row 3 points'

def test_clicking_a_card_enters_a_flip_by_hand(page, game1):
    rows, cols, answer = game1
    enter_counts(page, rows, cols)
    submit(page)
    flips = pending(page)
    page.click('.tile[data-i="0"][data-j="4"]') # a certain 1 the solver wouldn't ask for
    page.keyboard.type('1')
    for i, j in flips:
        page.fill(f'.tile[data-i="{i}"][data-j="{j}"] .flip', str(answer[i][j]))
    submit(page)
    assert page.eval_on_selector_all('.tile.revealed', 'tiles => tiles.length') == 5
    assert page.get_attribute('.tile[data-i="0"][data-j="4"]', 'class').split().count('revealed') == 1
