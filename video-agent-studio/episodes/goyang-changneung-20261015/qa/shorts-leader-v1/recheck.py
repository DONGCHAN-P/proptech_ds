import json,pathlib,subprocess,hashlib,io
from PIL import Image,ImageDraw
R=pathlib.Path.cwd();ep=R/'video-agent-studio/episodes/goyang-changneung-20261015';q=ep/'qa/shorts-leader-v1';ed=ep/'editor/shorts-leader-v1';v=ep/'outputs/shorts-leader-v1/changneung_leader_short_v1.mp4';ff=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe'
def run(a):return subprocess.run([str(x) for x in a],capture_output=True,check=True)
def save(n,d):(q/n).write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
d=json.loads((R/'video/src/changneung-shorts-leader-v1/data.json').read_text(encoding='utf8'));audit=json.loads((q/'independent_audit.json').read_text(encoding='utf8'));sha=hashlib.sha256(v.read_bytes()).hexdigest()
probe=json.loads(run([ff.with_name('ffprobe.exe'),'-v','error','-show_streams','-show_format','-of','json',v]).stdout);decode=run([ff,'-v','error','-i',v,'-c:v','rawvideo','-c:a','pcm_s16le','-f','null','-'])
run([R/'tools/python311/python.exe','-X','utf8',R/'analysis/validate_vertical_layout.py',ed/'layout_bounds.json','--report',q/'layout_final.json'])
times=[9.33,9.4,10.295,11.21,11.4,19.14,19.2,20.175,21.17,21.35,33.19,33.24,33.34,34.04,34.435,35.59,35.78,35.88,36.58,38.775,39,40.935,42.13,42.27,42.34,43,45.3];tiles=[]
for i,t in enumerate(times):
 im=Image.open(io.BytesIO(run([ff,'-v','error','-ss',t,'-i',v,'-frames:v','1','-f','image2pipe','-vcodec','png','pipe:1']).stdout)).convert('RGB');im.save(q/f'final_{i:02}.png');im=im.crop((140,430,835,1175));im.thumbnail((348,373));tile=Image.new('RGB',(355,400),'white');tile.paste(im,(0,23));ImageDraw.Draw(tile).text((4,5),f'{i:02} | {t:.3f}s',fill='black');tiles.append(tile)
for start in range(0,len(tiles),12):
 sh=Image.new('RGB',(1420,1200),'#ddd')
 for j,im in enumerate(tiles[start:start+12]):sh.paste(im,((j%4)*355,(j//4)*400))
 sh.save(q/f'final_sheet_{start//12+1}.jpg',quality=94)
manifest=json.loads((ed/'inputs_manifest.json').read_text(encoding='utf8'));checks=[{'path':p,'match':hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()==s} for p,s in manifest['files'].items()]
caps=[{'unit_id':u['unit_id'],'complete':''.join(''.join(c['text'].split()) for c in d['captions'] if c['unit_id']==u['unit_id'])==''.join(u['text'].split())} for u in d['clips']]
voice=hashlib.sha256((ed/'public/voice.wav').read_bytes()).hexdigest();oldvoice=next(x['path'] for x in audit['hash_checks'] if x['path'].endswith('voice.wav'));voice_unchanged=voice=='48b2370894a33b54a1b41730ebadfc3c3685813322b3502d6054979fcdfae731'
save('final_recheck.json',{'sha256':sha,'probe':probe,'decode_exit':decode.returncode,'decode_stderr':decode.stderr.decode(),'hash_checks':checks,'caption_complete':caps,'voice_pcm_unchanged':voice_unchanged,'frame_times':times,'actual_listening':False,'continuous_playback':False,'inherited_unchanged_coverage':'independent_audit.json initial 73 actual encoded samples; changed captions and S1 map independently sampled again'})
print(json.dumps({'sha256':sha,'frames':len(times),'decode':decode.returncode,'voice_unchanged':voice_unchanged,'hashes_pass':all(x['match'] for x in checks)}))
