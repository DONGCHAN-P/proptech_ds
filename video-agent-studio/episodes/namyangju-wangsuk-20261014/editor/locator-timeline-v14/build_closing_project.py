from pathlib import Path
import json,math,hashlib
EP=Path(__file__).resolve().parents[2];ROOT=EP.parents[2];SRC=ROOT/'video/src/namyangju-v14';PUB=ROOT/'video/public/namyangju-v14';O=EP/'outputs/locator-timeline-v14';N=EP/'narration/region-leaders-v7'
p=json.loads((ROOT/'video/src/namyangju-landuse-v8/project_final.json').read_text(encoding='utf-8'));p['revision']='locator-timeline-v14';p['script_revision']='script-v7-region-leaders';p['duration_frames']=27653;p['audio_revision']='audio-v2+series-hook-v6+region-leaders-v7'
p['narration']=[x for x in p['narration'] if x['scene_id'] not in ['M008','M009']]
for sid,start,nf in [('M008',21636,4956),('M009',26592,761)]:
 raw=json.loads((N/(sid+'.captions_timed.json')).read_text(encoding='utf-8'));cues=[]
 for c in raw['cues']:
  c={**c,'start_frame':math.floor(c['start_s']*30+1e-7),'end_frame':min(nf,math.ceil(c['end_s']*30-1e-7))};assert c['end_frame']>c['start_frame'];cues.append(c)
 p['captions'][sid]=cues
 audio=N/(sid+'.mp3');(PUB/(sid+'_v7.mp3')).write_bytes(audio.read_bytes())
 p['narration'].append({'scene_id':sid,'file':'namyangju-v14/'+sid+'_v7.mp3','from_frame':start,'duration_frames':nf,'sha256':hashlib.sha256(audio.read_bytes()).hexdigest(),'script_revision':'script-v7-region-leaders','audio_revision':'region-leaders-v7'})
text=''.join(json.loads((N/'M008.alignment.json').read_text(encoding='utf-8'))['characters']);a=json.loads((N/'M008.alignment.json').read_text(encoding='utf-8'))
anchors=[('overview','',{}),('north','왕숙1 북부는 B1과 B2',{'region':'north'}),('south','왕숙1 남부의 후보는 B17',{'region':'south'}),('south-school','강남 출근에는 계획된',{'region':'south','southSchool':True}),('a3','왕숙2에서는 A3를',{'region':'w2'}),('a1','A1은 약 6억',{'region':'w2','a1':True}),('conditions','주변 주거와 상권이',{'mode':'summary'})]
shots=[]
for i,(name,key,props) in enumerate(anchors):
 char=text.index(key) if key else 0;frame=21636+math.floor(a['character_start_times_seconds'][char]*30+1e-7);shots.append({'shot_id':'M008-v14-'+name,'scene_id':'M008','char_start':char,'from_frame':frame,'props':props or {'mode':'overview'}})
for i,s in enumerate(shots):s['to_frame']=shots[i+1]['from_frame'] if i+1<len(shots) else 26592;s['duration_frames']=s['to_frame']-s['from_frame']
shots.append({'shot_id':'M009-v14-summary','scene_id':'M009','from_frame':26592,'to_frame':27353,'duration_frames':761,'props':{'mode':'summary'}})
(SRC/'project_v14.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8');(SRC/'closing_shots.json').write_text(json.dumps(shots,ensure_ascii=False,indent=2),encoding='utf-8');(O/'closing_shot_manifest.json').write_text(json.dumps(shots,ensure_ascii=False,indent=2),encoding='utf-8')
def stamp(ms):
 h=ms//3600000;ms%=3600000;m=ms//60000;ms%=60000;return f'{h:02}:{m:02}:{ms//1000:02},{ms%1000:03}'
flat=[]
for n in p['narration']:
 for c in p['captions'][n['scene_id']]:flat.append({'scene_id':n['scene_id'],'from_frame':n['from_frame']+c['start_frame'],'to_frame':n['from_frame']+c['end_frame'],'lines':c['lines']})
flat.sort(key=lambda c:c['from_frame']);srt='\n\n'.join(f"{i+1}\n{stamp(round(c['from_frame']/30*1000))} --> {stamp(round(c['to_frame']/30*1000))}\n"+'\n'.join(c['lines']) for i,c in enumerate(flat))+'\n'
(O/'namyangju_locator_timeline_full_v14.srt').write_text(srt,encoding='utf-8');(O/'timed_captions_v14.json').write_text(json.dumps(flat,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'frames':27653,'cues':len(flat),'closing_shots':shots},ensure_ascii=True))
