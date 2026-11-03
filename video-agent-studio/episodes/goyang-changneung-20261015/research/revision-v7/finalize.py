from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parent;R=P.parent;E=R.parent;O=E/'outputs/source-review-v7'
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
f=json.loads((P/'facts.json').read_text(encoding='utf-8'))
url='https://www.xn--3-3u6ey6lv7rsa.kr/kor/CMS/Board/Board.do?board_seq=466&mCode=MN024&mgr_seq=12&mode=view'
f['facts'] += [
 {'claim_id':'CN7-S4-PRECOMP','statement':'LH는 S4가 2022년 사전청약 당시 27:1을 기록했다고 2026-07-03 보도했다.','source_url':url,'evidence_location':'본문 S4 공급형별 설명 문단(웹 lines66)','as_of':'2022년 사전청약 회고, 발표2026-07-03','checked_on':'2026-10-18','status':'qualified','stage':'pre_subscription','block':'S4','type':'단지전체 회고값; 특정84형 아님','numerator':None,'denominator':None,'application_period':'2022년만 명시; 정확 접수일 미확보','limits':'접수구분·유형별·모집/접수 인원 미표시. 다른 블록이나 본청약 경쟁률과 비교차트 금지.'},
 {'claim_id':'CN7-ACCESS','statement':'LH는 창릉의 은평·마포 인접, 향후 GTX-A 창릉역 및 고양은평선, S3·S4의 원흥 기존 생활 인프라 공유를 설명한다.','source_url':url,'evidence_location':'본문 지구입지 및 S3/S4 생활인프라 문단(lines64-65)','as_of':'2026-07-03','checked_on':'2026-10-18','status':'qualified','development_status':'approved_plan','limits':'현재 운영역 도보접근이나 단지출입구부터의 통근시간이 아님. 역 신설 및 2031년은 보도당시 계획이며 이번 실제 개통/착공 전수확인 안함.'}
]
loc=json.loads((E/'visual/semantic-v5/verified_missing_locations.json').read_text(encoding='utf-8'))
def find(x):
 if isinstance(x,dict):
  if x.get('name')=='창릉호반써밋' and x.get('status')=='verified_official_address_locator':return x
  for v in x.values():
   a=find(v)
   if a:return a
 if isinstance(x,list):
  for v in x:
   a=find(v)
   if a:return a
point=find(loc)
tab=json.loads((P/'price_table_descending.json').read_text(encoding='utf-8'))
for r in tab:
 if r['name']=='창릉호반써밋':r.update(latitude=point['lat'],longitude=point['lon'],coordinate_source_file='visual/semantic-v5/verified_missing_locations.json',coordinate_match_status=point['status'],coordinate_limits=point['coordinate_basis']+'; 경계/출입구/centroid 아님')
write(P/'price_table_descending.json',tab)
write(P/'resale_map.geojson',{'type':'FeatureCollection','features':[{'type':'Feature','geometry':{'type':'Point','coordinates':[r['longitude'],r['latitude']]},'properties':r}for r in tab]})
f['resale_audit']=tab;write(P/'facts.json',f)
write(P/'online_checks.json',{'checked_on':'2026-10-18','s4_lh_primary_page':{'url':url,'read':True},'pdf_refresh':'web tool internal errors and local urllib URLError; preserved PDFs used, hashes match prior official download manifest','competition_s1_s5':'공식 본문 또는 부록 타입별 표 확보 실패. S5 165.7 숫자 검색결과는 있으나 공식 원문 표 미열람이므로 영상 낭독 제외','legal':'새 법률해석/매도가능일 산정 안함. 기존 전매/거주의무 주장은 새 검증으로 승격하지 않음'})
write(P/'handoff.json',{'revision':'revision-v7','input_versions':['price-stage-v3','prices-v2','production-v2','script-v4-addendum','visual/semantic-v5/verified_missing_locations.json'],'outputs':['facts.json','price_table_descending.json','resale_map.geojson','online_checks.json','report.txt',str(O)],'validation':['보존 공식PDF 3개 SHA 기존 다운로드기록 일치','기본가격표3개·발코니표3개 실제 이미지 열람','6개 중위값 및n verified_rows.csv 재계산 전부 일치','LH2026-07-03 공식페이지 실제 웹 열람'],'unresolved':['새PDF 다운로드 실패; 최신 정정본 동일성 새 검증 안됨','원문이미지 영상재사용 허락/공공누리 유형 미확인','S1/S5 공식 사전청약 경쟁률 미확보','S4 경쟁률 분자분모/주택형/접수일 미확보','호반주소대표점은 단지경계centroid 아님'],'affected_claim_ids':[x['claim_id']for x in f['facts']],'affected_scene_ids':['M004','M006','M007','M008'],'next_owner':['writer_v7','editor_v6','director']})
(P/'report.txt').write_text('''가격 상승 중심의 후보 선정은 전망 수익률 대신 조건 비교로 설명한다.
S5: 세 사례 중 낮은 본청약 진입가격7.76598억, 공고상2028.01입주예정. 기다리는 기간·입주 초기 공사·버스 연결 확인이 핵심. 창릉 전체 첫입주라고 하지 않는다(S6 2027.12 계획).
S1:7.9038억,2029.05계획. S5대비13,782,000원 높으나 연도·타입·면적이 달라 순수 프리미엄이 아니다.
S4:8.73329억,2030.03계획. 기존 원흥생활권 공유는 공식 설명으로 뒷받침되나 가장 높은 진입가격·뒤늦은 입주가 가격상승 여지에 부담인 조건이다.
공식 철도계획의 실현·현실 통근연결·생활시설 정착은 비교단지와의 격차를 재평가할 관찰 사건이다. 역 신설=이미 이용 가능으로 표현하지 않는다.
2028~2030 세 후보 공급2,277호는 부분합이지 창릉 전체 물량/확정 실입주량이 아니다. 입주 동시 공급은 단기 경쟁요인이 될 수 있다는 분석이며 가격하락을 수치 예측하지 않는다.
수요 근거는 S4 2022년 사전청약27:1 공식회고뿐. 현재가격에서 미래수요·상승률을 보장하지 않는다. 과거 경쟁률의 다른 분양가·금리·공급조건을 현재와 동일시하지 않는다.
기존단지6개는2026Q3 계약,전용83이상85미만,5층이상,국토부공식XML10/16조회,해제표시또는해제일있으면제외,응답별개거래유지,중위값.이번10/18재조회없음. 원흥n3는소표본. 분양가는특정타입/층구간이고 실거래중위와 다르다.
원문84가격crop에는표제/단위가빠질수있으므로화면에공고명·일자·PDF페이지·단위천원·타입·층을별도표기. 전체 original.png로문맥확인가능.
''',encoding='utf-8')
print('handoff verified',len(f['facts']),len(tab),len(list(O.glob('*'))))
