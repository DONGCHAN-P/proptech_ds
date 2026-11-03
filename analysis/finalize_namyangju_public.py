import json,hashlib
from pathlib import Path
from datetime import datetime,timezone
root=Path(__file__).resolve().parents[1];e=root/'video-agent-studio/episodes/namyangju-wangsuk-20261014';o=e/'outputs/youtube-release-v15'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
rows=read(o/'public_verification.json');assert len(rows)==4 and all(x['privacy']=='public' for x in rows)
main=next(x for x in rows if x['receipt']=='main_upload_receipt.json')
summary={'published_at_verified':datetime.now(timezone.utc).isoformat(),'channel_id':'UCr_mTC0x_Uobv6MrIsOkrXw','main_url':'https://youtu.be/'+main['id'],'videos':rows,'paid_generation_cost':0,'user_publication_instruction':'공개로 그냥 업로드해버리자','processing_note':'API processingStatus retained as returned; privacy public verified','actual_listening':False,'continuous_playback':False}
write(o/'release_summary.json',summary)
s=read(e/'state.json');s.update(stage='published_public',active_tasks=[],pending_gate=None,pending_decision_ids={},publication_authorized=True,publication_status='public',youtube_url=summary['main_url'],shorts_urls=['https://youtube.com/shorts/'+x['id'] for x in rows if x!=main],release_summary='outputs/youtube-release-v15/release_summary.json');write(e/'state.json',s)
cp=root/'config/current_video.json';old=read(cp);write(o/'previous_current_video.json',old)
write(cp,{'version':'namyangju-readability-cta-v15','episode':e.name,'video':(e/'outputs/readability-cta-v15/namyangju_readability_cta_full_v15.mp4').relative_to(root).as_posix(),'subtitles':(e/'outputs/readability-cta-v15/namyangju_readability_cta_full_v15.srt').relative_to(root).as_posix(),'script':(e/'outputs/story-review-v8/script_v8.md').relative_to(root).as_posix(),'voice':'ElevenLabs Jun','duration_seconds':931.9666666666667,'youtube_url':summary['main_url'],'publication_status':'public','shorts_urls':s['shorts_urls'],'previous_video_url':old.get('youtube_url'),'report':(o/'release_summary.json').relative_to(root).as_posix()})
logp=root/'config/publish_log.json';log=read(logp)
write(o/'previous_publish_log.json',log)
if isinstance(log,list):log.append(summary)
else:log.setdefault('namyangju_releases',[]).append(summary)
write(logp,log)
print(json.dumps(summary,ensure_ascii=False))
