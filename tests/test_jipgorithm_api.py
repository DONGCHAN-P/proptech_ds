import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pytest
from fastapi.testclient import TestClient
from web.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('JIP_STORE_PATH', str(tmp_path / 'private.sqlite3'))
    monkeypatch.setenv('JIP_AUTH_MODE', 'local')
    from web.service_api import get_store
    get_store.cache_clear()
    return TestClient(app)


def signup(client, email='member@example.test'):
    result = client.post('/api/account/signup', json={'email': email, 'password': 'long-enough-password'})
    assert result.status_code == 200
    return result.json()['csrf']


def test_unauthenticated_cannot_execute_or_count_recommendations(client):
    assert client.post('/api/match', json={}).status_code == 401
    assert client.post('/api/match/count', json={}).status_code == 401
    assert client.get('/api/meta').status_code == 200


def test_map_page_allows_origin_referrer_without_private_query(client):
    response = client.get('/match.html?saved=private-saved-id')
    assert response.headers['referrer-policy'] == 'strict-origin-when-cross-origin'


def test_signup_session_csrf_saved_and_disabled_billing(client):
    csrf = signup(client)
    assert client.get('/api/account/me').json()['user']['email'] == 'member@example.test'
    assert client.post('/api/saved', json={'kind': 'apartment', 'key': '123', 'payload': {}}).status_code == 403
    headers = {'X-CSRF-Token': csrf}
    result = client.post('/api/saved', headers=headers, json={'kind': 'apartment', 'key': '123', 'payload': {'name': '단지'}})
    assert result.status_code == 200
    assert len(client.get('/api/saved').json()['items']) == 1
    assert client.post('/api/billing/checkout', headers=headers, json={}).status_code == 503
    assert client.get('/api/reports').status_code == 403
    assert client.post('/api/account/logout', headers=headers, json={}).status_code == 200
    assert client.get('/api/saved').status_code == 401


def test_no_client_plan_escalation_or_cross_origin_auth(client):
    result = client.post('/api/account/signup', headers={'Origin': 'https://evil.example'},
                         json={'email': 'x@example.test', 'password': 'long-enough-password'})
    assert result.status_code == 403
    signup(client)
    assert client.get('/api/account/me').json()['entitlements']['plan'] == 'free'
    assert client.post('/api/account/plan', json={'plan': 'plus'}).status_code in (404, 405)


def test_event_schema_audit_and_auth_cookies_do_not_echo_private_values(client):
    import uuid
    from web.service_api import get_store
    body = {'event_id': str(uuid.uuid4()), 'event_name': 'calculator_completed', 'props': {'cash': 12345678}}
    assert client.post('/api/events', json=body).status_code == 400
    body['props'] = {'scenario': 'base'}
    assert client.post('/api/events', json=body).status_code == 200
    assert '12345678' not in str(get_store().stats())
    assert get_store().stats()['requests']
    signup(client)
    cookie = client.cookies.get('jip_session')
    assert cookie and cookie not in str(get_store().stats())


def test_production_cannot_silently_use_local_auth(monkeypatch):
    from web.service_api import settings
    monkeypatch.setenv('APP_ENV', 'production')
    monkeypatch.setenv('JIP_AUTH_MODE', 'local')
    with pytest.raises(RuntimeError, match='Production requires'):
        settings()


def test_local_session_is_not_valid_after_switch_to_managed_auth(client, monkeypatch):
    signup(client)
    monkeypatch.setenv('JIP_AUTH_MODE', 'supabase')
    monkeypatch.setenv('SUPABASE_URL', 'https://example.supabase.co')
    monkeypatch.setenv('SUPABASE_ANON_KEY', 'test-public-placeholder')
    assert client.get('/api/account/me').status_code == 401
