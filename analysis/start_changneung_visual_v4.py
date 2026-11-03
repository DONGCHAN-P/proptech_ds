import json, sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from notify.video_decisions import write,now
ep=root/'video-agent-studio/episodes/goyang-changneung-20261015'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
note='자막 읽기표기를 S1/S2/S5·DMC·300곳·2028년 등 시각 표기로 전수 정규화. 창릉지구 영역과 창릉역 예정 위치 구분. S5 등 단지 설명은 실제 토지이용계획 상세와 전체지도 위치로 교체. 기존 승인 음성·길이 보존, 새 유료 호출 없음.'
dpath=root/'output/video_decisions/decisions/dadaae0b1c36.json'
d=read(dpath)
if d['status']=='pending':
 d.update(status='revision_requested',response={'source':'direct_user_chat','at':now().isoformat(),'note':note});write(dpath,d)
dec=read(ep/'decisions.json')
for item in dec['decisions']:
 if item['id']==d['id']:item.update(d)
write(ep/'decisions.json',dec)
s=read(ep/'state.json');s.update(stage='visual_revision_v4',pending_gate=None,pending_decision_ids={},active_tasks=['subtitle-display-v4','map-location-v4','render-v4'],revision_request=note,revision_baseline='outputs/production-v3/changneung_full_v3r2.mp4',publication_authorized=False)
write(ep/'state.json',s)
out=ep/'outputs/production-v4';out.mkdir(parents=True,exist_ok=True)
write(out/'revision_request.json',{'at':now().isoformat(),'baseline':s['revision_baseline'],'user_request':note,'spoken_script_revision':'script-v3','audio_revision':'audio-v3','new_paid_generation':False,'publication_authorized':False})
guide=root/'video-agent-studio/guides/지역_상세지도와_의미단위_자막.md'
text=guide.read_text(encoding='utf-8')
addition='''\n## 낭독문과 화면 자막의 표기 분리 — 2026-10-16 추가\n\n음성 합성을 위한 읽기 표기를 화면에 그대로 노출하지 않는다. 자막은 `S1·S2·S5`, `DMC`, `GTX-A`, `LH`, `LX`, `300곳`, `2028년 1월`, `84㎡`, `3호선`, `7억 6,998만 원`처럼 읽기 쉬운 영문·숫자 표기를 사용한다. 숫자의 값·단위·공고 조건은 그대로 보존한다. 삼송 등 지명, 첫째 등 문장 구조를 이루는 서수, ‘첫 두 달’ 같은 자연스러운 표현은 무조건 숫자로 바꾸지 않는다. 타입명과 학교 코드도 공식 표기를 대조한다.\n\n원문 `spoken_text`와 화면 `display_text`를 따로 저장하고 문자 정렬은 원문 기준으로 유지한다. 모든 치환의 전후·큐·원문 범위·사유를 기록한다. 자막을 연결해 낭독문과 글자 그대로 같아야 한다는 검사는 이 명시적 변환표를 적용한 뒤 수행한다. 최종 SRT뿐 아니라 번인 자막에도 같은 변환을 적용한다.\n\n단지 설명은 실제 위치를 알아볼 수 있어야 한다. 이용 조건 때문에 특정 전체도를 확대하지 못하면 재가공 허용 원자료·공고 배치도·공개 공간 데이터로 대체 자료를 찾는다. 이름만 적힌 사각형과 동서남북 문장 패널을 상세지도 완성본으로 납품하지 않는다. 지구 경계와 역 예정 위치는 서로 다른 범례·형태로 표시하고, 미확정 역은 정밀 출입구처럼 표시하지 않는다.\n'''
if '## 낭독문과 화면 자막의 표기 분리' not in text:guide.write_text(text+addition,encoding='utf-8')
history=root/'video-agent-studio/guides/사용자_피드백_이력.md'
text=history.read_text(encoding='utf-8')
if '# 2026-10-16 · 창릉 자막 시각 표기와 실제 단지 지도' not in text:history.write_text(text+'\n# 2026-10-16 · 창릉 자막 시각 표기와 실제 단지 지도\n\n사용자 검토: 읽기용 에스원·삼백곳·디엠씨·한글 연도 대신 S1·300곳·DMC·숫자 연도로 전수 수정. 창릉역과 창릉지구가 구분되지 않으므로 영역과 역을 분리해 안내. 6:30 S5 단독 사각형은 위치를 이해할 수 없으므로 왕숙 상세 배치도처럼 실제 계획의 단지·학교·공원·도로 공간 맥락과 전체지도상 위치를 보여줄 것. 기존 가이드에 이미 있던 관계상자 대체 금지 규칙을 실제 완료 검수에 적용해야 한다. 음성은 그대로 보존하고 자막 표시문만 변환표로 분리한다. 이전 완료 검토는 수정 요청으로 종료하고 새 산출물은 새 완료 결정에 묶는다.\n',encoding='utf-8')
print('v4 revision request and permanent guide recorded')
