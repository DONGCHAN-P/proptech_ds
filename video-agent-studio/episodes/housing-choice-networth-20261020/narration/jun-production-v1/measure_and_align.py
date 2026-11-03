"""로컬 PCM/공급자 문자 정렬을 기존206 의미 단위 자막에 연결. TTS/네트워크 호출 없음."""
from pathlib import Path
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
import re
import wave
import numpy as np

OWN=Path(__file__).resolve().parent
EP=OWN.parents[1]
ROOT=EP.parents[2]
RATE=44100
FRAME=RATE//30
SCRIPT_SHA='0368c9e08b8a2447ed429d9e78ab9a8238b2d823c27467362174600876a797b7'
PHONETIC_SHA='ea636bf3e07e4fa73fd7dbb25f04e89c38aec191cad02abf3de309af6fbd72a7'
PREP=EP/'narration/free-tts-v1/prepare-v6/prepared.json'
OLD_TIMING=EP/'narration/free-tts-v1/caption-v7/final_timing.json'


def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return sha256(Path(p).read_bytes()).hexdigest()
def text_sha(s):return sha256(s.encode('utf-8')).hexdigest()
def rel(p):return Path(p).relative_to(ROOT).as_posix()
def save(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def compact(s):return re.sub(r'\s+','',s)
def read_pcm(p):
    with wave.open(str(p),'rb') as w:
        assert w.getnchannels()==1 and w.getsampwidth()==2 and w.getframerate()==RATE
        return np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').copy()
def write_pcm(p,data):
    with wave.open(str(p),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(RATE);w.writeframes(data.astype('<i2',copy=False).tobytes())
def signal_bounds(data):
    hits=np.flatnonzero(np.abs(data.astype(np.int32))>=32768*10**(-60/20))
    assert len(hits)>0, '무신호 PCM'
    return int(hits[0])/RATE,(int(hits[-1])+1)/RATE
def spoken_offset(p,offset):
    for span in p['display_mapping']:
        if offset==span['source_start']:return span['spoken_start']
        if offset==span['source_end']:return span['spoken_end']
        if span['source_start']<offset<span['source_end']:
            assert span['kind']=='literal', '숫자/단위 중간 자막 경계 금지'
            return span['spoken_start']+offset-span['source_start']
    raise ValueError('표시 원문 위치 대응 없음')
def as_srt(t):
    ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'


ledger=load(OWN/'generation_ledger.json')
assert ledger['status']=='all54_generated_measured_alignment_validated_not_listened'
assert len(ledger['requests'])==54 and all(x['status']=='complete' for x in ledger['requests'])
assert ledger['actual_credits']==sum(x['actual_credits'] for x in ledger['requests'])<=10739
assert ledger['submitted_characters']==8949 and ledger['automatic_retries']==0
assert sha(EP/'outputs/script-final-v6/script_v6.md')==SCRIPT_SHA
assert sha(EP/'narration/jun-replacement-v1/pronunciation_proposal.json')==PHONETIC_SHA
prepared=load(PREP)
old=load(OLD_TIMING)
assert old['script_sha256']==prepared['script_sha256']==SCRIPT_SHA
assert sum(len(c['cues']) for c in old['chapters'])==206
receipts={x['paragraph_id']:x for x in ledger['requests']}
chapters=[];paragraph_checks=[];cue_checks=[];mapping_rows=[];all_words=[]
body_frames=0;caption_rows=[];deltas=[];padding_rows=[]
for chapter in prepared['chapters']:
    n=int(chapter['chapter']);scene=f'C{n:02}';old_ch=next(c for c in old['chapters'] if c['chapter']==n)
    lead=.6 if n==1 else 3.5
    cursor=round(lead*RATE)
    chunks=[np.zeros(cursor,dtype='<i2')]
    new_paragraphs=[];cue_rows=[];provider_ends=[];pcm_ends=[];chapter_words=[]
    for p in chapter['paragraphs']:
        pid=p['paragraph_id'];receipt=receipts[pid];base=OWN/'paragraphs'/pid
        for name,digest in receipt['artifact_sha256'].items():assert sha(OWN/name)==digest
        pcm=read_pcm(base/'audio.wav');duration=len(pcm)/RATE
        assert duration==receipt['pcm_duration_s'] and len(pcm)==receipt['pcm_samples']
        a=load(base/'alignment.json');normal=load(base/'normalized_alignment.json')
        text=p['spoken_text'];assert a['characters']==list(text) and ''.join(a['characters'])==receipt['request']['text']==text
        starts=np.asarray(a['character_start_times_seconds']);ends=np.asarray(a['character_end_times_seconds'])
        assert len(starts)==len(ends)==len(text)
        assert np.isfinite(starts).all() and np.isfinite(ends).all()
        assert (starts>=0).all() and (ends>=starts).all() and (np.diff(starts)>=0).all() and (np.diff(ends)>=0).all()
        assert ends.max()<=duration+.1
        if normal is not None:
            assert len(normal['characters'])==len(normal['character_start_times_seconds'])==len(normal['character_end_times_seconds'])
        first_signal,last_signal=signal_bounds(pcm)
        nonspace=[i for i,c in enumerate(text) if not c.isspace()]
        provider_first=float(min(starts[i] for i in nonspace))
        provider_last=float(max(ends[i] for i in nonspace))
        overhang=max(0,math.ceil(provider_last*RATE)-len(pcm))
        offset=cursor/RATE
        chunks.append(pcm);cursor+=len(pcm)
        if overhang:
            chunks.append(np.zeros(overhang,dtype='<i2'));cursor+=overhang
            padding_rows.append({'paragraph_id':pid,'decoded_pcm_s':duration,'provider_last_end_s':provider_last,'added_silence_samples':overhang,
                                 'reason':'공급자 정렬이 디코딩 끝보다 늦음. 원본/정렬 보존, 장 연결에서 해당 차이만 무음으로 확보.'})
        provider_ends.append(offset+provider_last);pcm_ends.append(offset+last_signal)
        words=[]
        for word_index,match in enumerate(re.finditer(r'\S+',text)):
            row={'word_index':word_index,'text':match.group(),'spoken_start':match.start(),'spoken_end':match.end(),
                 'start_s':float(starts[match.start()])+offset,'end_s':float(max(ends[match.start():match.end()]))+offset,
                 'timing_basis':'exact provider character alignment grouped at whitespace; not ASR'}
            words.append(row)
        for row in words:chapter_words.append({**row,'paragraph_id':pid,'paragraph':p['paragraph']})
        local_cues=[q for q in old_ch['cues'] if int(q['paragraph'])==p['paragraph']]
        for q in local_cues:
            ss,se=q['source_start'],q['source_end'];assert p['text'][ss:se]==q['text']
            bs,be=spoken_offset(p,ss),spoken_offset(p,se)
            assert text[bs:be]==q['spoken_text']
            use=[i for i in range(bs,be) if not text[i].isspace()]
            assert use
            s=float(min(starts[i] for i in use))+offset;e=float(max(ends[i] for i in use))+offset
            assert s<e
            word_indices=[i for i,w in enumerate(words) if w['spoken_start']<be and w['spoken_end']>bs]
            lines=q.get('display_lines') or [q['text']]
            assert 1<=len(lines)<=2 and compact(''.join(lines))==compact(q['text'])
            row={k:v for k,v in q.items() if k not in ('start_s','end_s','native_start_s','native_end_s','first_word_index','last_word_index','timing_basis')}
            row.update(start_s=s,end_s=e,native_start_s=s,native_end_s=e,first_word_index=min(word_indices),last_word_index=max(word_indices),
                       spoken_start=bs,spoken_end=be,paragraph_id=pid,display_lines=lines,
                       timing_basis='actual ElevenLabs Jun exact character alignment mapped through frozen v6 display/spoken spans; existing caption-v7 segmentation')
            cue_rows.append(row)
            cue_checks.append({'id':row['id'],'text_exact':True,'spoken_exact':True,'segmentation_preserved':True,
                               'alignment_path':rel(base/'alignment.json'),'spoken_start':bs,'spoken_end':be,'native_start_s':s,'native_end_s':e})
        meta={'paragraph':p['paragraph'],'paragraph_id':pid,'chapter_paragraph':p['chapter_paragraph'],'offset_s':offset,
              'start_s':offset,'end_s':offset+duration+overhang/RATE,'raw_pcm_end_s':offset+duration,
              'paragraph_end_basis':'raw decoded PCM plus explicit provider-alignment overhang padding; end_s is padded slot end',
              'measured_seconds':duration,'pcm_frames':len(pcm),'wave_file':rel(base/'audio.wav'),'wave_sha256':sha(base/'audio.wav'),
              'last_native_word_end_s':offset+provider_last,'last_pcm_signal_end_s':offset+last_signal,
              'first_provider_character_start_s':offset+provider_first,'first_pcm_signal_start_s':offset+first_signal,
              'speech_start_s':offset+min(provider_first,first_signal),'speech_end_s':offset+max(provider_last,last_signal),
              'speech_boundary_basis':'provider nonspace character times and PCM threshold -60dBFS; actual listening not performed',
              'alignment_overhang_padding_s':overhang/RATE,'padded_slot_seconds':duration+overhang/RATE,
              'provider_alignment':rel(base/'alignment.json'),'provider_alignment_sha256':sha(base/'alignment.json'),
              'normalized_alignment':rel(base/'normalized_alignment.json'),'normalized_alignment_sha256':sha(base/'normalized_alignment.json'),
              'display_text_sha256':text_sha(p['text']),'spoken_text_sha256':text_sha(text),'actual_listening':False}
        new_paragraphs.append(meta)
        mapping_rows.append({'paragraph_id':pid,'paragraph':p['paragraph'],'scene_id':scene,'text':p['text'],'spoken_text':text,
                             'display_mapping':p['display_mapping'],'source_start':p['source_start'],'source_end':p['source_end'],
                             'display_text_sha256':text_sha(p['text']),'spoken_text_sha256':text_sha(text)})
        signal=pcm.astype(np.float64)/32768
        paragraph_checks.append({'paragraph_id':pid,'decoded_seconds':duration,'pcm_samples':len(pcm),'provider_alignment_exact':True,
                                 'provider_alignment_characters':len(text),'normalized_alignment_exact':normal is not None and ''.join(normal['characters'])==text,
                                 'provider_first_s':provider_first,'provider_last_s':provider_last,'signal_first_s':first_signal,'signal_last_s':last_signal,
                                 'peak_dbfs':float(20*np.log10(max(np.max(np.abs(signal)),1e-15))),
                                 'rms_dbfs':float(20*np.log10(max(np.sqrt(np.mean(signal**2)),1e-15))),
                                 'saturated_samples':int((np.abs(pcm.astype(np.int32))>=32767).sum()),'actual_listening':False})
        if p!=chapter['paragraphs'][-1]:
            gap=round(.35*RATE);chunks.append(np.zeros(gap,dtype='<i2'));cursor+=gap
    speech_end=max(max(provider_ends),max(pcm_ends))
    desired=max(cursor,math.ceil((speech_end+(3 if n==10 else 1.2))*RATE))
    total_frames=math.ceil(desired/FRAME)*FRAME
    chunks.append(np.zeros(total_frames-cursor,dtype='<i2'))
    chapter_pcm=np.concatenate(chunks)
    assert len(chapter_pcm)==total_frames
    file=OWN/f'chapter_{n:02}.wav';write_pcm(file,chapter_pcm)
    prior_end=0
    for q in cue_rows:
        assert prior_end<=q['start_s']<q['end_s']<=total_frames/RATE,(q['id'],prior_end,q['start_s'])
        prior_end=q['end_s']
    assert total_frames/RATE-speech_end >= (3 if n==10 else 1.2)-1e-9
    row={'chapter':n,'scene_id':scene,'title':chapter['title'],'audio_file':rel(file),'audio_sha256':sha(file),
         'total_seconds':total_frames/RATE,'pcm_frames':total_frames,'sample_rate':RATE,'channels':1,'sample_width_bytes':2,
         'last_speech_end_s':speech_end,'last_speech_end_basis':'max(nonspace provider character end, last decoded PCM sample >= -60dBFS); unlistened signal evidence',
         'last_native_word_end_s':max(provider_ends),'last_pcm_signal_end_s':max(pcm_ends),'leading_silence_s':lead,'paragraph_gap_s':.35,
         'tail_from_last_spoken_s':total_frames/RATE-speech_end,'cues':cue_rows,'paragraphs':new_paragraphs,'listening':'not_performed',
         'body_offset_s':body_frames/RATE,'body_offset_frames':body_frames,'timing_basis':'actual provider character alignment and measured PCM; not estimate'}
    chapters.append(row)
    all_words.append({'chapter':n,'words':chapter_words})
    save(OWN/f'chapter_{n:02}.words.json',all_words[-1])
    for q in cue_rows:caption_rows.append({**q,'chapter':n,'body_start_s':q['start_s']+body_frames/RATE,'body_end_s':q['end_s']+body_frames/RATE})
    deltas.append({'scene_id':scene,'changed_paragraph_ids':[p['paragraph_id'] for p in chapter['paragraphs']],
                   'changed_sentences':[p['text'] for p in chapter['paragraphs']], 'script_text_changed':False,'voice_changed':True,
                   'previous_seconds':old_ch['total_seconds'],'new_seconds':total_frames/RATE,'timing_delta_s':total_frames/RATE-old_ch['total_seconds']})
    body_frames+=total_frames
body=OWN/'body_mono.wav'
with wave.open(str(body),'wb') as w:
    w.setnchannels(1);w.setsampwidth(2);w.setframerate(RATE)
    for c in chapters:w.writeframes(read_pcm(ROOT/c['audio_file']).tobytes())
assert len(caption_rows)==206
assert [q['id'] for q in caption_rows]==[q['id'] for c in old['chapters'] for q in c['cues']]
input_lock=load(OWN/'input_lock.json')
asr_path=OWN/'asr-numeric-samples/summary.json'
asr=load(asr_path) if asr_path.exists() else None
timing={'script_path':rel(EP/'outputs/script-final-v6/script_v6.md'),'script_sha256':SCRIPT_SHA,'script_revision':'script-final-v6',
        'voice':{'name':'Jun - Clear Korean Lecturer','voice_id':'4p6UA7mnodF5q7JFFrnW','provider':'elevenlabs','model':'eleven_v4','speed':.97,
                 'voice_settings':{'stability':.6,'similarity_boost':.95,'speed':.97}},
        'audio_revision':'jun-production-v1','chapters':chapters,'status':'generated_measured_character_aligned_not_listened',
        'source_mapping':rel(OWN/'display_spoken_mapping.json'),'gate_evidence':input_lock,
        'media_contract_sha256':old['media_contract_sha256'],'previous_audio_revision':'production-injoon-v6','actual_listening':False,
        'ASR_QA_performed':False,'local_ASR_samples_performed':asr is not None,'local_ASR_scope':asr['sampled_paragraph_ids'] if asr else [],
        'paid_api_calls':54,'timing_scope':'per-chapter local time; body_offset_s excludes brand inserts; editor establishes final film global offsets',
        'caption_revision':'caption-v7-segmentation-on-Jun-v1','caption_renderer_contract':old['caption_renderer_contract'],
        'caption_scope':'existing206 cue IDs, original text and display_lines retained; every cue timed from actual Jun provider characters',
        'body_audio_file':rel(body),'body_audio_sha256':sha(body),'body_seconds':body_frames/RATE,'body_pcm_frames':body_frames,'sample_rate':RATE,
        'body_last_speech_end_s':chapters[-1]['body_offset_s']+chapters[-1]['last_speech_end_s'],'created_at_utc':datetime.now(timezone.utc).isoformat()}
save(OWN/'display_spoken_mapping.json',{'script_sha256':SCRIPT_SHA,'phonetic_manifest_sha256':PHONETIC_SHA,'grounding_manifest_sha256':sha(PREP),
                                      'offset_unit':'Unicode code points','paragraphs':mapping_rows})
save(OWN/'final_timing.json',timing)
save(OWN/'alignment_padding.json',{'policy':'공급자 정렬 원본 불변, 최대100ms 이내 디코딩 끝 초과분은 장 결합 때만 무음 추가. 보간·속도변경·발음수정 없음.', 'paragraphs':padding_rows})
save(OWN/'timing_delta.json',{'changed_scene_ids':[x['scene_id'] for x in deltas],'script_changed':False,'audio_revision':'jun-production-v1',
                             'previous_body_seconds':sum(c['total_seconds'] for c in old['chapters']),'new_body_seconds':body_frames/RATE,
                             'timing_delta_s':body_frames/RATE-sum(c['total_seconds'] for c in old['chapters']),'scenes':deltas})
save(OWN/'timing_proposals.json',{'audio_revision':'jun-production-v1','timing_basis':'actual measured Jun PCM + exact provider alignment','director_timing_lock_pending':True,
                                 'scenes':[{'scene_id':c['scene_id'],'start_s':c['body_offset_s'],'end_s':c['body_offset_s']+c['total_seconds'],
                                            'timing_basis':'actual measured body PCM; excludes intro/outro/brand inserts','confidence':'measured_not_listened','audio_revision':'jun-production-v1'} for c in chapters]})
save(OWN/'captions_body.json',{'scope':'body-only offsets; final film offsets are editor-owned','cues':caption_rows})
srt=[]
for i,q in enumerate(caption_rows,1):srt.append(f'{i}\n{as_srt(q["body_start_s"])} --> {as_srt(q["body_end_s"])}\n'+ '\n'.join(q['display_lines'])+'\n')
(OWN/'captions_body.srt').write_text('\n'.join(srt),encoding='utf-8')
save(OWN/'technical_validation.json',{'status':'passed_technical_only_not_listened','script_sha256':SCRIPT_SHA,'final_timing_sha256':sha(OWN/'final_timing.json'),
                                    'chapters':10,'paragraphs':54,'cues':206,'body_seconds':body_frames/RATE,'body_audio_sha256':sha(body),
                                    'paragraph_checks':paragraph_checks,'cue_checks':cue_checks,'all206_segmentation_preserved':True,
                                    'saturated_samples':sum(p['saturated_samples'] for p in paragraph_checks),'actual_listening':False,'ASR_performed':asr is not None,
                                    'ASR_scope':asr['sampled_paragraph_ids'] if asr else [],'full_episode_ASR':False,
                                    'warnings':['공급자 character-cost 비용과 계정 사용량 즉시 반영은 다를 수 있어 별도 원장으로 보존.',
                                                '자막은 공급자 문자 정렬 기반이며 음향 정답/자연스러움 검증을 뜻하지 않음.'],
                                    'code_sha256':sha(Path(__file__))})
print(json.dumps({'status':'measured_and_aligned','chapters':10,'paragraphs':54,'cues':206,'body_seconds':body_frames/RATE,
                  'final_timing':rel(OWN/'final_timing.json'),'body_mono':rel(body),'actual_listening':False},ensure_ascii=False))
