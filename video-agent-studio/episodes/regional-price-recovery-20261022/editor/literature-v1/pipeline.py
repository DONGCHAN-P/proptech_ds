from pathlib import Path
import subprocess,sys,json,hashlib,os
from datetime import datetime,timezone
ED=Path(__file__).resolve().parent;EP=ED.parents[1];OUT=EP/'outputs/literature-visual-v1';P=OUT/'project'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
files=[f for f in P.rglob('*') if f.is_file() and '.hyperframes' not in f.parts and 'node_modules' not in f.parts]
frozen={str(f.relative_to(P)):sha(f) for f in files};(OUT/'checks/render_inputs.json').write_text(json.dumps({'at_utc':datetime.now(timezone.utc).isoformat(),'files':frozen},ensure_ascii=False,indent=2),encoding='utf8')
status={'pid':os.getpid(),'stage':'starting','paid_calls':0,'voice_calls':0};status_path=OUT/'checks/pipeline_status.json'
for stage,args in [('render',[ED/'run_cli.py','render']),('assemble',[ED/'assemble.py']),('encoded_qa',[ED/'encoded_qa.py'])]:
    status.update(stage=stage,at_utc=datetime.now(timezone.utc).isoformat());status_path.write_text(json.dumps(status),encoding='utf8');print(json.dumps(status),flush=True)
    result=subprocess.run([sys.executable,'-X','utf8',*map(str,args)])
    if result.returncode:
        status.update(stage='failed',failed_step=stage,exit_code=result.returncode);status_path.write_text(json.dumps(status),encoding='utf8');sys.exit(result.returncode)
changed=[f for f,d in frozen.items() if sha(P/f)!=d]
status.update(stage='complete_pending_independent_qa',inputs_changed_by_cli=changed,at_utc=datetime.now(timezone.utc).isoformat());status_path.write_text(json.dumps(status),encoding='utf8');print(json.dumps(status),flush=True)
