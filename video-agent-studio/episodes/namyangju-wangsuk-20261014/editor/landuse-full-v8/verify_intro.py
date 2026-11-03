from pathlib import Path
import subprocess,json,hashlib
r=Path(__file__).resolve().parents[2];out=r/'outputs/intro-review-v9';v=out/'namyangju-intro_v9.mp4';tools=Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin');ff=str(tools/'ffmpeg.exe');fp=str(tools/'ffprobe.exe')
p=json.loads(subprocess.check_output([fp,'-v','error','-show_streams','-show_format','-of','json',str(v)]));dec=subprocess.run([ff,'-v','error','-i',str(v),'-f','null','-'],capture_output=True,text=True);assert dec.returncode==0,dec.stderr
for n in [90,95,210,350,420,500,690,850,916,917,1000,1066]:
 subprocess.run([ff,'-v','error','-i',str(v),'-vf',f'select=eq(n\\,{n})','-frames:v','1','-y',str(out/f'encoded_{n}.png')],check=True)
d={'file':str(v),'sha256':hashlib.sha256(v.read_bytes()).hexdigest(),'bytes':v.stat().st_size,'whole_decode_exit':dec.returncode,'probe':p,'actual_listening':False,'continuous_playback':False};(out/'technical_check.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'sha256':d['sha256'],'bytes':d['bytes'],'duration':p['format']['duration'],'frames':p['streams'][0].get('nb_frames')},indent=2))
