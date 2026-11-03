"""Record the exact, explicit user reply for the frozen two-Shorts review packet."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
HERE=Path(__file__).resolve().parent;EP=HERE.parents[1];ROOT=EP.parents[2]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
folder=HERE/'shorts_media_input_v2';report=read(folder/'report.json');listing=read(folder/'image_paths.json')
assert len(listing)==12 and len(report['image_manifest'])==12
assert [r['video_sha256'] for r in report['items']]==[
    '8599bb589247e8b6c62b577bee3a5ce5898026dffce8abf13c5033a18b4b5efd',
    '3f70117cab7c454257a1cb539d61c85d6efcba3c5a052c843f2f796c973cdbe3']
for row in report['image_manifest']:
    assert row['path'] in listing and sha(ROOT/row['path'])==row['sha256']
for row in report['items']:
    assert sha(ROOT/row['video'])==row['video_sha256']
    assert sha(ROOT/row['subtitles'])==row['subtitles_sha256']
auth={'authorized':True,'user_quote':'쇼츠 자료 묶음의 Claude 전송 승인',
    'questionItemId':'["request_user_input_async","call_44acb9e0445d4985af0bcde415030f10",0]',
    'destination':'Claude (Anthropic) Opus/max through existing logged-in subscription',
    'scope':'exact frozen two-Shorts v2 packet:12 specified encoded PNGs, both scripts/SRTs, aggregates and review records',
    'excluded':['audio files','API keys','account information','individual transactions','metadata/description bodies'],
    'report':(folder/'report.json').relative_to(ROOT).as_posix(),'report_sha256':sha(folder/'report.json'),
    'image_list':(folder/'image_paths.json').relative_to(ROOT).as_posix(),'image_list_sha256':sha(folder/'image_paths.json'),
    'video_sha256':[r['video_sha256'] for r in report['items']],
    'at_utc':datetime.now(timezone.utc).isoformat()}
path=HERE/'shorts_claude_payload_authorization.json';assert not path.exists()
path.write_text(json.dumps(auth,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
state_path=EP/'state.json';state=read(state_path)
state['shorts_jun_v1'].update(status='two_v2_videos_Codex_pass_Claude_final_review_running',Claude_payload_question_pending=False,
    Claude_payload_authorization=path.relative_to(ROOT).as_posix())
state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'recorded':True,'images':len(listing),'video_count':2,'new_TTS_calls':0}))
