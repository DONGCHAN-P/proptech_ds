from pathlib import Path
import json,hashlib
E=Path(__file__).resolve().parent;EP=E.parents[1];O=EP/'outputs/production-v5'
def read(f):return json.loads(f.read_text(encoding='utf8'))
def save(f,x):f.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf8')
def sha(f):return hashlib.file_digest(f.open('rb'),'sha256').hexdigest()
V=O/'gyosan_review_v5_free_tts.mp4';h=read(E/'handoff.json');assert sha(V)==h['sha256']
save(E/'editor_visual_review.json',dict(video_sha256=sha(V),inspected=['changed_proofs/contactsheet.jpg:15 parent midpoints,10 body titles,6 chapter titles,M009 resale recall','changed_proofs/new_spoken_phrases.jpg:21 changed spoken phrase midpoint samples','FHD:M002_v4_014_p11_new.wav_mid.png','FHD:M008_v4_016_p01_new.wav_mid.png','FHD:M009_resale_recall.png'],findings_required=0,scope='Sampled actual encoded frames, not continuous video/audio review',actual_listening=False,continuous_playback=False,nearby_boundary_files_available=True,nearby_boundary_all_visually_reviewed=False,exact_seek_frame_correspondence_guaranteed=False))
manifest=read(O/'input_manifest.json')
for f in [*E.glob('*.py'),E/'placement_guide.md',E/'audio_reuse.json',E/'units_prepared.json']:
 manifest[str(f.relative_to(EP.parents[2]))]=sha(f)
save(O/'input_manifest.json',manifest)
h.update(editor_review=str(E/'editor_visual_review.json'),visual_inheritance=str(E/'visual_inheritance.json'),actual_encoded_samples=113,limitations=['실제 청취·발음·자연스러움 및 전편 연속 재생 미검수','정지 프레임 seek의 정확 절대프레임 대응은 보장하지 않음','자족5/7 정밀필지 미확정 등 v4 선언 범위 유지'])
q=EP/'qa/review-v5-independent/report.json'
if q.exists():
 qa=read(q);assert qa['sha256']==sha(V);assert qa['required_unresolved']==0
 h.update(status='complete_local_free_review',independent_qa=str(q),independent_qa_sha256=sha(q),required_unresolved=0,next_owner='director: shelf/state and local user delivery; no upload')
save(E/'handoff.json',h)
print(json.dumps(dict(status=h['status'],sha256=h['sha256'])))
