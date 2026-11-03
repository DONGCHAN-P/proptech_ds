import json,hashlib,wave,array
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
EP=ROOT/'video-agent-studio/episodes/namyangju-wangsuk-20261014'
HERE=Path(__file__).parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
research=read(EP/'research/map-led-v5/analysis.json')
old_geo=read(ROOT/'video/src/namyangju-v2/project.json')
story=read(EP/'writer/map-led-v4/scene_plan.json')
gaps=read(EP/'writer/map-led-v4/image_gap_requests.json')
assets=[{'asset_id':'BGM_DATA_CITY_AMBIENT_V1','kind':'music','file':'namyangju-map-led-v6/data_city_ambient_v1.wav','source_url':'analysis/assemble_v12.py','rights':'original local synthesis; no samples; no attribution required'},
{'asset_id':'PLAN_W1_ORIGINAL','kind':'official_plan','file':'namyangju-map-led-v6/wangsuk1_official_original.jpg','source_url':'https://www.nyj.go.kr/www/contents.do?key=3039','rights':'KOGL3 attribution, no derivatives','immutable':True},
{'asset_id':'PLAN_W2_ORIGINAL','kind':'official_plan','file':'namyangju-map-led-v6/wangsuk2_official_original.jpg','source_url':'https://www.nyj.go.kr/www/contents.do?key=3039','rights':'KOGL3 attribution, no derivatives','immutable':True}]
points=[]
for b in research['blocks']:
    c=b.get('coordinates') or {}
    if isinstance(c.get('lon'),(float,int)) and isinstance(c.get('lat'),(float,int)):
        points.append({'id':b['candidate_id'],'name':b['district']+' '+b['block_id'],'lon':c['lon'],'lat':c['lat'],'status':c.get('status','qualified'),'source_url':b.get('source_url')})
project={'revision':'map-led-production-v6-template','script_revision':'map-led-v4_PENDING','audio_revision':None,'timing_locked':False,'fps':30,'width':1920,'height':1080,'duration_frames':None,'assets':assets,'scenes':[],'narration':[],'captions':{},'music_regions':[],'image_gaps':gaps['requests'],'map':{'bounds':[127.10,37.58,127.235,37.735],'paths':[p for p in old_geo['paths'] if p['kind'] in ['water','road']],'block_points':points},'comparison':None}
rail=read(ROOT/'video/public/namyangju-rail-route-proof-v2/proof_data.json')
project['atlas']={'blocks':research['blocks'],'dimensions':research['dimensions'],'operating_rail':rail['lines'],'operating_stations':rail['stations'],'plan_image_georegistration_complete':False,'planned_facilities':'directional relationships from notice facts; no invented geographic pins or polygons'}
project['script_revision']='script-v4-hook-outside'
project['source_storyboard_revision']=story['revision']
project['comparison']=read(EP/'research/outside-comparisons-v6/comparison.json')
write(ROOT/'video/src/namyangju-map-led-v6/project.json',project)
templates=[]
for s in story['scenes']:
    templates.append({'scene_id':s['scene_id'],'title':s['title'],'message':s['message'],'claim_ids':s['claim_ids'],'source_script_revision':story['revision'],'target_script_revision':'script-v4-hook-outside','timing_locked':False,'from_frame':None,'duration_frames':None,'suggested_visuals':{'M000':['official_plan','registered_map'],'M001':['official_plan','registered_map'],'M002':['registered_map','completion_calendar'],'M003':['rail_status','registered_map','completion_calendar'],'M004':['block_candidate','price_comparison'],'M005':['registered_map','completion_calendar'],'M006':['block_candidate','completion_calendar'],'M007':['price_comparison','registered_map'],'M007B':['outside_locator','outside_price_comparison'],'M008':['block_candidate','registered_map'],'M009':['registered_map','channel_outro']}[s['scene_id']],'asset_selection':'explicit asset_ids per shot; no modulo/random fallback','music_role':'intro_hook' if s['scene_id']=='M000' else 'outro' if s['scene_id']=='M009' else 'none'})
write(HERE/'scene_templates.json',templates)
music=ROOT/'assets/music/data_city_ambient_v1.wav'
with wave.open(str(music)) as w:
    samples=array.array('h',w.readframes(w.getnframes()));music_meta={'duration_s':len(samples)/w.getnchannels()/w.getframerate(),'channels':w.getnchannels(),'sample_rate':w.getframerate(),'sample_width':w.getsampwidth(),'peak_absolute':max(map(abs,samples))/32768}
music_meta.update({'sha256':hashlib.sha256(music.read_bytes()).hexdigest(),'license_file':'assets/music/data_city_ambient_v1.license.json','copied_asset_sha256':hashlib.sha256((ROOT/'video/public/namyangju-map-led-v6/data_city_ambient_v1.wav').read_bytes()).hexdigest(),'actual_listening':False,'new_generation':False})
write(HERE/'music_asset_readiness.json',music_meta)
write(HERE/'music_plan.json',{'status':'provisional_until_new_voice_lock','asset_id':'BGM_DATA_CITY_AMBIENT_V1','intro':{'estimated_duration_s':[20,30],'music_leadin_s':[1,2],'source_offset_s':0,'gain':.55,'duck_gain':.18,'fade_in_s':1,'fade_out_s':2,'hook':'M000 begins after short 1-2s musical establishment; no separate long logo intro'},'body':{'gain':0,'reason':'intro/outro requested; keep map narration clear'},'outro':{'estimated_duration_s':[10,20],'source_offset_s':32,'gain':.48,'duck_gain':.18,'fade_in_s':1,'fade_out_s':2.5,'voice_free_endcard_s':[8,10],'direction_basis':'director latest request; writer suggested 3-5s tail retained as earlier proposal'},'voice_ranges_basis':'actual measured narration intervals after new Jun generation; no generated voice yet','loudness_note':'source peak approx -18.7dBFS; gains provisional, listen and verify final mix before passing','paid_music':False})
print('template prepared; timing locked false; full composition unavailable; music64s',len(points),'qualified guide points')
