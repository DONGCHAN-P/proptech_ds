import pathlib,json,hashlib
P=pathlib.Path(__file__).parent
assets=[]
for stem,title in [('w1_north','왕숙1 북부'),('w1_south','왕숙1 남부'),('w2','왕숙2'),('macro','왕숙1·왕숙2 권역 관계')]:
 file=P/f'{stem}_board.json'
 if not file.exists():continue
 data=json.loads(file.read_text(encoding='utf-8'))
 assets.append(dict(asset_id=stem.upper()+'_LANDUSE_V7',scene_ids=['M001','M002','M003','M005'],type='factual_spatial_diagram',source_or_prompt=data['source'],dimensions=data['dimensions'],actual_file=f'visual/landuse-v7/{stem}_board_unlabelled.svg',actual_place='남양주 '+title,AI=False,usage_conditions='공개 계획자료의 사실 배치 직접 정리. 자체 색·글꼴. 원본 이미지 최종 크롭 사용 아님. 원본 재사용 허가 미확인.',geometry_status='주요 용도별 도해 단순화; 정밀경계·측량·보행경로 아님; 일부 작은필지 생략',review_status='원본 및 자체 PNG 실제 시각 확인, 최종 동영상 검수는 편집 후',motion='still_motion; 같은 판 안에서 확대·이동 및 의미별 시설 강조',feature_count=len(data['features'])))
P.joinpath('assets.json').write_text(json.dumps(dict(revision='visual-landuse-v7',assets=assets),ensure_ascii=False,indent=2),encoding='utf-8')
outputs=[]
for p in P.glob('*'):
 if p.suffix in ['.json','.svg','.png'] and p.name not in ['handoff.json','file_integrity.json']:
  outputs.append(dict(path='visual/landuse-v7/'+p.name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
P.joinpath('file_integrity.json').write_text(json.dumps(outputs,ensure_ascii=False,indent=2),encoding='utf-8')
handoff=dict(revision='visual-landuse-v7',status='actual boards ready for editor integration',input_version='script-v4-hook-outside/audio-v2',outputs=[a['actual_file'] for a in assets]+['visual/landuse-v7/'+s+'_board.json' for s in ['w1_north','w1_south','w2','macro'] if (P/(s+'_board.json')).exists()],coordinate_contract='All features[].polygon and anchor and cameras are local board pixel coordinates. dimensions gives extent. Do not treat these as WGS84. Keep aspect ratio. Use screen-constant selective labels.',validation=dict(actual_pngs_inspected=True,reference_plan_pages_inspected=True,feature_counts={a['asset_id']:a['feature_count'] for a in assets},video_review=False),unresolved=['원본 지도 자체의 크롭/변형 허가 미확인. 자체 사실 도해 사용.', '정밀경계/측량/보행경로와 개통·개교를 보장하지 않음.','기업CI 최종배치는 editor/research 담당.'],affected_scenes=['M001','M002','M003','M005'],next_owner='/root/rail_route_editor')
P.joinpath('handoff.json').write_text(json.dumps(handoff,ensure_ascii=False,indent=2),encoding='utf-8')
print('Manifest assets',len(assets),'integrity files',len(outputs))
