import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = Path('C:/projects/realestate_reco')
data = json.loads((OUT / 'script_audit_checks.json').read_text(encoding='utf-8'))
assert data['passed'], '독립 대조 실패를 먼저 해결해야 한다.'
checks = json.loads((OUT / 'skill_structure_checks.json').read_text(encoding='utf-8'))
assert checks['pass'], '스킬 구조 검사 실패'
delta = json.loads((OUT / 'config_delta_checks.json').read_text(encoding='utf-8'))
assert delta['passed'], '설정 변경분 재검수 실패'
script_key = 'video-agent-studio/episodes/newlywed-apartment-picks-20261101/writer/top20-split-v4/longform-natural-v5-20261104/script_v5.md'
revision = {'script_sha256': data['input_sha256'][script_key],
            'input_manifest': 'script_audit_checks.json#/input_sha256',
            'latest_config_delta': {'evidence': 'config_delta_checks.json', 'path': delta['path'], 'sha256': delta['current_sha256']}}

findings = {
    'task_id': data['task_id'], 'role': 'qa',
    'scope': '최신 대본·읽기문 및 로컬 스킬 적용 시험. 오디오·영상 품질 통과가 아님.',
    'checked_revision': revision,
    'open_counts': {'critical': 0, 'required': 0, 'recommended': 0},
    'findings': [],
    'item_schema': ['issue_id', 'scene_id', 'timecode', 'severity', '문제', 'evidence', '수정안', 'owner', 'status', 'checked_revision'],
    'coverage': data['coverage'],
    'evidence': ['script_audit_checks.json', 'config_delta_checks.json', 'skill_structure_checks.json', 'skill_application_test.md', 'final_report.md'],
    'native_skill_auto_discovery': 'unchecked; WORKFLOW 상대 링크와 명시 경로만 확인',
    'new_voice_generation': {'needed_if_adopted_sentence_count': data['counts']['reading_changed'],
                             'reading_characters': data['counts']['changed_reading_chars_including_spaces'],
                             'approval_granted': False, 'performed': False},
}

issue = {
    'issue_id': 'QA_TEXT_READY', 'scene_id': data['affected_scene_ids'], 'timecode': None,
    'severity': 'recommended', '문제': '최신 v5의 문구 독립 QA 전달. 미해결 critical/required 0.',
    'evidence': ['final_report.md', 'script_audit_checks.json', 'findings.json'],
    '수정안': '문구 필수 수정 없음. 채택 시 47개 읽기문을 새 발화 대상으로 검토하고 실제 청취·정렬·영향 장면 QA를 이어간다.',
    'owner': 'director', 'status': 'handoff_ready', 'checked_revision': revision,
    'impact': '미디어·예산·유료 생성·게시 승인 아님. 기존 오디오·영상 변경 없음.',
    'delivery': '직접 에이전트 메시지 도구가 없어 로컬 issue 파일로 전달',
}

def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

save('findings.json', findings)
save('issue_QA_TEXT_READY.json', issue)
names = ['final_report.md', 'findings.json', 'script_audit_checks.json', 'config_delta_checks.json', 'skill_application_test.md', 'skill_structure_checks.json', 'issue_SKILL_TEST_READY.json', 'issue_QA_TEXT_READY.json', 'audit_script.py', 'audit_config_delta.py', 'audit_skill.py', 'finalize_review.py']
handoff = {
    'task_id': data['task_id'], 'role': 'qa', 'status': 'text_qa_complete_media_unchecked',
    'summary': '최신 v5 critical/required/recommended 각 0. 90ID 유지, 변경47/미변경43, 새 읽기문3088자. 스킬 A/B 로컬 준비안 및 링크/참조/권한 점검 완료.',
    'input_revisions': revision,
    'outputs': [{'path': (OUT / name).relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256((OUT/name).read_bytes()).hexdigest(), 'bytes': (OUT/name).stat().st_size} for name in names],
    'affected_scene_ids': data['affected_scene_ids'],
    'checks': [{'check': '독립 대본·숫자·참조·해시', 'result': 'passed', 'evidence': 'script_audit_checks.json'},
               {'check': '스킬 A/B 로컬 준비안·구조·권한', 'result': 'passed', 'evidence': 'skill_application_test.md / skill_structure_checks.json'},
               {'check': '실제 청취·연속 재생·MP4 프레임/기술 검사', 'result': 'unchecked', 'evidence': None}],
    'open_issue_ids': [],
    'unresolved': ['실제 새 음성·타이밍·영상은 미생성/미검수', '네이티브 스킬 자동 등록은 미확인'],
    'next_role': 'director',
    'expected_voice_regeneration': {'sentences': 47, 'reading_characters_including_spaces': 3088, 'approval': False, 'performed': False},
    'next_action': '총괄이 현재 파일 SHA로 원고·실제 전송 청크·예산 범위를 연결한다. 생성 후 음성 담당의 실제 청취·정렬, 편집 담당의 영향 장면 수정과 독립 QA가 필요하다.',
}
save('handoff.json', handoff)
print(json.dumps({'outputs': len(names) + 1, 'open_counts': findings['open_counts'], 'changed': data['counts']['changed'], 'reading_chars': 3088, 'script_sha256': revision['script_sha256']}, ensure_ascii=False))
