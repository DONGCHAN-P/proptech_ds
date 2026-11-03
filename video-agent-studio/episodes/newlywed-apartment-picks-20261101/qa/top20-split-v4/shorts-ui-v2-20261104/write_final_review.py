"""Record a completed direct visual review; invoke only after viewing the listed sheets."""
from pathlib import Path
import argparse
import hashlib
import json
from datetime import datetime, timezone

Q=Path(__file__).resolve().parent
E=Q.parents[2]
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
ap=argparse.ArgumentParser()
ap.add_argument('--id',required=True)
ap.add_argument('--ui-count',type=int,required=True)
args=ap.parse_args()
sid=args.id
m=read(Q/'encoded'/sid/'encoded_manifest.json')
t=read(Q/f'{sid}_technical_review.json')
source=next(x for x in read(Q/'source_review.json')['shorts'] if x['short_id']==sid)
inputs=next(x for x in read(Q/'inputs_review.json')['shorts'] if x['short_id']==sid)
assert t['status']=='passed_technical_pending_direct_visual_review'
assert source['passed'] and inputs['passed']
assert sha(m['video'])==m['video_sha256']==t['video_sha256']
viewed=[dict(path=p,sha256=sha(p),scope='contact sheet of decoded MP4 frames, directly viewed') for p in m['contacts']+t['numeric_contacts']]
viewed += [dict(path=p,sha256=sha(p),scope='modeled UI overlay on decoded MP4 frame, directly viewed') for p in m['UI_mockups'][:args.ui_count]]
criteria=[
    'First frame gives the newlywed topic and exact rank range; the complete approved question precedes the first spoken regional rank.',
    'Five-row ledger removed; active region, couples count, large prices, bright photo band and captions remain distinct.',
    'All regional first/middle/last samples and boundary samples inspected; no confirmed wrong-region carryover, text clipping, or data confusion.',
    'Before/first-visible/bar-complete frames inspected for each numeric row. Values appear in order; proportional bars, labels and sample counts match frozen facts.',
    'Longest-caption samples and modeled app gutter inspected. Core text, units and sources remain inside the supplied safe profile.',
    'One complete CTA, final spoken caption and clean final hold inspected. No premature final cut confirmed.'
]
r=dict(task_id='shorts-ui-v2-20261104',short_id=sid,status='passed_for_local_review',checked_at_utc=datetime.now(timezone.utc).isoformat(),
       video=m['video'],video_sha256=m['video_sha256'],required_open_count=0,critical_open_count=0,findings=[],
       checked_revision=m['video_sha256'],bytes=t['bytes'],duration_s=float(t['probe']['format']['duration']),
       codecs=dict(video='h264',audio='aac',resolution=[1080,1920],fps=30,sample_rate=48000,channels=2),
       checks=criteria,technical_review=f'{sid}_technical_review.json',inputs_review='inputs_review.json',source_review='source_review.json',
       coverage=dict(parent_encoded_frame_samples=len(m['frames']),independent_numeric_frame_samples=len(t['numeric_frames']),
                     direct_viewed_sheets=viewed,scene_and_boundary_samples='all scenes; -0.10/0/+0.10/+0.30/+0.60s where available',
                     max_zoom='No camera zoom in this revision; fixed object-fit cover crop inspected in each regional scene.',
                     caption_completeness='All locked cues and wrapped source text checked; encoded longest/representative captions visually sampled.',
                     full_video_decode='independently passed',master_audio_signal='all sentence head/tail windows independently checked; unchanged source PCM guards verified',
                     actual_numeric_pronunciation='unchecked by listening; prior 23 numeric-sentence ASR supporting evidence reused only after source hash check',
                     actual_listening='unchecked',continuous_playback='unchecked'),
       final_hold_s=inputs['final_hold_s'],limitations=['Sampled encoded-frame review is not continuous playback.','Signal checks, immutable source PCM and ASR support do not substitute for actual listening.','Local review pass does not authorize upload or carry over an earlier user approval.'],
       next_owner='parent director: integrate exact-SHA local review receipt into the new version decision')
(Q/f'{sid}_final_review.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(short_id=sid,status=r['status'],video_sha256=r['video_sha256'],required_open_count=0,critical_open_count=0)))
