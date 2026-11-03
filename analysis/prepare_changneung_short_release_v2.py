"""Record direct scoped release instruction, preserving all five gates."""
import json, hashlib, secrets
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[1];EP=ROOT/'video-agent-studio/episodes/goyang-changneung-20261015';OUT=EP/'outputs/shorts-release-v2';OUT.mkdir(exist_ok=True)
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not (OUT/'upload_job.json').exists(), 'Already prepared; inspect existing job'
video='outputs/shorts-leader-v2/changneung_leader_short_v2.mp4';h=sha(EP/video);assert h=='6f44ee06f7594380275b1efd1da111e1836425197c9739729c33be377d2135ec'
now=datetime.now(timezone.utc).isoformat();ids={g:secrets.token_hex(6) for g in ['script','budget','completed','pre_upload']}
job={'video':str((EP/video).relative_to(ROOT)).replace('\\','/'),'sha256':h,'qa':str((EP/'qa/shorts-leader-v2/final_review.json').relative_to(ROOT)).replace('\\','/'),'channel_id':'UCr_mTC0x_Uobv6MrIsOkrXw','privacy':'private','publish_at':'2026-10-19T08:30:00Z','title':'3기 신도시 창릉의 대장단지는 어디가 될까?','description':'고양 창릉 S1·S4·S5 가운데 대장 후보는 어디일까요?\nS4는 가격수준을 이끌 후보로 먼저 살펴본 것이며, 상승률이 가장 높다는 결론은 아닙니다.\n\n전체 지도·교통·분양가·주변 시세 비교 본편\nhttps://youtu.be/eLF3-1ZaraQ\n\n가격은 각 모집공고의 전용 84㎡급·5층 기본가와 발코니 확장비 사례입니다. S5 약 7.77억(2025.01.31), S1 약 7.90억(2026.04.30), S4 약 8.73억(2026.06.30). 공고 시점과 타입이 다르며 옵션·세금은 별도입니다. 현재 매수 가능 가격이나 미래 수익률을 뜻하지 않습니다. 자료: LH 모집공고·공개 토지이용계획 및 본편 출처.\n\n#고양창릉 #창릉신도시 #3기신도시 #분양가 #Shorts','tags':['고양창릉','창릉신도시','3기신도시','S1','S4','S5','분양가','대장아파트','Shorts'],'approval_file':'output/video_decisions/decisions/'+ids['pre_upload']+'.json'}
save(OUT/'upload_job.json',job)
artifacts={p:sha(EP/p) for p in [video,'outputs/shorts-leader-v2/changneung_leader_short_v2.srt','qa/shorts-leader-v2/final_review.json']}
dec=read(EP/'decisions.json');records=dec['decisions']
for old in records:
    if old.get('id') in ['cd653bc196a7','e2831600c47f']:
        old.update(status='superseded',superseded_by=ids[old['gate']],reason='User requested full-frame v2 and now explicitly directs same-time upload')
        save(ROOT/'output/video_decisions/decisions'/f"{old['id']}.json",old)
for gate,id in ids.items():
    d={'id':id,'episode':'goyang-changneung-20261015','gate':gate,'status':'approved' if gate!='budget' else 'not_applicable','created_at':now,'approved_at':now,'video_kind':'shorts','video_revision':'shorts-leader-v2','scope':'exact_full_frame_v2_scheduled_2026-10-19_1730_KST','response_source':'direct_user_explicit_schedule_request','response_summary':'작업 마무리되는대로 쇼츠도 17시 30분 똑같이 업로드되도록 세팅','video_sha256':h,'artifact_hashes':artifacts,'new_paid_generation_authorized':False,'cash_cap_krw':0}
    if gate=='script':d['unchanged_excerpt_reference']='outputs/shorts-leader-v1/source_excerpt_selection.json';d['excerpt_sha256']=sha(EP/d['unchanged_excerpt_reference'])
    if gate=='pre_upload':d.update(job_sha256=sha(OUT/'upload_job.json'),publish_at=job['publish_at'],channel_id=job['channel_id'],completed_decision_file='output/video_decisions/decisions/'+ids['completed']+'.json',upload_authorized=True)
    records.append(d);save(ROOT/'output/video_decisions/decisions'/f'{id}.json',d)
save(EP/'decisions.json',dec);save(OUT/'approval_manifest.json',{'topic':'dd9fc5695a3c',**ids,'budget_policy':'no_new_paid_calls','video_sha256':h})
print(json.dumps({'prepared':True,'decisions':ids},ensure_ascii=False))
