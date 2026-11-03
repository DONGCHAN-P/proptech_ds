import json
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from web.budget import calculate, monthly_payment
from web.service_store import Store


def sample(**changes):
    values = dict(cash=20000, reserve=2000, annual_income=7000, monthly_income=450,
                  monthly_expenses=180, existing_payment=30, rate=4, years=30,
                  ltv=60, dsr=40, stress=1.5, cost_rate=2.5, fixed_cost=300,
                  payment_share=70, method='annuity')
    return dict(values, **changes)


def test_budget_respects_cash_ltv_dsr_and_monthly_capacity():
    result = calculate(sample())
    for row in result['scenarios']:
        assert row['loan'] <= row['price'] * .6 + .01
        assert row['price'] + row['costs'] - row['loan'] <= 18000 + .01
        assert row['monthly_payment'] <= (450 - 180 - 30) * .7 + .01
        assert monthly_payment(row['loan'], 5.5, 30, 'annuity') * 12 + 360 <= 2800 + .02
    assert result['policy_mode'] == 'user_assumptions'


def test_zero_interest_and_no_payment_capacity():
    assert monthly_payment(36000, 0, 30, 'annuity') == 100
    result = calculate(sample(existing_payment=1000))
    assert result['scenarios'][1]['loan'] == 0
    assert calculate(sample(cash=1000, reserve=2000))['scenarios'][1]['price'] == 0
    with pytest.raises(ValueError):
        calculate(sample(rate=-1))
    with pytest.raises(ValueError):
        calculate(sample(cash=float('nan')))


def test_equal_principal_uses_first_month_as_payment_limit():
    assert monthly_payment(36000, 4, 30, 'principal') == 220
    result = calculate(sample(method='principal'))
    assert result['scenarios'][1]['monthly_payment'] <= calculate(sample())['monthly_capacity'] + .01


@pytest.fixture
def store(tmp_path):
    return Store(str(tmp_path / 'service.sqlite3'))


def test_accounts_password_sessions_and_owner_isolation(store):
    alice = store.register('alice@example.test', 'long-enough-password')
    bob = store.register('bob@example.test', 'another-long-password')
    assert store.authenticate('alice@example.test', 'wrong-password') is None
    assert store.authenticate('alice@example.test', 'long-enough-password')['id'] == alice['id']
    token, csrf = store.create_session(alice['id'])
    assert store.session(token)['user']['id'] == alice['id']
    assert store.session(token)['csrf'] == csrf
    saved = store.save_item(alice['id'], 'apartment', 'unit-1', {'label': 'safe label'})
    assert store.saved_items(bob['id']) == []
    assert not store.delete_item(bob['id'], saved['id'])
    assert store.delete_item(alice['id'], saved['id'])
    store.logout(token)
    assert store.session(token) is None


def test_quota_atomic_and_paid_permissions_not_self_granted(store):
    user = store.register('quota@example.test', 'long-enough-password')
    def consume(_):
        return store.reserve_recommendation(user['id'])
    with ThreadPoolExecutor(max_workers=6) as pool:
        reservations = list(pool.map(consume, range(8)))
    assert sum(bool(x) for x in reservations) == 3
    assert not store.entitlements(user['id'])['features']['scheduled_reports']
    assert store.entitlements(user['id'])['remaining'] == 0
    store.refund_recommendation(user['id'])
    assert store.entitlements(user['id'])['remaining'] == 1


def test_event_allowlist_no_financial_payload_or_forged_identity(store):
    event = {'event_id': '0348712e-54ab-4c6e-afc3-71267fc9d840',
             'event_name': 'calculator_completed', 'props': {'cash': 999999, 'salary': 123},
             'user_id': 'forged'}
    with pytest.raises(ValueError):
        store.event(None, event)
    event['props'] = {'scenario': 'base'}
    assert store.event(None, event)
    assert not store.event(None, event)
    row = store.events_for_test()[0]
    assert row['user_id'] is None
    assert '999999' not in json.dumps(row)
    assert '123' not in json.dumps(row)


def test_saved_items_remain_visible_after_one_hundred_saves(store):
    user = store.register('saved@example.test', 'long-enough-password')
    first = store.save_item(user['id'], 'apartment', 'first', {})
    for number in range(101):
        store.save_item(user['id'], 'apartment', str(number), {})
    assert first['id'] in {row['id'] for row in store.saved_items(user['id'])}
def test_internal_qa_plan_has_no_recommendation_limit(tmp_path):
    from web.service_store import Store
    store = Store(str(tmp_path / 'qa.sqlite3'))
    user = store.register('qa@example.invalid', 'test-password-123')
    with store.db() as cx:
        store.execute(cx, "UPDATE app_users SET plan='qa' WHERE id=?", (user['id'],))
    for _ in range(40):
        assert store.reserve_recommendation(user['id'])
    assert store.entitlements(user['id'])['remaining'] is None
    assert store.entitlements(user['id'])['unlimited'] is True

