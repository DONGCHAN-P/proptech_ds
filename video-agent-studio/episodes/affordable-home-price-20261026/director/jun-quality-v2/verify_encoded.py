"""Whole-file decode/PTS/audio equality and real encoded sample extraction, not listening."""
from pathlib import Path
from collections import defaultdict
from PIL import Image,ImageDraw,ImageChops,ImageStat
import subprocess,json,hashlib,math
EP=Path(__file__).resolve().parents[2];ROOT=EP.parents[2]
F=EP/'editor/jun-quality-v2/main';OUT=EP/'outputs/jun-quality-v2/main'
OWN=Path(__file__).parent/'encoded_checks';OWN.mkdir(parents=True,exist_ok=True)
FF=ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
FP=ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
VIDEO=OUT/'affordable_home_price_jun_quality_v3.mp4'
OLD=EP/'outputs/jun-user-script-v1/full-film-v1/affordable_price_jun_user_script_v2.mp4'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()
def run(args):
    r=subprocess.run([str(x) for x in args],capture_output=True)
    if r.returncode:raise RuntimeError(r.stderr.decode('utf-8','replace')[-3000:])
    return r
sch=read(F/'schedule.json');caps=read(F/'full_caption_timing.json')
oldsch=read(EP/'editor/jun-user-script-v1/full-film-v1/schedule.json')
assert sch==oldsch,'Audio/scene clocks must remain frozen'
assert sha(F/'project/assets/mix.m4a')==sha(EP/'editor/jun-user-script-v1/full-film-v1/project/assets/mix.m4a')
assert sha(OUT/'subtitles.srt')==sha(EP/'outputs/jun-user-script-v1/full-film-v1/subtitles.srt')
meta=json.loads(run([FP,'-v','error','-show_streams','-show_format','-of','json',VIDEO]).stdout)
groups=defaultdict(set)
def add(n,label):
    if 0<=n<sch['frames']:groups[n].add(label)
for p in sch['placements']:
    for delta,tag in [(-1,'before'),(0,'first'),(1,'next')]:add(p['frame']+delta,p['id']+'_'+tag)
    if p['kind']=='scene':
        for offset,tag in [(min(21,p['frames']-1),'resident'),(p['frames']//2,'middle'),(p['frames']-1,'end')]:add(p['frame']+offset,p['id']+'_'+tag)
    elif p['kind']=='chapter':add(p['frame']+p['frames']//2,p['id']+'_middle')
for c in caps['cues']:
    add(min(round((c['global_start']+c['global_end'])*15),math.ceil(c['global_end']*30)-1),'cue_'+c['cue_id'])
for sid,offsets in [('S14',[1.5,6,7.5]),('S21',[25.5,25.65,26.5]),('S31',[.7,28])]:
    p=next(x for x in sch['placements'] if x['id']==sid)
    for t in offsets:
        if t<p['duration']:add(round((p['start']+t)*30),sid+'_special')
for n in [21053,21054,21060,21062,21143,21144,21443]:add(n,'ending')
indices=sorted(groups);dest=OWN/'frames';dest.mkdir(exist_ok=True)
select='select='+'+'.join(f'eq(n\\,{n})' for n in indices)
r=run([FF,'-v','error','-y','-i',VIDEO,'-map','0:v:0','-vf',select,'-fps_mode','vfr','-q:v','2',dest/'frame-%04d.jpg','-map','0:a:0','-f','null','-'])
(OWN/'decode.log').write_bytes(r.stderr)
paths=sorted(dest.glob('frame-*.jpg'));assert len(paths)==len(indices)
frames=[];by_index={}
for n,p in zip(indices,paths):
    with Image.open(p) as im:assert im.size==(1920,1080)
    row={'frame_index':n,'time_s':n/30,'labels':sorted(groups[n]),'path':rel(p)}
    frames.append(row);by_index[n]=row
pts=json.loads(run([FP,'-v','error','-select_streams','v:0','-show_frames','-show_entries','frame=best_effort_timestamp_time','-of','json',VIDEO]).stdout)
times=[float(x['best_effort_timestamp_time']) for x in pts['frames']]
assert len(times)==21444 and all(abs(t-i/30)<1.1e-6 for i,t in enumerate(times))
audio=[]
for p in [OLD,VIDEO]:
    stream=run([FF,'-v','error','-i',p,'-map','0:a:0','-c:a','copy','-f','adts','pipe:1']).stdout
    pcm=run([FF,'-v','error','-i',p,'-map','0:a:0','-f','s16le','-ar','48000','-ac','2','pipe:1']).stdout
    audio.append({'path':rel(p),'AAC_sha256':hashlib.sha256(stream).hexdigest(),'PCM_sha256':hashlib.sha256(pcm).hexdigest(),'PCM_samples_per_channel':len(pcm)//4})
audio_equal=audio[0]['PCM_sha256']==audio[1]['PCM_sha256']
assert audio_equal,'Changed audio detected; investigate before delivery'
def sheet(rows,name,cols=3):
    canvas=Image.new('RGB',(1920,math.ceil(len(rows)/cols)*384),'#e4e4e4');d=ImageDraw.Draw(canvas)
    for i,row in enumerate(rows):
        x=(i%cols)*640;y=(i//cols)*384
        with Image.open(ROOT/row['path']) as im:canvas.paste(im.resize((640,360),Image.Resampling.LANCZOS),(x,y+24))
        d.text((x+5,y+4),row['label']+' '+f'{row["time_s"]:.3f}s',fill='black')
    canvas.save(OWN/name,quality=94)
for typ in ['resident','middle','end']:
    rows=[]
    for p in sch['placements']:
        if p['kind']!='scene':continue
        row=next(x for x in frames if p['id']+'_'+typ in x['labels']);rows.append({**row,'label':p['id']+'_'+typ})
    for part in range(3):sheet(rows[part*11:(part+1)*11],f'encoded_{typ}_{part+1}.jpg')
special=[{**x,'label':','.join(x['labels'])[:55]} for x in frames if any('special' in k or k=='ending' for k in x['labels'])]
sheet(special,'encoded_specials.jpg')
source=read(EP/'qa/jun-user-script-v1/full-film-v1/DOM_evidence.json')
caps_comparison=[]
for i,c in enumerate(caps['cues']):
    n=min(round((c['global_start']+c['global_end'])*15),math.ceil(c['global_end']*30)-1)
    with Image.open(ROOT/by_index[n]['path']) as im:actual=im.convert('RGB').crop((96,876,1824,1000))
    with Image.open(ROOT/source['captions'][i]['frame']) as im:expected=im.convert('RGB')
    mae=sum(ImageStat.Stat(ImageChops.difference(actual,expected)).mean)/3
    caps_comparison.append({'cue_id':c['cue_id'],'mean_RGB_error':mae,'matches':mae<5})
assert all(x['matches'] for x in caps_comparison),'Caption raster differs from locked timing/layout'
report={'video':rel(VIDEO),'sha256':sha(VIDEO),'bytes':VIDEO.stat().st_size,'duration_s':float(meta['format']['duration']),
 'metadata':meta,'whole_AV_decode_pass':True,'PTS_frames':len(times),'PTS_match_index_over_30':True,
 'audio_comparison':audio,'audio_PCM_identical_to_approved_baseline':audio_equal,'AAC_identical':audio[0]['AAC_sha256']==audio[1]['AAC_sha256'],
 'unchanged_scene_schedule':True,'unchanged_SRT':True,'caption_samples':len(caps_comparison),'caption_comparisons':caps_comparison,
 'frames':frames,'sample_count':len(frames),'actual_listening':False,'continuous_playback':False,'visual_inspection':'separate reviewer must view extracted sheets'}
(OWN/'technical_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ['metadata','caption_comparisons','frames','audio_comparison']},ensure_ascii=False))
