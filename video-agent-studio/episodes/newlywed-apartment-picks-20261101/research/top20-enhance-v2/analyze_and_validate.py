"""53개 구 원표 재집계. --write: 담당 폴더 산출물 생성, 기본: 저장값 재검증."""
import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

OUT = Path(__file__).resolve().parent
EP = OUT.parents[1]
ROOT = EP.parents[2]
BASE = ROOT / 'analysis/newlywed_region_2024'
OLD = EP / 'research/top20-8min-v2'
CHECKED = '2026-11-02'
URL24 = 'https://mods.go.kr/boardDownload.es?bid=11815&list_no=442387&seq=3'
URL23 = 'https://sri.kostat.go.kr/boardDownload.es?bid=11815&list_no=434122&seq=3'
INPUTS = {
    'tsv_2024': BASE / 'source/capital_rows.tsv',
    'rankings': BASE / 'rankings.json',
    'pdf_2024': BASE / 'source/newlyweds_2024.pdf',
    'source_qa': EP / 'qa/ranking_source_review.json',
    'top20': OLD / 'top20.json',
    'comparison': OLD / 'top20_comparison.csv',
    'facts01_10': OLD / 'ranks01_10_facts.json',
    'facts11_20': OLD / 'ranks11_20_facts.json',
    'pdf_2023': OLD / 'source/newlyweds_2023.pdf',
    'old_source_manifest': OLD / 'source/source_manifest.json',
    'master_script_v4': EP / 'director/top20-production-v1/script_v4.md',
    'adopted_scenes': EP / 'director/top20-enhance-v2/added_scenes.json',
}


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path):
    return path.relative_to(ROOT).as_posix()


def key(row):
    return row['province'] + '|' + row['region']


def display_pct(numerator, denominator):
    return float((Decimal(numerator) / Decimal(denominator) * 100).quantize(
        Decimal('0.1'), rounding=ROUND_HALF_UP))


def compute():
    with INPUTS['tsv_2024'].open(encoding='utf-8-sig', newline='') as f:
        original = list(csv.DictReader(f, delimiter='\t'))
    numeric = ['newlywed_couples', 'first_marriage_couples', 'remarried_couples', 'pdf_page']
    for row in original:
        for col in numeric:
            row[col] = int(row[col])
    assert len(original) == 86 and len({key(r) for r in original}) == 86
    qa = read(INPUTS['source_qa'])
    assert qa['verdict']['source_transcription'] == 'pass'
    assert qa['checked_revision']['tsv_sha256'] == digest(INPUTS['tsv_2024'])
    assert qa['checked_revision']['rankings_sha256'] == digest(INPUTS['rankings'])
    assert read(INPUTS['rankings'])['metadata']['pdf_sha256'] == digest(INPUTS['pdf_2024'])
    qa_hashes = {i.get('relative_path'): i['sha256'] for i in qa['input_manifest']}
    assert qa_hashes[rel(INPUTS['pdf_2024'])] == digest(INPUTS['pdf_2024'])
    official = {key(r): r['official_values'] for r in qa['row_comparison_ledger']}
    for row in original:
        assert all(row[col] == official[key(row)][col] for col in numeric)
    pool = [r for r in original if r['region'].endswith('구')]
    assert len(pool) == 53 and Counter(r['province'] for r in pool) == {'서울': 25, '인천': 8, '경기': 20}
    published = {key(r): r for r in read(INPUTS['rankings'])['capital_gu_ranking']}
    top20 = read(INPUTS['top20'])
    assert top20['source_sha256'] == digest(INPUTS['rankings'])
    scene_ids = {key(r): r['scene_id'] for r in top20['regions']}
    ranks = []
    for row in pool:
        total_rank = 1 + sum(r['newlywed_couples'] > row['newlywed_couples'] for r in pool)
        first_rank = 1 + sum(r['first_marriage_couples'] > row['first_marriage_couples'] for r in pool)
        assert published[key(row)]['rank'] == total_rank
        assert all(row[c] == published[key(row)][c] for c in numeric)
        ranks.append({
            'region_key': key(row), 'province': row['province'], 'region': row['region'],
            'total_couples': row['newlywed_couples'], 'first_marriage_couples': row['first_marriage_couples'],
            'remarried_couples': row['remarried_couples'],
            'total_rank': total_rank, 'first_marriage_rank': first_rank,
            'rank_difference_total_minus_first': total_rank - first_rank,
            'in_total_top20': total_rank <= 20, 'in_first_marriage_top20': first_rank <= 20,
            'membership': ('both' if max(total_rank, first_rank) <= 20 else
                           'first_only' if first_rank <= 20 else 'total_only' if total_rank <= 20 else 'neither'),
            'original_scene_id': scene_ids.get(key(row)),
            'source_file': rel(INPUTS['tsv_2024']), 'source_url': URL24 + '#page=' + str(row['pdf_page']),
            'evidence_location': f"표6·{row['province']} {row['region']} 행·전체/초혼/재혼 열; PDF{row['pdf_page']}쪽",
        })
    ranks.sort(key=lambda r: r['total_rank'])
    index = {r['region_key']: r for r in ranks}
    assert {key(r) for r in top20['regions']} == {r['region_key'] for r in ranks if r['in_total_top20']}
    for row in top20['regions']:
        assert row['newlywed_couples'] == index[key(row)]['total_couples']
        assert row['first_marriage_couples'] == index[key(row)]['first_marriage_couples']
    first_order = sorted(ranks, key=lambda r: r['first_marriage_rank'])
    unchanged_top4 = [r['region_key'] for r in ranks[:4]] == [r['region_key'] for r in first_order[:4]]
    assert unchanged_top4
    exact_rows = {
        'ENH2-DONGAN': ('경기|안양시 동안구', 22, 16, 7162, 6510),
        'ENH2-MAPO': ('서울|마포구', 21, 17, 7286, 6487),
        'ENH2-NAMDONG': ('인천|남동구', 16, 27, 7997, 5588),
        'ENH2-WONMI': ('경기|부천시 원미구', 20, 24, 7365, 5982),
        'ENH2-MICHUHOL': ('인천|미추홀구', 10, 20, 8483, 6162),
    }
    for _, (k, tr, fr, tc, fc) in exact_rows.items():
        assert (index[k]['total_rank'], index[k]['first_marriage_rank'], index[k]['total_couples'],
                index[k]['first_marriage_couples']) == (tr, fr, tc, fc)
    membership = {label: [r['region_key'] for r in first_order if r['membership'] == label]
                  for label in ['both', 'first_only', 'total_only', 'neither']}
    assert len(membership['both']) == 18
    assert set(membership['first_only']) == {'경기|안양시 동안구', '서울|마포구'}
    assert set(membership['total_only']) == {'인천|남동구', '경기|부천시 원미구'}
    facts = []

    def fact(cid, statement, values, locations, scenes, status='verified', sources=None, dates=None):
        if sources:
            sources = [{**s, 'sha256': digest(ROOT / s['file'])} for s in sources]
        facts.append({'claim_id': cid, 'statement': statement, 'status': status,
            'original_source': sources or [{'url': URL24, 'file': rel(INPUTS['pdf_2024']),
                                           'sha256': digest(INPUTS['pdf_2024'])}],
            'evidence_location': locations, 'reference_date': dates or '2024-11-01',
            'checked_at': CHECKED, 'values': values, 'affected_scene_ids': scenes,
            'verification_method': '해시 일치 기존 원출처 검수 재사용 + 이번 로컬 직접 계산',
            'independent_review_of_new_calculation': False})

    fact('SCOPE-53', '2024-11-01 기준 수도권 53개 구를 전체 수 및 초혼 수로 각각 정렬한다. 전체는 초혼·재혼·혼인종류 미상 포함.',
         {'regions': 53, '서울': 25, '인천': 8, '경기': 20, 'unit': '쌍'},
         ['2024 PDF3쪽 일러두기, 7쪽 각주1, 32~33쪽 표6; 기존 독립 QA definition_evidence',
          'capital_rows.tsv에서 region의 마지막 글자가 구인 53개 행'], ['N001', 'N002'])
    fact('ENH2-MEMBERSHIP', '같은 53개 구를 초혼 수로 정렬하면 전체 TOP20의 18곳이 남고 동안구·마포구가 진입하며 남동구·원미구가 제외된다. 1~4위는 동일하다.',
         {'overlap': 18, 'entrants': membership['first_only'], 'exits': membership['total_only'],
          'top4_unchanged': unchanged_top4, 'denominator_regions': 53},
         ['2024 PDF32~33쪽 표6 전체·초혼 열; chart_data.json 전체 53행을 각각 독립 정렬'], ['N001', 'N002'])
    fact('ENH2-TOP4', '전체와 초혼 모두 1~4위는 인천 서구·서울 송파구·고양시 덕양구·서울 강서구 순이다.',
         {'ordered_region_keys': [r['region_key'] for r in ranks[:4]]},
         ['2024 PDF32~33쪽 표6, 전체/초혼 열 각각 53개 구 공동순위 계산'], ['N001'])
    for cid, (k, tr, fr, tc, fc) in exact_rows.items():
        row = index[k]
        fact(cid, f"{row['province']} {row['region']}: 전체 {tc:,}쌍으로 {tr}위, 초혼 {fc:,}쌍으로 {fr}위.",
             {'region_key': k, 'total_couples': tc, 'first_marriage_couples': fc,
              'total_rank': tr, 'first_marriage_rank': fr, 'denominator_regions': 53},
             [row['evidence_location']], ['N001' if cid in ['ENH2-DONGAN', 'ENH2-MAPO'] else 'N002'])

    transcriptions = {}
    for name in ['facts01_10', 'facts11_20']:
        for row in read(INPUTS[name])['regions']:
            value = row['count2023']
            ev = value if isinstance(value, dict) else row['count2023_evidence']
            transcriptions[row['region_id']] = (value['value'] if isinstance(value, dict) else value, ev, name)
    assert read(INPUTS['old_source_manifest'])['sources']['newlyweds_2023']['sha256'] == digest(INPUTS['pdf_2023'])
    with INPUTS['comparison'].open(encoding='utf-8-sig', newline='') as f:
        comparisons = list(csv.DictReader(f))
    yoy = []
    for row in comparisons:
        rid = 'R' + row['rank'].zfill(2)
        k = key(row)
        old_value, evidence, source_name = transcriptions[rid]
        assert (row['comparison_available'] == 'True') == (old_value is not None)
        if old_value is not None:
            assert evidence['status'] == 'verified' and old_value == int(row['count2023'])
        count24 = int(row['count2024'])
        assert count24 == index[k]['total_couples']
        delta = None if old_value is None else count24 - old_value
        pct = None if old_value is None else delta / old_value * 100
        display = None if old_value is None else display_pct(delta, old_value)
        if old_value is not None:
            assert delta == int(row['change_couples']) and display == float(row['change_percent_display'])
        else:
            assert not row['change_couples'] and not row['change_percent_display']
        record = {'region_id': rid, 'region_key': k, 'total_rank_2024': int(row['rank']),
            'count2023': old_value, 'count2024': count24, 'comparable': old_value is not None,
            'change_couples': delta, 'change_percent': pct, 'change_percent_display': display,
            'percentage_denominator': old_value, 'claim_id': 'ENH2-YOY-' + rid,
            'source2023_file': rel(INPUTS['pdf_2023']), 'source2023_url': URL23,
            'source2023_evidence_location': evidence['evidence_location'],
            'source2024_url': index[k]['source_url'],
            'transcription_file': rel(INPUTS[source_name]),
            'transcription_evidence_pointer': f"regions[region_id={rid}].count2023",
            'qualification': None if old_value is not None else '2023 원표의 같은 범위 원미구 행 미수록. 부천시 전체 수로 대체하지 않음.'}
        yoy.append(record)
        fact(record['claim_id'], f"{row['province']} {row['region']}: " +
             (f"{old_value:,}→{count24:,}쌍, 전년 대비 {delta:+,}쌍({display:+.1f}%)." if old_value is not None else
              '2023년 같은 범위 원값이 없어 증감 계산 불가.'),
             record, [evidence['evidence_location'], index[k]['evidence_location']],
             [scene_ids[k]], status='verified' if old_value is not None else 'qualified',
             sources=[{'url': URL23, 'file': rel(INPUTS['pdf_2023']), 'sha256': digest(INPUTS['pdf_2023'])},
                      {'url': URL24, 'file': rel(INPUTS['pdf_2024']), 'sha256': digest(INPUTS['pdf_2024'])}],
             dates=['2023-11-01', '2024-11-01'])
    comparable = [r for r in yoy if r['comparable']]
    old_sum, new_sum = (sum(r[c] for r in comparable) for c in ['count2023', 'count2024'])
    assert len(comparable) == 19 and (old_sum, new_sum) == (181425, 177161)
    summary = {'selected_cohort': '2024 전체 TOP20 중 비교 가능한 고정 19개 구, 원미구 제외',
        'regions': 19, 'count2023_sum': old_sum, 'count2024_sum': new_sum,
        'change_couples': new_sum - old_sum, 'change_percent': (new_sum - old_sum) / old_sum * 100,
        'change_percent_display': display_pct(new_sum - old_sum, old_sum),
        'percentage_denominator': old_sum, 'increasing': sum(r['change_couples'] > 0 for r in comparable),
        'decreasing': sum(r['change_couples'] < 0 for r in comparable),
        'formula': '(sum(count2024)-sum(count2023))/sum(count2023)*100; 지역별 변화율 단순평균 아님'}
    fact('ENH2-MATCHED19', '2024 전체 TOP20 중 비교 가능한 고정 19개 구의 합계는 181,425→177,161쌍, 4,264쌍(2.4%) 감소했다.',
         summary, ['chart_data.json yoy_comparable_top20의 비교 가능 19행 합산'], [],
         sources=[{'url': URL23, 'file': rel(INPUTS['pdf_2023'])}, {'url': URL24, 'file': rel(INPUTS['pdf_2024'])}],
         dates=['2023-11-01', '2024-11-01'])
    chart = {'task_id': 'top20-enhance-research-v2', 'reference_date': '2024-11-01',
        'unit': '쌍', 'ranking_population': '2024 수도권53개구: 서울25·인천8·경기20',
        'rank_method': '1+자기보다 값이 큰 구의 개수. 동률 공동순위(competition ranking).',
        'comparison_kind': '같은 기준일의 전체/초혼 지표 차이. 연도별 변화 아님.',
        'total_vs_first_marriage_53_gu': ranks, 'top20_membership': membership,
        'quoted_five_rows': {cid: index[v[0]] for cid, v in exact_rows.items()},
        'top4_unchanged': unchanged_top4, 'yoy_comparable_top20': yoy, 'yoy_matched19_summary': summary,
        'display_notes': ['전체는 초혼·재혼·혼인종류 미상 포함. 전체에서 재혼을 빼서 초혼을 계산하지 않음.',
            '부부 거처가 다르면 각 시군구에 0.5 가중치. 공표 정수의 반올림 때문에 세부 합계 차이가 날 수 있음.',
            '순위 차이는 지역의 선호·순유입·투자수익 또는 해당 원인에 대한 증거가 아님.',
            '전년 변화율 분모는 각 지역 2023년 공표값. 2024 TOP20 고정19개구 합계는 수도권 전체 변화율이 아님.']}
    facts_doc = {'task_id': 'top20-enhance-research-v2', 'revision': 'research-enhance-v2-final',
        'adopted_scene_ids': ['N001', 'N002'], 'facts': facts,
        'source_reuse': {'prior_qa': rel(INPUTS['source_qa']), 'all_86_rows_official_ledger_matched': True,
            'unchanged_input_hashes_confirmed': True, 'pdf_newly_extracted_or_visually_reviewed': False,
            'new_arithmetic_self_validated': True, 'new_arithmetic_independent_qa_performed': False},
        'unverified': ['새 계산의 독립 QA 미실시. 이 스크립트·차트·채택 원고의 검수 요청을 총괄에게 전달.',
            '선호도·전입/순유입·차이의 원인은 분석하지 않았음. 실제 음성 길이와 청취는 미확인.'],
        'input_manifest': 'source_manifest.json'}
    return {'chart_data.json': chart, 'verified_facts.json': facts_doc}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    manifest = {name: {'path': rel(path), 'sha256': digest(path), 'bytes': path.stat().st_size}
                for name, path in INPUTS.items()}
    outputs = compute()
    if args.write:
        for name, data in {**outputs, 'source_manifest.json': manifest}.items():
            (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        for name, field in [('ranking_53_gu.csv', 'total_vs_first_marriage_53_gu'),
                            ('top20_yoy.csv', 'yoy_comparable_top20')]:
            rows = outputs['chart_data.json'][field]
            with (OUT / name).open('w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
    assert read(OUT / 'source_manifest.json') == manifest, '입력 버전 변경: 기존 통과 승계 불가'
    for name, data in outputs.items():
        assert read(OUT / name) == data, name + ' 저장값과 재계산 불일치'
    for name, field in [('ranking_53_gu.csv', 'total_vs_first_marriage_53_gu'), ('top20_yoy.csv', 'yoy_comparable_top20')]:
        with (OUT / name).open(encoding='utf-8-sig', newline='') as f:
            csv_rows = list(csv.DictReader(f))
        assert len(csv_rows) == len(outputs['chart_data.json'][field])
        for saved, row in zip(csv_rows, outputs['chart_data.json'][field]):
            assert saved == {k: '' if v is None else str(v) for k, v in row.items()}
    scene_doc = read(INPUTS['adopted_scenes'])
    assert [s['scene_id'] for s in scene_doc['scenes']] == ['N001', 'N002']
    sentence_ids = {s['sentence_id'] for scene in scene_doc['scenes'] for s in scene['sentences']}
    assert len(sentence_ids) == 10
    known_claims = {f['claim_id'] for f in outputs['verified_facts.json']['facts']}
    assert all(set(s.get('claim_ids', [])) <= known_claims for scene in scene_doc['scenes'] for s in scene['sentences'])
    receipt = {'status': 'passed', 'task_id': 'top20-enhance-research-v2',
        'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'validator_sha256': digest(Path(__file__)),
        'checks': {'input_hashes': len(manifest), 'official_qa_ledger_rows': 86,
            'full_pool_rows': 53, 'membership_overlap': 18, 'entrants': 2, 'exits': 2,
            'quoted_five_rows_exact': True, 'top4_unchanged': True,
            'yoy_rows': 20, 'yoy_comparable_rows': 19, 'noncomparable_null_rows': 1,
            'json_and_csv_recomputed': True, 'adopted_sentence_claim_references_resolved': True},
        'output_sha256': {n: digest(OUT / n) for n in [*outputs, 'source_manifest.json', 'ranking_53_gu.csv', 'top20_yoy.csv']},
        'independent_qa': False, 'pdf_rerendered': False, 'tts_used': False}
    (OUT / 'validation_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'passed', 'checks': receipt['checks'],
        'output_folder': rel(OUT), 'yoy_summary': outputs['chart_data.json']['yoy_matched19_summary']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
