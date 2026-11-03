from pathlib import Path
import json,sys
P=Path(__file__).parent
sys.path.insert(0,str(Path('video-agent-studio/episodes/namyangju-wangsuk-20261014/research/map-led-v5/_pdfdeps').resolve()))
import pymupdf
d=pymupdf.open(P/'latest_plan_20261008.pdf')
for i in [4,5]:d[i].get_pixmap(matrix=pymupdf.Matrix(2,2)).save(P/f'latest_plan_supply_p{i+1}.png')
for i,pg in enumerate(d):
 if any(s in pg.get_text() for s in ['A-10','B-1','C-2']):print('page',i+1,pg.get_text()[:220])
v=json.loads((P.parent/'visual/regional.json').read_text(encoding='utf-8'))
print('plans selected',[(p['name'],p['xy']) for p in v['plans'] if p['name'] in ['A-10','A-11','A-12','A-13','B-1','B-2','C-2']])
print('names',[(p['name'],p['xy']) for p in v['plans'] if any(k in p['name'] for k in ['A10','A11','A12','A13','B1','B2','C2'])])
fp=P/'facts.json';pack=json.loads(fp.read_text(encoding='utf-8'))
new=[]
url='https://eum.go.kr/web/gs/gv/gvGosiDet.jsp?seq=642455'
def add(cid,s,**kw):new.append(dict(claim_id=cid,statement=s,source_url=url,source_file=str(P/'latest_plan_20261008.pdf'),evidence_location='p5 블록별 주택건설계획 원표/ latest_plan_supply_p5.png 시각확인; p7 주1',as_of='2026-10-08',checked_on='2026-10-19',status='verified',development_status='approved_plan',**kw))
add('GY-CANDIDATE-C2','C-2는 전용85㎡초과 민간분양 786호 계획이다.',block='C-2',exclusive_area='85㎡초과',housing_type='민간분양',planned_units=786,caution='평균공급면적140㎡는호수산정용. 전용140㎡/브랜드/분양가/청약일/처분조건 확정아님')
add('GY-CANDIDATE-B2','B-2는 전용60~85㎡ 민간분양 281호 계획이다.',block='B-2',exclusive_area='60~85㎡',housing_type='민간분양',planned_units=281,caution='평균공급면적110㎡는호수산정용. 전용84㎡확정타입/브랜드/분양가/청약일/처분조건 확정아님')
add('GY-CANDIDATE-B1','B-1은 전용60~85㎡ 공공분양520호와 통합공공임대173호를 합한693호 계획이다.',block='B-1',exclusive_area='60~85㎡',housing_type='공공분양+통합공공임대',planned_units=693,caution='일반공공분양/이익공유형 세부상품은이표로미확인. 미래일반매매확정후보로단정금지')
add('GY-CANDIDATE-EXCLUSIONS','A-10은707호·A-12는788호 모두 통합공공임대, A-11은511호·A-13은622호 공공분양60㎡이하 계획이다.',caution='A10/A12일반분양대장후보에서제외. A11/A13큰평형후보아님. 표의평균공급면적85㎡를전용85㎡로잘못읽지않기')
add('GY-BLOCK-CODE-SYSTEM','동일 고시 p4~5에 S계열과 A/B/C계열 블록이 함께 존재한다. S블록을 A/B/C블록으로 임의 치환하지 않는다.',caution='C-2/B-2는고시명칭과LH공개기하명칭(공동주택 C2/B2)직접대응; S5등과변환표를만들지않음')
old={x['claim_id'] for x in pack['facts']};pack['facts'] += [x for x in new if x['claim_id'] not in old];fp.write_text(json.dumps(pack,ensure_ascii=False,indent=2),encoding='utf-8')
report='''# 중앙권 구체 후보 추가검증

2026-10-08 최신5차고시 p5 블록별 공급표를 이미지로 직접 확인했다. S계열과 A/B/C계열은 동일 고시 안에 함께 존재한다. S↔A 변환이 필요한 자료가 아니다.

|블록|주택규모|유형·호수|후보판단|
|---|---|---|---|
|C-2|전용85㎡초과|민간분양786호|큰평형 민간분양 관찰후보 우선|
|B-2|전용60~85㎡|민간분양281호|중형 민간분양 대안후보|
|B-1|전용60~85㎡|공공분양520+통합임대173=693호|공공분양분 세부상품 추가확인후 비교|
|A-10|전용60㎡이하|통합임대707호|일반분양 대장후보 제외|
|A-12|전용60㎡이하|통합임대788호|일반분양 대장후보 제외|
|A-11 / A-13|전용60㎡이하|공공분양511 / 622호|큰평형 후보 아님|

대본 권장: “구체적인 블록으로 좁히면, 큰평형 민간분양을 보는 첫 관찰대상은 C2입니다. 최신 지구계획에서 전용85㎡초과786호가 민간분양으로 잡혀 있습니다. 중형면적을 원한다면 B2의 전용60~85㎡281호를 함께 보겠습니다. 이 순서는 현재가격 순위가 아니라 상품조건으로 좁힌 관찰순서입니다. 분양가격과 브랜드, 실제 평면, 역 출입구 연결이 나온 뒤 다시 비교해야 합니다.”

공식표의 평균공급면적110/140㎡는 건설호수 산정용이고 전용면적·실제타입이 아니다. 민간분양 계획이 현재 분양중이나 처분자유를 보장하지 않는다. 현재 신규 매수가능 블록이라고 쓰지 않는다. 향후 모집공고·전매·거주조건 확인 필요. B1 공공분양은 일반형/이익공유형 여부 이 고시로 미확인.

visual 직접회신: LH기하 C2는중서부, B1은중부, B2는B1동측중부. C2 주변은 근생/주복8·초5/고2·수변공원·하천·도시지원, B2는근생·교육·공공공지·도시지원의 대표점 근접관계. 이는 접합·도보·학교배정 증거가 아니므로 분단위·횡단없는동선·배정학교 단정금지. 102~104 정거장 지리좌표 검증없어 블록별 역세권 확정매칭 금지.

증거: latest_plan_supply_p5.png, latest_plan_20261008.pdf p5, p7주1. LH 공개기하와의 실제명칭 대응은 visual/regional.json의 공동주택(B1)/(B2)/(C2) 및 visual담당 회신.
'''
(P/'candidate_addendum.md').write_text(report,encoding='utf-8')
hpath=P/'handoff.json';h=json.loads(hpath.read_text(encoding='utf-8'));h['outputs'].extend([str(P/'candidate_addendum.md'),str(P/'latest_plan_supply_p5.png')]);h['verification'].append('추가5개claims/p5공급표 시각확인 및 visual실제블록명대응회신');h['unresolved'].append('B1공공분양 일반형/이익공유형 및 C2/B2 실제분양가·전매거주조건 미확인');hpath.write_text(json.dumps(h,ensure_ascii=False,indent=2),encoding='utf-8')
assert len({x['claim_id'] for x in pack['facts']})==len(pack['facts'])
print('facts',len(pack['facts']),'addendum bytes',(P/'candidate_addendum.md').stat().st_size)
