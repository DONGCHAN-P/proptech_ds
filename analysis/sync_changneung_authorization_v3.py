import json
from pathlib import Path
ep=Path('video-agent-studio/episodes/goyang-changneung-20261015')
p=ep/'brief.json';v=json.loads(p.read_text(encoding='utf-8'))
v['authorization'].update(full_script=True,script_finalized=True,paid_generation=True,publication=False,
script_revision='script-v3',script_decision_id='c3ed3e0a2d11',budget_decision_id='5900bea493aa',included_credit_cap=7661,additional_cash_usd_cap=0,new_paid_image_or_music=False)
v['scope']='사용자 저장 원고 v3로 영상 제작 승인. 왕숙 v15·광교동탄 v14의 채널 톤과 지정 레퍼런스 기법을 계승. 실제 프레임 비교→대표 장면 수정·검수→본편 확장 루프. Jun 포함크레딧 상한7661·추가결제0. 최종 완료검토와 공개 업로드는 별도 게이트.'
p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Brief synchronized with exact direct-user approvals; publication remains unauthorized.')
