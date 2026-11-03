"""저장된 준비 산출물의 독립 로컬 검사. 네트워크와 생성 호출 없음."""
from pathlib import Path
from hashlib import sha256
import json
import math
import re
from datetime import datetime, timezone

own = Path(__file__).resolve().parent
root = own.parents[4]
expected = '0368c9e08b8a2447ed429d9e78ab9a8238b2d823c27467362174600876a797b7'
checks = []


def check(name, passed):
    checks.append({'check': name, 'passed': bool(passed)})


def read(name):
    return json.loads((own / name).read_text(encoding='utf-8-sig'))


def digest(file):
    return sha256(file.read_bytes()).hexdigest()


def text_sha(text):
    return sha256(text.encode('utf-8')).hexdigest()


m = read('narration_manifest.json')
p = read('pronunciation_proposal.json')
b = read('budget_proposal.json')
a = read('account_readonly.json')
t = read('timing_proposals.json')
h = read('handoff.json')
source_file = root / m['inputs']['script']['path']
source = source_file.read_bytes().decode('utf-8')
check('확정 대본 SHA 일치', digest(source_file) == expected == m['script_sha256'] == b['script_sha256'])
prepared = json.loads((root / m['inputs']['free_tts_v6_manifest']['path']).read_text(encoding='utf-8-sig'))
grounded = [x for chapter in prepared['chapters'] for x in chapter['paragraphs']]
sections = re.split(r'^## \d+\. [^\n]+\n', source, flags=re.M)[1:]
body_paragraphs = [text.strip() for section in sections for text in re.split(r'\n\s*\n', section.strip())]
check('본문만 10장54문단', len(sections) == 10 and len(body_paragraphs) == len(grounded) == len(m['paragraphs']) == len(p['paragraphs']) == 54)
check('문단 ID 중복 없음', len({x['paragraph_id'] for x in m['paragraphs']}) == 54)
for raw, expanded, old, body_text in zip(m['paragraphs'], p['paragraphs'], grounded, body_paragraphs):
    file = root / raw['path']
    check(raw['paragraph_id'] + ' 원문/파일/근거 일치',
          raw['text'] == old['text'] == body_text == file.read_bytes().decode('utf-8') == source[raw['source_start']:raw['source_end']]
          and raw['sha256'] == digest(file) == text_sha(raw['text'])
          and raw['characters'] == len(raw['text']) and raw['utf8_bytes'] == len(file.read_bytes()))
    spoken = expanded['proposed_spoken_text']
    candidate = raw['text']
    for sub in reversed(expanded['substitutions']):
        check(raw['paragraph_id'] + ' 발음 원문 offset', candidate[sub['source_start']:sub['source_end']] == sub['original'])
        candidate = candidate[:sub['source_start']] + sub['spoken'] + candidate[sub['source_end']:]
    check(raw['paragraph_id'] + ' 발음 제안/체크섬 일치',
          spoken == old['spoken_text'] == candidate and expanded['proposed_spoken_text_sha256'] == text_sha(spoken)
          and expanded['source_text_sha256'] == raw['sha256'] and expanded['characters'] == len(spoken)
          and expanded['character_delta'] == len(spoken)-len(raw['text']))
check('원문8715·발음후보8949·차이234자', sum(x['characters'] for x in m['paragraphs']) == m['characters'] == 8715
      and sum(x['characters'] for x in p['paragraphs']) == p['characters'] == 8949 and p['character_delta'] == 234)
check('본문 합본 SHA/구분자', digest(root / m['body_file']['path']) == m['body_file']['sha256']
      and (own / 'narration_body.txt').read_bytes().decode('utf-8') == '\n\n'.join(x['text'] for x in m['paragraphs'])
      and m['body_file']['characters_with_separators'] == 8821)
check('매니페스트 참조 SHA', digest(own/'narration_manifest.json') == b['narration_manifest_sha256'] == h['input_revisions']['manifest_sha256']
      and digest(own/'pronunciation_proposal.json') == b['pronunciation_proposal_sha256'] == h['input_revisions']['pronunciation_proposal_sha256'])
for key in ('script', 'free_tts_v6_manifest', 'pronunciation_dictionary', 'previous_audio_timing', 'previous_run_inputs', 'tts_config', 'account_snapshot'):
    reference = m['inputs'][key]
    check('불변 입력 ' + key, digest(root / reference['path']) == reference['sha256'])
check('인증 GET3건과 계정 차감 산식', len(a['requests']) == 3 and all(x['method']=='GET' and x['http_status']==200 for x in a['requests'])
      and a['subscription']['character_limit'] - a['subscription']['character_count'] == a['subscription']['included_remaining'] == b['included_remaining'] == 22558)
check('승인모델·음성·배수', b['voice']['model']=='eleven_v4' and b['voice']['voice_id']=='4p6UA7mnodF5q7JFFrnW'
      and b['model_rates']=={'character_cost_multiplier':1, 'cost_discount_multiplier':1} and b['voice_rate']==1 and b['estimated_credits_per_character']==1)
for scenario in b['scenarios']:
    check(scenario['variant'] + ' 20% 상한', scenario['revision_reserve_characters']==math.ceil(scenario['input_characters']*.2)
          and scenario['character_cap']==scenario['input_characters']+scenario['revision_reserve_characters']
          and scenario['proposed_included_credit_cap']==scenario['character_cap'])
check('상한10739·예비1790·잔여여유11819', b['proposed_cap']==b['proposed_included_credit_cap']==10739
      and b['proposed_revision_reserve_characters']==1790 and b['included_headroom_after_proposed_cap']==22558-10739==11819)
check('추가현금0·미생성', b['additional_cash_usd_cap']==0 and b['additionalcash0'] is True
      and b['topup_or_overage_authorized'] is False and b['generation_authorized'] is False and b['generation_started'] is False
      and b['sample_generated'] is False and all(b[x]==0 for x in ('tts_post_calls','paid_generation_calls','upload_calls','delete_calls'))
      and b['text_variant_selected_for_generation'] is None and p['status']=='proposed_not_applied_not_authorized_for_generation')
check('계정 검토 산식/초과청구 비활성', b['account_checks_passed'] is True and all(b['readiness_checks'].values())
      and a['subscription']['max_credit_limit_extension']==0)
check('Jun 미측정과 기존 근거 분리', len(t['scenes'])==10 and t['new_body_seconds'] is None and t['timing_delta_s'] is None
      and all(x['start_s'] is None and x['end_s'] is None and x['measured_seconds'] is None and x['estimate_seconds'] is None
              and x['audio_revision']=='jun-replacement-v1-not-generated' for x in t['scenes'])
      and h['changed_scene_ids']==[] and t['actual_changed_scene_ids']==[])
for reference in h['outputs']:
    check('인계 산출물 ' + Path(reference['path']).name, digest(root / reference['path'])==reference['sha256'])
check('저장물 JSON 구문', all(json.loads(f.read_text(encoding='utf-8-sig')) is not None for f in own.glob('*.json')))
check('정확히54개 무개행 TXT', len(list((own/'paragraphs').glob('*.txt')))==54
      and all(not f.read_bytes().endswith(b'\n') for f in (own/'paragraphs').glob('*.txt')))
check('현재 검수 범위 명시', p['actual_listening'] is False and '미확인' in h['unresolved'])
files = [f for f in own.rglob('*') if f.is_file() and f.name != 'validation.json']
result = {
    'checked_at_utc':datetime.now(timezone.utc).isoformat(),
    'status':'passed' if all(x['passed'] for x in checks) else 'failed',
    'validation_scope':'준비 산출물만 별도 Python으로 재읽기. 독립 QA 담당 검수·실제 생성·청취·재생은 수행하지 않음.',
    'checks_passed':sum(x['passed'] for x in checks),'checks_failed':[x for x in checks if not x['passed']],
    'totals':{'chapters':10,'paragraphs':54,'raw_characters':m['characters'],'proposed_spoken_characters':p['characters'],
              'revision_reserve_characters':b['proposed_revision_reserve_characters'],'proposed_credit_cap':b['proposed_cap'],
              'included_remaining':b['included_remaining'],'headroom':b['included_headroom_after_proposed_cap'],'additional_cash_usd_cap':0},
    'script_sha256':expected,'manifest_sha256':digest(own/'narration_manifest.json'),
    'pronunciation_proposal_sha256':digest(own/'pronunciation_proposal.json'),
    'outputs':[{'path':f.relative_to(root).as_posix(),'sha256':digest(f),'bytes':f.stat().st_size} for f in sorted(files)],
    'checks':checks
}
(own/'validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:result[k] for k in ('status','checks_passed','checks_failed','totals','manifest_sha256','pronunciation_proposal_sha256')},ensure_ascii=False))
raise SystemExit(0 if result['status']=='passed' else 1)
