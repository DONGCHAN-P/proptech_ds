"""동결된 본편 문장을 복사해 쇼츠 계획만 생성한다. 네트워크/미디어 생성 없음."""
from pathlib import Path
import hashlib
import json
import re

OUT = Path(__file__).resolve().parent
EP = OUT.parents[2]
PROJECT = EP.parents[2]
TASK = 'part1-Jun-shorts-3way-content-plan'
REV = 'top20-split-v4/jun-and-shorts-v1'

SOURCES = {
    'SRC-BODY-LOCK': EP / 'director/top20-split-v4/part1-map-clean-v1/locked_timing.json',
    'SRC-INTRO-LOCK': EP / 'director/top20-split-v4/part1-intro-v3/locked_timing.json',
    'SRC-CRITERIA': EP / 'writer/top20-split-v4/map-clean-v1/criteria_script.json',
    'SRC-APPROVED-BODY': EP / 'director/top20-split-v4/part1-production-v1/approved_part1_scene_proposals.json',
    'SRC-PRICE-LEGEND': EP / 'research/top20-split-v4/prices/legend.json',
    'SRC-PRICE-INSIGHTS': EP / 'research/top20-split-v4/prices/region_insights.json',
    'SRC-PRICE-COVERAGE': EP / 'research/top20-split-v4/prices/coverage.json',
    'SRC-COHORT-CODE': EP / 'research/top20-split-v4/prices/build_region_insights.py',
    'SRC-RANKING': EP / 'research/top20-8min-v2/top20.json',
    'SRC-VERTICAL': PROJECT / 'config/vertical_video_safe_area.json',
    'CTX-STATE': EP / 'state.json',
    'CTX-BRIEF': EP / 'brief.json',
}


def read(key):
    return json.loads(SOURCES[key].read_text(encoding='utf-8-sig'))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def pointer(data, value):
    for token in value.strip('/').split('/'):
        token = token.replace('~1', '/').replace('~0', '~')
        data = data[int(token)] if isinstance(data, list) else data[token]
    return data


def price_text(value):
    value = int(value)
    eok, man = divmod(value, 10000)
    return f'{eok}억{man:,}만원' if man else f'{eok}억원'


body = read('SRC-BODY-LOCK')
intro = read('SRC-INTRO-LOCK')
criteria = read('SRC-CRITERIA')
approved = read('SRC-APPROVED-BODY')
insights = read('SRC-PRICE-INSIGHTS')
legend = read('SRC-PRICE-LEGEND')
ranking = read('SRC-RANKING')
vertical = read('SRC-VERTICAL')
coverage = read('SRC-PRICE-COVERAGE')

manifest = {
    'task_id': TASK, 'revision': REV,
    'hash_algorithm': 'SHA256 of original file bytes',
    'inputs': [
        {'source_id': key, 'path': str(path).replace('\\', '/'),
         'sha256': sha(path.read_bytes()), 'bytes': path.stat().st_size,
         'stability_required': key.startswith('SRC-')}
        for key, path in SOURCES.items()
    ],
    'authority_ko': '최신 task packet의 map-clean-v1 수용·Jun 및 쇼츠 3편 지시를 적용한다. state의 과거 free-only/완료 대기는 당시 기록이며 새 유료 생성·업로드 승인으로 사용하지 않는다.',
    'external_fact_verification_performed': False,
}
write('source_manifest.json', manifest)

main = {}
for i, scene in enumerate(body['body_scenes']):
    for j, sentence in enumerate(scene['sentences']):
        main[sentence['sentence_id']] = {
            **sentence, 'source_id': 'SRC-BODY-LOCK',
            'source_pointer': f'/body_scenes/{i}/sentences/{j}',
            'region_id': scene.get('region_id'), 'scene_id': scene['scene_id'],
        }
for i, sentence in enumerate(intro['intro_sentences']):
    main[sentence['sentence_id']] = {
        **sentence, 'source_id': 'SRC-INTRO-LOCK',
        'source_pointer': f'/intro_sentences/{i}', 'region_id': None,
        'scene_id': 'P01-INTRO',
    }
for i, sentence in enumerate(criteria['sentences']):
    main[sentence['sentence_id']] = {
        **sentence, 'source_id': 'SRC-CRITERIA',
        'source_pointer': f'/sentences/{i}', 'region_id': None,
        'scene_id': 'P01-CRITERIA',
    }
assert len(main) == 90
assert sum(len(s['sentences']) for s in body['body_scenes']) == 80

approved_by_id = {s['sentence_id']: s for sc in approved['scenes'] for s in sc['sentences']}
regions = {}
price_checks = []
rank_checks = []
for sc in approved['scenes']:
    if sc.get('scene_kind') != 'region':
        continue
    rank = sc['rank']
    rid = sc['region_id']
    p = sc['spoken_price_comparison']
    rank_sentence = sc['sentences'][0]
    price_sentence = next(s for s in sc['sentences'] if s['text'] == p['spoken_text'])
    frozen_rank = ranking['regions'][rank - 1]
    assert frozen_rank['region_id'] == rid
    assert f"{frozen_rank['newlywed_couples']:,}쌍" in rank_sentence['text']
    assert main[rank_sentence['sentence_id']]['text'] == rank_sentence['text']
    assert main[price_sentence['sentence_id']]['text'] == p['spoken_text']
    fact_rows = []
    selected_refs = [f for f in price_sentence['source_fields'] if f['claim_id'] == p['claim_id']]
    for i, row in enumerate(p['rows']):
        ref = selected_refs[i]
        frozen_row = pointer(insights, ref['field'])
        assert all(frozen_row[k] == v for k, v in row.items())
        shown_label = row.get('dong', row.get('label'))
        if rid == 'R20' and i == 0:
            shown_label = '2000년까지 준공(2000년 포함)'
        if p['type'] == 'band_distribution':
            shown_label = ['5억원 미만', '5억원 이상 7억원 미만'][i]
        fact_rows.append({
            **row, 'display_label': shown_label,
            'display_value': price_text(row['median_manwon']) if 'median_manwon' in row else f"{row['complex_n']}곳",
            'sample_display': f"거래 n={row['transaction_n']}" if 'transaction_n' in row else f"지도 연결 단지 {row['denominator']}곳 중",
            'source_id': 'SRC-PRICE-INSIGHTS', 'json_pointer': ref['field'],
        })
    if p['type'] == 'band_distribution':
        assert sum(x['complex_n'] for x in fact_rows) == 77
        assert insights['regions'][rank - 1]['mapped_complexes'] == 77
    regions[rank] = {
        'region_id': rid, 'rank': rank, 'province': frozen_rank['province'],
        'region': frozen_rank['region'], 'couples': frozen_rank['newlywed_couples'],
        'ledger_label': f"{rank}위 {frozen_rank['region'].split()[-1]} · {frozen_rank['newlywed_couples']:,}쌍",
        'active_full_region_title': f"{rank}위 {frozen_rank['province']} {frozen_rank['region']}",
        'rank_sentence_id': rank_sentence['sentence_id'],
        'price_sentence_id': price_sentence['sentence_id'],
        'price_type': p['type'], 'price_definition': p['denominator'],
        'claim_id': p['claim_id'], 'rows': fact_rows,
    }
    price_checks.append({'region_id': rid, 'sentence_id': price_sentence['sentence_id'],
                         'result': 'pass', 'row_count': len(fact_rows), 'price_type': p['type'],
                         'scope': '승인 본문 값·문장과 동결 region_insights의 지정 JSON pointer 대조; 원거래 재집계 아님'})
    rank_checks.append({'region_id': rid, 'sentence_id': rank_sentence['sentence_id'],
                        'result': 'pass', 'rank': rank, 'couples': frozen_rank['newlywed_couples']})

CTA_TEXT = '나머지 순위도 궁금하시다면 다른 순위 영상을 확인해 주세요. 지역별 자세한 가격과 생활권 비교는 본편에서 이어집니다.'
cta_texts = [t + '.' for t in CTA_TEXT.split('. ') ]
cta_texts[-1] = cta_texts[-1].rstrip('.') + '.'
assert len(cta_texts) == 2 and ' '.join(cta_texts) == CTA_TEXT
cta = {
    'revision': REV, 'asset_id': 'JUN-SHORTS-COMMON-CTA-V1',
    'status': 'text_proposal_only_audio_not_generated',
    'exacttext': CTA_TEXT,
    'sentences': [{'sentence_id': f'P01-SHORTS-CTA-{i+1:02}', 'exacttext': text,
                   'reading_text': text, 'audio_asset_ref': f'JUN-SHORTS-COMMON-CTA-V1/S{i+1:02}'}
                  for i, text in enumerate(cta_texts)],
    'reuse_in': ['SHORT01-PROMO', 'SHORT02-R20-R16', 'SHORT03-R15-R11'],
    'new_unique_sentences': 2, 'sentence_uses': 6,
    'characters_including_spaces_and_punctuation': len(CTA_TEXT),
    'characters_excluding_whitespace': len(re.sub(r'\s', '', CTA_TEXT)),
    'utf8_bytes': len(CTA_TEXT.encode('utf-8')),
    'counting_note': '문자수는 로컬 원문 길이. 제공자 청구 크레딧·실제 비용으로 확정하지 않는다. 총괄의 본편 90문장 예산에 신규 2문장을 한 번만 추가한다.',
    'generation_owner': '총괄 → narration', 'generation_authorized_by_this_plan': False,
    'audio_path': None, 'measured_duration_s': None,
    'pronunciation_dictionary': [],
    'emphasis': ['나머지 순위', '자세한 가격', '생활권 비교', '본편'],
    'direction': '자연스러운 안내. 두 문장을 한 번 생성해 세 편에서 재사용한다. 문장별 파일 또는 정확한 경계로 분리한다.',
}
write('common_cta.json', cta)

common_screenfacts = [
    {'fact_id': 'F-RANK-DEFINITION', 'text': '2024.11.01 신혼부부 수 · 수도권 53개 구',
     'source_ids': ['SRC-RANKING'], 'source_fields': ['/scope', '/statistic_reference_date', '/unit'],
     'show': '첫 순위 표시 전부터, 신혼부부 거주 수 순위임을 표시'},
    {'fact_id': 'F-PRICE-CONDITIONS', 'text': '아파트 실거래 · 전용 83~85㎡ · 2026.05~10 계약',
     'source_ids': ['SRC-PRICE-LEGEND', 'SRC-CRITERIA'],
     'source_fields': ['/area_m2', '/period', '/sentences/0/text'],
     'show': '첫 프레임의 조건 화면과 모든 가격 화면; 신규 낭독 없음'},
    {'fact_id': 'F-PRICE-CUTOFF', 'text': '2026.11.03 조회 · 취소 제외 · 10월은 조회일까지 신고분',
     'source_ids': ['SRC-PRICE-LEGEND', 'SRC-CRITERIA', 'SRC-APPROVED-BODY'],
     'source_fields': ['/retrieved_date', '/sentences/1/text', '/scenes/0/sentences/4/text'],
     'show': '가격 조건 화면에서 먼저 표시, 가격 화면에는 조회일·취소 제외 유지'},
]


def fact_set(ranks):
    facts = json.loads(json.dumps(common_screenfacts, ensure_ascii=False))
    for rank in ranks:
        r = regions[rank]
        facts.extend([
            {'fact_id': f'F-{r["region_id"]}-RANK', 'regionid': r['region_id'],
             'text': f"{rank}위 {r['province']} {r['region']} · {r['couples']:,}쌍",
             'sentence_id': r['rank_sentence_id'], 'claim_ids': approved_by_id[r['rank_sentence_id']]['claim_ids'],
             'source_ids': ['SRC-RANKING', 'SRC-BODY-LOCK'],
             'source_fields': [f'/regions/{rank-1}', main[r['rank_sentence_id']]['source_pointer']]},
            {'fact_id': f'F-{r["region_id"]}-PRICE', 'regionid': r['region_id'],
             'sentence_id': r['price_sentence_id'], 'claim_ids': [r['claim_id'], 'W4-METHOD'],
             'definition': r['price_definition'], 'price_type': r['price_type'],
             'source_ids': ['SRC-PRICE-INSIGHTS', 'SRC-PRICE-LEGEND', 'SRC-APPROVED-BODY'],
             'source_fields': [x['json_pointer'] for x in r['rows']],
             'rows': r['rows'], 'period': legend['period'], 'area_m2_inclusive': legend['area_m2'],
             'retrieved_date': legend['retrieved_date'],
             'display_definition': (
                 '단지별 거래 중위가격의 구간별 단지 수' if r['price_type'] == 'band_distribution'
                 else '준공 시기별 거래 중위값' if r['price_type'] == 'cohort_pair' else '법정동별 거래 중위값'),
             'interpretation': '동결 표본의 비교. 거래 구성·입지·연식 등의 차이가 함께 섞여 있다.',
             'show': '비교 집단명·두 값·각 표본수를 해당 발화에서 끝까지 표시'},
        ])
    return facts


def reused(sid, message, purpose, materials):
    s = main[sid]
    approved_sentence = approved_by_id.get(sid, {})
    return {
        'sentence_id': sid, 'exacttext': s['text'], 'reading_text': s.get('reading_text', s['text']),
        'regionid': s['region_id'], 'screenmessage': message,
        'visualpurpose': purpose, 'material_types': materials, 'screen_role': 'explanation',
        'voice_mode': 'reuse_full_main_Jun_complete_sentence',
        'audio_asset_ref': f'JUN-MAIN-SENTENCE/{sid}',
        'audio_asset_status': 'logical_reference_pending_parent_Jun_sentence_manifest',
        'claim_ids': approved_sentence.get('claim_ids', []),
        'source_ids': [s['source_id']], 'source_json_pointer': s['source_pointer'],
        'reference_free_voice_timing': {
            'source_id': s['source_id'], 'start_s': s.get('start_s'), 'end_s': s.get('end_s'),
            'purpose': '원문 위치/기존 무료 음성 길이 참고. Jun 추출 in/out 및 쇼츠 타임코드로 사용 금지',
        },
        'jun_start_s': None, 'jun_end_s': None,
    }


def region_sequence(rank):
    r = regions[rank]
    label = f"{rank}위 {r['province']} {r['region']} · {r['couples']:,}쌍"
    values = ' / '.join(f"{x['display_label']} {x['display_value']} ({x['sample_display']})" for x in r['rows'])
    return [
        reused(r['rank_sentence_id'], label,
               '설명: 다섯 지역의 순위·쌍 수 목록을 유지하고 현재 지역 한 행을 강조한다.', ['data_chart']),
        reused(r['price_sentence_id'], values,
               '설명: 현재 행을 펼쳐 두 비교 집단과 가격·표본수를 표시한다. 남동구는 77개 단지의 구간별 빈도를 표시한다.'
               if rank == 16 else '설명: 현재 행을 펼쳐 비교 집단명·두 중위값·거래 표본수를 함께 표시하고 발화에 맞춰 해당 값을 강조한다.',
               ['data_chart']),
    ]


def cta_sequence():
    return [
        {'sentence_id': s['sentence_id'], 'exacttext': s['exacttext'], 'reading_text': s['reading_text'],
         'regionid': None, 'screenmessage': ['다른 순위 영상에서 나머지 지역 확인', '20~11위 전체 가격·생활권 비교는 본편'][i],
         'visualpurpose': '설명: 현재 편의 다른 순위 영상과 20~11위 본편으로 연결한다. 공개 상태 확인 후 총괄이 실제 링크를 연결한다.',
         'material_types': ['editorial_card'], 'screen_role': 'explanation',
         'voice_mode': 'new_common_CTA_reuse_in_all_three', 'audio_asset_ref': s['audio_asset_ref'],
         'source_ids': ['USER-LATEST-TASK-CTA'], 'claim_ids': [],
         'jun_start_s': None, 'jun_end_s': None}
        for i, s in enumerate(cta['sentences'])
    ]


def duration(sequence, promo=False):
    total = sum(main[s['sentence_id']]['end_s'] - main[s['sentence_id']]['start_s']
                for s in sequence if s['sentence_id'] in main)
    return {
        'status': 'estimate_not_Jun_measured', 'target_range_seconds': [35, 50] if promo else [60, 90],
        'planning_range_seconds': [38, 50] if promo else [65, 85],
        'existing_free_voice_speech_sum_seconds_reference_only': round(total, 3),
        'new_common_CTA_estimate_seconds': [10, 14], 'silent_final_hold_seconds': 3,
        'early_conditions_reading_hold_estimate_seconds': [1.5, 2.5],
        'Jun_measured_seconds': None, 'playback_rate': 1.0,
        'timing_rule': 'Jun 생성 후 문장 전체와 호흡을 실제 청취·정렬해 확정. 문장별 전후 여유를 확인하고 목표 길이에 맞추려고 배속하거나 문장 일부를 자르지 않는다.',
        'if_over_target': '우선 자연스러운 발화·조건·다섯 지역 완결을 보존하고 총괄에 실제 길이를 보고한다. 신규 다른 내레이션은 추가하지 않는다.',
    }


promo_sequence = [
    reused('P01-INTRO-V3-01', '우리 예산으로 어느 동네부터?', '설명: 예산과 지역 선택이라는 본편 질문을 연다.', ['editorial_card']),
    reused('P01-INTRO-V3-04', '신혼부부가 많이 사는 지역부터', '설명: 거주 수 통계를 지역 선택의 출발점으로 제시한다.', ['data_chart']),
    reused('P01-INTRO-V3-05', '수도권 53개 구 · 이번 본편 20~11위', '설명: 본편에서 다루는 순위 범위를 정확히 표시한다.', ['data_chart']),
    *region_sequence(17), *cta_sequence(),
]
promo_sequence[3]['visualpurpose'] = '설명: 17위 인천 연수구와 7,875쌍을 크게 보여주고 연수동·송도동 두 비교 집단을 미리 표시한다.'
promo_sequence[4]['visualpurpose'] = '설명: 연수동·송도동의 거래 중위값 두 개를 세로 비교 도표에 크게 표시하고 각 거래 표본수를 붙인다.'

shorts = [
    {'short_id': 'SHORT01-PROMO', 'title': '신혼부부가 많이 사는 동네, 같은 구에서도 예산은 다릅니다 | 20~11위',
     'rankrange': {'from': 20, 'to': 11, 'role': '20~11위 본편 홍보', 'spoken_ranks': [17]},
     'regions': [regions[17]], 'purpose': '거주 순위와 생활권별 가격 차이를 한 사례로 보여주고 본편으로 연결',
     'sequence': promo_sequence, 'screenfacts': fact_set([17]),
     'related_short_ids': ['SHORT02-R20-R16', 'SHORT03-R15-R11']},
]
for sid, ranks, title, purpose in [
    ('SHORT02-R20-R16', list(range(20, 15, -1)), '신혼부부 거주 순위 20~16위 | 다섯 지역의 아파트 가격 비교', '원미·중랑·기흥·연수·남동 다섯 지역의 순위·쌍 수와 서로 다른 가격 비교를 완결'),
    ('SHORT03-R15-R11', list(range(15, 10, -1)), '신혼부부 거주 순위 15~11위 | 다섯 지역의 아파트 가격 비교', '구로·은평·권선·영통·노원 다섯 지역의 순위·쌍 수와 동별 거래 중위값 비교를 완결'),
]:
    sequence = [s for rank in ranks for s in region_sequence(rank)] + cta_sequence()
    shorts.append({'short_id': sid, 'title': title,
                   'rankrange': {'from': ranks[0], 'to': ranks[-1], 'role': '내용 분할', 'spoken_ranks': ranks},
                   'regions': [regions[n] for n in ranks], 'purpose': purpose,
                   'sequence': sequence, 'screenfacts': fact_set(ranks),
                   'related_short_ids': ['SHORT03-R15-R11' if sid == 'SHORT02-R20-R16' else 'SHORT02-R20-R16']})

layout = {
    'canvas': vertical['canvas'], 'profile': 'youtube_portrait_full_frame_v2',
    'source_id': 'SRC-VERTICAL', 'config_revision': vertical['revision'],
    'profile_contract': vertical['profiles']['youtube_portrait_full_frame_v2'],
    'construction': '1080×1920에서 도표·자막을 각각 새 배치. 가로 본편 크롭·완성 패널 축소·중앙 작은 카드 방식은 사용하지 않는다.',
    'five_region_visibility': '내용편은 첫 프레임부터 다섯 지역의 순위·지역명·쌍 수를 한 목록에 표시하고 모든 지역 구간 동안 유지한다. 현재 행만 펼쳐 두 가격 비교 값을 큰 글씨로 보여준다. 끝에서도 다섯 행을 모두 유지한다.',
    'ledger_label_policy': '목록에는 ledger_label의 구 이름과 순위·쌍 수를 사용한다. 현재 지역의 시·도 포함 정식 이름은 active_full_region_title로 제목 영역에 표시한다. 용인시 기흥구·수원시 권선구/영통구·부천시 원미구의 소속을 보존한다.',
    'ledger_geometry_proposal': {'zone_from_profile': 'map_or_chart', 'inactive_row_height_px': 64,
                                  'active_row_max_height_px': 300, 'total_for_five_rows_px': 556,
                                  'available_height_px': 650, 'status': 'layout_proposal_not_bbox_verified'},
    'text_placement': '비핵심 도형은 화면 전체를 채운다. 모든 뜻을 담은 글자·가격·표본수는 프로필 critical_rect 안에 독립 배치한다.',
    'small_text_policy': '공간이 부족하면 조건 읽기 화면과 비교 값 표시 구간을 늘린다. 글자 크기나 전체 화면을 줄여 해결하지 않는다.',
    'caption': '기존 원문을 의미 단위로 분할한다. 숫자·단위·지역명·가격 집단명을 보호하고 본문 흰 자막 박스를 큐 사이에도 유지한다.',
    'CTA_caption_cues_text_only': ['나머지 순위도 궁금하시다면', '다른 순위 영상을 확인해 주세요.',
                                   '지역별 자세한 가격과 생활권 비교는', '본편에서 이어집니다.'],
    'visual_roles': {'explanation': '순위·가격·정의·다음 연결을 설명하는 data_chart/editorial_card',
                     'atmosphere': '별도 분위기 화면 없음. 실제 지역 증거를 분위기 이미지로 대신하지 않는다.'},
    'validation_status': '미디어·프레임 미제작. 실제 글리프 bbox·앱 UI 모사·최장 자막·지역명·가격·표본수는 편집/독립 QA 단계의 필수 확인.',
}

existing_uses = [s['sentence_id'] for sh in shorts for s in sh['sequence'] if s['sentence_id'] in main]
counts = {
    'shorts': 3, 'full_main_sentences': 90, 'full_main_intro': 8, 'full_main_criteria': 2, 'full_main_body_including_outro': 80,
    'reused_main_sentence_uses': len(existing_uses), 'reused_main_unique_sentences': len(set(existing_uses)),
    'new_unique_CTA_sentences': 2, 'new_CTA_sentence_uses': 6,
    'total_sequence_sentence_uses': sum(len(s['sequence']) for s in shorts),
    'regional_comparisons': 10, 'median_price_values': 18, 'distribution_band_counts': 2,
    'full_main_plus_new_CTA_unique_sentences_for_parent_budget': 92,
}

for i, short in enumerate(shorts):
    short['CTAasset_refs'] = [s['audio_asset_ref'] for s in cta['sentences']]
    short['CTA_text_ref'] = 'common_cta.json'
    short['targetduration'] = duration(short['sequence'], i == 0)
    short['shared_layout_ref'] = 'shorts_plan.json#/layout_contract'
    short['source_manifest_ref'] = 'source_manifest.json'
    short['voice_reuse_policy'] = '본편 Jun 문장 ID 단위로 완결된 음성을 재사용한다. exacttext와 reading_text를 보존하고 신규 음성은 공통 CTA 2문장뿐이다.'
    short['opening_conditions'] = {
        'before_first_price': True, 'on_first_frame': True,
        'screen_only_text': ['가격: 거래 중위값', '전용 83~85㎡ · 2026.05~10 계약',
                             '2026.11.03 조회 · 취소 제외', '10월은 조회일까지 신고분'],
        'definition_detail': '동/준공군은 거래별 중위값. 남동구는 단지별 거래 중위값의 구간별 단지 수.'
                             if i == 1 else '법정동별 수록 거래의 가운데 값. 지도 점의 단지별 중위가격과 집계 단위를 구분한다.',
        'narration_added': False,
    }
    short['ending'] = {
        'exacttext': CTA_TEXT, 'silent_hold_after_last_word_seconds': 3,
        'other_ranking_targets': short['related_short_ids'],
        'full_main_target': 'map-clean-v1을 계승하는 Jun 본편 20~11위',
        'actual_urls': None, 'links_applied': False,
        'release_dependency': '다른 순위 영상/본편의 실제 게시 상태와 URL은 총괄이 확인 후 연결한다. 10~1위 제작·공개를 전제하지 않는다.',
    }

issues = [
    {'issue_id': 'DEF-R20-BOUNDARY', 'scene_ids': ['P01-R20', 'SHORT02-R20-R16'],
     'problem': '동결 집계의 표 이름은 2000년 이전이지만 집계·승인 발화는 2000년을 포함한다.',
     'evidence': {'source_ids': ['SRC-COHORT-CODE', 'SRC-APPROVED-BODY'], 'detail': 'cohort 경계 (0,2000); 승인 denominator에 2000년 포함 명시'},
     'proposal': '쇼츠 표시문만 2000년까지 준공(2000년 포함)으로 정확히 쓴다. 기존 본편 발화는 그대로 재사용한다.',
     'impact': '가격 정의·화면 집단명', 'status': '계획에 반영, 렌더 확인 필요'},
    {'issue_id': 'DEF-AGGREGATION-UNIT', 'scene_ids': [f'P01-R{x:02}' for x in range(20, 10, -1)],
     'problem': '동별·준공군 거래 중위값, 단지별 거래 중위가격, 남동구 구간별 단지 수는 집계 단위가 다르다.',
     'evidence': {'source_ids': ['SRC-PRICE-INSIGHTS', 'SRC-PRICE-LEGEND'], 'detail': insights['method']},
     'proposal': '동/준공군 거래 중위값과 단지별 중위가격의 분포를 화면에서 구분한다. 남동은 77개 중 61/16개를 모두 유지한다.',
     'impact': '초기 정의·가격 도표·표본수', 'status': '계획에 반영, 편집/QA 확인 필요'},
    {'issue_id': 'DEF-CUTOFF-AND-DEDUP', 'scene_ids': [s['short_id'] for s in shorts],
     'problem': '10월은 조회일까지 신고분이며 coverage는 additional_normal_trade_deduplication=false이다.',
     'evidence': {'source_ids': ['SRC-PRICE-COVERAGE', 'SRC-PRICE-LEGEND', 'SRC-APPROVED-BODY'], 'detail': '/additional_normal_trade_deduplication=false; 기존 도입의 10월 조회일 신고분 조건'},
     'proposal': '기간·면적·조회일·취소 제외를 처음에 표시한다. 추가 정상거래 중복 제거를 했다고 주장하지 않는다. 새 조사·집계 없이 동결 값을 보존한다.',
     'impact': '조건 표기·검증 주장 범위', 'status': '제약 기록; 원천 재집계 미실시'},
    {'issue_id': 'LINKS-PENDING', 'scene_ids': [s['short_id'] for s in shorts],
     'problem': '새 세 편과 Jun 본편의 게시 URL은 입력에 없다. 10~1위는 현재 state에서 대본 승인 대기다.',
     'evidence': {'source_ids': ['CTX-STATE'], 'detail': '/active_publication_status=local_only_not_uploaded; /active_parts/1/status=script_approval_pending; 최신 task의 10~1위 공개 전제 금지'},
     'proposal': 'CTA는 지정된 두 문장만 공통 사용한다. 다른 순위 영상은 A↔B, 홍보편은 A/B로 연결하고 20~11위 전체 비교는 본편으로 연결한다. 실제 링크는 총괄이 게시 상태 확인 후 적용한다.',
     'impact': '게시 시 연결 대상·메타데이터', 'status': '총괄 다음 단계 확인 필요; 계획 작성 차단 아님'},
]

plan = {
    'task_id': TASK, 'revision': REV, 'status': 'writer_content_plan_only',
    'ownership': str(OUT).replace('\\', '/') + '/**',
    'latest_scope': '홍보 1 + 내용 20→16위 1 + 내용 15→11위 1, 합계 3편',
    'counts': counts, 'source_manifest_ref': 'source_manifest.json',
    'shared_CTA_ref': 'common_cta.json', 'layout_contract': layout,
    'narration_handoff': {
        'full_main_parent_owned': True, 'new_unique_sentence_ids': [s['sentence_id'] for s in cta['sentences']],
        'pronunciation_policy': '재사용 문장은 source reading_text와 본편 Jun의 확정 발음을 그대로 따른다. 숫자·지역명을 쇼츠용으로 다시 쓰지 않는다.',
        'pronunciation_dictionary': {'원미구': '원미구', '기흥구': '기흥구', '권선구': '권선구', '영통구': '영통구',
                                     '중위값': '중윗값', '13억2,000만원': '십삼 억 이천 만 원', '3억3,150만원': '삼 억 삼천백오십 만 원'},
        'emphasis': ['현재 순위·지역명', '두 비교 집단', '두 가격 또는 두 구간별 단지 수', '나머지 순위', '본편'],
        'paid_generation_performed': False, 'audio_listening_performed': False,
    },
    'shorts': shorts, 'factual_and_definition_issues': issues,
    'next_steps': ['총괄이 본편 90문장 Jun 예산에 공통 CTA 신규 2문장을 한 번만 반영',
                   'narration이 Jun 문장별 실제 음성과 타이밍을 전달한 후 editor가 9:16으로 새 배치',
                   '독립 QA가 모든 음성 편집점·가격·다섯 지역 가독성·CTA 마지막 5~10초·UI 모사를 확인',
                   '총괄이 실제 영상/게시 승인 범위와 다른 순위 영상·본편 링크를 확인'],
    'verification_scope': '원문/문장 ID·동결 수치·정의·파일 해시 대조. 새 조사·유료 생성·Claude·외부 API·업로드·영상 재생·청취는 수행하지 않음.',
}
write('shorts_plan.json', plan)
for name, short in zip(['short01_promo.json', 'short02_ranks20_16.json', 'short03_ranks15_11.json'], shorts):
    write(name, {'revision': REV, 'task_id': TASK, **short})
write('issue_DEFINITIONS_AND_LINKS.json', {'task_id': TASK, 'recipient': '총괄', 'direct_peer_message_tool_available': False, 'issues': issues})

lines = [
    '# Jun 재사용 쇼츠 3편 구성안', '',
    '홍보 1편, 20→16위 1편, 15→11위 1편이다. 본편 원문·완결 문장 ID를 그대로 재사용한다. 신규 내레이션은 세 편 공통 CTA 두 문장뿐이다. 본편·사용자 원고·공통 상태 파일은 수정하지 않았다.', '',
    '| 편 | 범위 | 재사용 문장 | 신규 CTA 사용 | 목표 길이 |',
    '|---|---|---:|---:|---|',
]
for sh in shorts:
    n = sum(s['sentence_id'] in main for s in sh['sequence'])
    target = sh['targetduration']['target_range_seconds']
    lines.append(f"| {sh['short_id']} | {sh['rankrange']['from']}→{sh['rankrange']['to']} | {n} | 2 | {target[0]}~{target[1]}초 estimate |")
lines += [
    '', f"본편 90문장(도입 8 + 조건 2 + 본문·마무리 80) 중 쇼츠 재사용은 고유 {counts['reused_main_unique_sentences']}문장, 총 {counts['reused_main_sentence_uses']}회다. 공통 CTA는 고유 2문장, 총 6회 사용한다. 총괄 예산은 본편 90 + 공통 CTA 2 = 고유 92문장 기준으로 전달하며, 이 계획은 생성 실행·비용 승인을 뜻하지 않는다.",
    '', '## 공통 신규 CTA', '', f'> {CTA_TEXT}', '',
    f"`common_cta.json`의 `P01-SHORTS-CTA-01/02`를 한 번 생성해 세 편에서 재사용한다. 원문 문자 수는 공백·문장부호 포함 {cta['characters_including_spaces_and_punctuation']}자, 공백 제외 {cta['characters_excluding_whitespace']}자다. 실제 청구 크레딧은 총괄이 산정한다.",
    '', '다른 순위 영상은 20~16위와 15~11위의 상호 연결이다. 전체 20~11위의 상세 가격·생활권 비교는 본편으로 연결한다. 새 결과물의 URL은 아직 없으므로 게시 상태를 확인한 뒤 실제 링크를 연결한다. 10~1위가 이미 제작·공개됐다는 문장·화면은 넣지 않는다.',
    '', '## 9:16 화면·시간 공통 기준', '',
    '- 1080×1920, 30fps. `youtube_portrait_full_frame_v2`를 선택하고 가로 영상 크롭 없이 도표·자막을 새로 배치한다.',
    '- 첫 프레임부터 `전용 83~85㎡ · 2026.05~10 계약 · 거래 중위값`을 읽게 한다. 초기 조건 화면에는 `2026.11.03 조회·취소 제외·10월은 조회일까지 신고분`도 표시한다. 신규 낭독은 없다.',
    '- 내용편은 다섯 지역의 순위·이름·쌍 수를 첫 화면부터 목록으로 모두 보인다. 목록은 `18위 기흥구 · 7,686쌍`처럼 구 이름으로 쓰고 현재 지역의 시·도 포함 정식 이름은 제목에 표시한다. 네 비활성 행 64px씩과 현재 가격 비교 행 최대300px의 합계556px를 650px 도표 영역에 배치하는 제안이다. 현재 행의 비교 집단·두 값·표본수를 순서대로 크게 보여주고 나머지 네 지역도 보이게 유지한다.',
    '- 제목56px·자막54px·핵심값52px·조건26px 이상을 기준으로 실제 bbox를 측정한다. 다섯 지역·모든 가격을 담으려고 화면 전체나 글자를 축소하지 않는다. UI 겹침은 편집·독립 QA에서 검증한다.',
    '- 설명 화면은 data_chart/editorial_card다. 별도 분위기 화면은 계획하지 않았다. 남동구는 지도 연결77개 단지의 빈도 도표로 표시하며 도표의 점을 실제 지리 좌표처럼 제시하지 않는다.',
    '- 시간은 모두 estimate다. 기존 무료 음성 시작·끝은 원문 위치 참고용이다. Jun 문장 ID의 실제 음성을 확보한 뒤 새 타이밍을 정하며 배속으로 60초에 맞추지 않는다. 마지막 발화 뒤 무음 화면3초를 포함한다.',
]
for sh in shorts:
    lines += ['', f"## {sh['short_id']} · {sh['title']}", '', sh['purpose'], '',
              f"목표 {sh['targetduration']['target_range_seconds'][0]}~{sh['targetduration']['target_range_seconds'][1]}초 estimate. 기존 무료 음성의 선택 문장 발화 합계 {sh['targetduration']['existing_free_voice_speech_sum_seconds_reference_only']}초는 Jun 길이가 아니다. 공통 CTA estimate 10~14초, 조건 읽기·호흡·마지막3초를 더해 실제 Jun에서 재측정한다.", '',
              '| 순서 | 문장 ID / 지역 | 완결 원문 | 화면 메시지·목적 |', '|---:|---|---|---|']
    for i, s in enumerate(sh['sequence'], 1):
        lines.append(f"| {i} | `{s['sentence_id']}` / {s['regionid'] or '공통'} | {s['exacttext']} | {s['screenmessage']} — {s['visualpurpose']} |")
    lines += ['', '가격·표본수 원문 유지:', '', '| 지역 | 비교 정의 | 두 집단·값·표본수 | 근거 ID |', '|---|---|---|---|']
    for r in sh['regions']:
        rowtext = ' / '.join(f"{x['display_label']} **{x['display_value']}** ({x['sample_display']})" for x in r['rows'])
        lines.append(f"| {r['rank']}위 {r['region']} | {r['price_definition']} | {rowtext} | `{r['claim_id']}` · `SRC-PRICE-INSIGHTS` |")
lines += ['', '## 정의와 검증 범위', '']
for issue in issues:
    lines += [f"- **{issue['issue_id']}**: {issue['problem']} {issue['proposal']}"]
lines += ['', '순위·쌍 수10개, 기존 가격 비교10문장, 가격18개와 남동구 구간별 단지 수2개를 승인 본문·동결 집계의 JSON pointer로 대조했다. 최고가·지역 전체 가격·수익률·교통 인과로 확대하지 않는다. 새로운 사실 조사나 원거래 재집계는 하지 않았다.', '',
          '실제 음성·렌더·표본 프레임·연속 재생·청취·독립 QA는 이번 계획서의 검증 범위 밖이다. 문장 끝 잘림, 다음 문장 첫소리 유입, 자막 숫자·단위, 전체 다섯 지역 가독성, 비교 정의, 마지막 CTA와3초 유지 구간을 실제 출력에서 검수해야 한다.', '',
          '## 파일·다음 담당', '',
          '- 통합 원본: `shorts_plan.json`; 개별 계획: `short01_promo.json`, `short02_ranks20_16.json`, `short03_ranks15_11.json`.',
          '- 공통 신규 음성: `common_cta.json`. 입력 SHA·경로: `source_manifest.json`. 자동 대조 결과: `checks.json`.',
          '- 총괄 전달 이슈: `issue_DEFINITIONS_AND_LINKS.json`. 인계: `handoff.json`.',
          '- 총괄 → narration(본편90문장·CTA2문장 예산/실제 음성) → editor(세로 재배치) → 독립 QA. 본편·공통 scenes/state/decisions는 총괄 소유다.', '',
          '## 입력 SHA256', '', '| source ID | SHA256 |', '|---|---|']
lines += [f"| `{s['source_id']}` | `{s['sha256']}` |" for s in manifest['inputs']]
(OUT / 'shorts_plan.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')

write('checks.json', {'status': 'built_pending_separate_verification', 'counts': counts,
                      'price_checks': price_checks, 'rank_checks': rank_checks})
print(json.dumps({'outputs_directory': str(OUT), 'counts': counts, 'CTA_characters': cta['characters_including_spaces_and_punctuation'],
                  'shorts': [{'id': s['short_id'], 'existing_free_speech_sum_s': s['targetduration']['existing_free_voice_speech_sum_seconds_reference_only']} for s in shorts]}, ensure_ascii=False))
