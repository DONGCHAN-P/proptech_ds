"""실제 v2 MP4 전량 기술 디코드·PTS·오디오 복사·표본 추출. 청취/재생 아님."""
from pathlib import Path
from collections import defaultdict
from PIL import Image,ImageChops,ImageStat
from datetime import datetime,timezone
import json,hashlib,subprocess,math
OWN=Path(__file__).resolve().parent;EP=OWN.parents[2];ROOT=EP.parents[2]
F=EP/'editor/jun-user-script-v1/full-film-v1';OUT=EP/'outputs/jun-user-script-v1/full-film-v1'
FF=ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
FP=ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
v1=OUT/'affordable_price_jun_user_script_v1.mp4';v2=OUT/'affordable_price_jun_user_script_v2.mp4'
read=lambda p:json.loads(p.read_text('utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
fix=read(F/'ending_fix_receipt.json');sch=read(F/'schedule.json');caps=read(F/'full_caption_timing.json');source=read(OWN/'DOM_evidence.json')
h1,h2=sha(v1),sha(v2);assert h1==fix['source_sha256'] and h2==fix['output_sha256']
dest=OWN/('encoded-v2-'+h2[:12]);dest.mkdir(exist_ok=True)
groups=defaultdict(set)
def add(frame,label):
 if 0<=frame<sch['frames']:groups[frame].add(label)
for p in sch['placements']:
 for delta,label in [(-1,'before'),(0,'first'),(1,'next')]:add(p['frame']+delta,'boundary_'+p['id']+'_'+label)
 if p['kind'] in ['scene','chapter']:add(p['frame']+p['frames']-1,p['kind']+'_final_'+p['id'])
for c in caps['cues']:add(min(round((c['global_start']+c['global_end'])*15),math.ceil(c['global_end']*30)-1),'caption_'+c['cue_id'])
for frame in [21053,21054,21060,21062,21143,21144,21443]:add(frame,'critical_ending')
indices=sorted(groups)
probe=subprocess.run([str(FP),'-v','error','-show_streams','-show_format','-of','json',str(v2)],capture_output=True,text=True,encoding='utf-8');assert probe.returncode==0,probe.stderr
metadata=json.loads(probe.stdout)
print('METADATA_VERIFIED; extracting',len(indices),'actual frames with complete AV decode',flush=True)
select='select='+'+'.join(f'eq(n\\,{n})' for n in indices)
args=[str(FF),'-v','error','-y','-i',str(v2),'-map','0:v:0','-vf',select,'-fps_mode','vfr','-compression_level','3',str(dest/'frame-%04d.png'),'-map','0:a:0','-f','null','-']
r=subprocess.run(args,capture_output=True,text=True,encoding='utf-8');(OWN/'encoded_decode_extract.stderr.log').write_text(r.stderr,encoding='utf-8');assert r.returncode==0,r.stderr
paths=sorted(dest.glob('frame-*.png'));assert len(paths)==len(indices),(len(paths),len(indices))
frames=[];by_index={}
for n,p in zip(indices,paths):
 with Image.open(p) as im:assert im.size==(1920,1080)
 x={'frame_index':n,'time_s':n/30,'labels':sorted(groups[n]),'path':rel(p),'sha256':sha(p)};frames.append(x);by_index[n]=x
print('DECODE_DONE; verifying all presentation timestamps and AAC payload',flush=True)
pts=subprocess.run([str(FP),'-v','error','-select_streams','v:0','-show_frames','-show_entries','frame=best_effort_timestamp_time','-of','json',str(v2)],capture_output=True,text=True,encoding='utf-8');assert pts.returncode==0,pts.stderr
times=[float(x['best_effort_timestamp_time']) for x in json.loads(pts.stdout)['frames']]
assert len(times)==sch['frames']==21444 and all(abs(t-i/30)<1.1e-6 for i,t in enumerate(times))
audio=[]
for p in [v1,v2]:
 z=subprocess.run([str(FF),'-v','error','-i',str(p),'-map','0:a:0','-c:a','copy','-f','adts','pipe:1'],capture_output=True)
 assert z.returncode==0,z.stderr.decode('utf-8','replace')
 audio.append({'file':rel(p),'ADTS_AAC_bytes':len(z.stdout),'ADTS_AAC_sha256':hashlib.sha256(z.stdout).hexdigest()})
assert audio[0]['ADTS_AAC_sha256']==audio[1]['ADTS_AAC_sha256']
comparisons=[]
for i,c in enumerate(caps['cues']):
 frame=min(round((c['global_start']+c['global_end'])*15),math.ceil(c['global_end']*30)-1);p=ROOT/by_index[frame]['path'];orig=ROOT/source['captions'][i]['frame']
 with Image.open(p) as im:encoded=im.convert('RGB').crop((96,876,1824,1000))
 with Image.open(orig) as im:expected=im.convert('RGB')
 stat=ImageStat.Stat(ImageChops.difference(encoded,expected));mae=sum(stat.mean)/3
 comparisons.append({'cue_id':c['cue_id'],'frame_index':frame,'source_time_s':source['captions'][i]['time'],'actual_time_s':frame/30,'caption_ROI_mean_absolute_RGB_error':mae,'low_error_supports_source_match':mae<4})
 # 실제 인코딩 자막 ROI를 별도 보존한다.
 roi=dest/f'caption-{i+1:03}-{c["cue_id"]}.png';encoded.save(roi)
ending=[]
for n in [21053,21054,21060,21062,21143,21144]:
 p=ROOT/by_index[n]['path']
 with Image.open(p) as im:
  im=im.convert('RGB');band=im.crop((96,876,1824,1000));dark=sum(1 for rr,gg,bb in band.getdata() if min(rr,gg,bb)<160)
  expected=Image.new('RGB',band.size,(246,244,239));mae=sum(ImageStat.Stat(ImageChops.difference(band,expected)).mean)/3
 ending.append({'frame_index':n,'time_s':n/30,'path':rel(p),'caption_band_dark_pixels':dark,'ivory_band_RGB_MAE':mae,'inside_corrected_interval':21054<=n<21144})
assert all(x['caption_band_dark_pixels']==0 and x['ivory_band_RGB_MAE']<3 for x in ending if x['inside_corrected_interval'])
assert sha(v2)==h2
report={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'scope':'실제 MP4 v2 독립 디코드·샘플 프레임·PTS·AAC 복사 확인. 청취/연속 재생 아님.','v1':{'path':rel(v1),'sha256':h1,'bytes':v1.stat().st_size},'v2':{'path':rel(v2),'sha256':h2,'bytes':v2.stat().st_size},'ending_fix_receipt':{'path':rel(F/'ending_fix_receipt.json'),'sha256':sha(F/'ending_fix_receipt.json')},'metadata':metadata,'full_AV_decode_exit':r.returncode,'PTS':{'frame_count':len(times),'expected_fps':30,'all_frame_timestamps_equal_index_over_fps':True,'max_error_s':max(abs(t-i/30) for i,t in enumerate(times))},'audio_elementary_stream_comparison':{'method':'별도 로컬 FFmpeg -c:a copy -f adts pipe 추출 후 바이트 SHA 비교. 청취 아님.','streams':audio,'identical':True},'frames':frames,'caption_ROI_comparisons':comparisons,'ending':ending,'file_stable_after_checks':True,'actual_listening':False,'continuous_playback':False,'paid_calls':0,'external_transmissions':0}
(OWN/'encoded_evidence.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'actual_sampled_frames':len(frames),'PTS_frames':len(times),'AAC_identical':True,'caption_ROI_MAE_max':max(x['caption_ROI_mean_absolute_RGB_error'] for x in comparisons),'caption_ROI_high_error':[x for x in comparisons if not x['low_error_supports_source_match']],'ending':ending,'sha256':h2},ensure_ascii=False))
