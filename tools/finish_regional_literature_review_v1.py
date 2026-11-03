"""Verify and deliver the literature report; retain the voice hold and old media."""
from pathlib import Path
import argparse,datetime as dt,hashlib,json,os,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
EP=ROOT/'video-agent-studio/episodes/regional-price-recovery-20261022'
REPORT=ROOT/'reports/서울 경기 집값 격차의 복합 원인.md'
DEST=EP/'outputs/literature-review-v1'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(ROOT).as_posix()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--qa',required=True);ap.add_argument('--send',action='store_true');args=ap.parse_args()
    qp=(ROOT/args.qa).resolve();qp.relative_to(EP/'qa/literature-mechanisms-v1')
    qa=read(qp);assert REPORT.stat().st_size>5000
    digest=sha(REPORT);assert qa['counts']['required_open']==0 and str(qa['report_sha256']).lower()==digest
    assert sha(EP/'outputs/script-review-v3/script_v3.md')=='99b40e8730ee0f8fdf74402cffbe04b5b418540344e6d2a7175e6a01c3054664'
    assert sha(EP/'outputs/production-v1-jun/previews/full_visual_review_v1.mp4')=='bba7566079f9d452663f2adccaff8d1a5aff66f41fd298d893ab32c240babd89'
    assert sha(ROOT/'config/current_video.json')=='2cfbd606ce61a3b547e7a441c0f15d5270b1e7837c6ed4363dba813382ebfa4c'
    assert read(ROOT/'output/video_decisions/decisions/5fe307eed02c.json')['resolution']=='deferred_by_user'
    assert not(EP/'narration/production-v1/authorization.json').exists()
    DEST.mkdir(parents=True,exist_ok=True)
    record={'at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'task_id':'RPR-LIT-20261023',
        'status':'literature_report_ready_local_tests_pending','report':rel(REPORT),'report_sha256':digest,'bytes':REPORT.stat().st_size,
        'qa':rel(qp),'qa_sha256':sha(qp),'required_open':0,'local_causal_estimates_performed':False,
        'new_script_written':False,'voice_generation':'deferred_by_user','paid_generation_calls':0,'new_render':False}
    write(DEST/'delivery_manifest.json',record)
    state=read(EP/'state.json');state.update(stage='literature_report_ready_insight_validation_pending',updated_at=record['at_utc'],
        research_status='Literature mechanisms reviewed; hypotheses and external-data tests specified; no local causal decomposition yet',
        literature_report=rel(REPORT),literature_report_sha256=digest,literature_qa=rel(qp),
        literature_delivery_manifest=rel(DEST/'delivery_manifest.json'),next_script_status='not_written_not_approved')
    assert state['budget_status']=='voice_generation_deferred_by_user';write(EP/'state.json',state)
    shelf=read(ROOT/'config/video_shelf.json');entry=next(e for e in shelf['entries']if e['name']=='지역별가격회복')
    entry['status']='복합 원인 논문 조사 v1 완료 · 지역별 검증 가설·추가 데이터 계획 정리 · 우리 실거래 인과분석·새 대본 미실행 · 음성 생성 보류 · 기존 영상 보존.'
    entry['files']['논문조사.md']=rel(REPORT);entry['files']['논문조사_검수.json']=rel(qp);write(ROOT/'config/video_shelf.json',shelf)
    print(json.dumps({'report_integrity':'pass','report_bytes':REPORT.stat().st_size,'required_open':0,'voice':'deferred'},ensure_ascii=False),flush=True)
    if not args.send:return
    preference=read(EP/'state.json').get('literature_delivery_preference',{})
    if preference.get('mode')=='local_only' and preference.get('report_sha256')==digest:
        print(json.dumps({'telegram_status':'disabled_by_user_local_only','network_request_executed':False}))
        return
    from notify import telegram as tg
    receipt=ROOT/'output/telegram_deliveries/regional_literature_mechanisms_v1.json'
    if receipt.exists():
        old=read(receipt)
        if old.get('ok'):
            assert old['report_sha256']==digest;print(json.dumps({'telegram_ok':True,'already_delivered':True}));return
        raise RuntimeError('Inspect the previous report delivery before repeating')
    assert read(ROOT/'config/video_telegram_bridge.json')['private_chat_only']
    token,cid=tg.creds();expected=os.environ.get('TELEGRAM_USER_ID','').strip()or(cid if cid.isdigit()else'')
    assert token and cid.isdigit()and cid==expected
    chat=tg._post('getChat',token,data={'chat_id':cid});assert chat.get('ok')and chat['result']['type']=='private'and str(chat['result']['id'])==cid
    result={'at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'status':'request_started','ok':False,'report_sha256':digest,'private_recipient_verified':True}
    write(receipt,result)
    caption='서울·경기 집값 격차의 복합 원인 — 논문 조사 v1\n일자리·가구·구매력, 공급·재건축·전세, 교통·공간 전이 연구를 통합했습니다. 논문이 확인한 결과와 우리 실거래에서 검증할 가설을 구분하고, 출처·독서 범위·추가 데이터 계획을 기록했습니다.\n이번 결과는 문헌 조사입니다. 새 대본과 영상은 만들지 않았고 음성 생성 보류를 유지했습니다.'
    with REPORT.open('rb')as stream:
        response=tg._post('sendDocument',token,data={'chat_id':cid,'caption':caption},files={'document':(REPORT.name,stream,'text/markdown')},timeout=55)
    result.update(ok=bool(response.get('ok')),status='delivered'if response.get('ok')else'delivery_uncertain',message_id=(response.get('result')or{}).get('message_id'))
    if not result['ok']:result['error']=tg.mask(response.get('error','Unknown'),token)
    write(receipt,result)
    if result['ok']:
        state=read(EP/'state.json');state['literature_telegram_receipt']=rel(receipt);write(EP/'state.json',state)
    print(json.dumps(result,ensure_ascii=False));raise SystemExit(0 if result['ok'] else 1)
if __name__=='__main__':main()
