from pathlib import Path
import shutil,json,hashlib,runpy
E=Path(__file__).resolve().parent;EP=E.parents[1];OLD=E.parent/'review-v4';O=EP/'outputs/production-v5'
(O/'audio').mkdir(parents=True,exist_ok=True)
shutil.copytree(OLD/'source',E/'source',dirs_exist_ok=True)
for n in ['prepare_audio.py','timeline.py','prepare_visual.py','assemble.py','generate.ps1','render.cjs']:
 s=(OLD/n).read_text(encoding='utf8').replace('production-v4','production-v5').replace('units_v4.json','units_v5.json').replace('scenes_v4.json','scenes_v5.json').replace('script-v4-free','script-v5-free').replace('gyosan_v4.srt','gyosan_v5.srt').replace("tag='v4r1'","tag='v5'").replace('gyosan_review_v4r1_free_tts.mp4','gyosan_review_v5_free_tts.mp4')
 (E/n).write_text(s,encoding='utf8')
runpy.run_path(str(E/'prepare_audio.py'))
old=json.loads((OLD/'units_prepared.json').read_text(encoding='utf8'));new=json.loads((E/'units_prepared.json').read_text(encoding='utf8'));by={u['spoken_text']:u for u in old};records=[]
for u in new:
 prev=by.get(u['spoken_text']);dest=O/'audio'/u['file']
 if prev:
  src=EP/'outputs/production-v4/audio'/prev['file'];shutil.copyfile(src,dest)
  records.append(dict(unit_id=u['unit_id'],reused=True,source=str(src),sha256=hashlib.file_digest(dest.open('rb'),'sha256').hexdigest()))
 else:records.append(dict(unit_id=u['unit_id'],reused=False,text=u['text'],spoken_text=u['spoken_text']))
(E/'audio_reuse.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(dict(total=len(new),reused=sum(r['reused'] for r in records),new=sum(not r['reused'] for r in records))))
