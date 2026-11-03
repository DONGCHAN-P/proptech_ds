"""Pin a concise public/synthetic evidence packet and adapt the proven CLI transport."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
EP=HERE.parents[1]
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
target=HERE/'review_basis.json'
assert not target.exists(),'Preserve the old basis; explicitly version any research correction.'
facts=read(EP/'research/facts.json')
cases=read(EP/'research/verified_case_packet.json')
prepared=EP/'research/prepared-v1'
fact_fields=['claim_id','statement','value','unit','status','effective_status','exact_conditions','qualification','source_ids']
case_fields=['case_id','profile_id','household_id','price_krw','deduction_krw','deduction_note','rate_used','rate_status',
             'limits_krw','binding_constraints','loan_ceiling_krw','transaction_costs','required_loan_krw',
             'cash_required_including_reserve_krw','cash_shortfall_krw','cash_feasible','payment_if_financeable_krw']
affordability=[]
for row in cases['affordability_A']:
    out={k:row[k] for k in ['profile_id','deduction_krw','deduction_note']}
    for name in ['bank_assumptions_max','mortgage_budget_max']:
        out[name]={k:v for k,v in row[name].items() if k!='presentation'}
    affordability.append(out)
basis={'policy_as_of':'2026-10-26','facts':[{k:r[k] for k in fact_fields if k in r} for r in facts['facts']],
       'case_conditions':cases['conditions'],'cases':[{k:r[k] for k in case_fields} for r in cases['cases']],
       'affordability_A':affordability,'conditional_relief_table':cases['conditional_relief_table'],
       'independent_QA':{'arithmetic_comparisons':157,'policy_logic_checks':10,'required_issues':[],
                         'note':'Research/case approval only. The current actual script still needs independent review.'},
       'primary_sources':{v:read(prepared/'next_episode_research'/v) for v in ['sources.json','sources_v2.json']},
       'evidence_files_sha256':{p.relative_to(EP).as_posix():sha(p) for p in [EP/'research/facts.json',EP/'research/verified_case_packet.json',
          prepared/'next_case_independent_arithmetic.json',prepared/'next_policy_independent_qa/policy_and_case_review.json']}}
target.write_text(json.dumps(basis,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=HERE/'claude_review.py';text=p.read_text(encoding='utf-8')
assert 'outputs/growth-explanation-v1/facts.json' in text
text=text.replace('from claude_transport import parse_result','from claude_transport import parse_result\nfrom financial_review_context import build_packet, script_prompt, revision_prompt')
start=text.index('facts=json.loads(');end=text.index('if args.media_report:',start)
text=text[:start]+'packet=build_packet(script,sha,EP)\n'+text[end:]
start=text.index("prompt='''");end=text.index('if args.previous_review:',start)
text=text[:start]+'prompt=script_prompt(packet)\n'+text[end:]
start=text.index('    prompt=',text.index('if args.previous_review:'))
end=text.index("if args.media_report:\n    locked=",start)
text=text[:start]+'    prompt=revision_prompt(packet)\n'+text[end:]
assert 'growth-explanation-v1' not in text and '6%넘으면' not in text
p.write_text(text,encoding='utf-8')
print(json.dumps({'facts':len(basis['facts']),'cases':len(basis['cases']),'basis_bytes':target.stat().st_size,
                  'basis_sha256':sha(target),'external_calls':0}))
