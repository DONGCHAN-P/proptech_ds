"""Promote the independently checked school-label patch; no upload or paid action."""
import hashlib
import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EP = ROOT / 'video-agent-studio/episodes/goyang-changneung-20261015'
OUT = EP / 'outputs/production-v8-labels'

def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p, v): p.write_text(json.dumps(v, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    qp = EP/'qa/production-v8-labels/final_review.json'
    q = read(qp)
    assert q['status'] in ['passed_with_limits', 'review_preview_pass_with_explicit_coverage_limits']
    assert q.get('required_unresolved', q.get('required_open')) == []
    mp4 = OUT/'changneung_full_v8_labels.mp4'
    techp = OUT/'technical_v8_labels.json'
    tech = read(techp)
    digest = sha(mp4)
    assert tech['sha256'] == q['checked_revision'] == digest
    state = read(EP/'state.json')
    if state['current_preview']['sha256'] == digest:
        print('Already finalized'); return
    assert state['script_revision'] == 'script-v8'
    assert state['visual_label_patch']['baseline_sha256'] == '5131dbfe48a203ffa13d3ca9104c23baf9d53038880b8b99b4f4266eb39567c8'
    assert sha(EP/'outputs/script-review-v8/script_v8.md') == '6ffc9fc4819460d4cf6f03fd3b28102e2864402b9965ca14e158230474963982'
    now = datetime.now(timezone.utc)
    did = uuid.uuid4().hex[:12]
    paths = [mp4, OUT/'changneung_v8_labels.srt', techp, qp]
    artifacts = {p.relative_to(EP).as_posix(): sha(p) for p in paths}
    decision = dict(id=did, episode=state['episode_id'], gate='completed', status='pending',
        created_at=now.isoformat(), expires_at=(now+timedelta(days=7)).isoformat(),
        summary='창릉 v8 학교 시설번호를 예정 부지로 풀어 쓴 무료 검토본. 기존 음성·길이 유지. 유료 생성·업로드 제외.',
        scope='free_preview_v8_school_labels_only', script_revision='script-v8',
        audio_revision=state['audio_revision'], artifact_hashes=artifacts,
        paid_generation_authorized=False, upload_authorized=False)
    ds = read(EP/'decisions.json')
    prior = state.get('completed_gate_decision_id')
    for d in ds['decisions']:
        if d['id'] == prior and d['status'] == 'pending':
            d.update(status='superseded', superseded_by=did, reason='school_label_visual_patch')
            write(ROOT/'output/video_decisions/decisions'/f'{prior}.json',d)
    ds['decisions'].append(decision)
    write(EP/'decisions.json', ds)
    write(ROOT/'output/video_decisions/decisions'/f'{did}.json',decision)
    state.update(stage='preview_completed_review_pending', active_tasks=[],
        pending_gate='completed', pending_decision_ids={'completed':did}, completed_gate_decision_id=did,
        visual_revision='production-v8-labels', render_revision='production-v8-labels',
        delivery_revision='production-v8-labels', video_path=mp4.relative_to(EP).as_posix(),
        rendered_video_sha256=digest, qa_path=qp.relative_to(EP).as_posix())
    state['current_preview'].update(path=state['video_path'], sha256=digest,
        qa=state['qa_path'], visual_revision='production-v8-labels')
    state['visual_label_patch'].update(status='delivered',completed_decision_id=did,sha256=digest)
    write(EP/'state.json',state)
    pf=read(EP/'preflight.json')
    pf['status']=state['stage']; pf['delivery']=state['current_preview']
    pf['approvals']['completed']=dict(decision_id=did,status='pending',scope=decision['scope'])
    write(EP/'preflight.json',pf)
    cfg=read(ROOT/'config/video_shelf.json')
    e=next(e for e in cfg['entries'] if e['workspace'].endswith(state['episode_id']))
    e['status']='무료 TTS 검토본 v8 · 학교 시설번호 표기 개선 · 최종 Jun 음성 전'
    e['files']['영상.mp4']=mp4.relative_to(ROOT).as_posix()
    e['files']['자막.srt']=(OUT/'changneung_v8_labels.srt').relative_to(ROOT).as_posix()
    write(ROOT/'config/video_shelf.json',cfg)
    print(json.dumps({'decision_id':did,'sha256':digest},ensure_ascii=False))

if __name__=='__main__': main()
