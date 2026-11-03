from pathlib import Path
import json
q=Path('video-agent-studio/episodes/goyang-changneung-20261015/qa/production-v6-preview');f=json.loads((q/'findings.json').read_text(encoding='utf-8'))
for x in f:
 if x['issue_id'].startswith('QAV6-002') or x['issue_id']=='QAV6-003':
  x['status']='closed_verified_r2_mp4';x['checked_revision']='r2 c9e317a6fe1267e89ce9e31ceb903a295286c66e0f0477bd0abc8d02ce758bd4';x['evidence']={'prior':x['evidence'],'recheck':'252 actual MP4 timestamp samples inspected through 11 QA contact sheets; revised numeric groups and five destination focus/captions align'}
for issue,sc,t,problem,fix,evidence in [('QAV6-005','M000/M001','00:00~00:08.5 and 00:56.5~01:04.3','광역관계 설명 중 지축역만 현재 설명 대상으로 표시','전체 권역 관계 요약으로 교체하고 특정 지축 강조 제거','actual MP4 frames 29,1725; sheet01'),('QAV6-006','M007','11:19.5 /11:34.4 /11:55.3','첫 단지 발화 때 둘째 단지만 현재대상 요약으로 표시','쌍의 두 단지를 동등 표시하거나 실제 발화별 focus 일치','actual MP4 frames20386,20832,21460; sheet09')]:
 f.append({'issue_id':issue,'scene_id':sc,'timecode':t,'severity':'required','문제':problem,'evidence':evidence,'수정안':fix,'owner':'editor_v6','status':'open','checked_revision':'r2 c9e317a6fe1267e89ce9e31ceb903a295286c66e0f0477bd0abc8d02ce758bd4'})
(q/'findings.json').write_text(json.dumps(f,ensure_ascii=False,indent=2),encoding='utf-8')
