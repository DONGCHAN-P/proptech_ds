"""Independent local-only Jun input/cost/alignment/PCM audit; writes only this Q."""
import array,hashlib,json,pathlib,re,subprocess,wave
from datetime import datetime,timezone
Q=pathlib.Path(__file__).resolve().parent;E=Q.parents[2];R=E.parents[2]
N=E/'narration/top20-split-v4/jun-and-shorts-v1';D=E/'director/top20-split-v4/part1-jun-and-shorts-v1';W=E/'writer/top20-split-v4/jun-and-shorts-v1'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def norm(s):return ''.join(c for c in s if c.isalnum())
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
checks=[]
def check(name,result,evidence=None):checks.append(dict(check=name,passed=bool(result),evidence=evidence))
auth=read(D/'production_authorization.json');manifest=read(N/'narration_manifest.json');lock=read(N/'input_lock.json');ledger=read(N/'generation_ledger.json');reconcile=read(N/'reconciliation.json');t=read(N/'timing_proposals.json');native=read(N/'native_chunk_alignment.json');sentences=read(N/'sentences.json')['sentences'];words=read(N/'words.json')['words'];plan=read(W/'shorts_plan.json');cta=read(W/'common_cta.json')
check('authorization_and_frozen_manifest',auth['status']=='approved' and auth['decision_id']==lock['authorization_id']==ledger['authorization_id']=='9cde211f3073' and sha(N/'narration_manifest.json')==auth['manifest_sha256']==lock['manifest_sha256'])
check('bounded_scope_no_extra_generation',auth['main_sentences']==90 and auth['shared_CTA_sentences']==2 and auth['planned_requests']==16 and auth['included_credit_cap']==6500 and auth['additional_cash_cap_krw']==0 and not auth['top_up_authorized'] and not auth['automatic_retry'] and not auth['upload_authorized'] and not auth['part2_authorized'])
intro=read(E/'director/top20-split-v4/part1-intro-v3/locked_timing.json')['intro_sentences'];accepted_lock=read(E/'director/top20-split-v4/part1-map-clean-v1/locked_timing.json');body=[s for c in accepted_lock['body_scenes'] for s in c['sentences']];accepted=intro[:6]+accepted_lock['criteria_sentences']+intro[6:]+body
main=[s for s in manifest['sentences'] if s['kind']=='accepted_main'];additional=[s for s in manifest['sentences'] if s['kind']!='accepted_main'];assert len(accepted)==90
check('accepted90_text_and_reading_order_exact',len(main)==90 and all((a['sentence_id'],a['text'],a['reading_text'])==(b['sentence_id'],b['text'],b['reading_text']) for a,b in zip(main,accepted)))
check('shared_CTA_exact_by_text_aliases',len(additional)==2 and [(x['text'],x['reading_text']) for x in additional]==[(x['exacttext'],x['reading_text']) for x in cta['sentences']],dict(alias_map={a['sentence_id']:b['sentence_id'] for a,b in zip(cta['sentences'],additional)}))
check('accepted_baseline_video_hash',sha(R/manifest['source_video'])==manifest['source_video_sha256']=='a8d7771668848fe406d76e429db85026f1b300e634d6096b0a780390a9a2a064')
check('all92_proposal_texts_exact',len(sentences)==len(t['sentences'])==92 and all((x['sentence_id'],x['text'],x['reading_text'])==(y['sentence_id'],y['text'],y['reading_text'])==(z['sentence_id'],z['text'],z['reading_text']) for x,y,z in zip(manifest['sentences'],sentences,t['sentences'])))
check('16_requests_only_complete',len(ledger['requests'])==16 and len({x['asset_id'] for x in ledger['requests']})==16 and all(x['status']=='complete' and x['http_status']==200 for x in ledger['requests']))
credit_sum=sum(x['actual_credits'] for x in ledger['requests']);header_sum=sum(int(x['response_headers']['character-cost']) for x in ledger['requests'])
check('cost_headers_ledger_account_reconciliation',credit_sum==header_sum==ledger['actual_credits']==ledger['observed_account_delta']==reconcile['actual_account_credit_delta']==reconcile['actual_header_credit_sum']==2208 and ledger['initial_included_remaining']-ledger['final_included_remaining']==2208 and ledger['final_included_remaining']==14456,dict(header_sum=header_sum,local_snapshot_delta=ledger['observed_account_delta'],remaining=14456,cap=6500))
check('within_authorized_cap_no_cash_retry_topup',2208<=auth['included_credit_cap'] and ledger['automatic_retries']==ledger['topup_calls']==ledger['overage_calls']==ledger['cash_spent_krw']==0 and reconcile['additional_post_calls_after_generation']==0)
check('provider_voice_model_speed',all(x['request']['model_id']==auth['model']=='eleven_v4' and x['request']['voice_settings']['speed']==.97 and auth['voice_id'] in x['endpoint'] for x in ledger['requests']) and lock['voice_settings']['speed']==.97)
check('native_no_old_timing_or_tempo_scaling',t['provider_speed']==.97 and t['tempo_factor']==1 and t['trimmed'] is False and t['global_times_provisional_assembly_offsets'] is True and t['timing_locked_by_director'] is False)
FF=R/lock['ffmpeg_path'];chunk_metrics=[];alphanumeric_overruns=[];all_inputs=all_chars=all_native=all_pcm=all_mono=True;input_count=0
chunks_by_id={x['asset_id']:x for x in t['chunks']};native_by_id={x['asset_id']:x for x in native['chunks']}
for c in manifest['chunks']:
    asset=c['asset_id'];f=R/c['path'];text=f.read_text(encoding='utf-8-sig').replace('\r\n','\n');request=next(x for x in ledger['requests'] if x['asset_id']==asset);chunk=chunks_by_id[asset];nc=native_by_id[asset]
    input_count+=len(text);all_inputs &= sha(f)==c['sha256'] and request['request']['text']==text and request['request_text_sha256']==hashlib.sha256(text.encode()).hexdigest()
    rawalign=read(R/chunk['alignment']['path']);rawnorm=read(R/chunk['normalized_alignment']['path']);all_native &= rawalign==nc['alignment'] and rawnorm==nc['normalized_alignment']
    chars=rawalign['characters'];starts=rawalign['character_start_times_seconds'];ends=rawalign['character_end_times_seconds'];all_chars &= ''.join(chars)==text and len(chars)==len(starts)==len(ends)
    all_native &= all(0<=a<=b for a,b in zip(starts,ends)) and all(a<=b+1e-8 for a,b in zip(starts,starts[1:]))
    wavpath=R/chunk['wav_path']
    with wave.open(str(wavpath),'rb') as w:fmt=dict(sample_rate=w.getframerate(),channels=w.getnchannels(),width=w.getsampwidth(),frames=w.getnframes());pcm=w.readframes(w.getnframes())
    all_mono &= fmt['sample_rate']==44100 and fmt['channels']==1 and fmt['width']==2
    pcmsha=hashlib.sha256(pcm).hexdigest();duration=fmt['frames']/fmt['sample_rate'];arr=array.array('h');arr.frombytes(pcm);peak=max(abs(x) for x in arr)
    decoded=subprocess.run([str(FF),'-v','error','-xerror','-i',str(R/chunk['raw_audio']['path']),'-vn','-ac','1','-ar','44100','-c:a','pcm_s16le','-f','s16le','-'],capture_output=True)
    all_pcm &= decoded.returncode==0 and decoded.stdout==pcm and sha(wavpath)==chunk['wav_sha256'] and pcmsha==chunk['pcm_sha256'] and abs(duration-chunk['duration_s'])<1e-8 and peak<32767
    overrun=[dict(char=ch,end_s=e) for ch,e in zip(chars,ends) if e>duration+1e-8];alphanumeric_overruns += [dict(asset_id=asset,**x) for x in overrun if x['char'].isalnum()]
    chunk_metrics.append(dict(asset_id=asset,**fmt,duration_s=duration,peak_pcm=peak,wav_sha256=sha(wavpath),pcm_sha256=pcmsha,full_raw_decode_PCM_exact=decoded.returncode==0 and decoded.stdout==pcm,native_overrun_s=max(0,max(ends)-duration),overrun_characters=[x['char'] for x in overrun]))
check('all16_frozen_chunk_inputs_exact',all_inputs and input_count==5520,input_count);check('native5520_characters_exact_input',all_chars)
check('both_raw_native_arrays_unchanged_and_monotone',all_native);check('all16_complete_MP3_decodes_match_WAV_PCM',all_pcm,chunk_metrics);check('all16_PCM_headers_44100mono16bit',all_mono)
check('native_overruns_punctuation_only_under100ms',not alphanumeric_overruns and all(x['native_overrun_s']<=.100001 for x in chunk_metrics),alphanumeric_overruns)
by_sentence={s['sentence_id']:s for s in sentences};word_slices=word_times=reading_coverage=numeric_coverage=sentence_chars=True;protected_count=0
for s in sentences:
    chunk=chunks_by_id[s['asset_id']];a=native_by_id[s['asset_id']]['alignment'];starts=a['character_start_times_seconds'];ends=a['character_end_times_seconds'];duration=chunk['duration_s'];g=[w for w in words if w['sentence_id']==s['sentence_id']]
    reading_coverage &= norm(''.join(w['reading_text'] for w in g))==norm(s['reading_text'])
    rt=s['reading_character_timing'];dt=s['display_character_timing'];lo=s['chunk_char_start'];hi=s['chunk_char_end']
    sentence_chars &= ''.join(rt['characters'])==s['reading_text'] and ''.join(dt['characters'])==s['text'] and ''.join(a['characters'][lo:hi])==s['reading_text']
    for i,(st,en) in enumerate(zip(rt['chunk_local_start_times_seconds'],rt['chunk_local_end_times_seconds'])):
        sentence_chars &= abs(st-min(starts[lo+i],duration))<1e-8 and abs(en-min(ends[lo+i],duration))<1e-8
    for w in g:
        word_slices &= s['text'][w['display_char_start']:w['display_char_end']]==w['display_text'] and s['reading_text'][w['reading_char_start']:w['reading_char_end']]==w['reading_text']
        st=min(starts[w['chunk_char_start']],duration);en=min(ends[w['chunk_char_end']-1],duration)
        word_times &= abs(st-w['chunk_local_start_s'])<1e-8 and abs(en-w['chunk_local_end_s'])<1e-8 and 0<=st<=en<=duration
    protected=s['protected_numeric_spans'];protected_count+=len(protected)
    for i,ch in enumerate(s['text']):
        if ch.isascii() and ch.isdigit():numeric_coverage &= any(x['display_char_start']<=i<x['display_char_end'] and x['split_allowed'] is False for x in protected)
    for x in protected:numeric_coverage &= s['text'][x['display_char_start']:x['display_char_end']]==x['display_text'] and s['reading_text'][x['reading_char_start']:x['reading_char_end']]==x['reading_text']
check('all1317_word_reading_display_slices',len(words)==1317 and word_slices);check('all1317_word_times_from_new_native_chars',word_times);check('all92_reading_word_coverage',reading_coverage);check('all92_character_arrays_native_exact',sentence_chars);check('all_ASCII_numeric_tokens_in_protected_spans',numeric_coverage,dict(protected_spans=protected_count))
alias={x['sentence_id']:next(s['sentence_id'] for s in additional if s['text']==x['exacttext']) for x in cta['sentences']};short_refs=[];uses=cta_uses=0;shorts_ok=True
for sh in plan['shorts']:
    ids=[]
    for row in sh['sequence']:
        sid=alias.get(row['sentence_id'],row['sentence_id']);s=by_sentence.get(sid);shorts_ok &= s is not None and s['text']==row['exacttext'] and s['reading_text']==row['reading_text'];ids.append(sid)
        if sid.startswith('SHORTS-CTA'):cta_uses+=1
        else:uses+=1
    short_refs.append(dict(short_id=sh['short_id'],sentence_ids=ids,measured_sentence_span_sum_s=sum(by_sentence[x]['duration_s'] for x in ids),timing_scope='source native sentence spans; not final cut duration'))
check('all3_shorts_25_main_6_CTA_reuses_exact',shorts_ok and len(plan['shorts'])==3 and uses==25 and cta_uses==6,dict(main_uses=uses,CTA_uses=cta_uses,CTA_aliases=alias))
check('content_rank_groups_20to16_15to11',[[r['rank'] for r in x['regions']] for x in plan['shorts'][1:]]==[list(range(20,15,-1)),list(range(15,10,-1))])
cfg=read(R/'config/vertical_video_safe_area.json');profile=cfg['profiles']['youtube_portrait_full_frame_v2'];check('latest_portrait_profile_contract',plan['layout_contract']['profile']=='youtube_portrait_full_frame_v2' and profile['critical_rect']==dict(left=140,top=260,right=840,bottom=1360) and profile['minimum_font_px']==dict(title=56,caption=54,key_value=52,conditions=26))
asr_selection=[s for s in sentences if s['sentence_id'] in ['P01-INTRO-V3-05','P01-CRITERIA-01','P01-CRITERIA-02'] or (s['asset_id'].startswith('P01-R') and (re.match(r'\d+위',s['text']) or ('중위' in s['text'] or ('단지' in s['text'] and '구간' in s['text'] and any(c.isdigit() for c in s['text'])))))]
save(Q/'ASR_selection.json',dict(scope='new Jun numeric utterances only; no old free voice ASR',sentences=[{k:s[k] for k in ['sentence_id','asset_id','text','reading_text','wav_path','chunk_local_start_s','chunk_local_end_s']} for s in asr_selection]))
inputs=[D/'production_authorization.json',N/'narration_manifest.json',N/'input_lock.json',N/'generation_ledger.json',N/'reconciliation.json',N/'account_preflight.json',N/'account_final.json',N/'timing_proposals.json',N/'native_chunk_alignment.json',N/'sentences.json',N/'words.json',W/'shorts_plan.json',W/'common_cta.json',R/'config/vertical_video_safe_area.json']
report=dict(task_id='independent-Jun92-input-audio-cost-QA',checked_at=datetime.now(timezone.utc).isoformat(),status='passed_input_audio_technical_pending_ASR_and_encoded_media' if all(x['passed'] for x in checks) else 'required_correction',checks=checks,failed_checks=[x for x in checks if not x['passed']],main_sentences=90,shared_CTA_sentences=2,chunks=16,words=1317,provider_speed=.97,main_full_chunk_duration_s=sum(x['duration_s'] for x in chunk_metrics if x['asset_id']!='SHORTS-CTA'),CTA_duration_s=next(x['duration_s'] for x in chunk_metrics if x['asset_id']=='SHORTS-CTA'),cost=dict(actual_local_header_sum=header_sum,local_account_delta=2208,included_remaining_snapshot=14456,cap=6500,cash_krw=0,API_or_account_requests_by_QA=0),chunks_verified=chunk_metrics,shorts_reuse=short_refs,layout_profile=profile,input_versions={str(x.relative_to(R)):sha(x) for x in inputs},coverage=dict(full16_WAV_headers_and_PCM=True,complete16_raw_MP3_decode=True,new_native_character_mapping=True,source_text_only_reused=True,old_voice_ASR=False,new_Jun_ASR='pending',actual_hearing=False,actual_listening=False,continuous_playback=False,actual_encoded_media=False),limitations=['Native character alignment is provider metadata, not forced alignment or listening.','N global timing is provisional concatenation without brand/gaps; parent owns final lock.','Shorts critical text boxes and font sizes require actual encoded pixels plus glyph/DOM bounds.','Frozen manifest pre-authorization flags are historical; authorization9cde211f3073 is the execution authority.'],next_owner='director/editor: final main and3Shorts MP4s, current lock, DOM/glyph bounds and actual frame evidence; QA: final scoped review')
save(Q/'audio_script_review.json',report)
print(json.dumps(dict(status=report['status'],checks=len(checks),failed=[x['check'] for x in report['failed_checks']],cost=report['cost'],ASR_selected_sentences=len(asr_selection),report=str(Q/'audio_script_review.json')),ensure_ascii=False))
