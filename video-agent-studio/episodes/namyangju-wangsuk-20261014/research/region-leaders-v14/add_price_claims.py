import json,pathlib
p=pathlib.Path(__file__).parent;f=json.loads((p/'facts.json').read_text(encoding='utf-8'));c=json.loads((p/'candidates.json').read_text(encoding='utf-8'))
for r in c['candidates']:
 if r['id']not in['W1-B1','W1-B2']:continue
 q=r['price_example'];f['claims'].append(dict(claim_id='V14-PRICE-'+r['id'],sentence=r['id']+'의84A84.92㎡5층이상기본공급금액은'+str(q['price_won'])+'원이며발코니확장8455000원·옵션·세금은별도이다.',source_url=r['source_url'],source_file=r['source_file'],evidence_location='공고p6/7가격표·p8발코니확장표',reference_date='2025-07-29',verified_on='2026-10-15',status='verified',statistic='specific_published_unit_type_floor_example_not_mean',area_m2=84.92,floor='5층이상',unit='원',sample_count=1,qualification='분양가사례;2026현매매시세/시장평균아님'))
(p/'facts.json').write_text(json.dumps(f,ensure_ascii=False,indent=2),encoding='utf-8');print('price claims added')
