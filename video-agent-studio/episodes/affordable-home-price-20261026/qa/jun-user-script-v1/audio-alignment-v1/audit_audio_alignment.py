"""로컬 WAV·제공자 배열·정렬의 독립 QA. 생성기/ASR/외부 요청 미실행."""
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone
import array, audioop, hashlib, json, math, re, wave

OWN=Path(__file__).resolve().parent
EP=OWN.parents[2]
ROOT=EP.parents[2]
N=EP/'narration/jun-user-script-v1'
P=EP/'director/user-recording-v1'
files={};checks=[];errors=[]
def digest(p):
    p=p.resolve();key=p.relative_to(ROOT).as_posix()
    if key not in files:files[key]={'path':key,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    return files[key]['sha256']
def read(p):digest(p);return json.loads(p.read_text('utf-8-sig'))
def check(name,ok,detail):
    checks.append({'check':name,'result':'pass' if ok else 'fail','evidence':detail})
    if not ok:errors.append(name)
def equal(a,b):return math.isclose(a,b,abs_tol=1e-8,rel_tol=0)
def norm(s):return re.sub(r'\s+','',s)
old=read(OWN.parent/'findings.json')
oldhash={x['path']:x['sha256'] for x in old['checked_file_hashes']}
m=read(N/'narration_manifest.json');cap=read(N/'caption_plan.json');plan=read(P/'scene_plan.json')
g=read(N/'generation_input.json');led=read(N/'generation_ledger.json')
out=read(N/'scene_alignment.json');receipt=read(N/'alignment_receipt.json');signal=read(N/'voice_signal.json')
for name,path in [('approved_original_read_mapping',N/'narration_manifest.json'),('approved_display_mapping',N/'caption_plan.json'),('literal_scene_anchors',P/'scene_plan.json'),('frozen_voice_request_text',N/'generation_input.json')]:
    key=path.relative_to(ROOT).as_posix();check(name,digest(path)==oldhash[key],{'sha256':digest(path),'prior_evidence':'qa/jun-user-script-v1/findings.json; 원문/값 보존 검수는 동일 SHA로 계승'})
check('alignment_receipt_SHA_and_input_links',receipt['alignment_sha256']==digest(N/'scene_alignment.json') and all(digest(ROOT/out[k]['path'])==out[k]['sha256'] for k in ['manifest','caption_plan','scene_plan']),receipt)
check('ledger_current_authorization_input_generator_SHA',led['phonetic_manifest_sha256']==digest(N/'generation_input.json') and led['authorization_sha256']==digest(EP/'director/jun-user-script-v1/authorization.json') and led['generator_sha256']==digest(N/'generate.mjs'),{'authorization_id':led['authorization_id'],'authorization_sha256':led['authorization_sha256'],'generator_sha256':led['generator_sha256']})
paras={p['paragraph_id']:p for p in m['paragraphs']};scenes={s['scene_id']:s for s in out['scenes']};units={u['audio_unit_id']:u for u in out['audio_units']}
native={};spans={};maps={};audio_rows=[];clamps=[];credit_sum=0;requests_ok=[]
for ch,inp in zip(m['chapters'],g['paragraphs']):
    cid=ch['chapter_id'];base=N/'paragraphs'/(cid+'P01');r=read(N/'receipts'/(cid+'P01.json'))
    lr=next(x for x in led['requests'] if x['paragraph_id']==cid+'P01')
    artifacts_ok=all(digest(N/name)==h for name,h in r['artifact_sha256'].items())
    requests_ok.append(r==lr and r['status']=='complete' and r['request']['text']==inp['proposed_spoken_text']==ch['text'] and r['text_sha256']==hashlib.sha256(ch['text'].encode()).hexdigest()==ch['sha256'] and r['authorization_sha256']==led['authorization_sha256'] and r['phonetic_manifest_sha256']==led['phonetic_manifest_sha256'] and r['http_status']==200 and int(r['response_headers']['character-cost'])==r['actual_credits'] and artifacts_ok)
    credit_sum+=r['actual_credits']
    a=read(base/'alignment.json');na=read(base/'normalized_alignment.json')
    t=''.join(a['characters']);starts=a['character_start_times_seconds'];ends=a['character_end_times_seconds']
    with wave.open(str(base/'audio.wav'),'rb') as w:
        rate=w.getframerate();frames=w.getnframes();channels=w.getnchannels();width=w.getsampwidth();pcm=w.readframes(frames)
    duration=frames/rate
    samples=array.array('h');samples.frombytes(pcm)
    clipped=samples.count(-32768)+samples.count(32767)
    peak=audioop.max(pcm,2);rms=audioop.rms(pcm,2)
    row={'chapter':cid,'duration_s':duration,'pcm_samples':frames,'sample_rate':rate,'channels':channels,'sample_width_bytes':width,'audio_SHA256':digest(base/'audio.wav'),'peak_dbfs':20*math.log10(peak/32768) if peak else None,'rms_dbfs_integer_estimate':20*math.log10(rms/32768) if rms else None,'clipped_samples':clipped}
    signal_row=next(x for x in signal['rows'] if x['chapter']==cid)
    row['signal_receipt_matches']=signal_row['sha256']==row['audio_SHA256'] and signal_row['clipped_samples']==clipped and equal(signal_row['seconds'],duration) and abs(signal_row['peak_dbfs']-row['peak_dbfs'])<.001 and abs(signal_row['rms_dbfs']-row['rms_dbfs_integer_estimate'])<.02
    row['wave_and_receipt_match']=rate==44100 and channels==1 and width==2 and frames==r['pcm_samples'] and equal(duration,r['pcm_duration_s']) and units[cid]['sha256']==row['audio_SHA256'] and equal(duration,units[cid]['duration_s'])
    valid=len(starts)==len(ends)==len(t) and t==ch['text'] and na['characters']==a['characters'] and all(math.isfinite(s) and math.isfinite(e) and 0<=s<=e<=duration+.1000000001 for s,e in zip(starts,ends)) and all(starts[i]>=starts[i-1] and ends[i]>=ends[i-1] for i in range(1,len(t)))
    over=[{'char_index':i,'char':t[i],'raw_start_s':s,'raw_end_s':e,'overrun_s':max(s,e)-duration} for i,(s,e) in enumerate(zip(starts,ends)) if max(s,e)>duration]
    row['native_alignment_valid']=valid;row['provider_characters']=len(t);row['terminal_clamps']=over
    if over:clamps.append({'chapter':cid,'count':len(over),'max_overrun_s':max(x['overrun_s'] for x in over),'all_terminal_non_alnum':all(x['char_index']==len(t)-1 and not x['char'].isalnum() for x in over),'raw_alignment_preserved_SHA':digest(base/'alignment.json')})
    native[cid]={'text':t,'s':starts,'e':ends,'duration':duration,'frames':frames,'rate':rate}
    cursor=0
    for pid in ch['paragraph_ids']:
        p=paras[pid];spans[pid]=(cid,cursor,cursor+len(p['spoken_text']))
        assert t[cursor:cursor+len(p['spoken_text'])]==p['spoken_text']
        char_map=[];readpos=cursor
        for part in p['display_mapping']:
            if part['kind']=='literal':char_map += [(readpos+i,readpos+i) for i in range(len(part['original']))]
            else:char_map += [(readpos,readpos+len(part['spoken'])-1)]*len(part['original'])
            readpos+=len(part['spoken'])
        assert len(char_map)==len(p['text']) and readpos==spans[pid][2]
        maps[pid]=char_map;cursor=spans[pid][2]+2
    assert cursor-2==len(t)
    audio_rows.append(row)
check('7_complete_receipts_all_28_audio_alignment_artifact_SHA',len(requests_ok)==7 and all(requests_ok),{'requests':len(requests_ok),'artifact_files':28,'actual_credits':credit_sum,'submitted_characters':led['submitted_characters'],'reserved_pending_credits':led['reserved_pending_credits']})
check('actual_usage_2317_within_7000_no_pending_or_retries',credit_sum==led['actual_credits']==out['actual_credits']==receipt['actual_credits']==2317 and led['reserved_pending_credits']==0 and led['automatic_retries']==0 and led['submitted_characters']==5797 and led['cap']==7000,{'credits':credit_sum,'cap':led['cap']})
check('7_PCM_duration_headers_sample_counts_SHA_and_signal',all(x['wave_and_receipt_match'] and x['signal_receipt_matches'] and x['clipped_samples']==0 for x in audio_rows) and equal(sum(x['duration_s'] for x in audio_rows),679.2),audio_rows)
check('native_arrays_text_monotonic_and_terminal_clamps',all(x['native_alignment_valid'] for x in audio_rows) and len(clamps)==7 and all(x['count']==1 and x['all_terminal_non_alnum'] and x['max_overrun_s']<=.1000000001 for x in clamps) and all(equal(c['max_overrun_s'],next(z for z in out['decoder_boundary_clamps'] if z['chapter']==c['chapter'])['max_overrun_s']) for c in clamps),clamps)
scene_rows=[];cut_errors=[];char_errors=[];beat_errors=[];caption_errors=[];beat_rows=[];caption_rows=[];cue_ids=[]
for ch in m['chapters']:
    cid=ch['chapter_id'];n=native[cid];chapter_scenes=[s for s in out['scenes'] if s['audio_unit_id']==cid]
    cuts=[chapter_scenes[0]['audio_start_s']]+[s['audio_end_s'] for s in chapter_scenes]
    if not equal(cuts[0],0) or not equal(cuts[-1],n['duration']):cut_errors.append([cid,'chapter_extent'])
    for index,s in enumerate(chapter_scenes):
        sid=s['scene_id'];start,end=s['audio_start_s'],s['audio_end_s'];d=end-start
        expected=next(x for x in plan['scenes'] if x['scene_id']==sid)
        if index and not equal(start,chapter_scenes[index-1]['audio_end_s']):cut_errors.append([sid,'gap_or_overlap'])
        if not start<end or not equal(d,s['duration_s']) or s['paragraph_ids']!=expected['paragraph_ids']:cut_errors.append([sid,'extent_or_paragraphs'])
        if index:
            pid=s['paragraph_ids'][0];offset=spans[pid][1]
            first=next(i for i,char in enumerate(paras[pid]['spoken_text']) if not char.isspace())
            if not equal(start,n['s'][offset+first]):cut_errors.append([sid,'cut_not_native_first_character'])
        local=lambda t:max(0,min(min(t,n['duration'])-start,d))
        original='';orig_map=[];last_alnum=0
        for j,pid in enumerate(s['paragraph_ids']):
            p=paras[pid];a,z=spans[pid][1:]
            declared=next(x for x in s['characters'] if x['paragraph_id']==pid)
            if declared['spoken_sha256']!=p['spoken_sha256'] or len(declared['start_s'])!=z-a:char_errors.append([sid,pid,'length_or_SHA'])
            if any(not equal(v,local(t)) for v,t in zip(declared['start_s'],n['s'][a:z])) or any(not equal(v,local(t)) for v,t in zip(declared['end_s'],n['e'][a:z])):char_errors.append([sid,pid,'native_arrays'])
            for i in range(a,z):
                if n['text'][i].isalnum():
                    if n['s'][i]<start-1e-8 or n['e'][i]>end+1e-8:cut_errors.append([sid,'alnum_outside_scene',i,n['text'][i],n['s'][i],n['e'][i]])
                    last_alnum=max(last_alnum,local(n['e'][i]))
            if j:original+='\n\n';orig_map += [maps[pid][0]]*2
            original+=p['text'];orig_map+=maps[pid]
        if not equal(last_alnum,s['last_spoken_end_s']):cut_errors.append([sid,'last_spoken_marker'])
        compact_index=[i for i,char in enumerate(original) if not char.isspace()];compact=norm(original)
        if len(s['beats'])!=len(expected['beats']):beat_errors.append([sid,'beat_count'])
        previous=-1
        for bi,(beat,planned) in enumerate(zip(s['beats'],expected['beats']),1):
            target=norm(planned['anchor']);matches=[];pos=compact.find(target)
            while pos>=0:
                left,right=compact_index[pos],compact_index[pos+len(target)-1]
                ai,zi=orig_map[left][0],orig_map[right][1]
                if ai==beat['provider_char_start'] and zi+1==beat['provider_char_end'] and pos>=previous:matches.append((pos,ai,zi))
                pos=compact.find(target,pos+1)
            if not matches:beat_errors.append([sid,beat['beat_id'],'anchor_location']);continue
            where,ai,zi=matches[0];previous=where
            if beat['anchor_original']!=planned['anchor'] or beat['beat_id']!=f'{sid}.b{bi:02}' or not equal(beat['start_s'],local(n['s'][ai])) or not equal(beat['end_s'],local(n['e'][zi])):beat_errors.append([sid,beat['beat_id'],'native_timing'])
            beat_rows.append({'beat_id':beat['beat_id'],'chapter':cid,'scene_id':sid,'anchor_original':planned['anchor'],'provider_char_range':[ai,zi+1],'scene_start_s':beat['start_s'],'scene_end_s':beat['end_s'],'source_chapter_start_s':start+beat['start_s'],'source_chapter_end_s':start+beat['end_s']})
        previous_end=0
        for cue in s['captions']:
            source=next(x for x in cap['cues'] if x['cue_id']==cue['cue_id']);pid=source['paragraph_id'];cue_ids.append(cue['cue_id'])
            ai=maps[pid][source['source_start']][0];zi=maps[pid][source['source_end']-1][1]
            if source['scene_id']!=sid or any(cue[k]!=source[k] for k in ['text','display_lines','paragraph_id']) or not equal(cue['start_s'],local(n['s'][ai])) or not equal(cue['end_s'],local(n['e'][zi])) or cue['start_s']<previous_end-1e-8 or not 0<=cue['start_s']<cue['end_s']<=d+1e-8:caption_errors.append([sid,cue['cue_id'],'text_native_boundary_or_overlap'])
            previous_end=cue['end_s']
            caption_rows.append({'cue_id':cue['cue_id'],'scene_id':sid,'chapter':cid,'provider_char_range':[ai,zi+1],'scene_start_s':cue['start_s'],'scene_end_s':cue['end_s'],'source_chapter_start_s':start+cue['start_s'],'source_chapter_end_s':start+cue['end_s']})
        scene_rows.append({'scene_id':sid,'chapter':cid,'audio_start_s':start,'audio_end_s':end,'duration_s':d,'start_sample':round(start*n['rate']),'end_sample':round(end*n['rate']),'last_spoken_end_s':last_alnum,'basis':'실제 제공자 문자 배열과 소스 WAV의 PCM 샘플 범위; 실제 컷 파일/청취는 미확인'})
    for boundary in cuts[1:-1]:
        for i,char in enumerate(n['text']):
            if char.isalnum() and n['s'][i]<boundary-1e-8 and n['e'][i]>boundary+1e-8:cut_errors.append([cid,'native_alnum_straddles_cut',boundary,i,char])
    selected=[x for x in scene_rows if x['chapter']==cid]
    if sum(x['end_sample']-x['start_sample'] for x in selected)!=n['frames']:cut_errors.append([cid,'PCM_sample_coverage'])
check('31_scene_source_cuts_cover_all_PCM_no_native_alnum_cut',len(scene_rows)==31 and [s['scene_id'] for s in out['scenes']]==[s['scene_id'] for s in plan['scenes']] and not cut_errors,{'errors':cut_errors,'scenes':scene_rows,'total_source_PCM_s':sum(s['duration_s'] for s in scene_rows),'actual_extracted_scene_WAV_or_final_mix':'unchecked_not_provided_for_this_task'})
check('48_paragraph_character_arrays_exact_native_positions',not char_errors and sum(len(s['characters']) for s in out['scenes'])==48,{'errors':char_errors,'paragraphs':48,'reading_characters_without_separators':sum(len(p['spoken_text']) for p in paras.values())})
check('101_original_literal_beats_exact_native_character_windows',len(beat_rows)==101 and not beat_errors,{'errors':beat_errors,'beat_count':len(beat_rows)})
check('156_captions_text_order_native_character_boundaries',len(caption_rows)==156 and cue_ids==[c['cue_id'] for c in cap['cues']] and not caption_errors,{'errors':caption_errors,'caption_count':len(caption_rows)})
report={'task_id':'JUN-US1-ACTUAL-AUDIO-ALIGNMENT-QA','checked_at_utc':datetime.now(timezone.utc).isoformat(),'checks':checks,'failed_checks':errors,'audio_rows':audio_rows,'decoder_clamps':clamps,'scenes':scene_rows,'beats':beat_rows,'captions':caption_rows,'checked_file_hashes':list(files.values()),'actual_listening':False,'continuous_playback':False,'ASR_execution_by_QA':False,'paid_calls_by_QA':0,'external_requests_by_QA':0,'scope_limit':'소스 WAV와 제공자 인덱스상 컷·정렬 검증. 음향학적 발음/호흡/컷 품질 및 최종 MP4는 별도.'}
put=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
put(OWN/'alignment_evidence.json',report)
print(json.dumps({'checks':len(checks),'failed':errors,'WAV_seconds':sum(x['duration_s'] for x in audio_rows),'clipped_samples':sum(x['clipped_samples'] for x in audio_rows),'terminal_clamps':clamps,'beats':len(beat_rows),'captions':len(caption_rows),'checked_files':len(files)},ensure_ascii=False))
