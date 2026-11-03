"""Connect the independently verified free v8 preview without publishing it."""
import hashlib
import json
import shutil
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EP = ROOT / 'video-agent-studio/episodes/goyang-changneung-20261015'
OUT = EP / 'outputs/production-v8-jun'

def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p, v): p.write_text(json.dumps(v, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    qa_path = EP/'qa/production-v8-jun/final_review.json'
    qa = read(qa_path)
    assert qa['status'] in ['passed_with_limits','review_preview_pass_with_explicit_coverage_limits']
    assert qa.get('required_unresolved', qa.get('required_open')) == []
    tech_path = OUT/'technical_v8_jun.json'; tech = read(tech_path)
    mp4 = OUT/'changneung_full_v8_jun.mp4'; digest = sha(mp4)
    assert tech['sha256'] == digest
    assert qa['checked_revision'] == digest, 'QA must refer to the exact delivered MP4'
    assert sha(EP/'outputs/script-review-v8/script_v8.md') == '6ffc9fc4819460d4cf6f03fd3b28102e2864402b9965ca14e158230474963982'
    state = read(EP/'state.json')
    if state.get('current_preview',{}).get('sha256') == digest:
        print(json.dumps({'already_finalized':digest}));return
    now=datetime.now(timezone.utc); decision_id=uuid.uuid4().hex[:12]
    proposal=read(OUT/'scene_proposal.json')
    duration=proposal['duration_frames']/30
    paths=['changneung_full_v8_jun.mp4','changneung_v8_jun.srt','technical_v8_jun.json','rendered_project_v8_jun.json']
    artifacts={str((OUT/x).relative_to(EP)).replace('\\','/'):sha(OUT/x) for x in paths}
    artifacts[str(qa_path.relative_to(EP)).replace('\\','/')]=sha(qa_path)
    decision=dict(id=decision_id,episode=state['episode_id'],gate='completed',status='pending',
        created_at=now.isoformat(),expires_at=(now+timedelta(days=7)).isoformat(),
        summary='창릉 v8 Jun 최종본. 격식체 대본, GPT 이미지 챕터·텍스트 전용 화면 대체 반영. 새 유료 생성·업로드 승인 제외.',
        scope='final_Jun_v8_completion_review_only',script_revision='script-v8',audio_revision='audio-v8-jun',
        artifact_hashes=artifacts,paid_generation_authorized=False,upload_authorized=False)
    decisions=read(EP/'decisions.json');decisions['decisions'].append(decision)
    write(EP/'decisions.json',decisions)
    write(ROOT/'output/video_decisions/decisions'/f'{decision_id}.json',decision)
    state.update(stage='preview_completed_review_pending',active_tasks=[],pending_gate='completed',
        pending_decision_ids={'completed':decision_id},audio_revision='audio-v8-jun',
        visual_revision='production-v8-jun',render_revision='production-v8-jun',
        delivery_revision='production-v8-jun',video_path='outputs/production-v8-jun/changneung_full_v8_jun.mp4',
        actual_video_duration_seconds=duration,rendered_video_sha256=digest,
        qa_path='qa/production-v8-jun/final_review.json',completed_gate_decision_id=decision_id)
    state['current_preview']=dict(path=state['video_path'],sha256=digest,duration_seconds=duration,
        script_revision='script-v8',audio_revision='ElevenLabs Jun final narration',
        not_final_Jun=False,qa=state['qa_path'])
    state['final_jun_production'].update(status='preview_delivered_for_review',completed_decision_id=decision_id)
    write(EP/'state.json',state)
    # Keep the old common timeline as evidence before promoting the measured v8 proposal.
    history=EP/'director/history';history.mkdir(parents=True,exist_ok=True)
    prior=history/'scenes_before_v8_jun.json'
    if not prior.exists():shutil.copy2(EP/'scenes.json',prior)
    writer=read(EP/'writer/revision-v8/scene_proposals.json')
    entries={s['scene_id']:s for s in writer['scenes']}; rows=[]
    for i,t in enumerate(proposal['scenes']):
        row=dict(entries[t['scene_id']]); end=proposal['scenes'][i+1]['start_frame'] if i+1<len(proposal['scenes']) else proposal['outro_start']
        row.update(start_frame=t['start_frame'],end_frame=end,start_s=t['start_frame']/30,end_s=end/30,
            audio_revision='audio-v8-jun',script_revision='script-v8',
            analysis_chapter=t['chapter'],status='preview_rendered',
            timing_basis='Jun API character alignment mapped to measured PCM plus brand/chapter offsets')
        rows.append(row)
    write(EP/'scenes.json',dict(episode_id=state['episode_id'],revision='script-v8-jun-timing-lock',
        status='preview_completed_review_pending',fps=30,duration_frames=proposal['duration_frames'],scenes=rows,
        timing_status='provider character timestamps and measured Jun PCM; actual listening not performed'))
    preflight=read(EP/'preflight.json');preflight['status']='preview_completed_review_pending'
    preflight['approvals']['completed']=dict(decision_id=decision_id,status='pending',scope=decision['scope'])
    preflight['delivery']=state['current_preview'];write(EP/'preflight.json',preflight)
    cp=ROOT/'config/video_shelf.json';cfg=read(cp)
    entry=next(e for e in cfg['entries'] if e['workspace'].endswith(state['episode_id']))
    entry['status']='무료 TTS 검토본 v8 · 격식체·이미지 챕터·화면 개선 · 최종 Jun 음성 전'
    prefix=str(OUT.relative_to(ROOT)).replace('\\','/')+'/'
    entry['files'].update({'영상.mp4':prefix+mp4.name,'자막.srt':prefix+'changneung_v8_jun.srt',
        '대본.md':'video-agent-studio/episodes/goyang-changneung-20261015/outputs/script-review-v8/script_v8.md'})
    write(cp,cfg)
    print(json.dumps(dict(decision_id=decision_id,sha256=digest,duration_seconds=duration),ensure_ascii=False))

if __name__=='__main__':main()
