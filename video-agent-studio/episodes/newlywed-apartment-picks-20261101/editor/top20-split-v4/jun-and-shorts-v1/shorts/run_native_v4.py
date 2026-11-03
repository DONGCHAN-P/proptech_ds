"""Two separate 2-worker renders, then SH02; four Chrome render workers maximum."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_native_v4 as b


def command(*args):
    p=subprocess.run([sys.executable,'-X','utf8',str(b.HERE/'pipeline_native_v4.py'),*args])
    if p.returncode:raise RuntimeError(f'Local render/check failed: {args}; exit {p.returncode}')


if __name__=='__main__':
    projects=[b.HERE/'native-v4'/sid for sid in b.IDS]
    outputs=[b.OUT/b.FILENAMES[sid] for sid in b.IDS]
    assert len(set(map(str,projects)))==3 and len(set(map(str,outputs)))==3
    b.save(b.HERE/'native-v4/parallel_safety.json',{'maximum_concurrent_projects':2,'workers_per_project':2,'maximum_render_workers':4,
           'projects':[str(x)for x in projects],'outputs':[str(x)for x in outputs],
           'file_isolation':'Separate project, log, render output, HF state and extract-cache directories for each clip',
           'server_policy':'No fixed preview-server port requested by render CLI; renderer manages per-process local servers',
           'render_order':[['SHORT01-PROMO','SHORT03-R15-R11'],['SHORT02-R20-R16']]})
    command('check','--version','native-v4')
    with ThreadPoolExecutor(max_workers=2)as pool:
        jobs=[pool.submit(command,'deliver','--version','native-v4','--short',sid)for sid in ['SHORT01-PROMO','SHORT03-R15-R11']]
        for job in jobs:job.result()
    command('deliver','--version','native-v4','--short','SHORT02-R20-R16')
