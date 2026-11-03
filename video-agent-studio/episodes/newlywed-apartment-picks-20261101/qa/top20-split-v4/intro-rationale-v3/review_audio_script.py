"""Independent scoped QA. Reads production inputs; writes only this QA folder."""
import array
import csv
import hashlib
import json
import math
import pathlib
import re
import subprocess
import wave
from datetime import datetime, timezone

Q = pathlib.Path(__file__).resolve().parent
E = Q.parents[2]
ROOT = E.parents[2]
N = E / 'narration/top20-split-v4/intro-rationale-v3'
D = E / 'director/top20-split-v4/part1-intro-v3'
FF = ROOT / 'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
checks = []

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()

def check(name, result, detail=None):
    checks.append(dict(check=name, passed=bool(result), evidence=detail))

def norm(s):
    return ''.join(c for c in s if c.isalnum())

def wav(p):
    with wave.open(str(p), 'rb') as w:
        meta = dict(channels=w.getnchannels(), sample_rate=w.getframerate(), sample_width=w.getsampwidth(), frames=w.getnframes())
        return meta, w.readframes(w.getnframes())

def numeric_korean(s):
    s=s.strip()
    if s == '쉰세':
        return 50 + 3
    value=0; digit=0
    digits={'일':1,'이':2,'삼':3,'사':4,'오':5,'육':6,'칠':7,'팔':8,'구':9}
    for c in s:
        if c in digits: digit=digits[c]
        elif c == '십': value += (digit or 1)*10; digit=0
        else: raise ValueError(s)
    return value+digit

P = E / 'writer/top20-split-v4/intro-rationale-v3/intro_proposal_v3.json'
p=read(P); t=read(N/'timing_proposals.json'); led=read(N/'pronunciation_ledger.json'); words=read(N/'words.json')['words']; auth=read(D/'production_authorization.json')
check('approved_proposal_hash',sha(P)=='0cbd68f79ca4981b13d08b68547811c19102be6594933b3d59617af51168ea5d',sha(P))
check('approval_scope',auth['decision_id']=='d884be1c4e38' and auth['status']=='approved' and not auth['scope']['part2_production_authorized'] and auth['scope']['cash_cap_krw']==0)
check('eight_sentences_exact',len(p['sentences'])==len(t['sentences'])==len(led['sentences'])==8 and all(a['text']==b['text']==c['original_text']==c['display_text'] for a,b,c in zip(p['sentences'],t['sentences'],led['sentences'])))
expected=[]
numeric=[]
for s in led['sentences']:
    expected.append(s['reading_text'])
    original=s['original_text']; spoken=s['reading_text']
    last_o=last_s=0
    for x in s['transformations']:
        numeric.append(dict(sentence_id=s['sentence_id'],source=x['source_text'],reading=x['spoken_text'].strip(),decoded=numeric_korean(x['spoken_text'])))
        check('numeric_value_'+s['sentence_id']+'_'+str(x['source_start']),int(x['source_text'])==numeric_korean(x['spoken_text']) and original[x['source_start']:x['source_end']]==x['source_text'] and spoken[x['spoken_start']:x['spoken_end']]==x['spoken_text'])
        check('unchanged_reading_span_'+str(len(checks)),original[last_o:x['source_start']]==spoken[last_s:x['spoken_start']])
        last_o=x['source_end'];last_s=x['spoken_end']
    check('unchanged_reading_tail_'+s['sentence_id'],original[last_o:]==spoken[last_s:])
check('four_numeric_mentions',len(numeric)==4,numeric)
check('reading_file_exact',norm((N/'reading_text.txt').read_text(encoding='utf-8-sig'))==norm(' '.join(expected)))
by_sentence={s['sentence_id']:s for s in led['sentences']}
native_by_asset={}
for chunk in t['chunks']:
    native_by_asset[chunk['asset_id']]=read(ROOT/chunk['native_boundaries_path'])['boundaries']
native_used={k:[] for k in native_by_asset}
offset_exact=True;slice_exact=True;word_time=True;sentence_cover=True
for s in t['sentences']:
    group=[w for w in words if w['sentence_id']==s['sentence_id']]
    l=by_sentence[s['sentence_id']]
    sentence_cover &= norm(''.join(w['provider_text'] for w in group))==norm(l['reading_text'])
    sentence_cover &= abs(group[0]['start_s']-s['start_s'])<1e-8 and abs(group[-1]['end_s']-s['end_s'])<1e-8
    covered=set()
    for w in group:
        slice_exact &= l['display_text'][w['display_char_start']:w['display_char_end']]==w['display_text']
        slice_exact &= l['reading_text'][w['reading_char_start']:w['reading_char_end']]==w['reading_text']
        covered.update(range(w['reading_char_start'],w['reading_char_end']))
        chunk=next(c for c in t['chunks'] if c['asset_id']==w['asset_id'])
        start=chunk['start_s']+w['native_offset_ticks']/1e7/1.35
        end=start+w['native_duration_ticks']/1e7/1.35
        offset_exact &= abs(start-w['start_s'])<1e-8 and abs(end-w['end_s'])<1e-8
        word_time &= 0<=w['start_s']<w['end_s']<=t['duration_s']
        native_used[w['asset_id']].append((w['provider_text'],w['native_offset_ticks'],w['native_duration_ticks']))
    sentence_cover &= all(i in covered for i,c in enumerate(l['reading_text']) if c.isalnum())
native_equal=all(native_used[k]==[(x['text'],x['offset'],x['duration']) for x in v] for k,v in native_by_asset.items())
check('native_word_count_and_source',len(words)==91 and native_equal)
check('all_word_display_reading_slices',slice_exact)
check('all_sentence_reading_coverage',sentence_cover)
check('all_word_ticks_scaled_and_offset',offset_exact)
check('all_word_times_within_audio',word_time and all(a['end_s']<=b['start_s']+1e-8 for a,b in zip(words,words[1:])))
meta,pcm=wav(N/'intro_with_brand.wav')
hm,h=wav(ROOT/t['chunks'][0]['audio_path']); bm,b=wav(ROOT/t['brand_intro']['source_path']);rm,r=wav(ROOT/t['chunks'][1]['audio_path'])
check('PCM_exact_hook_brand_rest',pcm==h+b+r,dict(hook_frames=hm['frames'],brand_frames=bm['frames'],rest_frames=rm['frames'],format_equal=all(m['sample_rate']==meta['sample_rate'] and m['channels']==meta['channels'] and m['sample_width']==meta['sample_width'] for m in [hm,bm,rm])))
check('brand_exactly_once_PCM',pcm.count(b)==1 and len(b)==5*44100*2)
samples=array.array('h');samples.frombytes(pcm)
peak=max(abs(x) for x in samples); rms=math.sqrt(sum(x*x for x in samples)/len(samples))
metrics=dict(**meta,duration_s=meta['frames']/meta['sample_rate'],bytes=(N/'intro_with_brand.wav').stat().st_size,sha256=sha(N/'intro_with_brand.wav'),peak_pcm=peak,peak_dbfs=20*math.log10(peak/32768),rms_dbfs=20*math.log10(rms/32768))
check('WAV_format_length_hash',meta['sample_rate']==44100 and meta['channels']==1 and meta['sample_width']==2 and metrics['sha256']==t['audio_sha256'] and abs(metrics['duration_s']-47.67231292517007)<1e-10,metrics)
check('no_digital_clipping',peak<32767)
decode=subprocess.run([str(FF),'-v','error','-xerror','-i',str(N/'intro_with_brand.wav'),'-f','null','-'],capture_output=True,text=True)
(Q/'intro_wav_decode.log').write_text(decode.stderr,encoding='utf-8')
check('actual_WAV_full_decode',decode.returncode==0,dict(returncode=decode.returncode,log='intro_wav_decode.log'))
with (ROOT/'analysis/newlywed_region_2024/capital_gu_ranking.csv').open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
top=read(E/'research/top20-8min-v2/top20.json'); selected=sorted([r for r in top['regions'] if 11<=r['rank']<=20],key=lambda r:-r['rank'])
check('53_gu_and_20_to_11',len(rows)==53 and len(selected)==10 and [r['rank'] for r in selected]==list(range(20,10,-1)))
check('selected_ten_match_existing_csv',all(all(str(r[k])==str(next(c for c in rows if int(c['rank'])==r['rank'])[k]) for k in ['rank','province','region','newlywed_couples','reference_date']) for r in selected))
check('first_region_is_Wonmi',selected[0]['region']=='부천시 원미구' and selected[0]['newlywed_couples']==7365)
legend=read(E/'research/top20-split-v4/prices/legend.json')
check('six_legend_bins',len(legend['bands'])==6 and [b['color'] for b in legend['bands']]==['#3E82BD','#299D92','#BEA52D','#E3913D','#D75B58','#954B87'])
lock=read(D/'locked_timing.json');old=read(E/'director/top20-split-v4/part1-production-v1/locked_timing.json')
old_body=[s for s in old['scenes'] if s['scene_id']!='P01-INTRO']
new_body=lock['body_scenes']
body_same=len(old_body)==len(new_body) and all(a['scene_id']==b['scene_id'] and [(x['sentence_id'],x['text']) for x in a['sentences']]==[(x['sentence_id'],x['text']) for x in b['sentences']] and abs(a['start_s']+lock['delta_s']-b['start_s'])<1e-8 and abs(a['end_s']+lock['delta_s']-b['end_s'])<1e-8 for a,b in zip(old_body,new_body))
check('body_text_and_scene_times_inherited',body_same)
check('frame_padded_intro_and_cut_before_body_word',abs(lock['intro_end_s']-48.5)<1e-8 and lock['old_body_cut_s']<old_body[0]['start_s'] and abs(lock['delta_s']-(lock['intro_end_s']-lock['old_body_cut_s']))<1e-8,dict(cut_s=lock['old_body_cut_s'],first_body_word_native_s=old_body[0]['start_s'],gap_s=old_body[0]['start_s']-lock['old_body_cut_s'],intro_audio_end_s=lock['lead_s']+metrics['duration_s'],frame_padded_intro_end_s=lock['intro_end_s']))
check('177_cues_88_sentences',len(lock['captions'])==177 and len(lock['intro_sentences'])+sum(len(s['sentences']) for s in new_body)==88)
check('outro_three_second_rule',abs(lock['brand_outro']['start_s']-lock['last_spoken_end_s']-3)<1e-4)
base=E/'outputs/top20-split-v4/part1/part1_free_v4.mp4'
check('approved_body_video_SHA',sha(base)=='9de0ac10a1d177b49da95b720d863f913fbf8ecc8cdb972a461eb02524b180b2')
input_files=[P,D/'production_authorization.json',N/'handoff.json',N/'verification.json',N/'timing_proposals.json',N/'words.json',N/'pronunciation_ledger.json',N/'reading_text.txt',N/'intro_with_brand.wav',D/'locked_timing.json',E/'research/top20-8min-v2/top20.json',ROOT/'analysis/newlywed_region_2024/capital_gu_ranking.csv',E/'research/top20-split-v4/prices/legend.json',E/'qa/top20-split-v4/part1-production-v1/final_review.json']
report=dict(task_id='independentQA-intro-approved-v3-audio-script',checked_at=datetime.now(timezone.utc).isoformat(),status='passed_audio_script_technical_pending_encoded_video' if all(c['passed'] for c in checks) else 'required_correction',reviewer='independent_QA',decision_id='d884be1c4e38',checked_revision='intro-rationale-v3',checks=checks,failed_checks=[c for c in checks if not c['passed']],metrics=metrics,numeric_mentions=numeric,selected_regions=selected,legend=legend,interpretation='거주 신혼부부 수는 지역 선정 기준이며 매수 가능성·매수 추천·주택 소유자 수가 아님. 후속 예산별 비교는 미래 계획.',inputs={str(x.relative_to(ROOT)):sha(x) for x in input_files},coverage=dict(approved_sentences=8,native_words=91,new_WAV_full_decode=True,PCM_comparison=True,old_body_ASR_repeated=False,actual_listening=False,continuous_playback=False,ASR='pending_offline_new_intro_only',encoded_frames='pending_parent'),limitations=['공급자 단어 시각은 실제 청취 또는 강제정렬을 뜻하지 않음.','음색·자연스러움·핵심 수치의 실제 발음·접합부 청취는 unchecked.','영상 프레임·최종 MP4와 본편 재사용 동등성은 후속 검수 대상.'],next_owner='director/editor: encoded prefix/full MP4 및 body equality evidence 전달')
(Q/'audio_script_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(Q/'handoff.json').write_text(json.dumps(dict(status=report['status'],artifacts=[str(Q/'audio_script_review.json')],input_versions=report['inputs'],validation=dict(checks=len(checks),failed=len(report['failed_checks'])),unresolved=report['limitations'],affected_scenes=['P01-INTRO','P01-R20 connection','body timing offset','P01-OUTRO timing offset'],next_owner=report['next_owner']),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(output=str(Q/'audio_script_review.json'),checks=len(checks),failed=report['failed_checks'],status=report['status']),ensure_ascii=False))
