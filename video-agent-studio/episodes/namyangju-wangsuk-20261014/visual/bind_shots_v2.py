from pathlib import Path
import json,sys
sys.stdout.reconfigure(encoding='utf-8');root=Path(__file__).parent
plan=json.loads((root/'../writer/shot_plan_video_v2.json').read_text('utf-8'))
manifest=json.loads((root/'assets_v5.json').read_text('utf-8'));assets={a['asset_id']:a for a in manifest['assets']}
meta=json.loads((root/'regional_meta_v3.json').read_text('utf-8'));nodes={n['name']:n for n in meta['place_points']}
MAP='S002_namyangju_regional_osm_v3';P1='S003_wangsuk1_official_plan';P2='S003_wangsuk2_official_plan'
# Explicit, reviewed semantic bindings. No modulo, random, or automatic city rotation.
fixed={1:['PREV_V14'],2:[MAP],3:['NATIVE_five_questions'],4:[MAP],5:['NATIVE_calendar'],6:['NATIVE_block_cards'],7:['AIPREV002'],8:['PHOTO001'],9:[MAP],10:['NATIVE_commute'],11:['PHOTO002'],12:['NATIVE_station_diagram'],13:['NATIVE_station_diagram'],14:['PHOTO009'],15:[MAP],16:['GPT_CONCEPT_FAMILY'],17:[P1,P2],18:[P1],19:[P2],20:['NATIVE_district_size'],21:['NATIVE_stage'],22:[P1,P2],23:['GPT_CONCEPT_COMMUTE'],24:['PREV_V14'],25:['NATIVE_transport_status'],26:['NATIVE_calendar'],27:['NATIVE_gtx_timeline'],28:['NATIVE_transport_status'],29:['NATIVE_calendar'],30:['GPT_CONCEPT_COMMUTE'],31:['NATIVE_commute'],32:['PREV_V14'],33:['NATIVE_stage'],34:[MAP,'NATIVE_jobs_stage'],35:['NATIVE_official_document'],36:['NATIVE_industrial_size'],37:['NATIVE_company_stage'],38:['NATIVE_company_timeline'],39:['GPT_CONCEPT_WORKPLACE'],40:['PHOTO009'],41:['GPT_CONCEPT_FAMILY'],42:['NATIVE_school_document'],43:['NATIVE_school_calendar'],44:['NATIVE_stage'],45:['NATIVE_school_calendar'],46:[P2],47:['NATIVE_we_budget'],48:['GPT_CONCEPT_FAMILY'],49:['AIPREV002'],50:['NATIVE_price_chart_A1'],51:['NATIVE_price_chart_A3'],52:['NATIVE_price_source'],53:['NATIVE_price_conditions'],54:[MAP],55:['NATIVE_statistic'],56:['NATIVE_supply'],57:['NATIVE_five_questions'],58:['NATIVE_status'],59:['PHOTO009','NATIVE_household_questions'],60:['NATIVE_calendar'],61:[P1,P2],62:['NATIVE_five_questions']}
focus={2:[],4:['별내동','다산동','진접읍'],9:['별내동','다산동','진접읍','오남읍','호평동','평내동','화도읍'],15:['다산동','별내동','진접읍'],34:['진건읍','진접읍'],54:['다산동','별내동','진접읍']}
bindings=[];native={}
for shot in plan['shots']:
 n=int(shot['shot_id'].split('-')[-1]);ids=fixed[n];first=ids[0];isnative=first.startswith('NATIVE_');asset=assets.get(first)
 for id in ids:
  if id.startswith('NATIVE_'):native.setdefault(id,{'asset_id':id,'type':'native_semantic_diagram','source_basis':'writer shot purpose/claim_ids + research/facts-v1; editor must build this exact semantic component; no arbitrary stockmedia fallback','actual_place':None})
  else:assert id in assets,id
 kind='native_diagram' if isnative else 'ai_concept' if asset['type']=='ai_concept' else 'official_plan' if first in [P1,P2] else 'real_map' if first==MAP else 'prev_excerpt' if first=='PREV_V14' else 'real_photo'
 reason=shot['purpose'];restrictions=[];label=''
 if kind=='ai_concept':label='AI 개념 이미지 · 실제 왕숙 촬영 아님';restrictions+=['가상 생활 요구의 설명만; 실제 장소·시설·기업 운영 증거 아님']
 if kind=='real_photo':label=asset['actual_place'];restrictions+=['촬영/공표일·저작자·라이선스 출처 유지','역사진으로 지역일자리 운영·왕숙 개통/시설완공 증명 금지']
 if kind=='official_plan':restrictions+=['KOGL3 원본전체정지·무변형; crop/overlay/카메라확대금지','본문의 미검증 특정시설 위치를 도면상의 정확한핀으로 표시 금지']
 if kind=='real_map':restrictions+=['camera focus는 명시한 검증 지역명만; 좌표의 실제위치 유지','산업단지/역출입구/왕숙미래노선 정확한pin 미검증이므로 표시 금지']
 if kind=='prev_excerpt':label='전편: 광교·동탄';restrictions+=['원본전편 음소거 발췌·기존출처 유지; 남양주 현재영상처럼표현금지']
 if n in [12,13]:reason+='; 정확한 두 역 좌표 미검증으로 별내역(8호선·경춘선)/별내별가람역(4호선) 관계 도식으로 교체';restrictions+=['평내/화도 등 임의 camera 또는 station pin 사용금지','도식은 노선관계이며 거리축척 지도 아님']
 if n in [25,28]:reason+='; 검증되지 않은 미래노선 선형 대신 운영/계획/공구추진 상태 도식';restrictions+=['임의 노선선형·정밀 역위치·구간완료 주장 금지']
 if n in [34,37]:reason+='; 산단 정밀 좌표 미검증, 지명 수준과 진행단계로 한정';restrictions+=['진관·금곡·광릉 산단 exact pin 금지','남양주 북부 지역명은 해당 산업단지 위치 확정 증거 아님']
 if n==46:restrictions+=['왕숙2 전체계획도는 지구 설명만; WE드림파크 정확한 위치/완공 증거 아님']
 if n==48:reason+='; 왕숙 첫입주 가족생활에 맞는 실제가족사진 미확보, 기존 다산초 오인 대신 가상가족으로 명시 교체';restrictions+=['PHOTO010 기존다산초 사용금지; 왕숙 신설학교로 보이지 않게 함']
 if n==60:reason+='; 확인 안 된 기존 시간표PNG 대신 명시적 3달력 native도식';restrictions+=['랜덤 가족/사무실 이미지로 교체금지']
 fallback='NATIVE_'+('station_diagram' if n in [8,11,12,13,14,40,59] else 'school_calendar' if shot['chapter_id']=='S006' else 'commute' if shot['chapter_id']=='S004' else 'jobs_stage' if shot['chapter_id']=='S005' else 'five_questions' if shot['chapter_id'] in ['S001','S008'] else 'price_conditions' if shot['chapter_id']=='S007' else 'district_size')
 native.setdefault(fallback,{'asset_id':fallback,'type':'native_semantic_diagram','source_basis':'same shot facts/purpose; no unrelated media','actual_place':None})
 entry={'shot_id':shot['shot_id'],'chapter_id':shot['chapter_id'],'requested_type':shot['type'],'render_type':kind,'asset_ids':ids,'actual_place':asset.get('actual_place') if asset else None,'reason':reason,'claim_ids':shot['claim_ids'],'mandatory_label':label,'motion_allowed':'full_original_static_only' if kind=='official_plan' else 'bounded_camera_and_staged_verified_labels' if kind=='real_map' else 'native_semantic_frame_animation' if kind=='native_diagram' else 'original_excerpt_only' if kind=='prev_excerpt' else 'still_motion_modest_pan_zoom; preserve AI or photo-date/source labels','fallback_ids':[fallback],'restrictions':restrictions}
 if n in focus:entry['camera_focus_points']=[{'name':name,'lon':nodes[name]['lon'],'lat':nodes[name]['lat'],'osm_id':nodes[name]['osm_id'],'meaning':'지역명 기준점·역/사업장 좌표 아님'} for name in focus[n]]
 if kind=='real_map':entry['geography_file']='visual/regional_geo_v4.geojson';entry['overview_bounds']=meta['bounds']
 bindings.append(entry)
assert len(bindings)==62 and len({x['shot_id'] for x in bindings})==62
result={'revision':'shot-asset-binding-v2','inputs':['writer/shot_plan_video_v2.json','visual/assets_v5.json','visual/regional_meta_v3.json'],'selection_rule':'exact shot_id lookup only; random/modulo selection forbidden; missing id -> explicit same-subject fallback or fail closed','bindings':bindings,'native_asset_definitions':list(native.values()),'unused_real_photos':['PHOTO010','PHOTO015','PHOTO016'],'unused_note':'사진6개 전부 사용을 강제하지 않음. 기존학교·2024행사를 왕숙학교·일반가족·현재시설로 대신 사용하지 않음.','validation':'62shot unique lookup; all file assets manifest-verified; native ids explicitly defined; no unverified exact station/industry pin'}
(root/'shot_asset_binding_v2.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf-8')
print('62 semantic shot bindings verified; diagram substitutions:',[x['shot_id'] for x in bindings if x['requested_type'] in ['real_map','real_photo','ai_concept'] and x['render_type']=='native_diagram'])
