const fs=require('fs'),path=require('path'),e=path.resolve(__dirname,'../..'),o=path.join(e,'outputs/production-v5');const p=JSON.parse(fs.readFileSync(path.join(e,'outputs/production-v4/project_v4.json'))),m=JSON.parse(fs.readFileSync(path.join(o,'cue_focus_matrix_v5.json')));
for(const c of m.cue_rows){const v=c.visual_state;c.geometry_paths=[];c.claim_paths=[];
 if(/regional|jobs_region|jobs_connections/.test(v))c.geometry_paths.push('visual/semantic-v5/workplace_geometry.json');
 if(/plan_overview|school_detail|candidate_detail/.test(v))c.geometry_paths.push('research/map-location-v4/target_blocks.geojson','research/map-location-v4/raw/landfeatures.geojson','research/map-location-v4/raw/boundaryfeatures.geojson');
 if(/current_route|road_focus|existing_facilities|alternative_detail/.test(v))c.geometry_paths.push('visual/geographic-v1/osm_subset.geojson','visual/geographic-v1/locations.json');
 if(v==='official_whole')c.geometry_paths.push('research/map-clearance-v1/download_manifest.json');
 if(/jobs_evidence|jobs_question/.test(v))c.claim_paths.push('visual/semantic-v5/company_plan.json');
 if(/train_compare|commute|rail_calendar|jobs_connections|bus_evidence|current_route|road_focus/.test(v))c.claim_paths.push('visual/semantic-v5/commute_steps.json','research/commute-v3/facts.json');
 if(/price|waterfall|scenario|trade|comparison/.test(v))c.claim_paths.push('research/price-stage-v3/facts.json','research/prices-v2/facts.json');
 if(/school|calendar|restriction|disposal|candidate/.test(v))c.claim_paths.push('research/production-v2/facts.json');
 if(!c.claim_paths.length)c.claim_paths.push('writer/script-v3/claim_basis.json');
 c.location_basis=c.geometry_paths.length?c.geometry_paths.join(' / '):'비지리 도표: '+c.claim_paths.join(' / ');
}
const audit=p.shots.map(s=>{const k=s.shot.kind,f=s.shot.focus;let effect='주제별 기존 고정판';if(k==='official'&&!s.shot.keepOriginal)effect='early return이 title/focus를 버리고 overview로 덮어씀';else if(['school','candidate'].includes(k))effect='실제 블록 map 유지하나 subtitle 세부대상의 focus 없음; 제목·주제 고정';else if(k==='map')effect=['원흥','DMC','행신'].includes(f)?'운영역/일부 철도 강조; 발화 내 후속 목적지는 같은 focus':'IKEA'===f?'IKEA 면만 강조; 시설/횡단/생활 세부 focus 고정':'덕양로'===f?'life 도로 덕양로만 강조; 도래울로/권율대로/서오릉로/수색교 후속은 같은 focus':'미등록 focus: 실제 강조 없음';else if(k==='alternatives')effect='가격행 focus는 변화하나 GeoMap focus는 원흥으로 고정';else if(k==='price')effect='단지행만 변화; 기본/확장/합계 발화별 단계 없음';else if(k==='conditions')effect='variant별 글목록은 바뀌나 같은 생활지도/IKEA와 고정';return {shot_id:s.shot_id,kind:k,focus:f||null,current_effect:effect,review_basis:'v4r2 source 분기 분석; 전수 encoded 시청 주장 아님',replacement_states:m.shot_rows.find(x=>x.shot_id===s.shot_id).proposed_states}});
fs.writeFileSync(path.join(o,'cue_focus_matrix_v5.json'),JSON.stringify(m,null,2));fs.writeFileSync(path.join(o,'legacy_focus_audit_v5.json'),JSON.stringify(audit,null,2));console.log('183큐 구체 geometry/claim 경로 및47shot fallback 진단 보완');
