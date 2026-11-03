"""Freeze exact media, packaging and supplied QA evidence for Claude review."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EP = HERE.parents[1]
ROOT = EP.parents[2]
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
rel = lambda p: p.relative_to(ROOT).as_posix()
def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()
def local(value):
    p = (ROOT / value).resolve()
    assert p.is_relative_to(EP) and p.is_file(), value
    return p
def save(p, d):
    assert not p.exists(), 'Preserve frozen evidence: ' + str(p)
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

parser = argparse.ArgumentParser()
parser.add_argument('--video', required=True)
parser.add_argument('--subtitles', required=True)
parser.add_argument('--image-list', required=True)
parser.add_argument('--evidence', action='append', required=True)
parser.add_argument('--release-dir', default='outputs/private-release-v1')
parser.add_argument('--destination', default='claude_media_v1_input')
parser.add_argument('--timing', default='narration/production-injoon-v2/final_timing.json')
parser.add_argument('--source-dir', default='outputs/private-production-v1')
parser.add_argument('--edl-review', default='edl_review.json')
args = parser.parse_args()
dest = (HERE / args.destination).resolve()
assert dest.is_relative_to(HERE)
dest.mkdir(exist_ok=True)
assert not (dest / 'media_report.json').exists()
release = (EP / args.release_dir).resolve()
assert release.is_relative_to(EP)
lock = read(HERE / 'locked_script.json')
assert sha(local(lock['script_path'])) == lock['script_sha256']
timing_path = (EP / args.timing).resolve()
source = (EP / args.source_dir).resolve()
assert timing_path.is_relative_to(EP) and source.is_relative_to(EP)
timing = read(timing_path)
edl = read(source / 'assembly_edl.json')
edl_qa = read(HERE / args.edl_review)
video, subtitles = local(args.video), local(args.subtitles)
assert sha(subtitles) == edl_qa['subtitles_sha256']
assert sha(source / 'assembly_edl.json') == edl_qa['edl_sha256']
assert timing['script_sha256'] == edl['script_sha256'] == lock['script_sha256']
assert sha(timing_path) == edl_qa['timing_sha256']
metadata_path = release / 'metadata_measured.json'
metadata = read(metadata_path)
assert metadata['visibility'] == 'private' and not metadata['scheduled'] and not metadata['published']
description = (release / metadata['description']).resolve()
assert description.is_relative_to(release) and description.is_file()
assert len(description.read_bytes()) <= 5000
thumbnail = release / 'thumbnail.png'
images = []
for value in read(local(args.image_list)):
    p = local(value)
    assert p.suffix.lower() == '.png'
    images.append({'path': rel(p), 'sha256': sha(p),
                   'scope': 'Actual encoded sampled frame/contact sheet or release thumbnail; filenames and QA manifest identify time and scene.'})
assert images and len({r['path'] for r in images}) == len(images)
if not any(r['path'] == rel(thumbnail) for r in images):
    images.append({'path': rel(thumbnail), 'sha256': sha(thumbnail), 'scope': 'Actual release thumbnail.'})
evidence = {}
for value in args.evidence:
    p = local(value)
    evidence[rel(p)] = {'sha256': sha(p), 'review': read(p)}
report = {}
for field, p in [('video', video), ('subtitles', subtitles), ('metadata', metadata_path),
                 ('description', description), ('thumbnail', thumbnail)]:
    report[field] = rel(p)
    report[field + '_sha256'] = sha(p)
report.update(script_sha256=lock['script_sha256'], image_manifest=images,
    technical={'duration_s': edl['total_seconds'], 'width':1920, 'height':1080, 'fps':30,
               'verification_authority': 'Supplied exact-file render/decode and QA receipts, not a guessed playback claim.'},
    captions={'cues':sum(len(ch['cues']) for ch in timing['chapters']),
              'chapters':[{'chapter':ch['chapter'], 'title':ch['title'],
                  'cues':[{k:c[k] for k in ['id','scene_id','text','display_lines','start_s','end_s']} for c in ch['cues']]} for ch in timing['chapters']],
              'times':'Actual chapter-local native WordBoundary; EDL verification independently checks all global SRT offsets.',
              'EDL_review':edl_qa},
    evidence=evidence,
    asset_provenance=read(EP / 'visual/assets.json'),
    private_release_metadata={'title':metadata['title'], 'description':description.read_text(encoding='utf-8'),
                              'chapters':metadata['chapters'], 'visibility':'private', 'scheduled':False},
    coverage_limits={'actual_listening':False, 'continuous_playback':False, 'Studio_ContentID_review':False,
        'scope':'Actual encoded sampled frames plus complete source, subtitle, timing, local ASR and signal/decode evidence; no unperformed observations claimed.'},
    independent_Codex_final_review='Separate exact-version final receipt required by release gate; this packet itself grants no approval.')
save(dest / 'media_report.json', report)
save(dest / 'image_args.json', [r['path'] for r in images])
print(json.dumps({'status':'exact_media_evidence_frozen', 'video_sha256':report['video_sha256'],
                  'images':len(images), 'media_report':rel(dest / 'media_report.json')}))
