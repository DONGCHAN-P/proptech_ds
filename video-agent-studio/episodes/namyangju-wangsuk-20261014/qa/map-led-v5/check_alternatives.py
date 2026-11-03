import json,pathlib,xml.etree.ElementTree as ET,hashlib,statistics
p=pathlib.Path(__file__).parent;e=p.parents[1];src=e/'research/alternatives-v5';c=json.loads((src/'comparison.json').read_text(encoding='utf-8'));raw=json.loads((src/'raw_verified_rows.json').read_text(encoding='utf-8'));names={f['name'] for f in c['facts']};rows=[]
for info in raw['files']:
 f=pathlib.Path(info['path']);assert hashlib.sha256(f.read_bytes()).hexdigest()==info['sha256']
 for item in ET.parse(f).findall('.//item'):
  d={x.tag:(x.text or '').strip() for x in item}
  if d.get('aptNm') not in names:continue
  date=f"{d['dealYear']}-{int(d['dealMonth']):02d}-{int(d['dealDay']):02d}"
  if not('2026-07-01'<=date<='2026-09-30') or not(83<=float(d['excluUseAr'])<85) or int(d['floor'])<5 or d.get('cdealDay') or d.get('cdealType') in ['O','Y']:continue
  amount=int(d['dealAmount'].replace(',',''));assert amount>0
  rows.append((d['aptNm'],amount,date))
checks=[]
for fact in c['facts']:
 vals=[r[1] for r in rows if r[0]==fact['name']];assert len(vals)==fact['n'] and statistics.median(vals)==fact['median_manwon'] and [min(vals),max(vals)]==fact['range_manwon']
 checks.append({'claim_id':fact['claim_id'],'name':fact['name'],'n':len(vals),'median_manwon':statistics.median(vals),'range_manwon':[min(vals),max(vals)],'passed':True})
r={'revision':'map-led-v5-early','raw_independent_recount':True,'total_final_rows':len(rows),'groups':checks,'collection_date':'2026-10-13','contract_period':'2026-07-01~2026-09-30','filter':'83<=전용<85㎡,5층+,취소제외,양수금액','limitations':['10/15API갱신미조회','실제역보행거리미확인','정확면적/층/동향/연식/신축기축품질보정없음','기축매매vs공공분양옵션미포함표시가격','진접표본0,대체시세추정금지'],'required_issue':'handoff 59표본 표기 현재 실제49행과 불일치; 연구 정정 요청','outline_review':'전체계획→5요소 편의와 WHEN→대체가격VALUE→블록조건부후보 순서 적절. 사실인계 전 candidate 위치/개통/학교 추정 및 현재청약가능 언급 금지.','script_review':'pending script_v3','user_review_ready':False}
(p/'early_findings.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print('49 rows independent recount passed')
