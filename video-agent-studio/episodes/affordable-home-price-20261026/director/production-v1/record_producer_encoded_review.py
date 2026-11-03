"""Record actually viewed encoded samples and concise, pinned technical evidence."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
EP=HERE.parents[1]
ROOT=EP.parents[2]
OUT=EP/'outputs/private-production-v1'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
rel=lambda p:p.relative_to(ROOT).as_posix()
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
dest=HERE/'producer_encoded_review_v1.json'
assert not dest.exists()
render_path=EP/'editor/render_receipt.json'
render=read(render_path)
video=Path(render['final_file'])
assert sha(video)==render['final_sha256']=='ad9df5989c019395e9ea9eb7877c81300cf78e9ab611536ebcc7431c8fc3609a'
assert render['full_AV_decode'] and render['decode_returncode']==0
plan=read(OUT/'encoded_frame_plan.json')
assert plan['final_sha256']==render['final_sha256']
viewed={'00002','00034','00056','00065','00074','00092','00095','00107',
        '00125','00136','00117','00118','00160','00161','00007','00143'}
assert {Path(r['file']).stem for r in plan['critical_frames']}==viewed
images=plan['critical_frames']+plan['contact_sheets']+[plan['contact_overview']]
for row in images:assert sha(OUT/row['file'])==row['sha256']
signal_path=EP/'qa/audio-v1/final-signal-v1/signal_receipt.json'
signal=read(signal_path)
assert signal['approved_for_technical_signal_scope'] and signal['required_issues']==signal['critical_issues']==[]
assert signal['video_sha256']==render['final_sha256']
m=signal['measurements']
v=next(s for s in render['ffprobe']['streams'] if s['codec_type']=='video')
a=next(s for s in render['ffprobe']['streams'] if s['codec_type']=='audio')
report={'status':'producer_sampled_encoded_frames_pass_no_new_required_findings',
    'video_sha256':render['final_sha256'],'script_sha256':read(HERE/'locked_script.json')['script_sha256'],
    'technical':{'bytes':video.stat().st_size,'duration_s':render['duration_s'],
        'width':v['width'],'height':v['height'],'fps':v['r_frame_rate'],'codec':v['codec_name'],
        'audio_codec':a['codec_name'],'sample_rate':a['sample_rate'],'channels':a['channels'],
        'full_AV_decode_passed':True,'render_receipt':rel(render_path),'render_receipt_sha256':sha(render_path)},
    'signal':{k:m[k] for k in ['integrated_LUFS','LRA_LU','true_peak_dBTP',
        'rail_or_over_full_scale_sample_values','NaN_sample_values','Inf_sample_values','denormal_float32_sample_values']},
    'signal_receipt':{'path':rel(signal_path),'sha256':sha(signal_path),
        'scope':'Actual final AAC full signal analysis; not listening or perceived-click approval.'},
    'actual_viewed':{'overview_scenes':45,'overview_sheets':1,'larger_scene_contact_sheets':5,
        'fullres_critical_frames':16,'image_files':[r['file'] for r in images]},
    'observations':['Observed titles, chart labels and long two-line captions fit their areas.',
        'Tax curve black fill, monthly/savings focus,1month/6month clock focus and postbrand old-scene repetition repairs are visible in the encoded samples.',
        'Observed money labels match the locked script and inherited verified cases.'],
    'known_required_in_observed_scope':[], 'independent_final_media_review':'pending',
    'limitations':{'actual_listening':False,'continuous_playback':False,
        'all188_fullres_frames_viewed_by_producer':False,'Studio_ContentID_review':False}}
dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'actual_critical_fullres':16,'video_sha256':report['video_sha256']}))
