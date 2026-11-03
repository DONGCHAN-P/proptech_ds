from pathlib import Path
import json
q=Path('video-agent-studio/episodes/goyang-changneung-20261015/qa/production-v6-preview')
a=json.loads((q/'input_review.json').read_text(encoding='utf-8'))
findings=[]
for i,c in enumerate(a['numeric_boundary_candidates']):
 findings.append({'issue_id':'QAV6-002-'+str(i+1),'scene_id':c['scene_id'],'timecode':c['timecode'],'severity':'recommended' if i==1 else 'required','문제':'자막 의미/수량 묶음이 큐 사이에서 분리됨','evidence':{'source':'outputs/production-v6-preview/project.json','before':c['before'],'after':c['after'],'type':'timeline text inspection; MP4 not yet inspected'},'수정안':'절 경계 우선으로 큐 분리하고 숫자 전체와 단위를 같은 큐에 보존','owner':'editor_v6','status':'open','checked_revision':'production-v6-preview initial project'})
(q/'findings.json').write_text(json.dumps(findings,ensure_ascii=False,indent=2),encoding='utf-8')
plan={'expected_mp4_coverage':['all 10 scene representatives','all board and scene cut boundaries -1/0/+1 frames','maximum zoom or stable closeup states','intro start/end boundaries','speech end, 3-second hold, outro start/end','M002 five destination emphasis and three-column 15 values','M004 price units and scope','M005 block-school-park locator and leaders','M007 six apartment names, six prices and n values'], 'acceptance':['fixed map camera with current spoken target highlighted','detailed maps maintain whole-district locator','white subtitle box continuous during body and hook','no white box in unvoiced intro/outro/hold','semantic caption grouping; S1/DMC/numeric display protected','actual Claude-generated motion adopted with traceable provenance','duration at least 600 seconds','future rail status distinct from operating transport','M002 representative coordinate / current expected routes / 2026-10-19 08:00 / 10-18 query disclosed'],'coverage_status':{'input_timing':'checked','mp4_stream':'pending','mp4_decode':'pending','sampled_frames':'pending','continuous_playback':'unchecked','actual_listening':'unchecked','thumbnail':'outside delegated scope'}}
(q/'review_plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
print('QA findings and coverage plan saved')
