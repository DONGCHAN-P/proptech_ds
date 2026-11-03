"""Independent technical checks and extra encoded numeric frames, only for a supplied final manifest."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import subprocess
import wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

Q=Path(__file__).resolve().parent
E=Q.parents[2]
R=E.parents[2]
D=E/'director/top20-split-v4/shorts-ui-v2-20261104'
H=E/'editor/top20-split-v4/shorts-ui-v2-20261104'
FF=R/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
FP=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
ap=argparse.ArgumentParser()
ap.add_argument('--id',required=True)
args=ap.parse_args()
sid=args.id
manifest_path=Q/'encoded'/sid/'encoded_manifest.json'
m=read(manifest_path)
lockfile=D/'shorts'/sid/'locked_timing.json'
lock=read(lockfile)
video=Path(m['video'])
assert video.resolve().is_relative_to((E/'outputs/top20-split-v4/shorts-ui-v2-20261104').resolve())
assert sha(video)==m['video_sha256']
assert sha(lockfile)==m['lock_sha256']
folder=Q/'independent_encoded'/sid
folder.mkdir(parents=True,exist_ok=True)
checks=[]
def check(name,passed,detail=None):
    checks.append(dict(check=name,passed=bool(passed),detail=detail))

probe_result=subprocess.run([str(FP),'-v','error','-show_entries','stream=codec_type,codec_name,width,height,r_frame_rate,nb_frames,sample_rate,channels:format=duration,size','-of','json',str(video)],capture_output=True,check=True)
probe=json.loads(probe_result.stdout)
vs=next(x for x in probe['streams'] if x['codec_type']=='video')
aus=next(x for x in probe['streams'] if x['codec_type']=='audio')
check('final_probe',vs['codec_name']=='h264' and (vs['width'],vs['height'])==(1080,1920) and vs['r_frame_rate']=='30/1' and int(vs['nb_frames'])==lock['total_frames'] and abs(float(probe['format']['duration'])-lock['total_s'])<.04 and aus['codec_name']=='aac' and int(aus['sample_rate'])==48000 and int(aus['channels'])==2)
check('file_size',int(probe['format']['size'])==video.stat().st_size)
decode=subprocess.run([str(FF),'-v','error','-xerror','-i',str(video),'-f','null','-'],capture_output=True)
(folder/'full_decode.stderr.log').write_bytes(decode.stderr)
check('independent_full_decode',decode.returncode==0 and not decode.stderr.strip(),dict(returncode=decode.returncode,stderr_bytes=len(decode.stderr)))
parent_artifacts=[dict(path=x['file'],expected_sha256=x['sha256'],same=sha(x['file'])==x['sha256']) for x in m['frames']]
check('parent_frame_hashes',all(x['same'] for x in parent_artifacts),len(parent_artifacts))

raw=subprocess.run([str(FF),'-v','error','-i',str(video),'-vn','-ar','48000','-ac','2','-f','s16le','-'],capture_output=True,check=True).stdout
decoded=np.frombuffer(raw,dtype='<i2').reshape(-1,2)
with wave.open(lock['master_audio'],'rb') as w:
    master=np.frombuffer(w.readframes(w.getnframes()),'<i2').reshape(-1,2)
audio=[]
for s in lock['sentences']:
    for kind,st,en in [('head',s['start_s']+.03,min(s['end_s'],s['start_s']+.55)),('tail',max(s['start_s'],s['end_s']-.50),s['end_s'])]:
        lo=round(st*48000);hi=round(en*48000)
        x=master[lo:hi].astype(float).ravel();y=decoded[lo:hi].astype(float).ravel()
        corr=float(np.corrcoef(x,y)[0,1]);audio.append(dict(sentence_id=s['sentence_id'],kind=kind,start_s=st,end_s=en,correlation=corr))
check('all_sentence_head_and_tail_master_signal',all(x['correlation']>.97 for x in audio),dict(windows=len(audio),minimum_correlation=min(x['correlation'] for x in audio)))
check('audio_no_pcm_saturation',int(np.abs(decoded.astype('int32')).max())<32767)
frames=[]
anchors=read(H/sid/'price_anchor_audit.json')
scenes={s['scene_id']:s for s in lock['scenes']}
for a in anchors:
    target=a['target_s'];base=math.ceil(target*30-1e-8)
    points=[(base-1,'before'),(base,'first_visible'),(math.ceil((target+.4)*30),'bar_complete')]
    for fr,kind in points:
        dest=folder/f"{a['scene_id']}_row{a['row']}_{kind}.jpg"
        time=fr/30
        subprocess.run([str(FF),'-v','error','-y','-ss',f'{time:.9f}','-i',str(video),'-frames:v','1','-q:v','2',str(dest)],capture_output=True,check=True)
        frames.append(dict(scene_id=a['scene_id'],row=a['row'],kind=kind,time_s=time,frame=fr,target_s=target,value=a['rendered_value'],bar_fraction=a['bar_fraction'],file=str(dest),sha256=sha(dest)))
contacts=[]
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17)
for k in range(0,len(frames),12):
    sheet=Image.new('RGB',(1440,2010),'#e7e9ea');draw=ImageDraw.Draw(sheet)
    for j,f in enumerate(frames[k:k+12]):
        im=Image.open(f['file']);im.thumbnail((360,640));x=j%4*360;y=j//4*670
        sheet.paste(im,(x,y));draw.text((x+3,y+643),f"{f['time_s']:.3f}s row{f['row']} {f['kind']}",font=font,fill='#173348')
    p=folder/f'numeric_contact_{k//12+1:02d}.jpg';sheet.save(p,quality=94);contacts.append(str(p))
check('final_sha_still_same',sha(video)==m['video_sha256'])
result=dict(status='passed_technical_pending_direct_visual_review' if all(x['passed'] for x in checks) else 'requires_correction',short_id=sid,video=str(video),video_sha256=m['video_sha256'],bytes=video.stat().st_size,lock_sha256=sha(lockfile),probe=probe,checks=checks,parent_manifest_sha256=sha(manifest_path),parent_frame_hash_verification=parent_artifacts,audio_windows=audio,numeric_frames=frames,numeric_contacts=contacts,actual_listening=False,continuous_playback=False,note='Signal correlation and decode success do not verify speech perception or continuous playback. Numeric frame creation is not visual approval.')
save(Q/f'{sid}_technical_review.json',result)
print(json.dumps(dict(status=result['status'],short_id=sid,video_sha256=m['video_sha256'],failed=[x['check'] for x in checks if not x['passed']],numeric_frames=len(frames),contacts=contacts)))
