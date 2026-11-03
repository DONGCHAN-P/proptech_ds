"""Register the exact user-review draft. Does not approve any video gate."""
import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EP = ROOT / 'video-agent-studio/episodes/goyang-changneung-20261015'

def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p, v): p.write_text(json.dumps(v, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    script = EP/'outputs/script-review-v7/script_v7.md'
    digest = sha(script)
    qa = read(EP/'qa/revision-v7/script_review.json')
    assert qa['checked_revision'] == digest
    assert qa['status'] == 'passed_for_user_script_review' and not qa['required_unresolved']
    state = read(EP/'state.json')
    decisions = read(EP/'decisions.json')
    existing = next((d for d in decisions['decisions'] if d.get('gate') == 'script'
        and d.get('artifact_hashes', {}).get('outputs/script-review-v7/script_v7.md') == digest), None)
    if existing:
        print(json.dumps({'already_registered':existing['id']})); return
    now = datetime.now(timezone.utc)
    decision_id = uuid.uuid4().hex[:12]
    records = ['outputs/script-review-v7/script_v7.md', 'writer/revision-v7/narration_packet.json',
               'writer/revision-v7/scene_proposals.json', 'qa/revision-v7/script_review.json']
    decision = dict(id=decision_id, episode=state['episode_id'], gate='script',
        status='pending', created_at=now.isoformat(), expires_at=(now+timedelta(days=7)).isoformat(),
        summary='창릉 v7: 구어체·가격 성장 요인·대장 후보 중심, 개인 이사 달력 삭제. 대본·장면 방향 검토만.',
        scope='script_v7_and_scene_direction_only', script_revision='script-v7',
        artifact_hashes={p:sha(EP/p) for p in records},
        paid_generation_authorized=False, upload_authorized=False)
    prior_id = state.get('pending_decision_ids', {}).get('completed')
    for old in decisions['decisions']:
        if old['id'] == prior_id and old.get('status') == 'pending':
            old.update(status='superseded', superseded_by=decision_id,
                       superseded_reason='User requested script and visual revision after r5 review.')
            write(ROOT/'output/video_decisions/decisions'/f'{prior_id}.json',old)
    decisions['decisions'].append(decision)
    write(EP/'decisions.json', decisions)
    write(ROOT/'output/video_decisions/decisions'/f'{decision_id}.json',decision)
    state.update(stage='script_review_pending', draft_script_revision='script-v7',
        draft_script_status='pending_approval', draft_script_path='outputs/script-review-v7/script_v7.md',
        draft_script_sha256=digest, pending_gate='script', pending_decision_ids={'script':decision_id})
    write(EP/'state.json',state)
    shelf_path=ROOT/'config/video_shelf.json'; shelf=read(shelf_path)
    entry=next(e for e in shelf['entries'] if e['workspace'].endswith(state['episode_id']))
    entry['files']['대본_수정안.md']=str(script.relative_to(ROOT)).replace('\\','/')
    entry['files']['수정내역.md']='video-agent-studio/episodes/goyang-changneung-20261015/outputs/script-review-v7/changes_v7.md'
    write(shelf_path,shelf)
    print(json.dumps({'decision_id':decision_id,'sha256':digest,'status':'pending'},ensure_ascii=False))

if __name__ == '__main__': main()
