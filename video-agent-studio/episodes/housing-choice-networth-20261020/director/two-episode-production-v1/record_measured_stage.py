"""Record only verified narration/tooling milestones; keep media review pending."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

EP = Path(__file__).resolve().parents[2]
ROOT = EP.parents[2]
HERE = Path(__file__).parent
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
def save(p, data):
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

lock = read(HERE / 'locked_script.json')
result = read(EP / 'narration/free-tts-v1/production_result_v5.json')
timing = read(EP / 'narration/free-tts-v1/final_timing.json')
assert result['script_sha256'] == timing['script_sha256'] == 'babeb15213477f3f6dcb8e8ab958e1a4ccc691c53c1fca6ca9ceae99cc5f269b'
assert result['clipped_samples'] == 0 and result['chapters'] == 10
for chapter in timing['chapters']:
    assert (ROOT / chapter['audio_file']).is_file()
state = read(EP / 'state.json')
state.update(stage='measured_audio_source_integration', updated_at=datetime.now(timezone.utc).isoformat())
state['free_tts_production'].update(status='generated_technical_pass_final_media_qa_pending',
    audio_revision=result['audio_revision'], actual_seconds=result['total_seconds'],
    final_timing='narration/free-tts-v1/final_timing.json', actual_listening=False)
save(EP / 'state.json', state)
queue = read(ROOT / 'config/video_production_queue_20261026.json')
queue['items'][0].update(status='measured_audio_source_integration',
    current_script='video-agent-studio/episodes/housing-choice-networth-20261020/outputs/script-final-v5/script_v5.md')
save(ROOT / 'config/video_production_queue_20261026.json', queue)
preflight = read(HERE / 'episode_preflight.json')
preflight['baseline'].update(script_revision='script-final-v5', audio_revision=result['audio_revision'])
for asset in read(HERE / 'media_assets.json')['assets']:
    key={'channel_brand_intro_clean_v7':'brand_intro','channel_brand_outro_clean_v7':'brand_outro','existing_channel_bgm':'bgm'}.get(asset['asset_id'])
    if key:
        preflight['baseline'][key]=asset['path']
preflight['approvals']['script'].update(status='dual_content_approved', artifact_hashes={'script_sha256':result['script_sha256']})
save(HERE / 'episode_preflight.json', preflight)
save(HERE / 'render_authorization.json', {
    'authorization':'direct_user_20261026_two_episode_private_production',
    'script_sha256':result['script_sha256'],
    'audio_revision':result['audio_revision'],
    'full_render_authorized':True,
    'preconditions':['measured timing integration', 'independent representative QA required issues closed', 'canonical audio carve and source diagnostics pass'],
    'private_upload':'conditional on exact final MP4 dual review',
    'paid_generation':False,
    'claims':{'audio_listened':False, 'continuous_video_review':False, 'final_media_approved':False}
})
decisions = read(EP / 'decisions.json')
decision_id='private-production-preview-improvements-v1'
if not any(d['id']==decision_id for d in decisions['decisions']):
    decisions['decisions'].append({
        'id':decision_id, 'gate':'internal_edit', 'status':'implementation_required',
        'script_sha256':result['script_sha256'],
        'issue_ids':['PVQA-001','PVQA-002','PVQA-003'],
        'choice':'Show actual quarterly matched-complex count ranges; focus the 120-month principal endpoint and the currently spoken growth panel.',
        'basis':'Independent inspection of source preview frames; current user guide requires sample scope and visual focus.',
        'owner':'video_editor', 'independent_recheck':'video_qa',
        'affected_scenes':['ch02/s2g','ch05/s5b','ch08/s8h'],
        'narration_change':False,
        'at_utc':datetime.now(timezone.utc).isoformat()})
    save(EP / 'decisions.json', decisions)
print(json.dumps({'stage':state['stage'], 'tts_seconds':result['total_seconds'], 'render':'authorized_after_source_QA', 'upload':'final_dual_QA_pending'}))
