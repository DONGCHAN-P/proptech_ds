"""읽기 전용 캐시 ASR의 7장 커버리지·값·원본 PCM 연결 확인. ASR 실행 없음."""
from pathlib import Path
from decimal import Decimal
import hashlib, json, re, difflib, wave
from datetime import datetime, timezone
OWN=Path(__file__).resolve().parent
EP=OWN.parents[2]
ROOT=EP.parents[2]
N=EP/'narration/jun-user-script-v1'
file_rows={}
def read(p):
    key=p.relative_to(ROOT).as_posix();file_rows[key]={'path':key,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
    return json.loads(p.read_text('utf-8-sig'))
alignment=read(OWN/'alignment_evidence.json');m=read(N/'narration_manifest.json');full=read(N/'asr-full-medium/summary.json')
actual_audio={r['chapter']:r for r in alignment['audio_rows']};scenes={s['scene_id']:s for s in alignment['scenes']};paras={p['paragraph_id']:p for p in m['paragraphs']}
units={x['chapter_id']:x for x in m['chapters']};rows=[];errors=[]
def number_values(text):
    t=re.sub(r'(?<=\d),(?=\d)','',text);t=re.sub(r'\s+','',t).replace('%','퍼센트').replace('㎡','제곱미터').replace('일주택','1주택')
    found=[]
    for token in re.finditer(r'\d+(?:\.\d+)?(?:[억천백십만](?:\d+(?:\.\d+)?)?)*',t):
        raw=token.group();pending=None;group=Decimal(0);total=Decimal(0)
        for bit in re.findall(r'\d+(?:\.\d+)?|[억천백십만]',raw):
            if bit[0].isdigit():pending=Decimal(bit)
            elif bit in '천백십':group+=(pending if pending is not None else 1)*{'천':1000,'백':100,'십':10}[bit];pending=None
            else:
                amount=group+(pending if pending is not None else 0)
                total+=(amount or 1)*{'억':100000000,'만':10000}[bit];group=Decimal(0);pending=None
        value=total+group+(pending if pending is not None else 0)
        tail=t[token.end():];unit=next((u for u in ['퍼센트','제곱미터','개월','년','주택','원'] if tail.startswith(u)),None)
        if any(x in raw for x in '억만') or unit=='원':unit='원'
        found.append({'raw':raw,'value':str(value),'unit':unit or 'number'})
    return found
for row in full['rows']:
    cid=row['scene_id'];individual=read(N/'asr-full-medium'/f'{cid}.json');ch=units[cid]
    ref=' '.join(paras[p]['text'] for p in ch['paragraph_ids'])
    expected=number_values(ref);heard=number_values(row['transcript'])
    numeric_equal=[(n['value'],n['unit']) for n in expected]==[(n['value'],n['unit']) for n in heard]
    c=row['comparison'];a,b=c['normalized_reference'],c['normalized_transcript'];diff=[]
    for op,i,j,x,y in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes():
        if op!='equal':diff.append({'operation':op,'reference_delta':a[i:j],'ASR_delta':b[x:y],'reference_context':a[max(0,i-12):j+12],'ASR_context':b[max(0,x-12):y+12]})
    valid=row==individual and row['audio_sha256']==actual_audio[cid]['audio_SHA256'] and abs(row['seconds']-actual_audio[cid]['duration_s'])<1e-8 and re.sub(r'\s+','',row['reference'])==re.sub(r'\s+','',ref)
    if not valid:errors.append([cid,'ASR_source_or_reference_mismatch'])
    if not numeric_equal:errors.append([cid,'independent_number_sequence_difference',expected,heard])
    if c.get('numeric_differences')!=[]:errors.append([cid,'cached_comparator_number_difference'])
    rows.append({'chapter':cid,'seconds':row['seconds'],'audio_SHA256':row['audio_sha256'],'source_and_individual_summary_match':valid,'numeric_differences_cached':c.get('numeric_differences'),'independent_numeric_sequence_equal':numeric_equal,'reference_number_count':len(expected),'ASR_number_count':len(heard),'reference_number_values':expected,'ASR_number_values':heard,'normalized_similarity_declared':c.get('text_similarity_ratio'),'text_differences_reviewed':diff,'actual_listening':False})
sample_rows=[]
for directory in ['asr-samples','asr-medium']:
    summary=read(N/directory/'summary.json')
    for row in summary['rows']:
        sid=row['scene_id'];s=scenes[sid];individual=read(N/directory/f'{sid}.json');wav_path=N/directory/f'{sid}.wav'
        digest=hashlib.sha256(wav_path.read_bytes()).hexdigest();file_rows[wav_path.relative_to(ROOT).as_posix()]={'path':wav_path.relative_to(ROOT).as_posix(),'sha256':digest,'bytes':wav_path.stat().st_size}
        source=N/'paragraphs'/(s['chapter']+'P01')/'audio.wav'
        with wave.open(str(source),'rb') as w:
            w.setpos(s['start_sample']);expected_pcm=w.readframes(s['end_sample']-s['start_sample']);params=(w.getframerate(),w.getnchannels(),w.getsampwidth())
        with wave.open(str(wav_path),'rb') as w:pcm=w.readframes(w.getnframes());valid_pcm=params==(w.getframerate(),w.getnchannels(),w.getsampwidth()) and pcm==expected_pcm
        valid=row==individual and digest==row['audio_sha256'] and valid_pcm
        if not valid:errors.append([directory,sid,'sample_PCM_or_metadata_mismatch'])
        sample_rows.append({'model_scope':directory,'scene_id':sid,'source_PCM_exact_slice':valid,'seconds':row['seconds'],'numeric_differences':row['comparison']['numeric_differences'],'audio_SHA256':digest})
assert len(rows)==7 and abs(sum(r['seconds'] for r in rows)-679.2)<1e-8
assert full['full_episode_ASR'] is True and full['alignment_sha256']==hashlib.sha256((N/'scene_alignment.json').read_bytes()).hexdigest()
out={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'scope':'기존 로컬 ASR 출력 열람. 새 ASR 실행/모델 다운로드/전송 없음.','full_coverage':{'chapters':7,'seconds':sum(r['seconds'] for r in rows),'model_declared_sha256':full['model_sha256'],'model_binary_rehashed_by_QA':False,'unprompted_configuration_basis':'asr_samples.py의 initial_prompt=None, hotwords=None, local_files_only=True 정적 열람. 저장된 출력에 대한 실행 설정 근거이며 실제 청취 아님.'},'chapters':rows,'samples':sample_rows,'failed_checks':errors,'independent_number_tokens':sum(r['reference_number_count'] for r in rows),'word_review':'모든 차이는 제공된 정규화 문자열로 다시 대조. 전체 문장/수치의 명백한 누락은 발견하지 못함. 비수치 용어 차이는 실제 청취로 확정하지 않음.','possible_manual_listening_targets':[{'scene_id':'S23','cue_id':'P054Q02','source':'규제','ASR':'주제','chapter':'C06','basis':'ASR_full_medium transcript substitution only; actual hearing unchecked'},{'scene_id':'S21','cue_id':'P048Q02','source':'일반과세 중개사의 부가세까지','ASR':'일반과세 중계사에 부과세까지','chapter':'C05','basis':'ASR_full_medium transcript substitution only; actual hearing unchecked'}],'checked_file_hashes':list(file_rows.values()),'actual_listening':False,'continuous_playback':False,'paid_calls_by_QA':0,'external_requests_by_QA':0}
(OWN/'ASR_evidence.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'full_chapters':len(rows),'full_seconds':out['full_coverage']['seconds'],'independent_numbers':out['independent_number_tokens'],'number_counts':[(r['chapter'],r['reference_number_count'],r['ASR_number_count']) for r in rows],'failed':errors,'sample_source_PCM_checks':len(sample_rows)},ensure_ascii=False))
