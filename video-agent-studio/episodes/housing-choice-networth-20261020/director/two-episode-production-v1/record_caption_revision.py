import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
EP = ROOT / 'video-agent-studio/episodes/housing-choice-networth-20261020'
BASE = Path(__file__).resolve().parent

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))

def write(p, obj):
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

issue = {
    'id': 'CAPTION-MEANING-001', 'status': 'required_open',
    'evidence': ['C09_P048Q007', 'C10_P052Q006', 'encoded contact_05.jpg'],
    'finding': 'Greedy caption length splitting leaves isolated predicates on screen.',
    'decision': 'Rebalance display cues at existing native word boundaries; preserve script, audio and all chapter durations.',
    'input': 'narration/free-tts-v1/final_timing.v6.json',
    'output': 'narration/free-tts-v1/caption-v7/final_timing.json',
    'owner': 'video_narration; integration video_editor; independent video_qa',
    'paid_calls': 0,
    'preservation': 'Existing v6 audio, timing and final MP4 retained. Caption revision renders under private-production-v3.',
    'at_utc': datetime.now(timezone.utc).isoformat(),
}
write(BASE/'caption_revision_v7.json', issue)
decisions = read(EP/'decisions.json')
if not any(x['id']==issue['id'] for x in decisions['decisions']):
    decisions['decisions'].append(issue)
    write(EP/'decisions.json', decisions)
state = read(EP/'state.json')
state['stage'] = 'caption_meaning_revision_v7'
state['updated_at'] = issue['at_utc']
state['free_tts_production']['status'] = 'audio_fixed_caption_only_revision_in_progress'
write(EP/'state.json', state)
queue = read(ROOT/'config/video_production_queue_20261026.json')
queue['items'][0]['status'] = state['stage']
write(ROOT/'config/video_production_queue_20261026.json', queue)
print(json.dumps({'status':state['stage'],'paid_calls':0}))
