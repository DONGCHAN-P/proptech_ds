"""Build a versioned script from three replacement blocks; preserve source artifacts."""
import hashlib
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
EP = Path(__file__).resolve().parents[2]
OUT = EP / 'outputs/growth-explanation-v1'
source_path = EP / 'outputs/script-review-v1/script_v1.md'
source = source_path.read_text(encoding='utf-8')
facts = json.loads((OUT/'facts.json').read_text(encoding='utf-8'))
assert hashlib.sha256(source_path.read_bytes()).hexdigest() == facts['input_sha256'][str(source_path.relative_to(ROOT))]
supplement = (OUT/'보강대본.md').read_text(encoding='utf-8')
blocks = re.findall(r'\*\*위치:[^\n]*\*\*\n\n(.*?)\n\n\*\*화면 지시\*\*', supplement, re.S)
assert len(blocks) == 3
old_assumptions = source.split('화면의 숫자는', 1)[1].split('\n\n', 1)[0]
revised = source.replace('화면의 숫자는'+old_assumptions, blocks[0], 1)
revised = revised.replace('## 8. 조건의 변화\n\n', '## 8. 조건의 변화\n\n'+blocks[1]+'\n\n', 1)
revised = revised.replace('이제 집값과 투자수익 두 숫자를 바꿔보겠습니다.', '이어서 집값과 투자수익을 함께 바꿔보겠습니다.', 1)
revised = revised.split('## 10. 다음 선택', 1)[0]+'## 10. 다음 선택\n\n'+blocks[2]+'\n'
revised = revised.replace('버전: script-v1 · 승인 전 검토용 · 작성일 2026-10-20',
                          '버전: script-growth-v2 · 승인 전 검토용 · 수정일 2026-10-26', 1)


def sections(text):
    return {int(number): body for number, body in re.findall(r'^## (\d+)\. [^\n]+\n(.*?)(?=^## |\Z)', text, re.M | re.S)}


before, after = sections(source), sections(revised)
unchanged = [1, 3, 4, 5, 6, 7, 9]
assert sorted(after) == list(range(1, 11))
assert all(before[n] == after[n] for n in unchanged)
assert before[8].replace('이제 집값과 투자수익 두 숫자를 바꿔보겠습니다.',
                         '이어서 집값과 투자수익을 함께 바꿔보겠습니다.').strip() in after[8]
assert all(term not in '\n'.join(blocks) for term in ['AI 개념 이미지', '공식 지수 아님', '인과분석 아님'])
(OUT/'script_growth_v2.md').write_text(revised, encoding='utf-8')
checks = dict(version='script-growth-v2', review_type='author_checks', independent_review='pending',
              unchanged_sections=unchanged, changed_sections=[2, 8, 10],
              original_assumptions_and_results='preserved', calculation_checks=facts['validation'],
              original_script_sha256=hashlib.sha256(source_path.read_bytes()).hexdigest(),
              revised_script_sha256=hashlib.sha256((OUT/'script_growth_v2.md').read_bytes()).hexdigest(),
              video_edited=False, audio_generated=False, playback_performed=False, listening_performed=False)
(OUT/'checks.json').write_text(json.dumps(checks, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

state_path = EP/'state.json'
state = json.loads(state_path.read_text(encoding='utf-8'))
state.update(stage='growth_supplement_script_review_ready', script_status='growth_supplement_draft_ready_not_approved',
             updated_at=datetime.now(timezone(timedelta(hours=9))).isoformat(),
             script_path=str((OUT/'script_growth_v2.md').relative_to(ROOT)),
             previous_script_path=str(source_path.relative_to(ROOT)),
             script_qa_path=str((OUT/'checks.json').relative_to(ROOT)),
             previous_script_qa_path='video-agent-studio/episodes/housing-choice-networth-20261020/qa/script-review/final_review.json')
state['growth_supplement'] = dict(version='growth-explanation-v1',
    user_direction='기존 영상 최대 보존; 주거 방식은 본인 상황에 맞춤; 집값은 보수적 계획 가정; 레버리지와 주거 안정성; 감당 가능한 매매 가격을 다음 편으로 연결',
    script=str((OUT/'보강대본.md').relative_to(ROOT)), facts=str((OUT/'facts.json').relative_to(ROOT)),
    author_checks=str((OUT/'checks.json').relative_to(ROOT)), integrated_into_video=False,
    narration='on_hold_by_user', paid_generation='not_authorized', user_script_approval='pending')
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

shelf_path = ROOT/'config/video_shelf.json'
shelf = json.loads(shelf_path.read_text(encoding='utf-8'))
for entry in shelf['entries']:
    if entry.get('workspace', '').replace('\\', '/') != EP.relative_to(ROOT).as_posix():
        continue
    entry['status'] = '집값 상승률·레버리지·주거 안정성 대본 보강 v2 / 기존 영상 보존 / 새 대본 미렌더 / 음성 생성 보류'
    entry['files']['대본_보강안.md'] = str((OUT/'script_growth_v2.md').relative_to(ROOT))
    entry['files']['집값상승률_보강.md'] = str((OUT/'보강대본.md').relative_to(ROOT))
    entry['files']['집값상승률_계산.md'] = str((OUT/'계산근거.md').relative_to(ROOT))
    # Keep the existing script/media links as references; the revision has its own entry.
shelf_path.write_text(json.dumps(shelf, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps(checks, ensure_ascii=False, indent=2))
