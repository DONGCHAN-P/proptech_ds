from pathlib import Path
import json,hashlib,sys
P=Path(__file__).parent
sys.path.insert(0,str(Path('video-agent-studio/episodes/namyangju-wangsuk-20261014/research/map-led-v5/_pdfdeps').resolve()))
import pymupdf
D='2026-10-19';F=[]
src=json.loads((P/'download_manifest.json').read_text(encoding='utf-8'))+json.loads((P/'latest_plan_manifest.json').read_text(encoding='utf-8'))
U={r['file']:r.get('url',r.get('entry_url')) for r in src}
def loc(file,term):
 d=pymupdf.open(P/file)
 return ', '.join('p'+str(i+1) for i,p in enumerate(d) if term in p.get_text())
def fact(cid,s,file,where,date,status='verified',**kw):
 F.append(dict(claim_id=cid,statement=s,source_url=U.get(file),source_file=str(P/file),evidence_location=where,as_of=date,checked_on=D,status=status,**kw))
plan='latest_plan_20261008.pdf';a='a2_corrected.pdf'
fact('GY-PLAN-LATEST','하남교산 최신 확인 지구계획은 2026-10-08 국토교통부고시 제2026-535호 5차 변경이다.',plan,'p1','2026-10-08',development_status='approved_plan')
fact('GY-PLAN-SIZE','전체 6,858,234㎡, 본단지 6,311,551㎡, 기업이전단지 546,683㎡다.',plan,'p1','2026-10-08')
fact('GY-PLAN-HOMES','5차 계획 주택수는 36,669호, 수용인구 87,319인이다.',plan,'p3 인구·주택수용계획','2026-10-08',development_status='approved_plan',caution='웹33천호/2026.7보고36,697호는 이전값; 입주완료 호수 아님')
fact('GY-PLAN-LAND','본단지 공원녹지는 2,147,612㎡(34.0%), 자족시설은 556,665㎡(8.8%)다.',plan,'p2 토지이용계획(변경없음)','2026-10-08',development_status='approved_plan',caution='자족시설과 도시지원시설 총598,849㎡9.5%를 혼동하지 말 것')
fact('GY-PLAN-END','본단지 및 기업이전단지 사업시행기간 종기는 2028-12-31이다.',plan,'p1','2026-10-08',caution='지구조성 사업기간이며 개별 아파트 입주일/철도개통일이 아님')
fact('GY-A2-SUPPLY','A2는 공공분양 1,115세대, 전용51~59㎡대다.',a,'p1·p4 공급대상','2025-04-24 정정공고',development_status='construction')
fact('GY-A2-MOVE','A2 입주 예정은 2029년 6월이며 공정에 따라 변동될 수 있다.',a,loc(a,'입주예정 시기는 2029'),'2025-04-24 정정공고',status='qualified')
fact('GY-A2-PRICE51','A2 51A 전용51.87㎡ 5층 이상 기본 공급금액 497,640,000원이다.',a,'p5 공급금액표','2025-04-24 정정공고',price={'statistic':'특정타입·층구간 공고가','scope':'교산 A2 51A','exclusive_area_sqm':51.87,'floor':'>=5','transaction_period':'2025년 본청약 공고','transaction_type':'공공분양 최초공급/실거래 아님','sample_size':248,'sample_definition':'해당 층구간 공급세대수/거래표본 아님','unit':'원','amount_krw':497640000,'balcony_extension_krw':4944000,'basic_plus_extension_krw':502584000,'aggregation':'공고두항목 단순합','cancelled_transactions':'해당없음','excluded':['유상옵션','취득세 등']})
fact('GY-A2-PRICE59','A2 59A 전용59.99㎡ 5층 이상 기본 공급금액 571,670,000원이다.',a,'p6~7 공급금액표; p8 확장비표','2025-04-24 정정공고',price={'statistic':'특정타입·층구간 공고가','scope':'교산 A2 59A','exclusive_area_sqm':59.99,'floor':'>=5','transaction_period':'2025년 본청약 공고','transaction_type':'공공분양 최초공급/실거래 아님','sample_size':47,'sample_definition':'해당 층구간 공급세대수/거래표본 아님','unit':'원','amount_krw':571670000,'balcony_extension_krw':6888000,'basic_plus_extension_krw':578558000,'aggregation':'공고두항목 단순합','cancelled_transactions':'해당없음','excluded':['유상옵션','취득세 등']},caution='교산전체평균/84㎡분양가/현재신규청약가로 쓰지 말 것')
fact('GY-A2-EXTENSION','A2는 전 세대 확장형이며 발코니 비확장을 선택할 수 없다.',a,'p8','2025-04-24 정정공고')
fact('GY-A2-RESALE','공고상 전매제한은 당첨자발표일부터 3년이다.',a,'p3·p27~28 전매행위제한','2025-04-24 정정공고',status='qualified',caution='공고 당시 조건; 등기 등 예외 포함 원문 확인. 개인별 현재 처분가능일 확정금지')
fact('GY-A2-RESIDENCE','공고상 거주의무 3년이며 개시일은 최초 입주가능일부터 3년 이내에서 정한다.',a,'p28 거주의무','2025-04-24 정정공고',status='qualified',caution='전매제한과 기산일 다름; 현행 개인법률판단 아님')
fact('GY-A2-SCHOOL','신설 교산초1 개교 전 천현초, 교산중1 개교 전 하남중학군 임시배치 예정이다.',a,loc(a,'하남교산초1'),'2025-04-24 정정공고',status='qualified',development_status='approved_plan',caution='배치계획 변경 가능; 개교월 미확정')
fact('GY-A2-SOUTH','공고상 A2 남측은 녹지·공원·초1·유1·중1·고3·공공청사 계획용지다.',a,loc(a,'초등학교(초1)'),'2025-04-24 정정공고',development_status='approved_plan')
fact('GY-RAIL-STATUS','2026-09-22 하남시 답변은 송파하남선 3·4공구 실시설계 진행, 2032년 적기개통 목표로 설명한다.','rail_20260922.html','답변일시2026-09-22·답변 나항','2026-09-22',status='qualified',development_status='approved_plan',caution='실시설계는 영업운행/전구간토목착공의 증거 아님; 개통확정 표현금지')
fact('GY-RAIL-GAP','A2 2029.6 입주 예정과 송파하남선 2032 목표 사이에는 기존 교통을 이용할 기간이 예상된다.',a,'입주예정+rail_20260922.html 답변','2026-09-22',status='qualified',derivation='두 공식 예정시점 비교; 개통월 미정이므로 정확한 개월수 산출금지')
rail=json.loads((P/'rail_map_manifest.json').read_text(encoding='utf-8'));U['hanam_rail_official_202510.pdf']=rail['url'];src.append(rail)
fact('GY-RAIL-CONNECTION','하남시 공식 노선도는 오금–100(서울)–101(감일)–102·103·104(교산)–105(하남시청)으로 송파하남선을 표시한다.','hanam_rail_official_202510.pdf','p9 상단 노선도/rail_official_p9.png 시각확인','2025-10',status='qualified',development_status='approved_plan',caution='번호는 계획정거장 표기, 정식역명·정밀출입구 아님. 도면연결 사실만 독립재구성. 하단GTX는검토/위례신사연장은건의중으로별도단계.')
fact('GY-JOBS-RELOCATION','2026.7 하남시 보고의 기업이전 대상은 1,241개 업체다.','council_20260722.html','13-11~12페이지 기업이전단지 조성 발언','2026-07-22',status='qualified',caution='새 대기업 유치/신규고용확정 수 아님; 기존기업 이전대책')
F.append({'claim_id':'GY-RAIL-CURRENT','statement':'5호선 하남시청역과 하남검단산역은 2021-03-27 개통했다.','source_url':'https://www.hanam.go.kr/www/selectBbsNttView.do?bbsNo=1164&key=10221&nttNo=260982','source_file':None,'evidence_location':'2021-04-01 하남시 개통 후 보도','as_of':'2021-04-01','checked_on':D,'status':'verified','development_status':'operating','caution':'현재운임·배차·집앞총통근시간 미검증'})
F.append({'claim_id':'GY-LIFE-STARFIELD','statement':'스타필드 하남은 미사대로750 소재 기존 운영시설이다.','source_url':'https://www.starfield.co.kr/hanam/about/directions.do','source_file':None,'evidence_location':'운영사 오시는길·운영시간 페이지','as_of':D,'checked_on':D,'status':'verified','development_status':'operating','caution':'교산각블록 도보시간 미측정; 사진 재사용권한 미확인'})
prices=json.loads((P/'existing_prices_all.json').read_text(encoding='utf-8'))
selected=['한솔리치빌(1단지)','하남자이','꿈동산신안','대명강변타운','미사레스티아','감일한라비발디']
for i,name in enumerate(selected,1):
 r=next(x for x in prices['results'] if x['name']==name)
 F.append({'claim_id':f'GY-EXISTING-{i}','statement':f"{name} 2026Q3 전용83≤㎡<85·5층이상·해제제외 매매 중위값 {r['median_manwon']/10000:g}억원, n={r['n']}건.",'source_url':'https://www.data.go.kr/data/15126468/openapi.do','source_file':str(P/'existing_price_rows.csv'),'evidence_location':f'aptNm={name}; 월별price_raw/41450_202607~09.xml','as_of':'2026Q3 계약 / 2026-10-19 조회','checked_on':D,'status':'qualified','price':dict(statistic='median',scope=name,region=r['dong'],exclusive_area_sqm='83<=x<85',floor='>=5',transaction_period='2026-07-01~2026-09-30',transaction_type='아파트매매 중개·직거래 포함',sample_size=r['n'],unit='만원',amount=r['median_manwon'],aggregation='공식XML item별 중위값; 날짜/면적/층 임의중복제거 없음',cancelled_transactions='cdealType 또는 cdealDay 비어있지 않으면 제외'),'caution':'A2 59㎡와 면적·주택연식·취득조건 다름; 차익산출금지; 향후해제 가능'})
for cid,s in [('GY-FUTURE-PRICE','교산 미래가격·상승률·확정대장 순위'),('GY-JOBS-TIME','교산 집앞에서 강남·잠실·판교까지의 현재 출근 총시간'),('GY-NEW-BLOCK-PRICES','A2 외 블록의 최신 본청약 가격·일정')]:
 F.append(dict(claim_id=cid,statement=s,source_url=None,source_file=None,evidence_location='검증근거 없음',as_of=D,checked_on=D,status='unverified',usage='수치 생성금지; 분석질문으로만 사용'))
(P/'facts.json').write_text(json.dumps({'revision':'gyosan-research-v1','checked_on':D,'facts':F},ensure_ascii=False,indent=2),encoding='utf-8')
(P/'sources.json').write_text(json.dumps({'revision':'v1','sources':src,'rtms':prices['sources'],'copyright':'공식 데이터 사실 재구성 권장. HUIC ESG 원도 및 현장사진은 재사용권리 미확정; 원도 직접삽입 승인 아님. 토지이음 고시자료 공공누리 출처표시 안내, 도면은 해당표제·출처 유지.'},ensure_ascii=False,indent=2),encoding='utf-8')
summary='''# 교산 대본용 연구 v1

기준일 2026-10-19. 확정 미래시세 없음. 최신 지구계획 5차(2026.10.08)를 우선한다.

## 5조건 순서
전체계획 → ①일자리 → ②교통 → ③공고가격 → ④학교·생활 → ⑤입주·거래조건 → 기존집 대안 → 후보권역.

최신 계획: 전체 6,858,234㎡(본단지6,311,551㎡), 36,669호·87,319인. 3기 공식웹33천호와 7월 시의회36,697호는 최신값 아님. 공원녹지34.0%, 자족시설8.8%. 자족용지는 고용완료 수치가 아니다. 사업종기2028.12와 A2입주2029.6은 다른 일정이다.

① 일자리: 강남·잠실·판교는 이동방향이 다른 비교 목적지로 제안한다. 통근순위나 교산거주자의 실제출근지 통계로 표현하지 않는다. 기업이전 대상1,241개는 기존기업 이전대책이며 신규일자리 확정 수가 아니다. 강남/판교 분당권 위치와 현재 접근 구간을 보여주되 분 단위 미확인.

② 교통: 현재 5호선 운영역과 장래 송파하남선을 분리한다. 2026.9.22 공식답변의 3·4공구는 실시설계 중, 2032개통목표. A2입주2029.6과 간격을 같은 달력으로 보여준다. 2032개통 확정/현재 3호선 운행/강남30분 확정 금지.

③ 공고가격: A2 51A 51.87㎡ 5층이상 기본497,640,000+확장4,944,000=502,584,000원. 59A 59.99㎡ 5층이상 기본571,670,000+확장6,888,000=578,558,000원. 유상옵션·세금별도. 확장선택불가이므로 확장포함합계를 실제 비교 출발값으로 권장. 거래가·평균가·84㎡가격이 아니다. 본청약공고 사례이지 현재접수표가 아니다.

④ 생활: A2 남측 초1·유1·중1·고3·공원·공공청사는 계획. 신설초 개교전 천현초 임시배치, 중학교는 하남중학군 임시배치 공고. 개교월 미확인. 스타필드하남은 기존 운영시설이지만 모든교산블록 도보생활권으로 과장금지. 기존생활권 접속과 새상권 성숙을 나누어 설명.

⑤ 공급·거래: A2공고 총1,115세대 전용51~59㎡대/2029.6예정. 다른블록 공급계획은 최신계획표에 있으나 분양가격·청약일정 확정아님. 전매3년은 당첨발표 기산, 거주의무3년은 별도기산. 임의 자유매매가능일 산출금지.

## 기존집 대안 (2026Q3, 전용83≤㎡<85, 5층이상, 해제표시제외, 중개+직거래, 중위값)
'''
for name in selected:
 r=next(x for x in prices['results'] if x['name']==name);summary+=f"- {name}: {r['median_manwon']/10000:g}억원, n={r['n']} ({r['dong']})\n"
summary+='''
월별 공식응답은 2026-10-19 조회, 7월317건/8월246건/9월182건 전체응답수와 totalCount 일치. 각 단지는 해당조건 필터 표본이다. CSV 원행·해제조건·SHA sources 보존. A2 59㎡와 기존84㎡는 평형·준공시점·취득조건이 다르므로 가격차를 미래차익으로 연결하지 않는다.

## 대장 후보 표현 제안
북부 기존생활권 접점 / 중앙 계획역세권 복합중심 / 남부 자족·녹지 축은 편집상의 설명구간이다. 행정권역/가격서열이 아니다. 현재 대장 확정 대신 조건부 후보: 초기 교통·기존생활 우선, 장래 역세권 연결 우선, 공원·학교 연속동선 우선으로 평가한다. A2는 가격·입주시점이 공고된 확인기준점이며 큰평형대장으로 단정하지 않는다. 향후 출입구/학교개교/실제분양가/공급시점/소음·경사·도로횡단을 확인해야 순위를 좁힐 수 있다.

## 지도와 권리
HUIC ESG p17의 2024 전체도는 참고원도. 최신5차 첨부지도는 지구밖도로 부분도여서 전체도로 쓰지 않는다. LH geometry는 조회버전 표기해 재구성. 역정밀핀·출입구·도보분 임의생성금지. 실제시설사진의 재사용권리는 별도확인 전 미확인.
'''
(P/'summary.md').write_text(summary,encoding='utf-8')
outputs=['facts.json','sources.json','summary.md','existing_prices_all.json','existing_price_rows.csv','latest_plan_20261008.pdf','latest_plan_map_20261008.pdf','a2_corrected.pdf']
handoff={'role':'research','revision':'v1','inputs':['brief.json/current','state.json/research_in_progress','최신5차고시2026-535','A2정정2025.4.24','국토부실거래2026Q3_2026.10.19조회'],'outputs':[str(P/x) for x in outputs],'verification':['공식고시 원문PDF와텍스트','A2확장비p8 이미지시각확인','HUIC2024원도p17 시각확인','최신5차지도는부분도임시각확인','실거래3개월 totalCount=item수745건 대조','모든JSON재파싱·필수필드확인'],'unresolved':['미래가격·상승률 없음','A2외 본청약가격미확인','강남잠실판교집앞총시간미측정','신설학교개교월미확인','전체지도geometry의고시일일치visual확인필요','사진및HUIC원도재사용권리미확인'],'affected_scene_ids':['전체계획','일자리','교통','가격','생활','공급','대안','후보'],'next_owner':'director/writer 및 visual','paid_api_calls':0}
(P/'handoff.json').write_text(json.dumps(handoff,ensure_ascii=False,indent=2),encoding='utf-8')
for n in ['facts.json','sources.json','handoff.json']:json.loads((P/n).read_text(encoding='utf-8'))
assert all(set(['claim_id','statement','source_url','source_file','evidence_location','as_of','checked_on','status'])<=f.keys() for f in F)
print({'facts':len(F),'outputs':[(x,(P/x).stat().st_size) for x in outputs]})
