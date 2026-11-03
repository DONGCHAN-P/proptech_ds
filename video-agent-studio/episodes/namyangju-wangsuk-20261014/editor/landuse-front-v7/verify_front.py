import json,subprocess,hashlib
from pathlib import Path
E=Path(__file__).resolve().parents[2];O=E/'outputs/front-review-v7';Q=O/'technical_qa';Q.mkdir(exist_ok=True)
B=Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin');F=O/'namyangju-landuse_front_v7.mp4'
def run(args):return subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace')
r=run([str(B/'ffprobe.exe'),'-v','error','-show_format','-show_streams','-of','json',str(F)]);assert r.returncode==0;info=json.loads(r.stdout);v=next(s for s in info['streams'] if s['codec_type']=='video');assert any(s['codec_type']=='audio' for s in info['streams']);assert (v['width'],v['height'],v['r_frame_rate'])==(1920,1080,'30/1');assert abs(float(info['format']['duration'])-13087/30)<.1
d=run([str(B/'ffmpeg.exe'),'-v','error','-i',str(F),'-f','null','-']);assert d.returncode==0 and not d.stderr.strip()
frames=[0,110,111,1650,2400,3000,4560,4800,10200,10500,10850,11150,12500,13080]
for f in frames:
 r=run([str(B/'ffmpeg.exe'),'-v','error','-ss',str(f/30),'-i',str(F),'-frames:v','1','-y',str(Q/f'encoded_{f}.png')]);assert r.returncode==0
sha=hashlib.sha256(F.read_bytes()).hexdigest();result={'file':F.name,'sha256':sha,'bytes':F.stat().st_size,'probe':info,'whole_decode_pass':True,'sample_frames':frames,'actual_listening':False,'continuous_playback':False}
(Q/'encoded_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'sha256':sha,'bytes':F.stat().st_size,'duration':info['format']['duration'],'whole_decode':'pass'}))
