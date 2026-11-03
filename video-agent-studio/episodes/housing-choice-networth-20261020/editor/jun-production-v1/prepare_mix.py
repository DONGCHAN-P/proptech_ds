"""Reuse the verified canonical carve implementation, on new Jun PCM and clocks only."""
import importlib.util, sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;EP=HERE.parents[1]
spec=importlib.util.spec_from_file_location('frozen_carve',EP/'editor/private-production-v2/prepare_mix.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
old.HERE=HERE;old.OUT=EP/'outputs/jun-production-v1'
if __name__=='__main__':
    result=old.main()
    r=old.read(HERE/'mix_receipt.json');r['audio_revision']='jun-production-v1'
    r['reuse_basis']='carve algorithm reused; every spectrum/level envelope newly measured against actual Jun PCM'
    r['implementation_path']='editor/private-production-v2/prepare_mix.py';r['implementation_sha256']=old.sha(EP/r['implementation_path'])
    old.dump(HERE/'mix_receipt.json',r)
    plan=old.read(old.OUT/'render_plan.json');plan['prepared_mix_receipt']='editor/jun-production-v1/mix_receipt.json';plan['prepared_mix_receipt_sha256']=old.sha(HERE/'mix_receipt.json');old.dump(old.OUT/'render_plan.json',plan)
    sys.exit(result)
