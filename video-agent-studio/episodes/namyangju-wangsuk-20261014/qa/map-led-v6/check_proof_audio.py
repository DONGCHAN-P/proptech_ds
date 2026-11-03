import pathlib,subprocess,json,numpy as np
p=pathlib.Path(__file__).parent;e=p.parents[1];ff='C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin/ffmpeg.exe';rate=48000
def dec(path):return np.frombuffer(subprocess.check_output([ff,'-v','error','-i',str(path),'-f','f32le','-ac','1','-ar',str(rate),'pipe:1']),dtype='<f4')
mix=dec(e/'outputs/video-review-v6/map-led_v6_intro-proof.mp4');music=dec(pathlib.Path('video/public/namyangju-map-led-v6/data_city_ambient_v1.wav'));voice=dec(e/'narration/audio-v2/M000.mp3');v=np.zeros(len(mix));v[72000:72000+len(voice)]=voice;checks=[]
for a,b in [(.2,.5),(.9,1.2),(3,6),(10,15),(20.5,21),(21.7,22.2)]:
 i,j=int(a*rate),int(b*rate);x=np.column_stack([music[i:j],v[i:j]]);coef=np.linalg.lstsq(x,mix[i:j],rcond=None)[0];checks.append({'window_s':[a,b],'estimated_music_gain':float(coef[0]),'estimated_voice_gain':float(coef[1]),'rms':float(np.sqrt(np.mean(mix[i:j]**2)))})
r={'file':'map-led_v6_intro-proof.mp4','actual_listening':False,'method':'원음악/원음성(1.5초shift)과실제AAC디코드신호의구간별최소제곱분리.압축오차있음.','peak_abs':float(np.max(np.abs(mix))),'rms_windows':checks,'sample_rate':rate}
(p/'proof_audio_check.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(r,ensure_ascii=True))
