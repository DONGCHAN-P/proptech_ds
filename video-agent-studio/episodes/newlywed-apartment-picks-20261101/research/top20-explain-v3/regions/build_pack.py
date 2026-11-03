import collections, copy, hashlib, json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent
EP = ROOT.parents[2]
TODAY = '2026-11-03'
def read(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def dump(name, data): (ROOT/name).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

prior_path = EP/'research/top20-8min-v2/combined_facts.json'
photo_path = EP/'visual/top20-8min-v2/photo_assets_v2.json'
prior = read(prior_path)
photos = read(photo_path)
records = read(ROOT/'research_records.json')
old_regions = {r['region_id']:r for r in prior['regions']}
photo_map = {r['region_id']:r for r in photos['assets']}
sources = read(ROOT/'source_registry.json') + read(ROOT/'source_registry_extra.json')
index_ids = {'JAMSIL','SAMSONG','YEOUIDO_FINANCE','NOWON_HOUSING','GIHEUNG_HOUSING','GUSEONG_ST','GUSEONG_INTERCHANGE','SINNAE_HOUSING','INCHEON_TRANSIT','GWANGGYO_PARK'}
for s in sources:
 s.update(checked_date=TODAY, primary_source=True, verification_mode=('official_returned_text' if s['source_id'] in index_ids else 'official_page_text'))
 s['date_note'] = '원자료에 명시한 시점; null은 게시·관측일 미표시. 확인일을 원자료 기준일로 대체하지 않음.'
source_map = {s['source_id']:s for s in sources}
for s in prior['sources']:
 source_map.setdefault(s['source_id'],dict(s, verification_mode='prior_research_reuse', reused_from=str(prior_path)))

sentence_links = {
 'R01':[['H01','G01'],['H01','L01'],['G01']], 'R02':[['H01'],['H01'],['L01']],
 'R03':[['H01'],['H01'],['L01']], 'R04':[['H01'],['H02'],['L01']],
 'R05':[['H01','H02'],['H01'],['L01']], 'R06':[['H01','H02'],['H01','H02'],['L01']],
 'R07':[['H01'],['H01'],['L01']], 'R08':[['H01','H02'],['H02'],['H01']],
 'R09':[['H01','H02'],['H02'],['G01']], 'R10':[['H01'],['H02'],['L01']],
 'R11':[['H01'],['L01'],['L01']], 'R12':[['H01'],['L01']], 'R13':[['H01'],['L01']],
 'R14':[['H01'],['H01','L01'],['H01']], 'R15':[['H01'],['L01'],['H02']],
 'R16':[['H01'],['L01','L02'],['L01']], 'R17':[['H01','H02'],['L01'],['L01']],
 'R18':[['H01'],['H02'],['L01']], 'R19':[['H01'],['L01'],['L01']],
 'R20':[['H01'],['H01','H02'],['H01']]
}
input_paths = [prior_path,photo_path,EP/'brief.json',EP/'state.json',EP/'director/top20-explain-v3/제작계획.md',ROOT/'research_records.json',ROOT/'source_registry.json',ROOT/'source_registry_extra.json',EP.parents[2]/'output/telegram_conversation/inbox/718066312.json']
# Project root is EP.parents[2]; no common file is written.
inputs = [{'path':str(p),'sha256':sha(p)} for p in input_paths]
regions = []
narrations = []
for row in records:
 rid = row['region_id']; old = old_regions[rid]; photo = photo_map[rid]
 prefix = 'V3-'+rid+'-'
 claims = []
 for short,statement,sid,facility in row['claims']:
  if rid in ('R08','R09') and short=='L01': continue  # production-context sentences are not extra facts
  src = source_map[sid]
  claims.append({'claim_id':prefix+short,'kind':{'H':'housing_or_submarket','L':'landmark_function','G':'geography'}[short[0]],'statement':statement,'original_source':[{'url':src['url'],'file':None}],'source_ids':[sid],'evidence_location':src['evidence_location'],'reference_date':src.get('as_of_date'),'reference_date_basis':src['date_note'],'checked_date':TODAY,'status':'verified','verification_scope':src['check_scope'],'verification_mode':src['verification_mode'],'facility_status':facility,'facility_status_as_of':src.get('as_of_date'),'evidence_type':'official_primary_text','opinion':False,'price_causation_established':False})
 for old_id,short in row.get('reuse',[]):
  candidates = old.get('all_claim_records',[])+old.get('feature_facts',[])
  c = next(x for x in candidates if x['claim_id']==old_id)
  urls = c.get('original_source') or [{'url':c.get('source_url'),'file':c.get('source_file')}]
  ids = c.get('source_ids') or [c.get('source_id')]
  claims.append({'claim_id':prefix+short,'previous_claim_id':old_id,'kind':{'H':'housing_or_submarket','L':'landmark_function','G':'geography'}[short[0]],'statement':c['statement'],'original_source':urls,'source_ids':ids,'evidence_location':c['evidence_location'],'reference_date':c.get('reference_date'),'reference_date_basis':'기존 검증의 기준일을 유지. null은 원자료 미표시.','checked_date':c.get('checked_date') or c.get('checked_at'),'record_review_date':TODAY,'status':c['status'],'verification_scope':'지정된 불변 공식 소스팩의 검증된 주장을 재사용. 이번에 원문·사진 픽셀·이용허락을 다시 검수한 것으로 기록하지 않음.','verification_mode':'prior_research_reuse','reused_from':str(prior_path),'facility_status':c.get('facility_status') or ('operating' if short.startswith('L') else None),'facility_status_as_of':c.get('reference_date'),'evidence_type':'prior_verified_official_primary_text','opinion':False,'price_causation_established':False})
  for src in old.get('sources',[]): source_map.setdefault(src['source_id'],dict(src, verification_mode='prior_research_reuse'))
 year=photo.get('photo_capture_year')
 pcopy={k:copy.deepcopy(photo.get(k)) for k in ('asset_id','actual_place','address_or_area','photo_capture_year','photo_capture_date_raw','absolute_file','actual_file','sha256','license','source_or_prompt')}
 pcopy.update(metadata_source=str(photo_path),metadata_source_sha256=sha(photo_path),place_match_reused=copy.deepcopy(photo.get('geography_verification',{})),prior_inspection_reused=copy.deepcopy(photo.get('inspection',{})),new_pixel_inspection_performed=False,new_license_inspection_performed=False,ai_generated=False)
 # Camera coordinates belong to the old photo record; this task supplies no map pin.
 pcopy['place_match_reused'].pop('coordinates_from_source',None)
 pcopy['place_match_reused'].pop('coordinates_role',None)
 pcopy['caption_ko']=row['caption']+' / '+(str(year)+'년 자료사진' if year else '촬영연도 미상 자료사진')
 ids={c['claim_id'] for c in claims}
 sentences=[x.strip()+'.' for x in row['narration'].split('.') if x.strip()]
 linked=[{'text':t,'claim_ids':[prefix+i for i in refs],'kind':('production_context' if '사진은' in t or '자료입니다' in t else 'fact_or_descriptive_synthesis')} for t,refs in zip(sentences,sentence_links[rid])]
 narration={'region_id':rid,'scene_id':old['scene_id'],'text':row['narration'],'character_count_including_spaces':len(row['narration']),'sentence_count':len(sentences),'sentences':linked,'claim_ids':[c['claim_id'] for c in claims],'style':'정보제공·합니다체','status':'ready_for_writer_integration_pending_independent_QA','cautions':row['cautions']}
 narrations.append(narration)
 regions.append({'region_id':rid,'rank':old['rank'],'scene_id':old['scene_id'],'province':old['province'],'region':old['region'],'statistical_geography_reference_date':'2024-11-01','geography_label':row.get('geography_label',old['province']+' '+old['region']),'geography_scope':'지역/명소명과 공식 주소·행정개편 자료의 명칭 대조. 새 경계 GIS·point-in-polygon 검사 없음.','pin_coordinates':None,'housing_feature_claim_ids':[c['claim_id'] for c in claims if c['kind']=='housing_or_submarket'],'landmark_function_claim_ids':([prefix+'H01'] if rid in ('R08','R14','R20') else [prefix+'H02'] if rid=='R09' else [c['claim_id'] for c in claims if c['kind']=='landmark_function']),'claims':claims,'photo':pcopy,'narration_suggestion':narration,'editorial_cautions':row['cautions']})

comparison={
 'reading_id':'V3-COMPARE-01','kind':'interpretation_not_causal_claim','status':'qualified',
 'text':'같은 구 안에서도 주택이 지어진 시기와 업무지·역 주변의 생활 구조는 다릅니다. 지역별 가격은 면적과 거래기간, 거래유형, 표본 수가 같은 조건인지 확인하며 읽습니다. 2024년 신혼부부 거주 순위를 현재의 주거 선호나 가격 상승 원인으로 해석하지 않습니다.',
 'basis_claim_ids':['V3-R03-H01','V3-R06-H01','V3-R06-H02','V3-R09-H01','V3-R09-H02','V3-R01-G01'],
 'source_scope':'본 자료의 검증 사실을 바탕으로 한 비교 조건 해설 제안. 추천·가격 전망·인과관계로 확정한 사실이 아님.',
 'checked_date':TODAY,'price_values_generated':False
}
used_source_ids=sorted({sid for r in regions for c in r['claims'] for sid in c['source_ids']})
result={'revision':'top20-explain-v3-regions-final-1','status':'research_final_pack_ready_for_writer_pending_independent_QA','created_date':TODAY,'role':'research/regions','write_scope':str(ROOT),'input_revisions':inputs,'scope':{'regions':20,'comparison_readings':1,'new_price_calculation':False,'trade_database_collection':False,'new_coordinates':False,'new_photo_downloads':False,'paid_calls':False,'tts':False,'uploads':False},'regions':regions,'sources':[source_map[sid] for sid in used_source_ids],'comparison_reading':comparison,'open_issues':[{'issue_id':'REGIONS-V3-SCOPE','severity':'note','detail':'공식 원문 전체 열람·공식 검색 반환 텍스트·기존 검증 승계를 구분했습니다. 캡처 및 로컬 HTTP 취득 실패를 원문/픽셀 검수 통과로 기록하지 않았습니다.','evidence':'source_snapshots/capture_receipt.json'},{'issue_id':'REGIONS-V3-MAGOK-DATES','severity':'note','affected_claim_ids':['V3-R04-H01','V3-R04-H02'],'affected_scene_ids':['S019'],'detail':'전체 사업기간의 공식 페이지 간 차이는 원고에서 제외. 확인한 과거 구역 조성 완료 이력만 사용.'},{'issue_id':'REGIONS-V3-INDEPENDENT-QA','severity':'required_next_step','detail':'이 담당의 자료·문장 대조는 자체 확인입니다. writer 통합 후 독립 QA가 필요합니다.'}]}
result['verification_policy']='verified는 기록한 제한된 문장의 근거를 확인했다는 뜻입니다. 원자료 기준일·확인 범위를 우선하며, 2026 현장검사·시설별 최신 영업시간 확인·새 독립 QA를 뜻하지 않습니다.'
dump('facts.json',result)
dump('narration_suggestions.json',{'revision':result['revision'],'checked_date':TODAY,'status':'ready_for_writer_integration','regions':narrations,'comparison_reading':comparison,'source_note':'출처는 도입에서 설명하고 화면별 반복 통계청 표기를 요구하지 않습니다. 사진 크레딧·자료시점·가격 비교조건은 유지합니다.','ranking_limit_note':'순위는 2024-11-01 거주지 통계입니다. 그 뒤 입주·이동이 반영된 2026 현재 순위로 표현하지 않습니다.'})

lines=['# TOP20 지역별 주거 특성·랜드마크 근거','',f'버전: {result["revision"]} / 조사 정리일: {TODAY} / writer 통합용 최종 자료팩, 독립 QA 전.','','범위는20지역과 비교 읽기1개입니다. 가격·거래 원자료·새 좌표는 생성하지 않았습니다. `verified`의 확인 범위는 각 claim의 원문/검색 반환/기존 검증 재사용 구분과 기준일에 한정합니다. 실제 장소 사진의 장소·이용조건·촬영연도는 기존 명세를 승계했으며 이번에 새로 픽셀을 검수하지 않았습니다.','', '2024 순위·현재 행정명·원자료 관측일·사진 촬영연도를 분리합니다. 새 핀 좌표가 필요하면 담당자의 검증된 단지 좌표를 사용해야 합니다. 아래 지역명은 상세 경계 도형의 새 검증을 뜻하지 않습니다.','']
for r in sorted(regions,key=lambda x:-x['rank']):
 lines += [f'## {r["rank"]}위 · {r["geography_label"]} · {r["region_id"]} / {r["scene_id"]}','','**원고 제안** ('+str(r['narration_suggestion']['character_count_including_spaces'])+'자): '+r['narration_suggestion']['text'],'','**사진 설명**: '+r['photo']['caption_ko'],'','사진 ID: `'+r['photo']['asset_id']+'` / 실제 장소: '+r['photo']['actual_place']+' / 이용조건: '+str(r['photo']['license'].get('name'))+' / 전체 크레딧·변형 조건은 facts.json의 photo.license를 그대로 승계합니다.','','| Claim ID | 확인 문장 | 상태·기준일·확인일 | 근거 위치·확인 범위 |','|---|---|---|---|']
 for c in r['claims']:
  citations='; '.join('['+source_map[sid].get('title',sid)+']('+source_map[sid]['url']+')' for sid in c['source_ids'])
  loc=' / '.join(c['evidence_location']) if isinstance(c['evidence_location'],list) else c['evidence_location']
  lines.append('| '+c['claim_id']+' | '+c['statement']+' | '+c['status']+' / '+str(c['reference_date'] or '원자료 미표시')+' / '+str(c['checked_date'])+' | '+citations+' · '+loc.replace('|','/')+' · '+c['verification_scope'].replace('|','/')+' |')
 lines += ['','**편집 주의**: '+' '.join(r['editorial_cautions']),'']
lines += ['## 비교 읽기1개 · 해석 제안','','`V3-COMPARE-01` / qualified / 사실에서 도출한 비교 조건 안내, 인과·투자추천 아님.','',comparison['text'],'','## 확인하지 않은 범위','','개별 개발사업의 최신 전 단계, 현재 요금·배차·실제 출퇴근시간·학군·관리비·판매 매물·거래가격·대출·정책·수익률은 이 자료팩에서 확정하지 않습니다. 촬영연도 미상 청라와 과거 사진의 시점은 자막/설명란에서 유지합니다. 신내역2015 사진에는 현재6호선 환승 정보를 당시 시설처럼 합성하지 않습니다.','','## 인계','','writer/top20-explain-v3에서 본 자료의 claim IDs와 문장별 연결을 유지하여 기존 초안에 통합합니다. 단지·지역 가격은 별도 prices 담당의 확정 조건을 따라야 합니다. 총괄이 공통 scenes/state/decisions를 갱신하고 독립 QA가 통합본을 확인합니다.']
(ROOT/'region_features.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

errors=[]
all_claims=[c for r in regions for c in r['claims']]
all_ids={c['claim_id'] for c in all_claims}
if len(regions)!=20 or len(set(r['region_id'] for r in regions))!=20: errors.append('지역20개 조건 실패')
if len(all_ids)!=len(all_claims): errors.append('claim ID 중복')
for r in regions:
 n=r['narration_suggestion']; rid=r['region_id']; local={c['claim_id'] for c in r['claims']}
 if not 100<=len(n['text'])<=170: errors.append(rid+': 글자 수')
 if not 2<=n['sentence_count']<=3: errors.append(rid+': 문장 수')
 if not all(s['text'].rstrip('.').endswith('니다') for s in n['sentences']): errors.append(rid+': 합니다체')
 if not r['housing_feature_claim_ids']: errors.append(rid+': 주거 특징 없음')
 if not r['landmark_function_claim_ids']: errors.append(rid+': 랜드마크 기능 근거 없음')
 if not pathlib.Path(r['photo']['absolute_file']).is_file(): errors.append(rid+': 기존 사진 파일 없음')
 for s in n['sentences']:
  if set(s['claim_ids'])-local: errors.append(rid+': 문장 claim 연결 실패')
 for c in r['claims']:
  for key in ['statement','original_source','evidence_location','checked_date','status','verification_scope']:
   if not c.get(key): errors.append(c['claim_id']+': '+key)
 if any(not source_map[sid].get('url') for c in r['claims'] for sid in c['source_ids']): errors.append(rid+': 출처 URL 없음')
if any(not (ROOT/o).is_file() for o in ['facts.json','region_features.md','narration_suggestions.json']): errors.append('산출물 없음')
for name in ['facts.json','narration_suggestions.json']: read(ROOT/name)
receipt={'checked_date':TODAY,'passed':not errors,'region_count':len(regions),'claim_count':len(all_claims),'status_counts':dict(collections.Counter(c['status'] for c in all_claims)),'source_count':len(used_source_ids),'photo_manifest_entries_reused':len(regions),'existing_photo_file_presence_pass':True,'new_photo_pixel_review':False,'pin_coordinates_provided':False,'narration_min_chars':min(len(n['text']) for n in narrations),'narration_max_chars':max(len(n['text']) for n in narrations),'comparison_readings':1,'errors':errors,'outputs':[{'file':n,'bytes':(ROOT/n).stat().st_size,'sha256':sha(ROOT/n)} for n in ['facts.json','region_features.md','narration_suggestions.json']]}
dump('validation.json',receipt)
handoff={'task_id':'TOP20-v3-REGIONAL-FEATURES','role':'research/regions','status':'complete_for_writer_integration' if not errors else 'validation_failed','input_revisions':inputs,'outputs':[str(ROOT/n) for n in ['facts.json','region_features.md','narration_suggestions.json','validation.json']],'affected_scene_ids':[r['scene_id'] for r in regions],'checks':[{'check':'20지역·주거특징·랜드마크 기능·문장별 claim·100~170자·2~3문장·합니다체·기존사진 파일존재·JSON 재열람','result':'passed' if not errors else 'failed','evidence':str(ROOT/'validation.json')},{'check':'새 픽셀검수·촬영·신규 라이선스 검토·독립 QA','result':'not_performed','evidence':'기존 사진 명세의 검증과 이용조건을 승계. 독립 QA는 다음 단계.'}],'open_issue_ids':['REGIONS-V3-SCOPE','REGIONS-V3-MAGOK-DATES','REGIONS-V3-INDEPENDENT-QA'],'next_role':'writer/top20-explain-v3 (Pascal01a19ced-7dc3-7071-bbb2-f49e3deb62fb), director, independent QA','summary_ko':'20지역 102~134자·2~3문장 합니다체. 주거지/생활권 차이+기존 실제 사진의 기능·촬영연도·라이선스 연결. 원문 열람/공식 반환 텍스트/기존 검증 승계 구분. 옛 서구=현 서해·검단, 판교2·3=수정구, 강남·노원은 교체사진, 신내2015사진 개통전 주의. 가격·신규 좌표·TTS·유료호출·업로드 없음. writer 통합 후 독립 QA 필요.'}
handoff['claim_index']={r['region_id']:{'scene_id':r['scene_id'],'claim_ids':[c['claim_id'] for c in r['claims']],'housing_feature_claim_ids':r['housing_feature_claim_ids'],'landmark_function_claim_ids':r['landmark_function_claim_ids']} for r in regions}
handoff['photo_replacements']=[{'region_id':rid,'scene_id':old_regions[rid]['scene_id'],'use_asset_id':photo_map[rid]['asset_id'],'absolute_file':photo_map[rid]['absolute_file'],'sha256':photo_map[rid]['sha256'],'actual_place':photo_map[rid]['actual_place'],'photo_capture_year':photo_map[rid]['photo_capture_year'],'replaces_asset_id':photo_map[rid]['replaces']['asset_id'],'input_manifest':str(photo_path),'input_manifest_sha256':sha(photo_path),'instruction':'교체된 현재 v2 사진 사용. 옛 타워/테헤란로/당현천 사진으로 자동 복귀하지 않음.'} for rid in ['R02','R06','R11']]
handoff['authorization_boundary']='새 대본·대표시안까지 준비하여 script gate로 사용자에게 전달. 해당 버전 승인 전 TTS·본편 렌더 없음. 이 담당은 자료조사만 완료했으며 업로드·유료 호출 권한을 확장하지 않음.'
dump('handoff.json',handoff)
print(json.dumps({'passed':not errors,'regions':len(regions),'claims':len(all_claims),'sources':len(used_source_ids),'narration_chars':[receipt['narration_min_chars'],receipt['narration_max_chars']],'errors':errors,'handoff':str(ROOT/'handoff.json')},ensure_ascii=False))
if errors: raise SystemExit(1)
