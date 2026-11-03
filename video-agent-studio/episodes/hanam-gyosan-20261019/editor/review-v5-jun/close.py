from pathlib import Path
import json,hashlib
E=Path(__file__).resolve().parent;EP=E.parents[1];O=EP/'outputs/production-v5-jun'
read=lambda f:json.loads(f.read_text(encoding='utf8'))
def save(f,x):f.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf8')
def sha(f):return hashlib.file_digest(f.open('rb'),'sha256').hexdigest()
V=O/'gyosan_v5_jun.mp4';h=read(E/'handoff.json');assert sha(V)==h['sha256']
c=read(O/'caption_cues.json');maxdelta=max(abs(x['start_frame']-x['speech_start_frame']) for x in c);assert maxdelta<=1
save(E/'editor_visual_review.json',dict(video_sha256=sha(V),inspected=['Actual MP442-target sample contactsheet','FHD intro_after','FHD M004_mid:59A original extension costs and separate sum','FHD M008_mid:C2 exact parcel and locator','FHD M009_resale_recall:resale median chart'],required_findings=0,scope='Sampled encoded stills; not continuous playback or listening',max_caption_display_vs_alignment_start_delta_frames=maxdelta,actual_listening=False,continuous_playback=False,exact_seek_frame_correspondence_guaranteed=False))
h.update(editor_review=str(E/'editor_visual_review.json'),max_caption_display_vs_alignment_start_delta_frames=maxdelta)
q=EP/'qa/review-v5-jun-independent/report.json'
if q.exists():
 qa=read(q);assert qa['sha256']==sha(V);assert qa['required_unresolved']==0
 h.update(status='complete_review_with_declared_limits',independent_qa=str(q),independent_qa_sha256=sha(q),required_unresolved=0,next_owner='director:approved public upload and shelf/state; editor does not upload')
save(E/'handoff.json',h)
manifest=read(O/'input_manifest.json')
for f in E.glob('*.py'):manifest[str(f.relative_to(EP.parents[2]))]=sha(f)
save(O/'input_manifest.json',manifest)
print(json.dumps(dict(status=h['status'],sha256=h['sha256'])))
