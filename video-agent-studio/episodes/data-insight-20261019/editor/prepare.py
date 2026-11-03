import json, pathlib, shutil, wave, math, struct
from PIL import Image
ROOT=pathlib.Path(__file__).resolve().parents[4]
EP=pathlib.Path(__file__).resolve().parents[1]
PUB=ROOT/'video/public/data-insight-v1'
SRC=ROOT/'video/src/data-insight-v1'
PUB.mkdir(parents=True,exist_ok=True); SRC.mkdir(parents=True,exist_ok=True)
data=json.loads((EP/'scenes.json').read_text(encoding='utf-8'))
manifest=json.loads((EP/'inputs/manifest.json').read_text(encoding='utf-8'))
for a in manifest:
 p=pathlib.Path(a['path']); shutil.copy2(p,PUB/p.name)
 if a['id']=='A05':
  im=Image.open(p); durations=[]
  for i in range(im.n_frames):
   im.seek(i); im.convert('RGB').save(PUB/f'A05_{i}.png');durations.append(im.info.get('duration',100))
  data['gif_durations']=durations
data['assets']={a['id']:pathlib.Path(a['path']).name for a in manifest}
(SRC/'data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
shutil.copy2(ROOT/'video/public/fonts/Pretendard-Bold.woff2',PUB/'bold.woff2')
shutil.copy2(ROOT/'video/public/fonts/Pretendard-Regular.woff2',PUB/'regular.woff2')
# Original 30-second instrumental: soft major-seventh pads, bell arpeggio and restrained pulse.
sr=44100; seconds=30
chords=[(130.8128,164.8138,195.9977,246.9417),(110,130.8128,164.8138,195.9977),(87.3071,110,130.8128,164.8138),(97.9989,123.4708,146.8324,184.9972)]
with wave.open(str(PUB/'bgm.wav'),'wb') as w:
 w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr)
 buf=bytearray()
 for i in range(sr*seconds):
  t=i/sr;c=chords[int(t/3.75)%4];env=min(t/1.2,1,(30-t)/2)
  pad=sum(math.sin(2*math.pi*f*t)+.15*math.sin(2*math.pi*f*2*t) for f in c)*.025
  beat=t%.46875;note=c[int(t/.46875)%4]*4
  bell=math.sin(2*math.pi*note*t)*math.exp(-beat*9)*.045
  pulse=math.sin(2*math.pi*55*t)*math.exp(-(t%.9375)*22)*.05
  v=(pad+bell+pulse)*env
  for gain in (1,.97):buf.extend(struct.pack('<h',int(max(-1,min(1,v*gain))*32767)))
 w.writeframes(buf)
def tc(s):
 return f'{int(s)//3600:02}:{int(s)//60%60:02}:{int(s)%60:02},000'
(EP/'outputs/v1').mkdir(parents=True,exist_ok=True)
(EP/'outputs/v1/captions.srt').write_text('\n\n'.join(f"{i+1}\n{tc(s['start'])} --> {tc(s['end'])}\n{s['caption']}" for i,s in enumerate(data['scenes']))+'\n',encoding='utf-8')
(EP/'outputs/v1/captions.json').write_text(json.dumps([{'text':s['caption'],'startMs':s['start']*1000,'endMs':s['end']*1000,'timestampMs':None,'confidence':None} for s in data['scenes']],ensure_ascii=False,indent=2),encoding='utf8')
usage=[{'asset_id':a['id'],'source_sha256':a['sha256'],'uses':[{'scene_id':s['scene_id'],'start':s['start'],'end':s['end']} for s in data['scenes'] if a['id'] in s['assets']]} for a in manifest]
(EP/'editor/asset_usage.json').write_text(json.dumps(usage,ensure_ascii=False,indent=2),encoding='utf-8')
print('Prepared 13 source assets, 7 synchronized GIF frames, fonts, original BGM, SRT and usage map.')
