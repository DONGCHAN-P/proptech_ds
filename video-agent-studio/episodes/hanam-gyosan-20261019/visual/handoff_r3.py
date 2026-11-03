import pathlib,json,hashlib
from PIL import Image
V=pathlib.Path(__file__).parent;EP=V.parent;R=V.parents[3];O=EP/'outputs/production-v1';S=R/'video/src/gyosan-production-v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
geo=json.loads((V/'geometry_checks_r3.json').read_text(encoding='utf8'));d=json.loads((V/'data_r3.json').read_text(encoding='utf8'));guard=json.loads((O/'preflight-r3/guard.json').read_text(encoding='utf8'))
assets=json.loads((V/'assets.json').read_text(encoding='utf8'));assets=[a for a in assets if not a['asset_id'].startswith('R3_')]
for name in ['REP_jobs_external','REP_C2','REP_B2']:
 p=O/'preflight-r3'/f'{name}.png'
 with Image.open(p) as im:dims=list(im.size)
 assets.append(dict(asset_id='R3_'+name,scene_ids=['M002'] if 'jobs' in name else ['M008'],type='actual_map',source_or_prompt=d['meta'],dimensions=dims,actual_file=str(p),actual_place='하남 교산·서울동남권·판교' if 'jobs' in name else '하남 교산 '+name.replace('REP_',''),AI=False,usage_conditions='KRIC 역 중심점·SGIS/MIT·LH 실제 계획 필지 재구성; 직장/출입구/통근경로 아님; 학교/공원은 계획 시설',review_status='실제 PNG 직접 확인 및 layout guard 통과; root/QA 대표 검토 대기',sha256=sha(p)))
(V/'assets.json').write_text(json.dumps(assets,ensure_ascii=False,indent=2),encoding='utf8')
receipt=O/'render_receipt_r3.json'
h=dict(revision='v1r3',status='changed_media_ready' if receipt.exists() else 'representative_review_pending',scope=['M002 외부 업무지 실제 역 대표점 지도','M008 C2/B2 전체 locator+실제필지상세+풀네임시설라벨','M007 부모 제공 제목 변경'],outputs=dict(representatives=str(O/'preflight-r3'),renderer=str(EP/'editor/production-v1/render_r3.cjs'),rendered_project=str(O/'rendered_project_r3.json'),receipt=str(receipt)),inputs=dict(source_sha256={p.name:sha(p) for p in [S/'Board.tsx',S/'R3Maps.tsx',S/'data_r3.json']},atlas_sha256=d['meta']['atlas_sha256'],project_sha256=sha(O/'project.json')),verification=dict(representative_guard=guard,geometry_checks=geo,actually_viewed=['REP_jobs_external','REP_C2','REP_B2'],all_target_block_bboxes_inside=True,all_label_points_inside=True,leader_intersections=0,mp4_continuous_playback=False,audio_listened=False),coordinates=dict(stations=d['external']['stations'],detail_mapping=d['details']),unresolved=['root/QA 대표3장 확인 후 변경 장면 렌더','전체 MP4 후속 검수'],next_owner='director / independent QA')
if receipt.exists():
 r=json.loads(receipt.read_text(encoding='utf8'));h['verification']['render_receipt']={k:r[k] for k in ['completed','input_digest','project_sha256','baseline_sha256','actual_still_calls','changed_png','reused_png','changed_variants']};h['unresolved']=['최종 MP4 연속 재생 및 실제 청취 미수행','통합 MP4 독립 QA 필요']
 h['verification']['root_and_independent_qa_representatives']='부모의 명시적 대표 3장 통과 전달 후 변경 렌더 실행'
 h['verification']['new_png_and_source_hash_check']=str(V/'verification_r3.json')
 for a in assets:
  if a['asset_id'].startswith('R3_'):a['review_status']='실제 PNG 확인·layout guard 통과·root/독립 QA 대표 검토 통과; 최종 MP4 후속 검수'
 (V/'assets.json').write_text(json.dumps(assets,ensure_ascii=False,indent=2),encoding='utf8')
(V/'handoff_r3.json').write_text(json.dumps(h,ensure_ascii=False,indent=2),encoding='utf8');print(h['status'])
