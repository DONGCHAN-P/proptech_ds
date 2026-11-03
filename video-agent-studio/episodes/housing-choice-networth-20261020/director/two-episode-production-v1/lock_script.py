"""Lock only the exact script independently passed by Codex and Claude."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[5]
EP=Path(__file__).resolve().parents[2]
HERE=Path(__file__).parent
parser=argparse.ArgumentParser()
parser.add_argument('--version',type=int,choices=[5,6],default=5)
args=parser.parse_args()
version=args.version
script=EP/f'outputs/script-final-v{version}/script_v{version}.md'
sha=hashlib.sha256(script.read_bytes()).hexdigest()
codex_path=EP/f'qa/private-production-v1/content_v{version}_review.json'
claude_path=HERE/('claude/script-v5-round2/receipt.json' if version==5 else 'claude/script-v6-terminology-round1/receipt.json')
codex=json.loads(codex_path.read_text(encoding='utf-8'))
claude=json.loads(claude_path.read_text(encoding='utf-8'))
assert codex['approved'] and codex['checked_sha256']==sha and codex['required_issues']==[]
assert claude['approved'] and claude['script_sha256']==sha and not claude['is_error']
review=json.loads(claude_path.with_name('review.json').read_text(encoding='utf-8'))
assert review['approved'] and review['required_issues']==[] and review['artifact_sha256']==sha
result={'script_path':script.relative_to(ROOT).as_posix(),'script_sha256':sha,
    'status':'content_approved_for_free_tts','codex_content_pass':True,'claude_content_pass':True,
    'codex_receipt':codex_path.relative_to(ROOT).as_posix(),'claude_receipt':claude_path.relative_to(ROOT).as_posix(),
    'review_receipt_sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (codex_path,claude_path)},
    'free_tts_authorized':True,'paid_tts_authorized':False,'final_media_approval':'pending'}
current=HERE/'locked_script.json'
if current.exists():
    old=json.loads(current.read_text(encoding='utf-8'))
    if old['script_sha256']!=sha:
        old_version=Path(old['script_path']).stem.replace('script_','')
        archive=HERE/f'locked_script_{old_version}.json'
        if archive.exists():
            assert archive.read_bytes()==current.read_bytes()
        else:
            archive.write_bytes(current.read_bytes())
current.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
state_path=EP/'state.json'
state=json.loads(state_path.read_text(encoding='utf-8'))
state.update(script_path=result['script_path'],script_status='dual_review_content_approved',stage='free_tts_and_source_production')
state['free_tts_production'].update(status='dual_content_review_passed',script_sha256=sha,
                                    locked_script=(HERE/'locked_script.json').relative_to(ROOT).as_posix())
state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
shelf_path=ROOT/'config/video_shelf.json'
shelf=json.loads(shelf_path.read_text(encoding='utf-8'))
for entry in shelf['entries']:
    if entry.get('workspace','').replace('\\','/')==EP.relative_to(ROOT).as_posix():
        entry['files']['대본_보강안.md']=result['script_path']
        entry['status']=f'대본 v{version} 양측 내용 검수 통과 / 무료 TTS·영상 제작 중 / 최종 영상 검수·비공개 업로드 전'
shelf_path.write_text(json.dumps(shelf,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
queue_path=ROOT/'config/video_production_queue_20261026.json'
if queue_path.exists():
    queue=json.loads(queue_path.read_text(encoding='utf-8'))
    for item in queue['items']:
        if item['episode']==EP.name:
            item.update(current_script=result['script_path'],status='approved_script_targeted_audio_update' if version==6 else 'free_tts_and_source_production')
    queue_path.write_text(json.dumps(queue,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
