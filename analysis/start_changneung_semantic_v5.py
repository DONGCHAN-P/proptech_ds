import json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from notify.video_decisions import write,now
ep=root/'video-agent-studio/episodes/goyang-changneung-20261015'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
event_path=root/'output/telegram_conversation/inbox/718066298.json';event=read(event_path)
assert event['source']=='authenticated_telegram_user'
if event.get('application_status')=='applied':raise SystemExit('Already applied; do not restart')
request={'at':now().isoformat(),'source_update_id':event['update_id'],'baseline':'outputs/production-v4/changneung_full_v4r2.mp4','scope':event['text'],'preserve':['script-v3 narration','audio-v3 AAC mix','183 normalized caption cues','24140 frames','brand and channel tokens'],'visual_revision':'production-v5','new_paid_generation':False,'upload_authorization':'existing v4r2 private upload preserved; no v5 upload until scoped release decision','required_representatives':['M002 job transition+regional destinations','semantic school focus','price breakdown motion']}
out=ep/'outputs/production-v5';write(out/'revision_request.json',request)
s=read(ep/'state.json');s.update(stage='semantic_visual_revision_v5',active_tasks=['semantic-v5-editor','semantic-v5-visual','semantic-v5-qa'],revision_request=request['scope'],revision_baseline=request['baseline'],visual_revision='production-v5',new_paid_generation=False,pending_gate=None,pending_decision_ids={},publication_authorized=False);write(ep/'state.json',s)
event.update(application_status='applied',applied_at=now().isoformat(),application_result='v5 visual revision started; user narration/audio retained; not yet completed',revision_request_file=str(out/'revision_request.json'));write(event_path,event)
guide=root/'video-agent-studio/guides/사용자_피드백_이력.md';text=guide.read_text(encoding='utf-8')
heading='# 2026-10-16 · 창릉 대사 동기 강조와 화면 다양성'
if heading not in text:guide.write_text(text+'\n'+heading+'\n\n텔레그램718066298: 지도를 띄우는 동안 대사·자막에 맞는 실제 위치를 강조해야 한다. 1:38 일자리 시작에는 명확한 화면 전환이 필요하며 서울 외부 업무지의 위치 라벨을 표시한다. 같은 지도를 반복하지 말고 설명에 맞는 이미지와 모션그래픽으로 보완한다. 지도 카메라를 반복 확대하는 대신 실제 대상의 색·면·선과 간결한 라벨을 연결하고, 지도가 필요 없는 가격·일정·선택 조건은 도표·단계·비교 화면으로 전환한다. 기존 팔레트·자막·음성은 계승한다. 생성 이미지는 정확한 위치나 실제 개발 모습을 증명하지 않으며, 정보 그래픽이 더 적합한 곳은 데이터 기반 도형으로 만든다.\n',encoding='utf-8')
print('v5 request applied and production state recorded')
