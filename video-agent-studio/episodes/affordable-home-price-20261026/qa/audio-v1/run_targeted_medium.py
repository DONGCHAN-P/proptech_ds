"""Only flagged new-episode paragraphs; load fixed offline medium once."""
import sys
from pathlib import Path
from types import SimpleNamespace
sys.dont_write_bytecode=True
QA=Path(__file__).resolve().parent
sys.path.insert(0,str(QA))
import run_asr
from prepare import read

if __name__=='__main__':
    cfg=read(QA/'config.json');run_asr.gate(cfg)
    original=run_asr.runtime;cache={}
    def cached(c,name):
        if name not in cache:cache[name]=original(c,name)
        return cache[name]
    run_asr.runtime=cached
    for p in sorted((QA/'runs').glob('ch*-small-*/report.json')):
        if read(p)['medium_candidates']:
            run_asr.run_medium(SimpleNamespace(small_report=str(p),scenes=None),cfg)
