from pathlib import Path
import subprocess,json
EP=Path(__file__).resolve().parents[2];OUT=EP/'outputs/literature-visual-v1';M=json.loads((OUT/'reused_assets.json').read_text(encoding='utf8'));ff=M['ffmpeg']
terms=[f'eq(n,{i})' for i in range(137)]
def balance(items):
    if len(items)==1:return items[0]
    mid=len(items)//2;return '('+balance(items[:mid])+'+'+balance(items[mid:])+')'
results=[]
for label,expr in [('flat137','+'.join(terms)),('balanced137',balance(terms))]:
    cmd=[ff,'-v','error','-f','lavfi','-i','color=c=white:s=16x16:d=0.1:r=30','-vf',f"select='{expr}'",'-f','null','-']
    result=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8');results.append({'case':label,'exit_code':result.returncode,'stderr_tail':result.stderr[-350:]})
(OUT/'checks/encoded/select_diagnostic.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(results,ensure_ascii=False))
