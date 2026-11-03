"""출력 계획을 원본과 별도로 대조한다. 실제 음성/프레임 검수는 하지 않는다."""
from pathlib import Path
import hashlib
import json
import re

OUT = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pointer(data, path):
    for key in path.strip('/').split('/'):
        key = key.replace('~1', '/').replace('~0', '~')
        data = data[int(key)] if isinstance(data, list) else data[key]
    return data


plan = read(OUT / 'shorts_plan.json')
manifest = read(OUT / 'source_manifest.json')
sources = {s['source_id']: s for s in manifest['inputs']}
data = {k: read(Path(v['path'])) for k, v in sources.items() if v['path'].endswith('.json')}
checks = []


def check(name, condition, detail):
    checks.append({'check': name, 'result': 'pass' if condition else 'fail', 'detail': detail})


hashes = [{'source_id': k, 'expected_sha256': v['sha256'], 'actual_sha256': digest(Path(v['path'])),
           'required': v['stability_required']} for k, v in sources.items()]
check('frozen_source_hashes', all(x['expected_sha256'] == x['actual_sha256'] for x in hashes if x['required']),
      '동결 입력 바이트 SHA256 재대조. 병렬 총괄이 갱신할 수 있는 CTX 상태/브리프는 스냅샷으로 기록한다.')
frozen_inputs = data['SRC-APPROVED-BODY']['input_revisions']
check('approved_frozen_price_and_rank_versions', all(
    next(x for x in frozen_inputs if x['key'] == key)['sha256'] == sources[source_id]['sha256']
    for key, source_id in [('prices', 'SRC-PRICE-INSIGHTS'), ('legend', 'SRC-PRICE-LEGEND'),
                           ('ranking', 'SRC-RANKING'), ('cohort_code', 'SRC-COHORT-CODE')]),
    '승인 본문에 동결된 집계/범례/순위/준공군 코드의 기대 SHA와 현재 입력이 일치하는지 확인한다.')

original = {}
for sc in data['SRC-BODY-LOCK']['body_scenes']:
    original.update({s['sentence_id']: s for s in sc['sentences']})
original.update({s['sentence_id']: s for s in data['SRC-INTRO-LOCK']['intro_sentences']})
original.update({s['sentence_id']: s for s in data['SRC-CRITERIA']['sentences']})
check('main_sentence_inventory_90', len(original) == 90, '본문/마무리80 + 도입8 + 조건2')
cta = read(OUT / 'common_cta.json')
expected_cta = '나머지 순위도 궁금하시다면 다른 순위 영상을 확인해 주세요. 지역별 자세한 가격과 생활권 비교는 본편에서 이어집니다.'
check('CTA_exact_two_sentences', cta['exacttext'] == expected_cta and
      ' '.join(x['exacttext'] for x in cta['sentences']) == expected_cta and len(cta['sentences']) == 2,
      '최신 task의 CTA 문자·띄어쓰기·문장부호 및 두 문장 구조')
check('CTA_budget_characters', len(expected_cta) == cta['characters_including_spaces_and_punctuation'] and
      len(re.sub(r'\s', '', expected_cta)) == cta['characters_excluding_whitespace'], '제공자 크레딧 추정이 아닌 로컬 문자수')
cta_ids = {s['sentence_id'] for s in cta['sentences']}
uses = []
price_rows = []
rank_rows = []
for i, (short, filename) in enumerate(zip(plan['shorts'], ['short01_promo.json', 'short02_ranks20_16.json', 'short03_ranks15_11.json'])):
    sid = short['short_id']
    standalone = read(OUT / filename)
    check(sid + '_standalone_matches', all(standalone[k] == v for k, v in short.items()), filename)
    reused = [s for s in short['sequence'] if s['sentence_id'] in original]
    uses.extend(s['sentence_id'] for s in reused)
    check(sid + '_verbatim_main', all(s['exacttext'] == original[s['sentence_id']]['text'] and
          s['reading_text'] == original[s['sentence_id']].get('reading_text', original[s['sentence_id']]['text']) for s in reused),
          '원문과 기존 낭독문을 문장 전체로 대조. 절·문장 조각 추출 없음.')
    check(sid + '_only_two_new_CTA', {s['sentence_id'] for s in short['sequence'] if s['sentence_id'] not in original} == cta_ids and
          [s['exacttext'] for s in short['sequence'][-2:]] == [s['exacttext'] for s in cta['sentences']],
          '공통 CTA 두 문장 외 신규 내레이션 없음')
    check(sid + '_no_part2_promotion', all(not s['sentence_id'].startswith('P02-') and
          s['sentence_id'] not in {'P01-OUTRO-V2-02', 'P01-OUTRO-V2-03'} for s in short['sequence']),
          '10~1위 발화와 그 후속편 예고/구독 CTA를 선택하지 않음')
    check(sid + '_complete_rank_and_price_sentences', all(
        r['rank_sentence_id'] in {s['sentence_id'] for s in reused} and
        r['price_sentence_id'] in {s['sentence_id'] for s in reused} for r in short['regions']),
        '각 등장 지역의 순위·쌍 수 및 가격 비교 문장 모두 포함')
    for r in short['regions']:
        source_rank = data['SRC-RANKING']['regions'][r['rank'] - 1]
        rank_rows.append({'short_id': sid, 'region_id': r['region_id'], 'result': 'pass' if (
            source_rank['rank'] == r['rank'] and source_rank['region_id'] == r['region_id'] and
            source_rank['newlywed_couples'] == r['couples']) else 'fail'})
    for f in short['screenfacts']:
        check(sid + '_' + f['fact_id'] + '_source_ids', all(k in sources for k in f['source_ids']), '화면 근거 ID 존재')
        if not f.get('rows'):
            continue
        for row in f['rows']:
            src = pointer(data[row['source_id']], row['json_pointer'])
            keys = ['median_manwon', 'transaction_n', 'complex_n', 'denominator']
            equal = all(row[k] == src[k] for k in keys if k in row)
            price_rows.append({'short_id': sid, 'region_id': f['regionid'], 'source_pointer': row['json_pointer'],
                               'result': 'pass' if equal else 'fail'})
        check(sid + '_' + f['fact_id'] + '_conditions', f['period'] == ['2026-05-01', '2026-10-31'] and
              f['area_m2_inclusive'] == [83, 85] and f['retrieved_date'] == '2026-11-03', '기간·면적·조회일')
    if i:
        expected_ranks = list(range(20, 15, -1)) if i == 1 else list(range(15, 10, -1))
        check(sid + '_all_five_regions', [r['rank'] for r in short['regions']] == expected_ranks and
              len(reused) == 10 and all(r['ledger_label'] for r in short['regions']), '다섯 지역 전체, 지역마다 두 완결 문장')
    check(sid + '_estimate_only', short['targetduration']['status'] == 'estimate_not_Jun_measured' and
          short['targetduration']['playback_rate'] == 1.0 and short['targetduration']['Jun_measured_seconds'] is None,
          '새 Jun 시간 미확정·강제 배속 없음')
    check(sid + '_early_conditions_and_end_hold', short['opening_conditions']['on_first_frame'] and
          short['opening_conditions']['before_first_price'] and short['ending']['silent_hold_after_last_word_seconds'] == 3,
          '조건의 초기 표시와 마지막 발화 후3초를 계획. 실제 프레임/청취 검증 아님')
check('regional_rank_values', all(x['result'] == 'pass' for x in rank_rows), '홍보1 + 내용10 지역 표시 사용 대조')
check('price_values_and_samples', all(x['result'] == 'pass' for x in price_rows), '홍보2 + 내용20 =22개 값/표본 행 사용 대조')
check('reuse_counts', len(uses) == 25 and len(set(uses)) == 23 and plan['counts']['total_sequence_sentence_uses'] == 31,
      '재사용25회/고유23 + 신규 공통CTA6회/고유2 =총31회')
check('portrait_profile_exact', plan['layout_contract']['profile_contract'] ==
      data['SRC-VERTICAL']['profiles']['youtube_portrait_full_frame_v2'] and
      plan['layout_contract']['canvas']['width'] == 1080 and plan['layout_contract']['canvas']['height'] == 1920,
      '정확한 프로필을 계승, 보수 프로필 좌표 혼합 없음')
check('CTA_caption_cues_verbatim', ' '.join(plan['layout_contract']['CTA_caption_cues_text_only']) == expected_cta,
      '자막 의미 단위 분할도 CTA 원문 보존')
md = (OUT / 'shorts_plan.md').read_text(encoding='utf-8')
check('readable_MD_contains_all_spoken_text', all(s['exacttext'] in md for sh in plan['shorts'] for s in sh['sequence']),
      '읽기용 문서에 선택한 모든 완결 발화 포함')
failures = [x for x in checks if x['result'] == 'fail']
report = {
    'task_id': plan['task_id'], 'status': 'pass' if not failures else 'fail',
    'validation_kind': 'writer_local_content_consistency_not_independent_media_QA',
    'plan_sha256': digest(OUT / 'shorts_plan.json'), 'counts': plan['counts'],
    'checks': checks, 'failure_count': len(failures), 'source_hashes': hashes,
    'price_checks': price_rows, 'rank_checks': rank_rows,
    'not_performed': ['새 사실 조사', '원거래 재집계', '외부 API', '유료 생성', 'Claude', '업로드', '프레임 확인', '실제 청취', '연속 재생', '독립 QA'],
}
(OUT / 'checks.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
if failures:
    print(json.dumps(failures, ensure_ascii=False))
    raise SystemExit(1)
handoff = {
    'task_id': plan['task_id'], 'role': 'writer', 'status': 'content_plan_ready',
    'summary': '홍보1·20→16위1·15→11위1. 본편 재사용25회/고유23문장. 신규 공통CTA2문장(65자)을3편에서6회 사용. 본편90+CTA2=예산 고유92문장. 18개 가격·남동61/16(총77단지) 보존. 시간estimate.',
    'input_revisions': {'manifest': 'source_manifest.json', 'sha256': digest(OUT / 'source_manifest.json'),
                        'main': 'map-clean-v1 body80 + intro-v3 8 + criteria2'},
    'outputs': ['shorts_plan.json', 'shorts_plan.md', 'short01_promo.json', 'short02_ranks20_16.json',
                'short03_ranks15_11.json', 'common_cta.json', 'source_manifest.json', 'checks.json', 'issue_DEFINITIONS_AND_LINKS.json'],
    'affected_scene_ids': ['P01-INTRO'] + [f'P01-R{n:02}' for n in range(20, 10, -1)]
                          + ['SHORT01-PROMO', 'SHORT02-R20-R16', 'SHORT03-R15-R11',
                             'P01-SHORTS-CTA-01', 'P01-SHORTS-CTA-02'],
    'checks': [{'check': '원문·동결수치·SHA·프로필', 'result': 'pass', 'evidence': 'checks.json'}],
    'open_issue_ids': ['DEF-R20-BOUNDARY', 'DEF-AGGREGATION-UNIT', 'DEF-CUTOFF-AND-DEDUP', 'LINKS-PENDING'],
    'limits': 'Jun 미생성·미청취·프레임 미확인. 독립 미디어 QA 별도. 다른 담당·공통 파일 수정 없음.',
    'next_role': '총괄 → narration → editor → 독립 QA',
}
(OUT / 'handoff.json').write_text(json.dumps(handoff, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': report['status'], 'checks': len(checks), 'failures': len(failures),
                  'price_row_uses': len(price_rows), 'rank_row_uses': len(rank_rows),
                  'counts': plan['counts'], 'handoff_characters': len(json.dumps(handoff, ensure_ascii=False))}, ensure_ascii=False))
