"""Web/mobile account and entitlement boundary. Billing deliberately disabled."""
import hashlib
import hmac
import json
import os
import time
import uuid
from functools import lru_cache
from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from web.budget import calculate, VERSION
from web.service_store import Store, PLANS

router = APIRouter()
COOKIE = 'jip_session'


def settings():
    production = os.getenv('APP_ENV') == 'production'
    mode = os.getenv('JIP_AUTH_MODE', 'supabase' if production else 'local')
    url = os.getenv('SUPABASE_URL', '').rstrip('/')
    key = os.getenv('SUPABASE_ANON_KEY', '')
    database = os.getenv('DATABASE_URL') or os.getenv('JIP_STORE_PATH') or str(Path(__file__).parent / 'runtime/service.sqlite3')
    if mode not in ('local', 'supabase'):
        raise RuntimeError('Unsupported authentication mode')
    if mode == 'supabase' and (not url.startswith('https://') or not key):
        raise RuntimeError('Supabase project configuration is required')
    if production and (mode != 'supabase' or not database.startswith(('postgresql://', 'postgres://'))):
        raise RuntimeError('Production requires Supabase authentication and Postgres')
    return dict(production=production, mode=mode, url=url, key=key, database=database)


@lru_cache(maxsize=1)
def get_store():
    return Store(settings()['database'])


def startup():
    settings()
    get_store().prune()


def check_origin(request):
    origin = request.headers.get('origin')
    if origin and origin.rstrip('/') != str(request.base_url).rstrip('/'):
        raise HTTPException(403, '허용하지 않는 요청 출처입니다.')


def current(request: Request):
    authorization = request.headers.get('authorization', '')
    if authorization.startswith('Bearer '):
        cfg = settings()
        if cfg['mode'] != 'supabase':
            raise HTTPException(401, '로그인이 필요합니다.')
        try:
            result = httpx.get(cfg['url'] + '/auth/v1/user',
                               headers={'apikey': cfg['key'], 'Authorization': authorization}, timeout=8)
            data = result.json()
            if result.status_code != 200 or not data.get('id'):
                raise ValueError()
        except (httpx.HTTPError, ValueError):
            raise HTTPException(401, '인증을 확인할 수 없습니다.') from None
        user = get_store().external_user(data['id'], data.get('email', ''))
        return dict(user=user, csrf=None, bearer=True)
    session = get_store().session(request.cookies.get(COOKIE))
    if not session or session['auth_mode'] != settings()['mode']:
        raise HTTPException(401, '로그인이 필요합니다.')
    if request.method not in ('GET', 'HEAD', 'OPTIONS'):
        check_origin(request)
        if not hmac.compare_digest(request.headers.get('x-csrf-token', ''), session['csrf']):
            raise HTTPException(403, '로그인 상태를 새로고침하고 다시 시도하세요.')
    return session


def safe_error(fn):
    try:
        return fn()
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from None


@router.get('/api/service/config')
def config():
    cfg = settings()
    return dict(auth_mode=cfg['mode'], local_review=not cfg['production'], billing_enabled=False,
                budget_mode='user_assumptions', budget_version=VERSION,
                privacy='금융 입력 원문은 일반 이벤트 로그에 저장하지 않습니다. 저장함은 직접 저장한 항목만 보관합니다.')


@router.get('/api/plans')
def plans():
    return {'plans': [dict(id=k, **v, purchasable=False) for k, v in PLANS.items() if k != 'qa'], 'billing_enabled': False}


def account_action(action, payload, request, response):
    check_origin(request)
    cfg = settings()
    email, password = payload.get('email', ''), payload.get('password', '')
    if not isinstance(email, str) or not isinstance(password, str) or len(email) > 254 or len(password) > 128:
        raise HTTPException(400, '이메일과 비밀번호를 확인하세요.')
    key = 'auth:' + hashlib.sha256(email.strip().lower().encode()).hexdigest()
    if not get_store().allow_request(key, maximum=15):
        raise HTTPException(429, '시도가 많습니다. 잠시 후 다시 시도하세요.')
    if cfg['mode'] == 'local':
        if request.url.hostname not in ('localhost', '127.0.0.1', '::1', 'testserver'):
            raise HTTPException(403, '로컬 검토 계정은 이 컴퓨터에서만 사용할 수 있습니다.')
        user = (safe_error(lambda: get_store().register(email, password)) if action == 'signup'
                else get_store().authenticate(email, password))
        if not user:
            raise HTTPException(401, '로그인 정보를 확인하세요.')
    else:
        path = '/signup' if action == 'signup' else '/token?grant_type=password'
        try:
            result = httpx.post(cfg['url'] + '/auth/v1' + path, json={'email': email, 'password': password},
                                headers={'apikey': cfg['key']}, timeout=10)
            data = result.json()
        except (httpx.HTTPError, ValueError):
            raise HTTPException(503, '인증 서비스에 연결할 수 없습니다.') from None
        if result.status_code >= 400:
            raise HTTPException(400, '인증 정보를 확인하세요. 이메일 인증이 필요할 수 있습니다.')
        if not data.get('access_token'):
            return {'verification_required': True, 'message': '이메일 인증 후 로그인하세요.'}
        user = get_store().external_user(data['user']['id'], data['user'].get('email', email))
    token, csrf = get_store().create_session(user['id'], cfg['mode'])
    # Local sessions are dev-only. Managed login sessions have a short independent expiry.
    if cfg['mode'] == 'supabase':
        with get_store().db() as cx:
            get_store().execute(cx, 'UPDATE app_sessions SET expires=? WHERE token_hash=?',
                                (time.time() + 900, hashlib.sha256(token.encode()).hexdigest()))
    response.set_cookie(COOKIE, token, max_age=900 if cfg['mode'] == 'supabase' else 604800,
                        httponly=True, secure=cfg['production'], samesite='lax', path='/')
    response.headers['Cache-Control'] = 'no-store'
    return {'user': user, 'csrf': csrf, 'entitlements': get_store().entitlements(user['id'])}


@router.post('/api/account/signup')
def signup(payload: dict, request: Request, response: Response):
    return account_action('signup', payload, request, response)


@router.post('/api/account/login')
def login(payload: dict, request: Request, response: Response):
    return account_action('login', payload, request, response)


@router.get('/api/account/me')
def me(response: Response, session=Depends(current)):
    response.headers['Cache-Control'] = 'no-store'
    return dict(user=session['user'], csrf=session['csrf'], entitlements=get_store().entitlements(session['user']['id']))


@router.post('/api/account/logout')
def logout(request: Request, response: Response, session=Depends(current)):
    get_store().logout(request.cookies.get(COOKIE, ''))
    response.delete_cookie(COOKIE, path='/')
    return {'ok': True}


@router.post('/api/budget/calculate')
def budget(payload: dict, request: Request, response: Response):
    check_origin(request)
    # Daily salted network bucket, not a stored raw IP or request-body log.
    peer = request.client.host if request.client else 'unknown'
    key = 'budget:' + hashlib.sha256((str(int(time.time() // 86400)) + peer).encode()).hexdigest()
    if not get_store().allow_request(key, 120, 60):
        raise HTTPException(429, '요청이 많습니다. 잠시 후 다시 시도하세요.')
    response.headers['Cache-Control'] = 'no-store'
    return safe_error(lambda: calculate(payload))


@router.post('/api/events')
def event(payload: dict, request: Request):
    check_origin(request)
    if payload.get('event_name') == 'recommendation_completed':
        raise HTTPException(400, '추천 완료 이벤트는 서버에서만 기록합니다.')
    peer = request.client.host if request.client else 'unknown'
    key = 'event:' + hashlib.sha256((str(int(time.time() // 86400)) + peer).encode()).hexdigest()
    if not get_store().allow_request(key, 120, 60):
        raise HTTPException(429, '요청이 많습니다.')
    session = get_store().session(request.cookies.get(COOKIE))
    if session and session['auth_mode'] != settings()['mode']:
        session = None
    return {'accepted': safe_error(lambda: get_store().event(session['user']['id'] if session else None, payload))}


@router.get('/api/saved')
def saved(response: Response, session=Depends(current)):
    response.headers['Cache-Control'] = 'no-store'
    return {'items': get_store().saved_items(session['user']['id'])}


@router.post('/api/saved')
def save(payload: dict, session=Depends(current)):
    if not isinstance(payload.get('payload'), dict) or not isinstance(payload.get('key'), str):
        raise HTTPException(400, '저장할 항목을 확인하세요.')
    return safe_error(lambda: get_store().save_item(session['user']['id'], payload.get('kind'), payload['key'], payload['payload']))


@router.delete('/api/saved/{item}')
def delete(item: str, session=Depends(current)):
    if not get_store().delete_item(session['user']['id'], item):
        raise HTTPException(404, '저장한 항목을 찾을 수 없습니다.')
    return {'ok': True}


@router.post('/api/billing/checkout')
def checkout(session=Depends(current)):
    raise HTTPException(503, '결제는 아직 활성화하지 않았습니다. 요금이 청구되지 않습니다.')


@router.get('/api/reports')
def reports(session=Depends(current)):
    if not get_store().entitlements(session['user']['id'])['features']['scheduled_reports']:
        raise HTTPException(403, '정기 리포트는 출시 준비 중입니다. 현재 계정에는 이용 권한이 없습니다.')
    raise HTTPException(503, '리포트 생성·발송 서비스가 아직 연결되지 않았습니다.')
