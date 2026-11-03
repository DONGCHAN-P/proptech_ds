"""독립 입력 QA. 로컬 파일만 읽고 이 QA 폴더에 증거를 쓴다."""
from pathlib import Path
from collections import Counter
from decimal import Decimal
import ast
import hashlib
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

OWN = Path(__file__).resolve().parent
EP = OWN.parents[1]
ROOT = EP.parents[2]
N = EP / 'narration/jun-user-script-v1'
D = EP / 'director/user-recording-v1'
sha = lambda b: hashlib.sha256(b).hexdigest()
norm = lambda s: re.sub(r'\s+', '', s)
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
checks = []
def check(name, passed, detail=None):
    checks.append({'check': name, 'result': 'pass' if passed else 'fail', 'evidence': detail})

doc = next((D / 'source').glob('*.docx'))
source = read(D / 'source_extracted.json')
plan = read(D / 'scene_plan.json')
m = read(N / 'narration_manifest.json')
g = read(N / 'generation_input.json')
b = read(N / 'budget_proposal.json')
c = read(N / 'caption_plan.json')
raw = read(N / 'generator_raw_manifest.json')
ready = read(N / 'generation_readiness.json')
account = read(N / 'account_readonly.json')
cfg_path = ROOT / 'config/tts.json'
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
with zipfile.ZipFile(doc) as z:
    xml = ET.fromstring(z.read('word/document.xml'))
    doc_paragraphs = [{'id': f'P{i:03}', 'text': ''.join(t.text or '' for t in p.findall('.//w:t', ns))}
                      for i, p in enumerate(xml.findall('w:body/w:p', ns), 1)]
check('preserved_DOCX_SHA', sha(doc.read_bytes()) == source['sha256'] == m['source_doc_sha256'] == 'f28deb75e0a271e30e3d29dbe52291ef30e28b0ef0bfc2648ad98bbd652e6a73')
check('independent_DOCX_XML_vs_extracted_100_body_paragraphs', doc_paragraphs == source['paragraphs'], len(doc_paragraphs))
by_id = {p['id']: p['text'] for p in doc_paragraphs}
expected = [(pid, s['scene_id'], s['chapter']) for s in plan['scenes'] for pid in s['paragraph_ids']]
check('48_original_paragraphs_31_scenes_exact_order', len(expected) == 48 and len(plan['scenes']) == 31 and expected == [(p['paragraph_id'], p['scene_id'], p['chapter']) for p in m['paragraphs']])
check('scene_plan_hash', sha((D / 'scene_plan.json').read_bytes()) == m['scene_plan_sha256'])

digits = {'영': 0, '일': 1, '이': 2, '삼': 3, '사': 4, '오': 5, '육': 6, '칠': 7, '팔': 8, '구': 9}
def parse_korean_number(s):
    if '점' in s:
        a, d = s.split('점')
        return Decimal(str(parse_korean_number(a)) + '.' + ''.join(str(digits[x]) for x in d))
    total, pending = 0, None
    for ch in s:
        if ch in digits:
            pending = digits[ch]
        else:
            total += (1 if pending is None else pending) * {'십': 10, '백': 100, '천': 1000}[ch]
            pending = None
    return total + (pending or 0)

transforms, text_errors = [], []
for p in m['paragraphs']:
    pid = p['paragraph_id']
    if p['text'] != by_id[pid]: text_errors.append([pid, 'source_text'])
    cursor = 0
    for part in p['display_mapping']:
        original, spoken = part['original'], part['spoken']
        if p['text'][cursor:cursor + len(original)] != original: text_errors.append([pid, 'mapping_original'])
        if part['kind'] == 'literal':
            if original != spoken: text_errors.append([pid, 'literal_changed'])
        else:
            if part.get('source_start') != cursor or part.get('source_end') != cursor + len(original): text_errors.append([pid, 'mapping_offsets'])
            valid = spoken == {'LTV': '엘티브이', 'DSR': '디에스알'}.get(original) if original in ('LTV', 'DSR') else Decimal(original.replace(',', '')) == parse_korean_number(spoken)
            transforms.append({'paragraph_id': pid, 'original': original, 'spoken': spoken, 'value_preserved': valid})
            if not valid: text_errors.append([pid, 'value_changed', original, spoken])
        cursor += len(original)
    if ''.join(x['original'] for x in p['display_mapping']) != p['text'] or ''.join(x['spoken'] for x in p['display_mapping']) != p['spoken_text']: text_errors.append([pid, 'mapping_join'])
    if len(p['text']) != p['characters'] or len(p['spoken_text']) != p['spoken_characters'] or sha(p['text'].encode()) != p['text_sha256'] or sha(p['spoken_text'].encode()) != p['spoken_sha256']: text_errors.append([pid, 'counts_or_hash'])
check('all_original_wording_mapping_values_units_and_order', not text_errors, {'errors': text_errors, 'transform_count': len(transforms), 'kinds': dict(Counter(x['original'] if x['original'] in ('LTV', 'DSR') else 'number' for x in transforms))})
for name, field in [('narration_body.txt', 'text'), ('spoken_body.txt', 'spoken_text')]:
    expected_text = '\n\n'.join(p[field] for p in m['paragraphs']) + '\n'
    check(name + '_paragraph_join', (N / name).read_text('utf-8') == expected_text,
          {'normalized_codepoints': len(expected_text), 'raw_bytes': len((N / name).read_bytes()), 'sha256': sha((N / name).read_bytes())})

chapters = []
for chapter, request in zip(m['chapters'], g['paragraphs']):
    selected = [p for p in m['paragraphs'] if p['chapter'] == chapter['chapter']]
    text = '\n\n'.join(p['spoken_text'] for p in selected)
    data = (ROOT / chapter['path']).read_bytes()
    passed = (data == text.encode() and request['proposed_spoken_text'] == chapter['text'] == text and
              chapter['paragraph_ids'] == request['source_paragraph_ids'] == [p['paragraph_id'] for p in selected] and
              sha(data) == sha(text.encode()) == chapter['sha256'] == request['proposed_spoken_text_sha256'] and
              len(text) == chapter['characters'] == request['characters'])
    chapters.append({'chapter_id': chapter['chapter_id'], 'characters': len(text), 'sha256': sha(data), 'request_sha256': sha(text.encode()), 'CRLF_count': data.count(b'\r\n'), 'pass': passed})
check('7_LF_inputs_byte_identical_to_exact_request_text', len(chapters) == 7 and all(x['pass'] for x in chapters), chapters)
original = sum(len(p['text']) for p in m['paragraphs'])
spoken = sum(len(p['spoken_text']) for p in m['paragraphs'])
billed = sum(x['characters'] for x in chapters)
check('original_vs_reading_and_billed_count', original == 5701 == m['input_characters'] == b['input_characters_original'] and spoken == 5715 == m['spoken_characters'] == b['input_characters_spoken_without_separators'] and billed == 5797 == m['billed_input_characters'] == b['input_characters_to_send'], {'original': original, 'reading': spoken, 'reading_delta': spoken-original, 'chapter_internal_separators': billed-spoken, 'billed': billed, 'chapter_characters': [x['characters'] for x in chapters]})
check('budget_7000_cash0_no_approval_no_retry', b['chapter_requests'] == 7 and b['estimated_first_pass_credits'] == 5797 and b['included_credit_cap_proposed'] == 7000 and b['revision_headroom_credits'] == 1203 and b['additional_cash_cap_krw'] == 0 and b['generation_authorized'] is False and b['top_up_authorized'] is False and b['automatic_retries'] == 0)
check('snapshot_arithmetic_only_not_live_query', b['account_snapshot_sha256'] == sha((N/'account_readonly.json').read_bytes()) and b['included_remaining'] == account['subscription']['character_limit']-account['subscription']['character_count'] == 18981 and b['cap_fits_included'] is True and b['credits_per_character_estimate'] == account['model']['model_rates']['character_cost_multiplier'] * account['model']['model_rates']['cost_discount_multiplier'] * account['voice']['sharing']['rate'] == 1,
      {'snapshot_utc': account['checked_at_utc'], 'new_authenticated_queries': 0})
mh, gh = sha((N/'narration_manifest.json').read_bytes()), sha((N/'generation_input.json').read_bytes())
code = (N/'generate.mjs').read_text('utf-8')
check('dependent_SHA_bindings', mh == raw['source_manifest_sha256'] == b['manifest_sha256'] == c['source_manifest_sha256'] == ready['source_manifest_sha256'] and gh == ready['generation_input_sha256'] and gh in code and ready['generator_sha256'] == sha((N/'generate.mjs').read_bytes()) and raw['inputs']['tts_config']['sha256'] == sha(cfg_path.read_bytes()) and g['raw_manifest']['sha256'] == sha((N/'generator_raw_manifest.json').read_bytes()))

caption_errors, amount_errors, boundaries_checked, protected_spans = [], [], 0, 0
amount = re.compile(r'\d[\d,]*(?:\.\d+)?(?:[억천백십만](?:\d[\d,]*(?:\.\d+)?)?)*(?:원|퍼센트|제곱미터|개월|년|주택)?')
for p in m['paragraphs']:
    qs = [q for q in c['cues'] if q['paragraph_id'] == p['paragraph_id']]
    if norm(''.join(q['text'] for q in qs)) != norm(p['text']): caption_errors.append([p['paragraph_id'], 'coverage'])
    last, normalized_cursor = 0, 0
    spans = [(a.start(), a.end(), a.group()) for a in amount.finditer(norm(p['text']))]
    protected_spans += len(spans)
    for q in qs:
        a, z = q['source_start'], q['source_end']
        if a < last or p['text'][last:a].strip() or p['text'][a:z] != q['text'] or (q['scene_id'],q['chapter']) != (p['scene_id'],p['chapter']): caption_errors.append([q['cue_id'], 'offsets_or_scope'])
        if norm(''.join(q['display_lines'])) != norm(q['text']) or not 1 <= len(q['display_lines']) <= 2: caption_errors.append([q['cue_id'], 'display'])
        if q['start_s'] is not None or q['end_s'] is not None: caption_errors.append([q['cue_id'], 'invented_timing'])
        for line in q['display_lines']:
            normalized_cursor += len(norm(line)); boundaries_checked += 1
            for start, end, token in spans:
                if start < normalized_cursor < end: amount_errors.append({'cue_id':q['cue_id'],'protected':token,'boundary':normalized_cursor})
        last = z
    if p['text'][last:].strip(): caption_errors.append([p['paragraph_id'],'tail'])
check('156_cues_complete_order_original_and_no_invented_timing', len(c['cues']) == len({q['cue_id'] for q in c['cues']}) == c['cue_count'] == 156 and not caption_errors and [q['paragraph_id'] for q in c['cues']] == sorted([q['paragraph_id'] for q in c['cues']], key=lambda x:[p['paragraph_id'] for p in m['paragraphs']].index(x)), caption_errors)
check('complete_amounts_units_percent_area_duration_across_cues_and_lines', not amount_errors, {'protected_spans':protected_spans,'line_or_cue_boundaries_checked':boundaries_checked,'errors':amount_errors,'P033Q03': next(q['display_lines'] for q in c['cues'] if q['cue_id']=='P033Q03')})
check('caption_1_2_lines_max31_characters', max(len(line) for q in c['cues'] for line in q['display_lines']) == c['max_line_characters'] == 31)
for p in [EP/'director/jun-user-script-v1/stage_generator.py',EP/'director/jun-user-script-v1/prepare.py',N/'verify_input_contract.py',N/'prepare_captions.py']:
    ast.parse(p.read_text('utf-8-sig'))
check('Python_AST_parse_without_execution', True)
auth = EP/'director/jun-user-script-v1/authorization.json'
check('no_current_authorization_file', not auth.exists())
files = [doc,D/'source_extracted.json',D/'scene_plan.json',D/'episode_preflight.json',cfg_path,
         EP/'director/jun-user-script-v1/prepare.py',EP/'director/jun-user-script-v1/stage_generator.py'] + [N/n for n in ['narration_manifest.json','generation_input.json','budget_proposal.json','caption_plan.json','generator_raw_manifest.json','generation_readiness.json','generate.mjs','narration_body.txt','spoken_body.txt','prepare_captions.py','verify_input_contract.py','account_readonly.json']] + [ROOT/x['path'] for x in m['chapters']] + [ROOT/'video-agent-studio/episodes/regional-price-recovery-20261022/narration/production-v1/common.mjs']
report = {'checked_at_utc':datetime.now(timezone.utc).isoformat(),'scope':'독립 원문/XML·숫자 역변환·바이트/해시·자막 텍스트 QA. 생성기/TTS/인증 요청 미실행.','checks':checks,'transformation_ledger':transforms,'checked_file_hashes':[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in files], 'failed_checks':[x['check'] for x in checks if x['result']=='fail']}
(OWN/'input_evidence.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'checks':len(checks),'failed_checks':report['failed_checks'],'transforms':len(transforms),'protected_spans':protected_spans,'caption_boundaries':boundaries_checked,'chapter_characters':[x['characters'] for x in chapters]},ensure_ascii=False))
