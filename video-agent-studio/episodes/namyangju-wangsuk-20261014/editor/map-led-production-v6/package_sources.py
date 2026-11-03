import json,hashlib,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[5];E=R/'video-agent-studio/episodes/namyangju-wangsuk-20261014';H=Path(__file__).parent;O=E/'outputs/video-review-v6'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
p=read(R/'video/src/namyangju-map-led-v6/project.json')
assert p['timing_locked'] and p['duration_frames']==26292
assert len(p['narration'])==11 and sum(len(c) for c in p['captions'].values())==269
assert p['scenes'][0]['from_frame']==0
for a,b in zip(p['scenes'],p['scenes'][1:]):assert a['from_frame']+a['duration_frames']==b['from_frame']
assert p['scenes'][-1]['from_frame']+p['scenes'][-1]['duration_frames']==p['duration_frames']
assert all(s['kind']!='image_gap' for s in p['scenes'])
inputs=['writer/map-led-v4/script_v4.md','writer/map-led-v4/scene_plan.json','writer/map-led-v4/captions_semantic_v4.json','narration/alignment_manifest_v2.json','research/map-led-v5/analysis.json','research/alternatives-v5/comparison.json','research/outside-comparisons-v6/comparison.json','research/outside-geo-v6/geometry.json']
manifest={'revision':'map-led-v6','source_script_sha256':read(E/'narration/alignment_manifest_v2.json')['source_script_sha256'],'audio_revision':'audio-v2','duration_frames':p['duration_frames'],'fps':30,'duration_s':p['duration_frames']/30,'inputs':[dict(path=x,sha256=hashlib.sha256((E/x).read_bytes()).hexdigest()) for x in inputs],'assets':p['assets'],'rights':{'official_plans':'남양주시 공공누리3유형 원본 전체 contain 표시, 자막/핀/도형은 원본과 분리','geographic_locator':'OSM 실제 도로·하천 선형 및 LH 공식 안내점, 경계·출입구 아님','planned_facility_relationship':'LH 공고 주변 배치 문장을 축척 없는 자체 관계도로 표시, 정밀 지리도 아님','outside_geometry':'© OpenStreetMap contributors, ODbL 1.0; 주요도로·하천 중심선','music':'Data City Ambient v1 자체 합성, 기존 license 원본 확인'},'optional_image_gaps':[dict(request_id='GAP-M002-01',fallback='검증 위치지도+산업단지 승인·준공목표 조건 표시',generated=False),dict(request_id='GAP-M005-01',fallback='원본계획도+검증 배치관계+입주/개교목표 조건',generated=False)],'cost':{'new_voice_actual_credits':2751,'new_voice_approved_cap':8255,'new_image_calls':0,'local_edit_render_usd':0},'review_limits':['실제 음성 청취·연속재생 미실시','자막은 제공 원본 문자 타임스탬프 exact span 매핑','마지막 문장부호만 PCM+80ms인 공급자 타임스탬프를 PCM 끝으로 제한; 발화 문자 미절단','계획 개통·개교·입주는 목표와 예정이며 운영 상태와 구분']}
save(O/'source_license_manifest.json',manifest);save(O/'scene_shot_manifest.json',read(H/'timing_lock.json'));save(O/'semantic_captions.json',read(H/'aligned_captions.json'))
code=[R/'video/src/NamyangjuMapLedV6.tsx',*sorted((R/'video/src/namyangju-map-led-v6').glob('*'))]
save(O/'project_source_hashes.json',[{'path':str(x.relative_to(R)).replace('\\','/'),'sha256':hashlib.sha256(x.read_bytes()).hexdigest()} for x in code if x.is_file()])
save(H/'music_plan.json',{'revision':'map-led-v6-music-locked','audio_revision':'audio-v2','fps':30,'intro_lead_frames':45,'instrumental_tail_frames':270,'narration_volume':.9,'regions':p['music_regions'],'ducking':'frame-driven smooth envelope with 6-frame pre-attack and 12-frame post-release','actual_listening':False,'proof_objective_check':'qa/map-led-v6/proof_audio_check.json'})
save(O/'music_mix_schedule.json',read(H/'music_plan.json'))
shutil.copy2(R/'video-agent-studio/guides/지역_상세지도와_의미단위_자막.md',O/'지역_상세지도와_의미단위_자막.md')
shutil.copy2(E/'narration/generation_ledger_v2.json',O/'audio_cost_ledger.json')
save(H/'source_validation.json',dict(timeline_contiguous=True,scenes=len(p['scenes']),chapters=11,cues=269,no_gap_cards=True,source_sha=manifest['source_script_sha256']))
print('sources packaged, 48 contiguous shots / 269 exact-timestamp captions')
