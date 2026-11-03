from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
from PIL import Image
ALT=Path(__file__).resolve().parent;ROOT=ALT.parents[1];EVI=ALT/'evidence';EP=ROOT.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
base=json.loads((ROOT/'photo_assets.json').read_text(encoding='utf-8'));v2=json.loads((ROOT/'photo_assets_v2.json').read_text(encoding='utf-8'))
changed=[a for a in v2['assets'] if a['rank'] in [2,6,11]]
assert len(v2['assets'])==20 and len(changed)==3
assert all(x==y for x,y in zip(base['assets'],v2['assets']) if x['rank'] not in [2,6,11])
for rel,digest in v2['protected_v1_hashes'].items():assert sha(ROOT/rel)==digest,rel
for a in changed:
 p=ROOT/a['actual_file'];assert sha(p)==a['sha256']
 with Image.open(p) as im:im.load();assert list(im.size)==[a['dimensions']['width'],a['dimensions']['height']]
 if a['rank']==6:a['address_or_area']='서울특별시 강남구 양재천 영동4교 인근(세부 법정동·필지 확정 아님)'
 a['inspection'].update(pixel_visual_review=True,status='self_checked_alternate_landscape_accepted',
   review_scope='3장 최종 contact sheet 실제 픽셀 확인, 노원1600px 개별 열람으로 기관 모자이크 확인. 개별 원문·기관 권리정책·해상도·해시·GPS/지역 대조.')
 a['replacement_release']['status']='accepted_for_this_landscape_context_pending_independent_QA'
v2['replacement_status']='three_replacements_self_checked'
v2['contact_sheet']='photos/alternates/R02_R06_R11_alternates_contactsheet.jpg'
v2['contact_sheet_scope']='교체3장만. 기존20장 contact sheet는 v1 이력으로 보존하며 v2 전체20장 미리보기로 오인하지 않음.'
v2['v1_full_contactsheet_reference']=base['contact_sheet']
v2['replacement_gaps']=[]
v2['active_replacement_conditions']=['R02/R06/R11 모두 개별 CC0 또는 공공기관의 CC BY4·공공누리1 허락이 확인된 실제 풍경 파일.',
 '특정 건축물·조형물·인물을 주피사체로 재확대하는 편집은 이 구도 확인 범위에 포함되지 않음. 원문 권리표시 누락만으로 전체권리 해결이라 판단하지 않음.',
 '최종 공개본의 독립 QA는 총괄 단계에서 별도 수행.']
dump(ROOT/'photo_assets_v2.json',v2)
md=['# TOP20 사진 원장 v2 — R02·R06·R11 좁은 보완','',
 '기존20장 파일과 v1 원장은 보존했다. v2는20행 중 R02·R06·R11만 다른 실사로 교체하며17행은 객체 내용까지 v1과 동일하다.',
 '통계 기준일은2024-11-01이다. 사진 촬영시점과 서울경관기록화2020사업연도는 별도 필드로 기록한다.',
 '최대6묶음 검색 후 종료했다. 장소·사용권·실제 파일·픽셀·해시가 확인된3장만 출고용 대체로 채택했다. 원본의 NoFoP/제3자 권리 조건은 각 행 replaces에 연결했다.',
 '출고 확인 범위는 이 수변·산책로 구도다. 권리표시 누락을 전체권리 해결로 해석하지 않았다. 기관이 보유권리의 자유이용 대상임을 밝힌 정책과 개별 표시, 실제 주피사체를 함께 확인했다.','',
 '미리보기: [교체3장 contact sheet](photos/alternates/R02_R06_R11_alternates_contactsheet.jpg) · [전체20행 v2 원장](photo_assets_v2.json) · [v1 보존 원장](photo_assets.json)','',
 '| ID / 장면 | 실제 장소 | 실제 파일 크기 | 촬영시점 | 라이선스 | 상태 |','|---|---|---|---|---|---|']
for a in changed:md.append(f'| {a["region_id"]} / {a["scene_ids"][0]} | {a["actual_place"]} | {a["dimensions"]["width"]}×{a["dimensions"]["height"]} | {a["photo_capture_date_raw"]} | {a["license"]["name"]} | 자체 확인·대체 채택, 독립 QA 미실행 |')
for a in changed:
 s=a['source_or_prompt'];lic=a['license'];old=a['replaces']
 md += ['',f'## {a["asset_id"]} — {a["actual_place"]}','',
   f'- 파일: [{a["actual_file"]}]({a["actual_file"]})',f'- 원문: [{s["title"]}]({s["file_page"]})',f'- 작가/권리자: {s["author"]}',
   f'- 원본·제공 URL: {s["original_image_url"]}',f'- 실제 저장 URL: {s["actual_download_url"]}',
   f'- 고정 원문/스냅샷: {s["fixed_revision_url"]} / [{s["metadata_snapshot"]}]({s["metadata_snapshot"]})',
   f'- 허락: {lic["name"]}; 버전 {lic["version"]}; {lic["license_url"]}',f'- 긍정적 권리 근거: {lic["copyright_permission_basis"]}',
   f'- 장소·구역: {a["geography_verification"]["basis"]}',f'- 원문/EXIF 카메라 좌표: {json.dumps(a["geography_verification"]["coordinates_from_source"],ensure_ascii=False)}',
   f'- 실제 픽셀 확인: {a["inspection"]["visual_content_finding"]}',f'- 변형: {lic["changes_notice"]}',f'- 귀속문: {lic["attribution_ko"]}',
   f'- SHA256: `{a["sha256"]}`',f'- 교체 전 자산: {old["asset_id"]} · [{old["actual_file"]}]({old["actual_file"]}) · {old["old_license"]["name"]}',
   '- 기존 조건/대체 이유: '+old['replacement_reason'],
   '- 기존 주의사항: '+' / '.join(old['old_inspection_notes']),
   '- 편집 조건: '+lic['usage_conditions_ko']]
 if 'rights_policy_url' in s:md += [f'- 기관 권리정책: [{s["rights_policy_url"]}]({s["rights_policy_url"]}) / [{s["rights_policy_snapshot"]}]({s["rights_policy_snapshot"]})',
   f'- JPEG 내 권리자: {s["embedded_copyright"]}',f'- JPEG 사업 기록: {s["embedded_project_comment"]} (촬영연도와 구분)',
   '- 공식 공개 다운로드 버튼에 이용목적 ‘상업적 활용’만 선택해1600px 파일을 받았다. 이메일·계정·연락처를 제출하지 않았다.']
md += ['','## 전체20행의 연결','',
 '| 지역 | 사용 자산 | 실제 파일 | 촬영연도 | 2024 통계 기준 |','|---|---|---|---|---|']
for a in v2['assets']:md.append(f'| {a["region_id"]} {a["statistical_region_2024"]} | {a["asset_id"]} | [{a["actual_file"]}]({a["actual_file"]}) | {a["photo_capture_year"] or "미상"} | 2024-11-01 |')
md += ['','교체 외17행의 작가·라이선스·귀속문·주의사항은 [보존된 v1 출처 원장](photo_sources.md)과 v2 JSON의 동일 행을 따른다.','',
 '## 미채택 후보·검수 한계','',
 '- 석촌호수공원1 후보는 롯데월드 건물이 크게 보이는 구도로 미채택. 같은 촬영자의 석촌호수공원2 수면 원경을 채택했다.',
 '- Commons 양재천2010 CC0 후보2장은 미리보기 실물은 저장했지만 강남구 구간의 정확한 촬영 위치가 확인되지 않아 출고용 대체로 확정하지 않았다.',
 '- 노면전차 주피사체 후보는 노원 산책로 대체 방향과 맞지 않아 미채택. 서초·과천 및 NoFoP/SA 조건의 사진도 대체하지 않았다.',
 '- 사진 인물을 신혼부부나 해당 구 거주자로 설명하지 않는다. 건축물/지도안내판/인물을 주피사체로 확대하면 이번 점검 범위를 다시 확인해야 한다.',
 '- 최종3장의 파일 디코드·해시·가로 비율·원문 이용조건·장소·실제 픽셀을 확인했다. 독립 QA·영상 렌더·청취는 수행하지 않았다.',
 '- [6묶음 검색 기록](photos/alternates/evidence/search_batches_all.json) · [보존/검증 기록](photos/alternates/evidence/v2_validation.json)','']
(ROOT/'photo_sources_v2.md').write_text('\n'.join(md),encoding='utf-8')
validation=json.loads((EVI/'v2_validation.json').read_text(encoding='utf-8'));validation.update(phase='final_self_checked',
 final_three_visual_review=True,protected_v1_hashes_still_match=True,unchanged_rows_17_equal=True,replacement_gaps=[],
 final_new_files=[{'asset_id':a['asset_id'],'actual_file':a['actual_file'],'sha256':a['sha256'],'dimensions':a['dimensions']} for a in changed])
dump(EVI/'v2_validation.json',validation)
handoff={'revision':'top20-8min-v2','photo_revision':'photo_assets_v2','owner':'visual/photos','status':'three_alternate_photos_self_checked',
 'outputs':{k:(ROOT/f).as_posix() for k,f in [('manifest','photo_assets_v2.json'),('sources','photo_sources_v2.md'),('contactsheet','photos/alternates/R02_R06_R11_alternates_contactsheet.jpg')]},
 'base_manifest':v2['base_manifest'],'changed_region_ids':['R02','R06','R11'],'affected_scene_ids':['S021','S017','S012'],
 'replacement_log':v2['replacement_log'],'replacement_gaps':[],
 'validation':{'new_physical_files':3,'new_files_decode_and_hash_checked':True,'all_landscape':True,'all_long_edges_at_least_1200':True,
  'individual_reuse_licenses_and_positive_permission_evidence_checked':True,'same_unresolved_nofop_third_party_trigger_detected':False,
  'visual_review':True,'original20_file_hashes_preserved':True,'original_manifest_and_docs_preserved':True,'unchanged17_rows_identical':True,
  'independent_qa_performed':False},
 'search_budget':{'used':6,'limit':6,'log':'photos/alternates/evidence/search_batches_all.json'},
 'remaining_conditions':['허락이 확인된 현재 수변/산책로 풍경 구도로 채택. 제3자 권리 전부를 포괄 보증하는 선언은 아님.',
  '귀속·촬영시점·기관2020사업연도 분리 표시 유지. 사람/특정 건축물/조형물을 주피사체로 확대하면 재검토.',
  '독립 QA는 총괄 단계에서3장 변경 범위만 확인. 기존17장 재검수는 불필요.'],
 'network_blockers':[],'new_paid_generation':False,'contact_email_or_upload_performed':False,'shared_files_modified':False,
 'next_owner':'director: v2 세 행을 자료화면 안내에 연결하고3장 독립 검수',
 'summary':'R02 CC0 석촌호수3840×2880, R06/R11 기관 보유권리·개별 CC BY4/공공누리1 공개사진1600×1067로 대체. 노원 가로3:2. 원본20장·v1원장 보존, 나머지17행 동일. 검색6묶음 종료, 대체공백0. 개별 출처·해시·픽셀·지역·귀속문·기존조건 연결 완료.'}
dump(ROOT/'photo_handoff_v2.json',handoff)
for rel,digest in v2['protected_v1_hashes'].items():assert sha(ROOT/rel)==digest,rel
for f in ['photo_assets_v2.json','photo_sources_v2.md','photo_handoff_v2.json']:assert (ROOT/f).stat().st_size>0
print(json.dumps({'status':handoff['status'],'new_photos':3,'unchanged_rows':17,'v1_preserved':True,'replacement_gaps':[],'search_batches':6},ensure_ascii=False))
