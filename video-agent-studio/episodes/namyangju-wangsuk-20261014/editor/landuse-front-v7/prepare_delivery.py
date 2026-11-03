import json,hashlib,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[5];E=R/'video-agent-studio/episodes/namyangju-wangsuk-20261014';H=Path(__file__).parent;O=E/'outputs/front-review-v7';P=R/'video/public/namyangju-landuse-v7'
def read(x):return json.loads(x.read_text(encoding='utf-8-sig'))
def save(x,v):x.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(x):return hashlib.sha256(x.read_bytes()).hexdigest()
p=read(R/'video/src/namyangju-landuse-v7/project.json');caps=[];srt=[]
def stamp(f):
 ms=round(f/30*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
for n in p['narration']:
 for c in p['captions'][n['scene_id']]:
  start=n['from_frame']+c['start_frame'];end=n['from_frame']+c['end_frame'];assert end<=13087
  caps.append(dict(scene_id=n['scene_id'],id=c['id'],text='\n'.join(c['lines']),startMs=round(start/30*1000),endMs=round(end/30*1000),timestampMs=None,confidence=None,start_frame=start,end_frame=end))
  srt.append(f'{len(caps)}\n{stamp(start)} --> {stamp(end)}\n'+ '\n'.join(c['lines'])+'\n')
(O/'namyangju-landuse_front_v7.srt').write_text('\n'.join(srt),encoding='utf-8');save(O/'captions.json',caps)
cuts=[(0,'intro_hook'),(669,'whole_official_plans'),(1500,'macro_regions'),(2009,'south_housing_jobs'),(2607,'industry_polygon_layer'),(2798,'planned_company_identity'),(4544,'operating_rail_and_plan_context'),(7792,'84_type_price_and_parcels'),(8804,'smaller_type_conditions'),(9306,'84_type_comparison_return'),(9892,'north_school_context'),(10280,'south_school_context'),(10628,'w2_a1_school_context'),(10772,'w2_south_single_pan'),(11183,'north_school_dates'),(11605,'south_school_dates'),(11891,'w2_school_dates'),(12296,'w2_south_held_revisit')]
bindings=[dict(id=f'V7-{i+1:02}',start_frame=a,end_frame=cuts[i+1][0] if i+1<len(cuts) else 13087,meaning=m) for i,(a,m) in enumerate(cuts)]
save(O/'scene_camera_manifest.json',{'revision':'landuse-front-v7','front_only':True,'end_frame':13087,'duration_s':13087/30,'fps':30,'narration':p['narration'],'visual_layers':bindings,'camera_policy':'held plan framing; W2 south pan only once at10772 for45frames, revisit12296 held; no per-cue overview zoom reset','captions':'one global fixed130px white container; empty during natural pauses, never unmounted','boards':{x:read(P/(x+'_board.json'))['cameras'] for x in ['macro','w1_north','w1_south','w2']}})
files=[P/x for x in ['macro_board.json','w1_north_board.json','w1_south_board.json','w2_board.json','woori_group_ci_official.png','shinhan_logo.svg']]
save(O/'source_manifest.json',{'script_revision':'script-v4-hook-outside','audio_revision':'audio-v2','source_script_sha256':'d816c5ba4341ddaafd4f3f3db6585873a519e1577d865dbf332d183925d4c2da','assets':[{'path':str(x.relative_to(R)).replace('\\','/'),'sha256':sha(x)} for x in files],'audio_reuse':[{'scene_id':n['scene_id'],'file':n['file'],'sha256':n['sha256']} for n in p['narration']],'new_paid_calls':0,'new_tts':False,'rights':{'official_original_plans':'Existing KOGL3 originals shown full-fit unchanged in intro/whole-plan shot. No annotation overlays on original bitmap.','landuse_boards':'New factual reconstruction from published LH plan-local positions; source artwork not used as backdrop. Not WGS84, survey, cadastral or built-state geometry.','macro':'New factual source-local schematic from city_business_p6. Adjacent area names directional only; not exact station positions.','woori':'Official Woori Financial Group CI, raw PNG unchanged; viewport trims blank margins only. See woori_group_ci_source.json.','shinhan':'Official group CI with explicit Shinhan Bank planned-company context. See research source_rights.','kakao':'Text name only; no CI asset used due official MediaKit commercial-use restriction.'},'validation_limits':['actual listening and continuous playback not performed','new video is front only; no full14minute merge']})
shutil.copy2(E/'research/landuse-v7/source_rights.json',O/'research_source_rights.json')
shutil.copy2(E/'visual/landuse-v7/assets.json',O/'visual_asset_manifest.json')
shutil.copy2(R/'video-agent-studio/guides/지역_상세지도와_의미단위_자막.md',O/'지역_상세지도와_의미단위_자막.md')
save(H/'delivery_preparation.json',{'front_cues':len(caps),'chapters':len(p['narration']),'visual_layers':len(bindings),'duration_frames':13087,'render_pending':True})
print('front captions',len(caps),'chapters',len(p['narration']),'visual layers',len(bindings))
