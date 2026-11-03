"""Research-backed script and shot plan. No media generation or approval inheritance."""
from pathlib import Path
import json,re,hashlib,uuid,copy
EP=Path(__file__).resolve().parents[1]
ROOT=EP.parents[2]
OUT=EP/'outputs/script-review-v4';OUT.mkdir(exist_ok=True)
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
sources=[
 {'id':'GY-AI-PARTICIPANTS','date':'2025-12-17','publisher':'하남시','url':'https://www.hanam.go.kr/sosik/selectBbsNttView.do?bbsNo=1164&key=10048&nttNo=495607','finding':'자족5 AI 클러스터 추진. KT클라우드·KT자산운용·포스텍·카네기멜론대·싱가포르국립대 참여 계획. AI 대학원·바이오 연구·슈퍼컴퓨터 인프라 계획. 기업별 입주일/채용 규모 미확인.','media_use':'본문 사실을 자체 도표로 재구성. 게시 사진은 공공누리4유형이므로 상업 영상용 직접 사용 자산에서 제외.'},
 {'id':'GY-AI-PERIOD','date':'2026-10-01','publisher':'하남시 청정하남','url':'https://www.hanam.go.kr/cleanh/cleanhBbsNttWebView.do?key=8364&nttNo=3495','finding':'자족5 AI 혁신클러스터 사업기간 2026~2030년 안내. 교산 밖 캠프콜번은 쇼핑·문화·업무·주거 복합개발 추진, 하산곡동209-9일원, 2027년 SPC설립 향후계획. 개별 점포 개점일 미확인.','media_use':'위치·기간 자체 지도/달력으로 제작. 홍보 조감도와 사진은 사용조건 확인 후 별도 판단.'},
 {'id':'GY-INDUSTRY7','date':'2026-07-16','publisher':'하남시의회 투자유치과 업무보고','url':'https://council.hanam.go.kr/minutes/svc/web/cms/mnts/SvcMntsViewer.php?mode=spkr1&schSn=3208&spkrCd=MBR10050','finding':'만남의광장 인근 자족5 AI클러스터, 자족7 도시첨단산업단지 지정 추진 및 용지별 타깃기업 유치 용역 예정. 유치완료/산단지정완료로 해석하지 않음.','media_use':'발표일과 단계만 자체 카드·지도에 표기.'}
]
dump(OUT/'research_additions.json',{'checked_at':'2026-10-20','sources':sources,'not_found':'검색·확인한 공식 자료 범위에서는 교산 내부 신규 상업시설의 개별 브랜드·입점계약·개점일을 확인하지 못함. 부재를 확정한 것이 아님.','excluded':'기존 하남스타트업캠퍼스의 AI클러스터 및 이글루코퍼레이션 본사 유치를 교산 자족5 입주로 전용하지 않음. 고용유발/생산유발 기대효과를 실제 채용·고용으로 사용하지 않음.'})
script=(EP/'outputs/script-review-v3/script_v3.md').read_text(encoding='utf8')
scenes=json.loads((EP/'writer/scenes_v3.json').read_text(encoding='utf8'))
changes={
'교산은 서울과 가깝다는 한 문장으로 끝낼 수 있는 지역이 아닙니다.':'저는 서울과의 거리, 집값, 실제로 누릴 생활 편의를 함께 보겠습니다.',
'이곳은 기업과 업무시설을 위한 계획 용지입니다. 앞으로 어떤 기업이 들어오고 얼마나 많은 일자리가 생기는지 살펴보겠습니다.':'구체적으로 볼 사업은 자족5 용지의 AI 혁신클러스터입니다. 하남시는 2025년 12월 발표에서 KT클라우드와 KT자산운용, 포스텍, 카네기멜론대학교, 싱가포르국립대학교가 참여하는 계획을 소개했습니다.\n구상에는 AI 교육·연구, 바이오 연구단지, 슈퍼컴퓨터 인프라가 들어 있습니다. 2026년 10월 시 안내에 적힌 사업기간은 2026년부터 2030년까지입니다.\n자족7 용지는 도시첨단산업단지 지정을 추진하고 있습니다. 저는 이 두 사업을 교산 안의 일자리를 늘릴 후보로 보겠습니다. 기업별 실제 입주와 채용 일정이 공개되면 주거 수요와 연결해 살펴보겠습니다.',
'기업이전 대책에 나오는 기존 기업 역시 새 대기업 일자리로 바꾸어 읽을 수는 없습니다.':'기존 기업의 이전 대책은 하남에서 영업하던 기업의 활동과 일자리를 이어가는 내용으로 따로 보겠습니다.',
'계획도에 상업용지나 여러 기능을 모아 놓는 중심복합 용지가 있다는 것은, 이런 시설이 들어설 땅을 마련했다는 뜻입니다.':'교산 내부에서는 상업용지와 중심복합 용지에 어떤 시설이 들어오는지 보겠습니다. 현재 확인한 공식 자료로는 이 용지의 개별 점포 이름과 개점일을 더 확인해야 합니다.',
'실제로 어떤 점포가 언제 문을 열지는 별도 과정입니다.':'지구 밖의 새 사업으로는 하산곡동 옛 캠프콜번 부지의 복합개발도 있습니다. 하남시는 쇼핑·문화·업무·주거 기능을 넣는 방향을 제시하고, 2027년 사업을 추진할 특수목적법인 설립을 향후 계획으로 안내했습니다. 저는 이 사업을 교산 주변의 상업·업무 기반이 늘어날 후보로 보겠습니다.',
'반대로 기존 하남의 상권과 스타필드 하남처럼 이미 운영하는 시설은 새 도시 밖에 있는 현재의 편의입니다.':'현재 이용할 수 있는 시설로는 기존 하남 상권과 스타필드 하남을 지도에 함께 놓겠습니다. 새로 추진하는 시설과 현재 운영 중인 시설의 위치를 나누어 보겠습니다.',
'이런 시설이 있다고 교산 전체를 도보 상권으로 부를 수는 없습니다.':'각 후보 단지에서 실제 도로를 따라 상권까지 어떻게 이동하는지 보겠습니다.',
'5. 공급 · 한 날짜에 완성되는 도시는 아닙니다':'5. 공급 · 주택과 교통이 채워지는 순서',
'이 주택이 한 달에 모두 입주하거나 시장에 매물로 나오는 것은 아닙니다.':'저는 전체 주택 계획을 단지별 입주와 거래 가능 시점으로 나누어 보겠습니다.',
'가격이 높은 후보와 가장 높은 수익률의 후보는 같은 말이 아닙니다.':'저는 대장 후보의 입지 장점과 실제 매입가격을 함께 비교해 투자 매력을 판단하겠습니다.'
}
for a,b in changes.items():
 assert a in script,a
 script=script.replace(a,b)
 for s in scenes:
  s['title']=s['title'].replace(a,b)
  for u in s['units']:u['text']=u['text'].replace(a,b)

# Each tuple is a narrated anchor, useful picture, meaningful action, evidence and fallback.
plans={
'M000':[
 ('첫 질문과 전편 연결','교산 전체 토지계획도 + 기존 광교·동탄/왕숙/창릉 실제 썸네일·영상','전편 화면을 짧게 묶은 뒤 교산 경계가 있는 고정 지도로 전환. 제목만 읽는 화면 금지.','기존 승인 브랜드·전편 자산','전편 스틸과 전체 지도'),
 ('오늘 비교할 조건','동일 지도에 기존 하남/새 중심/업무용지를 분리한 3개 영역','발화에 맞는 영역 윤곽과 짧은 질문만 순서대로 표시. 카메라 줌 없음.','현재 로컬 v2 지도','전체 지도를 유지하고 대상만 색으로 강조')],
'M001':[
 ('전체 토지이용과 36,669호','공식 계획 기반 전체 지도·색상 범례','주거→업무→공원 순서로 실제 면을 강조. 숫자는 해당 용도 위에 붙임.','기존 최신 고시·LH 도형','기존 v2 계획도'),
 ('북부·중앙·남부 구분','전체 계획도 위 설명용 세 영역','3개 이름을 지도 바깥에 배치하고 대상 면으로 연결. 행정경계와 다른 설명용 구역임을 표기.','기존 토지계획도','큰 지도에 번호만 추가')],
'M002':[
 ('잠실·강남·판교 방향','교산 경계와 3개 외부 업무지가 모두 보이는 광역 지도','말하는 목적지까지 방향선을 순차 표시. 계산하지 않은 시간은 쓰지 않음.','기존 광역 지도','위치 지도'),
 ('자족5 AI 혁신클러스터','전체 위치지도 + 자족5 확인된 실제 필지 + 자체 제작 발표 요약','자족5 면을 강조하고 AI교육·연구/바이오/컴퓨팅 3개 기능 아이콘 연결. 참여기관은 발표상 참여 계획으로 묶음.','GY-AI-PARTICIPANTS / GY-AI-PERIOD','필지 코드·경계를 매칭하지 못하면 전체지도에 만남의광장 인근 개략 영역만 표시. 정밀 위치처럼 점찍지 않음.'),
 ('2026~2030 및 자족7','사업기간 가로 달력 + 지정 추진 단계 표시','사업기간 띠가 그려진 뒤 자족7 지정 추진 카드로 전환. 개점·고용 확정 날짜로 전용하지 않음.','GY-AI-PERIOD / GY-INDUSTRY7','발표 사실을 자체 도표로 재구성. 원 보도사진 직접 사용 제외')],
'M003':[
 ('현재 5호선 연결','운영역·도로·교산 경계 지도','기존 역과 첫 이동 구간을 번갈아 강조. 지도 자체는 고정.','v2 운영철도 지도','같은 지도에 범례 유지'),
 ('송파하남선 계획','공식 노선 관계도 + 기존선 실선/계획선 점선','계획선 진행 표시를 천천히 한 번만 재생. 미확정 출입구 임의 배치 금지.','기존 공식 노선 자료','공식 관계도 그대로'),
 ('입주 2029.06과 철도 목표 2032','지도 아래 서로 다른 일정 2개 줄','A2 위치 강조와 두 날짜 사이 대기 구간 표시. 반복 줌/순간 전체지도 삽입 금지.','A2 공고 / 철도 목표 출처','지도와 가로 달력')],
'M004':[
 ('51A·59A 본청약 가격','실제 정정 공고 PDF의 해당 가격행 확대 + 주택형 면적','해당 행을 따라 강조하고 기본가→확장비→합계 막대를 누적. 단순 숫자 페이지 금지.','v2 원문 대조표:51A p6/59A p7/발코니 p8','자체 비용 막대와 공고 문서명·쪽수'),
 ('새집 59㎡와 기존 84㎡ 선택','면적 비례 평면 도형 + 실제 단지 위치','면적과 총부담 항목을 나란히 표시. 재현한 면적 도형을 실제 평면도로 부르지 않음.','공고면적/비교 실거래','비례 면적 그래픽')],
'M005':[
 ('A2 공원·학교·생활 동선','기존 v2 상세 토지계획도 + 좌측 전체 위치지도','주거/공원/학교를 말할 때 그 면만 강조. 학교 코드 대신 예정 부지 표기.','A2 공고 / LH 계획','기존 상세 계획도'),
 ('교산 내부 새 상권','상업·중심복합 면을 실제 경계로 표시한 계획도','주거→상업 면에 방향 연결. 상호·개점일은 발표 확인 후에만 기입.','기존 최신 계획도','현재 승인 지도'),
 ('캠프콜번과 스타필드 하남','교산 밖 두 시설의 위치와 교산 경계를 포함한 지도 + 사용권 있는 현장 사진','현재 운영/개발 추진 상태를 서로 다른 배지로 표시. 캠프콜번2027 SPC일정과 개점일을 구분.','GY-AI-PERIOD / 기존 운영시설 확인 자료','사진이 없으면 위치와 시설 기능을 자체 아이콘으로 표현'),
 ('미래 생활 이미지가 필요한 경우','거리 상업·공원 이용의 짧은 개념 이미지/영상','AI 생성·이해를 위한 예시로 표시. 실제 건축물·브랜드·설계를 재현한 것처럼 쓰지 않음.','새 생성은 현재 수행하지 않음','검증된 지도+아이콘으로 완결 가능')],
'M006':[
 ('36,669호와 단지별 입주','공급규모 도형 + 단지 위치 + 가로 일정','전체 계획 규모를 먼저 보여주고 확인된 A2 입주만 달력에 연결. 미공개 연도별 물량은 그리지 않음.','최신 고시 / A2 공고','확인된 날짜만 표시'),
 ('전매제한·거주의무','공고 조건에 따른 시작 기준이 분리된 일정 그래픽','각 시작 사건에서 해당 기간을 펼침. 예정입주+3년을 매매가능일로 계산하지 않음.','A2 공고','원문 조건+별도 일정줄')],
'M007':[
 ('주변 실거래 비교','하남·미사·감일 실제 단지 지도 + 가격 내림차순 막대','낭독하는 단지의 지도 마커와 막대를 동시 강조. 거래건수·면적·집계기간 유지.','기존 실거래 집계','v2 비교 지도 보존'),
 ('교산 59㎡와 기존84㎡','A2 및 비교 단지 위치 + 면적·입주편의 비교','가격·면적·현재 이용가능 시설을 따로 시각화. 단순 차액을 수익으로 표현하지 않음.','기존 공고·실거래','지도+비례 면적 그래픽')],
'M008':[
 ('C2·B2 대장 후보','사용자가 선호한 로컬 v2 토지이용계획도 구간 유지','기존 후보 필지 경계·좌측 위치지도·주변 용도 배치를 유지. 발화 대상의 면·라벨만 부드럽게 강조. 카메라 줌/새 추상 비교화면으로 교체 금지.','outputs/production-v2 / editor/review-v2 정확한 C2·B2 매칭','현재 토지계획도 화면 그대로'),
 ('북쪽 A2와 남쪽 업무용지','현재 후보 설명용 상세 계획도 유지','A2 및 남쪽 생활 조건을 기존 도형 위에서 설명. 자족5·7 상세 위치는 검증 후 보조 표시. 전체 후보구조 재설계하지 않음.','기존 검증 도형 / 신규 조사','현재 구간 보존')],
'M009':[
 ('오늘의 판단과 후속편','실제로 설명한 후보 지도·가격·달력의 3개 화면 요약','새 텍스트 목록 대신 기존 장면 핵심을 차례로 재호출. 과도한 빠른 몽타주 없음.','본편에서 사용한 자료','기존 요약 지도'),
 ('구독·좋아요·감사','기존 채널 CTA모션·브랜드 아웃트로','기존 v2 모션 유지. 마지막 발화 종료3초 후 아웃트로. 브랜드에는 흰 자막박스 없음.','기존 승인 브랜드','기존 CTA')]
}
story=['# 교산 v4 자료화면 설계\n\n상태: 대본·화면 기획 완료, 자산 신규 제작/음성/영상 반영 전. 시각표는 문장 기준이며 기존 영상 타임코드를 새 음성에 재사용하지 않는다.\n']
for s in scenes:
 sid=s['scene_id'];p=plans[sid]
 s['visual_plan']=[dict(zip(['narration_anchor','picture','action','evidence','fallback'],x)) for x in p]
 for beat in s['visual_plan']:
  beat['status']='기획 완료·신규 자산 제작/사용조건/위치 대조는 렌더 전 확인'
  beat['preserve_existing']=sid=='M008'
 if sid=='M008':s['preserve_visual_baseline']='editor/review-v2 + outputs/production-v2; user explicitly retained land-use segment'
 start=script.index('### 화면 지시',script.index('## '+sid))
 end=script.index('\n출처:',start)
 lines=['### 화면 지시','', '창릉 최종본의 색·서체·자막·브랜드를 계승합니다. 지도는 고정 구도, 대상 강조만 사용합니다. 출처는 자막 아래에 둡니다. 아래는 제작 지시이며 낭독하지 않습니다.','']
 for i,(anchor,picture,action,evidence,fallback) in enumerate(p,1):
  lines += [f'**{sid}-V{i:02d} | {anchor}**',f'- 자료화면: {picture}',f'- 화면 동작: {action}',f'- 근거/자산: {evidence}',f'- 확보 전 대안: {fallback}','']
 block='\n'.join(lines)
 script=script[:start]+block+script[end:]
 story += [f'## {sid} · {s["title"]}\n',block+'\n']
script=script.replace('대본 v3','대본 v4').replace('기준: 2026-10-19.','기준: 2026-10-20.').replace('narration/units_v3.json','narration/units_v4.json')
script=script.replace('창릉 최종 v8 포맷 계승. 합니다체. paid API 0.','창릉 최종 v8 포맷 계승. 합니다체. 조사·자료화면 기획 수정본. 음성·영상 미반영. paid API 0.\n\n신규 조사 출처: [조사 기록](research_additions.json) · [장면별 자료화면](visual_storyboard.md). 대장 후보의 기존 토지이용계획도 구간은 유지합니다.')
for sid,refs in [('M002','GY-AI-PARTICIPANTS · GY-AI-PERIOD · GY-INDUSTRY7'),('M005','GY-AI-PERIOD')]:
 a=script.index('\n출처:',script.index('## '+sid));b=script.find('\n\n',a)
 script=script[:b]+f' · 추가 조사: {refs} (2026.10.20 확인)'+script[b:]
units=[]
for s in scenes:
 for i,u in enumerate(s['units'],1):
  claims=list(u['claim_ids'])
  if '자족5' in u['text']:claims+=['GY-AI-PARTICIPANTS','GY-AI-PERIOD','GY-INDUSTRY7']
  if '캠프콜번' in u['text']:claims+=['GY-AI-PERIOD']
  u['claim_ids']=list(dict.fromkeys(claims))
  # Fresh IDs prevent these longer units from accidentally reusing old WAVs.
  unit=copy.deepcopy(u);unit.update(scene_id=s['scene_id'],title=s['title'],unit_id=f'{s["scene_id"]}_v4_{i:03d}',file=f'{s["scene_id"]}_v4_{i:03d}.wav',spoken_text=None,status='script_only_tts_preparation_required',visual_plan_scene=s['scene_id'])
  units.append(unit)
 s['script_revision']='v4';s['timing_status']='requires_new_audio_alignment'
(OUT/'script_v4.md').write_text(script,encoding='utf8')
(OUT/'visual_storyboard.md').write_text('\n'.join(story),encoding='utf8')
dump(EP/'writer/scenes_v4.json',scenes);dump(EP/'narration/units_v4.json',units)
for s in scenes:
 block=script.split('## '+s['scene_id']+' · ',1)[1].split('### 낭독',1)[1].split('### 화면 지시',1)[0].strip()
 assert block=='\n'.join(u['text'] for u in s['units']),s['scene_id']
assert len(plans)==10 and all(plans.values())
sha=hashlib.sha256((OUT/'script_v4.md').read_bytes()).hexdigest()
record={'revision':'script-v4-research-and-visual-plan','script':'outputs/script-review-v4/script_v4.md','script_sha256':sha,'status':'revised_script_for_review','decision_id':uuid.uuid4().hex[:12],'audio_reflected':False,'video_reflected':False,'paid_calls':0,'chapters_with_explicit_visual_plan':10,'visual_beats':sum(map(len,plans.values())),'preserved_candidate_visual':'M008 production-v2 land-use segment','five_existing_gates_unchanged':True}
statepath=EP/'state.json';state=json.loads(statepath.read_text(encoding='utf8'));state['script_language_revision']=record;dump(statepath,state);dump(OUT/'script_revision_record.json',record)
dump(OUT/'verification.json',{'script_scene_text_consistent':True,'units':len(units),'all_chapters_have_visual_plans':True,'candidate_landuse_preserved':True,'no_media_generated':True,'new_audio_ids_prevent_stale_reuse':True})
(OUT/'수정내역.md').write_text('''# 교산 대본 v4 수정내역

- v2의 쉬운 표현과 v3의 직접적인 판단 화법을 계승했습니다.
- 자족5 AI 혁신클러스터의 발표상 참여기관·기능·사업기간, 자족7 산업단지 지정 추진을 일자리에 추가했습니다.
- 캠프콜번 복합개발 추진을 교산 밖의 상업·업무 계획으로 추가했습니다. 교산 내부 개별 점포와 개점일은 현재 조사 범위에서 추가 확인이 필요합니다.
- 전 10개 장에 낭독 문장별 자료화면·동작·근거·자료 미확보 대안을 넣었습니다. 별도 visual_storyboard.md로도 확인할 수 있습니다.
- 사용자 추가 의견에 따라 M008 대장 후보의 기존 토지이용계획도 구성은 유지합니다.
- 원 보도자료 사진의 이용조건과 발표 단계는 조사 기록에 남겼습니다. 실제 입주·채용·개점으로 확대하지 않습니다.
- 새 대본은 음성·영상에 아직 반영하지 않았습니다. 새 유료 호출·업로드는 없습니다. 기존 영상과 승인 기록을 보존했습니다.
''',encoding='utf8')
shelfpath=ROOT/'config/video_shelf.json';shelf=json.loads(shelfpath.read_text(encoding='utf8'))
for e in shelf['entries']:
 if e['name']=='교산':
  for name,file in [('대본_수정안.md','script_v4.md'),('대본_수정내역.md','수정내역.md'),('자료화면_설계.md','visual_storyboard.md')]:e['files'][name]=(OUT/file).relative_to(ROOT).as_posix()
dump(shelfpath,shelf)
preflight=EP/'director/episode_preflight.json'
pre=json.loads(preflight.read_text(encoding='utf8'))
pre['script_v4_visual_preflight']={'script':'outputs/script-review-v4/script_v4.md','guide':'../../guides/자료화면_설계_원칙.md','visual_plan_coverage':'10/10 chapters;24 beats','keep_visual_scene_ids':['M008'],'new_research_claims':[s['id'] for s in sources],'assets_status':'planning_only_new_assets_not_generated','timing':'new_audio_alignment_required','paid_calls':0}
dump(preflight,pre)
print(json.dumps(record,ensure_ascii=False))
