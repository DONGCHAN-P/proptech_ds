"""Create two private upload jobs only after exact dual media approval and main replacement."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
HERE=Path(__file__).resolve().parent;EP=HERE.parents[1];ROOT=EP.parents[2]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()
def save(p,d):
    assert not p.exists(),f'Preserve prior release record: {p}'
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
auth_path=HERE/'shorts_authorization.json';auth=read(auth_path)
assert auth['youtube_upload_authorized'] and auth['visibility']=='private' and auth['count']==2 and auth['new_ElevenLabs_credits_cap']==0
main=read(EP/'outputs/jun-release-v1/completion.json')
assert main['status']=='Jun_private_uploaded_verified_old_private_replaced' and main['new_visibility']=='private'
codex_path=EP/'qa/shorts-jun-v1/final_review.json';codex=read(codex_path)
claude_path=HERE/'claude/shorts-final-v2/receipt.json';claude=read(claude_path)
review=read(claude_path.with_name('review.json'))
assert codex['approved'] and not codex['required_issues'] and not codex.get('critical_issues',[])
assert claude['approved'] and claude['exit_code']==0 and not claude['is_error']
jobs=[];now=datetime.now(timezone.utc).isoformat()
for ident in ['funnel','analysis']:
    folder=EP/'outputs/shorts-jun-v2'/ident;render=read(folder/'renders/render_receipt.json')
    q=next(x for x in codex['shorts'] if x['id']==ident);c=next(x for x in claude['items'] if x['id']==ident);r=next(x for x in review['shorts'] if x['id']==ident)
    assert q['approved'] and c['approved'] and r['approved'] and not q['required_issues'] and not r['required_issues']
    assert q['video_sha256']==c['video_sha256']==r['video_sha256']==render['video_sha256']==sha(ROOT/render['video'])
    assert q['subtitles_sha256']==c['subtitles_sha256']==render['subtitles_sha256']==sha(ROOT/render['subtitles'])
    out=EP/'outputs/shorts-release-v2'/ident;out.mkdir(parents=True,exist_ok=True)
    if ident=='funnel':
        title='같은 2억5천만원, 10년 뒤 자산이 갈리는 이유｜매매·전세·월세 #Shorts'
        description='초기 순자산 2억5천만원, 매달 주거·저축 예산 300만원으로 같은 수준의 6억원 집에서 10년을 살면 어떻게 달라질까요?\n\n기본 가정은 집값 연 2%·투자 연 6%·대출 연 4%입니다. 월세와 보증금을 고정하고 남은 돈을 전액 같은 투자 규칙으로 운용합니다. 표시한 결과는 반올림한 평가 순자산입니다. 집값 상승률 가정만 연 4%·6%로 바꾸면 매매의 결과와 순위가 달라집니다.\n'
    else:
        title='집값 상승률만으로 비교하면 놓치는 세 가지｜매매·전세·월세 #Shorts'
        description='같은 6억원 집에서 자기자금 2억4천만원과 대출 3억6천만원의 관계, 초기 투자금과 월 적립금의 차이를 설명합니다.\n\n첫해 집값 2% 상승에 따른 평가이익 1,200만원은 집에 투입한 자기자금의 5%입니다. 이자·보유비용을 차감하기 전의 관계입니다. 이 비교의 순자산은 투자계좌와 남은 대출까지 연결해 계산합니다. 본편의 동일 자금·거주 조건으로 비교했습니다.\n'
    description+='\n전체 비교와 계산 과정: '+main['url']+'\n\n#매매 #전세 #월세 #순자산 #Shorts\n'
    assert len(title)<=100 and len(description.encode('utf8'))<5000
    metadata={'title':title,'description':description,'tags':['매매','전세','월세','순자산','주거비','Shorts'],'visibility':'private','scheduled':False,'main_video_url':main['url'],'related_video_setting':'Studio assignment tracked separately; main now observed public without changing its settings'}
    save(out/'metadata.json',metadata)
    (out/'description.md').write_text(description,encoding='utf8')
    dual={'video_sha256':render['video_sha256'],'subtitles_sha256':render['subtitles_sha256'],'required_open':[],'critical_open':[],
        'codex':{'receipt':rel(codex_path),'receipt_sha256':sha(codex_path),'approved':True},'claude':{'receipt':rel(claude_path),'receipt_sha256':sha(claude_path),'approved':True},
        'scope':'Exact Shorts media/SRT sampled review. Metadata prepared and locally validated by director; not sent to Claude. Listening/continuous playback unchecked.','at_utc':now}
    save(out/'dual_media_review.json',dual)
    save(out/'release_validation.json',{'checked_revision':render['video_sha256'],'status':'passed_with_limits','required_unresolved':[],'critical_open':[],'coverage':q.get('coverage',{}),'dual_review':rel(out/'dual_media_review.json')})
    job={'episode_root':rel(EP),'channel_id':auth['channel_id'],'privacy':'private','video':render['video'],'sha256':render['video_sha256'],'subtitles':render['subtitles'],'subtitles_sha256':render['subtitles_sha256'],'title':title,'description':description,'tags':metadata['tags'],'qa':rel(out/'release_validation.json'),'dual_review':rel(out/'dual_media_review.json'),'approval_file':rel(out/'pre_upload_decision.json'),'authorization':rel(auth_path),'burned_in_captions_verified':True,'short_id':ident}
    save(out/'upload_job.json',job)
    basis='Current direct user instruction requests two additional Shorts and uploads; existing private visibility applies. Exact dual media reviews and verified main replacement satisfy the release conditions. No human viewing is asserted.'
    save(out/'completed_decision.json',{'id':f'housing-choice-short-{ident}-jun-v2-completed','gate':'completed','status':'approved','video_sha256':render['video_sha256'],'approval_basis':basis})
    save(out/'pre_upload_decision.json',{'id':f'housing-choice-short-{ident}-jun-v2-private','gate':'pre_upload','status':'approved','video_sha256':render['video_sha256'],'job_sha256':sha(out/'upload_job.json'),'channel_id':auth['channel_id'],'privacy':'private','completed_decision_file':rel(out/'completed_decision.json'),'current_direct_user_authorization':rel(auth_path),'new_paid_generation_authorized':False,'approval_basis':basis})
    jobs.append(rel(out/'upload_job.json'))
print(json.dumps({'jobs':jobs,'uploaded':False}))
