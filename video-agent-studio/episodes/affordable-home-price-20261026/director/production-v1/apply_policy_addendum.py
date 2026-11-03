"""Version fresh primary-source corrections before any script/TTS approval."""
import copy
import hashlib
import html
import json
import re
from pathlib import Path

HERE=Path(__file__).resolve().parent;EP=HERE.parents[1]
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):
    assert not p.exists(),f'Preserve existing revision: {p}'
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

add=read(EP/'research/newborn_reset_addendum_v1.json')
nhuf=EP/'research/evidence/director-newborn-v1/NHUF.html'
text=html.unescape(re.sub('<[^>]+>',' ',nhuf.read_text(encoding='utf-8')))
text=re.sub(r'\s+',' ',text)
match=re.search(r'부부\s*각\s*1인의\s*소득이\s*1\.3억원\s*이하',text)
assert match,'Fresh fund source must explicitly support each-partner income cap.'
add['new_claims'][1]['exact_conditions']=add['new_claims'][1]['exact_conditions'].replace('2026.08.11','2026.10.19')
assert any('2026.10.19' in frag['context'] for s in add['sources'] if s['source_id']=='KB' for frag in s['fragments'] if frag['term']=='0.75')
add['new_claims'].append({'claim_id':'N01B','statement':'맞벌이 기본 소득요건은 합산2억원 이하와 부부 각1인1억3천만원 이하입니다.',
    'source':'현행 주택도시기금 원문의 각1인 명시를 적용. 수탁은행의1인 표현을 적어도한명으로 확대하지 않음.',
    'fresh_primary_context':text[max(0,match.start()-100):match.end()+100]})
add['revision']='v2_each_partner_income_and_current_20261019_rate_note'
save(EP/'research/newborn_policy_addendum_v2.json',add)
facts=copy.deepcopy(read(EP/'research/facts.json'))
for row in facts['facts']:
    if row['claim_id']=='N01':
        row['exact_conditions']='접수일기준2년내출산,2023-01-01이후출생; 입양아는접수일현재만2세미만. 무주택세대주 구입용도. 외벌이합산1.3억이하,맞벌이합산2억이하이며부부각1인의소득1.3억이하. 특별공급/우선공급 나이예외는별도.'
        row['value'].pop('one_partner_dual_income_max',None)
        row['value']['each_partner_dual_income_max']=1.3
        row['source_ids']=['DIRECTOR_CURRENT_NHUF','DIRECTOR_CURRENT_KB']
        row['evidence_locations']=[{'source_id':'DIRECTOR_CURRENT_NHUF','location':'현재HTML 맞벌이 설명/출산범위; evidence/director-newborn-v1/NHUF.html'},
                                   {'source_id':'DIRECTOR_CURRENT_KB','location':'입양자격 및 A1금리; evidence/director-newborn-v1/KB.html'}]
        row['director_correction']='N01A/N01B; copied v1 source pack retained unchanged.'
facts['facts'].append({'claim_id':'N05A','statement':add['new_claims'][1]['statement'],
    'exact_conditions':add['new_claims'][1]['exact_conditions'],
    'value':{'initial_B_rate':0.029,'basic_special_years':5,'current_schedule_spread_pp':0.75,'B_reset_example_rate':0.0365},
    'source_ids':['DIRECTOR_CURRENT_KB','DIRECTOR_CURRENT_NHUF'],'status':'verified','effective_status':'effective',
    'qualification':'현재접수시점금리표를적용한B기본금리 예시. 추가출산·우대·중도상환0.60회상환잔액/남은300개월 재계산.'})
facts['revision']='v2_director_fresh_primary_correction'
save(EP/'research/facts_v2.json',facts)
basis=read(HERE/'review_basis.json')
fields=['claim_id','statement','value','unit','status','effective_status','exact_conditions','qualification','source_ids']
basis['facts']=[{k:r[k] for k in fields if k in r} for r in facts['facts']]
basis['director_primary_addendum']=add
basis['case_B_after_5years']=add['case']
basis['primary_source_correction']='The current fund page explicitly says each partner <=1.3eok for dual-income eligibility. This version overrides the copied v1 shorthand.'
basis['evidence_files_sha256']['research/facts_v2.json']=sha(EP/'research/facts_v2.json')
basis['evidence_files_sha256']['research/newborn_policy_addendum_v2.json']=sha(EP/'research/newborn_policy_addendum_v2.json')
save(HERE/'review_basis_v2.json',basis)
p=HERE/'financial_review_context.py';code=p.read_text(encoding='utf-8').replace("/'review_basis.json'","/'review_basis_v2.json'").replace('신생아2.9%초기5년','신생아2.9%초기5년·현재접수표0.75%p가산·잔액346755901원/300개월3.65%월1763962원예시')
p.write_text(code,encoding='utf-8')
print(json.dumps({'facts':len(facts['facts']),'basis_sha256':sha(HERE/'review_basis_v2.json'),
                  'script_or_audio_changed':False,'primary_fresh_sources_cached':2}))
