import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
EP=ROOT/'video-agent-studio/episodes/namyangju-wangsuk-20261014'
OUT=EP/'outputs/video-review-v4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
original=ROOT/'video/src/namyangju-v2/project.json'
data=read(original)
semantic=read(EP/'writer/semantic-captions-v4/captions.json')
assert set(semantic['chapters'])==set(data['captions'])
data['captions']=semantic['chapters']
remotion=[];srt=[];critical_frames=[]
def stamp(seconds):
    ms=round(seconds*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'
for chapter in data['chapters']:
    cues=data['captions'][chapter['scene_id']]
    for i,cue in enumerate(cues):
        assert len(cue['lines'])<=2 and max(map(len,cue['lines']))<=36
        assert cue['end_s']>cue['start_s']>=0
        if i:assert abs(cues[i-1]['end_s']-cue['start_s'])<.00001
        assert cue['end_s']<=chapter['frames']/30+.001
        start=chapter['start_s']+cue['start_s'];end=chapter['start_s']+cue['end_s']
        text='\n'.join(cue['lines'])
        remotion.append({'text':text,'startMs':round(start*1000),'endMs':round(end*1000),'timestampMs':None,'confidence':None})
        srt.append(f'{len(srt)+1}\n{stamp(start)} --> {stamp(end)}\n{text}\n')
        if any(x in cue['text'].replace(' ','') for x in ['8만114','1만5천955','4억9천304','120만','6만4천159']):
            critical_frames.append({'id':cue['id'],'frame':round((start+end)*15),'global_s':(start+end)/2,'lines':cue['lines']})
write(ROOT/'video/src/namyangju-v4/project.json',data)
write(OUT/'captions.remotion.json',remotion)
write(OUT/'semantic_caption_keyframes.json',critical_frames)
(OUT/'namyangju-wangsuk_v4.srt').write_text('\n'.join(srt),encoding='utf-8')
das=read(EP/'research/dasan-context-v2/context.json');bye=read(EP/'research/region-context-v4/byeollae_context.json')
preferred_das=[('다산역경기행복주택아파트',-200,-24),('다산자이 IVY PLACE',110,-36),('다산역자연앤푸르지오',130,20),('현대프리미엄아울렛 스페이스원',140,-20),('다산중앙공원',85,0),('다산선형공원',-310,20)]
preferred_bye=[('별내 체육공원',-190,-12),('남양주별내 대원칸타빌',150,18),('별내동익미라벨아파트',-180,-10),('별내역파라곤스퀘어',130,0)]
for ctx,preferred,title in [(das,preferred_das,'다산 생활권'),(bye,preferred_bye,'별내 생활권')]:
    ctx['region_title']=title;ctx['display_labels']=[]
    for name,dx,dy in preferred:
        matches=[f for f in ctx['features'] if f['name']==name]
        if not matches:continue
        feature=min(matches,key=lambda f:(f['lon']-ctx['station']['lon'])**2*.626+(f['lat']-ctx['station']['lat'])**2)
        ctx['display_labels'].append(dict(feature,dx=dx,dy=dy))
write(ROOT/'video/public/namyangju-v4/comparison_contexts.json',{'revision':'region-context-v4','contexts':[das,bye]})
manifest={'script_revision':'script-v2','audio_revision':'audio-v1','source_project_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'semantic_revision':semantic['revision'],'semantic_sha256':hashlib.sha256((EP/'writer/semantic-captions-v4/captions.json').read_bytes()).hexdigest(),'semantic_cue_count':len(remotion),'critical_caption_frames':critical_frames,'same_chapter_audio_paths':True,'same_chapter_frames':True,'proof_visual_only_insert_s':[94,174],'other_context_shot':'V2-054','context_regions':['Dasan','Byeollae'],'timing_alignment':'semantic boundaries and character_weight_estimate; NOT forced alignment','paid_generation':False,'full_prior_master_preserved':True}
write(Path(__file__).parent/'input_manifest.json',manifest)
print('v4 data prepared',len(remotion),'semantic cues',len(critical_frames),'key captions')
