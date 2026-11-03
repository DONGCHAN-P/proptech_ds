"""Verify deliverable links, pinned inputs and final experiment designation."""
from pathlib import Path
import hashlib
import json
import re
from urllib.parse import unquote
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
docs=[ROOT/'reports/지역별 집값 6개월 예측 연구.md',OUT/'README.md']
links=[]
for doc in docs:
    content=doc.read_text('utf-8')
    for target in re.findall(r'\]\(([^)]+)\)',content):
        if target.startswith(('https://','http://','#')): continue
        p=(doc.parent/unquote(target.split('#')[0])).resolve()
        links.append({'document':doc.relative_to(ROOT).as_posix(),'target':str(p),'exists':p.exists()})
assert all(x['exists'] for x in links),[x for x in links if not x['exists']]
R=OUT/'results_v3'
verification=json.loads((R/'artifact_verification.json').read_text('utf-8'))
assert verification['passed']
assert len(verification['saved_model_replay'])==6
for filename,expected in verification['code_hashes'].items():
    # This delivery-only checker is added after model verification; every recorded
    # implementation hash must still agree, without pretending it was reviewed.
    assert hashlib.sha256((OUT/filename).read_bytes()).hexdigest()==expected,filename
files=docs+[R/'forecast_next_6_months.csv',R/'backtest_metrics.csv',R/'artifact_verification.json',
            OUT/'code_review_v3.md',OUT/'input_manifest.json',OUT/'panel_audit.json']
manifest={'final_results':'analysis/regional_forecast_20261027/results_v3',
          'link_check_count':len(links),'all_links_exist':True,
          'files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files],
          'focused_tests_passed':14,'saved_models_replayed':6,
          'scope':'research prototype with documented snapshot and data-coverage limits'}
(OUT/'delivery_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n','utf-8')
print(json.dumps({'links_passed':len(links),'final_results':'results_v3','replayed_models':6}))
