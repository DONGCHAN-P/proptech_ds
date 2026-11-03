import json
from pathlib import Path
from datetime import datetime, timezone

episode = Path(__file__).resolve().parent
root = episode.parents[2]
now = datetime.now(timezone.utc).isoformat()
updates = {'33fb71e0961f': 'revision_requested', 'e0f76cd4e81e': 'approved'}
receipt = {
    'source': 'direct_user_async_question_reply',
    'question_call_id': 'call_127e9c4505ef4da3b00b0c8717a16b94',
    'recorded_at': now,
    'responses': updates,
    'script_feedback': 'Opening wording revision requested; specific wording awaits user feedback.',
    'budget_scope': 'Existing exact v5 script/input hashes only; maximum 281 submitted characters and 281 credits, additional cash USD0.',
    'execution_authorized': False,
    'reason': 'Matching script approval absent. Revised artifacts require new decisions; this approval does not transfer.',
}
def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
for decision_id, status in updates.items():
    path = root / 'output/video_decisions/decisions' / (decision_id + '.json')
    data = json.loads(path.read_text(encoding='utf-8-sig'))
    assert data['episode'] == episode.name
    assert data['source_script_sha256'] == '97d44556982b25cd12eef8779dab965f60de08485b3678c91de9c0e5060b6ab7'
    assert data['status'] in ('pending', status)
    data.update(status=status, direct_response_at=now, response_source=receipt['source'])
    data['execution_authorized'] = False
    data['response_scope_note'] = receipt['reason']
    save(path, data)
path = episode / 'decisions.json'
data = json.loads(path.read_text(encoding='utf-8-sig'))
for item in data['decisions']:
    if item.get('id') in updates:
        item.update(json.loads((root / 'output/video_decisions/decisions' / (item['id'] + '.json')).read_text(encoding='utf-8')))
save(path, data)
path = episode / 'state.json'
state = json.loads(path.read_text(encoding='utf-8-sig'))
state.update(stage='v8_visual_ready_hook_wording_revision_requested', pending_gate='script_revision',
             new_paid_generation_authorized=False, full_render_waiting_for='revised_opening_script_approval_and_matching_budget_then_audio_timing')
state['pending_decision_ids'] = {}
state['opening_v5_review_reply'] = receipt
save(path, state)
save(episode / 'outputs/story-review-v5/user_review_reply.json', receipt)
print(json.dumps({'statuses': updates, 'voice_generation_authorized': False}))
