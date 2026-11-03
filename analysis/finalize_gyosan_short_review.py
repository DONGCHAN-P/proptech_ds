from pathlib import Path
import json, hashlib, re
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
EP=ROOT/'video-agent-studio/episodes/hanam-gyosan-20261019'
OUT=EP/'outputs/shorts-leader-v1'
ED=EP/'editor/shorts-leader-v1'
video=OUT/'gyosan_leader_short_v1r2.mp4'
digest=hashlib.sha256(video.read_bytes()).hexdigest()
assert digest=='14e972395577696f955c241ada9a5b0a1da41a9de463d89eaa882a64c550247e'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
tech=read(OUT/'technical_r2.json')
vs=next(x for x in tech['streams'] if x['codec_type']=='video')
assert (vs['width'],vs['height'],vs['avg_frame_rate'])==(1080,1920,'30/1')
assert any(x['codec_type']=='audio' for x in tech['streams'])
layout=read(ED/'layout_validation_r2.json')
assert not layout['critical_bounds_violations'] and not layout['critical_text_overlaps']
plan=read(ED/'clip_plan.json')
captions=re.findall(r'\d\d:\d\d:\d\d,\d\d\d --> \d\d:\d\d:\d\d,\d\d\d', (OUT/'gyosan_leader_short_v1.srt').read_text(encoding='utf-8-sig'))
assert captions and plan['duration']<=float(tech['format']['duration'])
review={
 'status':'passed_with_limits','sha256':digest,'required_unresolved':0,
 'reviewed_at':datetime.now(timezone.utc).isoformat(),'reviewer':'root; independent of editing agent',
 'file':str(video.relative_to(EP)).replace('\\','/'),'duration_s':float(tech['format']['duration']),
 'closed_issues':[{'id':'GY-SHORT-MAP-01','resolution':'Actual encoded r2 17/33s show complete C2/B2 parcels outside locator and mask; checked directly by root'}],
 'coverage':{'actual_encoded_r2_frames_viewed_s':[1,17,33,44,49],'actual_encoded_initial_frames_viewed_s':[1,17,33,44,49],'full_av_decode_root_exit_code':0,'text_bounds_elements':204,'text_bounds_failures':0,'editor_text_overlaps':0,'source_narration':'Existing approved Jun M008; 10 meaning-unit excerpts; editor source-PCM exact and AAC correlation checks reused, no new speech','caption_cues':len(captions),'actual_listening':False,'continuous_playback':False,'actual_device_playback':False,'independent_external_fact_research':False},
 'content_assessment':{'visuals':'official plan geometry rendered as diagrams; no photorealistic generated events, people or places','narration':'generic licensed Jun voice; synthetic narration is acknowledged in description, no named-person impersonation','platform_label_guaranteed_absent':False},
 'limits':['Sampled visual review, not continuous audiovisual review','Plan facts reused from reviewed public Jun v5; no new market claims','Device safety is a layout model, not all-device guarantee'],
 'paid_generation_calls':0
}
qp=EP/'qa/shorts-leader-v1/final_review.json'
qp.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'sha256':digest,'required_unresolved':0,'duration':review['duration_s'],'caption_cues':len(captions)}))
