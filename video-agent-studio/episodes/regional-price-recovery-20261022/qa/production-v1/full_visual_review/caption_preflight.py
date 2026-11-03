"""Offline caption/source preflight only; no rendering, raw data, or synthesis."""
import hashlib
import json
import math
import re
from collections import Counter
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

QA = Path(__file__).resolve().parent
EP = QA.parents[2]
ROOT = EP.parents[2]
OUT = EP / 'outputs/production-v1-jun'
inputs = {}
checks = Counter()
failures = []

def read(p):
    return json.loads(Path(p).read_text('utf-8-sig'))

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def rel(p):
    return Path(p).resolve().relative_to(ROOT).as_posix()

def track(p):
    inputs[rel(p)] = {'sha256': sha(p), 'bytes': Path(p).stat().st_size}

def check(kind, ok, detail):
    checks[kind] += 1
    if not ok:
        failures.append({'check': kind, **detail})

def compact(text):
    return re.sub(r'\s+', '', text)

mapping_path = OUT / 'checks/visual-review/caption_display_mapping.json'
captions_path = OUT / 'checks/visual-review/captions.json'
html_path = OUT / 'project/visual-review.html'
mapping, display = read(mapping_path), read(captions_path)
timing = read(OUT / 'project/timing_resolved.json')
scenes = read(EP / 'outputs/script-review-v3/scenes_v3.json')['scenes']
approved = {b['beat_id']: b['narration_text'] for s in scenes for b in s['beats']}
manifest = read(EP / 'narration/production-v1/manifest.json')
original_proof = read(QA.parent / 'input_verification.json')
prep = read(OUT / 'checks/visual-review/prepare_receipt.json')
decision_path = ROOT / 'output/video_decisions/decisions/5fe307eed02c.json'
decision = read(decision_path)

# A finite list audited against approved wording; do not import producer normalization code.
allowed = {
    '칠 년 구 개월': '7년 9개월', '오 년 삼 개월': '5년 3개월',
    '이천육 년': '2006년', '이천이십육 년': '2026년', '이분기': '2분기',
    '육백육십사만 건': '664만건', '일분기': '1분기',
    '지수를 백으로': '지수를 100으로', '기준값 백에서': '기준값 100에서',
    '오백삼십삼': '533', '이백삼': '203', '출발선 백과': '출발선 100과',
    '다섯 배': '5배', '두 배': '2배', '이십 년': '20년',
    '거리는 영입니다': '거리는 0입니다', '십 퍼센트': '10%',
    '이천이십일 년': '2021년', '이천이십이 년': '2022년',
    '이천팔 년': '2008년', '이천십 년': '2010년', '삼분기': '3분기',
    '십일 퍼센트': '11%', '이천구 년': '2009년', '네 분기': '4분기',
    '일 년': '1년', '이천십오 년': '2015년', '이천십사 년': '2014년',
    '육 년': '6년', '이천십육 년': '2016년', '이천십칠 년': '2017년',
    '이천이십 년': '2020년', '삼 년': '3년', '팔 퍼센트': '8%',
    '이천십팔 년': '2018년', '두 해 구 개월': '2년 9개월',
    '이천이십오 년': '2025년', '십일 년': '11년', '오 년': '5년', '십 년': '10년',
    '일 퍼센트': '1%', '삼 점 사 퍼센트': '3.4%', '오 점 구 퍼센트': '5.9%',
    '두 건': '2건', '세 건': '3건', '다섯 건': '5건',
    '이천이십삼 년': '2023년', '삼만 천육백 호': '31,600호',
    '이천이십사 년': '2024년', '이만 구천사백 호': '29,400호',
}
check('approved_script_sha', sha(EP / 'outputs/script-review-v3/script_v3.md') == mapping['script_sha256'] ==
      '99b40e8730ee0f8fdf74402cffbe04b5b418540344e6d2a7175e6a01c3054664', {})
check('39_ordered_originals', list(approved) == [x['beat_id'] for x in mapping['paragraphs']] ==
      [x['beat_id'] for x in manifest['paragraphs']] == [x['beat_id'] for x in timing['beats']] and len(approved) == 39, {})
check('113_display_cues', len(display['captions']) == 113, {})
check('provisional_only', mapping['timing_locked'] is False and display['timing_locked'] is False and
      timing['timing_locked'] is False and display['body_offset'] == 5, {})

paragraph_results = []
# Number + unit, full year/quarter and year/month expressions must stay in one cue.
atoms = re.compile(r'\d{4}년(?:\s*[1-4]분기)?|\d+년(?:\s*\d+개월)?|(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:만건|개월|분기|건|호|배|%)?')
for row, narration, beat in zip(mapping['paragraphs'], manifest['paragraphs'], timing['beats']):
    bid = row['beat_id']
    check('original_exact_preservation', row['approved_original'] == approved[bid] == narration['text'], {'beat_id': bid})
    pos, parts = 0, []
    for n in row['normalizations']:
        start, end = n['source_start'], n['source_end']
        check('normalization_spans', pos <= start < end <= len(row['approved_original']) and
              row['approved_original'][start:end] == n['source'], {'beat_id': bid, 'span': [start,end]})
        check('audited_numeric_meaning', allowed.get(n['source']) == n['display'], {'beat_id': bid, 'source': n['source'], 'display': n['display']})
        parts += [row['approved_original'][pos:start], n['display']]
        pos = end
    parts.append(row['approved_original'][pos:])
    check('only_declared_changes', ''.join(parts) == row['display_paragraph'], {'beat_id': bid})
    cues = [c for c in display['captions'] if c['beat_id'] == bid]
    check('paragraph_lossless_cue_join', compact(''.join(c['text'] for c in cues)) == compact(row['display_paragraph']), {'beat_id': bid})
    check('unchanged_paragraph_windows', bool(cues) and math.isclose(cues[0]['start'], beat['start'], abs_tol=1e-8) and
          math.isclose(cues[-1]['end'], beat['end'], abs_tol=1e-8), {'beat_id': bid})
    boundaries, offset = [], 0
    for cue in cues[:-1]:
        offset += len(compact(cue['text']))
        boundaries.append(offset)
    text = compact(row['display_paragraph'])
    protected = [{'text': m.group(), 'start': m.start(), 'end': m.end()} for m in atoms.finditer(text)]
    splits = [a for a in protected if any(a['start'] < x < a['end'] for x in boundaries)]
    check('number_unit_date_not_split', not splits, {'beat_id': bid, 'splits': splits})
    paragraph_results.append({'beat_id': bid, 'source_preserved': row['approved_original'] == approved[bid],
                              'normalizations': len(row['normalizations']), 'display_cues': len(cues),
                              'protected_atoms': protected, 'body_start': beat['start'], 'body_end': beat['end']})

class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.elements = []; self.caption = None; self.captions = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs); self.elements.append((tag,a))
        if tag == 'div' and a.get('id','').startswith('vr-cap-'):
            self.caption = {'attrs': a, 'text': ''}
    def handle_data(self, text):
        if self.caption is not None: self.caption['text'] += text
    def handle_endtag(self, tag):
        if tag == 'div' and self.caption is not None:
            self.captions.append(self.caption); self.caption = None

html = html_path.read_text('utf-8-sig')
page = Page(); page.feed(html)
check('html_cue_count', len(page.captions) == len(display['captions']) == 113, {})
for encoded, cue in zip(page.captions, display['captions']):
    a = encoded['attrs']
    check('html_cue_exact_binding', encoded['text'].replace('\u00a0',' ') == cue['text'] and a['id'].startswith('vr-cap-' + cue['beat_id'] + '-') and
          math.isclose(float(a['data-start']), cue['start'], abs_tol=1e-6) and
          math.isclose(float(a['data-duration']), cue['end']-cue['start'], abs_tol=1e-6), {'beat_id': cue['beat_id']})
    compound = re.findall(r'\d{4}년\s+[1-4]분기|\d+년\s+\d+개월', encoded['text'])
    check('html_compound_dates_no_wrap', all(' ' not in x and '\u00a0' in x for x in compound), {'beat_id': cue['beat_id']})
check('number_units_keep_all_css', 'word-break:keep-all;overflow-wrap:normal' in html, {})
for i, cue in enumerate(display['captions']):
    check('cue_times_global_offset', cue['start'] < cue['end'] and
          math.isclose(cue['global_start'], cue['start']+5, abs_tol=1e-8) and
          math.isclose(cue['global_end'], cue['end']+5, abs_tol=1e-8), {'beat_id': cue['beat_id'], 'cue': i})
    if i:
        check('cue_contiguity', math.isclose(cue['start'], display['captions'][i-1]['end'], abs_tol=1e-8), {'cue': i})
root = next(a for _,a in page.elements if a.get('id') == 'root')
check('visual_entry_separate_and_no_voice', root['data-composition-id'] == 'visual-review' and
      not any(tag in ('audio','video') for tag,_ in page.elements) and '음성 없는 전체 검토본 · 임시 타이밍' in html, {})
check('provisional_last_caption_hold', math.isclose(float(root['data-duration']), display['last_caption_end_body']+3, abs_tol=1e-6)
      and math.isclose(prep['outro_start'] - display['last_caption_end_global'], 3, abs_tol=1e-8)
      and prep['actual_last_spoken_end'] is None, {})
for p in [OUT / 'project/index.html', OUT / 'project/timing_resolved.json', EP / 'narration/production-v1/manifest.json']:
    check('actual_Jun_inputs_unchanged', sha(p) == original_proof['inputs'][rel(p)]['sha256'], {'path': rel(p)})
check('actual_entry_snapshot', sha(OUT / 'project/index.html') == prep['protected_original_actual_Jun_entry_sha256'], {})
check('voice_deferred_authorization_absent', decision['status'] == 'revision_requested' and decision['resolution'] == 'deferred_by_user'
      and not (EP / 'narration/production-v1/authorization.json').exists(), {})
supply = next(p for p in mapping['paragraphs'] if p['beat_id'] == 'S011-P2')
supply_text = ''.join(c['text'] for c in display['captions'] if c['beat_id'] == 'S011-P2')
check('approved_supply_rounding_preserved', all(x in supply_text for x in ['2023년','31,600호','2024년','29,400호']) and
      all(x not in supply_text for x in ['31,630','29,441','31630','29441']) and
      '삼만 천육백 호' in supply['approved_original'] and '이만 구천사백 호' in supply['approved_original'], {'beat_id':'S011-P2'})

for p in [mapping_path,captions_path,html_path,OUT/'checks/visual-review/prepare_receipt.json',
          OUT/'checks/visual-review/caption_bounds.json',OUT/'project/timing_resolved.json',OUT/'project/index.html',
          EP/'outputs/script-review-v3/scenes_v3.json',EP/'outputs/script-review-v3/script_v3.md',
          EP/'narration/production-v1/manifest.json',decision_path,EP/'brief.json',EP/'state.json',
          ROOT/'tools/check_regional_full_visual_review_v1.py',QA.parent/'input_verification.json',Path(__file__)]: track(p)
report = {'task_id':'RPR-FULLVISUAL-CAPTION-PREFLIGHT','checked_at_utc':datetime.now(timezone.utc).isoformat(),
          'status':'pass_authored_caption_preflight' if not failures else 'required_fix_open',
          'scope':'승인 원문/숫자 표시/113큐/HTML/Jun입력SHA/음성보류 문맥만. MP4·프레임·소리 검사 없음.',
          'check_counts':dict(checks),'failures':failures,'paragraphs':paragraph_results,'input_sha256':inputs,
          'approved_originals':39,'display_cues':113,'audited_normalization_occurrences':sum(len(p['normalizations']) for p in mapping['paragraphs']),
          'html_whitespace_policy':'JSON의 일반 공백을 HTML에서 NBSP로 바꾸는 경우만 동등 취급. 날짜/년월25개 내부 NBSP와 keep-all CSS 확인. 문자·숫자 변경은 허용하지 않음.',
          'approved_supply':{'2023':'31,600호','2024':'29,400호','policy':'승인 원문 반올림값 보존.31630/29441로 대체하지 않음.'},
          'authorization_context':{'source':rel(decision_path),'sha256':sha(decision_path),'status':decision['status'],
                                   'resolution':decision['resolution'],'authorization_present':False,'paid_actions':0},
          'coverage':{'authored_text':'checked','actual_Jun_entry':'SHA unchanged','provisional_hold':'last caption +3s; actual speech 없음',
                      'producer_caption_bounds':'113큐 영수증 존재; 새 브라우저 측정/인코딩 프레임 확인은 하지 않음',
                      'actual_mp4':'unchecked_wait_parent_technical_report','encoded_frames':'unchecked',
                      'continuous_playback':'unchecked','actual_listening':'unchecked','mobile_playback':'unchecked',
                      'raw_csv_recompute':False,'new_render':False,'new_paid_calls':0,'network_calls':0},
          'next_role':'director:부모 technical report와 실제 MP4 준비 알림 후 신규 인코딩 QA 별도. 현재 텍스트 검증을 본편 품질 통과로 확대하지 않음.'}
(QA/'caption_preflight.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'checks':sum(checks.values()),'failures':failures,'input_count':len(inputs)},ensure_ascii=False))
