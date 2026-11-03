"""Track the user's revision without expanding approvals or budgets."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

D = Path(__file__).resolve().parent
E = D.parents[2]
R = E.parents[2]


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def save(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    now = datetime.now(timezone.utc).isoformat()
    gatepath = R / 'output/video_decisions/decisions/5fa686c7d1e9.json'
    gate = read(gatepath)
    assert gate['gate'] == 'completed' and gate['status'] in ['pending', 'revision_requested']
    gate.update(status='revision_requested', revision_request=dict(
        at=now, source='same_conversation_direct_user',
        text='쇼츠 인트로·아웃트로 추가, 최근 Shorts 자료를 조사해 UI 보완',
        revision='shorts-ui-v2-20261104', previous_version_approved=False))
    save(gatepath, gate)
    save(D.parent / 'part1-jun-and-shorts-v1/completed_decision.json', gate)
    s = read(E / 'state.json')
    s.update(phase='shorts_ui_v2_20261104_in_production', pending_decision_id=None,
             requested_revision='top20-split-v4/shorts-ui-v2-20261104',
             shorts_revision_request=gate['revision_request'],
             shorts_revision_paid_calls_authorized=0, updated_at=now)
    s['active_approval_status'].update(completed='revision_requested:5fa686c7d1e9',
                                      pre_upload='not_reached_shorts_ui_v2')
    save(E / 'state.json', s)
    protected = [R / 'config/current_video.json',
                 R / 'output/video_decisions/decisions/c35ac917a1fe.json',
                 D.parent / 'part1-jun-and-shorts-v1/budget_decision.json',
                 D.parent / 'part1-jun-and-shorts-v1/production_authorization.json']
    save(D / 'preserved_state_fingerprint.json', dict(files=[dict(
        path=p.relative_to(R).as_posix(), sha256=hashlib.sha256(p.read_bytes()).hexdigest())
        for p in protected]))
    old = D.parent / 'part1-jun-and-shorts-v1/collect_evidence.py'
    source = old.read_text(encoding='utf-8').replace(
        'top20-split-v4/jun-and-shorts-v1', 'top20-split-v4/shorts-ui-v2-20261104')
    source = source.replace("if portrait:\n        for scene", "if portrait:\n        add(0, 'first_frame')\n        for scene", 1)
    source = source.replace("s=scene['start_s'];end=scene['end_s'];", "s=scene['start_s'];end=scene['end_s'];\n            for delta in [-.10,0,.10,.30,.60]:add(s+delta,'boundary_'+scene['kind']);\n            ", 1)
    (D / 'collect_evidence.py').write_text(source, encoding='utf-8')
    print('revision_recorded_old_completion_not_approved_budgets_preserved')


if __name__ == '__main__':
    main()
