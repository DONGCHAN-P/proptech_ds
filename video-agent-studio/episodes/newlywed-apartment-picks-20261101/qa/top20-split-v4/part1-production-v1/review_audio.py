"""독립 PART1 입력·음성 구조 감사. 외부 호출/합성/다른 담당 파일 변경 없음."""
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timezone
import array
import hashlib
import json
import math
import re
import subprocess
import wave

ROOT = Path(__file__).resolve().parents[6]
E = ROOT / 'video-agent-studio/episodes/newlywed-apartment-picks-20261101'
D = E / 'director/top20-split-v4/part1-production-v1'
N = E / 'narration/top20-split-v4/part1-v1'
Q = Path(__file__).resolve().parent

def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def norm(t):
    return ''.join(c.lower() for c in t if c.isalnum())

checks = []
failures = []
def check(name, condition, evidence=None):
    item = dict(check=name, passed=bool(condition), evidence=evidence)
    checks.append(item)
    if not condition:
        failures.append(item)

def sino(s):
    s = re.sub(r'\s+', '', s)
    native = {'쉰세': 53}
    if s in native:
        return native[s]
    digit = dict(zip('영일이삼사오육칠팔구', range(10)))
    small = {'십':10,'백':100,'천':1000}
    total = section = n = 0
    for c in s:
        if c in digit:
            n = digit[c]
        elif c in small:
            section += (n or 1) * small[c]
            n = 0
        elif c in {'만','억'}:
            total += (section+n or 1) * {'만':10000,'억':100000000}[c]
            section = n = 0
        else:
            raise ValueError('unexpected numeral '+s)
    return total + section + n

def money_arabic(s):
    s = s.replace(',', '').replace('원', '')
    total = 0
    if '억' in s:
        a,s = s.split('억')
        total += int(a) * 100000000
    if '만' in s:
        a,s = s.split('만')
        total += int(a) * 10000
    if s:
        total += int(s)
    return total

auth = read(D/'production_authorization.json')
approval = read(D/'script_approval.json')
canonical = read(D/'approved_part1_scene_proposals.json')
lock = read(D/'locked_timing.json')
ledger = read(N/'pronunciation_ledger.json')
sentences = read(N/'sentences.json')['sentences']
manifest = read(N/'narration_manifest.json')
words = read(N/'words.json')['words']
times = read(N/'sentence_times_global.json')['sentences']
verification = read(N/'verification.json')
source_path = ROOT / canonical['source_scene_json']
source = read(source_path)
source_scenes = [s for s in source['scenes'] if s['part'] == 1]
scenes = canonical['scenes']
expected_scenes = ['P01-INTRO'] + [f'P01-R{i}' for i in range(20,10,-1)] + ['P01-OUTRO']
cs = [(s['scene_id'], v['sentence_id'], v['text']) for s in scenes for v in s['sentences']]
byid = {s['sentence_id']:s for s in sentences}
mdpath = ROOT / auth['script_md']
md = mdpath.read_text(encoding='utf-8-sig')
check('canonical_hash_matches_authorization', sha(D/'approved_part1_scene_proposals.json') == auth['scene_json_sha256'])
check('approved_MD_hash', sha(mdpath) == auth['script_md_sha256'] == approval['artifacts'][0]['sha256'])
check('source_hash_matches_prior_script_review', sha(source_path) == canonical['source_scene_json_sha256'] == read(E/'qa/top20-split-v4/script_review.json')['checked_revision']['scene_json_sha256'])
check('derivative_PART1_scene_content_exact_to_source', [{k:v for k,v in s.items() if k!='approval_status'} for s in scenes] == [{k:v for k,v in s.items() if k!='approval_status'} for s in source_scenes], '12개 approval_status만 pending_new_script_gate→approved_part1_only. 승인 receipt와 일치. 문장·화면지시·근거 필드 동일.')
check('derivative_scope_metadata_approved_PART1_only', all(s['approval_status']=='approved_part1_only' for s in scenes) and all(s['approval_status']=='pending_new_script_gate' for s in source_scenes))
check('approval_scope', auth['decision_id'] == approval['id'] == '8c7be2a79904' and auth['status'] == approval['status'] == 'approved' and auth['scope']['part']==1 and auth['scope']['cash_cap_krw']==0 and all(auth['scope'][k] is False for k in ['paid_generation_authorized','part2_authorized','external_file_export_authorized','upload_authorized']))
check('12_scenes_85_unique_sentences_no_PART2', [s['scene_id'] for s in scenes] == expected_scenes and len(cs) == len(sentences) == len(byid) == 85 and all(s['part']==1 for s in scenes))
check('original_and_display_exact', [(s['scene_id'],s['sentence_id'],s['original_text']) for s in sentences] == cs and all(s['original_text']==s['display_text'] for s in sentences))
check('pronunciation_ledger_exact', ledger['sentences'] == sentences)
check('reader_MD_offsets_exact_order', all(md[s['reader_md_char_start']:s['reader_md_char_end']]==s['original_text'] for s in sentences) and all(a['reader_md_char_end']<b['reader_md_char_start'] for a,b in zip(sentences,sentences[1:])))

numerics=[]
transform_n=0
for s in sentences:
    original = s['original_text']
    reading = s['reading_text']
    fwd = original
    reverse = reading
    for t in reversed(s['transformations']):
        check('transform_source_'+s['sentence_id']+'_'+str(t['source_start']), original[t['source_start']:t['source_end']]==t['source_text'] and reading[t['spoken_start']:t['spoken_end']]==t['spoken_text'])
        fwd = fwd[:t['source_start']] + t['spoken_text'] + fwd[t['source_end']:]
        reverse = reverse[:t['spoken_start']] + t['source_text'] + reverse[t['spoken_end']:]
        transform_n+=1
        if re.search(r'\d',t['source_text']):
            src,spoken=t['source_text'],t['spoken_text']
            if src=='10월':
                a,b=10,10 if spoken=='시월' else None
            elif '원' in src:
                a,b=money_arabic(src),sino(spoken.replace('원',''))
            else:
                a,b=int(src.replace(',','')),sino(spoken)
            numerics.append(dict(sentence_id=s['sentence_id'],source=src,reading=spoken,source_value=a,independently_decoded=b,matched=a==b))
    check('reversible_'+s['sentence_id'], fwd==reading and reverse==original)
check('all_numeric_values_independently_decoded', all(v['matched'] for v in numerics), {'expressions':len(numerics)})
check('10월_all_siwol', sum(s['original_text'].count('10월') for s in sentences)==2 and sum(s['reading_text'].count('시월') for s in sentences)==2 and all('십월' not in s['reading_text'] for s in sentences))
aliases={'GTX-A':'지티엑스 에이','e편한':'이편한','G밸리':'지밸리','Y CITY(와이시티)':'와이시티'}
check('explicit_proper_name_aliases', all(all(alias in s['reading_text'] for s in sentences if src in s['original_text']) for src,alias in aliases.items()),aliases)

chunks=manifest['chunks']
check('13_chunks_exact_sentence_order', [i for c in chunks for i in c['sentence_ids']]==[s['sentence_id'] for s in sentences] and len(chunks)==13)
all_native=[]
chunk_evidence=[]
for c in chunks:
    path=ROOT/c['path']
    txt=path.read_text(encoding='utf-8')
    sid=c['asset_id']
    rawmeta=read(N/f'raw/{sid}.boundaries.json')['boundaries']
    rawwords=[b for b in rawmeta if b['type']=='WordBoundary']
    mapped=[w for w in words if w['asset_id']==sid]
    receipt=read(N/f'raw/{sid}.receipt.json')
    check('chunk_text_'+sid,sha(path)==c['sha256'] and txt==c['text'] and norm(txt)==norm(' '.join(byid[i]['reading_text'] for i in c['sentence_ids'])))
    check('native_word_metadata_'+sid, norm(''.join(b['text'] for b in rawwords))==norm(txt) and [b['text'] for b in rawwords]==[w['provider_text'] for w in mapped])
    check('native_times_'+sid,len(rawwords)==len(mapped) and all(abs(w['raw_start_s']-b['offset']/1e7)<1e-8 and abs(w['raw_end_s']-(b['offset']+b['duration'])/1e7)<1e-8 and abs(w['chunk_local_start_s']-w['raw_start_s']/1.35)<1e-8 for b,w in zip(rawwords,mapped)))
    check('raw_receipt_'+sid,receipt['status']=='complete' and receipt['input_sha256']==sha(path) and receipt['paid_api_calls']==receipt['cash_cost_krw']==0 and receipt['voice']=='ko-KR-InJoonNeural')
    all_native.extend(rawwords)
    chunk_evidence.append(dict(asset_id=sid,receipt_sha256=sha(N/f'raw/{sid}.receipt.json'),metadata_sha256=sha(N/f'raw/{sid}.boundaries.json'),native_word_count=len(rawwords)))
check('1277_words_complete',len(all_native)==len(words)==1277 and Counter(w['sentence_id'] for w in words).keys()==byid.keys())
check('word_display_and_MD_offsets',all(byid[w['sentence_id']]['display_text'][w['display_char_start']:w['display_char_end']]==w['display_text'] and md[w['reader_md_char_start']:w['reader_md_char_end']]==w['display_text'] for w in words))
check('word_global_order',all(w['start_s']<w['end_s'] for w in words) and all(a['start_s']<=b['start_s'] for a,b in zip(words,words[1:])))
check('85_global_sentence_times',len(times)==85 and [s['sentence_id'] for s in times]==list(byid) and all(t['text']==byid[t['sentence_id']]['original_text'] and t['reading_text']==byid[t['sentence_id']]['reading_text'] for t in times))
for s in sentences:
    ws=[w for w in words if w['sentence_id']==s['sentence_id']]
    check('sentence_provider_coverage_'+s['sentence_id'],norm(''.join(w['provider_text'] for w in ws))==norm(s['reading_text']))

check('timing_lock_hash',sha(D/'locked_timing.json')=='a4a9efe64e87a329917b5b1dc3d6d7c4285f5c16ff6b05555b4a357dc2ceecf5')
check('lock_audio_script_hashes',lock['audio_sha256']==sha(ROOT/lock['audio_path']) and lock['source_scene_json_sha256']==sha(D/'approved_part1_scene_proposals.json'))
check('lock_scene_order', [s['scene_id'] for s in lock['scenes']]==expected_scenes)
check('lock_sentence_identity',[(s['scene_id'],v['sentence_id'],v['text']) for s in lock['scenes'] for v in s['sentences']]==cs)
captions=lock['captions']
capgroups=defaultdict(list)
for c in captions:
    capgroups[c['sentence_id']].append(c)
check('176_semantic_cues_original_reconstruction',len(captions)==176 and set(capgroups)==set(byid) and all(norm(''.join(c['text'] for c in capgroups[sid]))==norm(s['original_text']) for sid,s in byid.items()))
check('caption_times_nonoverlap',all(c['start_s']<c['end_s'] for c in captions) and all(a['end_s']<=b['start_s']+1e-6 for a,b in zip(captions,captions[1:])))

audio_path=ROOT/lock['audio_path']
def pcm(p):
    with wave.open(str(p),'rb') as w:
        params=(w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes())
        return params,w.readframes(w.getnframes())
params,fullpcm=pcm(audio_path)
channels,width,sr,nframes=params
check('actual_WAV_format_duration',channels==1 and width==2 and sr==44100 and abs(nframes/sr-lock['total_s'])<1/sr,dict(channels=channels,sample_width_bytes=width,sample_rate=sr,frames=nframes,duration_s=nframes/sr,bytes=audio_path.stat().st_size))
pcm_evidence=[]
for r in verification['full_processed_PCM_preservation']:
    pp,chunkpcm=pcm(N/f"processed/{r['asset_id']}.wav")
    a,b=r['global_frames']
    passed=chunkpcm==fullpcm[a*width*channels:b*width*channels]
    check('processed_full_PCM_'+r['asset_id'],passed)
    pcm_evidence.append(dict(asset_id=r['asset_id'],global_frames=[a,b],independently_compared_exact=passed,pcm_sha256=hashlib.sha256(chunkpcm).hexdigest()))
brand_evidence=[]
for b in lock['brand_inserts']:
    bp,bpcm=pcm(b['source_file'])
    start=round(b['start_s']*sr)
    match=bpcm==fullpcm[start*2:start*2+len(bpcm)]
    occurrences=fullpcm.count(bpcm)
    check('brand_once_PCM_'+b['kind'],match and occurrences==1 and sha(b['source_file'])==b['sha256'])
    brand_evidence.append(dict(kind=b['kind'],start_s=b['start_s'],duration_s=b['duration_s'],full_PCM_exact=match,full_PCM_occurrences=occurrences))
last=max(w['end_s'] for w in words)
outro=next(b['start_s'] for b in lock['brand_inserts'] if b['kind']=='outro')
check('last_native_word_then_3s_hold',outro-last>=3 and outro-last<3+1/sr,dict(last_provider_word_end_s=last,outro_start_s=outro,gap_s=outro-last,acoustic_endpoint='unchecked; provider metadata is not listening'))
samples=array.array('h',fullpcm)
peak=max(abs(v) for v in samples)
rms=math.sqrt(sum(v*v for v in samples)/len(samples))
check('PCM_activity_no_integer_clipping',peak>0 and peak<32767,dict(peak=peak,peak_dbfs=20*math.log10(peak/32768),rms=rms,rms_dbfs=20*math.log10(rms/32768),scope='signal measurement only; audibility/naturalness unverified'))
decoder=ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
decoded=subprocess.run([str(decoder),'-v','error','-xerror','-i',str(audio_path),'-f','null','-'],capture_output=True,text=True)
(Q/'audio_decode.stderr.txt').write_text(decoded.stderr,encoding='utf-8')
check('actual_full_WAV_strict_decode',decoded.returncode==0,dict(exit_code=decoded.returncode,stderr_file=str(Q/'audio_decode.stderr.txt')))

reuse=[]
for name in ['script_review.json','map_data_review.json','map_revision_v3_review.json']:
    p=E/'qa/top20-split-v4'/name
    reuse.append(dict(path=str(p),sha256=sha(p),scope='기존 승인 전 가격/출처/지도 검수의 해당 불변 입력에만 재사용. 새 음성/MP4 검사로 확대하지 않음.'))
frozen=[]
for r in canonical['input_revisions']:
    p=ROOT/r['path']
    matched=p.is_file() and sha(p)==r['sha256']
    check('frozen_input_'+r['key'],matched)
    frozen.append(dict(key=r['key'],path=str(p),sha256=sha(p) if p.is_file() else None,expected_sha256=r['sha256'],matched=matched))

paths=[Path(__file__),D/'production_authorization.json',D/'script_approval.json',D/'approved_part1_scene_proposals.json',D/'locked_timing.json',N/'produce.py',N/'approval_receipt.json',N/'narration_manifest.json',N/'pronunciation_ledger.json',N/'sentences.json',N/'reading_text.txt',N/'words.json',N/'sentence_times_global.json',N/'narration_with_clean_brand.wav',N/'verification.json',N/'integrity_audit.json']
input_hashes=[dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size) for p in paths]
report=dict(task_id='part1-independent-audio-script-v1',generated_at=datetime.now(timezone.utc).isoformat(),reviewer='independent_QA_role',status='passed_bounded_audio_text_metadata' if not failures else 'required_findings_open',checked_revision=dict(canonical_sha256=sha(D/'approved_part1_scene_proposals.json'),locked_timing_sha256=sha(D/'locked_timing.json'),audio_sha256=sha(audio_path)),counts=dict(scenes=12,sentences=85,chunks=13,native_words=1277,caption_cues=176,explicit_transformations=transform_n,independently_decoded_numeric_expressions=len(numerics),checks=len(checks),failed_checks=len(failures)),coverage=dict(manually_read_original_reading_pairs=85,script_original_display_reading_reversibility='checked_all',numbers_dates_units_proper_names='checked_text_and_native_provider_metadata',price_research='hash_pinned_prior_QA_reuse_no_reaggregation',actual_WAV='full_PCM_read_and_strict_decode',actual_listening=False,continuous_playback=False,ASR='parent_owned_pending; not duplicated',naturalness='unchecked',phonetic_endpoint_sync='unchecked; boundaries are provider metadata scaled by fixed 1.35',MP4_pixel_review='pending_parent_actual_encoded_frames',Claude_review='not_called_no_external_transfer',part2='not_generated_or_reviewed; approved_PART1_outro_teaser_preserved'),required_open_count=0 if not failures else len(failures),critical_open_count=0,required_issues=[],findings=[],failed_checks=failures,checks_file=str(Q/'audio_script_checks.json'),numeric_evidence_file=str(Q/'numeric_decode_evidence.json'),inputs=input_hashes,prior_QA_reuse=reuse,frozen_input_hashes=frozen,chunk_provider_evidence=chunk_evidence,PCM_preservation=pcm_evidence,brand_evidence=brand_evidence,local_delivery_decision='audio/text bounded pass only; final MP4 independent reviewer decision pending' if not failures else 'hold',cash_cost_krw=0,network_calls=0,paid_calls=0,external_messages_sent=0,modified_scope=str(Q))
(Q/'audio_script_checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
(Q/'numeric_decode_evidence.json').write_text(json.dumps(numerics,ensure_ascii=False,indent=2),encoding='utf-8')
(Q/'audio_script_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(Q/'findings.json').write_text(json.dumps([],ensure_ascii=False,indent=2),encoding='utf-8')
handoff=dict(task_id=report['task_id'],status=report['status'],outputs=[str(Q/'audio_script_review.json'),str(Q/'audio_script_checks.json'),str(Q/'numeric_decode_evidence.json'),str(Q/'findings.json')],input_versions=report['checked_revision'],validation=report['counts'],unresolved=['actual_listening_unchecked','continuous_playback_unchecked','parent_ASR_pending','actual_MP4_frames_pending'],affected_scenes=expected_scenes,next_owner='director: ASR evidence and actual MP4/encoded frame packet; QA: extend final_review.json',required_open_count=report['required_open_count'],critical_open_count=0)
(Q/'handoff.json').write_text(json.dumps(handoff,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(status=report['status'],counts=report['counts'],failures=failures,output=str(Q/'audio_script_review.json')),ensure_ascii=False))
