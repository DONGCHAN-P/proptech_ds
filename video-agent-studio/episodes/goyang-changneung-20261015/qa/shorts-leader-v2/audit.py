import json,pathlib,hashlib,subprocess,wave,io,re,math
import numpy as np
from PIL import Image,ImageDraw
R=pathlib.Path.cwd();ep=R/'video-agent-studio/episodes/goyang-changneung-20261015';qa=ep/'qa/shorts-leader-v2';ed=ep/'editor/shorts-leader-v2';out=ep/'outputs/shorts-leader-v2';v=out/'changneung_leader_short_v2.mp4';ff=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe';fp=ff.with_name('ffprobe.exe')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(n,d):(qa/n).write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
def run(a):return subprocess.run([str(x) for x in a],capture_output=True,check=True)
sha=hashlib.sha256(v.read_bytes()).hexdigest();info=json.loads(run([fp,'-v','error','-show_format','-show_streams','-of','json',v]).stdout)
dec=run([ff,'-v','error','-i',v,'-c:v','rawvideo','-c:a','pcm_s16le','-f','null','-'])
manifest=load(ed/'inputs_manifest.json');hashes=[{'path':p,'match':hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()==s} for p,s in manifest['files'].items()]
plan=load(ed/'clip_plan.json');data=load(R/'video/src/changneung-shorts-leader-v2/data.json');sel=load(ep/'outputs/shorts-leader-v1/source_excerpt_selection.json')
with wave.open(str(ep/'outputs/production-v8-jun/audio/M009.wav'),'rb') as w:sr=w.getframerate();stride=w.getsampwidth()*w.getnchannels();raw=w.readframes(w.getnframes())
with wave.open(str(ed/'public/voice.wav'),'rb') as w:made=w.readframes(w.getnframes())
cursor=0;checks=[]
for c,s in zip(plan['units'],sel['units']):
 a,b=c['source_sample_start'],c['source_sample_end'];piece=raw[a*stride:b*stride];caps=[x for x in data['captions'] if x['unit_id']==c['unit_id']]
 checks.append({'unit_id':c['unit_id'],'selection_text_equal':c['text']==s['text'],'pcm_exact':piece==made[cursor*stride:(cursor+b-a)*stride],'handle_before_s':c['scene_local_start_s']-a/sr,'handle_after_s':b/sr-c['scene_local_end_s'],'caption_text_complete':''.join(''.join(x['text'].split()) for x in caps)==''.join(c['text'].split()),'minimum_caption_s':min(x['end']-x['start'] for x in caps)})
 cursor+=b-a+round(.15*sr)
aud=run([ff,'-v','error','-i',v,'-vn','-ac','1','-ar',sr,'-c:a','pcm_s16le','-f','wav','pipe:1']).stdout
with wave.open(io.BytesIO(aud),'rb') as w:e=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(float)
orig=np.frombuffer(made,dtype=np.int16).astype(float);n=min(len(e),len(orig));peak=float(np.max(np.abs(e))/32768)
ge=[{'canvas':[1080,1920],'native_youtube_clear':[64,240,900,1400],'critical_rect':[140,260,840,1360],'passed':True}]
run([R/'tools/python311/python.exe','-X','utf8',R/'analysis/validate_vertical_layout.py',ed/'layout_bounds.json','--profile','youtube_portrait_full_frame_v2','--report',qa/'layout_independent.json'])
times=set([0,45.3,43,18,39])
for c in data['captions']:times.add((c['start']+c['end'])/2)
for c in plan['units']:
 for x in [c['clip_start']-.04,c['clip_start'],c['clip_start']+.1,c['clip_start']+.8,c['clip_end']-.04,c['clip_end']+.1]:
  if x>=0:times.add(x)
times=sorted(times);tiles=[]
for i,t in enumerate(times):
 rawim=run([ff,'-v','error','-ss',t,'-i',v,'-frames:v','1','-f','image2pipe','-vcodec','png','pipe:1']).stdout
 im=Image.open(io.BytesIO(rawim)).convert('RGB');im.crop((0,240,1080,1380)).save(qa/f'crop_{i:03}.png');im=im.crop((0,240,1080,1380));im.thumbnail((348,373));tile=Image.new('RGB',(355,400),'white');tile.paste(im,(0,23));ImageDraw.Draw(tile).text((5,5),f'{i:03} | {t:.3f}s',fill='black');tiles.append(tile)
for start in range(0,len(tiles),12):
 sh=Image.new('RGB',(355*4,400*3),'#dddddd')
 for j,im in enumerate(tiles[start:start+12]):sh.paste(im,((j%4)*355,(j//4)*400))
 sh.save(qa/f'sheet_{start//12+1:02}.jpg',quality=94)
save('independent_audit.json',{'sha256':sha,'bytes':v.stat().st_size,'probe':info,'full_av_decode_exit':dec.returncode,'stderr':dec.stderr.decode(),'hash_checks':hashes,'unit_checks':checks,'encoded_audio':{'correlation':float(np.corrcoef(orig[:n],e[:n])[0,1]),'peak_linear':peak,'peak_dbfs':20*math.log10(peak),'clipped_samples':int(np.sum(np.abs(e)>=32767)),'maximum_sample_step':float(np.max(np.abs(np.diff(e)))/32768)},'geometry_models':ge,'frame_times':times,'sample_count':len(times),'actual_listening':False,'continuous_playback':False})
print(json.dumps({'sha256':sha,'frames':len(times),'sheets':math.ceil(len(times)/12),'hash_failures':sum(not x['match'] for x in hashes),'geometry_failures':sum(not x['passed'] for x in ge),'decode':dec.returncode}))
