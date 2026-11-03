"""v1 불변 산출물을 계승하고 SC01~04 변경만 v2로 연결한다."""
import copy
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

W = Path(__file__).resolve().parent
EP = W.parent
ROOT = EP.parents[2]
FROZEN = '9658fc12dc76f67bb75d00e9c88170b167933ad8482dae1b752e4009d2aaf1a3'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def save(name, value):
    (W / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def rel(p):
    return p.relative_to(ROOT).as_posix()

preservation = read(W / 'v1_preservation_v2.json')
for name, digest in preservation['files'].items():
    assert sha(W / name) == digest, f'v1 보존 해시 불일치: {name}'
assert sha(W / 'script_v2.md') == FROZEN

old_scene_pack = read(W / 'scene_proposals_v1.json')
old_claim_map = read(W / 'claim_map_v1.json')
old_numeric = read(W / 'protected_numeric_v1.json')
old_pron = read(W / 'pronunciation_notes_v1.json')
review = read(EP / 'qa/content_v1_review.json')
facts = read(EP / 'research/facts_v2.json')
addendum = read(EP / 'research/newborn_policy_addendum_v2.json')
packet = read(EP / 'research/verified_case_packet.json')
fact_by_id = {x['claim_id']: x for x in facts['facts']}
case_by_id = {x['case_id']: x for x in packet['cases']}
reset = addendum['case']

script = (W / 'script_v2.md').read_text(encoding='utf-8')
body = script.split('---', 2)[2].strip()
paragraphs = []
chapters = []
for n, chunk in enumerate(re.split(r'(?m)^## ', body)[1:], 1):
    heading, text = chunk.split('\n', 1)
    ps = text.strip().split('\n\n')
    chapters.append(heading)
    paragraphs.extend((n, p) for p in ps)

digits = '영일이삼사오육칠팔구'
def sino(n):
    n = int(n)
    if n == 0:
        return '영'
    if n >= 10000:
        hi, lo = divmod(n, 10000)
        return sino(hi) + '만' + (sino(lo) if lo else '')
    out = ''
    for power, suffix in [(1000, '천'), (100, '백'), (10, '십'), (1, '')]:
        q, n = divmod(n, power)
        if q:
            out += ('' if q == 1 and power > 1 else digits[q]) + suffix
    return out

def number(s):
    s = s.replace(',', '')
    if '.' in s:
        a, b = s.split('.')
        return sino(a) + '점' + ''.join(digits[int(c)] for c in b)
    return sino(s)

pron_re = re.compile(r'\d{4}년\s*\d{1,2}월\s*\d{1,2}일|LTV|DSR|DTI|(?<![A-Za-z])[AB](?![A-Za-z])|\d[\d,]*(?:\.\d+)?(?:%포인트|%|㎡)?')
def speaking(text):
    transforms, parts, last, offset = [], [], 0, 0
    for m in pron_re.finditer(text):
        a = m.group()
        if re.fullmatch(r'\d{4}년\s*\d{1,2}월\s*\d{1,2}일', a):
            year, month, day = map(int, re.findall(r'\d+', a))
            mo = '시월' if month == 10 else '유월' if month == 6 else sino(month) + '월'
            b = sino(year) + '년 ' + mo + ' ' + sino(day) + '일'
        elif a in {'LTV', 'DSR', 'DTI', 'A', 'B'}:
            b = {'LTV': '엘티브이', 'DSR': '디에스알', 'DTI': '디티아이', 'A': '에이', 'B': '비'}[a]
        else:
            nm = re.match(r'\d[\d,]*(?:\.\d+)?', a).group()
            b = number(nm) + {'%포인트': ' 퍼센트 포인트', '%': ' 퍼센트', '㎡': ' 제곱미터', '': ''}[a[len(nm):]]
        prefix = text[last:m.start()]
        parts.append(prefix)
        offset += len(prefix)
        transforms.append({'display_start': m.start(), 'display_end': m.end(), 'display': a, 'spoken_start': offset, 'spoken_end': offset + len(b), 'spoken': b, 'reason': '숫자·단위·약어 발음층 분리'})
        parts.append(b)
        offset += len(b)
        last = m.end()
    parts.append(text[last:])
    return ''.join(parts), transforms

numeric_re = re.compile(r'만\s*\d+\s*세\s*미만|\d{4}년\s*\d{1,2}월\s*\d{1,2}일|\d[\d,]*(?:\.\d+)?억(?:\s*\d[\d,]*(?:\.\d+)?(?:천)?만)?\s*원|\d[\d,]*(?:\.\d+)?(?:천)?만\s*원|\d[\d,]*(?:\.\d+)?(?:%포인트|%|㎡|개월|년|원|억|회|세)')

scene_pack = copy.deepcopy(old_scene_pack)
base_scenes = copy.deepcopy(old_scene_pack['scenes'])
new_scene = copy.deepcopy(next(s for s in base_scenes if s['scene_id'] == 'S034'))
new_scene.update({
    'scene_id': 'S034R', 'chapter_entry_id': None,
    'message': 'B의60회 상환 후 잔액·남은300개월에 재산정한 월액과 예산 비교',
    'claim_ids': ['N05A'], 'case_ids': ['B_newborn_P600000000_C0'],
    'additional_case_ids': [reset['case_id']],
    'story_finding_ids': ['I09', 'I07'], 'material_type': 'data_chart', 'supporting_material_types': [],
    'visual_purpose': '설명', 'graphic_id': 'newborn_remaining_balance_reset_300',
    'asset_ids': ['G_S034R_newborn_remaining_balance_reset_300'],
    'asset_status': '네이티브 도표 제작 예정',
    'visual_direction': '처음60회 상환→잔액346,755,901원→남은300개월·연3.65%→월1,763,962원(약176.4만)의 시간축을 발화 순서대로 강조. 초기 월162.6만과 재산정 월176.4만을 각 구간에 붙인다. B 주거·저축 월300/소유30/저축100/상환목표170의 예산 막대를 함께 제시. 추가출산·우대·자산초과가산·중도상환0의 기본사례 조건 행. A의 최초원금·새360개월 금리 비교 도표와 다른 구도.',
    'model_source': 'research/newborn_policy_addendum_v2.json#/case',
    'fallback': '잔액·상환기간·재산정 월액의 동일 수치와 시간축을 편집 가능한 SVG로 제작',
})
ordered = base_scenes[:34] + [new_scene] + base_scenes[34:]
assert len(ordered) == len(paragraphs) == 45

updates = {
    'S001': {
        'visual_direction': 'HB01 오른쪽 열쇠·폴더 배경 위 작은 산술 오버레이: 현금2억5천+총액상한6억=8억5천. 첫6억 표시 옆에 수도권·규제지역·시가15억이하 주택구입 범위를 읽히게 고정. 담보→소득→비용→월예산 필터를 순차 강조',
    },
    'S003': {'visual_direction': '현금·심사·생활 예산의 범위 막대와 교집합. 총액6억은 수도권·규제지역·시가15억이하 구입 사례임을 조건 행에 연결하고 기준일2026-10-26을 출처 영역에 표시'},
    'S009': {'message': '담보에서 반영할 임차인 보호 공제의 뜻', 'visual_direction': '담보 배분에서 선순위 권리를 분리하고, 보증으로 보완되지 않고 남은 공제액5500만원을 한 층으로 표시. 비용 영수증과 별도인 대출상한 차감 관계'},
    'S010': {'visual_direction': '실행은행 취급확인→가입심사→공제보완0/보완되지 않고 남은공제5500 두 가지. 기존임차인0·선순위0. 보증 승인을 통과한 조건을 실행액 옆에 표시'},
    'S020': {'visual_direction': '감면 전 취득세 본표 옆 생초최대200/출산최대500의 대안 가지. 출산 감면은 출산일2028-12-31까지·취득은 출산전1년~출산후5년·12억이하·1가구1주택(취득후3개월내 포함)·자녀와 거주 및 추징 요건을 해당 가지에 읽히게 표시. 생초는 본인/배우자 소유이력 등 별도 요건. 동시적격 큰 감면 하나, 감면후교육세 포함 순납부세액은 별도 확인'},
    'S022': {'visual_direction': '보증 승인 등 공제0의 한도42000만과 보증으로 보완되지 않고 남은공제5500 반영 한도36500만 비교. 필요39074만 고정선과 추가현금2574만을 별도 열로 표시'},
    'S025': {'visual_direction': '위6/9/12억의 상품·세금 축과 아래 수도권·규제지역 일반구입 총액 축 분리. 시가15억이하6억·15초과25이하4억·25초과2억. 앞 세 집은 모두 시가15억이하 구간임을 연결'},
    'S032': {'claim_ids': ['N01', 'N02'], 'visual_direction': 'NB01 신생아 장 도입 배경. 네이티브 자격창: 접수전2년내 출산·입양/2023-01-01이후 출생/입양아 접수일현재 만2세미만. 외벌이1.3억·맞벌이합산2억 AND 부부각자1.3억, 순자산51100만을 동시에 표시; 특별공급·우선공급 나이예외는 해당 기본사례 밖 exact_conditions에 보존'},
    'S033': {'visual_direction': 'NB01을 내려 네이티브 자금 도표로 전환. 가격9억·서울면적85·DTI60·상품4억. B6억 주택 보증 승인 공제0에서 필요39074만이 한도 안; 보완되지 않은5500 공제 입력은 한도36500만의 별도 조건 비교로만 표시'},
    'S034': {
        'claim_ids': ['N03', 'N05A'], 'additional_case_ids': [reset['case_id']],
        'message': '초기5년 기본금리와 접수일 기준 가산 산식',
        'graphic_id': 'newborn_initial_5y_and_application_formula',
        'asset_ids': ['G_S034_newborn_initial_5y_and_application_formula'],
        'visual_direction': '30년 중 처음5년 구간에 초기2.9%·월162.6만 고정. 신규 합산소득8500만이하인 B: 접수일 기준 [생초신혼디딤돌 최저기본금리−신생아 최저특례금리]를 B 특례금리에 가산하는 네이티브 도식. KB2026-10-19표 적용 예시에서 가산0.75%포인트·기본금리2.9→3.65를 다음 구간에 연결. 추가출산·우대·자산초과가산·중도상환0 조건 표시',
        'model_source': 'research/newborn_policy_addendum_v2.json#/case',
    },
    'S035': {
        'claim_ids': ['N03', 'M01'],
        'message': '9억 사례는 공제 입력과 상품4억 중 작은 한도 적용',
        'visual_direction': '현재9억 사례의 입력 공제5500만원을 표시. 9억×70%−5500만=담보57500만과 상품40000만을 비교해 작은40000만 선택. 필요현금56615만(비용3615만·예비3000만 포함) 연결. 주택가격6억초과의 보증 불가를 보편 규정으로 표시하지 않음',
    },
    'S040': {'visual_direction': '각 가격별 동일 최초원금·새360개월에서4→6% 비교: 월227→285/170→213, 저축43→15부족/100→57 순차 강조. A의 금리 민감도이며 B의60회 상환후잔액·남은300개월과 별도 계산으로 명시'},
}

changed_body = []
pron_scenes, numeric_occurrences, claim_rows = [], [], []
v1_scene_by_id = {s['scene_id']: s for s in old_scene_pack['scenes']}
for s, (chapter, p) in zip(ordered, paragraphs):
    sid = s['scene_id']
    assert s['chapter'] == chapter
    if sid in updates:
        s.update(updates[sid])
    if sid not in v1_scene_by_id or v1_scene_by_id[sid]['display_text'] != p:
        changed_body.append(sid)
    spoken, transforms = speaking(p)
    units = [u for u in re.split(r'(?<=[.?!])\s+|(?<=,)\s+', p) if u]
    protected = []
    for m in numeric_re.finditer(p):
        numeric_occurrences.append({'scene_id': sid, 'display_start': m.start(), 'display_end': m.end(), 'display': m.group(), 'protect_across_cues_and_lines': True})
        protected.append(m.group())
    s.update({
        'display_text': p, 'narration_text': spoken, 'spoken_text': spoken,
        'script_revision': 'v2', 'audio_revision': None, 'start': None, 'end': None,
        'timing_basis': 'estimate', 'estimated_duration_seconds': round(len(p)/5.67, 2),
        'protected_numeric': protected, 'emphasis_order': protected[:10],
        'caption_candidates': [{'unit_id': f'{sid}_U{n:02d}', 'display_text': u, 'start': None, 'end': None, 'timing_basis': 'unassigned'} for n, u in enumerate(units, 1)],
        'source_evidence': [{'claim_id': cid, 'basis_date': fact_by_id[cid].get('basis_date', '2026-10-26'), 'source_ids': fact_by_id[cid]['source_ids'], 'evidence_locations': fact_by_id[cid].get('evidence_locations', [{'source_id': 'DIRECTOR_CURRENT_KB', 'location': 'research/newborn_policy_addendum_v2.json:2026-10-19표 A1 산식'}])} for cid in s['claim_ids']],
        'status': 'proposal_v2_SC01_SC04_pending_dual_content_review',
    })
    if sid in ['S034', 'S034R']:
        s['additional_case_source'] = 'research/newborn_policy_addendum_v2.json#/case'
    pron_scenes.append({'scene_id': sid, 'display_text': p, 'spoken_text': spoken, 'transforms': transforms})
    claim_rows.append({'scene_id': sid, 'chapter': chapter, 'claim_ids': s['claim_ids'], 'case_ids': s['case_ids'], 'additional_case_ids': s.get('additional_case_ids', []), 'story_finding_ids': s['story_finding_ids'], 'condition_set_id': s['condition_set_id'], 'basis': 'facts_v2 우선·기존 사례와 신규 접수일 기준 산식'})

common = {'episode_id': old_scene_pack['episode_id'], 'script_revision': 'v2', 'frozen_script_sha256': FROZEN, 'policy_as_of': '2026-10-26'}
input_paths = [
    EP / 'brief.json', EP / 'state.json', EP / 'qa/content_v1_review.json',
    EP / 'research/facts_v2.json', EP / 'research/newborn_policy_addendum_v2.json',
    EP / 'research/verified_case_packet.json',
    EP / 'research/prepared-v1/next_episode_story_findings.json',
    EP / 'research/prepared-v1/next_episode_editorial_plan.json',
    EP / 'research/prepared-v1/next_policy_independent_qa/findings.json',
    EP / 'visual/assets.json', W / 'script_v1.md', W / 'scene_proposals_v1.json',
    W / 'claim_map_v1.json', W / 'protected_numeric_v1.json', W / 'pronunciation_notes_v1.json',
]
input_revisions = {rel(p): {'sha256': sha(p)} for p in input_paths}
input_revisions['v1_instruction_hashes_reused'] = {k:v for k,v in old_scene_pack['input_revisions'].items() if '/guides/' in k or k.endswith('WORKFLOW.md') or k.endswith('video_writer.toml') or k.endswith('video_call_policy.json')}

scene_pack.update(common)
scene_pack.update({'status': 'v2_writer_revision_frozen_pending_Claude_and_Codex_review', 'scenes': ordered, 'scene_count_body': 45, 'input_revisions': input_revisions, 'changed_body_scene_ids': changed_body, 'new_scene_ids': ['S034R']})
count = sum(len(p) for _,p in paragraphs)
seconds = round(count/5.67, 2)
scene_pack['timing'].update({'display_characters_narration': count, 'visible_characters_with_headings_and_linebreaks': len(body), 'estimated_narration_seconds': seconds, 'estimated_narration_plus_chapters_minutes': round((seconds+30)/60, 2), 'measured': False, 'audio_created': False})
scene_pack['condition_sets']['A_BANK']['C55'] = '서울 사례에서 보증으로 보완되지 않고 남은 공제액5500만원을 적용한 입력. 실제 공제는 상품별 확인'
b = scene_pack['condition_sets']['B_POLICY']
b.update({
    'adoption_child_age_at_application': '만2세미만 기본조건; 특공/우선공급 나이예외는 별도',
    'newborn_income_rule': {'single_income_combined_max_krw': 130000000, 'dual_combined_max_krw': 200000000, 'each_partner_dual_income_max_krw': 130000000, 'source': 'facts_v2 N01 현행 NHUF'},
    'newborn_rate': '신규 합산소득8천·30년·초기기본2.9%·5년; 접수일 기준 가산산식, 현행2026-10-19표 가산0.75%포인트 적용 예시3.65%',
    'reset_case': reset,
    'reset_preferences': {'additional_births': 0, 'rate_preferences': 0, 'asset_excess_surcharge': 0, 'prepayment': 0},
    'monthly_budget_if_compared': {'housing_plus_savings_krw': 3000000, 'ownership_plan_krw': 300000, 'saving_target_krw': 1000000, 'mortgage_target_krw': 1700000},
})
b['guarantee_rules']['newborn_9eok'] = '공제액5500만원을 넣은9억 사례의 입력. 70%×9억−5500만=57500만과 상품40000만 중 작은40000만. 보증범위의 전면 단정 없음'
scene_pack['condition_sets']['TRANSACTION']['child_relief_conditions'] = {'birth_deadline': '2028-12-31', 'purchase_window': '출산전1년~출산후5년', 'other_conditions': fact_by_id['T05']['exact_conditions'], 'overlap': '각 적격요건 확인 후 큰 감면 하나', 'net_after_relief_education_tax': None}
save('scene_proposals_v2.json', scene_pack)

used_claims = sorted({cid for s in ordered for cid in s['claim_ids']})
used_cases = sorted({cid for s in ordered for cid in s['case_ids']})
claim_map = copy.deepcopy(old_claim_map)
claim_map.update(common)
claim_map.update({
    'evidence_scope': 'facts_v2가 동일claim을 대체. SC01~04와 신생아 현행 근거를 반영한 연결; 기존157산술·10논리 및 신규4개 산술검증은 총괄 증거를 재사용하며 writer가 재실행한 것으로 기록하지 않음',
    'input_revisions': input_revisions, 'scene_map': claim_rows,
    'used_facts_with_exact_conditions': [fact_by_id[c] for c in used_claims],
    'used_case_ids': used_cases, 'additional_case_ids': [reset['case_id']],
    'case_basis': '기존18조건부사례 중 사용분의 숫자 유지. B60회후잔액/300개월 재산정은 신규addendum의 별도 조건부 예시',
    'story_findings_coverage': {f'I{i:02d}': [s['scene_id'] for s in ordered if f'I{i:02d}' in s['story_finding_ids']] for i in range(1, 11)},
    'superseded_story_language': {'I09': '기존 이후금리 미확정 문구를 N05A의 접수일 기준 산식과 현행표 B예시로 구체화. I08 A의 최초원금/새360개월 비교는 그대로 유지', 'M08': '9억 장면의 현행 보증범위 전면 단정 근거로 미사용'},
    'new_primary_source_provenance': {'path': 'research/newborn_policy_addendum_v2.json', 'primary_urls': addendum['primary_urls'], 'cached_source_hashes': {s['source_id']: s['sha256'] for s in addendum['sources']}, 'writer_scope': '총괄이 오늘 취득한 로컬 근거를 읽음. writer 자체 웹 취득 아님'},
})
claim_map['additional_derivations']['newborn_reset_current_application_schedule'] = reset
claim_map['additional_derivations']['reset_independent_verification_inherited'] = addendum['verification']
save('claim_map_v2.json', claim_map)

numeric = copy.deepcopy(old_numeric)
numeric.update(common)
numeric.update({'protected_occurrences': numeric_occurrences, 'newborn_reset_case_exact': reset, 'reset_inherited_independent_checks': addendum['verification'], 'existing_case_numeric_status': 'v1의 기존 수치 필드 원값 유지'})
for pair in numeric['critical_pairs']:
    if 'S001' in pair['scenes']:
        pair['keep'] = '수도권·규제지역 시가15억이하 구입 총액상한6억. 현금2억5천+상한6억=산술8억5천, 담보·소득·비용·월예산 추가 필터'
    if 'S034' in pair['scenes']:
        pair['keep'] = 'B초기기본2.9%·5년·월162.6만. 신규합산8500만이하 접수일 기준 가산산식, 현행2026-10-19표0.75%포인트로 이후기본3.65%'
numeric['critical_pairs'] += [
    {'scenes': ['S032'], 'keep': '맞벌이합산2억 이하 AND 부부각자1.3억 이하. 입양아 접수일현재 만2세미만'},
    {'scenes': ['S034R'], 'keep': '최초390740000원·2.9%·360개월에서60회상환→잔액346755901.403311원→3.65%·남은300개월→월1763962.030097원(약176.4만원), 추가출산/우대/자산초과가산/중도상환0'},
    {'scenes': ['S034R'], 'keep': 'B 주거·저축 월300만원·소유30·저축100·상환목표170: 초기162.6/재산정176.4를 비교. A 동일최초원금·새360개월 금리민감도와 별도'},
    {'scenes': ['S035'], 'keep': '9억 사례 공제5500만원 입력:70%×9억−5500만=57500만>상품40000만; 최종40000만. 필요현금56615만·추가31615만 불변'},
    {'scenes': ['S020'], 'keep': '2028-12-31은 출산일 마감. 취득은 출산전1년~출산후5년 등 적격요건. 생초200·출산500 미합산, 감면후교육세 포함 순액 미산출'},
]
save('protected_numeric_v2.json', numeric)

pron = copy.deepcopy(old_pron)
pron.update(common)
pron.update({'scenes': pron_scenes, 'owner_next': 'narration — v2 고정SHA의 독립 내용검토·승인 후 사용', 'status': 'v2 미합성·미청취 발음 제안'})
pron['pronunciation_dictionary'] += [
    {'display': '0.75%포인트', 'spoken': '영점칠오 퍼센트 포인트', 'meaning': '가산금리 차이. 0.75퍼센트 인상으로 바꾸지 않음'},
    {'display': '3.65%', 'spoken': '삼점육오 퍼센트'},
    {'display': '176.4만 원', 'spoken': '백칠십육점사만 원'},
    {'display': '60회 / 300개월', 'spoken': '육십회 / 삼백개월', 'meaning': '상환 횟수와 남은 기간을 각각 읽음'},
    {'display': '만 2세 미만', 'spoken': '만 이세 미만'},
]
pron['emphasis_notes'] = [e for e in pron['emphasis_notes'] if e['scenes'] != ['S034']]
pron['emphasis_notes'] += [
    {'scenes': ['S001', 'S025'], 'words': ['수도권·규제지역', '15억 원 이하']},
    {'scenes': ['S032'], 'words': ['접수일 현재', '만 2세 미만', '부부 각자']},
    {'scenes': ['S034'], 'words': ['처음 5년', '대출접수일 기준', '0.75%포인트']},
    {'scenes': ['S034R'], 'words': ['60회 상환 뒤 잔액', '남은 300개월', '176.4만 원', 'B도 월 300만 원']},
]
save('pronunciation_notes_v2.json', pron)

changes = {
    **common, 'base_script': 'writer/script_v1.md', 'base_script_sha256': preservation['files']['script_v1.md'],
    'review_input': 'qa/content_v1_review.json', 'status': '수정 반영·새SHA 독립 내용검토 대기',
    'changed_body_scene_ids': changed_body,
    'changed_visual_or_condition_scene_ids': list(updates) + ['S034R'],
    'new_scene_ids': ['S034R'], 'retained_scene_ids': [s['scene_id'] for s in base_scenes],
    'items': [
        {'issue_id': 'SC01', 'scene_ids': ['S001', 'S003', 'S025'], 'change': '총액6억을 수도권·규제지역·시가15억이하 구입 범위로 첫소개부터 명시', 'claim_ids': ['L04'], 'status': 'implemented_pending_review'},
        {'issue_id': 'SC02', 'scene_ids': ['S032'], 'change': '맞벌이합산2억과 각자1.3억·입양아 접수일현재 만2세미만 반영', 'claim_ids': ['N01'], 'status': 'implemented_pending_review'},
        {'issue_id': 'SC03', 'scene_ids': ['S034', 'S034R'], 'change': 'B 소득구간 접수일 기준 가산산식·현행표2.9→3.65·60회후잔액/남은300개월의 월176.4만을 추가. 우대/추가출산/자산초과가산/중도상환0, B월300·목표170 조건 명시', 'claim_ids': ['N05A'], 'case_id': reset['case_id'], 'status': 'implemented_pending_review'},
        {'issue_id': 'SC04', 'scene_ids': ['S035'], 'change': '6억초과 보증범위 단정을 삭제하고9억×70%−공제5500=57500만과 상품40000만 비교로 한도 설명. 기존 현금56615만 유지', 'claim_ids': ['N03', 'M01'], 'M08_current_generalization_removed': True, 'status': 'implemented_pending_review'},
        {'issue_id': 'STYLE-C55', 'scene_ids': ['S009', 'S010', 'S022', 'S033'], 'change': '보증으로 보완되지 않고 남은 공제액이라는 쉬운 표현', 'status': 'implemented_pending_review'},
        {'issue_id': 'RELIEF-BIRTH-WINDOW', 'scene_ids': ['S020'], 'change': '2028년말 출산 마감과 출산전1년~후5년 취득범위 설명, 상세조건 화면 제안. 감면미합산·순교육세미산출 유지', 'claim_ids': ['T04', 'T05'], 'status': 'implemented_pending_review'},
    ],
    'unchanged': ['10장 표제와 순서·서술문단 형식', '기존6/9/12억 사례·거래비용·예비자금·정책상품한도', 'A소득·DSR·LTV·가격역산·동일최초원금/새360개월 금리민감도', 'HB01 도입/썸네일·NB01 신생아장 전용', '기존 v1 전체 파일'],
    'v1_preservation_manifest': 'writer/v1_preservation_v2.json',
}
save('changes.json', changes)

checks = []
def check(name, result, evidence):
    checks.append({'check': name, 'result': 'pass' if result else 'fail', 'evidence': evidence})

scene_by_id = {s['scene_id']: s for s in ordered}
check('v1 기존파일 불변', all(sha(W/name)==digest for name,digest in preservation['files'].items()), preservation)
check('v2 고정SHA', sha(W/'script_v2.md') == FROZEN, FROZEN)
check('10개 표제·순서 유지', chapters == [c['title'] for c in old_scene_pack['chapter_entries']], chapters)
check('메타데이터v2·서술문단', '\nversion: v2\n' in script and not re.search(r'(?m)^(?:[-*] |\d+\) |\[|### )', body), '45개 서술문단')
check('표시문자수6800이내', count <= 6800 and len(body) <= 6800, {'narration':count,'visible':len(body)})
check('도입20~30초 estimate', 20 <= ordered[0]['estimated_duration_seconds'] <= 30, ordered[0]['estimated_duration_seconds'])
check('문단·장면 표시문 일치', [p for _,p in paragraphs] == [s['display_text'] for s in ordered], len(ordered))
check('의미후보 재조합', all(' '.join(u['display_text'] for u in s['caption_candidates']) == s['display_text'] for s in ordered), '문장/절 의미 경계·타이밍 미지정')
check('보호숫자 큐 경계 불분할', all(any(o['display'] in u['display_text'] for u in scene_by_id[o['scene_id']]['caption_candidates']) for o in numeric_occurrences), len(numeric_occurrences))
check('claim·기존case 연결 유효', all(c in fact_by_id for c in used_claims) and all(c in case_by_id for c in used_cases), {'current_facts_count':len(facts['facts']), 'used_claims':len(used_claims)})
check('SC01 첫총액·CH6 지역가격 범위', all('수도권·규제지역' in scene_by_id[sid]['display_text'] and '15억 원 이하' in scene_by_id[sid]['display_text'] for sid in ['S001','S025']), ['S001','S025'])
check('SC02 각자소득·입양나이', '부부 각자 1억 3천만 원 이하' in scene_by_id['S032']['display_text'] and '접수일 현재 만 2세 미만' in scene_by_id['S032']['display_text'], fact_by_id['N01'])
check('SC03 접수일·가산폭·기본재산정', all(t in scene_by_id['S034']['display_text'] for t in ['대출접수일 기준','8,500만 원 이하','0.75%포인트','3.65%']), fact_by_id['N05A'])
check('SC03 잔액·남은기간·B예산', all(t in scene_by_id['S034R']['display_text'] for t in ['60회 상환 뒤 잔액','남은 300개월','176.4만 원','B도 월 300만 원','170만 원']), reset)
check('SC04 공제입력/제약비교·M08일반화 제거', 'M08' not in scene_by_id['S035']['claim_ids'] and '6억 원 초과 주택은' not in body and all(t in scene_by_id['S035']['display_text'] for t in ['공제액 5,500만 원','70%','5억 7,500만 원','상품 한도 4억 원']), '기존9억 사례의 한도/현금 유지')
check('감면 출산일·취득범위 보존', all(t in scene_by_id['S020']['display_text'] for t in ['2028년 말까지 출산','출산 전 1년','출산 후 5년','큰 감면 하나']), 'T04/T05 상세조건 scene_proposals_v2')
check('기존 사례 수치 전부 유지', numeric['case_numbers_exact'] == old_numeric['case_numbers_exact'] and numeric['affordability_exact'] == old_numeric['affordability_exact'], '기존 산술 재실행 대신 원값·필드 대조')
check('신규 재산정 숫자 원문 일치', numeric['newborn_reset_case_exact'] == addendum['case'] and all(addendum['verification'].values()), '총괄 독립4검증 인계값 재사용; writer 재실행 아님')
check('A민감도와B재산정 기간 구별', '새로 360개월' in scene_by_id['S040']['display_text'] and '남은 300개월' in scene_by_id['S034R']['display_text'], ['S034R','S040'])
check('NB01 신생아장 전용·HB01 도입 유지', [s['scene_id'] for s in ordered if 'NB01' in s['asset_ids']] == ['S032'] and [s['scene_id'] for s in ordered if 'HB01' in s['asset_ids']] == ['S001'], '그림 미열람·manifest 기준')
check('추정 시간만 사용', all(s['start'] is None and s['end'] is None and s['timing_basis']=='estimate' for s in ordered), '음성 미생성·미청취')
check('발음변환 문자 범위', all(s['display_text'][t['display_start']:t['display_end']]==t['display'] and s['spoken_text'][t['spoken_start']:t['spoken_end']]==t['spoken'] for s in pron_scenes for t in s['transforms']), 'DSR/LTV/DTI/퍼센트포인트 및 신규숫자')
validation = {**common, 'status':'writer_change_and_structure_checks_only', 'checks':checks, 'passed':sum(c['result']=='pass' for c in checks), 'failed':sum(c['result']=='fail' for c in checks), 'content_review':'새 고정SHA에 대한 main Claude+Codex 내용검토 대기', 'not_performed':['정책 재조사','기존157·10검사 및 신규4산술 재실행','Claude/외부검토 호출','TTS·청취·영상재생·렌더·업로드']}
save('validation_v2.json', validation)
assert validation['failed'] == 0, validation

output_names = ['script_v2.md','changes.json','scene_proposals_v2.json','claim_map_v2.json','protected_numeric_v2.json','pronunciation_notes_v2.json','validation_v2.json','v1_preservation_v2.json','prepare_script_v2.py','build_writer_v2.py']
outputs = [{'path':rel(W/n),'sha256':sha(W/n),'bytes':(W/n).stat().st_size} for n in output_names]
save('handoff_v2.json', {
    'task_id':'affordable-home-price-writer-v2-SC01-SC04','role':'writer','status':'v2_frozen_pending_dual_content_review',
    'summary':f'SC01~04와쉬운공제표현·출산감면시기를 반영했습니다. 기존v1 {len(preservation["files"])}개 파일은 해시로 불변 확인. v2는10장·45본문장면, 낭독표시{count}자/표제포함{len(body)}자, 장전환 포함 약{(seconds+30)/60:.2f}분 estimate. B접수일기준 가산산식과60회후잔액/300개월 월176.4만을 추가했으며 기존사례 숫자는 유지합니다.',
    'frozen_script_sha256':FROZEN,'previous_script_sha256':preservation['files']['script_v1.md'],
    'input_revisions':input_revisions,'outputs':outputs,'affected_scene_ids':list(dict.fromkeys(changed_body+list(updates))),
    'new_scene_ids':['S034R'],
    'checks':[{'check':'writer 변경범위·구조·원값 연결','result':'pass','evidence':rel(W/'validation_v2.json')},{'check':'Claude+Codex 새SHA 내용검토','result':'pending','evidence':None}],
    'open_issue_ids':[], 'review_issue_status':{x['id']:'implemented_pending_review' for x in review['required_issues']},
    'unresolved':['v2 고정SHA의 독립 내용검토·버전 승인','이후 실제 음성·발음 청취·정렬·타임록','도표/배경 구현·자막 실제 글리프/프레임 검수','개인별 은행·보증 실행조건, 실제 기타비용과 감면후교육세 포함 세액'],
    'scope_notes':['담당writer만 작성, 공통state/scenes/decisions 및 타담당파일 수정 없음','v1의18조건부사례 패킷 수치 그대로; B재산정은 addendum 별도예시','현재접수금리표의 기본금리·추가출산/우대/자산초과가산/중도상환0','기존 산술/논리와 신규4산술검사는 인계 증거 재사용','TTS·비용·외부검토·업로드 호출 없음'],
    'next_role':'director → Claude+Codex v2 내용검토 → 승인 후 narration/visual/editor',
    'next_action':'이 frozen_script_sha256으로 검토. 추가수정은 새버전 발급; v1·v2 고정본을 덮어쓰지 않음',
    'created_at_utc':datetime.now(timezone.utc).isoformat(),
})
assert sha(W/'script_v2.md') == FROZEN
assert all(sha(W/name)==digest for name,digest in preservation['files'].items())
print(json.dumps({'frozen_script_sha256':FROZEN,'narration_display_characters':count,'visible_characters':len(body),'body_scenes':45,'new_scene':'S034R','estimate_with_chapters_minutes':round((seconds+30)/60,2),'checks_passed':validation['passed'],'checks_failed':validation['failed'],'v1_preserved_files':len(preservation['files']),'handoff':rel(W/'handoff_v2.json')},ensure_ascii=False))
