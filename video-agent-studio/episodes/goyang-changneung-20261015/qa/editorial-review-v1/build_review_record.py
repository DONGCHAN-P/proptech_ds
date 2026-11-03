from pathlib import Path
import hashlib,json
q=Path(__file__).resolve().parent;ep=q.parents[1]
v=ep/'outputs/production-v5/changneung_full_v5r2.mp4'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(v)=='7979a8071e4c07d4047a46b37b4abf6fa89c1a8aa9f4fb0c90dd0d99bec9f0b0'
rows=[('M009', '11:24-12:51', 'actual_0738.png'), ('M008', '10:52.9-11:24.1', 'actual_0659.png'), ('M004', '05:01.9-05:28.1', 'actual_0310.png'), ('M007', '09:15-10:05', 'actual_0571.png'), ('M005/M009', '06:46.4-07:00.4 / 12:12.7-12:31.3', 'actual_0409.png'), ('M002', '02:36.3-02:55.9', 'actual_0164.png'), ('M006', '07:59.8-08:33.2', 'actual_0495.png'), ('M004/M007', '05:50.7-06:25.2 / 10:05-10:25', 'actual_0350.png')]
# 아래 한국어 기록을 최종 산출물로 사용한다.
ko=[
 ('세 후보 장점·대가를 종합하는 결론 화면 부족','같은 항목으로 세 후보의 장점·부담을 나란히 회수'),
 ('가족 달력이 빈 양식으로 남아 대입 방법이 보이지 않음','개인 일정 기입 예시와 기다리는 주거비 계산 구조 제시'),
 ('확장비 소액 차이에 큰 화면을 반복하고 세 후보 총액은 한 번에 비교되지 않음','원값·조건을 보존하며 세 후보 확장 포함 총액을 함께 표시'),
 ('대안 지도에서 가격·거래 건수가 자막과 분리됨','현재 설명 단지의 중위값과 n을 지도 가까이 유지'),
 ('학교·공원·하천 이름 밀집과 여러 면 동시 강조로 위계가 약함','현재 설명 대상만 강조하고 이름·일정판을 정리해 지도 면적 확보'),
 ('업무지 위치를 보여주지만 환승 순서가 구체적으로 보이지 않음','검증된 역명·노선 순서를 지리 지도와 구별해 짧게 표시'),
 ('기산점이 다른 두 기간을 동일 시작점의 막대로 표시','날짜를 만들지 말고 각 기산 사건을 독립된 시작 카드로 표현'),
 ('추상적 조건 세 줄 카드가 오래 반복됨','기존 입주·철도·학교 근거를 이용해 준비·지연 조건을 순차 대비')]
findings=[]
for i,(row,k) in enumerate(zip(rows,ko),1):
 scene,time,evidence=row
 findings.append({'issue_id':f'ER-V1-{i:03}','priority':i,'scene_id':scene,'timecode':time,'severity':'recommended','문제':k[0],'evidence':[evidence,'편집품질_독립검토.md'],'수정안':k[1],'owner':'director/editor','status':'proposal_only','checked_revision':'production-v5r2'})
(q/'findings.json').write_text(json.dumps({'review_type':'편집 품질·메시지 전달 재검토','media_changes_executed':False,'technical_gate_reopened':False,'findings':findings},ensure_ascii=False,indent=2),encoding='utf-8')
h={'status':'독립 검토 완료·수정 미실행','next_owner':'director','video_file':str(v),'video_sha256':sha(v),'script_file':str(ep/'writer/script-v3/script_v3.md'),'project_file':str(ep/'outputs/production-v5/project_v5.json'),'outputs':[str(q/'편집품질_독립검토.md'),str(q/'findings.json')],'coverage':{'existing_v5_actual_samples':706,'existing_v5r2_boundary_samples':15,'new_v5r2_fullsize_samples_s':[145,164,228,310,350,409,495,571,659,689,738],'actual_listening':False,'continuous_playback':False},'recommendation_count':8,'unresolved':'개선안 채택과 제작 실행은 총괄 판단 대기. 이번에는 새 미디어 제작·원본 수정·외부 전송 없음.','limitations':'표본 육안 검수와 원문 독해에 근거한 평가. 실제 전체 청취·연속 시청·이탈률 측정 미실시.'}
(q/'handoff.json').write_text(json.dumps(h,ensure_ascii=False,indent=2),encoding='utf-8')
assert (q/'편집품질_독립검토.md').stat().st_size>1000 and len(json.loads((q/'findings.json').read_text(encoding='utf8'))['findings'])==8
print('review files verified; media hash unchanged')
