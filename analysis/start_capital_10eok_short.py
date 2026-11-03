import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from notify.video_decisions import create, now, write

studio = ROOT / 'video-agent-studio'
ep = studio / 'episodes/capital-10eok-map-20261017'
if (ep / 'brief.json').exists():
    print('Episode already initialized; preserve existing work.')
    raise SystemExit(0)
for folder in ['research', 'writer', 'visual', 'editor', 'qa', 'outputs']:
    (ep / folder).mkdir(parents=True, exist_ok=True)
brief = {
    'episode_id': ep.name, 'request_type': 'new_video', 'format': 'short_form',
    'user_request': '실거래가 데이터로 2006년부터 연도별 10억 초과 단지 점이 사라지는 숏폼',
    'confirmed_scope': {'regions': ['서울', '경기', '인천'], 'exclusive_area_sqm': {'gte': 83, 'lt': 85}, 'statistic': '단지별 계약연도 실거래 중위값', 'threshold_krw': 1000000000, 'above_threshold': 'hide', 'at_or_below_threshold': 'show', 'reappearance': True, 'start_year': 2006},
    'proposed_missing_data_policy': '해당 연도 거래가 없으면 회색으로 별도 표시; 가격초과와 구분. 신축 이전 연도 가격을 역으로 채우지 않음.',
    'proposed_end_year_policy': '완결 연도와 최신 부분연도를 명확히 구분하며 실제 수집일 표시',
    'source': 'master/trade_events.parquet 및 staged/trade 원문, 기존 좌표 자료는 정밀도 감사 후 사용',
    'style': '채널 크림/파랑/잉크/Pretendard 유지; 고정 수도권 지도와 연도·단지 수; 줌 반복 없음',
    'vertical_safe_area': 'config/vertical_video_safe_area.json',
    'budget': {'external_paid_generation_allowed': False, 'cash_cap': 0, 'voice_generation_allowed': False},
    'publication_authorized': False,
}
write(ep / 'brief.json', brief)
topic = create(ep.name, 'topic', '수도권 84㎡급(83≤면적<85) 단지 연도별 거래중위값 지도: 2006년부터 10억 초과 숨김, 10억 이하 재진입 시 재등장. 사용자가 주제와 범위를 직접 지정.')
topic.update(status='approved', artifact_hashes={'brief.json': hashlib.sha256((ep/'brief.json').read_bytes()).hexdigest()}, response={'source': 'direct_user_chat_and_async_scope_answers', 'at': now().isoformat(), 'note': '숏폼 제작 요청 및 수도권/84㎡/재등장 기준 직접 선택'})
write(ROOT / 'output/video_decisions/decisions' / f"{topic['id']}.json", topic)
write(ep / 'state.json', {'episode_id': ep.name, 'stage': 'data_audit', 'topic_decision_id': topic['id'], 'active_tasks': ['data_audit'], 'script_ready': False, 'new_paid_generation': False, 'upload_authorized': False, 'publication_authorized': False})
write(ep / 'decisions.json', {'decisions': [topic]})
write(ep / 'scenes.json', {'revision': 'unwritten', 'scenes': []})
pre = json.loads((studio / 'templates/episode_preflight.json').read_text(encoding='utf-8-sig'))
pre.update(episode_id=ep.name, status='data_audit')
pre['approvals']['topic'].update(status='approved', decision_id=topic['id'], artifact_hashes=topic['artifact_hashes'])
pre['approvals']['budget'].update(status='no_paid_service_requested', cash_cap=0)
write(ep / 'preflight.json', pre)
print(json.dumps({'episode_root': str(ep), 'topic_decision_id': topic['id']}, ensure_ascii=False))
