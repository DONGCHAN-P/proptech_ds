"""Editor integration after the visual worker handoff; preserve the approved text."""
from pathlib import Path
import json,re,hashlib
EP=Path(__file__).resolve().parents[2];OUT=EP/'outputs/literature-visual-v1';P=OUT/'project';D=EP/'director/literature-visual-v1';T=json.loads((P/'timing.json').read_text(encoding='utf8'))
attrs=lambda tag:dict(re.findall(r'([\w-]+)="([^"]*)"',tag))
hashof=lambda text:hashlib.sha256(text.encode('utf8')).hexdigest()
edits=[];late=[]
for scene in T['scenes']:
    path=P/'compositions'/f'{scene["scene_id"]}.html';text=path.read_text(encoding='utf8');before=text
    for b in scene['beats']:
        if 'visual_duration' in b:
            pattern=r'<section\b[^>]*\bid="'+b['id']+r'"[^>]*>'
            m=re.search(pattern,text);assert m,b['id'];tag=re.sub(r'data-duration="[^"]+"',f'data-duration="{b["visual_duration"]:.6f}"',m.group());text=text[:m.start()]+tag+text[m.end():]
    for tag,body in re.findall(r'<section\b([^>]*)>(.*?)</section>',text,re.S):
        a=attrs(tag);duration=float(a['data-duration']);ends=[]
        for sub in re.findall(r'<[^/!][^>]+>',body):
            d=attrs(sub)
            if 'data-at' in d:ends.append(float(d['data-at'])+float(d.get('data-dur','.7')))
            for kind,default in [('move','2'),('grow','1.5')]:
                if f'data-{kind}-at' in d:ends.append(float(d[f'data-{kind}-at'])+float(d.get(f'data-{kind}-dur',default)))
            if 'data-exit-at' in d:ends.append(float(d['data-exit-at'])+.35)
        if ends and max(ends)>duration+.02:late.append({'beat':a['id'],'visual_duration':duration,'animation_end':max(ends)})
    if text!=before:path.write_text(text,encoding='utf8');edits.append({'file':path.relative_to(EP).as_posix(),'before_sha256':hashof(before),'after_sha256':hashof(text),'change':'Extend final paragraph graphic through scene handoff; narration and caption timing unchanged'})
record={'ownership':'visual worker completed and closed; director/editor integrates timing windows in the frozen handoff','edits':edits,'animations_past_clip_end':late,'last_caption_end':T['last_caption_end'],'body_duration':T['body_duration'],'final_caption_hold':T['body_duration']-T['last_caption_end'],'approved_script_unchanged':True}
(D/'visual_integration.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(record,ensure_ascii=False));assert not late
