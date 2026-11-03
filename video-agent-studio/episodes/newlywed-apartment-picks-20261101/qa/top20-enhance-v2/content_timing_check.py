"""추가 두 장면의 로컬 수치·문자·PCM 연결 독립 검수. 생성/청취 없음."""
import csv
import hashlib
import json
import re
import wave
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('C:/projects/realestate_reco')
EP = ROOT / 'video-agent-studio/episodes/newlywed-apartment-picks-20261101'
OUT = EP / 'qa/top20-enhance-v2'

def read(rel):
    return json.loads((EP / rel).read_text(encoding='utf-8-sig'))

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()

def save(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def norm(s):
    return re.sub(r'[\W_]+', '', s, flags=re.UNICODE)

def wav(path):
    with wave.open(str(path), 'rb') as f:
        return f.getparams(), f.readframes(f.getnframes())

checks = []
def check(name, result, detail=None):
    checks.append(dict(check=name, passed=bool(result), detail=detail))

TREL = 'director/top20-enhance-v2/locked_timing.json'
trev = sha(EP / TREL)
t = read(TREL)
old = read('director/top20-production-v1/locked_timing.json')
added = read('director/top20-enhance-v2/added_scenes.json')
facts = read('research/top20-enhance-v2/verified_facts.json')
receipt = read('research/top20-enhance-v2/validation_receipt.json')
claims = read('research/top20-enhance-v2/added_scenes_claim_review.json')
manifest = read('research/top20-enhance-v2/source_manifest.json')
verification = read('narration/top20-enhance-v2/verification.json')
asr = read('director/top20-enhance-v2/evidence/audio-asr/summary.json')
words = read('narration/top20-enhance-v2/words_v4.json')['words']
source = ROOT / 'analysis/newlywed_region_2024/source/capital_rows.tsv'
check('원본 TSV 해시', sha(source) == manifest['tsv_2024']['sha256'])
with source.open(encoding='utf-8-sig', newline='') as f:
    rows = list(csv.DictReader(f, delimiter='\t'))
pool = [dict(region_key=r['province'] + '|' + r['region'], province=r['province'],
             total_couples=int(r['newlywed_couples']),
             first_marriage_couples=int(r['first_marriage_couples']))
        for r in rows if r['region'].endswith('구')]
check('TOP20 제한 없이 원본의 53개 구 사용', len(pool) == 53 and len({r['region_key'] for r in pool}) == 53,
      dict(all_source_rows=len(rows), pool=len(pool), provinces=dict(Counter(r['province'] for r in pool))))
for r in pool:
    r['total_rank'] = 1 + sum(x['total_couples'] > r['total_couples'] for x in pool)
    r['first_marriage_rank'] = 1 + sum(x['first_marriage_couples'] > r['first_marriage_couples'] for x in pool)
bykey = {r['region_key']: r for r in pool}
total20 = {r['region_key'] for r in pool if r['total_rank'] <= 20}
first20 = {r['region_key'] for r in pool if r['first_marriage_rank'] <= 20}
top4total = [r['region_key'] for r in sorted(pool, key=lambda x: -x['total_couples'])[:4]]
top4first = [r['region_key'] for r in sorted(pool, key=lambda x: -x['first_marriage_couples'])[:4]]
check('1~4위의 지역과 순서 동일', top4total == top4first, top4total)
check('TOP20 진입2·제외2·공통18', first20-total20 == {'경기|안양시 동안구', '서울|마포구'}
      and total20-first20 == {'인천|남동구', '경기|부천시 원미구'} and len(total20 & first20) == 18)
five = []
for claim_id in ['ENH2-DONGAN','ENH2-MAPO','ENH2-NAMDONG','ENH2-WONMI','ENH2-MICHUHOL']:
    fact = next(x for x in facts['facts'] if x['claim_id'] == claim_id)
    v = fact['values']; calculated = bykey[v['region_key']]
    ok = all(v[k] == calculated[k] for k in ['total_couples','first_marriage_couples','total_rank','first_marriage_rank'])
    check(claim_id + ' 원본 직접 순위/수량', ok and v['denominator_regions'] == 53)
    five.append(dict(claim_id=claim_id, **calculated, matches_fact=ok))

sentences = {s['sentence_id']: s for scene in added['scenes'] for s in scene['sentences']}
expected_numbers = {
    'N001-02': [53], 'N001-03': [1,4,20],
    'N001-04': [bykey['경기|안양시 동안구']['total_rank'], bykey['경기|안양시 동안구']['first_marriage_rank'],
                bykey['서울|마포구']['total_rank'], bykey['서울|마포구']['first_marriage_rank']],
    'N001-05': [bykey['경기|안양시 동안구']['first_marriage_couples'], bykey['서울|마포구']['first_marriage_couples']],
    'N002-01': [bykey['인천|남동구']['total_rank'],bykey['인천|남동구']['first_marriage_rank'],
                bykey['경기|부천시 원미구']['total_rank'],bykey['경기|부천시 원미구']['first_marriage_rank']],
    'N002-02': [bykey['인천|미추홀구']['total_rank'],bykey['인천|미추홀구']['first_marriage_rank']],
}
expected_readings = {
    'N001-02':['오십삼 개 구'], 'N001-03':['일 위부터 사 위까지','상위 스무 곳'],
    'N001-04':['전체 이십이 위','초혼 기준 십육 위','이십일 위에서 십칠 위'],
    'N001-05':['동안구 육천오백십 쌍','마포구 육천사백팔십칠 쌍'],
    'N002-01':['전체 십육 위','초혼 기준 이십칠 위','전체 이십 위','이십사 위'],
    'N002-02':['전체 십 위','초혼 기준 이십 위'],
}
for sid, expected in expected_numbers.items():
    numbers = [int(x.replace(',','')) for x in re.findall(r'\d[\d,]*', sentences[sid]['text'])]
    check(sid + ' 표시값·읽기값', numbers == expected and all(x in sentences[sid]['reading_text'] for x in expected_readings[sid]),
          dict(display_numbers=numbers, expected=expected))
check('원고 검토 기록 입력 일치', claims['source_sha256'] == sha(EP/'director/top20-enhance-v2/added_scenes.json'))
for rel, expected in receipt['output_sha256'].items():
    check('리서치 산출물 해시 '+rel, sha(EP/'research/top20-enhance-v2'/rel) == expected)

new_word_details = []
for scene in added['scenes']:
    sid = scene['scene_id']; locked = next(s for s in t['scenes'] if s['scene_id'] == sid)
    prefix = EP/'narration/top20-enhance-v2'/sid
    provider = json.loads((prefix/'provider_boundaries.json').read_text(encoding='utf-8-sig'))['boundaries']
    native = [w for w in provider if w['type'] == 'WordBoundary']
    mapped = [w for w in words if w.get('scene_id') == sid]
    generation = json.loads((prefix/'generation_receipt.json').read_text(encoding='utf-8-sig'))
    reading = (prefix/'reading.txt').read_text(encoding='utf-8-sig')
    target = '\n'.join(s['reading_text'] for s in scene['sentences'])
    check(sid+' 읽기문·provider words 문자 1:1', len(native) == len(mapped)
          and norm(reading) == norm(target) == norm(locked['reading_text']) == norm(''.join(w['text'] for w in mapped))
          and all(a['text'] == b['text'] for a,b in zip(native,mapped)))
    timing_ok = len(native) == len(mapped) and all(
        abs(w['local_start_s'] - p['offset']/10000000/1.35) < 1e-8
        and abs(w['local_end_s'] - (p['offset']+p['duration'])/10000000/1.35) < 1e-8
        and abs(w['start_s']-locked['start_s']-w['local_start_s']) < 1e-8
        and abs(w['end_s']-locked['start_s']-w['local_end_s']) < 1e-8
        for p,w in zip(native,mapped))
    check(sid+' provider ticks/1.35·global 연결', timing_ok)
    check(sid+' 생성 영수증·실파일 SHA', sha(prefix/'production.wav') == generation['production_audio_sha256'] == locked['audio_sha256']
          and sha(prefix/'reading.txt') == generation['input_sha256'])
    check(sid+' 표시문·타이밍·자막 5문장 연결', len(locked['sentences']) == len(locked['captions']) == 5
          and all(x['text'] == sentences[x['sentence_id']]['text'] and x['reading_text'] == sentences[x['sentence_id']]['reading_text']
                  for x in locked['sentences'])
          and all(c['text'] == sentences[c['sentence_id']]['text'] and c['start_s'] >= locked['start_s'] and c['end_s'] <= locked['end_s']
                  for c in locked['captions']))
    asrrow = next(x for x in asr['reports'] if x['scene_id'] == sid)
    expected = sum([expected_numbers.get(s['sentence_id'],[]) for s in scene['sentences']],[])
    recognized = [int(x) for x in re.findall(r'\d+',asrrow['recognized'])]
    check(sid+' 부모 ASR 숫자 및 파일 연결', recognized == expected and asrrow['audio_sha256'] == locked['audio_sha256'],
          dict(expected=expected, recognized=recognized))
    new_word_details.append(dict(scene_id=sid, native_words=len(native), matched_words=len(mapped), start_s=locked['start_s'], end_s=locked['end_s']))

op,ob = wav(old['audio_file']); np,nb = wav(t['audio_file'])
insert = round(verification['insert_at_s']*op.framerate)
frame_bytes = op.nchannels*op.sampwidth
extras = b''
added_frames = 0
for sid in ['N001','N002']:
    sc = next(s for s in t['scenes'] if s['scene_id'] == sid)
    p,b = wav(sc['audio_path']); added_frames += p.nframes; extras += b
    check(sid+' 실측 PCM 길이', p[:3] == op[:3] and abs(p.nframes/p.framerate-sc['duration_s']) < 1e-9)
prefix_ok = nb[:insert*frame_bytes] == ob[:insert*frame_bytes]
suffix_ok = nb[(insert+added_frames)*frame_bytes:] == ob[insert*frame_bytes:]
insert_ok = nb[insert*frame_bytes:(insert+added_frames)*frame_bytes] == extras
check('기존 모든 PCM 프레임 splice 1:1', op[:3] == np[:3] and prefix_ok and suffix_ok and insert_ok
      and np.nframes == op.nframes+added_frames)
check('verification 실제 PCM 필드', verification['unchanged_original_pcm_frames'] == op.nframes
      and abs(verification['duration_s']-np.nframes/np.framerate)<1e-9
      and abs(verification['added_duration_s']-added_frames/op.framerate)<1e-9
      and verification['original_audio_sha256'] == sha(old['audio_file'])
      and verification['new_audio_sha256'] == sha(t['audio_file']) == t['audio_sha256'])
delta = added_frames/op.framerate
old_sentence_count = 0
for s in old['scenes']:
    new = next(x for x in t['scenes'] if x['scene_id'] == s['scene_id'])
    shift = delta if s['start_s'] >= verification['insert_at_s'] else 0
    check(s['scene_id']+' 기존 문장·읽기문·이동량', s.get('narration_text') == new.get('narration_text')
          and s.get('reading_text') == new.get('reading_text')
          and abs(new['start_s']-s['start_s']-shift) < 1e-8
          and abs(new['end_s']-s['end_s']-shift) < 1e-8
          and len(s.get('sentences',[])) == len(new.get('sentences',[]))
          and all(a['sentence_id'] == b['sentence_id'] and a['text'] == b['text']
                  and abs(b['start_s']-a['start_s']-shift)<1e-8 and abs(b['end_s']-a['end_s']-shift)<1e-8
                  for a,b in zip(s.get('sentences',[]),new.get('sentences',[]))))
    old_sentence_count += len(s.get('sentences',[]))
check('103개 기존문장 보존', old_sentence_count == verification['original_sentences_preserved'] == 103)
check('29장면·113문장·1065단어 실측 목록', len(t['scenes']) == t['scene_id_count'] == 29
      and sum(len(x.get('sentences',[])) for x in t['scenes']) == t['sentence_count'] == 113
      and len(words) == verification['all_words'] == 1065)
check('음성 총528.3000907초·480초 초과', np.nframes/np.framerate == t['duration_s'] == verification['duration_s']
      and np.nframes/np.framerate > 480)
check('발화 뒤3초와10초 아웃트로', abs(t['brand_outro']['start_s']-t['last_spoken_end_s']-3) < 1/op.framerate
      and abs(t['brand_outro']['end_s']-t['brand_outro']['start_s']-10)<1e-8)
check('부모 ASR 검수 입력 타이밍 일치', asr['timing_sha256'] == trev)

script_hash = sha(EP/'director/top20-enhance-v2/script_v5.md')
metadata = [
    dict(field='script_sha256', actual=t['script_sha256'], expected=script_hash, problem='script_revision은 v5이나 SHA는 v4 원고를 가리킴'),
    dict(field='word_count', actual=t['word_count'], expected=len(words), problem='추가131개 단어를 반영하지 않은934'),
    dict(field='audio_body_duration_s', actual=t['audio_body_duration_s'], expected=old['audio_body_duration_s']+delta, problem='추가57.345034초를 반영하지 않은 기존 본문 길이'),
]
metadata = [x for x in metadata if x['actual'] != x['expected']]
finding = dict(issue_id='EV2-C01', scene_id=['N001','N002'], timecode='07:09.489~08:06.834', severity='required',
               문제='실제 음성과 장면 타이밍은 일치하나 locked_timing 최상위 원고SHA·단어수·본문길이는 구버전 값이다.',
               evidence=dict(path=str(EP/TREL),sha256=trev, mismatches=metadata),
               수정안='총괄이 현재 v5 원고SHA·1065단어·본문510.931950113초로 메타데이터를 갱신하고 현재/이전 값의 필드를 구분한다. 음성은 변경할 필요 없다. ASR은 audio SHA가 같으면 기존 기록을 연결해 재사용한다.',
               owner='director',status='open',checked_revision=trev)
report = dict(task_id='top20-enhance-QA-v2',stage='content_timing',created_at=datetime.now(timezone.utc).isoformat(),
              verdict='content_and_PCM_pass_metadata_required' if metadata else 'content_and_PCM_pass',
              checked_revision=dict(timing_sha256=trev,audio_sha256=sha(t['audio_file']),added_scenes_sha256=sha(EP/'director/top20-enhance-v2/added_scenes.json')),
              calculation_method='원본 capital_rows.tsv에서 구로 끝나는53행을 직접 선택; 순위=1+해당 값보다 큰 행 수. 리서치 계산 코드 호출 없음.',
              calculation=dict(source=str(source),sha256=sha(source),pool=53,reference_date='2024-11-01',unit='쌍',
                               five_rows=five,top4_total=top4total,top4_first=top4first,
                               entrants=sorted(first20-total20),exits=sorted(total20-first20),overlap=len(total20&first20)),
              timing=dict(duration_s=np.nframes/np.framerate,mp4_duration='unchecked_final_encode_pending',
                          original_frames=op.nframes,new_frames=np.nframes,insert_frame=insert,added_frames=added_frames,
                          added_duration_s=delta,prefix_equal=prefix_ok,suffix_equal=suffix_ok,insert_matches_new_files=insert_ok,
                          preserved_original_sentences=old_sentence_count,new_word_mapping=new_word_details,
                          last_speech_end_s=t['last_spoken_end_s'],outro_start_s=t['brand_outro']['start_s']),
              checks=checks,failed_checks=[x for x in checks if not x['passed']],metadata_mismatches=metadata,
              asr=dict(source=str(EP/'director/top20-enhance-v2/evidence/audio-asr/summary.json'),sha256=sha(EP/'director/top20-enhance-v2/evidence/audio-asr/summary.json'),
                       performed_by='director',numbers='10개 추가 문장 숫자 모두 원고/직접 계산값 일치',
                       spelling_differences='초혼/재혼이 초원·초온·재원으로, 쌍이 상으로 인식됨. 발음 오류 여부를 ASR만으로 확정하지 않음'),
              coverage=dict(actual_listening=False,continuous_playback=False,pronunciation='unchecked',
                            new_visuals='unchecked_previews_pending',full_decode='unchecked_final_encode_pending',
                            uploads='범위 밖; 로컬 개선본 검수에서 업로드 여부는 차단 사유 아님'),
              findings=[finding] if metadata else [])
if report['failed_checks']:
    report['verdict'] = 'checks_failed_review_required'
save('content_timing_qa.json',report)
existing=read('qa/top20-enhance-v2/findings.json')
existing['findings']=[x for x in existing['findings'] if x['issue_id']!='EV2-C01'] + report['findings']
existing['content_timing_checked_revision']=trev
save('findings.json',existing)
save('issue_CONTENT_TIMING_HANDOFF.json',dict(issue_id='EV2-CONTENT-TIMING-HANDOFF',recipients=['director','editor:01a19bab-9d3b-7ed1-9e83-49c83b4661e9'],
     delivery_method='직접 메시지 도구 없음; 공유QA파일로 총괄 전달',direct_message_sent=False,
     scene_id=['N001','N002'],문제='내용/PCM 검수 통과. 최상위 메타데이터3개 갱신 필요.',
     evidence=str(OUT/'content_timing_qa.json'),수정안=metadata,영향='MP4 전 대표3 시각 검수와 최종 인코딩 검수는 별도 진행. 음성 재생성 불필요.'))
save('handoff.json',dict(task_id='top20-enhance-QA-v2',status='content_timing_reviewed_representatives_pending',
     artifacts=[str(OUT/n) for n in ['baseline_audit.json','content_timing_qa.json','findings.json','issue_CONTENT_TIMING_HANDOFF.json']],
     input_revision=report['checked_revision'],verified=['원본53구의5행·첫4위 직접 재계산','기존20769118 PCM 프레임 1:1 보존','추가131 provider words 매핑','실측 음성528.3000907초'],
     unresolved=['EV2-C01 메타데이터 갱신'] if metadata else [],
     pending=['대표3 시각 검수','총괄handoff 후 최종MP4 SHA·길이·전장디코드·전체장면/경계/긴자막/최대줌 검수','실제 청취·연속 재생 미실시'],
     affected_scenes=['N001','N002','C001','E001'],next_owner=['director','editor'],direct_message_sent=False))
for name in ['content_timing_qa.json','findings.json','issue_CONTENT_TIMING_HANDOFF.json','handoff.json']:
    json.loads((OUT/name).read_text(encoding='utf-8'))
print(json.dumps(dict(verdict=report['verdict'],checks=len(checks),failed=report['failed_checks'],five_rows=five,
                     duration_s=report['timing']['duration_s'],metadata=metadata,report=str(OUT/'content_timing_qa.json')),ensure_ascii=False))
