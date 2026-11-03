"""Authorize one exact local render after independent source and voice gates."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
EP = HERE.parents[1]
ROOT = EP.parents[2]
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def local(raw):
    p = (ROOT / raw).resolve()
    assert p.is_relative_to(EP) and p.is_file(), raw
    return p
parser = argparse.ArgumentParser()
parser.add_argument('--source-review', required=True)
parser.add_argument('--audio-review', required=True)
args = parser.parse_args()
dest = HERE / 'render_authorization_v1.json'
assert not dest.exists(), 'Preserve existing exact render authority.'
source_path, audio_path = local(args.source_review), local(args.audio_review)
source, audio = read(source_path), read(audio_path)
assert source['source_approved'] and source['approved'] and source['required'] == source['critical'] == []
assert audio.get('approved') is True or audio.get('audio_approved') is True
for key in ['required_issues','critical_issues','required','critical','open_required','required_open_issues']:
    assert not audio.get(key), key
template = read(EP / 'editor/main_render_authorization_template.json')
spec = read(EP / 'editor/render_commands.json')
assert sha(EP / 'editor/render_pipeline.py') == template['pipeline_sha256']
assert sha(EP / 'editor/render_commands.json') == template['render_commands_sha256']
assert sha(EP / 'editor/render_input_manifest.json') == template['input_manifest_sha256']
assert source['checked_revision']['script_sha256'] == audio['script_sha256'] == template['script_sha256']
audio_timing = audio.get('final_timing_sha256') or audio.get('final_timing', {}).get('sha256')
assert source['checked_revision']['timing_sha256'] == audio_timing == template['timing_sha256']
for project, digest in source['checked_revision']['source_chapters'].items():
    assert sha(EP / 'outputs/private-production-v1' / project / 'index.html') == digest
edl_path = HERE / 'edl_review_v3.json'
edl = read(edl_path)
assert edl['edl_sha256'] == template['edl_sha256'] and edl['timing_sha256'] == audio_timing
assert edl['subtitles_sha256'] == template['captions_sha256']
assert round(edl['planned_total_seconds'] * 30) == spec['total_video_frames'] == 35581
auth = dict(template)
auth.update(approved=True, status='exact_local_render_authorized_after_independent_gates',
    evidence={key:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for key,p in [
        ('source_qa',source_path),('audio_qa',audio_path),('edl_review',edl_path)]},
    authorization_basis='Current direct user instruction: two sequential reviewed free-voice films and private uploads.',
    user_authorization=(HERE / 'authorization.json').relative_to(ROOT).as_posix(),
    paid_generation_authorized=False, new_TTS_calls=0, upload_authorized_by_this_file=False,
    actual_listening=False, continuous_playback=False, at_utc=datetime.now(timezone.utc).isoformat())
auth.pop('note', None)
dest.write_text(json.dumps(auth, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status':auth['status'],'authorization':dest.relative_to(ROOT).as_posix(),'frames':35581}))
