"""로컬 원본과 v5를 독립 대조한다. 작가 검증 코드는 실행하지 않는다."""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path('C:/projects/realestate_reco')
EP = ROOT / 'video-agent-studio/episodes/newlywed-apartment-picks-20261101'
WRITER = EP / 'writer/top20-split-v4/longform-natural-v5-20261104'
OUT = Path(__file__).resolve().parent
READ_FILES = {}

def rel(path):
    return path.relative_to(ROOT).as_posix()

def read(path):
    value = path.read_bytes()
    READ_FILES[rel(path)] = hashlib.sha256(value).hexdigest()
    return value.decode('utf-8-sig')

def js(path):
    return json.loads(read(path))

def norm(text):
    return re.sub(r'\s+', '', text)

def numbers(text):
    return re.findall(r'\d[\d,]*(?:\.\d+)?', text)

def pointer(value, pointer_text):
    for key in pointer_text.strip('/').split('/'):
        key = key.replace('~1', '/').replace('~0', '~')
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value

def subset(expected, actual):
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(k in actual and subset(v, actual[k]) for k, v in expected.items())
    if isinstance(expected, list):
        return isinstance(actual, list) and len(expected) == len(actual) and all(subset(a, b) for a, b in zip(expected, actual))
    return expected == actual

manifest = js(EP / 'narration/top20-split-v4/jun-and-shorts-v1/narration_manifest.json')
baseline = [s for s in manifest['sentences'] if s['kind'] == 'accepted_main']
reader_path = ROOT / manifest['main_reader_script']
reader = read(reader_path)
mapping = js(WRITER / 'sentence_mapping.json')
patch_packet = js(WRITER / 'sentence_patches.json')
phonetics = js(WRITER / 'phonetics.json')
script = read(WRITER / 'script_v5.md')
writer_handoff = js(WRITER / 'handoff.json')
freeze = js(WRITER / 'freeze_manifest.json')
language = js(ROOT / 'config/video_language.json')
timing = js(EP / 'narration/top20-split-v4/jun-and-shorts-v1/timing_proposals.json')
source_scenes = js(EP / 'writer/top20-split-v4/scene_proposals_v2.json')
ranking = js(ROOT / 'analysis/newlywed_region_2024/rankings.json')
legend = js(EP / 'research/top20-split-v4/prices/legend.json')

old = {s['sentence_id']: s for s in baseline}
new = {s['sentence_id']: s for s in mapping['sentences']}
patches = {s['sentence_id']: s for s in patch_packet['patches']}
ids = [s['sentence_id'] for s in baseline]
new_ids = [s['sentence_id'] for s in mapping['sentences']]
script_pairs = [(sid, text.rstrip('\r')) for sid, text in re.findall(r'<!--\s*([\w-]+)\s*-->\s*\n([^\n]+)', script)]
checks = []

def check(name, passed, details=None):
    checks.append({'check': name, 'passed': bool(passed), 'details': details})

check('원본_90ID_순서_유지', len(ids) == len(new_ids) == 90 and ids == new_ids and len(set(new_ids)) == 90)
check('원본_reader_해시', READ_FILES[rel(reader_path)] == manifest['main_reader_script_sha256'])
reader_offsets = [reader.find(s['text']) for s in baseline]
check('원본90문장_reader_내용과순서', all(i >= 0 for i in reader_offsets) and reader_offsets == sorted(reader_offsets))
check('v5_MD와_mapping_90문장_일치', script_pairs == [(s['sentence_id'], s['text']) for s in mapping['sentences']])
actual_changed = [sid for sid in ids if old[sid]['text'] != new[sid]['text'] or old[sid]['reading_text'] != new[sid]['reading_text']]
check('patch_count_실제변경집합', len(patch_packet['patches']) == len(patches) == patch_packet['patch_count'] and set(actual_changed) == set(patches))
patch_failures = []
for sid, p in patches.items():
    expected = (old[sid]['text'], old[sid]['reading_text'], new[sid]['text'], new[sid]['reading_text'])
    actual = (p['old_text'], p['old_reading_text'], p['new_text'], p['new_reading_text'])
    if expected != actual or p['oldID'] != sid or p['new_sentence_id'] != sid:
        patch_failures.append(sid)
check('patches_전후와_원본_mapping_일치', not patch_failures, patch_failures)

numeric_changes = [{'sentence_id': sid, 'old': numbers(old[sid]['text']), 'new': numbers(new[sid]['text'])}
                   for sid in ids if numbers(old[sid]['text']) != numbers(new[sid]['text'])]
check('기존_전체숫자_유지_유일한추가2024', numeric_changes == [{'sentence_id': 'P01-INTRO-V3-04', 'old': [], 'new': ['2024']}], numeric_changes)
numeric_span_checks = []
span_overrides = {'P01-R11-V2-04': [('상계2차중앙하이츠', '상계 이차 중앙 하이츠')]}
for s in timing['sentences']:
    sid = s['sentence_id']
    if sid not in new:
        continue
    for sp in s.get('protected_numeric_spans', []):
        display, reading = sp['display_text'], sp['reading_text']
        for replacement_display, replacement_reading in span_overrides.get(sid, []):
            if display == replacement_display:
                reading = replacement_reading
        # 목적격/관형격 조사 변경(예: 2호선을 → 2호선의)은 값 변경과 구분한다.
        display_core = re.sub(r'(?:을|를|의)$', '', display)
        reading_core = re.sub(r'(?:을|를|의)$', '', reading)
        numeric_span_checks.append({'sentence_id': sid, 'display': display, 'reading': reading,
                                    'comparison_policy': '공백 및 끝의 을/를/의 조사만 제외; 숫자·단위는 유지',
                                    'display_preserved': norm(display_core) in norm(new[sid]['text']),
                                    'reading_preserved': norm(reading_core) in norm(new[sid]['reading_text'])})
check('보호숫자span_표시문_읽기문유지', all(s['display_preserved'] and s['reading_preserved'] for s in numeric_span_checks), numeric_span_checks)

rank_rows = []
for rank in range(20, 10, -1):
    sid = f'P01-R{rank:02d}-V2-01'
    row = next(x for x in ranking['capital_gu_ranking'] if x['rank'] == rank)
    expected = f"{rank}위는 {row['province']} {row['region']}, {row['newlywed_couples']:,}쌍입니다."
    rank_rows.append({'sentence_id': sid, 'expected': expected, 'actual': new[sid]['text'], 'passed': expected == new[sid]['text']})
check('순위10곳_지역_거주수_원천랭킹대조', all(x['passed'] for x in rank_rows), rank_rows)

price_checks = []
source_cache = {}
for key, claim in source_scenes['claim_registry'].items():
    match = re.fullmatch(r'W4V2-R(\d+)-PRICE-SELECTED', key)
    if not match or not 11 <= int(match.group(1)) <= 20:
        continue
    for field in claim['source_fields']:
        path = ROOT / field['path']
        if path not in source_cache:
            source_cache[path] = js(path)
        actual = pointer(source_cache[path], field['field'])
        price_checks.append({'claim_id': key, 'path': rel(path), 'pointer': field['field'],
                             'expected': field.get('value'), 'actual': actual,
                             'passed': subset(field.get('value'), actual)})
check('가격10지역_참조수치_표본_분모_현물대조', len({x['claim_id'] for x in price_checks}) == 10 and all(x['passed'] for x in price_checks), price_checks)
check('가격기준문2개_완전보존', all(old[sid]['text'] == new[sid]['text'] and old[sid]['reading_text'] == new[sid]['reading_text'] for sid in ['P01-CRITERIA-01', 'P01-CRITERIA-02']))
check('원본기간_면적_조회일', legend['period'] == ['2026-05-01', '2026-10-31'] and legend['area_m2'] == [83, 85] and legend['retrieved_date'] == '2026-11-03')

entities = ['미리내마을(롯데2)', '계남초등학교', '계남중학교', '신중동역', '서울의료원', '청남공원', '신내역', '경춘선', '서울면남초등학교', '용마중학교', '용마산(용마폭포공원)역', 'GTX-A', '수인분당선', '구성역', '용인기흥효성해링턴플레이스', '청곡초등학교', '상갈역', '연수2동', '송도 센트럴파크', 'e편한세상송도', '인천송담초등학교', '인천미송중학교', '송도달빛축제공원역', '논현 웰카운티', '논현 파크 포레', '소래습지생태공원', '인천논곡초등학교', '인천금융고등학교', '신도림로', '경인로', '신도림역', 'G밸리', '금천구 가산동', '현대연예인', '서울구일초등학교', '구일중학교', '구일고등학교', '상림마을', '우물골', '진관동 주민센터', '녹번역센트레빌', '영락중학교', '서울녹번초등학교', '녹번역', '수원종합버스터미널', 'Y CITY(와이시티)', '수원중촌초등학교', '상촌초등학교', '칠보중학교', '원천호수', '신대호수', '광교호수공원', '망포마을쌍용1차', '태장초등학교', '잠원중학교', '망포역', '경춘선숲길', '상계2차중앙하이츠', '상계중학교', '서울상계초등학교', '노원역']
entity_checks = [{'sentence_id': sid, 'entity': ent, 'preserved': norm(ent) in norm(new[sid]['text'])}
                 for sid in ids for ent in entities if norm(ent) in norm(old[sid]['text'])]
check('보호지명_학교_단지_교통명_문장별유지', all(x['preserved'] for x in entity_checks), entity_checks)

references = []
for s in mapping['sentences']:
    reference = s['evidence_reference']
    path = ROOT / reference['path']
    if path not in source_cache:
        source_cache[path] = js(path)
    original = pointer(source_cache[path], reference['json_pointer']) if reference.get('json_pointer') else None
    references.append({'sentence_id': s['sentence_id'], 'path': rel(path),
                       'passed': (original is None or (original['sentence_id'] == s['sentence_id'] and original['text'] == old[s['sentence_id']]['text'] and original.get('claim_ids', []) == reference.get('claim_ids', []) and original.get('source_fields', []) == reference.get('source_fields', [])))})
check('90문장_참조경로와본문_원본claimIDs_유지', all(x['passed'] for x in references), references)

inputs = []
for item in patch_packet['input_revisions']:
    path = ROOT / item['path']
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    inputs.append({'path': item['path'], 'expected': item['sha256'], 'actual': digest, 'passed': digest == item['sha256']})
check('작가선언입력9개_현재해시대조', all(x['passed'] for x in inputs), inputs)
outputs = []
for name, expected_hash in freeze['artifact_hashes'].items():
    path = WRITER / name
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    outputs.append({'path': rel(path), 'expected': expected_hash, 'actual': digest, 'passed': digest == expected_hash})
check('작가freeze_manifest_출력현재해시대조', all(x['passed'] for x in outputs), outputs)

short_impacts = {}
for file in ['short01_promo.json', 'short02_ranks20_16.json', 'short03_ranks15_11.json']:
    short = js(EP / 'writer/top20-split-v4/jun-and-shorts-v1' / file)
    seq = [s['sentence_id'] for s in short['sequence']]
    affected = [sid for sid in seq if sid in actual_changed]
    short_impacts[file] = {'changed_sentence_ids': affected, 'changed_count': len(affected), 'new_asset_created': False}

changed_readings = [sid for sid in ids if old[sid]['reading_text'] != new[sid]['reading_text']]
changed_scene_ids = sorted({new[sid]['scene_id'] for sid in changed_readings})
protected = next(x for x in phonetics['entries'] if x['canonical_entity'] == '상계2차중앙하이츠')
check('상계_원본식별자_2차_표시문_이차읽기', protected['display_name'] == '상계2차 중앙하이츠' and protected['reading_text'] == '상계 이차 중앙 하이츠' and norm(protected['reading_text']) in norm(new['P01-R11-V2-04']['reading_text']))
check('2024거주통계_scope', ranking['metadata']['reference_date'] == '2024-11-01' and len(ranking['capital_gu_ranking']) == 53 and '2024년' in new['P01-INTRO-V3-04']['text'] and ('거주' in new['P01-INTRO-V3-04']['text'] or '살고 있는지' in new['P01-INTRO-V3-04']['text']) and '53개 구' in new['P01-INTRO-V3-05']['text'])
check('최신국소수정_도입04_브랜드간격_준공집단표현',
      '지역마다 신혼부부가 몇 쌍씩 살고 있는지 비교한 거죠' in new['P01-INTRO-V3-04']['text']
      and '데이터로 보는 부동산' in new['P01-INTRO-V3-02']['reading_text']
      and '집단' not in new['P01-R20-V2-05']['text'] and '지어진 아파트' in new['P01-R20-V2-05']['text'])
check('freeze_문자수_변경수독립대조', freeze['changed_sentence_count'] == len(changed_readings)
      and freeze['changed_reading_characters'] == sum(len(new[sid]['reading_text']) for sid in changed_readings)
      and freeze['reading_characters'] == sum(len(new[sid]['reading_text']) for sid in ids))

stability = [{'path': name, 'read_sha256': digest, 'current_sha256': hashlib.sha256((ROOT/name).read_bytes()).hexdigest()}
             for name, digest in READ_FILES.items()]
check('검수중_입력불변', all(x['read_sha256'] == x['current_sha256'] for x in stability), stability)
result = {
    'task_id': 'longform-natural-v5-20261104',
    'method': '독립 로컬 텍스트·원본·숫자·참조 현물 검사. 작가 validation 결과로 대체하지 않음.',
    'source_scope': {'ranking_metadata': ranking['metadata'], 'price_method': source_scenes['price_and_map_contract'], 'current_reader': rel(reader_path)},
    'counts': {'main': len(ids), 'changed': len(actual_changed), 'unchanged': len(ids)-len(actual_changed),
               'reading_changed': len(changed_readings), 'changed_reading_chars_including_spaces': sum(len(new[sid]['reading_text']) for sid in changed_readings),
               'changed_reading_chars_no_whitespace': sum(len(norm(new[sid]['reading_text'])) for sid in changed_readings),
               'numeric_spans': len(numeric_span_checks), 'entity_checks': len(entity_checks), 'price_source_fields': len(price_checks)},
    'changed_sentence_ids': actual_changed, 'affected_scene_ids': changed_scene_ids,
    'linked_shorts_impact_against_original_sequences': short_impacts,
    'audio_expectation': '채택 시 바뀐 읽기문만 새 음성 필요. 기존 음성과 동일하다고 간주할 수 없음. 비용·생성 승인이 아님.',
    'old_sanggye_reading': old['P01-R11-V2-04']['reading_text'],
    'new_sanggye_reading': new['P01-R11-V2-04']['reading_text'],
    'latest_targeted_texts': {sid: {'text': new[sid]['text'], 'reading_text': new[sid]['reading_text']} for sid in ['P01-INTRO-V3-02','P01-INTRO-V3-04','P01-R20-V2-05']},
    'checks': checks, 'input_sha256': READ_FILES,
    'coverage': {'script_text': '90/90', 'patches': f'{len(patches)}/{len(patches)}',
                 'actual_listening': 'unchecked', 'continuous_playback': 'unchecked',
                 'actual_mp4_sampled_frames': 'unchecked', 'media_stream_decode': 'unchecked',
                 'new_audio_render': 'not_created', 'external_claude': 'not_used'},
}
result['passed'] = all(x['passed'] for x in checks)
(OUT / 'script_audit_checks.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'passed': result['passed'], 'counts': result['counts'],
                  'failed_checks': [{'check': x['check'], 'details': x['details']} for x in checks if not x['passed']],
                  'latest_targeted_texts': result['latest_targeted_texts'],
                  'affected_scene_ids': changed_scene_ids, 'short_impacts': short_impacts,
                  'checked_script_sha256': READ_FILES[rel(WRITER/'script_v5.md')]}, ensure_ascii=False))
