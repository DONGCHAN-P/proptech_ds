"""추가된 승인 화면 팩트만 대조하고 writer 인계를 갱신한다."""
from pathlib import Path
import hashlib
import json

B = Path(__file__).resolve().parent
EP = B.parents[2]
VISUAL = EP / 'director/top20-split-v4/part1-jun-and-shorts-v1/shorts_visual_facts.json'


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


plan = load(B / 'shorts_plan.json')
cta = load(B / 'common_cta.json')
facts = load(VISUAL)
protected = ['shorts_plan.json', 'shorts_plan.md', 'short01_promo.json',
             'short02_ranks20_16.json', 'short03_ranks15_11.json', 'common_cta.json',
             'source_manifest.json', 'checks.json', 'issue_DEFINITIONS_AND_LINKS.json']
before = {name: sha(B / name) for name in protected}
checks = []


def check(name, ok, detail):
    checks.append({'check': name, 'result': 'pass' if ok else 'fail', 'detail': detail})


check('accepted_visual_scope', [x['rank'] for x in facts] == list(range(20, 10, -1)),
      '화면 팩트는20~11위10개 지역')
pricefacts = {f['regionid']: f for sh in plan['shorts'][1:]
              for f in sh['screenfacts'] if 'rows' in f}
rows = []
for region in facts:
    rid = region['region_id']
    own = pricefacts[rid]
    check(rid + '_accepted_html_sha', sha(Path(region['source_file'])) == region['source_sha256'],
          '승인 HTML 바이트 SHA 확인; 프레임 검수 아님')
    check(rid + '_two_rows', len(region['rows']) == len(own['rows']) == 2, '두 비교 행 유지')
    for i, (shown, original) in enumerate(zip(region['rows'], own['rows'])):
        if rid == 'R16':
            value = original['complex_n']
            maximum = max(x['complex_n'] for x in own['rows'])
            expected_value = f'{value}단지'
            expected_sample = f"지도 연결 {original['denominator']}단지 기준"
            expected_label = ['5억 미만', '5~7억'][i]
        else:
            value = original['median_manwon']
            maximum = max(x['median_manwon'] for x in own['rows'])
            expected_value = original['display_value']
            expected_sample = f"거래 {original['transaction_n']}건 · {original['complex_n']}단지"
            expected_label = original.get('dong', original.get('label'))
            if rid == 'R20' and i == 0:
                expected_label = '2000년까지 준공'
        ok = (shown['value'] == expected_value and shown['sample'] == expected_sample
              and shown['label'] == expected_label
              and abs(shown['bar_fraction'] - value / maximum) < 2e-9)
        check(rid + f'_row{i + 1}', ok, '값·집단명·거래/단지 표본수·막대 비례')
        rows.append({'region_id': rid, 'row': i + 1, 'label': shown['label'],
                     'value': shown['value'], 'sample': shown['sample'],
                     'result': 'pass' if ok else 'fail'})
    expected_type = 'band_distribution' if rid == 'R16' else 'cohort_pair' if rid == 'R20' else 'dong_pair'
    expected_title = '단지별 가격대 분포' if rid == 'R16' else '준공 시기별 거래 중위값' if rid == 'R20' else '동별 거래 중위값'
    check(rid + '_aggregation_definition', own['price_type'] == expected_type
          and region['title'] == expected_title, expected_title)

r16 = pricefacts['R16']
check('R16_complex_distribution_not_transaction_median',
      r16['price_type'] == 'band_distribution'
      and all('median_manwon' not in x and 'transaction_n' not in x for x in r16['rows'])
      and [x['complex_n'] for x in r16['rows']] == [61, 16]
      and all(x['denominator'] == 77 for x in r16['rows']),
      '단지별 거래 중위가격의 구간별 단지 수:77단지 중61/16. 둘째 구간은5억 이상7억 미만')
covered = {n for sh in plan['shorts'][1:] for n in sh['rankrange']['spoken_ranks']}
check('covered_ranks_exactly20_to11', covered == set(range(11, 21)) and len(pricefacts) == 10,
      '53개 구는 순위 모집단. 본편은TOP20 중20~11위10개 지역을 소개')
check('fullmain_CTA_target_is20_to11',
      all('20~11위' in sh['ending']['full_main_target'] for sh in plan['shorts']),
      '본편 연결 범위를53개 구 전체 또는TOP20 전체로 확대하지 않음')
check('price_fact_regions_are_subset', all(
    {f['regionid'] for f in sh['screenfacts'] if 'rows' in f}
    <= {f'R{x:02}' for x in sh['rankrange']['spoken_ranks']} for sh in plan['shorts']),
    '홍보17위 사례 / 내용20~16위 / 내용15~11위에만 가격값 연결')
exact = '나머지 순위도 궁금하시다면 다른 순위 영상을 확인해 주세요. 지역별 자세한 가격과 생활권 비교는 본편에서 이어집니다.'
check('common_CTA_exact65', cta['exacttext'] == exact and len(exact) == 65
      and ' '.join(x['exacttext'] for x in cta['sentences']) == exact, '지정 CTA 원문65자 보존')
aliases = [{'writer_sentence_id': s['sentence_id'], 'parent_sentence_id': f'SHORTS-CTA-{i + 1:02}',
            'exacttext': s['exacttext'], 'match_basis': 'exacttext'}
           for i, s in enumerate(cta['sentences'])]
check('CTA_alias_mapping', [x['writer_sentence_id'] for x in aliases]
      == ['P01-SHORTS-CTA-01', 'P01-SHORTS-CTA-02'],
      '총괄 생성 ID SHORTS-CTA-01/02에 원문 일치로 매핑')
after = {name: sha(B / name) for name in protected}
check('plan_and_wording_files_unchanged', before == after, '계획·문구·기존 검증 기록 수정 없음')
failed = [x for x in checks if x['result'] == 'fail']
report = {
    'task_id': plan['task_id'], 'status': 'pass' if not failed else 'fail',
    'validation_scope': '신규 승인 화면 팩트·범위/집계 정의·CTA ID 인계',
    'new_source': {'path': str(VISUAL).replace('\\', '/'), 'sha256': sha(VISUAL),
                   'source_id': 'SRC-ACCEPTED-SHORTS-VISUAL-FACTS'},
    'checked_regions': 10, 'checked_rows': 20, 'checks': checks,
    'failures': len(failed), 'price_rows': rows, 'CTA_aliases': aliases,
    'parent_voice_report': {'source': '최신 task packet', 'generated_sentences': 92,
                            'CTA_generated_once': True, 'actual_reported_value': 2208,
                            'value_unit': 'task packet에 단위 미표기',
                            'independently_listened_by_writer': False},
    'preserved_artifact_sha256': after,
    'superseded_execution_note': '직전 PowerShell stdin 전달의 한글 인코딩 손상으로 문자열 대조가 무효가 되어 UTF-8 파일 실행으로 교정함. 가격 변경 근거로 사용하지 않음.',
    'not_performed': ['추가 사실 조사', '본편/계획 문구 변경', '음성 생성', '음성 청취',
                      '프레임 검수', '연속 재생', '독립 미디어 QA'],
}
(B / 'handoff_final_check.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
if failed:
    print(json.dumps({'status': 'fail', 'issues': failed}, ensure_ascii=False))
    raise SystemExit(1)
h = load(B / 'handoff.json')
h['status'] = 'writer_handoff_complete'
h['summary'] = '홍보1·20→16위1·15→11위1. 새 화면 팩트10지역20행과 값·표본수·정의 일치. 53개 구는 모집단, 소개는20~11위10지역. R16은77단지의61/16 구간 분포. 계획·문구 변경 없음.'
h['input_revisions']['accepted_visual_facts'] = {
    'path': str(VISUAL.relative_to(EP)).replace('\\', '/'), 'sha256': sha(VISUAL)}
if 'handoff_final_check.json' not in h['outputs']:
    h['outputs'].append('handoff_final_check.json')
h['checks'] = [
    {'check': '기존 원문·가격·SHA', 'result': 'pass', 'evidence': 'checks.json'},
    {'check': '새 화면팩트·소개범위·R16정의·CTA별칭', 'result': 'pass', 'evidence': 'handoff_final_check.json'},
]
h['limits'] = '총괄 보고:92문장 생성 완료(actual2208), CTA1회 생성. writer 미청취·프레임 미확인. CTA별칭은 exacttext로 SHORTS-CTA-01/02에 연결. 실제 Jun 타이밍·독립 미디어 QA는 후속 담당.'
h['next_role'] = '총괄 → editor → 독립 QA'
(B / 'handoff.json').write_text(json.dumps(h, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
assert load(B / 'handoff.json')['status'] == 'writer_handoff_complete'
assert all((B / name).is_file() for name in h['outputs'])
assert {name: sha(B / name) for name in protected} == before
print(json.dumps({'status': h['status'], 'checks': len(checks), 'failures': 0,
                  'regions': 10, 'price_rows': 20, 'R16': '77단지 중61/16 구간 분포',
                  'rank_scope': '53개 구 모집단 중20~11위10지역',
                  'unchanged_plan_files': len(protected),
                  'handoff_characters': len(json.dumps(h, ensure_ascii=False)),
                  'paths': [str(B / 'handoff.json'), str(B / 'handoff_final_check.json')]}, ensure_ascii=False))
