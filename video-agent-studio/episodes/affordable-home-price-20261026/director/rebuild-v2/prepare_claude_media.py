"""Compact actual-encoded evidence for Opus/max; independent full QA is separate."""
import argparse,hashlib,json,math,subprocess
from pathlib import Path
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;EP=D.parents[1];ROOT=EP.parents[2]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def relative(p):return p.relative_to(ROOT).as_posix()
ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);a=ap.parse_args()
assert a.run.replace('-','').isalnum()
full=EP/'outputs/rebuild-v2/full-film-r2-v1';movie=full/'affordable_home_price_rebuild_r2_v1.mp4'
edl=read(full/'global_edl.json');render=read(full/'render_receipt.json')
assert sha(movie)==render['mp4']['sha256'] and edl['script']['sha256']=='cc1ef7d80225e992e7e5d31faffbfb09a8f90c80fb5352e17c36eb8c90755b12'
out=D/a.run;out.mkdir(exist_ok=False);(out/'frames').mkdir()
scenes={s['scene_id']:s for s in edl['scenes']};beats={}
for b in edl['beats']:beats.setdefault(b['scene_id'],[]).append(b)
requests={}
def request(frame,tag):
 assert 0<=frame<edl['total_frames'];requests.setdefault(frame,[]).append(tag);return frame
def beatframe(sid,i):
 s=scenes[sid];b=beats[sid][i]
 return min(s['end_frame']-1,math.ceil((b['local_start_s']+.7)*30)+s['start_frame'])
overview=[(s['scene_id'],request(beatframe(s['scene_id'],-1),s['scene_id']+' final information')) for s in edl['scenes']]
progressions={sid:[request(scenes[sid]['start_frame'],sid+' opening')]+[request(beatframe(sid,i),sid+' beat'+str(i)) for i in range(len(beats[sid]))] for sid in ['R003','R006','R030']}
critical=[('R001',2),('R011',1),('R017',3),('R026',3),('R029',0),('R030',2)]
critical=[(sid,request(beatframe(sid,i),sid+' critical full frame')) for sid,i in critical]
long=[];used=set()
for c in sorted(edl['cues'],key=lambda c:len(c['text']),reverse=True):
 if c['scene_id'] in used:continue
 used.add(c['scene_id']);long.append((c['scene_id'],request((c['start_frame']+c['end_frame']-1)//2,c['id']+' long caption')))
 if len(long)==2:break
cutframes=[]
for sid in ['R003','R029','R018','R023']:
 cut=scenes[sid]['start_frame']
 for delta in [-1,0,1]:cutframes.append(request(cut+delta,sid+' entry '+str(delta)))
chapterframes={s['chapter_id']:request((s['start_frame']+s['end_frame']-1)//2,'chapter'+str(s['chapter_id'])+' midpoint') for s in edl['segments'] if s['kind']=='chapter'}
frames=sorted(requests);expr='+'.join('eq(n,'+str(n)+')' for n in frames).replace(',',r'\,')
ff=ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
cmd=[str(ff),'-nostdin','-n','-v','error','-i',str(movie),'-map','0:v:0','-an','-vf','select='+expr,'-fps_mode','passthrough','-q:v','2',str(out/'frames/frame-%04d.jpg')]
r=subprocess.run(cmd,capture_output=True);(out/'extract.log').write_bytes(r.stderr);assert r.returncode==0
files=sorted((out/'frames').glob('frame-*.jpg'));assert len(files)==len(frames)
lookup=dict(zip(frames,files));imagepaths=[]
def sheet(name,rows,columns=2,width=640):
 height=360+24;canvas=Image.new('RGB',(columns*width,math.ceil(len(rows)/columns)*height),'white');draw=ImageDraw.Draw(canvas)
 for i,(tag,frame) in enumerate(rows):
  im=Image.open(lookup[frame]).convert('RGB').resize((width,360));x=(i%columns)*width;y=(i//columns)*height;canvas.paste(im,(x,y+24));draw.text((x+8,y+5),tag+' f'+str(frame)+' '+str(round(frame/30,3))+'s',fill='black')
 dest=out/name;canvas.save(dest,quality=94);imagepaths.append(relative(dest));return dest
for i in range(0,len(overview),8):sheet('overview-'+str(i//8+1)+'.jpg',overview[i:i+8])
for sid,fframes in progressions.items():sheet(sid+'-progression.jpg',[(sid,fr) for fr in fframes])
for sid,fr in critical:
 target=out/(sid+'-critical.jpg');Image.open(lookup[fr]).save(target,quality=96);imagepaths.append(relative(target))
for i,(sid,fr) in enumerate(long):
 target=out/('long-caption-'+str(i+1)+'-'+sid+'.jpg');Image.open(lookup[fr]).save(target,quality=96);imagepaths.append(relative(target))
chapter=Image.new('RGB',(1280,1536),'white');draw=ImageDraw.Draw(chapter)
for i in range(8):
 cp=lookup[chapterframes[i+1]];im=Image.open(cp).convert('RGB').resize((640,360));x=(i%2)*640;y=(i//2)*384;chapter.paste(im,(x,y+24));draw.text((x+8,y+5),'Chapter '+str(i+1)+' actual full MP4',fill='black')
target=out/'chapter-cards.jpg';chapter.save(target,quality=94);imagepaths.append(relative(target))
sheet('cut-entries.jpg',[(str(i),fr) for i,fr in enumerate(cutframes)],columns=3,width=640)
baseline=EP/'qa/comparison-housing-choice-v1/baseline_04m45_full.png'
canvas=Image.new('RGB',(1920,2208),'white');draw=ImageDraw.Draw(canvas)
for i,(tag,p) in enumerate([('Published Jun housing-choice baseline',baseline),('Rebuilt affordable-price actual full-film frame',lookup[dict(critical)['R030']])]):
 canvas.paste(Image.open(p).convert('RGB').resize((1920,1080)),(0,i*1104+24));draw.text((12,i*1104+5),tag,fill='black')
target=out/'baseline-comparison.jpg';canvas.save(target,quality=94);imagepaths.append(relative(target))
assert len(imagepaths)==19
save(out/'image_paths.json',imagepaths)
save(out/'frame_manifest.json',{'video':relative(movie),'video_sha256':sha(movie),'frames':[{'frame':n,'PTS_s':n/30,'path':relative(lookup[n]),'sha256':sha(lookup[n]),'reasons':requests[n]} for n in frames],'images':[{'path':p,'sha256':sha(ROOT/p)} for p in imagepaths],'actual_listening':False,'continuous_playback':False})
report={'video':relative(movie),'video_sha256':sha(movie),'srt':relative(full/'captions_global.srt'),'srt_sha256':sha(full/'captions_global.srt'),'duration_s':edl['total_seconds'],'frames':edl['total_frames'],'script_sha256':edl['script']['sha256'],'script_markdown_sha256':sha(D/'frozen-script-v3-r2/script_v3_r2.md'),'source_scene_order':[s['scene_id'] for s in edl['scenes']],
 'actual_encoded_image_scope':'19 images: all34 final-information overview5 sheets,3 progressive examples,6 critical full frames,2 longest caption full frames,8 unique chapter cards,4 entry-cut triplets,1 published baseline comparison. Image manifest carries exact video/frame/image hashes.',
 'frame_manifest':relative(out/'frame_manifest.json'),'independent_full_QA':'in progress in qa/rebuild-v2/media-qa, not pre-claimed approved','representative_QA':read(EP/'qa/rebuild-v2/media-qa/expansion_approval_v3.json'),'audio_scope':read(EP/'qa/rebuild-v2/audio_review.json'),'technical':read(full/'av_signal_receipt.json'),
 'corrections':'Opening context blank-body bug corrected and checked actual R0067.31875s. R011186.5 retained; R0176:4:2 bar lengths corrected; R029labels hidden with values. R030 now300 budget−30 ownership−100 savings→170 mortgage→5억6586 price, each actual anchor. New images3, distinct chapter photos8, no AI badge or internal source IDs. Narration A arc finishes before B.',
 'outro':{'last_speech_global_s':edl['last_speech_global_s'],'outro_start_s':edl['outro_start_s'],'gap_s':edl['outro_start_s']-edl['last_speech_global_s']},'actual_listening':False,'continuous_playback':False,'screen_content_is_current_exact_MP4':True}
save(out/'review_report.json',report)
print(json.dumps({'images':len(imagepaths),'sampled_full_video_frames':len(frames),'video_sha256':sha(movie),'report':relative(out/'review_report.json')}))
