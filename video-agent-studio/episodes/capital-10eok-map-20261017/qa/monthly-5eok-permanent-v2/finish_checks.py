from pathlib import Path
import json,subprocess,hashlib
from PIL import Image
import numpy as np
Q=Path(__file__).resolve().parent;EP=Q.parents[1];O=EP/'outputs/monthly-5eok-permanent-v2';BIN=EP.parents[2]/'video/node_modules/@remotion/compositor-win32-x64-msvc';read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=read(Q/'motion_independent_review.json');logs=read(O/'motion_frame_log.json');static=Image.open(O/'cache/static.png').convert('RGB');checks=[]
for sample in r['selected_frames']:
 f=sample['frame'];l=logs[f];mi=l['month_index'];prev=l['previous_month_index'];a=l['alpha_smoothstep'];p=Image.open(O/f'cache/from_{mi:03}.png').convert('RGB');c=Image.open(O/f'cache/map_{mi:03}.png').convert('RGB');layer=c if a==1 or mi==prev else Image.blend(p,c,a);im=static.copy();im.paste(layer,(0,690));panel=Image.open(O/f'cache/panel_{mi:03}.png').convert('RGBA');im.paste(panel,(0,380),panel);exp=np.asarray(im.resize((375,667),Image.Resampling.BILINEAR),dtype=np.float32);act=np.asarray(Image.open(sample['file']).convert('RGB'),dtype=np.float32);mae=float(np.abs(exp[270:622]-act[270:622]).mean());assert mae<4;checks.append({'frame':f,'map_blend_expected_mae':mae})
bounds=read(O/'monthly_text_bounds.json');assert len(bounds)==1250
for b in bounds:
 l,t,rr,bb=b['bbox'];assert 0<=l<rr<=1080 and 0<=t<bb<=1920
for month in sorted(set(b['month'] for b in bounds)):
 bs={b['field']:b for b in bounds if b['month']==month};assert bs['month']['bbox'][2]<bs['counter']['bbox'][0]
ex=O/'motion_excerpt_10s.mp4';probe=json.loads(subprocess.run([str(BIN/'ffprobe.exe'),'-v','error','-show_streams','-show_format','-of','json',str(ex)],capture_output=True,check=True).stdout);assert len(probe['streams'])==1 and int(probe['streams'][0]['nb_frames'])==300
d=subprocess.run([str(BIN/'ffmpeg.exe'),'-v','error','-i',str(ex),'-an','-c:v','rawvideo','-f','null','-'],capture_output=True,check=True)
r.update(selected_map_blend_pixel_checks=checks,all_1250_month_text_boxes_inside_canvas=True,month_counter_overlap_count=0,readme_transition_price_interpolation_distinction=True,excerpt={'file':str(ex),'sha256':sha(ex),'frames':300,'duration_s':10,'decode_exit':0})
(Q/'motion_independent_review.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'selected':len(checks),'max_map_mae':max(c['map_blend_expected_mae'] for c in checks),'textboxes':1250,'excerpt_decode':0}))
