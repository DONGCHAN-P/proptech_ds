"""Freeze actual encoded media evidence for an independent Claude review."""
import hashlib
import json
import subprocess
from pathlib import Path
from PIL import Image

EP=Path(__file__).resolve().parents[2]
ROOT=EP.parents[2]
HERE=Path(__file__).parent
SOURCE=EP/'outputs/private-production-v2'
RELEASE=EP/'outputs/private-release-v2'
DEST=HERE/'claude_media_v6_input'
DEST.mkdir(exist_ok=True)
(DEST/'images').mkdir(exist_ok=True)
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    digest=hashlib.sha256()
    with p.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):
            digest.update(block)
    return digest.hexdigest()
def relative(p):return p.relative_to(ROOT).as_posix()
receipt=read(EP/'editor/private-production-v2/render_receipt.json')
plan=read(SOURCE/'encoded_frame_plan.json')
edl=read(SOURCE/'assembly_edl.json')
timing=read(EP/'narration/free-tts-v1/final_timing.v6.json')
video=Path(receipt['final_file']);subtitles=Path(receipt['captions_file'])
assert receipt['decode_returncode']==0 and sha(video)==receipt['final_sha256']==plan['final_sha256']
assert sha(subtitles)==receipt['captions_sha256']
metadata_path=RELEASE/'metadata_measured.json'
metadata=read(metadata_path)
description_path=RELEASE/metadata['description']
thumbnail=RELEASE/'thumbnail.png'
images=[]
for i,sheet in enumerate(plan['contact_sheets'],1):
    source=SOURCE/sheet['file']
    assert sha(source)==sheet['sha256']
    target=DEST/'images'/f'overview_{i:02}.png'
    with Image.open(source) as im:im.save(target)
    images.append({'path':relative(target),'sha256':sha(target),'scope':'actual final encoded scene overview; small text requires fullres samples'})
selected=[(1,'s4'),(2,'s2g'),(3,'s3d'),(4,'s4d'),(7,'s7a'),(8,'s8h'),(8,'s8l'),(10,'s10invest'),(10,'s10life'),(10,'s10next')]
for chapter,scene in selected:
    row=next(r for r in plan['samples'] if r.get('chapter')==chapter and r['scene_id']==scene and r['role']=='representative')
    p=SOURCE/row['file']
    assert sha(p)==row['sha256']
    images.append({'path':relative(p),'sha256':sha(p),'chapter':chapter,'scene':scene,'global_time_s':row['global_time_s'],'scope':'actual encoded 1920x1080 frame'})
ffmpeg=ROOT/read(HERE/'ffmpeg_receipt.json')['binary']
for chapter,cue_id in [(5,'C05_P023Q004'),(6,'C06_P027Q003')]:
    c=next(c for c in timing['chapters'] if c['chapter']==chapter)
    cue=next(cue for cue in c['cues'] if cue['id']==cue_id)
    local=(cue['start_s']+cue['end_s'])/2
    offset=next(o['global_offset_s'] for o in edl['offset_map'] if o['chapter']==chapter and o['local_start_s']<=local<o['local_end_s'])
    time=round((local+offset)*30)/30
    target=DEST/'images'/f'changed_ch{chapter:02}_{time:.3f}s.png'
    if not target.exists():
        subprocess.run([str(ffmpeg),'-v','error','-nostdin','-ss',str(time),'-i',str(video),'-frames:v','1','-n',str(target)],check=True,capture_output=True)
    images.append({'path':relative(target),'sha256':sha(target),'chapter':chapter,'cue':cue_id,'cue_text':cue['text'],'global_time_s':time,'scope':'actual encoded changed-caption midpoint'})
images.append({'path':relative(thumbnail),'sha256':sha(thumbnail),'scope':'actual release thumbnail'})
audio_review=read(EP/'qa/private-production-v1/audio_v6_delta_handoff.json')
assert audio_review['approved'] and not audio_review['required_issues']
report={
    'video':relative(video),'video_sha256':sha(video),
    'subtitles':relative(subtitles),'subtitles_sha256':sha(subtitles),
    'metadata':relative(metadata_path),'metadata_sha256':sha(metadata_path),
    'description':relative(description_path),'description_sha256':sha(description_path),
    'thumbnail':relative(thumbnail),'thumbnail_sha256':sha(thumbnail),
    'script_sha256':timing['script_sha256'],
    'technical':{'duration_s':1525.266667,'width':1920,'height':1080,'fps':30,'audio':'AAC 48kHz stereo','full_video_and_audio_decode':'passed','producer_scene_overview_count':50,'extracted_unique_frames':175},
    'source_checks':{'same_model_and_amounts':'previous dual content approval retained','v6_changed_terms':'two synonyms clarified; no financial changes','CLI_BBox_native_timing_and_canonical_carve':'passed; exact source receipts retained','subtitles':'342 actual-word-aligned cues; no overlaps; brand offsets independently matched; maximum rounding error0.5ms','CTA_after_last_spoken_word_seconds':3.019251333333159},
    'audio_evidence':{'full_original_10_chapter_ASR_seconds':1508.9,'numeric_ambiguous_clips':'seven values resolved by targeted small+medium local ASR','replaced_paragraphs':2,'unchanged_paragraphs_SHA_reused':52,'new_paragraphs_seconds':48.648,'new_small_and_medium_runs':4,'new_terms_and_quantities':'matched; 2 required lexical issues closed','integrated_LUFS':-17.2,'LRA_LU':4.1,'true_peak_dBFS':-2.8,'NaN_Inf_denormal_counts':0,'actual_listening':False},
    'private_release_metadata':{'title':metadata['title'],'description':description_path.read_text(encoding='utf-8'),'chapters':metadata['chapters'],'visibility':'private','scheduled':False},
    'image_manifest':images,
    'independent_Codex_final_review':'in progress; not pre-approved by this packet',
    'known_required_source_and_targeted_ASR_issues':[],
    'coverage_limits':{'continuous_playback':False,'actual_listening':False,'Studio_ContentID_review':False,'scope':'Actual final encoded sampled frames, source layout/timing checks, full decode and signal/ASR evidence only.'},
    'evidence_receipts':{relative(p):sha(p) for p in [EP/'editor/private-production-v2/render_receipt.json',EP/'qa/private-production-v1/source_v6_pass_receipt.json',EP/'qa/private-production-v1/audio_v6_delta_review.json',HERE/'edl_review_v6.json',HERE/'final_signal_v6/receipt.json']}
}
(DEST/'media_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(DEST/'image_args.json').write_text(json.dumps([r['path'] for r in images],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'video_sha256':report['video_sha256'],'images':len(images),'media_report':relative(DEST/'media_report.json'),'uploaded':False}))
