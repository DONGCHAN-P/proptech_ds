import json,sys,hashlib
from pathlib import Path
from datetime import datetime,timezone
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from notify.video_decisions import create,write
e=root/'video-agent-studio/episodes/goyang-changneung-20261015';e.mkdir(exist_ok=True)
assert (root/'output/cleanup-20261015/deletion_result_video.json').exists(),'Guide and first cleanup must finish first'
assert not (e/'state.json').exists(),'Do not replace an existing episode'
for name in ['research','outputs']: (e/name).mkdir(exist_ok=True)
topic=create(e.name,'topic','왕숙 다음 편 창릉: 동일한 지도·달력 분석 형식의 자료조사 시작. 대본·유료 생성·업로드는 미승인.')
topic.update(status='approved',scope='research_only',approval_source='direct_user_request_after_completed_wangsuk_series_order',approval_text='정리되면 이번 영상 양식에 맞게 다음 영상 자료조사를 진행해줘',script_generation_authorized=False,paid_generation_authorized=False,publication_authorized=False)
write(root/'output/video_decisions/decisions'/f"{topic['id']}.json",topic)
brief={'episode_id':e.name,'mode':'new_video_research_only','topic':'고양 창릉: 입주 시점의 일자리·교통·분양가·생활·공급과 권역별 후보','language':'ko','previous_episode':'namyangju-wangsuk-20261014','previous_video_url':'https://youtu.be/T_GBxTRgRSc','next_after_this':'하남 교산','requested_deliverables':['primary_source_research_pack','fact_register_with_status_dates_rights','map_and_calendar_requirements','comparison_and_candidate_matrix','unverified_items'],'guide':'../../guides/제작_기본가이드.md','scope':'전체계획도→일자리→교통→분양가→생활시설→주변공급→대체지역→일반형권역후보,자료조사만','authorization':{'research':True,'full_script':False,'paid_generation':False,'publication':False},'notes':['왕숙의 블록·가격·역 위치는 복사하지 않는다.','목표·예정·운영·발표일과 확인일을 구분한다.','자료가 없으면 미확인으로 남기며 추정값을 확정 사실로 쓰지 않는다.']}
write(e/'brief.json',brief)
write(e/'state.json',{'episode_id':e.name,'stage':'research_in_progress','active_tasks':['primary_source_research'],'topic_decision_id':topic['id'],'script_revision':None,'audio_revision':None,'paid_generation_authorized':False,'publication_authorized':False,'previous_episode_cleanup_completed':True,'started_at':datetime.now(timezone.utc).isoformat()})
write(e/'decisions.json',{'episode_id':e.name,'decisions':[topic]})
p=root/'video-agent-studio/templates/episode_preflight.json';check=json.loads(p.read_text(encoding='utf-8'));check['episode_id']=e.name;check['baseline']['previous_video']='https://youtu.be/T_GBxTRgRSc';check['approvals']['topic'].update(decision_id=topic['id'],status='approved_research_only');write(e/'preflight.json',check)
print(json.dumps({'episode_root':str(e),'topic_research_decision':topic['id']}))
