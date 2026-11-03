"""Build private-release metadata from measured chapter offsets, without uploading."""
import argparse
import hashlib
import json
from pathlib import Path

EP = Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser()
parser.add_argument('--source-dir',default='outputs/private-production-v1')
parser.add_argument('--release-dir',default='outputs/private-release-v1')
parser.add_argument('--timing',default='narration/free-tts-v1/final_timing.json')
args=parser.parse_args()
SOURCE=(EP/args.source_dir).resolve()
OUT=(EP/args.release_dir).resolve()
assert SOURCE.is_relative_to(EP) and OUT.is_relative_to(EP)
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
timing_path=(EP/args.timing).resolve()
assert timing_path.is_relative_to(EP) and timing_path.is_file()
timing = read(timing_path)
edl = read(SOURCE / 'assembly_edl.json')
assert edl['status'] == 'measured_audio_units'
titles = {c['chapter']:c['title'] for c in timing['chapters']}
chapters = []
for segment in edl['segments']:
    if segment['id'] == 'opening_hook' or segment['id'].startswith('chapter_') and segment['id'] != 'chapter_1_after_hook':
        seconds = int(segment['global_start_s'])
        stamp = f'{seconds//60:02d}:{seconds%60:02d}'
        chapters.append({'chapter':segment['chapter'], 'start_s':segment['global_start_s'], 'timestamp':stamp, 'title':titles[segment['chapter']]})
assert len(chapters)==10 and chapters[0]['start_s']==0
body = (OUT / 'description_draft.md').read_text(encoding='utf-8').rstrip()
description = body + '\n\n타임라인\n' + '\n'.join(f"{c['timestamp']} {c['title']}" for c in chapters) + '\n'
assert len(description.encode('utf-8')) <= 5000
(OUT / 'description_measured.md').write_text(description, encoding='utf-8')
metadata = read(OUT / 'metadata_draft.json')
metadata.update(description='description_measured.md', chapters=chapters,
    timing_basis='measured_audio_and_brand_EDL; final encoded media QA pending',
    edl_sha256=hashlib.sha256((SOURCE / 'assembly_edl.json').read_bytes()).hexdigest(),
    description_bytes=len(description.encode('utf-8')))
(OUT / 'metadata_measured.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'chapters':len(chapters), 'description_bytes':metadata['description_bytes'], 'upload':False}))
