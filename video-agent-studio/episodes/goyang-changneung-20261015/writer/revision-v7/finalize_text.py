from pathlib import Path
import re,json
ep=Path(__file__).resolve().parents[2]
p=ep/'outputs/script-review-v7/script_v7.md'
s=p.read_text(encoding='utf-8')
s=s.replace('단지 단위 회고 수치예요','LH가 소개한 당시 경쟁률이에요')
s=s.replace('지금 단계의 대장 가설과 가격 여력','지금 단계의 대장 후보와 가격 여력')
s=s.replace('오늘 대장 가설의 중심은','오늘 대장 후보를 고르는 기준은')
s=s.replace('그 수요가 실제 거래로 이어지는지가 유동성을 판단할 다음 단계이고요.','이후에 실제 거래가 잘 이뤄지는지도 봐야겠죠.')
s=s.replace('향후 거래 유동성','실제 거래가 잘 이뤄지는지')
s=s.replace('기존 수요 접점과 향후 거래 유동성','기존 수요와 만나는 위치와 실제 거래가 잘 이뤄지는지')
s=s.replace('기존 수요 접점과 향후유동성','기존 수요와 만나는 위치와 실제 거래가 잘 이뤄지는지')
s=s.replace('S4는 기존 수요 접점과 실제 거래가 잘 이뤄지는지,','S4는 기존 수요와 만나는 위치와 실제 거래가 잘 이뤄지는지,')
s=s.replace('그래서 S4는 가격수준을 이끌 후보라는 가설이고,','그래서 S4는 가격수준을 이끌 후보로 먼저 보는 것이고,')
s=s.replace('그 수요가 창릉의 어느 블록으로 이동할지는 아직 가설입니다.','그 수요가 창릉의 어느 블록으로 이동할지는 앞으로 지켜볼 부분입니다.')
s=s.replace('이 가설을 바꾸면 됩니다.','후보 평가를 바꿔 가면 됩니다.')
s=s.replace('기존 창릉호반써밋 좌표는 원자료 확인 후 사용, 미확인 상태에서 임의 핀 금지.','기존 창릉호반써밋은 VWorld 지번주소 대표점(경도126.88969554509904, 위도37.646405154969955)을 사용. 근거 visual/semantic-v5/verified_missing_locations.json. 단지 중심·경계·출입구가 아니라 동산동365의 정제 주소 위치이며 임의 단지면 생성 금지.')
s=s.replace('호반 좌표는 원자료 확인 후 사용, 미확인 상태에서 임의 핀 금지.','호반은 visual/semantic-v5/verified_missing_locations.json의 VWorld 주소 대표점(경도126.88969554509904, 위도37.646405154969955). 단지 중심·경계·출입구가 아님. 임의 단지면 생성 금지.')
order=['M000','M001','M002','M003','M004','M007','M006','M005','M009']
for n,sid in enumerate(order,1):
    s=re.sub(r'(?m)^## '+sid+r' · (?:\d{2} · )?',f'## {sid} · {n:02} · ',s)
header='''## 공통 화면 지침 · 모든 장면에 적용

화면 챕터 번호는 위에서 아래 설명 순서대로 01~09를 사용한다. 장면ID M000/M001/M002/M003/M004/M007/M006/M005/M009는 기존 자산 연결용으로 보존하며 화면 번호로 쓰지 않는다. 우상단에는 현재 챕터 번호와 짧은 주제 라벨을 같은 위치에 유지한다. 브랜드 인트로·아웃트로에는 본문 라벨과 자막 박스를 남기지 않는다.

출처는 해당 가격·지도·도표의 아래에 작은 자막으로 붙이고 본문 의미 단위 자막과 겹치지 않게 한다. 본청약 가격은 아래 원문 가격표·확장비표에서 해당 타입·층·금액을 먼저 짚은 뒤 요약 그래프로 전환한다. 원문 표를 분위기 배경처럼 흐리거나 장식으로 사용하지 않는다. 거래 표본은 ‘거래 11건’처럼 단위까지 쓰고 n= 표기는 쓰지 않는다. 통근 수치는 ‘66분’처럼 분 단위를 숫자와 붙여 표시한다. 지도는 발화 대상의 우상단 라벨 또는 해당 위치 라벨을 먼저 보여 주고 실제 위치를 강조한다.

모든 화면은 설명 목적에 맞는 검증 자료를 사용한다. 지도·가격 비교·거래 조건의 원문과 요약을 연결하고, 계획/현재/목표 표시를 유지한다. 글꼴·색·배치·하단 자막은 기존 승인 채널 문법을 따른다. 화면별 아래 지시는 이 공통 지침에 추가한다.

'''
if '## 공통 화면 지침' not in s:
    s=s.replace('## M000',header+'## M000',1)
p.write_text(s,encoding='utf-8')
issue=ep/'writer/revision-v7/issue_V7-HOBAN-COORD.json'
j=json.loads(issue.read_text(encoding='utf-8'))
j['status']='resolved_existing_official_address_locator'
j['resolution']={'source':'visual/semantic-v5/verified_missing_locations.json','lon':126.88969554509904,'lat':37.646405154969955,'basis':'VWorld 지번주소 대표점; 단지중심/경계/출입구 아님'}
issue.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
