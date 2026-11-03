"""Bind real Claude/native approvals before allowing the existing free TTS plan."""
import hashlib,json,sys,importlib.util
from datetime import datetime,timezone
from pathlib import Path
D=Path(__file__).resolve().parent;EP=D.parents[1];ROOT=EP.parents[2]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()
def save(p,x):
 assert not p.exists(),str(p)
 p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
md=D/'frozen-script-v3-r2/script_v3_r2.md';script=D/'frozen-script-v3-r2/scenes_v3_r2.json'
review=D/'claude/script-v3-r2-round2/review.json';receipt=D/'claude/script-v3-r2-round2/receipt.json'
native=EP/'qa/rebuild-v2/content_review_r2.json'
cr,rc,n=map(read,[review,receipt,native])
assert cr['approved'] is True and not cr['required_issues']
assert rc['approved'] is True and rc['artifact_sha256']==sha(md)==cr['artifact_sha256']
assert n['decision']['approved'] is True
assert sha(script)=='cc1ef7d80225e992e7e5d31faffbfb09a8f90c80fb5352e17c36eb8c90755b12'
plan=EP/'narration/rebuild-v2/prepare-r2/prepared.json';p=read(plan)
assert p['script_sha256']==sha(script)
lock=D/'locked_script_r2.json';auth=D/'free_edge_authorization_r2.json';out=EP/'narration/rebuild-v2/audio-r2'
save(lock,{'approved':True,'episode_id':EP.name,'script_revision':p['revision'],
 'script_path':rel(script),'script_sha256':sha(script),'markdown_path':rel(md),'markdown_sha256':sha(md),
 'claude_approved':True,'review_reference':{'Claude_receipt':rel(receipt),'Claude_receipt_sha256':sha(receipt),'native_review':rel(native),'native_review_sha256':sha(native)},
 'at_utc':datetime.now(timezone.utc).isoformat()})
modulepath=EP/'narration/rebuild-v2/build_narration.py'
spec=importlib.util.spec_from_file_location('voice_builder',modulepath);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
save(auth,{'approved':True,'source':'main_direct_instruction','instruction_reference':rel(D/'authorization.json'),
 'episode_id':EP.name,'script_revision':p['revision'],'script_sha256':sha(script),
 'prepared_sha256':sha(plan),'lock_sha256':sha(lock),'network_tts_authorized':True,
 'provider':'edge-tts','voice':'ko-KR-InJoonNeural','rate':'+0%','external_payload':'text_only',
 'cash_cap_krw':0,'paid_calls_authorized':False,'credentials_allowed':False,'automatic_retries':0,
 'max_network_attempts':len(p['scenes']),'allowed_scene_ids':[x['scene_id'] for x in p['scenes']],
 'command_argv':m.command_argv(plan,lock,auth,out)})
gate=m.check_gate(plan,lock,auth,out)
print(json.dumps({'status':'exact_script_and_free_voice_gate_passed','scene_count':len(p['scenes']),'script_sha256':sha(script),'command_argv':read(auth)['command_argv']},ensure_ascii=False))
