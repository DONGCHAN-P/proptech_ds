from pathlib import Path
import shutil,json,hashlib,subprocess
EP=Path(__file__).resolve().parents[1];R=EP.parents[2];O=EP/'outputs/release-prep-v1';O.mkdir(parents=True,exist_ok=True)
bg=R/'video-agent-studio/assets/chapter-backgrounds/v1/comparison.png'
template=R/'video-agent-studio/assets/thumbnail-series/v1/template.html'
text=template.read_text(encoding='utf8').replace('{{REGION}}','하남').replace('{{DISTRICT}}','교산').replace('{{QUESTION}}','대장 후보는?').replace('{{BACKGROUND_URI}}',bg.resolve().as_uri())
html=O/'thumbnail.html';html.write_text(text,encoding='utf8')
chrome=R/'video/node_modules/.remotion/chrome-headless-shell/win64/chrome-headless-shell-win64/chrome-headless-shell.exe'
cmd=[str(chrome),'--headless','--no-sandbox','--hide-scrollbars','--allow-file-access-from-files','--window-size=1280,720','--virtual-time-budget=2000','--screenshot='+str((O/'thumbnail.png').resolve()),html.resolve().as_uri()]
p=subprocess.run(cmd,capture_output=True);assert p.returncode==0,p.stderr[-1500:]
record=dict(format_reference='assets/thumbnail-series/v1/template.html',template_sha256=hashlib.sha256(template.read_bytes()).hexdigest(),background=str(bg),background_sha256=hashlib.sha256(bg.read_bytes()).hexdigest(),ai_concept_not_actual_location=True,new_paid_generation=False,file='thumbnail.png',sha256=hashlib.sha256((O/'thumbnail.png').read_bytes()).hexdigest())
(O/'thumbnail_manifest.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8');print('reused channel typography + existing AI concept asset; no paid generation')
