import json
import sys
from pathlib import Path
from hashlib import sha256

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
ep = root / 'video-agent-studio/episodes/namyangju-wangsuk-20261014'
qa = json.loads((ep / 'qa/shorts-safe-v2/final_review.json').read_text(encoding='utf-8'))
assert qa['local_review_ready'] and qa['required_open_count'] == 0
for item in qa['files']:
    assert sha256(Path(item['file']).read_bytes()).hexdigest() == item['sha256']
state_path = ep / 'state.json'
state = json.loads(state_path.read_text(encoding='utf-8'))
state['vertical_video_revision'] = {
    'revision': 'shorts-safe-v2', 'profile': 'config/vertical_video_safe_area.json',
    'status': 'local_review_ready', 'published_posts_changed': False,
    'qa': 'qa/shorts-safe-v2/final_review.json',
    'files': [{k: x[k] for k in ('file', 'sha256', 'frames', 'duration')} for x in qa['files']],
    'actual_device_playback': False, 'simulated_ui_cases': 54,
}
experiment_path = ep / 'outputs/thumbnail-ab-v1/experiment.json'
experiment = json.loads(experiment_path.read_text(encoding='utf-8'))
experiment.update(status='B_selected_user_reported', test_started=False,
                  manual_selection_source='b안으로 그냥 마무리했어 맘에들어서',
                  live_application_verified=False)
experiment_path.write_text(json.dumps(experiment, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
state['thumbnail_experiment'].update(status='B_selected_user_reported', test_started=False,
                                     live_application_verified=False)
state['thumbnail_experiment'].pop('requires', None)
state['thumbnail_experiment'].pop('current_thumbnail_unchanged', None)
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
from notify.telegram import send
sent = send('쇼츠 화면 잘림 수정 완료: 1080×1920 유지, 제목·가격·자막·출처를 공통 안전영역 안으로 재배치했습니다. 기존 3편 수정본은 outputs/shorts-safe-v2에 저장했습니다. 9개 화면비×2맞춤×3편=54 UI 모형 겹침 0건, 원음성·자막 타이밍 보존 확인. 실제 모든 기기 재생 검증은 아니며 기존 게시물은 변경하지 않았습니다. 앞으로 제작 기본가이드와 공통 설정에 적용합니다.\n가격편: '+str(ep / 'outputs/shorts-safe-v2/02_price_safe_v2.mp4'))
(root / 'output/vertical-safe-area/delivery_receipt.json').write_text(json.dumps({'verified_files': 3, 'telegram_notice_sent': sent, 'published_posts_changed': False}, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'verified_files': 3, 'telegram_notice_sent': sent}))
