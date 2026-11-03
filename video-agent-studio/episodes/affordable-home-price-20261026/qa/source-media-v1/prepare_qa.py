"""소스 미디어 검수 준비. 담당 QA 폴더만 기록한다."""
from pathlib import Path
import hashlib
import json
import re

QA = Path(__file__).resolve().parent
EP = QA.parents[1]
WORK = EP.parents[2]
EXPECTED_SCRIPT = '9658fc12dc76f67bb75d00e9c88170b167933ad8482dae1b752e4009d2aaf1a3'
EXPECTED_TIMING = '67d7e97351b9a6b9ef4ae71410cfab798d1ab120b792ff924ccc3c11051c16a4'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def write(name, value):
    (QA/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def normalized(text):
    return re.sub(r'\s+', '', text)


lock = read(EP/'director/production-v1/locked_script.json')
timing = read(EP/'narration/production-injoon-v2/final_timing.json')
prepared = read(EP/'narration/prepare-v2-r2/prepared.json')
proposals = read(EP/'writer/scene_proposals_v2.json')
bindings = read(EP/'outputs/private-production-v1/scene_bindings.json')
style = EP/'outputs/private-production-v1/assets/shell.css'
inputs = [EP/'director/production-v1/locked_script.json', WORK/lock['script_path'],
          EP/'narration/production-injoon-v2/final_timing.json', EP/'narration/prepare-v2-r2/prepared.json',
          EP/'writer/scene_proposals_v2.json', EP/'research/facts_v2.json',
          EP/'research/verified_case_packet.json', EP/'research/newborn_policy_addendum_v2.json',
          style]
inputs += sorted((style.parent/'fonts').glob('*.woff2'))
manifest = [dict(path=p.as_posix(), sha256=sha(p), bytes=p.stat().st_size) for p in inputs]
checks = []
failures = []


def check(name, passed, scene=None, cue=None, details=None):
    row = dict(check=name, passed=bool(passed), scene_id=scene, cue_id=cue)
    if details is not None:
        row['details'] = details
    checks.append(row)
    if not passed:
        failures.append(row)


check('승인대본/잠금 해시', lock['approved'] and sha(WORK/lock['script_path']) == lock['script_sha256'] == EXPECTED_SCRIPT)
check('전달된 실측타이밍 해시', sha(EP/'narration/production-injoon-v2/final_timing.json') == EXPECTED_TIMING)
check('준비/실측/제안 대본 해시 일치', prepared['script_sha256'] == timing['script_sha256'] == proposals['frozen_script_sha256'] == EXPECTED_SCRIPT)
check('정책사실 승인해시 재사용', sha(EP/'research/facts_v2.json') == lock['facts_sha256'])
check('신생아 원문/산술 승인해시 재사용', sha(EP/'research/newborn_policy_addendum_v2.json') == lock['newborn_addendum_sha256'])
scene_map = {s['scene_id']: s for s in proposals['scenes']}
prepared_map = {p['scene_id']:p for c in prepared['chapters'] for p in c['paragraphs']}
binding_map = {b['scene_id']:b for b in bindings['bindings']}
check('45장면 ID 일치', len(scene_map) == len(prepared_map) == len(binding_map) == 45 and set(scene_map) == set(prepared_map) == set(binding_map))
all_cues = []
scene_plan = []
paragraph_local = {}
for chapter in timing['chapters']:
    for paragraph in chapter['paragraphs']:
        paragraph_local[paragraph['paragraph']] = dict(chapter=chapter['chapter'], paragraph_start_s=paragraph['offset_s'], paragraph_end_s=paragraph['offset_s']+paragraph['measured_seconds'])
    previous_end = -1
    for cue in chapter['cues']:
        item = dict(cue, chapter=chapter['chapter'])
        all_cues.append(item)
        check('큐 시간/원어경계/순서', 0 <= cue['start_s'] < cue['end_s'] <= chapter['total_seconds'] and cue['start_s'] >= previous_end-1e-6 and abs(cue['start_s']-cue['native_start_s']) < 1e-6 and abs(cue['end_s']-cue['native_end_s']) < 1e-6, cue['scene_id'], cue['id'])
        previous_end = cue['end_s']
        check('표시문과명시줄바꿈 일치/최대2줄', normalized(''.join(cue['display_lines'])) == normalized(cue['text']) and 1 <= len(cue['display_lines']) <= 2, cue['scene_id'], cue['id'])
        source = prepared_map[cue['scene_id']]['text']
        check('원문 span 일치', normalized(source[cue['source_start']:cue['source_end']]) == normalized(cue['text']), cue['scene_id'], cue['id'])
check('실측10장/150큐', len(timing['chapters']) == 10 and len(all_cues) == 150)
for sid, scene in scene_map.items():
    paragraph = prepared_map[sid]
    cues = [c for c in all_cues if c['scene_id'] == sid]
    check('45장면 표시문/읽기문 exact연결', paragraph['text'] == scene['display_text'] == binding_map[sid]['display_text'] and paragraph['spoken_text'] == scene['spoken_text'] == binding_map[sid]['spoken_text'], sid)
    check('150큐 연결 원문복원', normalized(''.join(c['text'] for c in cues)) == normalized(paragraph['text']), sid)
    split_boundaries = []
    cursor = 0
    for cue in cues:
        for line in cue['display_lines']:
            cursor += len(normalized(line))
            split_boundaries.append(cursor)
    text = normalized(paragraph['text'])
    cut_protected = []
    for protected in scene.get('protected_numeric', []):
        token = normalized(protected)
        for match in re.finditer(re.escape(token), text):
            for boundary in split_boundaries:
                if match.start() < boundary < match.end():
                    cut_protected.append(dict(expression=protected, boundary=boundary))
    check('보호숫자/단위 큐·줄경계 보존', not cut_protected, sid, details=cut_protected)
    anchors = paragraph_local[scene['scene_id'] and paragraph['paragraph']]
    scene_plan.append(dict(scene_id=sid,chapter=scene['chapter'],graphic_id=scene['graphic_id'],claim_ids=scene['claim_ids'],case_ids=scene.get('case_ids',[]),protected_numeric=scene.get('protected_numeric',[]),asset_ids=scene.get('asset_ids',[]),visual_direction=scene['visual_direction'],cue_ids=[c['id'] for c in cues],chapter_local_measured=anchors,native_cue_start_s=min(c['start_s'] for c in cues),native_cue_end_s=max(c['end_s'] for c in cues),future_global_times='편집 실측 EDL 수신 후 계산. 브랜드삽입 전 로컬시간을 글로벌로 오인하지 않음.'))

packet = dict(script_sha256=EXPECTED_SCRIPT, timing_sha256=EXPECTED_TIMING,
              css_path=style.as_posix(), css_sha256=sha(style), cues=all_cues,
              scene_plan=scene_plan, input_manifest=manifest)
write('caption_packet.json', packet)
write('caption_text_review.json', dict(scope='150큐 원문·숫자·원어타이밍의 결정적 대조;실제청취아님', checks=len(checks), failed=len(failures), failures=failures, results=checks, input_manifest=manifest))
write('scene_review_plan.json', dict(status='ready_waiting_measured_source_handoff', scenes=scene_plan,
      source_gate=['현재45소스HTML/EDL/폰트/이미지/CLI receipt SHA 고정','실측150큐를 실제HTML에서 전량 글리프검사','45장면 대표·입장/퇴장·최대내용/줌 상태 실제소스프레임 확인','제목/자료/출처/자막 영역과발화대상 일치','CH05비용/CH06대출 분리, CH08가구B/60→300개월/감면조건','순방향/역방향 seek 및 브랜드 전후 공백에 이전큐 hold 없음'],
      encoded_gate=['실제최종MP4 SHA/코덱/크기/길이/전체decode','45장면 대표+장/브랜드경계 전후·최대글자 상태 추출','후보소스프레임과실제인코딩 비교','자막공백박스고정/브랜드·CTA끝무음박스숨김','최종Codex미디어검수는확인한MP4버전에만귀속'],
      actual_listening='unchecked;Kant audio-v1과분리',continuous_playback='unchecked', brand_gap='임의70ms연장/이전큐유지승계금지.실제EDL와native경계대조'))
print(json.dumps(dict(cues=len(all_cues),scenes=len(scene_plan),checks=len(checks),failures=len(failures)),ensure_ascii=False))
