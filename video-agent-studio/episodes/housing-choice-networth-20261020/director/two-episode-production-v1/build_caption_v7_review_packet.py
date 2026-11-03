"""Freeze targeted, actual encoded caption evidence; never substitutes for playback."""
import hashlib
import json
import math
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE=Path(__file__).resolve().parent
EP=HERE.parents[1]
ROOT=EP.parents[2]
SOURCE=EP/'outputs/private-production-v3'
RELEASE=EP/'outputs/private-release-v3'
DEST=HERE/'claude_media_v7_input'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
rel=lambda p:p.relative_to(ROOT).as_posix()

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

assert not (DEST/'media_report.json').exists(),'Retain frozen evidence; choose a new packet revision.'
receipt=read(EP/'editor/private-production-v3/render_receipt.json')
video=Path(receipt['final_file']).resolve()
subtitles=Path(receipt['captions_file']).resolve()
assert video.is_relative_to(EP) and subtitles.is_relative_to(EP)
assert receipt['decode_returncode']==0 and sha(video)==receipt['final_sha256']
assert sha(subtitles)==receipt['captions_sha256']
assert receipt['audio_stream_identical_to_v2'] is True
timing=read(EP/'narration/free-tts-v1/caption-v7/final_timing.json')
changes=read(EP/'narration/free-tts-v1/caption-v7/change_manifest.json')
edl=read(SOURCE/'assembly_edl.json')
edl_review=read(HERE/'edl_review_v7.json')
assert edl_review['checked_cues']==206 and edl_review['subtitles_sha256']==sha(subtitles)

all_cues={c['id']:(ch['chapter'],c) for ch in timing['chapters'] for c in ch['cues']}
repaired_ids={new for row in changes['v6_to_v7_cue_mapping'] if row['was_short'] for new in row['v7_ids']}
extreme_ids={max(all_cues,key=lambda k:max(map(len,all_cues[k][1]['display_lines']))),
             max(all_cues,key=lambda k:all_cues[k][1]['end_s']-all_cues[k][1]['start_s'])}
for chapter,fragment in [(5,'대출잔액에'),(6,'한국 돈으로'),(9,'주거 계획이 바뀝니다'),(10,'매매에 더 큰 가치를')]:
    extreme_ids.add(next(k for k,(ch,c) in all_cues.items() if ch==chapter and fragment in c['text']))
selected_ids=repaired_ids|extreme_ids
rows=[]
for cue_id in selected_ids:
    chapter,cue=all_cues[cue_id]
    local=(cue['start_s']+cue['end_s'])/2
    off=next(o['global_offset_s'] for o in edl['offset_map'] if o['chapter']==chapter and o['local_start_s']<=local<o['local_end_s'])
    rows.append({'cue_id':cue_id,'chapter':chapter,'text':cue['text'],'display_lines':cue['display_lines'],
                 'global_time_s':round((local+off)*30)/30,'is_short_repair':cue_id in repaired_ids})
rows.sort(key=lambda r:r['global_time_s'])
DEST.mkdir(exist_ok=True);(DEST/'images').mkdir(exist_ok=True)
ffmpeg=ROOT/read(HERE/'ffmpeg_receipt.json')['binary']

def extract(row):
    p=DEST/'images'/f"{row['cue_id']}.png"
    assert not p.exists(),f'Keep existing frame evidence: {p}'
    subprocess.run([str(ffmpeg),'-v','error','-nostdin','-threads','2','-ss',str(row['global_time_s']),
                    '-i',str(video),'-frames:v','1','-n',str(p)],check=True,capture_output=True)
    row.update(path=rel(p),sha256=sha(p))
    return row

with ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(extract,rows))
images=[]
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
for offset in range(0,len(rows),16):
    group=rows[offset:offset+16]
    sheet=Image.new('RGB',(1760,math.ceil(len(group)/2)*118),(234,237,240))
    draw=ImageDraw.Draw(sheet)
    for i,row in enumerate(group):
        x=(i%2)*880;y=(i//2)*118
        draw.text((x+8,y+4),f"{row['cue_id']} | {row['global_time_s']:.3f}s",font=font,fill=(24,42,54))
        with Image.open(ROOT/row['path']) as frame:
            crop=frame.crop((96,864,1824,1014)).resize((864,75),Image.Resampling.LANCZOS)
            sheet.paste(crop,(x+8,y+30))
    p=DEST/'images'/f'caption_contact_{offset//16+1:02}.png';sheet.save(p)
    images.append({'path':rel(p),'sha256':sha(p),'scope':'Actual final encoded caption-region crops, with cue ID/time. Complete frames retained in frame_manifest.json.'})
for row in rows:
    if row['cue_id'] in extreme_ids:
        images.append({**row,'scope':'Actual final encoded full-resolution frame: longest-character-line candidate, longest-duration cue, core term or previously defective caption.'})
metadata_path=RELEASE/'metadata_measured.json';metadata=read(metadata_path)
description=RELEASE/metadata['description'];thumbnail=RELEASE/'thumbnail.png'
images.append({'path':rel(thumbnail),'sha256':sha(thumbnail),'scope':'Unchanged release thumbnail.'})
source_qa=EP/'qa/private-production-v1/source_v7_pass_receipt.json'
source_review=read(source_qa)
assert source_review['approved'] is True
source_summary={k:source_review[k] for k in ['approved','approval_scope','script_sha256',
    'caption_timing_sha256','required_issues','critical_issues','coverage','issue_status']}
source_summary.update(receipt_path=rel(source_qa),receipt_sha256=sha(source_qa))
prior=read(HERE/'claude_media_v6_input/media_report.json')
report={k:prior[k] for k in ['audio_evidence','coverage_limits']}
report['audio_evidence']={**report['audio_evidence'],'encoded_AAC_exact_prior_stream':True,
    'encoded_AAC_sha256':receipt['audio_stream_SHA256'],'new_TTS_or_audio_reencoding':False}
for field,p in [('video',video),('subtitles',subtitles),('metadata',metadata_path),('description',description),('thumbnail',thumbnail)]:
    report[field]=rel(p);report[field+'_sha256']=sha(p)
report.update(script_sha256=timing['script_sha256'],image_manifest=images,
    technical={'duration_s':edl['total_seconds'],'width':1920,'height':1080,'fps':30,
               'full_video_and_audio_decode':'passed','actual_encoded_caption_frames':len(rows)},
    change_scope={'issue':'CAPTION-MEANING-001','before':342,'after':206,'old_short_cues':47,'short_cues_after':0,
                  'repaired_caption_groups':len(repaired_ids),'audio_changed':False,'script_changed':False,
                  'scene_anchors_choreography_assets':'unchanged; exact source audit retained by editor',
                  'repaired_cues':rows},
    source_checks={'independent_source_QA':source_summary,'producer_conservation':read(HERE/'producer_caption_v7_review.json'),
                   'EDL_and_all_subtitles':edl_review},
    asset_provenance=read(EP/'visual/private-production-v1/housing-stability-v1.json'),
    private_release_metadata={'title':metadata['title'],'description':description.read_text(encoding='utf-8'),
                              'chapters':metadata['chapters'],'visibility':'private','scheduled':False},
    known_required_issues=[],
    independent_Codex_final_review='New encoded revision pending final independent receipt; this packet makes no approval claim.')
(DEST/'frame_manifest.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(DEST/'media_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(DEST/'image_args.json').write_text(json.dumps([r['path'] for r in images],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'actual_encoded_evidence_frozen','frames':len(rows),'Claude_images':len(images),
                  'video_sha256':sha(video),'report':rel(DEST/'media_report.json')}))
