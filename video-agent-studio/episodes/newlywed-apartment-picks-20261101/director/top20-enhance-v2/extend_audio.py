"""Generate only added narration with the selected free voice, then PCM-splice.
No credentials or paid providers. Existing narration bytes remain unchanged.
"""
from pathlib import Path
import argparse,asyncio,copy,datetime,hashlib,html,json,subprocess,sys,wave

D=Path(__file__).resolve().parent;E=D.parents[1];R=E.parents[2]
N=E/'narration/top20-enhance-v2';N.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(E/'narration/top20-production-v1/deps'))
import edge_tts
FF=R/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
RATE=44100;FACTOR=1.35
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,j):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def norm(s):return ''.join(c.lower()for c in html.unescape(s)if c.isalnum())
def pcm(p):
 with wave.open(str(p),'rb')as f:
  assert (f.getnchannels(),f.getsampwidth(),f.getframerate())==(1,2,RATE)
  return f.readframes(f.getnframes())
def wav(p,data):
 with wave.open(str(p),'wb')as f:f.setparams((1,2,RATE,0,'NONE','not compressed'));f.writeframes(data)
def ff(args):
 p=subprocess.run([str(FF),'-hide_banner','-loglevel','error',*map(str,args)],capture_output=True)
 assert p.returncode==0,p.stderr.decode(errors='replace')[-800:]

async def generate(retry_blocked=False):
 packet=read(D/'added_scenes.json')
 for scene in packet['scenes']:
  sid=scene['scene_id'];out=N/sid;out.mkdir(exist_ok=True)
  text='\n'.join(x['reading_text']for x in scene['sentences']);inputp=out/'reading.txt';inputp.write_text(text,encoding='utf-8')
  rp=out/'generation_receipt.json'
  if rp.exists():
   old=read(rp)
   if old['status']=='complete':
    assert old['input_sha256']==sha(inputp)
    assert sha(out/'production.wav')==old['production_audio_sha256']
    continue
   assert retry_blocked and old.get('error_type')=='ClientConnectorError' and (not(out/'raw.mp3').exists()or(out/'raw.mp3').stat().st_size==0),'Existing attempt requires explicit local retry decision'
   archive=out/'generation_receipt_network_blocked.json';assert not archive.exists()
   rp.rename(archive)
  rec={'status':'started','voice':'ko-KR-InJoonNeural','provider':'microsoft_edge_consumer_tts','rate':'+0%','postprocess_atempo_factor':FACTOR,'input_sha256':sha(inputp),'characters':len(text),'cash_cost_krw':0,'paid_api_calls':0,'automatic_retry':False,'actual_listening':False,'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};save(rp,rec)
  boundaries=[]
  try:
   comm=edge_tts.Communicate(text,rec['voice'],rate='+0%',boundary='WordBoundary',connect_timeout=15,receive_timeout=40)
   with(out/'raw.mp3').open('wb')as f:
    async for item in comm.stream():
     if item['type']=='audio':f.write(item['data'])
     elif item['type']=='WordBoundary':boundaries.append(item)
   assert boundaries and(out/'raw.mp3').stat().st_size>1000
   save(out/'provider_boundaries.json',{'units':'100ns ticks','boundaries':boundaries})
   ff(['-i',out/'raw.mp3','-ar',RATE,'-ac',1,'-c:a','pcm_s16le','-y',out/'raw.wav'])
   ff(['-i',out/'raw.wav','-af',f'atempo={FACTOR}','-ar',RATE,'-ac',1,'-c:a','pcm_s16le','-y',out/'production.wav'])
   rec.update(status='complete',duration_s=len(pcm(out/'production.wav'))/2/RATE,production_audio_sha256=sha(out/'production.wav'),provider_word_count=len(boundaries));save(rp,rec)
   print(json.dumps({'scene_id':sid,'status':'complete','duration_s':rec['duration_s'],'free':True}),flush=True)
  except Exception as exc:
   rec.update(status='failed',error_type=type(exc).__name__);save(rp,rec);raise

def align(scene):
 sid=scene['scene_id'];out=N/sid;rows=scene['sentences'];expected=norm(''.join(x['reading_text']for x in rows));words=[];cursor=0
 for b in read(out/'provider_boundaries.json')['boundaries']:
  token=norm(b['text'])
  assert expected[cursor:cursor+len(token)]==token,(sid,cursor,b['text'])
  words.append({'scene_id':sid,'text':b['text'],'local_start_s':b['offset']/1e7/FACTOR,'local_end_s':(b['offset']+b['duration'])/1e7/FACTOR,'normalized_char_start':cursor,'normalized_char_end':cursor+len(token),'timing_basis':'native_provider_words_scaled_by_existing_1.35_tempo'})
  cursor+=len(token)
 assert cursor==len(expected)
 sentence_times=[];cursor=0
 for row in rows:
  size=len(norm(row['reading_text']));ws=[w for w in words if w['normalized_char_start']<cursor+size and w['normalized_char_end']>cursor]
  assert ws and ws[0]['normalized_char_start']==cursor and ws[-1]['normalized_char_end']==cursor+size
  for w in ws:w.update(sentence_id=row['sentence_id'],sentence_normalized_char_start=w['normalized_char_start']-cursor,sentence_normalized_char_end=w['normalized_char_end']-cursor)
  sentence_times.append({'sentence_id':row['sentence_id'],'text':row['text'],'reading_text':row['reading_text'],'start_s':ws[0]['local_start_s'],'end_s':ws[-1]['local_end_s'],'timing_basis':'provider_word_metadata_scaled_to_actual_pcm','confidence':'metadata_not_actual_listening'})
  cursor+=size
 duration=len(pcm(out/'production.wav'))/2/RATE
 assert sentence_times[-1]['end_s']<=duration+.04
 return {'scene_id':sid,'duration_s':duration,'audio_path':str((out/'production.wav').resolve()),'audio_sha256':sha(out/'production.wav'),'narration_text':'\n'.join(r['text']for r in rows),'reading_text':'\n'.join(r['reading_text']for r in rows),'sentence_times':sentence_times,'sentences':[],'captions':[],'anchors':{'narration_start':sentence_times[0]['start_s']},'timing_basis':'actual_free_tts_pcm_and_native_word_metadata','is_estimate':False},words

def lock():
 base=read(E/'director/top20-production-v1/locked_timing.json');packet=read(D/'added_scenes.json');sp=read(E/'director/top20-production-v1/scene_proposals_v4.json')
 fullpath=Path(base['audio_file']);assert sha(fullpath)==base['audio_sha256'];original=pcm(fullpath)
 insert=next(s['start_s']for s in base['scenes']if s['scene_id']=='C001');frame=round(insert*RATE)
 added=[align(s)for s in packet['scenes']];more=b''.join(pcm(s['audio_path'])for s,w in added);delta=len(more)/2/RATE
 full=N/'narration_with_clean_brand_v4.wav';wav(full,original[:frame*2]+more+original[frame*2:])
 scenes=copy.deepcopy(base['scenes']);idx=next(i for i,s in enumerate(scenes)if s['scene_id']=='C001')
 for s in scenes[idx:]:
  for k in ['start_s','end_s']:s[k]+=delta
  for key in ['sentences','captions']:
   for x in s[key]:x['start_s']+=delta;x['end_s']+=delta
 cursor=insert
 for s,w in added:
  s.update(start_s=cursor,end_s=cursor+s['duration_s'])
  s['sentences']=[{**st,'local_start_s':st['start_s'],'local_end_s':st['end_s'],'start_s':cursor+st['start_s'],'end_s':cursor+st['end_s']}for st in s['sentence_times']]
  s['captions']=[{'sentence_id':st['sentence_id'],'text':st['text'],'start_s':st['start_s'],'end_s':st['end_s']}for st in s['sentences']]
  cursor+=s['duration_s']
 scenes[idx:idx]=[s for s,w in added]
 oldwordpath=Path(base['scenes'][0]['words_path']);oldwordpath=oldwordpath if oldwordpath.is_absolute()else R/oldwordpath
 allwords=copy.deepcopy(read(oldwordpath)['words']);allwords.extend(w for s,ws in added for w in ws);byid={s['scene_id']:s for s in scenes}
 for w in allwords:
  sc=byid[w['scene_id']];w['start_s']=sc['start_s']+w['local_start_s'];w['end_s']=sc['start_s']+w['local_end_s']
 allwords.sort(key=lambda w:w['start_s']);wordpath=N/'words_v4.json';save(wordpath,{'audio_revision':'reuse-v3-plus-free-N-v4','words':allwords})
 for s in scenes:s['words_path']=str(wordpath.resolve())
 t=copy.deepcopy(base);t.update(audio_file=str(full.resolve()),audio_sha256=sha(full),source_timing=str((D/'locked_timing.json').resolve()),source_timing_sha256=None,words_file=str(wordpath.resolve()),scenes=scenes,duration_s=len(pcm(full))/2/RATE,total_duration_s=len(pcm(full))/2/RATE,total_duration_with_brand_and_hold_s=len(pcm(full))/2/RATE,last_spoken_end_s=base['last_spoken_end_s']+delta,last_speech_end_s=base['last_spoken_end_s']+delta,audio_revision='reuse-v3-plus-free-N-v4',script_revision='v5',sentence_count=base['sentence_count']+sum(len(s['sentences'])for s in packet['scenes']),scene_id_count=len(scenes),newly_generated_scene_ids=[s['scene_id']for s in packet['scenes']],added_duration_s=delta,previous_lock_sha256=sha(E/'director/top20-production-v1/locked_timing.json'),actual_listening_performed=False,word_count=len(allwords),audio_body_duration_s=base['audio_body_duration_s']+delta,previous_script_sha256=base['script_sha256'])
 for b in t['brand_visuals']:
  if b['start_s']>=insert:b['start_s']+=delta
 for k in ['brand_outro']:
  t[k]['start_s']+=delta;t[k]['end_s']+=delta
 save(D/'locked_timing.json',t)
 newscenes=[]
 for ps in sp['scenes']:
  if ps['scene_id']=='C001':
   for s in packet['scenes']:newscenes.append({**s,'region_id':None,'rank':None,'narration_text':'\n'.join(x['text']for x in s['sentences']),'status':'measured_timing_locked'})
  newscenes.append(ps)
 for s in newscenes:
  a=byid[s['scene_id']]
  for k in ['start_s','end_s','duration_s','sentence_times','anchors']:s[k]=a[k]
 sp.update(revision='v5',scenes=newscenes,added_scene_ids=[s['scene_id']for s in packet['scenes']],timing_locked=True,audio_confirmed=True,actual_duration_s=t['duration_s'],target_duration_s=540)
 save(D/'scene_proposals_v5.json',sp)
 md=['# 신혼부부 TOP20 · 정보·비주얼 보강 대본 v5','',f'기존26개 발화 장면은 음성 바이트를 보존했습니다. 새 분석 {delta:.2f}초 추가. 예상 인코딩 길이 {t["duration_s"]:.2f}초.','']
 for s in newscenes:
  md.extend(['## '+s['scene_id']+' · '+s['title'],'',*[''+st['text']for st in s['sentences']],''])
 (D/'script_v5.md').write_text('\n'.join(md),encoding='utf-8')
 t.update(script_sha256=sha(D/'script_v5.md'),source_scene_proposals_v5_sha256=sha(D/'scene_proposals_v5.json'))
 save(D/'locked_timing.json',t)
 final=pcm(full);assert final[:frame*2]==original[:frame*2]and final[frame*2+len(more):]==original[frame*2:]
 assert t['duration_s']>480 and abs(t['brand_outro']['start_s']-t['last_spoken_end_s']-3)<1/RATE
 v={'status':'pcm_reuse_and_provider_alignment_verified','original_audio_sha256':sha(fullpath),'new_audio_sha256':sha(full),'unchanged_original_pcm_frames':len(original)//2,'insert_at_s':insert,'added_scene_ids':t['newly_generated_scene_ids'],'added_duration_s':delta,'duration_s':t['duration_s'],'new_sentences':t['sentence_count']-103,'original_sentences_preserved':103,'all_words':len(allwords),'actual_listening':False,'paid_api_calls':0,'cash_cost_krw':0}
 save(N/'verification.json',v);print(json.dumps(v,ensure_ascii=False))

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['generate','lock']);ap.add_argument('--retry-blocked-once',action='store_true');a=ap.parse_args()
 if a.action=='generate':asyncio.run(generate(a.retry_blocked_once))
 else:lock()
