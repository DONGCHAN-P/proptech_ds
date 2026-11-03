"""Expose draft review documents without approving production gates."""
from pathlib import Path
import json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[4]
EP = Path(__file__).resolve().parents[1]
rel = EP.relative_to(ROOT).as_posix()
required = {
    '대본.md': f'{rel}/outputs/script-review-v1/script_v1.md',
    '자료조사.md': 'reports/거주비를 포함한 주거 선택 비교.md',
    '화면설계.md': f'{rel}/outputs/script-review-v1/visual_storyboard.md',
    '협업기록.md': f'{rel}/writer/consensus_record.md',
    '계산모형.md': f'{rel}/research/illustrative_model_note.md',
}
for source in required.values():
    assert (ROOT / source).is_file(), source
qa = json.loads((EP/'qa/script-review/final_review.json').read_text(encoding='utf-8'))
shelf_path = ROOT/'config/video_shelf.json'
shelf = json.loads(shelf_path.read_text(encoding='utf-8'))
entry = {'name': '매매전월세', 'status': '자료조사·대본 초안 v1 / 사용자 검토 전 / 음성·영상 미제작', 'workspace': rel, 'files': required}
shelf['entries'] = [e for e in shelf['entries'] if e['name'] != entry['name']] + [entry]
shelf_path.write_text(json.dumps(shelf, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
state_path = EP/'state.json'
state = json.loads(state_path.read_text(encoding='utf-8'))
state.update(stage='script_draft_ready', script_status='draft_ready_not_approved',
    claude_collaboration='two_actual_script_reviews_completed_partial_consensus',
    updated_at=datetime.now(timezone.utc).isoformat(),
    script_path=required['대본.md'], research_report_path=required['자료조사.md'],
    visual_storyboard_path=required['화면설계.md'], consensus_path=required['협업기록.md'],
    script_qa_path=f'{rel}/qa/script-review/final_review.json',
    claude_receipts=[f'{rel}/director/claude-story-v1/round1.receipt.json', f'{rel}/director/claude-story-v1/receipt.json'],
    limitations=['Illustrative 10-year model, not historical backtest or forecast', 'No TTS, video rendering, paid generation, or upload started'])
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'stage': state['stage'], 'files': list(required), 'approval': state['script_status']}, ensure_ascii=False))
