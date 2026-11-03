import json, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
EP=ROOT/'video-agent-studio/episodes/namyangju-wangsuk-20261014'
RESEARCH=EP/'research/rail-route-proof-v1'
PUBLIC=ROOT/'video/public/namyangju-rail-route-proof-v1'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,d): p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
data=read(RESEARCH/'data.json')
name_ids={'별내역':'byeollae','별내별가람역':'byeolgaram','오남역':'onnam','진접역':'jinjeop','다산역':'dasan','불암산역':'bulamsan'}
stations={}
for station in data['stations']:
    station=dict(station)
    station['osm_node_id']=station['id']
    station['id']=name_ids[station['name']]
    stations[station['id']]=station
data['stations']=list(stations.values())
for line in data['lines']:
    if len(line.get('points',[]))>1: line['segments']=[line['points']]
    if line['id']=='eight':
        # Display passenger operation only, excluding actual turnback track north of terminus.
        kept=[]
        station=stations['byeollae']
        for segment in line['segments']:
            if len(segment)<20: continue
            i=min(range(len(segment)),key=lambda j:(segment[j][0]-station['lon'])**2*.626+(segment[j][1]-station['lat'])**2)
            kept.append(segment[i:] if segment[0][1]>segment[-1][1] else segment[:i+1])
        line['segments']=kept
        line['display_note']='Actual track clipped to nearest existing track point at Byeollae passenger terminus; turnback tracks excluded. No invented connector.'
project=read(ROOT/'video/src/namyangju-v2/project.json')
data['captions']=[dict(c,start_s=max(0,c['start_s']+74-94),end_s=min(80,c['end_s']+74-94)) for c in project['captions']['S002'] if c['end_s']+74>94 and c['start_s']+74<174]
data['background']=[]
for p in project['paths']:
    if p['kind'] not in ('road','water'): continue
    if not any(127.065<q[0]<127.225 and 37.59<q[1]<37.75 for q in p['points']): continue
    data['background'].append(dict(p,source='existing regional OSM map visual-v4'))
for e in read(RESEARCH/'raw_osm.json')['elements']:
    if e.get('type')!='way' or 'geometry' not in e: continue
    tags=e.get('tags',{})
    kind='road' if 'highway' in tags else 'building' if 'building' in tags else 'water' if 'waterway' in tags else 'park' if tags.get('leisure')=='park' else None
    if kind is None: continue
    pts=[[g['lon'],g['lat']] for g in e['geometry']]
    if not any(127.065<p[0]<127.225 and 37.59<p[1]<37.75 for p in pts): continue
    data['background'].append({'kind':kind,'points':pts,'osm_way_id':e['id'],'name':tags.get('name','')})
data['railBounds']=[127.066,37.60,127.223,37.744]
data['byeollaeBounds']=[127.100,37.623,127.152,37.674]
data['dasanBounds']=[127.135,37.614,127.165,37.634]
if data.get('commute'):
    data['commute']['station']['name']='별내역 4번출구 인근'
    data['commute']['origin_display_note']='단지 대표 진입도로 지점 · 현장 출입구 미확인'
    data['commute']['destination_display_note']='실제 출구 인근 도로점까지 · 마지막 보도 통행 미확인'
    data['commute']['bounds']=[127.113,37.639,127.140,37.666]
    data['commute']['busStops']=[dict(name='탑승 정류장',lon=data['commute']['boarding']['point'][0],lat=data['commute']['boarding']['point'][1]),dict(name='하차 정류장',lon=data['commute']['alighting']['point'][0],lat=data['commute']['alighting']['point'][1])]
data['sourceNote']='역·선로·도로: OSM / 버스: GBIS / 연구 확인일 2026.10.15'
write(PUBLIC/'proof_data.json',data)
write(Path(__file__).parent/'input_manifest.json',{'original_master':'outputs/video-review-v3/namyangju-wangsuk_v3.mp4','script_revision':'script-v2','audio_revision':'audio-v1','source_start_s':94,'source_end_s':174,'duration_s':80,'research_revision':data.get('revision'),'research_sha256':hashlib.sha256((RESEARCH/'data.json').read_bytes()).hexdigest(),'background_way_count':len(data['background']),'caption_timing_basis':'existing_character_weight_estimate_NOT_forced_alignment','paid_generation':False,'modified_full_master':False})
print('prepared',len(data['background']),'background ways',len(data['captions']),'captions')
