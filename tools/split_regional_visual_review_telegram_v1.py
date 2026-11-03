"""Make smaller lossless parts after the single-file upload timed out."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
EP=ROOT/'video-agent-studio/episodes/regional-price-recovery-20261022'
OUT=EP/'outputs/production-v1-jun';D=EP/'director/production-v1/delivery'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assets=read(OUT/'reusable_assets/manifest.json');copy=read(D/'telegram_copy_manifest.json')
source=ROOT/copy['path'];assert sha(source)==copy['sha256']
dest=D/'telegram_parts_v1';dest.mkdir(exist_ok=True)
assert not list(dest.glob('part_*.mp4')),'Preserve existing split files'
cmd=[assets['ffmpeg'],'-hide_banner','-y','-i',str(source),'-map','0','-c','copy','-f','segment','-segment_time','225','-reset_timestamps','1','-segment_format_options','movflags=+faststart',str(dest/'part_%02d.mp4')]
proc=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8',errors='replace')
(dest/'split.log').write_text(proc.stderr,encoding='utf8');assert proc.returncode==0
parts=[];frame=0
for p in sorted(dest.glob('part_*.mp4')):
    info=json.loads(subprocess.check_output([assets['ffprobe'],'-v','error','-show_streams','-show_format','-of','json',str(p)],text=True,encoding='utf8'))
    v=next(s for s in info['streams']if s['codec_type']=='video');n=int(v['nb_frames'])
    assert v['width']==1280 and v['height']==720 and v['r_frame_rate']=='30/1'
    decoded=subprocess.run([assets['ffmpeg'],'-v','error','-i',str(p),'-f','null','-'],capture_output=True,text=True,encoding='utf8')
    assert decoded.returncode==0 and not decoded.stderr.strip()
    parts.append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size,'frames':n,'global_video_start':frame/30,'global_video_end':(frame+n)/30,'full_decode':'pass'})
    frame+=n
assert frame==copy['frames']and len(parts)==4
record={'master_sha256':copy['master_sha256'],'copy_sha256':copy['sha256'],'video_frames':frame,'parts':parts,'all_video_frames_preserved':True,'reencoded':False,'purpose':'four smaller720p review parts; original single upload uncertain; local1080p preserved'}
(dest/'manifest.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(record,ensure_ascii=False))
