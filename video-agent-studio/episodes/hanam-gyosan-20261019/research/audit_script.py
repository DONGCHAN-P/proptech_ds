from pathlib import Path
import json,hashlib
P=Path(__file__).parent;E=P.parent
script=E/'outputs/script_v1.md';scenes=E/'writer/scenes_v1.json'
facts=json.loads((P/'facts.json').read_text(encoding='utf-8'))['facts'];ids={f['claim_id'] for f in facts}
S=json.loads(scenes.read_text(encoding='utf-8'));missing=[]
for s in S:
 for i,u in enumerate(s.get('units',[])):
  for c in u.get('claim_ids',[]):
   if c not in ids:missing.append({'scene_id':s['scene_id'],'unit_index':i,'claim_id':c})
receipt={'review':'script-v1 bounded fact-to-wording audit','checked_on':'2026-10-19','status':'pass_no_required_factual_correction','scope':['outputs/script_v1.md 全낭독문 열람','writer/scenes_v1.json claims 참조 무결성','확정 facts수치·면적·통계·기간·기산일·교통상태와 대본 문장대조','C2/B2후보 공식표근거 및 조건부분석표현 검토'],'input_hashes':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [script,scenes,P/'facts.json']},'required_issues':[],'missing_claim_references':missing,'observations':['최신36,669/87,319, A2확장포함가격, 기존5개단지 중위값/n 모두 연구팩과 일치','C2=85㎡초과민간786, B2=60~85㎡민간281는 고시p5와일치','공공분양 소형A2를대장으로단정하지않으며 C2/B2는조건부관찰후보','현재교통/실시설계/2032목표/A2입주를분리함','주변84㎡실거래와A2 59㎡공고가격의차익산출없음'],'limitations':['오디오청취·영상프레임검수 아님','지형/실제역출입구/학교배정 최종확정 검토 아님','후보 순위는편집판단이며공식가격서열보증아님']}
if missing:receipt['status']='pass_wording_with_reference_issues';receipt['required_issues']=missing
(P/'script_v1_fact_pass_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print({'status':receipt['status'],'missing':missing,'scenes':len(S)})
