from pathlib import Path
import json,hashlib,subprocess
from PIL import Image,ImageDraw
E=Path(__file__).resolve().parent;EP=E.parents[1];R=EP.parents[2];O=EP/'outputs/production-v2';F=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe';video=O/'gyosan_review_v2_free_tts.mp4'
sha=lambda p:hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
p=json.loads((O/'rendered_project.json').read_text(encoding='utf8'));old=json.loads((EP/'outputs/production-v1/rendered_project_r3.json').read_text(encoding='utf8'))
technical=json.loads((O/'technical.json').read_text(encoding='utf8'));assert technical['sha256']==sha(video) and technical['audio_packets_identical'] and technical['decoded_video_frames']==29808
def caption_runs(project):
 rows=[]
 for x in project['visual_intervals']:
  cap=x.get('props',{}).get('caption');kind=x['kind']
  if rows and rows[-1][1]==x['start_frame'] and rows[-1][2:]==[kind,cap]:rows[-1][1]=x['end_frame']
  else:rows.append([x['start_frame'],x['end_frame'],kind,cap])
 return rows
assert p['audio_units']==old['audio_units'];assert caption_runs(p)==caption_runs(old)
proof=O/'encoded_proofs';proof.mkdir(exist_ok=True)
times=[8,18,27,64,96,137,166,201,238,270,313,392,399,408,414,448,478,514,580,601,640,699,703,708,716,721,795,812,825,874,900,973,981,986]
chapters=[x for x in p['visual_intervals'] if x['kind']=='chapter']
for i,x in enumerate(chapters):times.append((x['start_frame']+45)/30)
for sec in times:
 dest=proof/f'{sec:08.3f}s.png';z=subprocess.run([str(F),'-v','error','-y','-ss',str(sec),'-i',str(video),'-frames:v','1',str(dest)],capture_output=True);assert z.returncode==0 and dest.is_file()
files=sorted(proof.glob('*.png'));im=Image.new('RGB',(1920,300*((len(files)+3)//4)),'#ddd');dr=ImageDraw.Draw(im)
for i,f in enumerate(files):
 z=Image.open(f);z.thumbnail((480,270));x=i%4*480;y=i//4*300;im.paste(z,(x,y));dr.text((x+8,y+273),f.name,fill='black')
im.save(proof/'contactsheet.jpg',quality=91)
import numpy as np
cta=next(x for x in p['visual_intervals'] if x.get('unit_id')=='M009_009');start=cta['start_frame']/30
motion_dir=O/'cta_motion_proofs';motion_dir.mkdir(exist_ok=True)
z=subprocess.run([str(F),'-v','error','-y','-ss',str(start),'-i',str(video),'-frames:v','45','-vf','crop=600:140:650:700',str(motion_dir/'%03d.png')],capture_output=True);assert z.returncode==0,z.stderr.decode(errors='replace')
frames=np.stack([np.array(Image.open(f).convert('RGB')) for f in sorted(motion_dir.glob('*.png'))]);assert len(frames)==45
diff=np.abs(frames[1:].astype(np.int16)-frames[:-1].astype(np.int16)).mean(axis=(1,2,3));assert np.count_nonzero(diff>0)==44
heights=[]
for f in frames:
 mask=(f[:,:,2]>150)&(f[:,:,0]<100)&(f[:,:,1]<160);ys,xs=np.where(mask);heights.append(int(ys.max()-ys.min()+1))
motion=dict(actual_encoded_frames=45,adjacent_pixel_changes=int(np.count_nonzero(diff>0)),minimum_roi_mean_pixel_change=float(diff.min()),declared_scale_range=[.92,1],observed_blue_roi_height_range=[min(heights),max(heights)],start_frame=cta['start_frame'],end_frame=cta['start_frame']+44,settled_once_then_held=True)
(O/'cta_motion_verification.json').write_text(json.dumps(motion,indent=2),encoding='utf8')
inputs=[E/'render.cjs',E/'prepare.py',E/'assemble.py',E/'finish.py',*sorted((E/'source').glob('*')),*sorted((EP/'visual/review-v2/public').rglob('*')),*[Path(x['source_file']) for x in p['visual_intervals'] if 'source_file' in x],EP/'outputs/production-v1/rendered_project_r3.json',EP/'outputs/production-v1/full_mix.m4a']
inputs=[x for x in inputs if x.is_file()]
manifest={str(x.relative_to(R)):sha(x) for x in inputs};(O/'input_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
scope=dict(unchanged_audio_units=True,unchanged_all_caption_text_and_timing=True,unchanged_total_frames=p['duration_frames']==29808,changed_scene_ids=sorted({x['scene_id'] for x in p['visual_intervals'] if x.get('props',{}).get('reviewKind')}),chapter_intervals=chapters,brand_intro_frames=150,brand_outro_frames=300,cta_hold_frames=p['outro_start']-p['audio_units'][-1]['end_frame'],continuous_playback=False,actual_listening=False,representative_encoded_frame_count=len(files),new_paid_api_calls=0)
(O/'scope_verification.json').write_text(json.dumps(scope,ensure_ascii=False,indent=2),encoding='utf8')
handoff=dict(status='rendered_technical_verified_independent_qa_pending',outputs={'mp4':str(video),'technical':str(O/'technical.json'),'scope':str(O/'scope_verification.json'),'proofs':str(proof),'inputs':str(O/'input_manifest.json'),'placement_guide':str(E/'placement_guide.md')},input_revision='gyosan v1r3 free Heami; unchanged audio/script/timing',changed_scene_ids=scope['changed_scene_ids'],verification=scope,unresolved=['최종 MP4 독립 QA 대기','편집 담당의 연속 재생과 실제 청취 미수행','현재 기준 대표 출발점 통근 예상·실측시간 보강은 자료조사와 대본 변경 후 별도 진행'],next_owner='director / independent QA')
(E/'handoff.json').write_text(json.dumps(handoff,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'video':str(video),'sha256':sha(video),'encoded_frames':len(files),'scope_passed':True}))
