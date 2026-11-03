"""Offline metadata only: no generation, API request, refresh or installation."""
import importlib.metadata
import json
import os
from pathlib import Path
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[5]


def inspect():
    deps = ROOT / 'tools/youtube_deps'
    versions = {
        d.metadata.get('Name', '').lower(): d.version
        for d in importlib.metadata.distributions(path=[str(deps)])
    }
    base_versions = {
        d.metadata.get('Name', '').lower(): d.version
        for d in importlib.metadata.distributions()
    }
    report = {
        'checked_at': datetime.now(timezone.utc).isoformat(),
        'mode': 'offline_metadata_only',
        'python_version': sys.version.split()[0],
        'python_executable': sys.executable,
        'edge_tts_installed_in_active_python': 'edge-tts' in base_versions,
        'youtube_dependencies': {n: versions.get(n) for n in (
            'google-api-python-client', 'google-auth', 'google-auth-oauthlib')},
        'credential_environment_present': {k: bool(os.environ.get(k)) for k in (
            'ANTHROPIC_API_KEY', 'ANTHROPIC_AUTH_TOKEN', 'ANTHROPIC_BASE_URL',
            'CLAUDE_CODE_OAUTH_TOKEN', 'CLAUDE_CODE_USE_BEDROCK',
            'CLAUDE_CODE_USE_VERTEX', 'CLAUDE_CODE_USE_FOUNDRY')},
        'dotenv_exists': (ROOT / '.env').is_file(),
        'dotenv_loaded': False,
        'api_requests': 0,
        'token_refreshes': 0,
        'audio_generated': False,
    }
    sys.path.insert(0, str(deps))
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.http import MediaFileUpload
        from googleapiclient.discovery import build
        from google.auth.transport.requests import Request
        report['youtube_dependency_imports'] = 'passed_no_service_created'
    except Exception as exc:
        report['youtube_dependency_imports'] = type(exc).__name__
    token_file = ROOT / 'config/youtube-token.json'
    report['youtube_token_file_exists'] = token_file.is_file()
    if token_file.is_file():
        token = json.loads(token_file.read_text(encoding='utf-8-sig'))
        scopes = set(token.get('scopes', []))
        expiry = token.get('expiry')
        parsed = datetime.fromisoformat(expiry.replace('Z', '+00:00')) if expiry else None
        if parsed and parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        report['youtube_oauth'] = {
            **{k + '_present': bool(token.get(k)) for k in (
                'token', 'refresh_token', 'client_id', 'client_secret')},
            'upload_scope': 'https://www.googleapis.com/auth/youtube.upload' in scopes,
            'readonly_scope': 'https://www.googleapis.com/auth/youtube.readonly' in scopes,
            'force_ssl_scope': 'https://www.googleapis.com/auth/youtube.force-ssl' in scopes,
            'access_token_expired_offline': parsed < datetime.now(timezone.utc) if parsed else None,
            'remote_validity_checked': False,
        }
    report['youtube_client_file_exists'] = (ROOT / 'config/youtube-client-secret.json').is_file()
    return report


if __name__ == '__main__':
    print(json.dumps(inspect(), ensure_ascii=False, indent=2))
