"""Re-edit complete existing Jun utterances; never call a generation service."""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json

D = Path(__file__).resolve().parent
E = D.parents[2]
R = E.parents[2]
OLD = D.parent / 'part1-jun-and-shorts-v1'
W = E / 'writer/top20-split-v4/jun-and-shorts-v1'


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def save(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    assert not (D / 'shorts_media_receipt.json').exists(), 'Preserve frozen timing'
    save(D / 'baseline_state.json', read(E / 'state.json'))
    save(D / 'baseline_release.json', read(OLD / 'release_manifest.json'))
    budget = OLD / 'budget_decision.json'
    author = OLD / 'production_authorization.json'
    save(D / 'request_scope.json', dict(
        user_request='쇼츠 인트로·아웃트로와 최근 Shorts 자료에 근거한 UI 개선',
        assets=['SHORT01-PROMO', 'SHORT02-R20-R16', 'SHORT03-R15-R11'],
        main_video_change=False, voice_mode='reuse_complete_existing_Jun_utterances',
        new_paid_calls=0, additional_credits=0, cash_spent_krw=0,
        old_credit_cap=6500, old_actual_credits=2208,
        preserved_budget=dict(path=str(budget), sha256=sha(budget)),
        preserved_authorization=dict(path=str(author), sha256=sha(author)),
        prior_completed_decision='5fa686c7d1e9', previous_approval_applied=False,
        uploads_authorized=False, part2_authorized=False))
    facts = OLD / 'shorts_visual_facts.json'
    (D / 'shorts_visual_facts.json').write_bytes(facts.read_bytes())
    intro = copy.deepcopy(read(W / 'short01_promo.json')['sequence'][0])
    narration = []
    for filename in ['short01_promo.json', 'short02_ranks20_16.json', 'short03_ranks15_11.json']:
        plan = read(W / filename)
        seq = plan['sequence']
        if plan['short_id'] == 'SHORT01-PROMO':
            seq = [x for x in seq if x['sentence_id'] not in [
                'P01-INTRO-V3-04', 'P01-INTRO-V3-05', 'P01-SHORTS-CTA-01']]
        else:
            seq = [copy.deepcopy(intro)] + [x for x in seq if x['sentence_id'] != 'P01-SHORTS-CTA-02']
        plan.update(revision='shorts-ui-v2-20261104', sequence=seq,
                    opening_conditions='첫 프레임에 신혼부부 거주 수 순위와 해당 범위, 기존 Jun 질문으로 시작',
                    ending='완결된 기존 CTA 한 문장, 다른 편 범위/본편 안내, 마지막 발화 뒤1.05초',
                    voice_reuse_policy='전체 문장 PCM만 재사용; 발화 순서 외 원문/읽기문/발음 불변; 생성0')
        save(D / 'plans' / filename, plan)
        narration += [f"## {plan['short_id']}", '', *[x['exacttext'] + '\n' for x in seq], '']
    (D / 'shorts_script.md').write_text('# 쇼츠 개선 대본 · 기존 Jun 문장 재배치\n\n' + '\n'.join(narration), encoding='utf-8')
    spec = importlib.util.spec_from_file_location('approved_jun_reuse', OLD / 'prepare_shorts.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.D = D
    module.W = D / 'plans'
    module.main()
    receipt = read(D / 'shorts_media_receipt.json')
    receipt['shared_CTA_generated_once'] = 'reused_from_prior_generated_CTA_no_generation_this_revision'
    save(D / 'shorts_media_receipt.json', receipt)
    assert sha(budget) == read(D / 'request_scope.json')['preserved_budget']['sha256']
    print('three_reused_Jun_timelines_ready_no_new_generation')


if __name__ == '__main__':
    main()
