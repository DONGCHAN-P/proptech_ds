"""Apply the common caption-rail fix without rebuilding audio or other visuals."""
from pathlib import Path
import hashlib,json,re,sys
EP=Path(__file__).resolve().parents[2]
H=EP/'editor/top20-production-v1'
sys.path.insert(0,str(H))
from caption_backgrounds import body_windows,markup
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
backup=H/'evidence/caption-bg-before';backup.mkdir(exist_ok=True)
changed=[]
for kind,project in [('main',H/'main'),('promo',H/'shorts/promo'),('analysis',H/'shorts/analysis')]:
    captions=read(project/'caption_mapping.json')['cues']
    if kind=='main':
        timeline=read(H/'timeline_resolved.json')
        windows=body_windows(timeline['scenes'],max(c['end_s'] for c in captions))
        path=project/'scenes/CAPTIONS.html'
    else:
        windows=[[0,max(c['end_s'] for c in captions)]]
        path=project/'scenes'/(kind+'-CAPTIONS.html')
    before=path.read_text(encoding='utf-8');assert 'data-caption-bg=' not in before
    old=backup/(kind+'_CAPTIONS.html');old.write_text(before,encoding='utf-8')
    match=re.search(r'<div\b[^>]*\bdata-composition-id="[^"]+"[^>]*>',before);assert match
    after=before[:match.end()]+markup(windows,kind,kind!='main')+before[match.end():]
    path.write_text(after,encoding='utf-8')
    changed.append({'id':kind,'file':str(path),'before_sha256':sha(old),'after_sha256':sha(path),'persistent_windows_s':windows,'captions_unchanged':True,'audio_unchanged':True})
(H/'evidence/caption_background_fix.json').write_text(json.dumps(changed,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(changed,ensure_ascii=False))
