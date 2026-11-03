"""Full final AV decode, audio signal, pinned encoded-frame packet and QA-only sheets."""
import sys,json,hashlib,subprocess,re,wave
from pathlib import Path
from datetime import datetime,timezone
sys.dont_write_bytecode=True
Q=Path(__file__).resolve().parent;E=Q.parent.parent;R=E.parents[2];O=E/'outputs/jun-production-v1'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 d=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(4*1024*1024),b''):d.update(c)
 return d.hexdigest()
def pin(p):return dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size)
def dump(n,d):(Q/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 receipt=read(E/'editor/jun-production-v1/render_receipt.json');packetp=O/'encoded_frame_plan.json';packet=read(packetp);source=read(Q/'source_release_review.json');edl=read(O/'assembly_edl.json')
 video=Path(receipt['final_file']);assert video.is_file() and sha(video)==receipt['final_sha256']==packet['final_sha256']
 assert packet['status']=='encoded_frames_extracted_review_pending' and packet['EDL_sha256']==source['EDL']['sha256']==sha(O/'assembly_edl.json')
 for d in source['source_inputs']:
  for k in ['HTML','timing']:assert sha(Path(d[k]['path']))==d[k]['sha256']
 fft=E/'outputs/private-production-v1/media-bin/ffmpeg.exe';ffp=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe';D=Q/('encoded-'+sha(video)[:12]);D.mkdir(exist_ok=True)
 probe=json.loads(subprocess.run([str(ffp),'-v','error','-show_streams','-show_format','-of','json',str(video)],capture_output=True,check=True,text=True).stdout)
 vp=next(x for x in probe['streams'] if x['codec_type']=='video');ap=next(x for x in probe['streams'] if x['codec_type']=='audio');assert (vp['codec_name'],vp['width'],vp['height'],vp['r_frame_rate'],vp['pix_fmt'])==('h264',1920,1080,'30/1','yuv420p');assert ap['codec_name']=='aac' and ap['sample_rate']=='48000' and ap['channels']==2
 assert abs(float(probe['format']['duration'])-edl['total_seconds'])<.05
 decodeargv=[str(fft),'-nostdin','-hide_banner','-v','error','-threads','2','-i',str(video),'-map','0:v:0','-map','0:a:0','-f','null','NUL'];decodelog=D/'full_AV_decode.log'
 with decodelog.open('w',encoding='utf-8') as f:decode=subprocess.run(decodeargv,stdout=f,stderr=subprocess.STDOUT)
 assert decode.returncode==0 and not decodelog.read_text(encoding='utf-8').strip(),'Full AV decode failed; keep log'
 signalargv=[str(fft),'-nostdin','-hide_banner','-i',str(video),'-map','0:a:0','-vn','-af','volumedetect,ebur128=peak=true','-f','null','NUL'];signallog=D/'full_audio_signal.log'
 with signallog.open('w',encoding='utf-8') as f:signal=subprocess.run(signalargv,stdout=f,stderr=subprocess.STDOUT)
 assert signal.returncode==0
 log=signallog.read_text(encoding='utf-8');last=log[log.rfind('Summary:'):];last=last[:1800]
 from PIL import Image,ImageDraw,ImageFont,ImageChops
 samples=[]
 for row in packet['samples']:
  p=O/row['file'];assert sha(p)==row['sha256'];im=Image.open(p);assert im.size==(1920,1080)
  samples.append({**row,'absolute_file':str(p)})
 # Re-decode three independently chosen producer frame timestamps and compare pixels.
 reps=[r for r in samples if r['role']=='representative'];verified=[]
 for row in [reps[0],reps[len(reps)//2],reps[-1]]:
  dest=D/f'reextract-{row["global_frame"]:06d}.png';argv=[str(fft),'-v','error','-nostdin','-ss',f'{row["global_frame"]*1000000//30/1000000:.6f}','-i',str(video),'-frames:v','1','-an','-n',str(dest)]
  if not dest.exists():subprocess.run(argv,check=True,capture_output=True)
  with Image.open(dest) as ours,Image.open(row['absolute_file']) as theirs:assert ImageChops.difference(ours.convert('RGB'),theirs.convert('RGB')).getbbox() is None
  verified.append(dict(global_frame=row['global_frame'],independent_frame=pin(dest),producer_frame=pin(Path(row['absolute_file'])),decoded_pixels_equal=True))
 maxrows=[]
 for i,row in enumerate(source['maximum_scale_samples_to_inspect']):
  dest=D/f'maxscale-{i+1:02d}.png';argv=[str(fft),'-v','error','-nostdin','-ss',f'{row["global_frame"]*1000000//30/1000000:.6f}','-i',str(video),'-frames:v','1','-an','-n',str(dest)]
  if not dest.exists():subprocess.run(argv,check=True,capture_output=True)
  maxrows.append({**row,'scene_id':f'max_scale_ch{row["chapter"]:02d}','role':'maximum_scale','absolute_file':str(dest),'sha256':sha(dest)})
 sheets=[];font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17)
 groups=[('representatives',reps),('scene_boundaries',[r for r in samples if r['role'].startswith('boundary_')]),('joins',[r for r in samples if r['role'].startswith('join_')]),('longest_captions',[r for r in samples if r['role']=='longest_caption']),('end_tail',[r for r in samples if r['scene_id']=='final_CTA_hold']),('maximum_scales',maxrows)]
 for category,group in groups:
  for start in range(0,len(group),8):
   page=group[start:start+8];sheet=Image.new('RGB',(1280,4*386),'#eeeeee');draw=ImageDraw.Draw(sheet)
   for i,row in enumerate(page):
    x=i%2*640;y=i//2*386
    with Image.open(row['absolute_file']) as im:sheet.paste(im.convert('RGB').resize((640,360),Image.Resampling.LANCZOS),(x,y))
    draw.text((x+8,y+362),f'{row["scene_id"]} {row["role"]} {row["global_time_s"]:.3f}s',font=font,fill='#001122')
   dest=D/f'{category}-{start//8+1:02d}.jpg';sheet.save(dest,quality=94);sheets.append(dict(category=category,file=pin(dest),frames=[r['global_frame'] for r in page]))
 guidep=E/'editor/jun-production-v1/placement_guide.md';guide_refs=[]
 if guidep.exists():
  guide=guidep.read_text(encoding='utf-8')
  for name in re.findall(r'`([^`]+\.(?:json|txt|mp4|srt))`',guide):
   candidates=[E/name,O/name,R/name];f=next((x for x in candidates if x.exists()),None);guide_refs.append(dict(reference=name,resolved=pin(f) if f else None))
 expected=[video,O/'captions_measured.srt',E/'outputs/jun-release-v1/metadata_measured.json',E/'outputs/jun-release-v1/description_measured.md',E/'outputs/jun-release-v1/thumbnail.png',guidep]
 technical=dict(status='pass_technical_only_visual_review_pending',video=pin(video),full_AV_decode=dict(returncode=decode.returncode,log=pin(decodelog),argv=decodeargv,all_video_and_audio_streams_decoded=True),signal=dict(returncode=signal.returncode,log=pin(signallog),argv=signalargv,EBU_summary=last,mean_volume=re.findall(r'mean_volume:\s*([^\n]+)',log),max_volume=re.findall(r'max_volume:\s*([^\n]+)',log)),ffmpeg=pin(fft),ffprobe=pin(ffp),probe=probe,frame_packet=pin(packetp),producer_frames_verified=len({r['global_frame'] for r in samples}),independent_pixel_redecodes=verified,maximum_scale_frames=maxrows,contact_sheets=sheets,all_encoded_samples=samples,expected_delivery_files=[dict(path=str(p),exists=p.exists(),bytes=p.stat().st_size if p.exists() else 0) for p in expected],placement_guide=pin(guidep) if guidep.exists() else None,guide_reference_files=guide_refs,ZIP_integrity='not_applicable_no_ZIP_requested_or_supplied',actual_listening=False,continuous_playback=False,all_images_actually_viewed=False,checked_at=datetime.now(timezone.utc).isoformat())
 dump('final_technical_checks.json',technical);print(json.dumps(dict(status=technical['status'],video=technical['video'],signal_summary=last,sheets=len(sheets),frames=technical['producer_frames_verified'],new_maxscale_frames=len(maxrows)),ensure_ascii=False))
if __name__=='__main__':main()
