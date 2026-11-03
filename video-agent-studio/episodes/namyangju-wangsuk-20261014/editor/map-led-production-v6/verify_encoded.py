import json,subprocess,hashlib,re
from pathlib import Path
E=Path(__file__).resolve().parents[2];O=E/'outputs/video-review-v6';Q=O/'technical_qa';Q.mkdir(exist_ok=True)
B=Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin');F=O/'namyangju-map-led_v6.mp4'
def run(args):return subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace')
probe=run([str(B/'ffprobe.exe'),'-v','error','-show_streams','-show_format','-of','json',str(F)]);assert probe.returncode==0;info=json.loads(probe.stdout)
v=next(s for s in info['streams'] if s['codec_type']=='video');a=next(s for s in info['streams'] if s['codec_type']=='audio')
assert (v['width'],v['height'],v['r_frame_rate'])==(1920,1080,'30/1');assert abs(float(info['format']['duration'])-876.4)<.1
decode=run([str(B/'ffmpeg.exe'),'-v','error','-i',str(F),'-f','null','-']);assert decode.returncode==0 and not decode.stderr.strip()
audio=run([str(B/'ffmpeg.exe'),'-hide_banner','-i',str(F),'-vn','-af','astats=metadata=0:reset=0','-f','null','-']);assert audio.returncode==0
(Q/'audio_astats.txt').write_text(audio.stderr,encoding='utf-8')
frames=[0,30,120,669,900,1800,2009,2100,4544,5600,7100,7120,7160,7792,9400,9892,10790,13087,13550,15360,16200,18250,18850,19800,21238,21750,24300,25470,26000,26280]
for f in frames:
 r=run([str(B/'ffmpeg.exe'),'-v','error','-ss',str(f/30),'-i',str(F),'-frames:v','1','-y',str(Q/f'encoded_{f}.png')]);assert r.returncode==0
result={'file':F.name,'sha256':hashlib.sha256(F.read_bytes()).hexdigest(),'probe':info,'whole_decode_pass':True,'actual_frames':frames,'actual_listening':False,'continuous_playback':False,'astats_log':'technical_qa/audio_astats.txt','caption_timing_basis':'provider raw character alignment, exact approved spans; sampled visual inspection pending'}
(Q/'encoded_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'duration':info['format']['duration'],'bytes':F.stat().st_size,'sha256':result['sha256'],'decode':'pass','frames':len(frames)}))
