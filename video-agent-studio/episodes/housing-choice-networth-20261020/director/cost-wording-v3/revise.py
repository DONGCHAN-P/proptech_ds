"""Clarify grouped cost assumptions; retain all amounts and earlier script versions."""
import hashlib
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
EP = Path(__file__).resolve().parents[2]
SOURCE = EP/'outputs/growth-explanation-v1/script_growth_v2.md'
OUT = EP/'outputs/cost-wording-v3'
OUT.mkdir(parents=True, exist_ok=True)
before_bytes = SOURCE.read_bytes()
before = SOURCE.read_text(encoding='utf-8')
changes = [
    ('버전: script-growth-v2', '버전: script-cost-wording-v3'),
    ('거래 시작 비용과 월 유지비는 뒤에서 보여드릴 가정 금액을 적용하겠습니다.',
     '취득세나 중개보수처럼 계약할 때 한 번 드는 초기 부대비용과 매달 드는 유지비는 뒤에서 설명할 가정 금액을 적용하겠습니다.'),
    ('거래를 시작하는 비용은 설명을 위해 600만원으로 가정합니다.',
     '집을 살 때는 집값 외에 취득세와 부동산 중개보수, 등기 관련 비용도 듭니다. 이번 비교에서는 이런 항목을 초기 부대비용으로 묶어 약 600만원으로 가정하겠습니다.'),
    ('초기 계약비용을 100만원으로 두면 투자계좌에는 4천900만원이 남습니다.',
     '전세도 중개보수 등 계약 과정에 드는 초기 부대비용이 있습니다. 이 비용을 약 100만원으로 잡으면 투자계좌에는 4천900만원이 남습니다.'),
    ('계약비용 100만원을 내고 나면 투자계좌의 출발 금액은 1억6천900만원입니다.',
     '월세도 중개보수 등 초기 부대비용을 약 100만원으로 가정하겠습니다. 이 비용을 내고 나면 투자계좌의 출발 금액은 1억6천900만원입니다.'),
    ('소유자 부담 유지·보유 비용을 월 30만원으로 가정하면',
     '보유세와 수선비 등 집을 보유하면서 드는 비용을 월평균 30만원으로 묶어 가정하면'),
]
after = before
for old, new in changes:
    assert after.count(old) == 1, old
    after = after.replace(old, new, 1)
target = OUT/'script_cost_v3.md'
assert not target.exists(), 'Preserve an existing revision; choose a new version.'
target.write_text(after, encoding='utf-8')
# Apart from the declared wording replacements, the text is identical.
restored = after
for old, new in reversed(changes):
    restored = restored.replace(new, old, 1)
assert restored == before
assert SOURCE.read_bytes() == before_bytes
checks = dict(version='script-cost-wording-v3', review_type='author_wording_check',
              change_count=len(changes), all_amounts_and_model_results='unchanged',
              source=SOURCE.relative_to(ROOT).as_posix(),
              source_sha256=hashlib.sha256(before_bytes).hexdigest(),
              target=target.relative_to(ROOT).as_posix(),
              target_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
              scope='Cost category explanations only; 600/100/100만원 remain illustrative grouped assumptions.',
              itemized_statutory_cost_estimation=False, video_edited=False, audio_generated=False)
(OUT/'checks.json').write_text(json.dumps(checks, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
(OUT/'수정내역.md').write_text(
    '# 비용 설명 보강 v3\n\n'
    '초기 부대비용의 항목과 설명용 가정이라는 성격을 낭독문에 추가했다.\n\n'
    '- 매매: 취득세·중개보수·등기 관련 비용을 묶어 약 600만원으로 가정.\n'
    '- 전세·월세: 중개보수 등 계약 과정의 초기 부대비용을 각각 약 100만원으로 가정.\n'
    '- 소유자 월 30만원: 보유세·수선비 등의 월평균 비용 묶음으로 설명.\n\n'
    '항목별 실제 세액·보수 합계를 새로 산출한 작업은 아니다. 계산용 금액과 투자금·순자산 결과는 유지했다. '
    '기존 버전과 MP4·음성은 보존했다.\n', encoding='utf-8')
state_path = EP/'state.json'
state = json.loads(state_path.read_text(encoding='utf-8'))
state.update(script_path=target.relative_to(ROOT).as_posix(),
             previous_script_path=SOURCE.relative_to(ROOT).as_posix(),
             script_status='cost_wording_draft_ready_not_approved',
             script_qa_path=(OUT/'checks.json').relative_to(ROOT).as_posix(),
             updated_at=datetime.now(timezone(timedelta(hours=9))).isoformat())
state['cost_wording'] = dict(version='v3', changes=(OUT/'수정내역.md').relative_to(ROOT).as_posix(),
                              integrated_into_video=False, amounts_changed=False)
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
shelf_path = ROOT/'config/video_shelf.json'
shelf = json.loads(shelf_path.read_text(encoding='utf-8'))
for entry in shelf['entries']:
    if entry.get('workspace', '').replace('\\', '/') == EP.relative_to(ROOT).as_posix():
        entry['files']['대본_보강안.md'] = target.relative_to(ROOT).as_posix()
        entry['files']['비용설명_수정내역.md'] = (OUT/'수정내역.md').relative_to(ROOT).as_posix()
        entry['status'] = '비용 항목 설명 보강 대본 v3 / 계산 금액 유지 / 영상 미반영 / 음성 생성 보류'
shelf_path.write_text(json.dumps(shelf, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps(checks, ensure_ascii=False))
