from pathlib import Path
import json
e=Path(__file__).resolve().parent
p=e/'state.json';s=json.loads(p.read_text(encoding='utf-8'))
s.update(stage='rail_route_proof_preparation',active_tasks=['rail_route_research','rail_route_editor'],requested_output='standalone_rail_route_proof_v1',full_video_patch_authorized=False,proof_review_required_before_full_patch=True)
p.write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8')
p=e/'decisions.json';d=json.loads(p.read_text(encoding='utf-8'));d['decisions'].append({'decision_id':'NYJ-RAIL-PROOF-20261015-01','status':'approved_direct_user_instruction','scope':'Standalone clip near 2min: rail overlays and one apartment walking/bus route animation; preserve v3 and await proof review before merge','input_versions':['script-v2','audio-v1','video-v3'],'full_video_patch_authorized':False,'paid_generation_authorized':False});p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
print('standalone proof registered; full patch awaits user review')
