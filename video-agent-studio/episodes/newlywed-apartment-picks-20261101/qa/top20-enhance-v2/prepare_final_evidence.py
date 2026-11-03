import hashlib,json,math,subprocess,time
from pathlib import Path
from PIL import Image,ImageDraw

ROOT=Path('C:/projects/realestate_reco');EP=ROOT/'video-agent-studio/episodes/newlywed-apartment-picks-20261101'
Q=EP/'qa/top20-enhance-v2';D=Q/'final-evidence';D.mkdir(exist_ok=True)
ED=EP/'editor/top20-enhance-v2';VIDEO=EP/'outputs/top20-enhance-v2/main/top20_main_enhanced_v1.mp4'
FF=ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe';FP=FF.with_name('ffprobe.exe')
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,obj):(Q/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
expected='12b2221c246c1a10fb6e2c92750fbb4ca4d40b2195b721bef0afa2ee56bf28f5'
actual=sha(VIDEO);assert actual==expected
r=read(ED/'render_receipt_main_v1.json');assert r['output_sha256']==actual
freeze=read(ED/'source_freeze.json');assert freeze['project_sha256']==r['project_sha256']
t=read(EP/'director/top20-enhance-v2/locked_timing.json')
frames=read(ED/'evidence/encoded-main-v1/frames.json')
for i,f in enumerate(frames):
 assert sha(f['file'])==f['sha256']
 f['manifest_index']=i
 assert Image.open(f['file']).size==(1920,1080)
def scene_at(sec):
 for s in t['scenes']:
  if s['start_s']<=sec<s['end_s']:return s['scene_id']
 for k in ['brand_intro','brand_outro']:
  if t[k]['start_s']<=sec<t[k]['end_s']:return k
 return 'outside'
for f in frames:f['expected_scene_at_request']=scene_at(f['time_s'])

def sheets(rows,prefix):
 out=[]
 for start in range(0,len(rows),9):
  sheet=Image.new('RGB',(1920,1152),'#ffffff');draw=ImageDraw.Draw(sheet)
  for slot,f in enumerate(rows[start:start+9]):
   x=(slot%3)*640;y=(slot//3)*384
   im=Image.open(f['file']).convert('RGB');im.thumbnail((640,360));sheet.paste(im,(x,y+24))
   draw.text((x+6,y+6),f"{f.get('manifest_index',start+slot):03d}  {f['time_s']:.6f}s  {f.get('expected_scene_at_request',f.get('scene_id',''))}",fill='black')
  p=D/f'{prefix}-{start//9+1:02d}.jpg';sheet.save(p,quality=94);out.append(str(p))
 return out
existing_sheets=sheets(frames,'encoded125')

cues=read(ED/'main/caption_mapping.json')['cues'];longest=[]
for sc in t['scenes']:
 cs=[(i,c) for i,c in enumerate(cues) if c['scene_id']==sc['scene_id']]
 if cs:
  i,c=max(cs,key=lambda x:len(x[1]['text']));longest.append((i,c))
extra=[]
log=D/'additional_extract.stderr.log'
with log.open('wb') as err:
 for n,(i,c) in enumerate(longest):
  sec=(c['start_s']+c['end_s'])/2
  p=D/f'long-{n:02d}-{c["scene_id"]}-{sec:.6f}s.jpg'
  cmd=[str(FF),'-v','error','-ss',str(sec),'-i',str(VIDEO),'-frames:v','1','-y',str(p)]
  cp=subprocess.run(cmd,stdout=subprocess.DEVNULL,stderr=err)
  assert cp.returncode==0 and p.exists()
  extra.append(dict(time_s=sec,scene_id=c['scene_id'],file=str(p),sha256=sha(p),cue_index=i,text=c['text'],
                    expected_scene_at_request=c['scene_id'],reason='scene_longest_caption'))
extra_sheets=sheets(extra,'longest28')
probe=json.loads(subprocess.run([str(FP),'-v','error','-show_entries','format=duration,size:stream=index,codec_name,codec_type,width,height,r_frame_rate,avg_frame_rate,sample_rate,channels,duration,nb_frames,time_base,start_time','-of','json',str(VIDEO)],capture_output=True,check=True).stdout)

# 모든 실제 컷의 직전/첫/다음 30fps 프레임이 표본에 포함되는지 점검한다.
boundaries=sorted(set([0]+[s['start_s'] for s in t['scenes']]+[t[k]['start_s'] for k in ['brand_intro','brand_outro']]))
frame_numbers={math.ceil(f['time_s']*30-1e-6):f['manifest_index'] for f in frames}
coverage=[]
for sec in boundaries:
 cut=math.ceil(sec*30-1e-6);want=[max(0,cut-1),cut,cut+1]
 hits={str(n):frame_numbers.get(n) for n in want}
 coverage.append(dict(source_cut_s=sec,first_frame_index=cut,requested_frame_indices=want,evidence_manifest_indices=hits,
                      all_three_present=all(v is not None for v in hits.values())))
zooms=[]
for p in sorted((ED/'main/scenes').glob('*.html')):
 text=p.read_text(encoding='utf-8-sig')
 if 'scale' in text or 'zoom' in text:
  import re
  zooms.append(dict(scene=p.stem,expressions=re.findall(r'.{0,90}(?:scale|zoom).{0,150}',text)[:12]))
save('final_evidence_manifest.json',dict(video=str(VIDEO),video_sha256=actual,probe=probe,
 project_sha256=r['project_sha256'],render_receipt_sha256=sha(ED/'render_receipt_main_v1.json'),
 source_frame_manifest_sha256=sha(ED/'evidence/encoded-main-v1/frames.json'),
 existing_frames=frames,extra_long_caption_frames=extra,sheets=existing_sheets+extra_sheets,
 boundary_coverage=coverage,scene_ids=[s['scene_id'] for s in t['scenes']],zoom_source_expressions=zooms,
 visual_inspection_status='pending_contact_sheets_and_detail'))
print(json.dumps(dict(existing_frames=len(frames),extra_frames=len(extra),sheet_count=len(existing_sheets+extra_sheets),
 boundary_count=len(coverage),missing_boundary_triplets=[b for b in coverage if not b['all_three_present']],
 manifest=str(Q/'final_evidence_manifest.json')),ensure_ascii=False),flush=True)
FULL_FF=ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
start=time.time();cmd=[str(FULL_FF),'-v','error','-xerror','-i',str(VIDEO),'-map','0:v:0','-map','0:a:0','-f','null','-']
with (D/'independent-full-decode-fullbin.stdout.log').open('wb') as out,(D/'independent-full-decode-fullbin.stderr.log').open('wb') as err:
 cp=subprocess.run(cmd,stdout=out,stderr=err)
save('independent_full_decode.json',dict(video_sha256=actual,command=cmd,exit_code=cp.returncode,
 passed=cp.returncode==0,elapsed_s=round(time.time()-start,3),scope='전체 비디오15850프레임 및 전체 오디오 스트림 디코드;실제 청취/연속 재생 아님',
 stderr_path=str(D/'independent-full-decode-fullbin.stderr.log'),stderr_bytes=(D/'independent-full-decode-fullbin.stderr.log').stat().st_size))
assert cp.returncode==0
print('independent full decode passed',flush=True)
