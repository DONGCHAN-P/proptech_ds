import hashlib,json,math,shutil,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from notify.video_decisions import create,write
from notify.telegram import send,send_file
ep=root/'video-agent-studio/episodes/goyang-changneung-20261015'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
qa=read(ep/'qa/script-v2/final_review.json')
assert not qa['open_required'] and qa['status']!='requires_revision'
script=ep/'writer/script-v2/script_v2.md';manifest=ep/'writer/script-v2/manifest.json'
m=read(manifest)
assert qa['checked_script_sha256']==sha(script)==m['source_script_sha256']
count=sum(len((ep/'writer/script-v2'/x['path']).read_text(encoding='utf-8')) for x in m['chapters'])
assert count==m['individual_character_sum']
out=ep/'outputs/script-review-v2';out.mkdir(exist_ok=True)
shutil.copyfile(script,out/'script_v2.md')
shutil.copyfile(ep/'writer/script-v2/changes.json',out/'changes.json')
pre=read(ep/'narration/read_preflight_v2.json')
reserve=math.ceil(count*.2);cap=count+reserve
assert pre['subscription']['remaining']>=cap and pre['model']['token_cost_factor']==1
budget={'revision':'budget-v2-script-v2','script_revision':'script-v2',
 'source_script_sha256':sha(script),'narration_manifest_sha256':sha(manifest),
 'voice':'Jun - Clear Korean Lecturer','voice_id':pre['voice']['id'],'model':'eleven_v4',
 'chapter_count':len(m['chapters']),'input_characters':count,'correction_character_cap':reserve,
 'total_submitted_character_cap':cap,'actual_credit_hard_cap':cap,
 'included_balance_checked':pre['subscription']['remaining'],'additional_cash_usd_cap':0,
 'automatic_retry':False,'overage_or_topup_authorized':False,
 'paid_image_or_music_generation_authorized':False,'generation_authorized':False,
 'scope':'Exact script-v2 chapters and limited manual corrections only; included credits; original brand/BGM reuse; local render',
 'guard':'Both exact script and budget gates required before POST; fresh balance check; ambiguous failed calls reconciled before retry'}
write(out/'budget_proposal_v2.json',budget)
artifacts={str(p.relative_to(ep)):sha(p) for p in [script,manifest,ep/'qa/script-v2/final_review.json',out/'script_v2.md']}
ds=create(ep.name,'script','수정 대본 v2 확정: 원흥역 기준 통근시간·현재 버스/도로 거점·본청약 가격과 현재 대안 비교, 반복 경고 축소. outputs/script-review-v2/script_v2.md')
ds.update(artifact_hashes=artifacts,script_revision='script-v2');write(root/'output/video_decisions/decisions'/f"{ds['id']}.json",ds)
db=create(ep.name,'budget',f'Jun 수정 대본 v2 {count}자+수정여유{reserve}자, 포함 크레딧 최대{cap}, 추가결제0. 자동재시도/충전/초과결제/새 유료이미지음악 제외.')
db.update(artifact_hashes={**artifacts,str((out/'budget_proposal_v2.json').relative_to(ep)):sha(out/'budget_proposal_v2.json')},budget=budget)
write(root/'output/video_decisions/decisions'/f"{db['id']}.json",db)
dec=read(ep/'decisions.json');dec['decisions'].extend([ds,db]);write(ep/'decisions.json',dec)
s=read(ep/'state.json');s.update(stage='script_v2_and_budget_review_pending',script_revision='script-v2',source_script_sha256=sha(script),narration_characters=count,budget_credit_cap=cap,pending_gate='script_and_budget',pending_decision_ids={'script':ds['id'],'budget':db['id']},paid_generation_authorized=False)
s['active_tasks']=['local_editor_preparation'];write(ep/'state.json',s)
p=read(ep/'preflight.json')
for gate,d in [('script',ds),('budget',db)]:p['approvals'][gate].update(decision_id=d['id'],artifact_hashes=d['artifact_hashes'],status='pending')
p['approvals']['budget'].update(credits_cap=cap,cash_cap=0,automatic_retry_allowed=False)
write(ep/'preflight.json',p)
f=send_file(out/'script_v2.md','창릉 수정 대본 v2: 통근시간·현재 교통·본청약 가격 구분 반영. 영상용 자료 준비 중이며 유료 음성·본편 렌더는 아직 시작하지 않았습니다.')
notice=send(f"창릉 수정 대본 v2 독립 검수 완료. 대본 확정: /approve {ds['id']}\n음성예산: {count}자+수정여유{reserve}자, 포함크레딧최대{cap}, 추가결제0원. 승인: /approve {db['id']}\n자동재시도·충전·초과결제·새유료이미지음악은 제외합니다. 기존 브랜드/BGM 재사용. 프로젝트 AGENTS.md의 버전별 대본/예산 게이트에 따라 새 파일과 상한을 묶었습니다. 승인 후 음성→타임록→편집·렌더를 이어갑니다.")
receipt={'script_decision_id':ds['id'],'budget_decision_id':db['id'],'characters':count,'reserve':reserve,'credits_cap':cap,'file_sent':f,'notice_sent':notice,'script_sha256':sha(script)}
write(out/'review_request.json',receipt);print(json.dumps(receipt))
