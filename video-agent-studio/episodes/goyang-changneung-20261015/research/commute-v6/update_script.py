from pathlib import Path
import re, json, hashlib, sys
EP=Path(__file__).resolve().parents[2]
ROOT=EP.parents[2]
sys.path.insert(0,str(ROOT))
from notify import video_decisions as gates
old_dir=EP/'outputs/script-review-v5'
out=EP/'outputs/script-review-v6'
out.mkdir(exist_ok=True)
draft=(old_dir/'script_v5.md').read_text(encoding='utf-8')
old='''외부 업무지는 도심, 상암 DMC, 여의도, 마곡, 강남을 지도에 놓겠습니다. 출근지 통계 순위가 아니라 이동 방향이 다른 비교 대상입니다.
원흥역에서 열차를 탄 뒤의 시간 사례는 경복궁 약 24분, 종로3가 약 28분, 교대 약 49분입니다. 2022년 8월 시행 공개 시각표의 아침 열차 사례입니다. 여기에 집에서 원흥역까지, 대기와 회사까지의 마지막 이동이 더해집니다.
상암·여의도·마곡은 새절과 DMC, 공덕·공항철도 축의 연결을 보겠습니다. 역 이름만 가까운지보다 첫 구간과 마지막 환승을 이어 놓아야 내 출근길이 됩니다.'''
new='''그렇다면 지금 있는 교통으로 서울의 주요 업무지까지 얼마나 걸릴까요? S1·S4·S5의 대표 위치에서 광화문역, 상암 MBC, 여의도역, 마곡 LG사이언스파크, 강남역까지 길찾기를 비교했습니다. 평일 오전 8시에 이동을 시작하는 조건으로, 걷고 기다리고 갈아타는 시간을 함께 봤습니다.
세 위치의 결과를 묶으면 광화문역은 약 65분에서 70분, 상암 MBC는 약 45분에서 65분입니다. 여의도역은 약 60분에서 80분, 마곡 LG사이언스파크는 약 70분에서 80분, 강남역은 약 85분에서 95분입니다. 같은 창릉이어도 어느 블록에서 어디로 가는지에 따라 차이가 납니다.
예를 들어 상암 MBC까지는 S1 대표점에서 약 46분, S4는 약 62분, S5는 약 56분으로 나왔습니다. 기존 생활시설과 접점이 있는 S4가 출근도 언제나 가장 빠른 것은 아닙니다. 상암을 오가는 가구와 강남을 오가는 가구의 판단이 달라져야 하는 이유입니다.
이 숫자는 현재 길찾기의 예상값입니다. 아직 확정 출입구가 아닌 블록 대표 좌표를 썼고, 입주 후 새 보행로와 버스 배치는 반영하지 않았습니다. 역으로 표시한 목적지는 역 도착까지이므로 사무실까지는 마지막 이동을 더해야 합니다. 새 철도가 열리기 전의 출근 부담을 비교하는 기준으로 보겠습니다.'''
assert old in draft
draft=draft.replace(old,new)
old_direction='일자리 장 전환 명확히. 실제 5업무지 위치와 원흥발 역간 사례 분리. 2022년 시각표의 최신성 한계 표시, 현재 총통근시간처럼 사용 금지. 출발지→버스/보행→운영역→환승→회사 순서의 도식은 단계만 강조. 추정 집-역 분값 생성 없음.'
new_direction='''현재 교통 예상시간 지도. 창릉 경계와 S1/S4/S5 대표점→광화문역·상암 MBC·여의도역·LG사이언스파크·강남역을 실제 위치에 표시. 목적지 하나씩 강조하며 그 옆에 시간 요약을 붙이고 단지별 3열 표(분): 광화문66/68/67, 상암46/62/56, 여의도63/78/72, 마곡72/80/68, 강남87/94/94. 표의 순서는 S1/S4/S5. 출처 'Google Maps 대중교통 예상 · 2026.10.19(월)08:00 기준 / 10.18 조회 · 블록 대표 좌표→표기 목적지 · 현재 교통'. 08:00부터 가장 이른 표시 도착까지 계산해 이후 출발 경로의 대기도 포함. 내레이션 범위는 블록 간 결과를 5분 반올림한 범위이며 일별 변동폭이 아님. 현재 공사 지역 대표 좌표가 확정 출입구인 것처럼 그리지 않는다. 노선은 research/commute-v6/browser_receipts.json의 해당 경로에서만 선택. 기존 2022년 열차 구간 시간표 판은 이 장에서 교체하고 중복 삽입하지 않는다. 지도 카메라는 안정적으로 유지하고 목적지 강조만 순차 변경. 지구 locator·반복 줌 금지·채널 톤·기존 영상 및 레퍼런스 준수.'''
assert old_direction in draft
draft=draft.replace(old_direction,new_direction)
draft=draft.replace('# 창릉 대본 v5 · Codex × Claude 구성 합의안','# 창릉 대본 v6 · 현재 교통 통근 예상 보강')
draft=draft.replace('상태: 사용자 검토 대기·미확정.','상태: 사용자 검토 대기·미확정. v5의 Claude 구성 협의에 기반하되 이번 통근시간 보강은 Codex가 새로 조사·작성했으며 Claude 재검토를 받았다는 뜻은 아니다. ',1)
draft=draft.replace('사실은 v4와 script-v4-addendum의 확인 범위만 사용하며','사실은 v4·script-v4-addendum과 새 commute-v6의 확인 범위를 사용하며',1)
draft=draft.replace('매일 정시에 출근한다면 먼저 기존 역까지의 첫 구간을 비교하고,','매일 정시에 출근한다면 앞서 본 목적지별 현재 교통 예상시간과 기존 역까지의 첫 구간을 비교하고,')
(out/'script_v6.md').write_text(draft,encoding='utf-8')
chunks=re.findall(r'## (M\d+[^\n]*)\n\n### 낭독\n\n([\s\S]*?)(?=\n### 화면 지시)',draft)
assert len(chunks)==10
narration='\n\n'.join(t.strip() for _,t in chunks)
(out/'narration_v6.txt').write_text(narration,encoding='utf-8')
(out/'changes_v6.md').write_text('# v6 변경\n\nM002의 2022년 원흥역 열차 구간 사례를 현재 3블록×5목적지 길찾기 예상으로 교체. 도보·대기·환승을 포함하며 오전8시 기준으로 통일. M008에서 이 표를 회수. 다른 장의 낭독은 보존. 기존 v5·영상·음성은 보존. 신규 유료 생성·렌더·업로드 없음. Claude의 기존 구성 협의와 새 통근 조사 범위를 구분.\n',encoding='utf-8')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
dp=out/'review_decision.json'
decision=json.loads(dp.read_text(encoding='utf-8')) if dp.exists() else gates.create(EP.name,'script','창릉 대본 v6: 현재 교통 3개 블록×5개 업무지 통근 예상 보강. 대본·화면 지시만 검토. 유료 생성·업로드 제외.')
decision.update(script_revision='script-v6',scope='script_and_scene_direction_only',artifact_hashes={str(p.relative_to(EP)):sha(p) for p in [out/'script_v6.md',out/'narration_v6.txt',out/'changes_v6.md',EP/'research/commute-v6/report.md',EP/'research/commute-v6/route_observations.json']},paid_generation_authorized=False,upload_authorized=False)
gates.write(dp,decision);gates.write(ROOT/'output/video_decisions/decisions'/f"{decision['id']}.json",decision)
priorp=ROOT/'output/video_decisions/decisions/055ac0e79b6f.json'
prior=json.loads(priorp.read_text(encoding='utf-8'))
if prior['status']=='pending':
 prior.update(status='superseded',superseded_by=decision['id'],reason='사용자 현재 교통 통근 예상 보강 요청으로 v6 작성')
 gates.write(priorp,prior)
statep=EP/'state.json';state=json.loads(statep.read_text(encoding='utf-8'))
state.update(stage='script_review_pending',draft_script_revision='script-v6',draft_script_status='review_pending',draft_script_path='outputs/script-review-v6/script_v6.md',draft_script_sha256=sha(out/'script_v6.md'),pending_gate='script',pending_decision_ids={'script':decision['id']},paid_generation_authorized=False,voice_generation_hold=True,active_tasks=[])
gates.write(statep,state)
logp=EP/'decisions.json';log=json.loads(logp.read_text(encoding='utf-8'))
for d in log['decisions']:
 if d.get('id')==prior['id']:d.update(prior)
if not any(d.get('id')==decision['id'] for d in log['decisions']):log['decisions'].append(decision)
gates.write(logp,log)
check={'chapters':len(chunks),'narration_chars':len(narration),'route_queries':15,'departure':'2026-10-19 08:00 Asia/Seoul','script_sha256':sha(out/'script_v6.md'),'decision_id':decision['id'],'paid_generation':False,'render_started':False}
gates.write(out/'validation.json',check)
print(json.dumps(check,ensure_ascii=False))
