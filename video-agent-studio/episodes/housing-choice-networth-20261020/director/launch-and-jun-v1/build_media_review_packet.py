"""Freeze actual encoded Jun evidence for an exact-version Claude media review."""
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[5]
HERE=Path(__file__).resolve().parent
EP=HERE.parents[1]
SOURCE=EP/'outputs/jun-production-v1'
RELEASE=EP/'outputs/jun-release-v1'
DEST=HERE/'claude_media_input_v1'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def rel(p):return p.relative_to(ROOT).as_posix()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

assert not (DEST/'media_report.json').exists(),'Use a new immutable review packet if evidence changes.'
receipt=read(EP/'editor/jun-production-v1/render_receipt.json')
frames=read(SOURCE/'encoded_frame_plan.json')
assert frames['status']=='encoded_frames_extracted_review_pending'
video=Path(receipt['final_file']).resolve()
subtitles=SOURCE/'captions_measured.srt'
assert sha(video)==receipt['final_sha256']==frames['final_sha256']
assert receipt['decode_returncode']==0
timing=read(EP/'narration/jun-production-v1/final_timing.json')
signal=read(EP/'editor/jun-production-v1/signal_receipt.json')
assert signal['final_sha256']==sha(video)
source_checks=read(EP/'editor/jun-production-v1/static_checks.json')
bbox=read(SOURCE/'preview/bbox_report.json')
assert source_checks['status']=='pass' and bbox['status']=='sampled_bbox_pass'
DEST.mkdir(exist_ok=True)
images=[]
def append(p,role,extra=None):
    assert p.is_file()
    item={'path':rel(p),'sha256':sha(p),'role':role}
    if extra:item.update(extra)
    images.append(item)
for index,row in enumerate(frames['contact_sheets'],1):
    file=SOURCE/row['file'];assert sha(file)==row['sha256']
    out=DEST/f'encoded_scene_contact_{index:02}.png'
    with Image.open(file) as im:im.convert('RGB').save(out)
    append(out,'actual encoded 50-scene representatives contact sheet',{'source_sha256':row['sha256']})
for chapter in range(1,11):
    row=next(r for r in frames['samples'] if r.get('chapter')==chapter and r['role']=='longest_caption')
    file=SOURCE/row['file'];assert sha(file)==row['sha256']
    append(file,'full resolution current chapter long caption',{'global_time_s':row['global_time_s'],'scene_id':row['scene_id']})
joins=[r for r in frames['samples'] if r['role']=='join_at']
for row in joins[:2]+joins[-1:]:
    file=SOURCE/row['file'];assert sha(file)==row['sha256']
    append(file,'actual encoded brand/join boundary',{'global_time_s':row['global_time_s'],'scene_id':row['scene_id']})
append(RELEASE/'thumbnail.png','user-selected TH003 thumbnail')
metadata=RELEASE/'metadata_measured.json'
desc=RELEASE/'description_measured.md'
report={
    'revision':'jun-production-v1', 'change_scope':'All narration replaced with approved Jun; exact original script/visual assets retained. Actual cue and motion timing, fresh BGM mix, title and thumbnail updated.',
    'video':rel(video),'video_sha256':sha(video),'subtitles':rel(subtitles),'subtitles_sha256':sha(subtitles),
    'metadata':rel(metadata),'metadata_sha256':sha(metadata),'description':rel(desc),'description_sha256':sha(desc),
    'thumbnail':rel(RELEASE/'thumbnail.png'),'thumbnail_sha256':sha(RELEASE/'thumbnail.png'),
    'script_sha256':timing['script_sha256'],'timing_sha256':sha(EP/'narration/jun-production-v1/final_timing.json'),
    'actual_seconds':read(SOURCE/'assembly_edl.json')['total_seconds'],
    'image_manifest':images,'source_static_checks':source_checks,
    'layout_check_summary':{k:v for k,v in bbox.items() if k not in ['checked_chapters','checked_elements']},
    'signal_measurements':signal,'narration_technical_validation':{
        k:v for k,v in read(EP/'narration/jun-production-v1/technical_validation.json').items() if k not in ['paragraph_checks','cue_checks']},
    'prior_exact_script_content_approval':read(HERE/'locked_script.json'),
    'previous_final_media_approval_scope':'Old approvals support unchanged script/visual design only; old audio/timing checks not inherited.',
    'producer_full_AV_decode_returncode':receipt['decode_returncode'],
    'encoded_unique_frames':frames['unique_frame_count'],
    'actual_listening':False,'continuous_playback':False,'Studio_ContentID_review':False,
    'user_guide':'No clipped text, no repetitive unrelated charts/photos, protect numeric semantic captions, no AI badges or unnecessary negative disclaimers, highlight currently spoken target, actual +3s end hold.'
}
audio=EP/'qa/jun-production-v1/audio_review.json'
assert audio.is_file(),'Independent ASR/audio evidence needed before freezing final voice review packet.'
report['independent_audio_review']=read(audio)
report['independent_audio_review_sha256']=sha(audio)
assert report['independent_audio_review'].get('approved') is True
save(DEST/'media_report.json',report)
save(DEST/'image_paths.json',[r['path'] for r in images])
print(json.dumps({'media_report':rel(DEST/'media_report.json'),'image_paths':rel(DEST/'image_paths.json'),
                  'images':len(images),'video_sha256':sha(video),'actual_listening':False},ensure_ascii=False))
