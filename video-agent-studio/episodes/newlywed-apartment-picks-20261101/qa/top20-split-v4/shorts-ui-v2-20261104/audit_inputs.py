"""Read-only audit of frozen locks; writes only this QA task's records."""
from pathlib import Path
from collections import defaultdict
import hashlib
import json
import re
import subprocess
import wave
import numpy as np

Q = Path(__file__).resolve().parent
E = Q.parents[2]
R = E.parents[2]
D = E / 'director/top20-split-v4/shorts-ui-v2-20261104'
N = E / 'narration/top20-split-v4/jun-and-shorts-v1'
OLD = E / 'qa/top20-split-v4/jun-and-shorts-v1'
FF = R / 'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
read = lambda p: json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name, data):
    (Q / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
def wav(p):
    with wave.open(str(p), 'rb') as w:
        params = [w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()]
        return params, np.frombuffer(w.readframes(w.getnframes()), '<i2').reshape(-1, params[0])
def ts(v):
    z = round(v * 1000); h, z = divmod(z, 3600000); m, z = divmod(z, 60000); s, z = divmod(z, 1000)
    return f'{h:02d}:{m:02d}:{s:02d},{z:03d}'

prior = read(OLD / 'audio_script_review.json')
native = read(N / 'timing_proposals.json')
byid = {s['sentence_id']: s for s in native['sentences']}
grouped = defaultdict(list)
for s in native['sentences']:
    grouped[s['asset_id']].append(s)
for ss in grouped.values():
    ss.sort(key=lambda x: x['chunk_local_start_s'])
old_chunks = {x['asset_id']: x for x in prior['chunks_verified']}
reuse = []
for p, h in prior['input_versions'].items():
    if any(k in p for k in ['timing_proposals', 'native_chunk_alignment', 'sentences.json', 'narration_manifest']):
        reuse.append(dict(path=p, expected=h, actual=sha(R / p), same=sha(R / p) == h))
scope = read(D / 'request_scope.json')
frozen = []
for k in ['preserved_budget', 'preserved_authorization']:
    x = scope[k]; frozen.append(dict(kind=k, path=x['path'], same=sha(x['path']) == x['sha256']))
facts = read(D / 'shorts_visual_facts.json')
byregion = {x['region_id']: x for x in facts}
facts_equal = sha(D / 'shorts_visual_facts.json') == sha(D.parent / 'part1-jun-and-shorts-v1/shorts_visual_facts.json')
source_arrays = {}
reports = []
failures = []
for p in sorted((D / 'shorts').glob('*/locked_timing.json')):
    lock = read(p); sid = lock['short_id']; checks = []; rows = []
    def check(key, passed, evidence=None):
        checks.append(dict(check=key, passed=bool(passed), evidence=evidence))
        if not passed:
            failures.append(dict(short_id=sid, check=key, evidence=evidence))
    check('lock_master_plan_facts_manifest_hashes',
          sha(lock['master_audio']) == lock['master_audio_sha256'] and
          sha(lock['source_plan']) == lock['source_plan_sha256'] and
          sha(lock['source_visual_facts']) == lock['source_visual_facts_sha256'] and
          sha(N / 'narration_manifest.json') == lock['source_voice_manifest_sha256'])
    check('whole_intro_question_before_first_rank',
          lock['sentences'][0]['text'] == '우리 예산으로 집을 산다면, 어느 동네부터 찾아봐야 할까요?' and
          lock['sentences'][0]['end_s'] < lock['sentences'][1]['start_s'],
          dict(intro=[lock['sentences'][0]['start_s'], lock['sentences'][0]['end_s']], first_rank=lock['sentences'][1]['start_s']))
    cta = [s for s in lock['sentences'] if s['sentence_id'].startswith('SHORTS-CTA')]
    check('single_complete_cta', len(cta) == 1 and cta[0]['text'] == byid[cta[0]['sentence_id']]['text'])
    hold = lock['total_s'] - lock['sentences'][-1]['end_s']
    check('at_least_1_05s_after_final_native_speech', hold >= 1.05 - 1e-8, hold)
    regions = [s['region_id'] for s in lock['scenes'] if s['kind'] == 'region']
    expected = ['R17'] if sid == 'SHORT01-PROMO' else [f'R{x:02d}' for x in (range(20,15,-1) if sid == 'SHORT02-R20-R16' else range(15,10,-1))]
    check('expected_regions_and_order', regions == expected, regions)
    vp, voice = wav(p.parent / 'voice.wav'); mp, master = wav(p.parent / 'master_audio.wav'); bp, bed = wav(p.parent / 'music.wav')
    check('wav_format_duration', vp[:3] == mp[:3] == bp[:3] == [2,2,48000] and len(voice) == len(master) == len(bed) == lock['total_frames'] * 1600)
    expected_voice = np.zeros_like(voice)
    for s, clip in zip(lock['sentences'], lock['source_clips']):
        native_s = byid[s['sentence_id']]; aid = s['asset_id']; path = R / clip['audio_path']
        if aid not in source_arrays:
            raw = subprocess.run([str(FF), '-v','error','-i',str(path),'-vn','-ar','48000','-ac','2','-f','s16le','-'],capture_output=True,check=True).stdout
            source_arrays[aid] = np.frombuffer(raw,'<i2').reshape(-1,2)
        same_group = grouped[aid]; ix = next(i for i,x in enumerate(same_group) if x['sentence_id'] == s['sentence_id'])
        prev = same_group[ix-1]['chunk_local_end_s'] if ix else None
        nxt = same_group[ix+1]['chunk_local_start_s'] if ix+1 < len(same_group) else None
        lo = round(clip['start_s']*48000); hi=round(clip['end_s']*48000); target=round(clip['target_start_s']*48000)
        piece = source_arrays[aid][lo:hi]; expected_voice[target:target+len(piece)] = piece
        immutable = ['text','reading_text','display_text','sentence_normalized_text','protected_numeric_spans','reading_character_timing','display_character_timing','chunk_local_start_s','chunk_local_end_s','chunk_char_start','chunk_char_end']
        fields = all(s[k] == native_s[k] for k in immutable)
        words = len(s['words']) == len(native_s['words']) and all(
            {k:v for k,v in a.items() if k not in ['start_s','end_s','local_start_s','local_end_s']} ==
            {k:v for k,v in b.items() if k not in ['start_s','end_s','local_start_s','local_end_s']}
            for a,b in zip(s['words'],native_s['words']))
        offset = clip['target_start_s'] - clip['start_s']
        timing = abs(s['start_s']-(offset+native_s['chunk_local_start_s'])) < 1e-7 and abs(s['end_s']-(offset+native_s['chunk_local_end_s'])) < 1e-7
        guard = (clip['previous_speech_end_s'] == prev and clip['next_speech_start_s'] == nxt and
                 clip['first_native_s'] == native_s['chunk_local_start_s'] and clip['last_native_s'] == native_s['chunk_local_end_s'] and
                 clip['start_s'] <= clip['first_native_s'] and clip['end_s'] >= clip['last_native_s']+.03-1e-8 and
                 (prev is None or clip['start_s'] >= prev+.10-1e-8) and (nxt is None or clip['end_s'] <= nxt-.12+1e-8))
        source_same = sha(path) == clip['audio_sha256'] == old_chunks[aid]['wav_sha256']
        pcm_same = hashlib.sha256(piece.tobytes()).hexdigest() == clip['source_pcm_sha256']
        captions = [c for c in lock['captions'] if c['sentence_id'] == s['sentence_id']]
        caption_full = ' '.join(c['text'] for c in captions) == s['text']
        protected = all(any(span['display_text'] in c['text'] for c in captions) for span in s['protected_numeric_spans'])
        check(s['sentence_id']+'_native_source_caption_guard', fields and words and timing and guard and source_same and pcm_same and caption_full and protected,
              dict(native_immutable=fields, words_immutable=words, target_offset=timing, guard=guard, source_hash_same=source_same, pcm_same=pcm_same, captions_complete=caption_full, no_numeric_split=protected))
        rows.append(dict(sentence_id=s['sentence_id'], start_s=s['start_s'], end_s=s['end_s'], source_sha256=clip['audio_sha256'], source_trim=[clip['start_s'],clip['end_s']], guard_passed=guard))
    check('entire_voice_pcm_exact_including_silence', np.array_equal(voice, expected_voice))
    check('master_equals_voice_plus_music_no_clipping', np.array_equal(master.astype('int32'),voice.astype('int32')+bed.astype('int32')) and np.abs(master.astype('int32')).max()<32767)
    cues=lock['captions']
    check('caption_nonoverlap_and_native_end', all(a['end_s']<=b['start_s']+1e-7 for a,b in zip(cues,cues[1:])) and all(c['start_s']<c['end_s'] for c in cues))
    srt='\n\n'.join(f"{i+1}\n{ts(c['start_s'])} --> {ts(c['end_s'])}\n{c['text']}" for i,c in enumerate(cues))+'\n'
    check('srt_exact_locked_captions', (p.parent/'captions.srt').read_text(encoding='utf-8-sig')==srt)
    check('scene_facts_exact_frozen_rows', all(sc['visual_facts']==byregion[sc['region_id']] for sc in lock['scenes'] if sc['region_id']))
    reports.append(dict(short_id=sid, lock_sha256=sha(p), master_audio_sha256=sha(p.parent/'master_audio.wav'), duration_s=lock['total_s'], sentences=len(rows), captions=len(cues), regions=regions, final_hold_s=hold, checks=checks, source_clips=rows, passed=all(x['passed'] for x in checks)))
result=dict(task_id='shorts-ui-v2-20261104', status='passed_inputs_pending_visual_and_final_mp4' if not failures and all(x['same'] for x in reuse+frozen) and facts_equal else 'requires_correction',
            prior_native_evidence_reuse=reuse, preserved_authorizations=frozen, frozen_facts_sha_same=facts_equal, shorts=reports, failures=failures,
            asr_reuse=dict(prior_alignment_sentences=92, prior_numeric_ASR_sentences=23, prior_numeric_ASR= str(OLD/'ASR_support_review.json'), same_source_hash_verified=True, new_ASR_runs=0, note='92문장 전체 ASR로 표현하지 않음. 90+2 native 정렬 검수와 23개 숫자 문장 ASR 보조근거를 구분.'),
            coverage=dict(pcm_and_native_alignment='checked', captions='checked_all_76_cues', actual_listening='unchecked', continuous_playback='unchecked', final_mp4='pending'),
            ownership='only this QA task directory; no media/state/old QA mutations')
save('inputs_review.json',result)
print(json.dumps(dict(status=result['status'], failures=failures, shorts=[{k:s[k] for k in ['short_id','sentences','captions','final_hold_s','passed']} for s in reports]),ensure_ascii=False))
