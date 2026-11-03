from pathlib import Path
import json,hashlib,sys
from PIL import Image
sys.stdout.reconfigure(encoding='utf-8');root=Path(__file__).parent
a=json.loads((root/'assets_v4.json').read_text('utf-8'));a['revision']='visual-v5'
p=json.loads((root/'gpt-generated-v1/prompts.json').read_text('utf-8'));c=json.loads((root/'citations_v4.json').read_text('utf-8'))
for key,id,filename,scenes in [('commute','GPT_CONCEPT_COMMUTE','AI_S004_commute_v1.png',['S004']),('workplace','GPT_CONCEPT_WORKPLACE','AI_S005_workplace_v1.png',['S005']),('family','GPT_CONCEPT_FAMILY','AI_S006_family_v1.png',['S006'])]:
 file=root/'gpt-generated-v1'/filename;im=Image.open(file);im.verify();dims=Image.open(file).size
 item={'asset_id':id,'scene_ids':scenes,'type':'ai_concept','source_or_prompt':{'tool':p['tool'],'generation_mode':p['generation_mode'],'exact_prompt':p['prompts'][key],'prompt_file':'visual/gpt-generated-v1/prompts.json'},'dimensions':list(dims),'actual_file':'visual/gpt-generated-v1/'+filename,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'actual_place':None,'AI':True,'AI_label':'AI 개념 이미지 · 실제 왕숙 촬영 아님','usage_conditions':'이번 영상용 신규 내장 image_gen 생성. 가상의 생활 장면. 남양주 실제 장소·특정기업 운영·계획학교 개교·역 출입구·미래 완공 증거로 사용 금지. 기존 사용자 소유 AI 두 장과 출처 구분. 외부 유료 API 호출 없음.','review_status':'총괄 실제 생성·육안검수 전달받음; 시각담당 파일 실존·PNG 디코딩·해상도·SHA256 확인','motion':'still_motion; modest image pan/zoom/crop allowed with persistent AI label','placement':'62샷 중 해당 주제의 AI 슬롯에만 사용; 여러 crop을 사용해도 같은 원본이라는 점 유지'}
 a['assets'].append(item);c[id]={k:item[k] for k in ['source_or_prompt','sha256','dimensions','AI','AI_label','actual_place','usage_conditions']}
a['known_limitations']=[x for x in a['known_limitations'] if 'ROOT 신규GPT' not in x]
(root/'assets_v5.json').write_text(json.dumps(a,ensure_ascii=False,indent=2),'utf-8');(root/'citations_v5.json').write_text(json.dumps(c,ensure_ascii=False,indent=2),'utf-8')
assert len(a['assets'])==22
for x in a['assets']:
 actual=Path(x['actual_file']);assert (actual if actual.is_absolute() else root.parent/actual).exists()
print(json.dumps({'actual_assets':len(a['assets']),'new_ai':[{k:x[k] for k in ['asset_id','dimensions','sha256']} for x in a['assets'][-3:]]}))
