"""Two-second local export smoke of the actual carved opening. Never a full chapter."""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;EP=HERE.parents[1];ROOT=EP.parents[2];OUT=EP/'outputs/private-production-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    source=OUT/'ch01';target=OUT/'render-smoke-v1';target.mkdir(exist_ok=True)
    page=(source/'index.html').read_text(encoding='utf8')
    page,count=re.subn(r'(data-composition-id="main" data-start="0" data-duration=")[^"]+',r'\g<1>2',page,count=1)
    if count!=1:raise ValueError('Cannot set a finite 2-second smoke duration')
    (target/'index.html').write_text(page,encoding='utf8')
    for n in ['hyperframes.json','meta.json','package.json']:shutil.copy2(source/n,target/n)
    for f in (source/'assets').rglob('*'):
        if not f.is_file():continue
        p=target/'assets'/f.relative_to(source/'assets');p.parent.mkdir(parents=True,exist_ok=True)
        if not p.exists():os.link(f,p)
        if sha(p)!=sha(f):raise ValueError('Smoke dependency differs from source')
    ffmpeg=OUT/'media-bin/ffmpeg.exe';probe=ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
    env=os.environ.copy();env['PATH']=str(ffmpeg.parent)+os.pathsep+str(probe.parent)+os.pathsep+env['PATH'];env['DO_NOT_TRACK']='1'
    cli=shutil.which('hyperframes.cmd');output=target/'actual_carve_2s_smoke.mp4'
    command=[cli,'render','.', '--fps','30','--quality','draft','--workers','2','--browser-gpu','--output',str(output),'--frames-cache-dir',str(target/'frames-cache')]
    if output.exists():raise ValueError('Preserve existing smoke output; do not overwrite')
    print('running 2-second actual-carve export smoke',flush=True)
    with (target/'render.log').open('w',encoding='utf8') as log:completed=subprocess.run(command,cwd=target,env=env,stdout=log,stderr=subprocess.STDOUT)
    result={'status':'failed' if completed.returncode else 'encoded_pending_probe','source_html_sha256':sha(source/'index.html'),'smoke_html_sha256':sha(target/'index.html'),'duration_s':2,'argv':command,'returncode':completed.returncode,'actual_listening':False,'full_chapter_or_full_episode':False}
    if completed.returncode:
        (HERE/'render_smoke_receipt.json').write_text(json.dumps(result,indent=2),encoding='utf8');return completed.returncode
    result['ffprobe']=json.loads(subprocess.check_output([str(probe),'-v','error','-show_format','-show_streams','-of','json',str(output)]))
    decoded=subprocess.run([str(ffmpeg),'-v','error','-i',str(output),'-f','null','-'],capture_output=True,text=True)
    result['decode_returncode']=decoded.returncode;result['decode_stderr']=decoded.stderr
    if decoded.returncode or decoded.stderr or abs(float(result['ffprobe']['format']['duration'])-2)>.06:raise ValueError('Smoke decode/duration failed')
    if not any(s['codec_type']=='audio' for s in result['ffprobe']['streams']):raise ValueError('Smoke audio stream missing')
    result.update(status='2s_actual_carve_export_and_decode_pass',file=str(output),output_sha256=sha(output))
    (HERE/'render_smoke_receipt.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'status':result['status'],'file':str(output)}));return 0


if __name__=='__main__':sys.exit(main())
