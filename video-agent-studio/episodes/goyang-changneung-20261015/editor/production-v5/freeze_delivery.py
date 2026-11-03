from pathlib import Path
import json,hashlib
E=Path(__file__).resolve().parent;EP=E.parent.parent;R=EP.parents[2];O=EP/'outputs/production-v5'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((EP/'outputs/production-v4/source_freeze_v4.json').read_text(encoding='utf-8'));paths={x['path'] for x in old['source_files']}
for folder in ['video/src/changneung-v5','video/public/changneung-v5']:
 paths.update(p.relative_to(R).as_posix() for p in (R/folder).rglob('*') if p.is_file())
for rel in ['visual/semantic-v5/workplace_geometry.json','visual/semantic-v5/verified_missing_locations.json','visual/semantic-v5/company_plan.json','visual/semantic-v5/commute_steps.json','visual/semantic-v5/assets.json','visual/semantic-v5/handoff.json','outputs/production-v5/cue_focus_matrix_v5.json']:
 paths.add((EP/rel).relative_to(R).as_posix())
paths.update(p.relative_to(R).as_posix() for p in E.glob('*.cjs'))
paths.add((E/'assemble_full_v5.py').relative_to(R).as_posix())
files=[{'path':s,'sha256':h(R/s),'bytes':(R/s).stat().st_size} for s in sorted(paths) if (R/s).is_file()]
freeze={'revision':'production-v5','duration_frames':24140,'fps':30,'source_files':files,'audio':old['audio'],'rights_manifest':['visual/semantic-v5/assets.json','research/map-location-v4/source_manifest.json','visual/semantic-v5/verified_missing_locations.json'],'temporary_cache':['editor/production-v5/cache','outputs/production-v5/frames'],'preserved_originals':['outputs/production-v4/changneung_full_v4r2.mp4','narration/audio-v3'],'actual_listening':False,'continuous_playback':False}
(O/'source_freeze_v5.json').write_text(json.dumps(freeze,ensure_ascii=False,indent=2),encoding='utf-8')
primary=[O/'changneung_full_v5r2.mp4',O/'changneung_full_v5.srt',O/'project_v5.json']
(O/'delivery_manifest.json').write_text(json.dumps({'primary':[{'file':p.name,'sha256':h(p),'bytes':p.stat().st_size} for p in primary if p.exists()],'freeze_sha256':h(O/'source_freeze_v5.json'),'actual_listening':False,'continuous_playback':False,'new_upload_authorized':False},ensure_ascii=False,indent=2),encoding='utf-8')
print('입력 동결',len(files),'개 / 존재하는 주산출물 해시 기록')
