from pathlib import Path
import json,re,hashlib,shutil
p=Path(__file__).resolve().parents[1];root=p.parents[2];w=p/'writer';out=p/'outputs/script-review-v1';out.mkdir(parents=True,exist_ok=True)
def read(n):return json.loads((p/n).read_text(encoding='utf-8-sig'))
kr=read('research/korea_sources.json');mt=read('research/method_sources.json')
ledger=[]
for x in kr['claims']+mt['sources']:
 if 'url' not in x:continue
 ledger.append({'claim_id':x['claim_id'],'claim':x.get('문장',x.get('sentence')),'url':x['url'],'source_date':x.get('기준일',x.get('reference_date')),'accessed':'2026-10-20','strength':x['status'],'location':x.get('근거위치',x.get('location')),'verification_scope':'research担当の原文/公式検索本文の確認記録を再利用。writer/Claudeによる独立原文再閲覧ではない。','notes':x.get('note','')})
for x in ledger:x['verification_scope']='조사 담당의 원문·공식 검색본문 확인 기록을 재사용. 작가·Claude의 독립 원문 재열람은 아님.'
ledger.extend([{'claim_id':'SIM01','claim':'가상기본/민감도120월 장부와 동일 초기순자산·월예산','file':'research/illustrative_results.json','strength':'hypothetical_executed','source_date':'illustrative-v1','accessed':'2026-10-20'},{'claim_id':'QA01','claim':'모형 독립검산 통과 범위 및 제한','file':'qa/model-review/findings.json','strength':'independent_passed_with_limits','source_date':'2026-10-20','accessed':'2026-10-20'},{'claim_id':'SHEET01','claim':'원본시트 표본감사, 개인금액비공개','file':'research/sheet_audit.json','strength':'sample_audit_only','source_date':'2026-10-20','accessed':'2026-10-20'}])
urls=sorted(set(x['url'] for x in ledger if 'url'in x))
(w/'source_ledger.json').write_text(json.dumps({'revision':'writer-v1','unique_source_urls':len(urls),'claim_entries':len(ledger),'sources':ledger},ensure_ascii=False,indent=2),encoding='utf-8')
story=(w/'visual_storyboard.md').read_text(encoding='utf-8');rows=[x for x in story.splitlines() if re.match(r'\| S\d{3} ',x)]
ids={1:['SIM01'],2:['SIM01'],3:[],4:['SIM01'],5:['SIM01'],6:['SIM01'],7:['SIM01'],8:['SIM01'],9:['SIM01'],10:['SIM01'],11:['SIM01','QA01','M01'],12:['SIM01','M01'],13:['SIM01','SHEET01'],14:['M08','M09','M10','M11'],15:['SIM01'],16:['M06'],17:['SIM01','QA01'],18:['SIM01','QA01'],19:['SIM01'],20:['SIM01','QA01'],21:['SIM01'],22:['SIM01'],23:['SIM01','QA01'],24:['KR001','KR003','KR004'],25:[]}
scenes=[]
for i,line in enumerate(rows,1):
 cells=[c.strip() for c in line.strip('|').split('|')]
 scenes.append({'scene_id':f'S{i:03}','narration_anchor':cells[1],'purpose':cells[2],'visual_direction':cells[3],'evidence':cells[4],'asset_status_and_fallback':cells[5],'claim_ids':ids[i],'asset_types':[t for t in ['real_photo','data_chart','map','ai_concept','editorial_card'] if t in cells[2]],'estimate_duration_seconds':34 if i<25 else 40,'timing_basis':'estimate; no audio generated','script_revision':'script-v1','status':'proposal_not_approved'})
(w/'scene_proposals.json').write_text(json.dumps({'revision':'scene-proposals-v1','common_scenes_modified':False,'scenes':scenes},ensure_ascii=False,indent=2),encoding='utf-8')
(w/'claim_map.json').write_text(json.dumps({'revision':'v1','scenes':[{'scene_id':s['scene_id'],'narration_anchor':s['narration_anchor'],'claim_ids':s['claim_ids']}for s in scenes]},ensure_ascii=False,indent=2),encoding='utf-8')
pron={'S&P500':'エスアンドピーごひゃく','ETF':'イーティーエフ','LTV':'エルティーブイ','DSR':'ディーエスアール'}
pron={'S&P500':'에스 앤드 피 오백','ETF':'이 티 에프','LTV':'엘 티 브이','DSR':'디 에스 알','원리금균등':'원금과 이자를 합친 같은 금액을 갚는 방식','전용면적':'집 안에서 전용으로 쓰는 면적'}
(w/'narration_handoff.json').write_text(json.dumps({'status':'draft_not_approved_no_TTS','pronunciation':pron,'emphasis':['같은 집','같은 초기 순자산','같은 월예산','남은 대출','가정','평가 순자산'],'number_rule':'숫자·단위 묶기. 원장정밀값과 낭독반올림값 구분.','estimated_duration_minutes':[13,16],'timing_basis':'7438 Korean narration characters; actual voice duration not measured'},ensure_ascii=False,indent=2),encoding='utf-8')
for n in ['script_v1.md','visual_storyboard.md','source_ledger.json','claim_map.json','scene_proposals.json','narration_handoff.json']:
 shutil.copy2(w/n,out/n)
shutil.copy2(w/'script_v1.md',w/'script.md')
print(json.dumps({'unique_urls':len(urls),'claims':len(ledger),'scenes':len(scenes),'output':str(out)},ensure_ascii=False))

