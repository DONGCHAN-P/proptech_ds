import pathlib,json,subprocess,numpy as np
p=pathlib.Path(__file__).parent;e=p.parents[1];ff='C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin/ffmpeg.exe';sr=48000
def dec(v,ss=0,dur=None):
 args=[ff,'-v','error','-ss',str(ss),'-i',str(v)]
 if dur:args+=['-t',str(dur)]
 return np.frombuffer(subprocess.check_output(args+['-f','f32le','-ac','1','-ar',str(sr),'pipe:1']),dtype='<f4')
mix=dec(e/'outputs/video-review-v6/namyangju-map-led_v6.mp4',849,27.4);bgm=dec(pathlib.Path('video/public/namyangju-map-led-v6/data_city_ambient_v1.wav'),32,28);voice=dec(e/'narration/audio-v2/M009.mp3');v=np.zeros(len(mix));v[:len(voice)]=voice;rows=[]
for a,b in [(2,8),(16.5,18.35),(18.7,21),(24.5,25),(26.8,27.3)]:
 i,j=int(a*sr),int(b*sr);x=np.column_stack([bgm[i:j],v[i:j]]);coef=np.linalg.lstsq(x,mix[i:j],rcond=None)[0];rows.append({'relative_s':[a,b],'absolute_s':[849+a,849+b],'estimated_music_gain':float(coef[0]),'estimated_voice_gain':float(coef[1]),'rms':float(np.sqrt(np.mean(mix[i:j]**2)))})
r={'actual_listening':False,'source':'actualfullAACvsoriginalM009+originalmusic32s','voice_pcm_s':len(voice)/sr,'voice_end_absolute_s':849+len(voice)/sr,'music_tail_s':9,'windows':rows,'peak_abs_tail':float(np.max(np.abs(mix))),'last_0_1s_rms':float(np.sqrt(np.mean(mix[-4800:]**2)))}
(p/'full_tail_audio_check.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(r))
