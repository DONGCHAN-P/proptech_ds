"""Prepare title, real chapters, description and selected thumbnail for final QA."""
import datetime as dt
import hashlib
import json
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[5]
HERE=Path(__file__).resolve().parent
EP=HERE.parents[1]
OUT=EP/'outputs/jun-release-v1'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(ROOT).as_posix()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

auth=read(HERE/'authorization.json')
timing=read(EP/'narration/jun-production-v1/final_timing.json')
edl=read(EP/'outputs/jun-production-v1/assembly_edl.json')
assert timing['script_sha256']==auth['script_sha256']
assert len(timing['chapters'])==10
choice_path=HERE/'thumbnail_choice.json'
if choice_path.exists():
    choice=read(choice_path)
else:
    choice={'asset_id':'TH004','basis':'director stated default after optional selection; no user choice asserted',
            'source':'outputs/launch-proposal-v2/TH004_hidden_results_1280x720.png',
            'user_selected':False,'at_utc':dt.datetime.now(dt.timezone.utc).isoformat()}
    save(choice_path,choice)
assert choice['asset_id'] in ['TH003','TH004']
image=(EP/choice['source']).resolve()
assert image.is_relative_to(EP/'outputs/launch-proposal-v2') and image.is_file()
OUT.mkdir(exist_ok=True)
assert not (OUT/'upload_job.json').exists() and not (OUT/'upload_receipt.json').exists(),'Keep frozen release bundle immutable.'
chapters=[]
for ch in timing['chapters']:
    num=ch['chapter']
    starts=[segment['global_start_s'] for segment in edl['segments'] if segment.get('chapter')==num]
    assert starts
    start=min(starts)
    stamp=f'{int(start)//60:02d}:{int(start)%60:02d}'
    chapters.append({'chapter':num,'start_s':start,'timestamp':stamp,'title':ch['title']})
old=EP/'outputs/private-release-v3'
oldmeta=read(old/'metadata_measured.json')
desc=(old/oldmeta['description']).read_text(encoding='utf8').split('\n타임라인\n')[0].rstrip()
desc+='\n\n타임라인\n'+'\n'.join(f"{ch['timestamp']} {ch['title']}" for ch in chapters)+'\n'
assert len(desc.encode('utf8'))<=5000
(OUT/'description_measured.md').write_text(desc,encoding='utf8')
shutil.copy2(image,OUT/'thumbnail.png')
meta={'title':auth['new_title'],'visibility':'private','channel':'데이터로보는부동산',
      'description':'description_measured.md','tags':oldmeta['tags'],'chapters':chapters,
      'scheduled':False,'published':False,'voice':'ElevenLabs Jun','audio_revision':'jun-production-v1',
      'script_sha256':auth['script_sha256'],'timing_sha256':sha(EP/'narration/jun-production-v1/final_timing.json'),
      'thumbnail_asset_id':choice['asset_id'],'thumbnail_choice':rel(choice_path),
      'prepared_at_utc':dt.datetime.now(dt.timezone.utc).isoformat()}
assert 0<len(meta['title'])<=100
save(OUT/'metadata_measured.json',meta)
receipt={'metadata':rel(OUT/'metadata_measured.json'),'metadata_sha256':sha(OUT/'metadata_measured.json'),
         'description':rel(OUT/'description_measured.md'),'description_sha256':sha(OUT/'description_measured.md'),
         'thumbnail':rel(OUT/'thumbnail.png'),'thumbnail_sha256':sha(OUT/'thumbnail.png'),
         'chapters':len(chapters),'selected_thumbnail':choice['asset_id'],'uploaded':False}
save(OUT/'release_inputs_receipt.json',receipt)
print(json.dumps(receipt,ensure_ascii=False))
