"""Freeze the approved script and prepare provisional visual-only production inputs."""
from pathlib import Path
import json, hashlib, shutil, re, math, csv
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[5]
EP=ROOT/'video-agent-studio/episodes/regional-price-recovery-20261022'
OUT=EP/'outputs/literature-visual-v1'; P=OUT/'project'; D=EP/'director/literature-visual-v1'
SCRIPT_SHA='5f40c29d4a3e0ef5255ade11eaa63cb04c8093e2c3d1d0296873126707a26d9b'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def dump(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stamp(t):
    ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
def display(text):
    for a,b in [('59제곱미터','59㎡'),('4.1퍼센트','4.1%'),('천 채','1,000채'),('팔백 채','800채'),('이백 채','200채')]:text=text.replace(a,b)
    text=re.sub(r'(\d{4}년) (\d분기)',lambda m:m.group(1)+'\u00a0'+m.group(2),text)
    return text
def split_caption(text):
    sentences=re.split(r'(?<=[.?!])\s+',text);parts=[]
    for sentence in sentences:
        words=sentence.split(' ');line=''
        for word in words:
            if len(line)+len(word)+1>68 and line:parts.append(line);line=word
            else:line=(line+' '+word).strip()
        if line:
            if len(line)<12 and parts and len(parts[-1])+len(line)<80:parts[-1]+=' '+line
            else:parts.append(line)
    return parts

OUT.mkdir(parents=True,exist_ok=True);D.mkdir(parents=True,exist_ok=True)
source=EP/'outputs/literature-video-v1'
assert sha(source/'내레이션_초안.md')==SCRIPT_SHA
state=read(EP/'state.json')
if not (D/'state_before.json').exists():dump(D/'state_before.json',state)
protected={state['script_file']:state['script_sha256'],state['production_review_video']:state['production_render']['video_sha256'],'reports/서울 경기 집값 격차의 복합 원인.md':state['literature_report_sha256'],'config/current_video.json':sha(ROOT/'config/current_video.json')}
if (D/'protected.json').exists():protected=read(D/'protected.json')
else:dump(D/'protected.json',protected)
for path,digest in protected.items():assert sha(ROOT/path)==digest,path
for name in ['compositions','assets','assets/fonts','checks','previews']:(P/name if name in ['compositions','assets','assets/fonts'] else OUT/name).mkdir(parents=True,exist_ok=True)
old=EP/'outputs/production-v1-jun/project/assets'
for f in (old/'fonts').glob('*.woff2'):shutil.copy2(f,P/'assets/fonts'/f.name)
shutil.copy2(old/'gsap.min.js',P/'assets/gsap.min.js')
reusable=read(EP/'outputs/production-v1-jun/reusable_assets/manifest.json')
dump(OUT/'reused_assets.json',reusable)
for a in reusable['assets']:
    if a['asset_id'].startswith('existing_emoji'):
        src=ROOT/a['actual_file'];assert sha(src)==a['sha256'];shutil.copy2(src,P/'assets'/src.name)
dump(P/'hyperframes.json',{'paths':{'blocks':'compositions','components':'compositions/components','assets':'assets'},'authoringSkill':'general-video','registry':'https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry'})
dump(P/'package.json',{'name':'regional-literature-visual-v1','private':True,'type':'module','scripts':{'check':'npx.cmd --no-install hyperframes check','preview':'npx.cmd --no-install hyperframes preview --background'}})
scenes=read(source/'장면표.json')['scenes'];timeline=[];cues=[];cursor=0
titles=['같은 수도권, 다른 가격 흐름','1. 인구와 가구','2. 거주 방식','3. 재건축 이주','4. 공급의 시점','5. 일자리 연결','6. 선택지','7. 데이터로 확인할 것']
for scene,title in zip(scenes,titles):
    local=3.0;beats=[]
    for i,paragraph in enumerate(scene['narration_text'].split('\n\n')):
        duration=math.ceil(max(6,len(paragraph)/8.25+1.0)*30)/30
        beat={'id':f'{scene["scene_id"]}-P{i+1}','index':i,'start':local,'duration':duration,'end':local+duration,'narration_text':paragraph,'display_text':display(paragraph)}
        parts=split_caption(beat['display_text']);weights=[len(x) for x in parts];used=0
        for j,(part,weight) in enumerate(zip(parts,weights)):
            start=local+duration*used/sum(weights);used+=weight;end=local+duration*used/sum(weights)
            cues.append({'scene_id':scene['scene_id'],'beat_id':beat['id'],'text':part,'start':cursor+start,'end':cursor+end,'global_start':cursor+start+5,'global_end':cursor+end+5})
        beats.append(beat);local+=duration
    duration=math.ceil((local+(3 if scene['scene_id']=='L008' else 1))*30)/30
    beats[-1]['visual_duration']=duration-beats[-1]['start']
    timeline.append({'scene_id':scene['scene_id'],'title':title,'start':cursor,'duration':duration,'end':cursor+duration,'beats':beats,'claim_ids':scene['claim_ids']});cursor+=duration
dump(P/'timing.json',{'revision':'literature-visual-v1','provisional':True,'timing_locked':False,'script_sha256':SCRIPT_SHA,'body_duration':cursor,'story_end':cues[-1]['end'],'last_caption_end':cues[-1]['end'],'visual_hold_after_last_caption':3,'intro_duration':5,'outro_duration':10,'total_duration':cursor+15,'scenes':timeline,'captions':cues,'basis':'text reading estimate only; not actual Jun or speech alignment'})
dump(P/'assets/claims.json',read(source/'인용근거.json'))
with (ROOT/'analysis/housing_growth_2006/full_history_v1/chart_source.csv').open(encoding='utf-8-sig',newline='') as f:rows=[r for r in csv.DictReader(f) if r['region'] in ('서울','경기')]
dump(P/'assets/price_data.json',rows)
(OUT/'previews/literature_visual_v1.srt').write_text('\n\n'.join(f'{i+1}\n{stamp(c["global_start"])} --> {stamp(c["global_end"])}\n{c["text"]}' for i,c in enumerate(cues))+'\n',encoding='utf8')
approval={'id':'regional-literature-script-v1-20261023','status':'approved_by_explicit_reply','basis':'이 대본으로 화면 제작 진행','script_sha256':SCRIPT_SHA,'scope':'8-scene visuals and local visual-review render; voice generation remains on hold; no upload','at_utc':datetime.now(timezone.utc).isoformat()}
dump(D/'script_approval.json',approval)
dec=read(EP/'decisions.json')
item=next(d for d in dec['decisions'] if d['id']==approval['id']);item.update(approval)
dump(EP/'decisions.json',dec)
state.update(stage='literature_visual_v1_in_production',next_script_status='approved_for_visual_production',literature_visual_script_approval=(D/'script_approval.json').relative_to(ROOT).as_posix(),new_render_authorized_at_this_stage=True,literature_visual_output=OUT.relative_to(ROOT).as_posix(),updated_at=approval['at_utc'])
assert state['budget_status']=='voice_generation_deferred_by_user';dump(EP/'state.json',state)
pre=read(EP/'episode_preflight_literature_video_v1.json');pre['approvals']['script'].update(status='approved_by_explicit_reply',decision_id=approval['id'],artifact_hashes={'내레이션_초안.md':SCRIPT_SHA});pre['status']='visual_production_approved_voice_hold';dump(EP/'episode_preflight_literature_visual_v1.json',pre)
print(json.dumps({'status':'prepared','scenes':len(timeline),'captions':len(cues),'body_duration':cursor,'total_duration':cursor+15,'voice_generated':False,'script_sha256':SCRIPT_SHA},ensure_ascii=False))
