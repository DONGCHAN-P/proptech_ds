import json
from pathlib import Path
EP=Path(__file__).resolve().parents[1]
def write(name,s):
 p=EP/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8')
def save(name,x):write(name,json.dumps(x,ensure_ascii=False,indent=2)+'\n')
data=json.loads((EP/'research/data.json').read_text(encoding='utf-8'));timing=json.loads((EP/'editor/timing.json').read_text(encoding='utf-8'))
save('scenes.json',[{'scene_id':'RACE01','start':0,'end':timing['duration'],'message':'全수집대상에서 다시 선정되는 단지별 중위가격TOP20의 진입·추월·이탈','narration_text':None,'script_revision':'top20-screen-v1','audio_revision':'original-race-pulse-v1','timing_basis':'frame-authored 30fps; 79 observed rank snapshots','claim_ids':['all 1580 price/n/rank claims in research/facts.json'],'asset_ids':['race_data.json','original_race_pulse.wav'],'status':'rendering'}])
save('decisions.json',[{'id':'TOP20-D01','choice':'replace_fixed_region_rows_with_moving_complex_rank_rows','basis':'사용자 직접 수정. 기존 고정행 D02를 이 편에서 대체. 과거MP4보존.'},{'id':'TOP20-D02','choice':'all_collected_eligible_complexes_each_period','basis':'매시점12,470개중적격후보전체재선정.최종TOP20생존자고정금지.'},{'id':'TOP20-D03','choice':'84_to_under85m2_trailing_four_quarters_min5','basis':'평형기준유지.단지희소거래완화.화면5건조건과각행n표시.10건기준민감도는자료에보관.'},{'id':'TOP20-D04','choice':'56.8s_with_8s_final_hold','basis':'20행요구유지하고이름31px·가격32px.대표1위교체홀드추가.마지막정지8초.'},{'id':'TOP20-D05','choice':'brief_collision_label_suppression','basis':'단지색/DOM/실제y이동유지.교차중글자경계가맞붙을때해당이름·숫자만가림.안정상태20행전부표시.'},{'id':'TOP20-D06','choice':'qualified_dates_and_missing_data_handling','basis':'분기말최근1년실거래중위값.동적구간두관측분기범위.결측단지과거0원·전방채움없음.진입·이탈연출만연결.'},{'id':'TOP20-D07','choice':'adopt_Claude_scope_n_hook_pacing_feedback','basis':'7개지역상시표기,각행거래건수,13회1위교체훅,57초로연장.15행축소제안은사용자TOP20요구우선으로미채택.소수1자리제안은실제중위금액2자리표시를유지해화면상동률확대를줄임.표시정밀도는추정신뢰도와구분.'}])
write('writer/화면구성.md',f'''# 단지 중위가격 TOP20 레이스

최종 구성: {timing['duration']:.1f}초,1080×1920,30fps,내레이션 없이 원본BGM과 화면 데이터.

훅: **1위가13번바뀌었다**
비교: 전용84㎡대 단지TOP20. 최근1년(4개분기)개별거래금액의중위값,5건이상거래. 7개수집지역의단지전체에서매시점재선정.

| 구간 | 화면/연출 |
|---|---|
| 0–1.8초 | 2006Q4 TOP20 완성표부터 시작. 계기 질문 ‘2006→2026,어떤단지가올라올까?’ |
| 1.8–{timing['race_end']:.1f}초 | 79시점 순위 전환. 단지의 같은 이름·색을 유지하며 새 순위 위치로 y이동. 신규 진입은 아래쪽 경계에서 위로, 퇴장은 아래로 이동. 값이 없는 기간을 0원으로 만들지 않음 |
| 대표 교체 | 2010Q4 래미안퍼스티지 /2016Q3 아크로리버파크 /2023Q3 래미안원베일리 /2025Q4 현대14차. 실제 이벤트에 추가 읽기 홀드 |
| {timing['race_end']:.1f}–{timing['duration']:.1f}초 | 2026Q2 TOP20 정지. 실제 집계창2025Q3~2026Q2. 거래건수·억원 단위·모든20개단지 유지 |
| 마지막4초 | 전체TOP20을 유지하면서 ‘다음비교도궁금하다면구독·좋아요’. 음악은마지막1초페이드 |

행 순서=중위금액 내림차순, 동률이면 직전TOP20순서→ID. 순위 진입은 준공·입주 사실이 아니라 해당 표본/거래건수 조건에서의 랭킹 진입이다.

단지명은 원자료 신고명 기준이고, 열거된 동번호 생략 등 표시명은 research/name_mapping.csv에 원명과 매핑했다. n열은 해당 최근1년 거래건수다. 동적 보간 구간에는 중간가격에 임의의 정수n을 붙이지 않고 대시를 표시한다.

20행 요청에 맞춰 단지명31px,가격32px,순위27px,보조위치/건수24px. 화면 전체를 축소하지 않고 고유좌표로설계했다. 마지막 표는8초정지한다.
''')
write('outputs/업로드정보.md','''# 단지 TOP20 쇼츠 업로드 정보

제목: 1위가13번바뀌었다｜84㎡대아파트중위가TOP20,2006→2026 #Shorts

설명:
2006년부터2026년까지,어떤아파트단지가가격상위권에들어왔을까요?
서울·경기·인천·부산·대구·대전·세종에서수집한단지12,470개와전용84㎡대실거래2,153,830건을바탕으로TOP20의순위변화를그렸습니다.

단지의이름·색을유지한채순위가바뀌면막대의위치가바뀝니다. 처음으로순위에들어온단지와재진입단지를함께볼수있습니다. 이번조건에서1위는13번교체됐습니다.

집계기준:
- 거래기간2006-01-01~2026-06-30,순위시점2006Q4~2026Q2 총79개
- 각분기말최근4개분기의전용84㎡이상85㎡미만아파트매매금액중위값,5건이상거래단지
- 매시점수집대상전체에서TOP20재선정,동률은직전순위→단지ID기준
- 화면건수는해당최근1년유효거래수,가격은억원소수둘째자리반올림
- 분기사이의움직임은두실제관측점을연결한시각전환. 진입/이탈단지의없는과거가격을만들지않음
- 순위진입/퇴장은거래가격뿐아니라표본5건충족·창밖거래이탈·거래구성변화에따라발생할수있음
- 단지별층·동·세부면적·거래방식의구성은시점마다달라짐
- 5건/10건조건에따라끝점1위가달라지는민감도는함께제공한집계자료에기록
- 수집지역과파일별수집일이정해진로컬자료. 수도권원본행 multiplicity 보존, 확장자료는기존취소우선/거래키중복처리를계승. 이번제작에서후속신고정정을새로조회하지않음
- 단지명은원자료신고명기준,원명·표시명은별도CSV로제공
- 자료:국토교통부실거래가 수집분. 음악/화면은직접제작

다음에는어느지역·평형을비교해볼까요? 댓글로남겨주세요.
데이터로보는부동산을구독하고다음비교도함께확인해주세요.

#부동산 #아파트 #실거래가 #아파트순위 #Shorts

현재상태:로컬납품. 신규유튜브업로드는이번요청범위에포함되지않음.
''')
state=json.loads((EP/'state.json').read_text(encoding='utf-8'));state.update(phase='rendering_then_independent_qa',duration_s=timing['duration'],source_data='research/data.json',source_validation='research/validation.json',Claude_direction='one text packet review; responses and accepted/rejected decisions saved; not actual video review');save('state.json',state)
print(json.dumps({'documents':'written','duration':timing['duration'],'race_end':timing['race_end']},ensure_ascii=False))
