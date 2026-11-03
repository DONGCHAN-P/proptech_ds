"""Record the user's research pivot without changing prior scripts or media."""
from pathlib import Path
import datetime as dt,json
ROOT=Path(__file__).resolve().parents[1]
EP=ROOT/'video-agent-studio/episodes/regional-price-recovery-20261022'
DEST=EP/'research/literature-mechanisms-v1'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
now=dt.datetime.now(dt.timezone.utc).isoformat();DEST.mkdir(parents=True,exist_ok=True)
state=read(EP/'state.json')
if not (DEST/'state_before_research_pivot.json').exists():write(DEST/'state_before_research_pivot.json',state)
state.update(stage='literature_research_before_insight_and_script_rebuild',updated_at=now,
    content_status='user_rejected_chart_recitation_requires_explanatory_insights',
    research_status='Literature review on heterogeneous housing demand, supply constraints, rental/redevelopment and spatial mechanisms; no new causal estimates yet',
    current_direction='insights first; regional differences and Seoul/Gyeonggi mechanisms; interest rates not the main story',
    next_script_status='not_written_not_approved',new_render_authorized_at_this_stage=False,
    literature_research_notes='research_notes/서울 경기 집값 격차의 복합 원인',
    literature_expected_report='reports/서울 경기 집값 격차의 복합 원인.md')
assert state['budget_status']=='voice_generation_deferred_by_user'
write(EP/'state.json',state)
decisions=read(EP/'decisions.json')
key='regional-insight-literature-pivot-20261023'
if not any(d['id']==key for d in decisions['decisions']):
    decisions['decisions'].append({'id':key,'created_at':now,'status':'explicit_research_authorization',
        'basis':['차트를 읽는 반복 대신 지역별 상승과 하락의 원인 분석','뭘 말할건지를 먼저 정리','금리 외 복잡한 이유와 부동산 논문 조사 요청'],
        'scope':'Read scholarly/official research and produce mechanisms, evidence strength, counterevidence and testable data plans. Preserve original v3/media. No new script approval, paid synthesis, render or upload.'})
write(EP/'decisions.json',decisions)
write(DEST/'request.json',{'task_id':'RPR-LIT-20261023','created_at':now,
    'scope':'literature_and_insight_research_only','as_of':'2026-10-23','target':'Seoul/Gyeonggi regional differences, with comparison regions and 2006+ trade data',
    'notes_root':'research_notes/서울 경기 집값 격차의 복합 원인','report':'reports/서울 경기 집값 격차의 복합 원인.md',
    'workstreams':['demand_jobs_households','supply_redevelopment_rental','spatial_transport_expectations'],
    'literature_prior_register':'analysis/housing_growth_2006/research/external_factors_sources.json',
    'local_data_limits':'Prior matched-index and transaction summaries are descriptive; district household and job history missing; no new causal attribution is established',
    'voice':'deferred_by_user','paid_calls':0,'prior_script_and_media_preserved':True})
shelf=read(ROOT/'config/video_shelf.json')
entry=next(e for e in shelf['entries'] if e['name']=='지역별가격회복')
entry['status']='기존 v3·화면 검토본 보존 · 사용자 요청으로 인사이트·지역별 복합 원인 논문 조사 선행 · 새 대본 미확정 · 음성 생성 보류. 대본보기.html은 이전 v1.'
write(ROOT/'config/video_shelf.json',shelf)
feedback=ROOT/'video-agent-studio/guides/사용자_피드백_이력.md'
heading='## 2026-10-23 · 지역 데이터 영상은 인사이트를 먼저 확정'
if heading not in feedback.read_text(encoding='utf8'):
    with feedback.open('a',encoding='utf8')as stream:
        stream.write('\n\n'+heading+'\n\n사용자는 같은 가격 그래프를 반복하며 상승률과 회복 기간을 읽는 구성에 문제를 제기했다. 먼저 무엇을 설명할지 정리하고, 지역별 수요·공급·일자리·이동·접근성 등의 차이와 상호작용을 논문 및 자료로 검토한다. 확인된 주장·반례·미확인을 구분한 뒤 대본과 화면을 결정한다. 금리를 주된 설명으로 고정하지 않고 서울·경기 내부 차이도 검증한다. 기존 음성 생성 보류는 유지한다.\n')
print(json.dumps({'stage':state['stage'],'notes_root':state['literature_research_notes'],'voice':'deferred'},ensure_ascii=False))
