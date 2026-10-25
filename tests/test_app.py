import pytest

from frontend.app import create_app

@pytest.fixture
def client():
    return create_app().test_client()

def body(rows, cols, revealed=None, level=None):
    return {'rows': [list(c) for c in rows], 'cols': [list(c) for c in cols], 'revealed': revealed, 'level': level}

def test_index_has_every_input(client):
    page = client.get('/').get_data(as_text=True)
    assert page.count('class="count value"') == 10
    assert page.count('class="count voltorbs"') == 10
    assert page.count('class="flip"') == 25
    assert 'id="level"' in page

def test_plays_game1_through_the_api(client, game1):
    rows, cols, answer = game1
    revealed = [[None] * 5 for _ in range(5)]
    batches = []
    for _ in range(10):
        response = client.post('/api/solve', json=body(rows, cols, revealed, level=1))
        assert response.status_code == 200
        data = response.get_json()
        flips = data['recommendation']['flips']
        if data['status'] != 'playing':
            break
        assert data['recommendation']['safe'] is True
        batches.append(flips)
        for i, j in flips:
            revealed[i][j] = answer[i][j]
    assert data['status'] == 'won' and data['coins'] == 24 and flips == []
    assert batches == [[[0, 2], [2, 2], [3, 2], [4, 2]], [[0, 1], [3, 1]]]
    assert data['cells'][0][1] == {'options': [2], 'revealed': True, 'voltorb': 0.0, 'multiplier': 1.0}

def test_flipping_a_voltorb_loses(client, game1):
    rows, cols, _ = game1
    revealed = [[None] * 5 for _ in range(5)]
    revealed[0][0] = 0
    data = client.post('/api/solve', json=body(rows, cols, revealed)).get_json()
    assert data['status'] == 'lost' and data['coins'] == 0 and data['recommendation']['flips'] == []

def test_impossible_flip_is_a_422(client, game1):
    rows, cols, _ = game1
    revealed = [[None] * 5 for _ in range(5)]
    revealed[0][4] = 3 # column 4 is all 1's
    response = client.post('/api/solve', json=body(rows, cols, revealed))
    assert response.status_code == 422
    assert 'no' in response.get_json()['error']

@pytest.mark.parametrize('payload', [
    None,
    [],
    {'rows': [[5, 1]] * 4, 'cols': [[5, 1]] * 5},
    {'rows': [[5, 1]] * 5, 'cols': [[5, '1']] * 5},
    {'rows': [[5, 1]] * 5, 'cols': [[5, 6]] * 5},
    {'rows': [[16, 0]] * 5, 'cols': [[5, 1]] * 5},
    {'rows': [[5, 1]] * 5, 'cols': [[5, 1]] * 5, 'revealed': [[None] * 5] * 4},
    {'rows': [[5, 1]] * 5, 'cols': [[5, 1]] * 5, 'revealed': [[4] + [None] * 4] + [[None] * 5] * 4},
    {'rows': [[5, 1]] * 5, 'cols': [[5, 1]] * 5, 'level': 9},
    {'rows': [[5, 1]] * 5, 'cols': [[5, 1]] * 5, 'level': True},
])
def test_malformed_requests_are_400(client, payload):
    response = client.post('/api/solve', json=payload)
    assert response.status_code == 400
    assert response.get_json()['error']
