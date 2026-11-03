from pathlib import Path
import json,sys
sys.stdout.reconfigure(encoding='utf-8');root=Path(__file__).parent
a=json.loads((root/'assets_v2.json').read_text('utf-8'));a['revision']='visual-v3'
meta=json.loads((root/'regional_meta_v3.json').read_text('utf-8'))
a['assets'].append({'asset_id':'S002_namyangju_regional_osm_v3','scene_ids':['S001','S002'],'type':'actual_geographic_map','source_or_prompt':{'publisher':'OpenStreetMap contributors','data_url':meta['source_url'],'raw_data_file':'visual/regional_osm_v3.json','coordinates_file':'visual/regional_meta_v3.json','official_wangsuk_locations':'DEV-001, 남양주시 key3039'},'dimensions':[1920,1080],'actual_file':meta['actual_file'],'actual_place':'남양주 별내·다산·진접·오남·호평·평내·화도·진건·퇴계원·일패·이패','AI':False,'usage_conditions':'OSM ODbL: 출처와 copyright URL 영상·출처목록 유지. raw data·좌표 메타 제공. 표준타일 서버 다운로드 없음. 공개 Overpass 원데이터를 자체 도식화.','review_status':'실제 원데이터 5,615개 요소·12개 지역명 좌표와 이미지 육안확인; 도보권·경계·통근시간·철도운영상태 근거로 사용 금지','projection':'regional equirectangular, lon*cos(37.7), same degree scale','timing':'not_locked'})
svg=(root/'outputs/S003_district_comparison.svg').read_text('utf-8')
rep=[('왕숙1 · 왕숙2: 서로 다른 지구','일자리: 기업 이름보다 진행 단계'),('왕숙1','기존 산업 기반'),('진접·진건·퇴계원읍 / 계획 64,159세대','진관·금곡·광릉테크노밸리 / 조성 완료'),('왕숙2','왕숙 산업단지'),('일패·이패동 / 계획 15,955세대','2026.10.8 개발실시계획 승인·고시 발표'),('계획 면적','입주 예정기업'),('왕숙1 약 1,029만㎡ / 왕숙2 약 239만㎡','우리금융·카카오·신한 / 실제 운영 미확인'),('전체 계획 ≠ 입주','우리금융'),('80,114세대는 두 지구 계획의 단순 합계','2026.5 건축허가 / 2029년 준공 목표'),('남양주시 사업개요 2026.3.4 | 최신 변경고시 전수 대조 미완료','남양주시 공식 자료 | 계획·허가와 준공·실제 상주인력 구분')]
for x,y in rep:svg=svg.replace(x,y)
rows=[('기존 산업 기반','진관·금곡·광릉테크노밸리 / 조성 완료'),('왕숙 산업단지','2026.10.8 개발실시계획 승인·고시 발표'),('입주 예정기업','우리금융·카카오·신한 / 실제 운영 미확인'),('우리금융','2026.5 건축허가 / 2029년 준공 목표')]
svg='<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080"><rect width="1920" height="1080" fill="#F6F4EF"/><g font-family="Noto Sans KR, Malgun Gothic, sans-serif"><text x="100" y="130" font-size="62" fill="#111111">일자리: 기업 이름보다 진행 단계</text>'
for i,(label,value) in enumerate(rows):
    y=220+i*135;svg+=f'<rect x="100" y="{y}" width="1720" height="110" rx="18" fill="white"/><text x="135" y="{y+68}" font-size="40" fill="#2F6FED">{label}</text><text x="620" y="{y+68}" font-size="32" fill="#111111">{value}</text>'
svg+='<text x="100" y="955" font-size="27" fill="#6E6E6E">남양주시 공식 자료 | 계획·허가와 준공·실제 상주인력 구분</text></g></svg>'
(root/'outputs/S005_jobs_stage_v3.svg').write_text(svg,'utf-8')
facts=json.loads((root/'../research/facts.json').read_text('utf-8'))['facts'];ids=['DEV-012','DEV-004','DEV-006','DEV-007']
a['assets'].append({'asset_id':'S005_jobs_stage_v3','scene_ids':['S005'],'type':'editorial_card','source_or_prompt':[{'claim_id':i,'source_url':next(f['source_url'] for f in facts if f['claim_id']==i)} for i in ids],'dimensions':[1920,1080],'actual_file':'visual/outputs/S005_jobs_stage_v3.svg','actual_place':None,'AI':False,'usage_conditions':'자체 정보 카드, 출처 유지. 사진·기관 이미지·기업 로고 복제 없음.','review_status':'facts-v1 단계·문구 대조; 실제 래스터 렌더 가독성 편집팀 확인 필요','timing':'not_locked'})
(root/'assets_v3.json').write_text(json.dumps(a,ensure_ascii=False,indent=2),'utf-8')
for x in a['assets']:
    assert (root.parent/x['actual_file']).exists(),x['actual_file']
print('visual-v3 actual assets verified:',len(a['assets']))
