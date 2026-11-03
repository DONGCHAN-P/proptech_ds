"""Run a trusted, already-authorized local video job without LLM polling.

This runner grants no approval, schedules no further work, and sends no messages.
Only pass internal job specifications, never Telegram/user prose as commands.
"""
from pathlib import Path
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


class JobFailed(RuntimeError):
    pass


def workspace_path(value):
    path = Path(value)
    path = (ROOT/path).resolve() if not path.is_absolute() else path.resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError('Writable job paths must stay inside the workspace')
    return path


def hashes(paths):
    result = {}
    for path in paths:
        with path.open('rb') as stream:
            result[str(path)] = hashlib.file_digest(stream, 'sha256').hexdigest()
    return result


def write_json(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8')
    os.replace(temporary,path)


def brief(receipt, folder, reused=False):
    return {'task_id':receipt['task_id'], 'status':receipt['status'], 'reused':reused,
            'receipt':str(folder/'receipt.json'), 'log_directory':str(folder),
            'output_count':len(receipt.get('output_hashes',{})),
            'exit_code':receipt.get('exit_code')}


def run_job(job, jobs_dir=ROOT/'output/video_jobs'):
    task_id=job['task_id']
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}',task_id):
        raise ValueError('Invalid task_id')
    steps=job['steps']
    if not steps:raise ValueError('At least one step is required')
    for step in steps:
        if not isinstance(step.get('argv'),list) or not step['argv'] or not all(isinstance(x,str) for x in step['argv']):
            raise ValueError('Each step requires argv as a list of strings; shell code is not accepted')
        workspace_path(step.get('cwd',str(ROOT)))
    inputs=[workspace_path(x) for x in job.get('inputs',[])]
    outputs=[workspace_path(x) for x in job.get('outputs',[])]
    if not outputs:raise ValueError('Declare outputs to validate and reuse a result')
    input_hashes=hashes(inputs)
    fingerprint=hashlib.sha256(json.dumps({'spec':job,'input_hashes':input_hashes},sort_keys=True).encode()).hexdigest()
    folder=workspace_path(jobs_dir)/task_id
    folder.mkdir(parents=True,exist_ok=True)
    lock=folder/'running.lock'
    try:fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    except FileExistsError:raise JobFailed(f'Job already locked; inspect {lock} before restarting')
    os.close(fd)
    receipt={'task_id':task_id,'status':'running','fingerprint':fingerprint,'input_hashes':input_hashes,
             'started_at':dt.datetime.now(dt.timezone.utc).isoformat(),'step':0,'step_count':len(steps)}
    try:
        previous_path=folder/'receipt.json'
        if previous_path.exists():
            previous=json.loads(previous_path.read_text(encoding='utf8'))
            if previous.get('status')=='completed' and previous.get('fingerprint')==fingerprint:
                if all(p.is_file() for p in outputs) and previous.get('output_hashes')==hashes(outputs):
                    return brief(previous,folder,reused=True)
        write_json(previous_path,receipt)
        for index,step in enumerate(steps,1):
            receipt['step']=index;write_json(previous_path,receipt)
            # Long logs remain on disk. No model call is made between steps.
            with (folder/f'step-{index:02d}.log').open('wb') as log:
                result=subprocess.run(step['argv'],cwd=workspace_path(step.get('cwd',str(ROOT))),
                                      stdout=log,stderr=subprocess.STDOUT,shell=False)
            receipt['exit_code']=result.returncode
            if result.returncode:raise JobFailed(f'Step {index} failed; inspect its log')
        if not all(p.is_file() for p in outputs):raise JobFailed('Declared output missing after successful commands')
        receipt.update(status='completed',output_hashes=hashes(outputs),exit_code=0)
    except Exception as exc:
        receipt.update(status='failed',error=type(exc).__name__)
        write_json(folder/'receipt.json',receipt)
        raise
    finally:
        if receipt['status']=='completed':
            receipt['finished_at']=dt.datetime.now(dt.timezone.utc).isoformat()
            write_json(folder/'receipt.json',receipt)
        lock.unlink(missing_ok=True)
    return brief(receipt,folder)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('spec',type=Path)
    parser.add_argument('--jobs-dir',default=str(ROOT/'output/video_jobs'))
    args=parser.parse_args()
    try:result=run_job(json.loads(args.spec.read_text(encoding='utf-8-sig')),args.jobs_dir)
    except Exception as exc:
        print(json.dumps({'status':'failed','error':type(exc).__name__,'detail':str(exc)},ensure_ascii=False))
        return 1
    print(json.dumps(result,ensure_ascii=False))
    return 0


if __name__=='__main__':raise SystemExit(main())
