"""REQ01/REC01 narrow recheck; preserve all initial QA files."""
import ast
import hashlib
import json
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

QA = Path(__file__).resolve().parent
EP = QA.parents[1]
ROOT = EP.parents[2]
OUT = EP / 'outputs/production-v1-jun'
inputs = {}
checks = []

def read(p):
    return json.loads(Path(p).read_text('utf-8-sig'))

def rel(p):
    return Path(p).resolve().relative_to(ROOT).as_posix()

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def track(p, expected=None):
    p = Path(p)
    if not p.is_absolute():
        p = ROOT / p
    inputs[rel(p)] = {'sha256': sha(p), 'bytes': p.stat().st_size}
    if expected is not None:
        assert inputs[rel(p)]['sha256'] == expected, rel(p)
    return inputs[rel(p)]['sha256']

def check(name, ok, evidence):
    assert ok, (name, evidence)
    checks.append({'check': name, 'result': 'pass', 'evidence': evidence})

initial = read(QA / 'findings.json')
previous = read(QA / 'input_verification.json')
initial_preserved = {}
for name, expected in {
    'findings.json': 'cd4674abe0f8c9e35678b92007120528f2cd4593e2216a1e8a9acff46c70f114',
    'handoff.json': 'ada9683666ee9290c1798e4f13797f0de72e60e60793cb851b0eed3efaca2497',
    'input_verification.json': 'e11899fca5ad62341526aef92f7121f5f21251b3b4ff96a3b3881726da4ecf69',
    'issue_RPR-P1-REQ-01.json': 'd4a6800a689e7fd3ea500437668cf7e02906576d3e2aac8c66b5fd305214e97a',
}.items():
    initial_preserved[name] = track(QA / name, expected)

data_path = OUT / 'project/assets/chart_data.json'
track(data_path, initial['checked_revision']['chart_data_sha256'])
track(EP / 'visual/production-v1/chart_data.json', initial['checked_revision']['chart_data_sha256'])
track(EP / 'outputs/script-review-v3/script_v3.md', initial['checked_revision']['script_sha256'])
d = read(data_path)
tech_path = OUT / 'checks/preview_technical_v2.json'
tech = read(tech_path)
handoff_path = EP / 'editor/production-v1/handoff_fix.json'
handoff = read(handoff_path)
scope_path = OUT / 'checks/fix_req01/scope_and_units.json'
scope = read(scope_path)
bounds_path = OUT / 'checks/fix_req01/text_bounds.json'
bounds = read(bounds_path)
for p in [tech_path, handoff_path, scope_path, bounds_path,
          OUT / 'checks/fix_req01/technical.json', OUT / 'checks/fix_req01/visual_review_v3.json',
          OUT / 'checks/fix_req01/incheon_v3_ffprobe.json', OUT / 'checks/selected_previews.json']:
    track(p)

selected = read(OUT / 'checks/selected_previews.json')['selected_previews']
check('selected_paths_and_shas', [(x['path'], x['sha256']) for x in selected] ==
      [(x['path'], x['sha256']) for x in tech['clips']] ==
      [(x['path'], x['sha256']) for x in handoff['selected_previews']], 'selected_previews / handoff_fix / preview_technical_v2')
for item in tech['clips'] + tech['frames'] + [tech['combined_preview']]:
    track(item['path'], item['sha256'])
    if 'bytes' in item:
        check('actual_file_size', (ROOT / item['path']).stat().st_size == item['bytes'], item['path'])
track(tech['contact_sheet'])
expected_incheon = '1d03c38d53853a2a97ce22c4b03c6a81a753c5971fc1842cb0d3d045cdb699f0'
check('exact_incheon_v3', tech['clips'][1]['sha256'] == expected_incheon, expected_incheon)
for clip in tech['clips']:
    check('technical_receipt_same_media', clip['duration'] == 8 and clip['resolution'] == [1920, 1080]
          and clip['fps'] == '30/1' and clip['audio_streams'] == 0 and clip['full_decode'] == 'pass', clip['clip'])

class BeatText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.records = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.stack.append((tag, a))
    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                self.stack = self.stack[:i]
                break
    def handle_data(self, text):
        if self.stack and self.stack[-1][0] == 'text':
            beat = next((a['id'] for _, a in self.stack if 'rpr-beat' in a.get('class', '')), None)
            self.records.append((beat, text, self.stack[-1][1]))

expected_beats = [x for x in previous['authored_coverage'] if x['chart_units'] == ['', '']]
unit_results = []
for s in sorted(set(x['scene_id'] for x in expected_beats)):
    p = OUT / f'project/compositions/{s}.html'
    track(p)
    text = p.read_text('utf-8-sig')
    jobs = json.JSONDecoder().raw_decode(text.split('const jobs=', 1)[1])[0]
    parsed = BeatText()
    parsed.feed(text)
    for old in [x for x in expected_beats if x['scene_id'] == s]:
        job = next(x for x in jobs if x['id'] == old['chart_ids'][0])
        nodes = [a for bid, value, a in parsed.records if bid == old['beat_id'] and value == '2006Q1=100']
        check('12_authored_units', job['unit'] == '2006Q1=100' and len(nodes) == 1, old['beat_id'])
        unit_results.append({'beat_id': old['beat_id'], 'unit': job['unit'], 'node': nodes[0], 'html_sha256': sha(p),
                             'actual_encoded_recheck': old['beat_id'] == 'S007-P2'})
check('exact_affected_set', len(unit_results) == 12 and {x['beat_id'] for x in unit_results} ==
      {x['beat_id'] for x in handoff['affected_beat_ids']}, '12 shared episode-chart beats')

build_path = EP / 'editor/production-v1/build.py'
track(build_path)
tree = ast.parse(build_path.read_text('utf-8-sig'))
fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'episode_chart')
assignment = next(n for n in fn.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'unit' for t in n.targets))
unit_expression = compile(ast.Expression(assignment.value), '<supported start unit only>', 'eval')
dynamic = []
for region, rows in d['series'].items():
    # Evaluate only the audited pure unit expression, never import/run the builder.
    actual = eval(unit_expression, {'__builtins__': {}}, {'d': d, 'r': region})
    expected = rows[0]['quarter'] + '=100'
    check('dynamic_supported_start', actual == expected, region + ':' + expected)
    dynamic.append({'region': region, 'supported_start': rows[0]['quarter'], 'unit': actual})
check('glyph_bound_receipt', bounds['ok'] and len(bounds['checks']) == 39 and not bounds['console_errors']
      and all(not x.get('outside') and not x.get('unit_overlaps') for x in bounds['checks']),
      '제작자 실제 SVG getBBox 영수증39건 열람; 이번 QA가 브라우저 측정을 재실행한 것은 아님')

for clip in [tech['clips'][0], tech['clips'][2]]:
    track(clip['path'], previous['inputs'][clip['path']]['sha256'])
track(OUT / 'previews/지역별회복_모션시안_v1_무음.mp4', initial['checked_revision']['combined_mp4_sha256'])
for p, expected in scope['preserved_original_mp4_and_qa_hashes'].items():
    track(p, expected)
for p in [EP / 'brief.json', EP / 'state.json', EP / 'outputs/production-v1-budget/budget_decision.json']:
    track(p)
budget_path = ROOT / 'output/video_decisions/decisions/5fe307eed02c.json'
track(budget_path)
budget = read(budget_path)
for frame in tech['frames']:
    if frame['clip'] == 'incheon2008-2016recovery':
        alias = OUT / f'checks/fix_req01/encoded/incheon_v3_{frame["at_seconds"]}s.png'
        track(alias, frame['sha256'])
track(OUT / 'project/preview/incheon2008-2016recovery.html')
track(Path(__file__))

revision = {'production_revision': 'production-v1-jun / selected Incheon v3 / combined v2',
            'script_sha256': initial['checked_revision']['script_sha256'],
            'chart_data_sha256': sha(data_path), 'incheon_v3_sha256': expected_incheon,
            'combined_v2_sha256': tech['combined_preview']['sha256'],
            'preview_technical_v2_sha256': sha(tech_path), 'handoff_fix_sha256': sha(handoff_path)}
shared_evidence = {'new_encoded_pngs': [x for x in tech['frames'] if x['clip'] == 'incheon2008-2016recovery'],
                   'unit_html_checks': unit_results, 'dynamic_start_checks': dynamic,
                   'bounds_receipt': rel(bounds_path), 'bounds_receipt_sha256': sha(bounds_path)}
issues = []
for old in initial['findings']:
    item = {k: old[k] for k in ['issue_id', 'scene_id', 'severity', '문제', '수정안', 'owner']}
    item['timecode'] = {'combined_v2_sample_seconds': [10, 12, 15] if old['scene_id'] == 'S007' else [2, 4, 7],
                        'clip_sample_seconds': [2, 4, 7], 'timing_basis': 'provisional_not_Jun'}
    item['checked_revision'] = revision
    if old['issue_id'] == 'RPR-P1-REQ-01':
        item.update(status='closed_verified', evidence=shared_evidence,
                    closure='인천 v3 실제2/4/7초 원해상도PNG에 자체지수·2006Q1=100 확인. 공유12비트 HTML 단위 존재,7지역 동적 시작값과39건 경계 영수증 확인. 나머지11비트의 최종 MP4 화질 통과를 뜻하지 않음.')
    elif old['issue_id'] == 'RPR-P1-REC-01':
        item.update(status='closed_verified', evidence={'frames': shared_evidence['new_encoded_pngs'],
                    'observed': '고점2008Q3·관측저점2013Q1·최초복귀2016Q2 라벨을 plot y265보다 위의 별도 레인에서 모두 선명하게 확인. 곡선 겹침·잘림·부분글리프 누락 없음.'})
    else:
        item.update(status='open_advisory', evidence={'actual_sheet_viewed': tech['contact_sheet'],
                    'unchanged_clip_sha256': tech['clips'][0]['sha256'],
                    'authored_clarification': 'S004-P2는6패널+28px 서울/대구 종점수치 강조.1~2패널 확대가 아님. editor 정정을 source geometry와 대조.',
                    'actual_mobile_playback': 'unchecked'},
                    disposition='모바일 작은 눈금 권장사항 유지. 확대 구현/모바일 검증 완료로 완화하거나 닫지 않음.')
    issues.append(item)

report = {'task_id': 'RPR-PROD1-PREVIEW-QA-RECHECK-V3', 'checked_at_utc': datetime.now(timezone.utc).isoformat(),
          'status': 'pass_narrow_recheck_with_mobile_advisory',
          'counts': {'critical_open': 0, 'required_open': 0, 'recommended_open': 1, 'closed_verified_this_recheck': 2},
          'checked_revision': revision, 'initial_report_preserved': initial_preserved,
          'scope': 'REQ01/REC01 수정부·공유12비트 단위·선택3클립 SHA 및 새9프레임 접촉시트만. 원CSV 재검산/새 렌더/음성/API/외부 전송 없음.',
          'findings': issues, 'checks': checks, 'current_input_sha256': inputs,
          'coverage': {'new_full_resolution_pngs_viewed': [x['path'] for x in tech['frames'] if x['clip'] == 'incheon2008-2016recovery'],
                       'nine_frame_contact_sheet_viewed': tech['contact_sheet'], 'combined_v2_sample_seconds': [2,4,7,10,12,15,18,20,23],
                       'unchanged_two_clips': 'SHA 일치로 기존 QA 재사용. 새 접촉시트에서 전후 대표 장면과 자막/출처 레이어를 표본 확인.',
                       'text_bounds': '공유12비트는 HTML독립검사+제작자39건 getBBox영수증 검토. 미인코딩11비트 실제 프레임 검수와 구분.',
                       'technical': '선택 인천v3 SHA 일치,기존8초/1920×1080/30fps/240프레임 전체디코드통과/음성0 영수증 재사용. decode통과를 재생/청취로 해석하지 않음.',
                       'combined_v2': tech['combined_preview'], 'expected_combined_duration_seconds': 24,
                       'cut_boundary_frames': 'unchecked:8/16초 전후 미제공', 'continuous_playback': 'unchecked',
                       'actual_listening': 'unchecked', 'actual_mobile_playback': 'unchecked',
                       'full_body_mp4': '이번검수대상아님·전체시각검토본렌더준비중', 'actual_Jun_timing': 'not_generated_unchecked',
                       'provisional_timing': True, 'new_recompute': False, 'new_render': False, 'new_paid_calls': 0, 'external_messages': 0},
          'authorization_context': {'latest_user_direction': '음성 생성 보류;전체시각/자막검토본은 임시타이밍·기존로컬BGM으로 진행',
                                    'budget_decision_source': rel(budget_path), 'budget_decision_sha256': sha(budget_path),
                                    'budget_record_status': budget.get('status'), 'budget_resolution': budget.get('resolution'),
                                    'direct_chat_response': budget.get('direct_chat_response'),
                                    'local_budget_copy': 'outputs/production-v1-budget/budget_decision.json은 과거 제안 시점 사본이며 현재 승인 상태의 근거가 아님',
                                    'authorization_issued_by_QA': False, 'approval_question_sent': False},
          'next_role': 'director/editor:좁은필수수정닫힘. REC02 advisory 유지. 전체본문MP4가준비되면신규인코딩범위QA별도추가;기존보고서/state수정없음.'}
(QA / 'recheck_v3.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
handoff_result = {'task_id': report['task_id'], 'role': 'qa', 'status': report['status'],
                  'input_revisions': revision, 'outputs': ['recheck_v3.json'],
                  'affected_scene_ids': sorted(set(x['scene_id'] for x in expected_beats)),
                  'checks': [{'check': 'REQ01단위/REC01라벨', 'result': 'closed_verified', 'evidence': 'recheck_v3.json'},
                             {'check': 'REC02작은눈금', 'result': 'open_advisory', 'evidence': 'recheck_v3.json'},
                             {'check': '실제모바일/경계/연속재생/Jun청취', 'result': 'unchecked', 'evidence': 'recheck_v3.json#coverage'}],
                  'open_issue_ids': ['RPR-P1-REC-02'], 'next_role': report['next_role']}
(QA / 'handoff_recheck_v3.json').write_text(json.dumps(handoff_result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': report['status'], 'checks': len(checks), 'inputs': len(inputs), 'counts': report['counts'],
                  'outputs': ['recheck_v3.json', 'handoff_recheck_v3.json']}, ensure_ascii=False))
