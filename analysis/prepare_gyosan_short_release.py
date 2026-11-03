"""Bind the requested derivative Short to exact artifacts, preserving main gates."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib

ROOT = Path(__file__).resolve().parents[1]
EP = ROOT/'video-agent-studio/episodes/hanam-gyosan-20261019'
OUT = EP/'outputs/shorts-release-v1'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def rel(p): return p.relative_to(ROOT).as_posix()

def main():
    video = EP/'outputs/shorts-leader-v1/gyosan_leader_short_v1r2.mp4'
    qa_path = EP/'qa/shorts-leader-v1/final_review.json'
    qa = read(qa_path)
    digest = sha(video)
    assert qa['sha256']==digest and qa['required_unresolved']==0
    script = EP/'outputs/shorts-leader-v1/script_excerpt.md'
    source_plan = EP/'editor/shorts-leader-v1/clip_plan.json'
    artifacts = {rel(p):sha(p) for p in (video,qa_path,script,source_plan)}
    names = ('topic','script','budget','completed','pre_upload')
    ids = {name:f'gyosan-short-v1-{name}-718066306' for name in names}
    gate_paths = {name:f'output/video_decisions/decisions/{ids[name]}.json' for name in names}
    job = {
        'revision':'gyosan-short-leader-v1r2','video':rel(video),'sha256':digest,'qa':rel(qa_path),
        'channel_id':'UCr_mTC0x_Uobv6MrIsOkrXw','privacy':'public','publication_authorized':True,
        'title':'3기 신도시 하남 교산의 대장단지는 어디가 될까?',
        'description':'하남 교산에서 대장 후보로 먼저 볼 곳은 어디일까요?\n중앙 권역 C2와 B2를 토지이용계획도에서 비교합니다.\n\n전체 지도·교통·분양가·주변 시세 비교 본편\nhttps://youtu.be/XWAWnSrz7FE\n\nC2: 전용 85㎡ 초과 민간분양 786호 계획\nB2: 전용 60~85㎡ 민간분양 281호 계획\n국토교통부 고시 2026-535호(2026.10.08)·LH 공개 토지이용계획 기준입니다. 실제 분양가·면적 구성·역 출입구와 이동 경로는 추후 공개 자료로 비교할 조건입니다. 후보 선정은 입지에 대한 분석이며 미래 가격·수익률을 보장하지 않습니다.\n\n자료: 국토교통부·LH 내집어디 https://wherehome.lh.or.kr/\n본편의 기존 Jun 합성 내레이션을 발췌했으며, 지도는 공개 토지이용계획을 재구성한 도표입니다.\n\n#하남교산 #교산신도시 #3기신도시 #대장아파트 #Shorts',
        'tags':['하남교산','교산신도시','3기신도시','대장아파트','C2','B2','민간분양','Shorts'],
        'contains_synthetic_media':False,
        'disclosure_assessment':{'scope':'only_this_new_short_not_existing_channel_videos','visuals':'SVG infographic reconstructed from official land-use geometry; no generated realistic footage, places, persons or music','audio':'licensed existing Jun generic narration excerpt; no claimed real speaker or impersonation','source':'https://support.google.com/youtube/answer/14328491?hl=ko','required_human_synthetic_deception':False,'note':'Explicit description acknowledges synthetic narration. Platform may independently apply labels.'},
        'gates':gate_paths,'receipt':rel(OUT/'upload_receipt.json')
    }
    OUT.mkdir(parents=True,exist_ok=True)
    assert not (OUT/'upload_receipt.json').exists(), 'Existing upload attempt; inspect before preparing'
    save(OUT/'upload_job.json',job)
    now = datetime.now(timezone.utc).isoformat()
    decisions = read(EP/'decisions.json')
    for name in names:
        gate = {'id':ids[name],'episode':'hanam-gyosan-20261019','gate':name,'status':'not_applicable_no_new_paid_generation' if name=='budget' else 'approved','created_at':now,'video_kind':'shorts','video_revision':'shorts-leader-v1r2','video_sha256':digest,'artifacts':artifacts,'source_event':'output/telegram_conversation/inbox/718066306.json','approval_basis':'Explicit request: 하남편 쇼츠도 올려줘; derivative excerpts of approved public Jun v5, same prior promotional Shorts format; no new narration or claims. Scope excludes unrelated drafts, paid generation, or existing-video AI settings.','new_paid_generation_authorized':False,'cash_cap_krw':0}
        if name=='pre_upload': gate.update(privacy='public',channel_id=job['channel_id'],job_sha256=sha(OUT/'upload_job.json'))
        save(ROOT/gate_paths[name],gate)
        decisions['decisions'] = [d for d in decisions['decisions'] if d.get('id')!=ids[name]]+[gate]
    save(EP/'decisions.json',decisions)
    save(OUT/'approval_manifest.json',{'gates':gate_paths,'sha256':digest,'main_gates_unchanged':True})
    print(json.dumps({'job':rel(OUT/'upload_job.json'),'sha256':digest,'privacy':'public','new_paid_calls':0},ensure_ascii=False))

if __name__=='__main__': main()
