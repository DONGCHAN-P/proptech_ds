"""Independent new two-sentence QA; frozen body/data evidence is reused by hash."""
import array,hashlib,json,math,pathlib,re,subprocess,wave
from datetime import datetime,timezone
Q=pathlib.Path(__file__).resolve().parent;E=Q.parents[2];ROOT=E.parents[2]
N=E/'narration/top20-split-v4/map-clean-v1';D=E/'director/top20-split-v4/part1-map-clean-v1'
FF=ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def wav(p):
    with wave.open(str(p),'rb') as w:
        return dict(rate=w.getframerate(),channels=w.getnchannels(),width=w.getsampwidth(),frames=w.getnframes()),w.readframes(w.getnframes())
def norm(s):return ''.join(c for c in s if c.isalnum())
def number(s):
    s=s.strip()
    if s=='시월':return 10
    digits={'일':1,'이':2,'삼':3,'사':4,'오':5,'육':6,'칠':7,'팔':8,'구':9};units={'십':10,'백':100,'천':1000};n=d=0
    for c in s:
        if c in digits:d=digits[c]
        elif c in units:n+=(d or 1)*units[c];d=0
        else:raise ValueError(s)
    return n+d
checks=[]
def check(name,result,evidence=None):checks.append(dict(check=name,passed=bool(result),evidence=evidence))
auth=read(D/'production_authorization.json');decision=read(D/'script_decision.json');P=E/'writer/top20-split-v4/map-clean-v1/criteria_script.json';script=read(P);t=read(N/'timing_proposals.json');led=read(N/'pronunciation_ledger.json');words=read(N/'words.json')['words'];lock=read(D/'locked_timing.json')
check('scoped_revision_authority_not_exact_wording_approval',auth['decision_id']==decision['id']=='291dc0fbeafc' and auth['approval_basis']=='direct_user_scoped_revision_instruction' and auth['exact_generated_wording_user_approval'] is False and decision['exact_generated_wording_user_approval'] is False)
check('zero_cost_no_part2_or_upload',auth['scope']['cash_cap_krw']==0 and all(auth['scope'][k] is False for k in ['paid_generation_authorized','upload_authorized','external_file_export_authorized','part2_production_authorized']))
check('script_hash_matches_gate_and_audio',sha(P)==auth['script_sha256']==t['script_sha256']==led['script_sha256'],sha(P))
check('two_sentences_preserved_exact',len(script['sentences'])==len(t['sentences'])==len(led['sentences'])==2 and all(a['text']==b['text']==c['original_text']==c['display_text'] for a,b,c in zip(script['sentences'],t['sentences'],led['sentences'])))
numeric=[];reading_ok=True
for s in led['sentences']:
    original=s['original_text'];spoken=s['reading_text'];last_o=last_s=0
    for x in s['transformations']:
        reading_ok &= original[last_o:x['source_start']]==spoken[last_s:x['spoken_start']]
        reading_ok &= original[x['source_start']:x['source_end']]==x['source_text'] and spoken[x['spoken_start']:x['spoken_end']]==x['spoken_text']
        if re.search(r'\d',x['source_text']):
            a=int(re.search(r'\d+',x['source_text']).group());b=number(x['spoken_text']);numeric.append(dict(sentence_id=s['sentence_id'],source=x['source_text'],reading=x['spoken_text'].strip(),decoded=b))
            check('numeric_'+s['sentence_id']+'_'+str(x['source_start']),a==b)
        else:reading_ok &= x['source_text']=='~' and x['spoken_text'].strip()=='에서'
        last_o=x['source_end'];last_s=x['spoken_end']
    reading_ok &= original[last_o:]==spoken[last_s:]
check('seven_numeric_values_and_explicit_area_range',len(numeric)==7 and [x['decoded'] for x in numeric]==[2026,5,10,83,85,11,3],numeric)
check('reading_transforms_and_identity_spans',reading_ok)
check('reading_text_file_exact',norm((N/'reading_text.txt').read_text(encoding='utf-8-sig'))==norm(' '.join(x['reading_text'] for x in led['sentences'])))
native=read(ROOT/t['chunks'][0]['native_boundaries_path'])['boundaries']
check('29_native_words_exact_source_ticks',len(words)==len(native)==29 and all((w['provider_text'],w['native_offset_ticks'],w['native_duration_ticks'])==(x['text'],x['offset'],x['duration']) for w,x in zip(words,native)))
slice_ok=timing_ok=coverage_ok=True
for s in led['sentences']:
    group=[w for w in words if w['sentence_id']==s['sentence_id']]
    coverage_ok &= norm(''.join(w['provider_text'] for w in group))==norm(s['reading_text'])
    spans=set()
    for w in group:
        slice_ok &= s['display_text'][w['display_char_start']:w['display_char_end']]==w['display_text'] and s['reading_text'][w['reading_char_start']:w['reading_char_end']]==w['reading_text']
        spans.update(range(w['reading_char_start'],w['reading_char_end']))
        timing_ok &= abs(w['native_offset_ticks']/1e7/1.35-w['start_s'])<1e-8 and abs((w['native_offset_ticks']+w['native_duration_ticks'])/1e7/1.35-w['end_s'])<1e-8
    coverage_ok &= all(i in spans for i,c in enumerate(s['reading_text']) if c.isalnum())
check('word_source_and_reading_slices',slice_ok);check('all_reading_characters_covered',coverage_ok);check('provider_tick_scaling',timing_ok)
check('words_order_and_WAV_bounds',all(0<=w['start_s']<w['end_s']<=t['duration_s'] for w in words) and all(a['end_s']<=b['start_s']+1e-8 for a,b in zip(words,words[1:])))
check('sentence_timing_first_last_native_words',all(abs(s['start_s']-next(w['start_s'] for w in words if w['sentence_id']==s['sentence_id']))<1e-8 and abs(s['end_s']-[w for w in words if w['sentence_id']==s['sentence_id']][-1]['end_s'])<1e-8 for s in t['sentences']))
fmt,pcm=wav(N/'criteria.wav');pf,processed=wav(N/'processed/P01-CRITERIA.wav')
check('full_processed_PCM_retained',pcm==processed and fmt==pf)
samples=array.array('h');samples.frombytes(pcm);peak=max(abs(x) for x in samples);rms=math.sqrt(sum(x*x for x in samples)/len(samples))
metrics=dict(**fmt,duration_s=fmt['frames']/fmt['rate'],bytes=(N/'criteria.wav').stat().st_size,sha256=sha(N/'criteria.wav'),peak_pcm=peak,peak_dbfs=20*math.log10(peak/32768),rms_dbfs=20*math.log10(rms/32768),last_native_word_end_s=words[-1]['end_s'],tail_after_native_word_s=fmt['frames']/fmt['rate']-words[-1]['end_s'])
check('actual_WAV_format_duration_hash',fmt==dict(rate=44100,channels=1,width=2,frames=549871) and metrics['sha256']==t['audio_sha256'] and abs(metrics['duration_s']-12.468730158730159)<1e-9,metrics)
check('no_PCM_clipping',peak<32767)
r=subprocess.run([str(FF),'-v','error','-xerror','-i',str(N/'criteria.wav'),'-f','null','-'],capture_output=True,text=True)
(Q/'criteria_decode.log').write_text(r.stderr,encoding='utf-8');check('actual_new_WAV_full_decode',r.returncode==0,dict(returncode=r.returncode,log='criteria_decode.log'))
legend=read(E/'research/top20-split-v4/prices/legend.json')
check('criteria_matches_frozen_price_period_area_retrieval',legend['period']==['2026-05-01','2026-10-31'] and legend['area_m2']==[83,85] and legend['retrieved_date']=='2026-11-03' and '83~85제곱미터' in script['sentences'][0]['text'] and '11월 3일' in script['sentences'][1]['text'],legend)
check('uncancelled_individual_transaction_median',legend['statistic']=='per-api-complex median of recorded uncancelled individual transactions' and all(x in script['sentences'][1]['text'] for x in ['취소 건을 빼고','단지별로','중위가격']))
oldlock=read(E/'director/top20-split-v4/part1-intro-v3/locked_timing.json');previous=[s for s in oldlock['intro_sentences'] if s['end_s']<lock['insert_at_s']][-1];following=[s for s in oldlock['intro_sentences'] if s['start_s']>lock['insert_at_s']][0]
check('insertion_in_existing_speech_gap',previous['end_s']<lock['insert_at_s']<following['start_s'],dict(previous_spoken_end=previous['end_s'],insert_at=lock['insert_at_s'],following_spoken_start=following['start_s']))
check('criteria_padding_and_natural_tail',lock['insert_duration_s']==12.8 and abs(lock['criteria_lead_s']-.3)<1e-9 and lock['criteria_lead_s']+metrics['duration_s']<=12.8 and metrics['tail_after_native_word_s']>.7)
check('criteria_global_timing_offsets',all(abs(a['start_s']+lock['criteria_lead_s']+lock['insert_at_s']-b['start_s'])<1e-8 and abs(a['end_s']+lock['criteria_lead_s']+lock['insert_at_s']-b['end_s'])<1e-8 for a,b in zip(t['sentences'],lock['criteria_sentences'])))
check('new_cues_and_lengths',len(lock['captions'])==181 and abs(lock['total_s']-oldlock['total_s']-12.8)<1e-8 and lock['total_frames']==18454)
old_audio=ROOT/auth['baseline_audio'];of,opcm=wav(old_audio);new_audio=pathlib.Path(lock['master_audio']);nf,npcm=wav(new_audio)
cut=round(lock['insert_at_s']*48000)*4;after=round((lock['insert_at_s']+12.8)*48000)*4
check('baseline_master_PCM_before_insertion_exact',npcm[:cut]==opcm[:cut])
check('baseline_master_PCM_after_insertion_exact',npcm[after:]==opcm[cut:])
check('master_format_duration_hash',of['rate']==nf['rate']==48000 and of['channels']==nf['channels']==2 and of['width']==nf['width']==2 and nf['frames']-of['frames']==614400 and sha(new_audio)==lock['master_audio_sha256'])
baseline=ROOT/auth['baseline_video'];prior=read(E/'qa/top20-split-v4/intro-rationale-v3/final_review.json')
check('frozen_baseline_and_QA_match',sha(baseline)==auth['baseline_sha256']==prior['video_sha256']=='158a92ca8e8354620b36affeffa7a69dd637edf7c4a1fd48f515e70d38c89997' and prior['required_open_count']==prior['critical_open_count']==0)
trans=read(D/'transition_plan.json');check('ten_region_photo_slots',len(trans['photos'])==10 and [x['rank'] for x in trans['photos']]==list(range(20,10,-1)))
input_paths=[P,D/'production_authorization.json',D/'script_decision.json',N/'handoff.json',N/'verification.json',N/'timing_proposals.json',N/'pronunciation_ledger.json',N/'words.json',N/'criteria.wav',E/'research/top20-split-v4/prices/legend.json',D/'locked_timing.json',D/'transition_plan.json',E/'qa/top20-split-v4/intro-rationale-v3/final_review.json']
report=dict(task_id='map-clean-v1-independent-new-criteria-review',status='passed_criteria_technical_pending_final_MP4' if all(x['passed'] for x in checks) else 'required_correction',checked_at=datetime.now(timezone.utc).isoformat(),approval_basis='direct_user_scoped_revision_instruction',exact_generated_wording_user_approval=False,decision_id='291dc0fbeafc',checked_revision='map-clean-v1',checks=checks,failed_checks=[x for x in checks if not x['passed']],metrics=metrics,numeric_mentions=numeric,inputs={str(p.relative_to(ROOT)):sha(p) for p in input_paths},frozen_facts=legend,body_PCM_reuse=dict(before_insertion_exact=True,after_insertion_exact=True,baseline_master_audio_sha256=sha(old_audio),new_master_audio_sha256=sha(new_audio),insertion_at_s=39.7,insertion_duration_s=12.8),coverage=dict(new_sentences=2,new_native_words=29,price_reaggregation=False,map_revalidation=False,old_body_ASR_repeated=False,new_WAV_full_decode=True,actual_listening=False,actual_hearing=False,continuous_playback=False,ASR_performed=False,actual_final_MP4_pixels=False),limitations=['숫자 변환·제공자 단어 메타데이터·PCM 검사는 실제 숫자 발음/자연스러움 청취가 아님.','10월은 조회일까지 신고분이라는 범위가 새 조건 화면 또는 잔존 도입 기준 화면에 보존되는지 픽셀 검수 필요.','10개 사진의 장소 식별·사진/지도 전환·정리한 하단·범례·간결 OSM 출처·긴 자막은 최종 MP4 대기.','지도 원자료/가격 집계는 동결 근거를 재사용하며 재집계하지 않음.'],next_owner='director/editor: final MP4 + per-region before/during/after frames + photo manifest/source credits; independent QA: final_review.json')
(Q/'audio_script_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
plan=dict(scope='final actual MP4 only; unchanged body data reuse; no repeated old ASR',criteria_frames=[dict(time_s=lock['insert_at_s']+x,purpose=label) for x,label in [(0,'insert boundary'),(1,'first sentence'),(4.8,'period and83–85area'),(7.6,'retrieval/cancellations/median'),(11.9,'long caption/end of last utterance'),(12.766667,'end pad')]],photo_transitions=[dict(scene_id=x['scene_id'],rank=x['rank'],samples=[dict(time_s=x['final_start_s']-1/30,purpose='before_photo'),dict(time_s=x['final_start_s']+min(1.2,x['duration_s']/2),purpose='photo_held'),dict(time_s=x['final_end_s']-.2,purpose='photo_to_map_during'),dict(time_s=x['final_end_s']+1/30,purpose='map_after')]) for x in trans['photos']],visual_checks=['each photo actual location/region and credit matches visual manifest','each rank change photo hero then map, no wrong rank/count','footer band889..922 cleared, legend above885 retained and captions below942 intact','compact map attribution readable and unobscured at upper-right; full source/licence URL present in delivery sources','price period/area/retrieval/uncancelled median and October reporting cutoff visible in intro','new criteria insert boundary and long captions, zoom maxima, brand/outro and inherited timing shift'],actual_listening=False,continuous_playback=False)
(Q/'pixel_review_plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status=report['status'],checks=len(checks),failed=report['failed_checks'],new_WAV=metrics,report=str(Q/'audio_script_review.json')),ensure_ascii=False))
