"""Publish verified local preview links only; grants no paid/upload approvals."""
import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EP = ROOT / 'video-agent-studio/episodes/goyang-changneung-20261015'
OUT = EP / 'outputs/production-v6-ui-r5'

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def write(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    qa_path = EP / 'qa/production-v6-ui-r5/final_review.json'
    qa = read(qa_path)
    technical = read(OUT / 'technical_r5.json')
    mp4 = OUT / 'changneung_full_v6_ui_r5.mp4'
    digest = sha(mp4)
    assert technical['sha256'] == digest, 'Technical receipt must match final MP4'
    assert qa.get('status') == 'passed_with_limits', 'Independent final QA must pass first'
    assert qa.get('required_open') == [], 'Required issues must be closed'
    assert digest == '5763a26b875a06769347ff384908d01010adee9d7fcc60119f8e803001e3d5f4', 'Director-reviewed version only'
    state = read(EP / 'state.json')
    decisions = read(EP / 'decisions.json')
    if state.get('current_preview', {}).get('sha256') == digest:
        print(json.dumps(dict(status='already_finalized', mp4_sha256=digest)))
        return
    now = datetime.now(timezone.utc)
    old_id = state.get('pending_decision_ids', {}).get('completed')
    decision_id = uuid.uuid4().hex[:12]
    artifact_names = ['changneung_full_v6_ui_r5.mp4', 'changneung_v6_ui_r5.srt',
                      'technical_r5.json', 'rendered_project_r5.json']
    hashes = {str((OUT / n).relative_to(EP)).replace('\\', '/'): sha(OUT / n) for n in artifact_names}
    hashes[str(qa_path.relative_to(EP)).replace('\\', '/')] = sha(qa_path)
    decision = dict(id=decision_id, episode=state['episode_id'], gate='completed',
        summary='창릉 v6 UI·모션 r5 무료 TTS 검토본. 대본·기존 음성 유지. 유료 생성·업로드 승인 제외.',
        status='pending', created_at=now.isoformat(), expires_at=(now + timedelta(days=7)).isoformat(),
        scope='free_TTS_preview_ui_r5_only', script_revision='script-v6',
        audio_revision=state['audio_revision'], artifact_hashes=hashes,
        paid_generation_authorized=False, upload_authorized=False)
    for record in decisions['decisions']:
        if record['id'] == old_id and record.get('status') == 'pending':
            record.update(status='superseded', superseded_by=decision_id,
                          superseded_reason='User requested visual/UI/motion revision; prior artifact retained.')
            old_file = ROOT / 'output/video_decisions/decisions' / (old_id + '.json')
            if old_file.exists():
                write(old_file, record)
    decisions['decisions'].append(decision)
    write(EP / 'decisions.json', decisions)
    write(ROOT / 'output/video_decisions/decisions' / (decision_id + '.json'), decision)
    state.update(active_tasks=[], stage='preview_completed_review_pending', pending_gate='completed')
    state['pending_decision_ids']['completed'] = decision_id
    state['current_preview'] = dict(path=str(mp4.relative_to(EP)).replace('\\', '/'), sha256=digest,
        duration_seconds=933.9333333333333, script_revision='script-v6',
        audio_revision='free local Heami review voice', not_final_Jun=True,
        qa=str(qa_path.relative_to(EP)).replace('\\', '/'))
    state['production_v6']['status'] = 'ui_motion_r5_delivered_for_review'
    state['production_v6']['completed_decision_id'] = decision_id
    write(EP / 'state.json', state)
    shelf_path = ROOT / 'config/video_shelf.json'
    shelf = read(shelf_path)
    entry = next(e for e in shelf['entries'] if e['workspace'].endswith(state['episode_id']))
    entry['status'] = '무료 TTS 검토본 v6 UI·모션 r5 · 최종 Jun 음성 전'
    base = str(OUT.relative_to(ROOT)).replace('\\', '/') + '/'
    entry['files']['영상.mp4'] = base + mp4.name
    entry['files']['자막.srt'] = base + 'changneung_v6_ui_r5.srt'
    write(shelf_path, shelf)
    print(json.dumps(dict(decision_id=decision_id, mp4_sha256=digest, no_upload=True), ensure_ascii=False))

if __name__ == '__main__':
    main()
