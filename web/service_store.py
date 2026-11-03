"""Private operational data, separate from real-estate analytics. No raw request logging."""
import hashlib
import hmac
import json
import secrets
import sqlite3
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

PLANS = {
    'free': {'name': '무료 회원', 'daily_recommendations': 3, 'scheduled_reports': False, 'advanced_match': False},
    'plus': {'name': 'Plus · 출시 준비', 'daily_recommendations': 30, 'scheduled_reports': True, 'advanced_match': True},
    'qa': {'name': '테스트 계정', 'daily_recommendations': None, 'scheduled_reports': False, 'advanced_match': False},
}
EVENTS = {'calculator_started': {}, 'calculator_completed': {'scenario': str},
          'match_step_completed': {'step': int}, 'login_opened': {},
          'recommendation_completed': {'result_count': int, 'engine_version': str},
          'apartment_saved': {}, 'logout': {}}


class Store:
    def __init__(self, location):
        self.location = location
        self.postgres = location.startswith(('postgres://', 'postgresql://'))
        if not self.postgres:
            Path(location).parent.mkdir(parents=True, exist_ok=True)
        with self.db() as cx:
            for statement in SCHEMA:
                self.execute(cx, statement)
            if self.postgres:
                self.execute(cx, "ALTER TABLE app_sessions ADD COLUMN IF NOT EXISTS auth_mode TEXT NOT NULL DEFAULT 'local'")
            elif 'auth_mode' not in [r['name'] for r in cx.execute('PRAGMA table_info(app_sessions)')]:
                cx.execute("ALTER TABLE app_sessions ADD COLUMN auth_mode TEXT NOT NULL DEFAULT 'local'")
            if self.postgres:
                # Only the server DB connection may access operational records.
                for table in ['app_users', 'app_sessions', 'app_usage', 'app_saved', 'app_events', 'app_limits', 'app_audit']:
                    self.execute(cx, f'ALTER TABLE {table} ENABLE ROW LEVEL SECURITY')
                    self.execute(cx, f'REVOKE ALL ON TABLE {table} FROM anon, authenticated')

    @contextmanager
    def db(self):
        if self.postgres:
            import psycopg
            from psycopg.rows import dict_row
            cx = psycopg.connect(self.location, row_factory=dict_row, connect_timeout=8)
        else:
            cx = sqlite3.connect(self.location, timeout=15)
            cx.row_factory = sqlite3.Row
            cx.execute('PRAGMA foreign_keys=ON')
        try:
            yield cx
            cx.commit()
        except Exception:
            cx.rollback()
            raise
        finally:
            cx.close()

    def execute(self, cx, sql, args=()):
        return cx.execute(sql.replace('?', '%s') if self.postgres else sql, args)

    def register(self, email, password):
        email = email.strip().lower()
        if len(email) > 254 or '@' not in email or not 10 <= len(password) <= 128:
            raise ValueError('이메일과 10~128자 비밀번호를 확인하세요.')
        salt = secrets.token_hex(16)
        hashed = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1).hex()
        user = {'id': str(uuid.uuid4()), 'email': email}
        try:
            with self.db() as cx:
                self.execute(cx, 'INSERT INTO app_users(id,email,password_hash,salt,plan) VALUES(?,?,?,?,?)',
                             (user['id'], email, hashed, salt, 'free'))
        except Exception as exc:
            if 'unique' in str(exc).lower() or 'duplicate' in str(exc).lower():
                raise ValueError('가입할 수 없는 이메일입니다.') from None
            raise
        return user

    def authenticate(self, email, password):
        with self.db() as cx:
            row = self.execute(cx, 'SELECT * FROM app_users WHERE email=?', (email.strip().lower(),)).fetchone()
        salt = row['salt'] if row and row['salt'] else 'dummy-salt-constant'
        hashed = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1).hex()
        if row and hmac.compare_digest(hashed, row['password_hash']):
            return {'id': row['id'], 'email': row['email']}
        return None

    def external_user(self, uid, email):
        # An authenticated Supabase subject, never a subject supplied by the request body.
        with self.db() as cx:
            self.execute(cx, 'INSERT INTO app_users(id,email,password_hash,salt,plan) VALUES(?,?,?,?,?) ON CONFLICT(id) DO NOTHING',
                         (uid, email, '', '', 'free'))
        return {'id': uid, 'email': email}

    def create_session(self, uid, auth_mode='local'):
        token, csrf = secrets.token_urlsafe(36), secrets.token_urlsafe(24)
        with self.db() as cx:
            self.execute(cx, 'INSERT INTO app_sessions(token_hash,user_id,csrf,expires,auth_mode) VALUES(?,?,?,?,?)',
                         (hashlib.sha256(token.encode()).hexdigest(), uid, csrf, time.time() + 604800, auth_mode))
        return token, csrf

    def session(self, token):
        if not token or len(token) > 256:
            return None
        with self.db() as cx:
            row = self.execute(cx, 'SELECT s.csrf,s.auth_mode,u.id,u.email FROM app_sessions s JOIN app_users u ON s.user_id=u.id WHERE s.token_hash=? AND s.expires>?',
                               (hashlib.sha256(token.encode()).hexdigest(), time.time())).fetchone()
        return {'user': {'id': row['id'], 'email': row['email']}, 'csrf': row['csrf'], 'auth_mode': row['auth_mode']} if row else None

    def logout(self, token):
        with self.db() as cx:
            self.execute(cx, 'DELETE FROM app_sessions WHERE token_hash=?', (hashlib.sha256(token.encode()).hexdigest(),))

    def entitlements(self, uid):
        day = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        with self.db() as cx:
            user = self.execute(cx, 'SELECT plan FROM app_users WHERE id=?', (uid,)).fetchone()
            usage = self.execute(cx, 'SELECT used FROM app_usage WHERE user_id=? AND day=?', (uid, day)).fetchone()
        plan = user['plan'] if user and user['plan'] in PLANS else 'free'
        unlimited = PLANS[plan]['daily_recommendations'] is None
        return dict(plan=plan, features=PLANS[plan], unlimited=unlimited, remaining=None if unlimited else max(0, PLANS[plan]['daily_recommendations'] - (usage['used'] if usage else 0)),
                    resets='UTC 00:00 / 한국시간 09:00', billing_enabled=False)

    def reserve_recommendation(self, uid):
        day = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        with self.db() as cx:
            user = self.execute(cx, 'SELECT plan FROM app_users WHERE id=?', (uid,)).fetchone()
            limit = PLANS.get(user['plan'] if user else 'free', PLANS['free'])['daily_recommendations']
            self.execute(cx, 'INSERT INTO app_usage(user_id,day,used) VALUES(?,?,0) ON CONFLICT(user_id,day) DO NOTHING', (uid, day))
            if limit is None:
                return self.execute(cx, 'UPDATE app_usage SET used=used+1 WHERE user_id=? AND day=?', (uid, day)).rowcount == 1
            return self.execute(cx, 'UPDATE app_usage SET used=used+1 WHERE user_id=? AND day=? AND used<?', (uid, day, limit)).rowcount == 1

    def refund_recommendation(self, uid):
        day = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        with self.db() as cx:
            self.execute(cx, 'UPDATE app_usage SET used=used-1 WHERE user_id=? AND day=? AND used>0', (uid, day))

    def save_item(self, uid, kind, key, payload):
        if kind not in ('apartment', 'budget', 'recommendation') or len(key) > 160:
            raise ValueError('지원하지 않는 저장 항목입니다.')
        raw = json.dumps(payload, ensure_ascii=False, allow_nan=False)
        if len(raw.encode()) > 200000:
            raise ValueError('저장 데이터가 너무 큽니다.')
        item = dict(id=str(uuid.uuid4()), kind=kind, item_key=key, payload=payload)
        with self.db() as cx:
            count = self.execute(cx, 'SELECT COUNT(*) AS n FROM app_saved WHERE user_id=?', (uid,)).fetchone()['n']
            if count >= 200:
                raise ValueError('저장 항목은 200개까지 보관할 수 있습니다. 먼저 일부를 삭제하세요.')
            self.execute(cx, 'INSERT INTO app_saved(id,user_id,kind,item_key,payload,created) VALUES(?,?,?,?,?,?)',
                         (item['id'], uid, kind, key, raw, time.time()))
        return item

    def saved_items(self, uid):
        with self.db() as cx:
            rows = self.execute(cx, 'SELECT id,kind,item_key,payload,created FROM app_saved WHERE user_id=? ORDER BY created DESC LIMIT 200', (uid,)).fetchall()
        return [dict(dict(row), payload=json.loads(row['payload'])) for row in rows]

    def delete_item(self, uid, item):
        with self.db() as cx:
            return self.execute(cx, 'DELETE FROM app_saved WHERE id=? AND user_id=?', (item, uid)).rowcount == 1

    def event(self, uid, data):
        name, props = data.get('event_name'), data.get('props', {})
        if name not in EVENTS or not isinstance(props, dict):
            raise ValueError('Unsupported event')
        for key, value in props.items():
            if key not in EVENTS[name] or type(value) is not EVENTS[name][key] or len(str(value)) > 80:
                raise ValueError('Unsupported event property')
        try:
            eid = str(uuid.UUID(data.get('event_id', '')))
        except (ValueError, TypeError, AttributeError):
            raise ValueError('Invalid event ID') from None
        with self.db() as cx:
            return self.execute(cx, 'INSERT INTO app_events(id,user_id,name,props,created) VALUES(?,?,?,?,?) ON CONFLICT(id) DO NOTHING',
                                (eid, uid, name, json.dumps(props), time.time())).rowcount == 1

    def events_for_test(self):
        with self.db() as cx:
            return [dict(r) for r in self.execute(cx, 'SELECT * FROM app_events').fetchall()]

    def allow_request(self, key, maximum=30, window=3600):
        bucket = str(int(time.time()) // window)
        with self.db() as cx:
            self.execute(cx, 'INSERT INTO app_limits(key,bucket,used) VALUES(?,?,0) ON CONFLICT(key,bucket) DO NOTHING', (key, bucket))
            return self.execute(cx, 'UPDATE app_limits SET used=used+1 WHERE key=? AND bucket=? AND used<?', (key, bucket, maximum)).rowcount == 1

    def prune(self):
        with self.db() as cx:
            self.execute(cx, 'DELETE FROM app_sessions WHERE expires<?', (time.time(),))
            self.execute(cx, 'DELETE FROM app_events WHERE created<?', (time.time() - 90 * 86400,))
            self.execute(cx, 'DELETE FROM app_limits WHERE bucket<?', (str(int(time.time()) // 3600 - 48),))
            self.execute(cx, 'DELETE FROM app_audit WHERE created<?', (time.time() - 30 * 86400,))

    def audit(self, route, status, elapsed_ms):
        with self.db() as cx:
            self.execute(cx, 'INSERT INTO app_audit(id,route,status,elapsed_ms,created) VALUES(?,?,?,?,?)',
                         (str(uuid.uuid4()), route, status, elapsed_ms, time.time()))

    def stats(self):
        with self.db() as cx:
            events = self.execute(cx, 'SELECT name,COUNT(*) AS count FROM app_events GROUP BY name ORDER BY name').fetchall()
            requests = self.execute(cx, 'SELECT route,status,COUNT(*) AS count FROM app_audit GROUP BY route,status ORDER BY route,status').fetchall()
        return {'events': [dict(r) for r in events], 'requests': [dict(r) for r in requests]}


SCHEMA = [
    'CREATE TABLE IF NOT EXISTS app_users(id TEXT PRIMARY KEY,email TEXT UNIQUE NOT NULL,password_hash TEXT NOT NULL,salt TEXT NOT NULL,plan TEXT NOT NULL)',
    "CREATE TABLE IF NOT EXISTS app_sessions(token_hash TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,csrf TEXT NOT NULL,expires DOUBLE PRECISION NOT NULL,auth_mode TEXT NOT NULL DEFAULT 'local')",
    'CREATE TABLE IF NOT EXISTS app_usage(user_id TEXT NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,day TEXT NOT NULL,used INTEGER NOT NULL,PRIMARY KEY(user_id,day))',
    'CREATE TABLE IF NOT EXISTS app_saved(id TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,kind TEXT NOT NULL,item_key TEXT NOT NULL,payload TEXT NOT NULL,created DOUBLE PRECISION NOT NULL)',
    'CREATE TABLE IF NOT EXISTS app_events(id TEXT PRIMARY KEY,user_id TEXT,name TEXT NOT NULL,props TEXT NOT NULL,created DOUBLE PRECISION NOT NULL)',
    'CREATE TABLE IF NOT EXISTS app_limits(key TEXT NOT NULL,bucket TEXT NOT NULL,used INTEGER NOT NULL,PRIMARY KEY(key,bucket))',
    'CREATE TABLE IF NOT EXISTS app_audit(id TEXT PRIMARY KEY,route TEXT NOT NULL,status INTEGER NOT NULL,elapsed_ms DOUBLE PRECISION NOT NULL,created DOUBLE PRECISION NOT NULL)',
]
