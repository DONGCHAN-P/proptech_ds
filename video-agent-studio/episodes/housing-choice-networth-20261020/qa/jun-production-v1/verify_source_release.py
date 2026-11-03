import sys,json,hashlib,re,html,math
from pathlib import Path
from html.parser import HTMLParser
from datetime import datetime,timezone
sys.dont_write_bytecode=True
Q=Path(__file__).resolve().parent;E=Q.parent.parent;R=E.parents[2];O=E/'outputs/jun-production-v1';OLD=E/'outputs/private-production-v3';REL=E/'outputs/jun-release-v1'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p):return dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size)
def norm(s):return re.sub(r'\s+','',s)
def table(s,n):
 m=re.search(r'\bconst '+n+r'\s*=\s*([\[{].*?[\]}])\s*;',s,re.S)
 return (m,json.loads(m[1])) if m else (None,None)
def visual_skeleton(s):
 s=re.sub(r'<audio\b[^>]*>.*?</audio>','',s,flags=re.S)
 s=re.sub(r'<p\b(?=[^>]*\bclass="clip cue")[^>]*>.*?</p>','__CAPTION__',s,flags=re.S)
 s=re.sub(r'(<\w+\b[^>]*\bdata-start="[^>]*>)',lambda m:re.sub(r'data-(?:start|duration)="[^"]*"','__TIME__',m[0]),s)
 for n in ['C','S','ANCHORS','SPANS']:
  m,_=table(s,n)
  if m:s=s[:m.start(1)]+'{}'+s[m.end(1):]
 return s
class CaptionParser(HTMLParser):
 def __init__(self):super().__init__();self.rows=[];self.active=None
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='p' and a.get('class')=='clip cue':self.active=dict(attrs=a,text='')
 def handle_data(self,data):
  if self.active is not None:self.active['text']+=data
 def handle_endtag(self,tag):
  if tag=='p' and self.active is not None:self.rows.append(self.active);self.active=None
def sec(s):
 h,m,s=s.replace(',','.').split(':');return int(h)*3600+int(m)*60+float(s)
def main():
 checks=[]
 def ck(n,b,**e):checks.append(dict(check=n,pass_=bool(b),**e))
 plan=read(O/'render_plan.json');edl=read(O/'assembly_edl.json');nt=read(E/'narration/jun-production-v1/final_timing.json');bboxp=O/'preview/bbox_report.json';bbox=read(bboxp)
 oldlock=read(Q/'cue_text_lock.json');nr={q['id']:q for c in nt['chapters'] for q in c['cues']};globalcues=[];sources=[];maxzooms=[]
 for ch in plan['chapters']:
  n=ch['chapter'];folder=O/ch['project'];hp=folder/'index.html';tp=folder/'timing.json';s=hp.read_text(encoding='utf-8');t=read(tp);prior=(OLD/ch['project']/'index.html').read_text(encoding='utf-8');p=CaptionParser();p.feed(s)
  ck(f'CH{n} visual content/CSS/JS conserved',visual_skeleton(s)==visual_skeleton(prior))
  ck(f'CH{n} actual narrator PCM',sha(folder/'assets/narration.wav')==nt['chapters'][n-1]['audio_sha256'])
  ck(f'CH{n} native cue node count',len(p.rows)==len(t['cues']))
  for node,c in zip(p.rows,t['cues']):
   q=nr[c['id']];a=node['attrs'];start=float(a['data-start']);end=start+float(a['data-duration'])
   expectedend=min(c['end_s']+.08,t['cues'][t['cues'].index(c)+1]['start_s'] if t['cues'].index(c)+1<len(t['cues']) else t['total_seconds'],t['last_speech_end_s'] if n==10 else t['total_seconds'])
   if n==1 and c['paragraph']==0:expectedend=min(expectedend,edl['hook_cut_s'])
   ck(c['id']+' source text/native bounds',norm(node['text'])==norm(q['text']) and c['display_lines']==q['display_lines'] and c['start_s']==q['start_s'] and c['end_s']==q['end_s'] and abs(start-c['start_s'])<1e-6 and abs(end-expectedend)<1e-6 and a['data-track-index']=='9')
   off=next(x['global_offset_s'] for x in edl['offset_map'] if x['chapter']==n and x['local_start_s']<=start<x['local_end_s'])
   gs,ge=start+off,c['end_s']+off
   ck(c['id']+' outside brand intervals',not any(gs<z['end_s']-1e-6 and ge>z['start_s']+1e-6 for z in edl['caption_hidden_intervals']))
   globalcues.append(dict(id=c['id'],start=gs,end=ge,text=c['text'],lines=c['display_lines']))
  b=next(x for x in bbox['checked_chapters'] if x['chapter']==n)
  ck(f'CH{n} current producer BBox pins',sha(hp)==b['html_sha256'] and sha(tp)==b['timing_sha256'] and b['paused'] and all(x['status']=='loaded' for x in b['fonts']))
  assets=[]
  for f in (OLD/ch['project']/'assets').rglob('*'):
   if f.is_file() and f.name not in ['narration.wav','music-bed.wav']:
    current=folder/'assets'/f.relative_to(OLD/ch['project']/'assets');ck('asset '+str(current),sha(current)==sha(f));assets.append(pin(current))
  ck(f'CH{n} speech speed unchanged',not re.search(r'data-playback-rate|timeScale\(|atempo',s))
  sources.append(dict(chapter=n,HTML=pin(hp),timing=pin(tp),unchanged_visual_assets=assets,scene_count=len(t['scenes']),cue_count=len(t['cues']),source_BBox_text_checks=b['text_checks']))
  _,anchors=table(s,'ANCHORS')
  for target,delay,scale in ([('서울 약',.35,1.05),('경기 6.6%',.35,1.05),('인천 4.0%',.35,1.05)] if n==2 else [('10년 동안 갚은 원금',.7,1.4)] if n==5 else [('계속거주 평가',.4,1.03)] if n==7 else []):
   local=anchors[target]+delay;off=next(x['global_offset_s'] for x in edl['offset_map'] if x['chapter']==n and x['local_start_s']<=local<x['local_end_s']);frame=round((local+off)*30)
   maxzooms.append(dict(chapter=n,anchor=target,scale=scale,source_local_s=local,global_frame=frame,global_time_s=frame/30,basis='source GSAP scale peak: anchor + start delay + tween duration; closest actual 30fps frame'))
 sp=O/'captions_measured.srt';blocks=sp.read_text(encoding='utf-8-sig').strip().split('\n\n');sr=[]
 for block in blocks:
  lines=block.splitlines();start,end=lines[1].split(' --> ');sr.append(dict(number=int(lines[0]),start=sec(start),end=sec(end),text='\n'.join(lines[2:])))
 ck('all206 final SRT vs exact native global offsets',len(sr)==206 and all(x['number']==i+1 and abs(x['start']-q['start'])<=.000501 and abs(x['end']-q['end'])<=.000501 and norm(x['text'])==norm(q['text']) for i,(x,q) in enumerate(zip(sr,globalcues))))
 ck('all cue ordering',all(y['start']>=x['end'] for x,y in zip(sr,sr[1:])))
 ck('all50 scenes',sum(x['scene_count'] for x in sources)==50)
 ck('clean brand and final tail',edl['intro_video_frames']==150 and edl['outro_video_frames']==300 and 3-1e-6<=edl['outro_delay_from_last_speech_s']<3+1/30+1e-6)
 receipt=read(REL/'release_inputs_receipt.json');meta=read(REL/'metadata_measured.json');description=(REL/'description_measured.md').read_text(encoding='utf-8');choicep=E/'director/launch-and-jun-v1/thumbnail_choice.json';choice=read(choicep)
 for key,filename in [('metadata','metadata_measured.json'),('description','description_measured.md'),('thumbnail','thumbnail.png')]:ck('release '+key+' hash',sha(REL/filename)==receipt[key+'_sha256'])
 ck('user selected TH003 exact thumbnail',choice['asset_id']==meta['thumbnail_asset_id']=='TH003' and choice['user_selected'] and sha(REL/'thumbnail.png')==sha(E/choice['source']))
 ck('private metadata script/timing',meta['visibility']=='private' and not meta['published'] and not meta['scheduled'] and meta['voice']=='ElevenLabs Jun' and meta['timing_sha256']==sha(E/'narration/jun-production-v1/final_timing.json')==plan['caption_timing_sha256'] and meta['script_sha256']==nt['script_sha256'])
 for m in meta['chapters']:
  off=min(x['global_start_s'] for x in edl['segments'] if x.get('chapter')==m['chapter']);stamp=m['timestamp'].split(':');stamp=int(stamp[0])*60+int(stamp[1]);ck('metadata chapter '+str(m['chapter']),abs(m['start_s']-off)<1e-8 and stamp==int(off+1e-7) and (m['timestamp']+' '+m['title']) in description)
 ck('BBox current sampled pass',bbox['status']=='sampled_bbox_pass' and not bbox['errors'] and not bbox['findings'])
 failures=[x for x in checks if not x['pass_']]
 d=dict(status='pass' if not failures else 'required_review',checks_count=len(checks),failures=failures,checks=checks,checked_at=datetime.now(timezone.utc).isoformat(),script_sha256=nt['script_sha256'],timing=pin(E/'narration/jun-production-v1/final_timing.json'),EDL=pin(O/'assembly_edl.json'),SRT=pin(sp),metadata=pin(REL/'metadata_measured.json'),description=pin(REL/'description_measured.md'),thumbnail=pin(REL/'thumbnail.png'),thumbnail_choice=pin(choicep),all206_cues=globalcues,source_inputs=sources,source_BBox_receipt=pin(bboxp),producer_BBox_reused_with_current_input_SHA_checks=True,independent_DOM_measurement_this_round=False,source_all50_scenes_and206_nodes_verified=True,actual_encoded_frame_inspection=False,actual_listening=False,continuous_playback=False,financial_model_recalculated=False,maximum_scale_samples_to_inspect=maxzooms)
 (Q/'source_release_review.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(status=d['status'],checks=len(checks),failures=failures,maxscale_frames=maxzooms),ensure_ascii=False))
if __name__=='__main__':main()
