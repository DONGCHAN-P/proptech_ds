"""Record the verified v6 source/audio gates and actual render start."""
import json
from datetime import datetime, timezone
from pathlib import Path
EP=Path(__file__).resolve().parents[2]
ROOT=EP.parents[2]
HERE=Path(__file__).parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lock=read(HERE/'locked_script.json')
timing=read(EP/'narration/free-tts-v1/final_timing.v6.json')
qa_path=EP/'qa/private-production-v1/source_v6_pass_receipt.json'
qa=read(qa_path)
audio_path=EP/'qa/private-production-v1/audio_v6_delta_handoff.json'
audio=read(audio_path)
assert qa['approved'] and audio['approved'] and not audio['required_issues']
assert timing['script_sha256']==lock['script_sha256']==audio['checked_sha256']
assert (EP/'outputs/private-production-v2/renders/measured-v6/ch04.render.log').exists()
state=read(EP/'state.json')
state.update(stage='full_render_v6_in_progress',updated_at=datetime.now(timezone.utc).isoformat())
state['free_tts_production'].update(status='source_and_targeted_ASR_passed_rendering',audio_revision=timing['audio_revision'],
    actual_seconds=sum(c['total_seconds'] for c in timing['chapters']),final_timing='narration/free-tts-v1/final_timing.v6.json',
    audio_delta_qa=audio_path.relative_to(EP).as_posix(),source_qa=qa_path.relative_to(EP).as_posix(),actual_listening=False)
save(EP/'state.json',state)
queue_path=ROOT/'config/video_production_queue_20261026.json'
queue=read(queue_path)
queue['items'][0].update(status='full_render_v6_in_progress',current_script=lock['script_path'])
save(queue_path,queue)
preflight=read(HERE/'episode_preflight.json')
preflight['baseline'].update(script_revision='script-final-v6',audio_revision=timing['audio_revision'])
preflight['approvals']['script'].update(status='dual_content_approved',artifact_hashes={'script_sha256':lock['script_sha256']})
save(HERE/'episode_preflight.json',preflight)
old=HERE/'render_authorization.json'
archive=HERE/'render_authorization_v5.json'
if not archive.exists():
    archive.write_bytes(old.read_bytes())
save(old,{'script_sha256':lock['script_sha256'],'audio_revision':timing['audio_revision'],'full_render_authorized':True,
    'authorization':'Current direct user request; both content reviews, targeted audio review, source QA and canonical carve passed.',
    'source_qa':qa_path.relative_to(EP).as_posix(),'targeted_audio_qa':audio_path.relative_to(EP).as_posix(),
    'private_upload':'final exact MP4 dual media approval required','new_paid_generation_authorized':False})
print(json.dumps({'stage':state['stage'],'source_approved':True,'new_audio_targeted_ASR_approved':True,'final_media_approved':False}))
