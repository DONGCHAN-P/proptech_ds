import json,pathlib,re,math
p=pathlib.Path(__file__).parent;ep=p.parent.parent;p.mkdir(exist_ok=True)
analysis=json.loads((ep/'research/map-led-v5/analysis.json').read_text(encoding='utf-8'));download=json.loads((ep/'research/map-led-v5/pdf_downloads.json').read_text(encoding='utf-8'))
url={z['file']:z['url'] for z in download}
main={b['candidate_id']:b for b in analysis['blocks']}
counts={'W1-A1':{'59':629},'W1-A2':{'46':57,'55':344},'W1-A24':{'55':390},'W1-B17':{'74':210,'84':281},'W2-A1':{'59A':350,'59B':188,'74A':73,'84A':201},'W2-A3':{'59':390,'74':102,'84':194}}
# B17 type count is checked below against source before use; do not assume sums alone are evidence.
counts['W1-B17']={'74':128,'84':363}
program={'housing':'공동주택 용지','housing_low':'단독주택 용지','school':'교육시설 계획','park':'공원·녹지 계획','jobs':'자족시설 용지','industry':'산업시설 용지','commerce':'상업시설 용지','commercial':'상업시설 용지','mixed':'주상복합 용지','public':'공공복합 용지','public_complex':'공공복합 용지','work':'업무시설 용지','water':'하천','road':'도로 계획','rail_corridor':'철도시설 계획'}
districts={'w1_north':'왕숙1','w1_south':'왕숙1','w2':'왕숙2'}
entries=[];anchors=[]
mainmap={'w1_a1':'W1-A1','w1_a2':'W1-A2','w1_a24':'W1-A24','w1_b17':'W1-B17','a1':'W2-A1','a3':'W2-A3'}
for board,district in districts.items():
 data=json.loads((ep/f'visual/landuse-v7/{board}_board.json').read_text(encoding='utf-8'))
 for feature in data['features']:
  id=feature['id'];kind=feature['type'];label=feature.get('label','');meaning=program.get(kind,'계획시설')
  candidate=mainmap.get(id)
  if board!='w2' and id in ['a1','a3']:candidate=None
  if board=='w2' and id.startswith('w1_'):candidate=None
  block=re.search(r'(?:[ASBDCM]-?\d+|PM-?\d+)',label.replace('왕숙1','').replace('왕숙2',''))
  code=block.group(0).replace(' ','') if block else None
  if code:code=re.sub(r'^([A-Z]+)-?(\d+)$',r'\1-\2',code)
  claim='V8-'+board.upper()+'-'+id.upper()
  source_file='w2_a3_pamphlet.pdf'if board=='w2'else'w1_a1_pamphlet.pdf'
  display=(code+' · '+meaning)if code else label or meaning
  if kind=='school':
   display=label if label not in ['초','중','고','유',''] else {'초':'초등학교 계획','중':'중학교 계획','고':'고등학교 계획','유':'유치원 계획','':'교육시설 계획'}[label]
  if board=='w2' and id=='school_k':display='교육시설 계획'
  e=dict(feature_id=id,board_id=board,district=district,full_block_code=(district+' '+code)if code else None,land_use=meaning,short_display_label=display,claim_id=claim,source_url=url[source_file],source_file='research/map-led-v5/'+source_file,source_page=5,source_date='2026-04'if board=='w2'else'2025-07',verified_on='2026-10-15',status='qualified_published_plan',supply_program=None,developer_brand=None,households_total=None,units_by_size=None,move_in_target=None,unknowns=['공급유형·시행/시공사·세대수·입주일은 토지이용도 색/블록코드로 추정하지 않음'])
  if candidate:
   b=main[candidate];notice=candidate.lower().replace('-','_')+'_notice.pdf';text=(ep/'research/map-led-v5'/notice.replace('.pdf','.txt')).read_text(encoding='utf-8')
   proof=[]
   for m in re.finditer(r'=== PAGE (\d+) ===',text):
    end=text.find('=== PAGE',m.end());page=text[m.end():end if end!=-1 else len(text)]
    if ('공급규모' in page and '공급대상' in page) or (int(m.group(1))==1):proof.append(int(m.group(1)))
   e.update(candidate_id=candidate,full_block_code=district+' '+b['block_id'],supply_program=b['housing_program'],short_display_label=b['block_id']+' · '+b['housing_program'],households_total=b['households_total'],public_sale_households=b['public_sale_households'],size_classes=b['size_classes'],units_by_size=counts[candidate],move_in_target=b['move_in_target'],source_url=url[notice],source_file='research/map-led-v5/'+notice,source_pages=proof[:4],source_date=b['publication_date'],unknowns=['입주 예정은 공정에 따라 변경 가능','현재 모집 접수 가능 상태로 표현하지 않음'],status='verified_official_notice')
   if candidate=='W2-A1':e['developer_brand']='왕숙 아테라';e['developer_brand_source']='official notice p1'
   if candidate=='W1-A2':e['other_program_note']='총608세대 중 공공분양401세대; 나머지207세대 행복주택 향후공급 계획(공고p1)'
   if candidate=='W1-A24':e['other_program_note']='총589세대 중 공공분양390세대; 나머지199세대 행복주택 향후공급 계획(공고p1)'
   poly=feature['polygon'];center=feature.get('anchor') or [sum(z[0] for z in poly)/len(poly),sum(z[1] for z in poly)/len(poly)]
   anchors.append(dict(candidate_id=candidate,board_id=board,feature_id=id,source_native_anchor=center,anchor_basis='editorial polygon label/centroid, not proven correspondence with official guidepoint',lon=b['coordinates']['lon'],lat=b['coordinates']['lat'],source_url=b['source_url'],geographic_basis=b['coordinates']['basis'],accuracy='qualified_guide_point_not_boundary_or_gate',use='match transition/locator; do not solve exact registration from centroid correspondence'))
  entries.append(e)
def save(n,v):(p/n).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
save('block_dictionary.json',dict(revision='landuse-dictionary-v8',entries=entries,display_policy={'main_blocks':'full district + code + verified supply program; optional compact type/units/move card','context_housing':'full district + code + 공동주택 용지; no inferred public/private/rental/brand','context_school':'confirmed education type only; ambiguous W2school_k→교육시설 계획','context_facilities':'named planned use from official legend, not guaranteed open facilities','visual_hierarchy':'do not show all labels simultaneously; narration-relevant neighborhood 4–7 contextual labels per focus'},limitations=['학교부지의 초/중 구분과 실제 학교배정/개교시점은 별도 사실','S/A/B prefix alone does not establish 공급유형','기존 승인 음성/대본 변경 없음']))
save('facts.json',{'claims':[dict(claim_id=e['claim_id'],sentence=e['district']+' '+e['short_display_label']+'로 공개 계획/공고에 기재됨.',source_url=e['source_url'],source_file=e['source_file'],evidence_location={'pages':e.get('source_pages',[e['source_page']]),'board_feature_id':e['feature_id']},reference_date=e['source_date'],verified_on=e['verified_on'],status='verified'if e['status']=='verified_official_notice'else'qualified',qualifications=e['unknowns'])for e in entries]})
def circle(lon,lat,r):return [[lon+r*math.cos(k*math.pi/12)/(111320*math.cos(lat*math.pi/180)),lat+r*math.sin(k*math.pi/12)/111320]for k in range(25)]
regions=[]
for id,cids,r in [('w1_north_block_area',['W1-A1','W1-A2'],500),('w1_south_block_area',['W1-A24','W1-B17'],600),('w2_block_area',['W2-A1','W2-A3'],700)]:
 aa=[a for a in anchors if a['candidate_id']in cids];lon=sum(a['lon']for a in aa)/len(aa);lat=sum(a['lat']for a in aa)/len(aa)
 regions.append(dict(id=id,label={'w1_north_block_area':'왕숙1 북측 블록 위치권역','w1_south_block_area':'왕숙1 남측 블록 위치권역','w2_block_area':'왕숙2 블록 위치권역'}[id],polygon_lonlat=circle(lon,lat,r),approximation_radius_m=r,precision='illustrative location area around verified official block guidepoints; radius chosen for readability, NOT legal district boundary',source_candidate_ids=cids,source='official LH notice map guidepoints',required_label='블록 위치권역(근사) · 지구 경계 아님'))
save('geographic_linkage.json',dict(revision='geographic-linkage-v8',coordinate_system='WGS84 longitude latitude',anchors=anchors,regions=regions,geographic_bounds=[127.10,37.59,127.23,37.73],south_focus_bounds=[127.157,37.647,127.186,37.668],w1_to_w2_focus_bounds=[127.155,37.605,127.196,37.706],boundary_status='legal WGS84 district polygons not acquired; no native plan pixel falsely georegistered',recommended_transition='keep geographic locator with named approximate areas visible; match to native plan via named A1/A2 or A24/B17/A1-A3 anchors; continuous camera zoom geographic map then split/match transition to source-native detailed board',prohibited=['display these circles as actual legal W1/W2 land boundary','project arbitrary source-native plan polygons onto GIS without independent registration','use housing label centroid and LH guidepoint as exact surveyed controlpoint','derive station entrance/real walking time from these points']))
save('handoff.json',dict(status='ready',input_revision='script-v4-hook-outside/audio-v2 + landuse-v7 boards',outputs=['block_dictionary.json','geographic_linkage.json','facts.json'],entry_count=len(entries),main_block_count=6,affected_scene_ids=['M001','M002','M003','M004','M005','M006','M007','M007B','M008'],validation=['All3 board feature IDs mapped.','Main6 matched official notice supply summaries and existing verified analysis.','B17 official p1 supply summary re-read:74㎡128 +84㎡363 =491.','No guessed brand/program for contextual plots.','GIS location areas explicitly illustrative; exact registration unavailable.'],next_assignees=['/root/rail_route_editor','/root/fact_review'],unresolved=['Legal district GIS boundary unavailable','Contextual developer/supply date unverified; display land use only'],scope='visual data only; unchanged narration/script, no paid calls'))
print('dictionary entries',len(entries),'main6',len(anchors),'regions',len(regions))
