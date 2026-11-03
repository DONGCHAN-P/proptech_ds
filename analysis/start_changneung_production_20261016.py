import json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from notify.video_decisions import create,write
e=root/'video-agent-studio/episodes/goyang-changneung-20261015'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
s=read(e/'state.json')
assert s['stage']=='initial_research_ready_with_gaps'
d=create(e.name,'topic','창릉을 왕숙 최종 v15와 같은 지도·달력 중심 형식으로 제작한다. 주제·구성 초안 및 대표 화면 준비 승인. 대본 확정·유료 예산·완료·공개는 별도 게이트.')
d.update(status='approved',scope='new_video_production_preparation',approval_source='direct_user_message_2026-10-16',approval_text='그럼 창릉지역 왕숙과 마찬가지 포맷으로 영상 제작해보자',paid_generation_authorized=False,publication_authorized=False)
write(root/'output/video_decisions/decisions'/f"{d['id']}.json",d)
dec=read(e/'decisions.json');dec['decisions'].append(d);write(e/'decisions.json',dec)
b=read(e/'brief.json');b.update(mode='new_video',scope='왕숙 v15 제작 형식 계승. 전체 계획도→일자리→교통→분양가→생활시설→주변 공급→대체 지역→권역별 일반형 후보. 확정 대본·예산 승인 전에는 무상 조사/초안/대표 화면까지 진행.',requested_deliverables=['longform_video','semantic_subtitles','source_and_QA_manifest','reusable_map_scenes','reviewable_script_and_budget'])
b['authorization'].update(research=True,full_script_draft=True,script_finalized=False,paid_generation=False,publication=False)
write(e/'brief.json',b)
s.update(stage='production_research_and_visual_preparation',topic_decision_id=d['id'],full_script_draft_authorized=True,full_script_authorized=False,active_tasks=['research_primary_sources_v2','existing_trade_comparisons_v2','representative_visuals_v1'],production_format_baseline='namyangju-wangsuk-20261014/readability-cta-v15',paid_generation_authorized=False,publication_authorized=False)
write(e/'state.json',s)
p=read(e/'preflight.json');p['approvals']['topic'].update(decision_id=d['id'],status='approved_production_preparation');p['baseline'].update(previous_video='https://youtu.be/T_GBxTRgRSc',current_video=None,script_revision=None,audio_revision=None);write(e/'preflight.json',p)
print(json.dumps({'topic_decision_id':d['id'],'stage':s['stage']},ensure_ascii=False))
