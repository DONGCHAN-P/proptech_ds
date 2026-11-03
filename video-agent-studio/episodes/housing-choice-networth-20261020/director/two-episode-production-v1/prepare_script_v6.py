"""Clarify two spoken terms, retaining all approved financial content."""
import hashlib
import json
from pathlib import Path
EP=Path(__file__).resolve().parents[2]
previous=EP/'outputs/script-final-v5/script_v5.md'
source=previous.read_text(encoding='utf-8')
assert hashlib.sha256(previous.read_bytes()).hexdigest()=='babeb15213477f3f6dcb8e8ab958e1a4ccc691c53c1fca6ca9ceae99cc5f269b'
changes=[
    {'chapter':5,'before':'원금 상환의 효과는 줄어든 빚에 반영합니다.','after':'원금 상환의 효과는 줄어든 대출잔액에 반영합니다.','paragraph_id':'C05_P023'},
    {'chapter':6,'before':'원화 자산은 1.1배에 1.1배를 곱한 1.21배가 됩니다.','after':'한국 돈으로 환산한 자산은 1.1배에 1.1배를 곱한 1.21배가 됩니다.','paragraph_id':'C06_P027'}
]
for change in changes:
    assert source.count(change['before'])==1
    source=source.replace(change['before'],change['after'])
folder=EP/'outputs/script-final-v6'
folder.mkdir(exist_ok=True)
target=folder/'script_v6.md'
if target.exists():
    assert target.read_text(encoding='utf-8')==source
else:
    with target.open('w',encoding='utf-8',newline='') as stream:
        stream.write(source)
result={'revision':'script-final-v6','previous_sha256':hashlib.sha256(previous.read_bytes()).hexdigest(),
    'script_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'changes':changes,
    'reason':'Targeted small+medium ASR found shared lexical ambiguity; no numeric discrepancy remains. Clear synonyms are used for two spoken terms.',
    'financial_values_and_model':'unchanged','all_other_paragraphs':'unchanged','TTS_before_dual_content_approval':False}
(folder/'changes.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'script':target.relative_to(EP).as_posix(),'sha256':result['script_sha256'],'changes':len(changes)},ensure_ascii=False))
