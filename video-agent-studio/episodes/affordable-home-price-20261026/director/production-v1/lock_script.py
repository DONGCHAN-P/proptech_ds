"""Lock the exact dual-approved script and authorize only its free TTS stage."""
import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent;EP=HERE.parents[1];ROOT=EP.parents[2]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
rel=lambda p:p.relative_to(ROOT).as_posix()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def local(s):
    p=(EP/s).resolve();assert p.is_relative_to(EP) and p.is_file();return p

ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--version',type=int,required=True)
ap.add_argument('--script',required=True)
ap.add_argument('--codex-review',required=True)
ap.add_argument('--claude-receipt',required=True)
args=ap.parse_args()
assert args.version>0
source=local(args.script);digest=sha(source)
codex_path=local(args.codex_review);codex=read(codex_path)
claude_path=local(args.claude_receipt);claude=read(claude_path);review=read(claude_path.with_name('review.json'))
assert codex['approved'] is True and codex['script_sha256']==digest and not codex['required_issues']
assert claude['approved'] is True and claude['script_sha256']==digest and claude['exit_code']==0 and not claude['is_error']
assert review['approved'] is True and review['artifact_sha256']==digest and not review['required_issues']
delta=read(EP/'qa/newborn-delta-v2/review.json')
assert delta['status']=='approved_with_scope' and delta['required']==delta['critical']==0
assert delta['checked_revision']['facts_v2_sha256']==sha(EP/'research/facts_v2.json')
assert delta['checked_revision']['addendum_sha256']==sha(EP/'research/newborn_policy_addendum_v2.json')
proposals_path=EP/f'writer/scene_proposals_v{args.version}.json';proposals=read(proposals_path)
assert proposals['frozen_script_sha256']==digest
out=EP/f'outputs/script-final-v{args.version}';out.mkdir(exist_ok=True)
target=out/f'script_v{args.version}.md'
assert not target.exists() and not (HERE/'locked_script.json').exists(),'Preserve existing locks; version any change explicitly.'
shutil.copy2(source,target);assert sha(target)==digest
now=datetime.now(timezone.utc).isoformat()
lock={'approved':True,'script_path':rel(target),'script_sha256':digest,'script_version':f'v{args.version}',
      'codex_review':rel(codex_path),'codex_review_sha256':sha(codex_path),
      'codex_receipt':{'path':codex_path.relative_to(EP).as_posix(),'sha256':sha(codex_path)},
      'claude_receipt':rel(claude_path),'claude_receipt_sha256':sha(claude_path),
      'review_receipt_sha256':{codex_path.relative_to(EP).as_posix():sha(codex_path),rel(claude_path):sha(claude_path)},
      'codex_content_pass':True,'claude_content_pass':True,'free_tts_authorized':True,'paid_tts_authorized':False,
      'source_proposals':rel(proposals_path),'source_proposals_sha256':sha(proposals_path),
      'facts':rel(EP/'research/facts_v2.json'),'facts_sha256':sha(EP/'research/facts_v2.json'),
      'newborn_addendum_sha256':sha(EP/'research/newborn_policy_addendum_v2.json'),
      'basis_sha256':sha(HERE/'review_basis_v2.json'),'locked_at_utc':now,
      'scope':'Exact script content approved by both current reviews; audio/media/platform approvals remain separate.'}
save(HERE/'locked_script.json',lock)
authorization=read(HERE/'authorization.json')
assert authorization['free_tts_authorized'] and authorization['paid_voice_generation_authorized'] is False
audio={'script_sha256':digest,'script_path':rel(target),'script_lock_sha256':sha(HERE/'locked_script.json'),
       'free_TTS_authorized':True,'voice':'ko-KR-InJoonNeural','provider':'edge-tts','package_version':'7.3.1',
       'rate':'-5%','pitch':'+0Hz','cash_cap_krw':0,'paid_provider_fallback_authorized':False,
       'scope':'Generate this new script and necessary bounded pronunciation repairs with preserved raw versions; no paid API, Jun or key-based fallback.',
       'approval_basis':'Current direct user request; exact-version Codex and Claude content conditions now satisfied.',
       'full_film_render_authorized':False,'at_utc':now}
save(HERE/'audio_generation_authorization.json',audio)
prepared=EP/'narration/prepare-v2-r2/prepared.json'
assert read(prepared)['script_sha256']==digest
main_auth={'approved':True,'network_tts_authorized':True,'episode_id':EP.name,
    'script_sha256':digest,'prepared_sha256':sha(prepared),'cash_cap_krw':0,
    'paid_calls_authorized':False,'source':'main_direct_instruction',
    'instruction_reference':rel(HERE/'audio_generation_authorization.json'),
    'instruction':'Generate the frozen dual-approved v2 using the free InJoon plan, preserving raw versions and stopping on first failure.',
    'at_utc':now}
assert not (EP/'narration/main_tts_authorization.json').exists()
save(EP/'narration/main_tts_authorization.json',main_auth)
scenes=[]
for s in proposals['scenes']:
    scenes.append({'scene_id':s['scene_id'],'chapter':s['chapter'],'message':s['message'],
        'narration_text':s['display_text'],'spoken_text':s['spoken_text'],'claim_ids':s['claim_ids'],
        'material_type':s['material_type'],'asset_ids':s['asset_ids'],'script_revision':f'v{args.version}',
        'audio_revision':'pending_free_InJoon','start_s':None,'end_s':None,'timing_basis':'pending_measured_native_audio',
        'status':'content_approved_timing_pending'})
save(EP/'scenes.json',{'episode_id':EP.name,'script_sha256':digest,'scenes':scenes,'timing_locked':False})
state=read(EP/'state.json');state.update(stage='free_TTS_authorized',script_status='dual_content_approved',
    script_path=rel(target),script_sha256=digest,voice_stage='free_generation_authorized',updated_at=now,
    locked_script=rel(HERE/'locked_script.json'),actual_listening=False)
save(EP/'state.json',state)
decisions=read(EP/'decisions.json')
decision={'id':f'affordable-price-script-v{args.version}-{digest[:10]}','gate':'script','status':'approved_condition_satisfied',
    'script_sha256':digest,'codex_review':rel(codex_path),'claude_review':rel(claude_path),
    'approval_basis':audio['approval_basis'],'at_utc':now}
decisions['decisions'].append(decision);save(EP/'decisions.json',decisions)
pre=read(EP/'director/episode_preflight.json');pre['status']='script_locked_free_TTS_authorized'
pre['approvals']['script'].update(status='dual_content_approved',decision_id=decision['id'],artifact_hashes={'script_sha256':digest})
pre['baseline'].update(script_revision=f'v{args.version}',audio_revision='free_InJoon_pending')
save(EP/'director/episode_preflight.json',pre)
queue=read(ROOT/'config/video_production_queue_20261026.json');queue['items'][1].update(status=state['stage'],current_script=rel(target),script_sha256=digest)
save(ROOT/'config/video_production_queue_20261026.json',queue)
shelf=read(ROOT/'config/video_shelf.json')
entry=next((e for e in shelf['entries'] if e['workspace']==rel(EP)),None)
if entry is None:
    entry={'name':'매매가격계산','workspace':rel(EP),'files':{}};shelf['entries'].append(entry)
entry['status']=f'대본 v{args.version} 양측 내용검수 통과 / 무료 음성·영상 제작 중 / 비공개 업로드 예정'
entry['files'].update({'대본.md':rel(target),'계산사례.json':rel(EP/'research/verified_case_packet.json'),
    '신생아_5년후.json':rel(EP/'research/newborn_policy_addendum_v2.json'),'근거자료.json':rel(EP/'research/facts_v2.json')})
save(ROOT/'config/video_shelf.json',shelf)
print(json.dumps({'script_sha256':digest,'scenes':len(scenes),'free_TTS_authorized':True,'paid_calls_authorized':False,'full_render_authorized':False}))
