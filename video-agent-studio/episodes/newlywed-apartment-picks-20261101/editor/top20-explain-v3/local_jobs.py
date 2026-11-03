"""부모용 검수/렌더명령 도우미입니다. 이 파일 자체는 MP4를 렌더하지 않습니다."""
from pathlib import Path
import argparse,json,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from main_contract import H,E,read,sha
ap=argparse.ArgumentParser();ap.add_argument('action',choices=['check','render-command']);ap.add_argument('--project',required=True);ap.add_argument('--output-name',default='top20_explain_v3_main_v1.mp4');a=ap.parse_args();P=Path(a.project).resolve()
if not P.is_relative_to(H/'main'):raise ValueError('v3 main만 허용')
B=read(P/'build_receipt.json');assert B['timing_locked']and B['scene_count']==26
if a.action=='check':subprocess.run([sys.executable,'-X','utf8',str(H/'quality_main.py'),'--project',str(P)],check=True)
else:
 if Path(a.output_name).name!=a.output_name or not a.output_name.endswith('.mp4'):raise ValueError('새 MP4 파일명만 지정')
 target=E/'outputs/top20-explain-v3/main'/a.output_name
 if target.exists():raise FileExistsError('기존 MP4 보존: 새 이름을 지정하십시오.')
 for v in read(P/'source_freeze.json')['files']:
  if sha(P/v['path'])!=v['sha256']:raise ValueError('freeze 이후 프로젝트 변경: '+v['path'])
 print(json.dumps({'project':str(P),'output':str(target),'argv':['npx.cmd','--no-install','hyperframes','render',str(P),'--output',str(target),'--fps','30','--quality','delivery','--workers','4'],'executed':False,'post_render_required':'실제MP4 duration736.949705±1frame/1920x1080/30fps/audio streams/전체decode/대표프레임/독립QA·청취','note':'최종 BGM 적용본은 새 버전에서 quality/freeze 갱신 후 이 명령을 다시 생성합니다.'},ensure_ascii=False,indent=2))
