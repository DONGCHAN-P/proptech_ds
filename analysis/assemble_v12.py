import array
import json
import pathlib
import subprocess
import sys
import numpy as np
import wave

root = pathlib.Path(__file__).resolve().parents[1]
ff = pathlib.Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin/ffmpeg.exe')
out = root / 'video/out'
music = root / 'assets/music/data_city_ambient_v1.wav'
if not music.exists():
    rate=44100; duration=64; signal=np.zeros(rate*duration,dtype=np.float64)
    # Original sustained chords and soft bell accents; no sampled music.
    chords=[[130.8128,164.8138,195.9977,246.9417],
            [110,130.8128,164.8138,195.9977],
            [87.3071,130.8128,174.6141,220],
            [97.9989,146.8324,195.9977,246.9417]]
    for bar in range(8):
        t=np.arange(rate*8)/rate
        envelope=np.sin(np.pi*t/8)**2
        for hz in chords[bar%4]:
            signal[bar*rate*8:(bar+1)*rate*8]+=.028*envelope*(np.sin(2*np.pi*hz*t)+.15*np.sin(2*np.pi*hz*2*t))
        for beat in range(4):
            u=t-beat*2
            mask=u>=0
            signal[bar*rate*8:(bar+1)*rate*8]+=.018*mask*np.exp(-np.maximum(u,0)*2)*np.sin(2*np.pi*chords[bar%4][beat]*4*u)
    stereo=np.stack([signal,signal*.96],axis=1)
    with wave.open(str(music),'wb') as w:
        w.setnchannels(2);w.setsampwidth(2);w.setframerate(rate)
        w.writeframes((np.clip(stereo,-1,1)*32767).astype('<i2').tobytes())
    music.with_suffix('.license.json').write_text(json.dumps({'title':'Data City Ambient v1','source':'original local synthesis','duration':64,'sampled_material':False,'method':'sine sustained chords and bell envelopes','attribution_required':False},indent=2),encoding='utf-8')
cut=412/30;main=18598/30;total=main+15
graph=(
    f'[0:v]split[v0][v1];[v0]trim=end_frame=412,setpts=PTS-STARTPTS,setsar=1[a];'
    f'[v1]trim=start_frame=412,setpts=PTS-STARTPTS,setsar=1[b];'
    '[1:v]fps=30,trim=duration=5,setpts=PTS-STARTPTS,setsar=1[c];'
    '[2:v]fps=30,trim=duration=10,setpts=PTS-STARTPTS,setsar=1[d];'
    f'[0:a]asplit[au0][au1];[au0]atrim=end={cut},asetpts=PTS-STARTPTS[a0];'
    f'[au1]atrim=start={cut}:end={main},asetpts=PTS-STARTPTS[a1];'
    '[1:a]atrim=duration=5,asetpts=PTS-STARTPTS[a2];'
    '[2:a]atrim=duration=10,asetpts=PTS-STARTPTS[a3];'
    '[a][a0][c][a2][b][a1][d][a3]concat=n=4:v=1:a=1[v][voice];'
    '[voice]asplit[side][dry];'
    f'[3:a]atrim=duration={total},asetpts=PTS-STARTPTS,volume=0.28,'
    f"volume='if(between(t,{cut},{cut+5})+gte(t,{main+5}),0.2,1)':eval=frame,"
    f'afade=t=in:d=3,afade=t=out:st={total-5}:d=5[bed];'
    '[bed][side]sidechaincompress=threshold=0.018:ratio=5:attack=25:release=450:makeup=1[ducked];'
    '[dry][ducked]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95:level=0[audio]')
(out/'newtown-v12-filter.txt').write_text(graph,encoding='utf-8')
cmd=[str(ff),'-y','-i',str(out/'newtown-v11-nexttown.mp4'),'-i',str(out/'channel-intro-v2.mp4'),'-i',str(out/'channel-outro-v2.mp4'),'-stream_loop','-1','-i',str(music),'-filter_complex_script',str(out/'newtown-v12-filter.txt'),'-map','[v]','-map','[audio]','-c:v','libx264','-preset','veryfast','-crf','23','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-t',str(total),'-movflags','+faststart',str(out/'newtown-v12-brand-bgm.mp4')]
print('Rendering v12',total,'seconds',flush=True)
subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL,stderr=(out/'newtown-v12-render.log').open('w',encoding='utf-8'))
print('Rendered',flush=True)
