"""One explicitly authorized free InJoon chunk; only I002. No credentials loaded."""
import asyncio
import copy
import datetime as dt
import difflib
import hashlib
import html
import json
import math
from pathlib import Path
import subprocess
import sys
import wave

DIR = Path(__file__).resolve().parent
OUT = DIR / 'production-v3'
EP = DIR.parents[1]
ROOT = DIR.parents[4]
sys.path.insert(0, str(DIR / 'deps'))
sys.path.insert(0, str(DIR))
import edge_tts
from prepare import parse_sino

FFMPEG = ROOT / 'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
FACTOR = 1.35
REV = 'free-edge-injoon-atempo135-i002clarity-v3'
OVERRIDES = {
    'I002-02': '전체 수 차이는 오십구 쌍이었는데, 초혼 부부는 수원시 영통구가 칠천육백삼십사 쌍, 수원시 권선구는 육천칠백사십육 쌍입니다.',
    'I002-03': '초혼만 놓으면 수원시 영통구가 팔백팔십팔 쌍 더 많아요.',
    'I002-04': '재혼 부부는 수원시 영통구가 칠백삼십삼 쌍이고, 수원시 권선구는 천오백육십삼 쌍으로 방향이 바뀝니다.',
    'I002-05': '이번에는 수원시 권선구가 팔백삼십 쌍 더 많습니다.',
}


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rel(p):
    return str(p.relative_to(ROOT)).replace('\\', '/')


def stamp():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def save(p, obj):
    p.resolve().relative_to(DIR)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf8')


def pcm(p):
    with wave.open(str(p), 'rb') as w:
        assert (w.getframerate(), w.getnchannels(), w.getsampwidth()) == (44100, 1, 2)
        return w.readframes(w.getnframes())


def wav(p, data):
    with wave.open(str(p), 'wb') as w:
        w.setparams((1, 2, 44100, 0, 'NONE', 'not compressed'))
        w.writeframes(data)


def duration(p):
    with wave.open(str(p), 'rb') as w:
        return w.getnframes()/w.getframerate()


def run_ff(args):
    result = subprocess.run([str(FFMPEG), '-hide_banner', '-loglevel', 'error']+args, capture_output=True)
    assert result.returncode == 0, 'Local FFmpeg operation failed'


def norm(s):
    return ''.join(c for c in html.unescape(s) if c.isalnum())


def prepare_inputs():
    OUT.mkdir(exist_ok=True)
    old = read(DIR / 'sentences.json')['sentences']
    rows = []
    for original in [r for r in old if r['scene_id']=='I002']:
        before = original['reading_text']
        after = OVERRIDES.get(original['sentence_id'], before)
        values = []
        for tr in original['numerical_transformations']:
            assert after.count(tr['spoken_text']) == 1
            assert str(parse_sino(tr['spoken_text'].removesuffix(' 쌍'))) == tr['exact_value']
            values.append({'display':tr['source_text'],'reading':tr['spoken_text'],'exact_value':tr['exact_value'],'unit':tr['unit'],'value_unchanged':True,'reading_start':after.index(tr['spoken_text']),'reading_end':after.index(tr['spoken_text'])+len(tr['spoken_text'])})
        changes = [{'operation':tag,'before_start':a,'before_end':b,'after_start':c,'after_end':d,'before':before[a:b],'after':after[c:d]} for tag,a,b,c,d in difflib.SequenceMatcher(None,before,after,autojunk=False).get_opcodes() if tag!='equal']
        rows.append({'sentence_id':original['sentence_id'],'scene_id':'I002','display_text':original['display_text'],'previous_reading_text':before,'reading_text':after,'reading_diff':changes,'numeric_values':values,'claim_ids':original['claim_ids']})
    assert len(rows)==7
    body = '\n'.join(r['reading_text'] for r in rows)
    inputp = OUT/'I002_reading_v3.txt'
    if inputp.exists():
        assert inputp.read_text(encoding='utf8')==body
    else:
        inputp.write_bytes(body.encode('utf8'))
    save(OUT/'reading_inputs_v3.json', {'task':'single_free_I002_clarity_patch','reading_revision':'I002-clarity-v3','script_revision':'top20-production-editorial-v4','display_text_unchanged':True,'source_script_sha256':read(DIR/'timing_proposals_v2.json')['script_sha256'],'provider':'microsoft_edge_consumer_tts','voice':'ko-KR-InJoonNeural','rate':'+0%','atempo_after_generation':FACTOR,'input_characters':len(body),'input_sha256':sha(inputp),'sentences':rows,'mapping_policy':'수원시를 붙인 정식 지명과 조사/접속어는 명시적 읽기문 변환. 화면 지명 약칭·원 수치·7개 문장 ID 유지. ASR 차이를 실제 발음 오류로 단정하지 않음.','pronunciation_display_abbreviation_mapping':[{'reading':'수원시 영통구','display':'영통구'},{'reading':'수원시 권선구','display':'권선구'},{'reading':'쌍이고,','display':'쌍,'}],'generation_limit':'one new free I002 chunk only; no new TTS for other25; no further cycle even if ASR differs','new_paid_calls_authorized':False,'cash_cap_krw':0,'actual_listening_performed':False})
    return rows, body


async def generate_once():
    rows, body = prepare_inputs()
    receiptp = OUT/'generation_receipt.json'
    assert not receiptp.exists(), 'One patch cycle already attempted; do not regenerate'
    frozen_paths = [p for directory in ['free-edge-v1','free-edge-atempo135-v1','production-v2'] for p in (DIR/directory).glob('*') if p.is_file()]
    frozen_paths += [DIR/'timing_proposals_v2.json',DIR/'proposed_timing.json']
    save(OUT/'frozen_previous_inputs.json', {'files':{rel(p):sha(p) for p in frozen_paths}})
    receipt = {'started_at_utc':stamp(),'scene_id':'I002','status':'in_progress','provider':'microsoft_edge_consumer_tts','voice':'ko-KR-InJoonNeural','rate':'+0%','edge_tts_version':edge_tts.__version__,'input_characters':len(body),'input_sha256':sha(OUT/'I002_reading_v3.txt'),'new_generation_chunks':1,'automatic_retry':False,'paid_api_calls':0,'cash_cost_krw':0,'actual_listening_performed':False}
    save(receiptp, receipt)
    raw_mp3 = OUT/'I002_raw.mp3'
    boundaries = []
    try:
        comm = edge_tts.Communicate(body,'ko-KR-InJoonNeural',rate='+0%',boundary='WordBoundary',connect_timeout=15,receive_timeout=35)
        with raw_mp3.open('wb') as f:
            async for item in comm.stream():
                if item['type']=='audio': f.write(item['data'])
                elif item['type'] in ['WordBoundary','SentenceBoundary']:boundaries.append(item)
        assert raw_mp3.stat().st_size>1000 and boundaries
        save(OUT/'I002_provider_boundaries_raw.json', {'units':'100ns ticks','boundaries':boundaries})
        run_ff(['-i',str(raw_mp3),'-ac','1','-ar','44100','-c:a','pcm_s16le','-y',str(OUT/'I002_raw.wav')])
        run_ff(['-i',str(OUT/'I002_raw.wav'),'-af','atempo=1.35','-ac','1','-ar','44100','-c:a','pcm_s16le','-y',str(OUT/'I002.wav')])
        run_ff(['-i',str(OUT/'I002.wav'),'-c:a','libmp3lame','-b:a','128k','-y',str(OUT/'I002.mp3')])
        receipt.update(status='complete',completed_at_utc=stamp(),raw_duration_s=duration(OUT/'I002_raw.wav'),production_duration_s=duration(OUT/'I002.wav'),provider_word_count=len(boundaries),raw_audio_sha256=sha(OUT/'I002_raw.wav'),production_audio_sha256=sha(OUT/'I002.wav'),metadata_sha256=sha(OUT/'I002_provider_boundaries_raw.json'))
        save(receiptp,receipt)
        print(json.dumps(receipt,ensure_ascii=False),flush=True)
    except Exception as e:
        receipt.update(status='failed',error_type=type(e).__name__,safe_reason='Single free I002 patch failed; no automatic retry',completed_at_utc=stamp())
        save(receiptp,receipt)
        print(json.dumps({'status':'failed','scene_id':'I002','error_type':type(e).__name__,'new_generation_chunks':1,'automatic_retry':False,'paid_api_calls':0}),flush=True)
        raise


def assemble():
    inputs=read(OUT/'reading_inputs_v3.json'); rows=inputs['sentences']; receipt=read(OUT/'generation_receipt.json')
    assert receipt['status']=='complete'
    expected=norm('\n'.join(r['reading_text']for r in rows)); cursor=0; words=[]
    for b in read(OUT/'I002_provider_boundaries_raw.json')['boundaries']:
        assert b['type']=='WordBoundary'
        token=norm(b['text'])
        if not token:continue
        assert expected[cursor:cursor+len(token)]==token, (b['text'],cursor)
        words.append({'scene_id':'I002','text':b['text'],'raw_start_s':b['offset']/10000000,'raw_end_s':(b['offset']+b['duration'])/10000000,'local_start_s':b['offset']/10000000/FACTOR,'local_end_s':(b['offset']+b['duration'])/10000000/FACTOR,'normalized_char_start':cursor,'normalized_char_end':cursor+len(token),'timing_basis':'new_provider_word_boundary_divided_by_1.35'})
        cursor+=len(token)
    assert cursor==len(expected)
    char_cursor=0; sentence_times=[]
    for row in rows:
        length=len(norm(row['reading_text']))
        ws=[w for w in words if w['normalized_char_start']<char_cursor+length and w['normalized_char_end']>char_cursor]
        assert ws and ws[0]['normalized_char_start']==char_cursor and ws[-1]['normalized_char_end']==char_cursor+length
        for w in ws:
            w['sentence_id']=row['sentence_id'];w['sentence_normalized_char_start']=w['normalized_char_start']-char_cursor;w['sentence_normalized_char_end']=w['normalized_char_end']-char_cursor
        sentence_times.append({'sentence_id':row['sentence_id'],'text':row['display_text'],'reading_text':row['reading_text'],'start_s':ws[0]['local_start_s'],'end_s':ws[-1]['local_end_s'],'word_count':len(ws),'timing_basis':'new_I002_provider_word_boundary_divided_by_1.35','confidence':'provider_metadata_not_listening_verified'})
        char_cursor+=length
    assert max(w['local_end_s']for w in words)<=receipt['production_duration_s']+0.04
    save(OUT/'I002_sentence_times_local.json',{'audio_revision':REV,'sentences':sentence_times,'actual_listening_performed':False,'asr_performed':False})
    old=read(DIR/'timing_proposals_v2.json'); old_words=read(DIR/'production-v2/words_v2.json')['words'];source_lock=read(EP/'director/top20-production-v1/locked_timing.json')
    changed_index=next(i for i,s in enumerate(old['scenes'])if s['scene_id']=='I002')
    old_duration=old['scenes'][changed_index]['duration_s']; delta=receipt['production_duration_s']-old_duration
    # This remains a narration proposal in the v2 timebase. Parent reapplies hook-before-brand/clean-v7.
    scenes=[]; allwords=[]; paths=[]; body_frames=0
    for original in old['scenes']:
        if original['scene_id']=='E001':continue
        scene=copy.deepcopy(original);start_s=5+body_frames/44100
        if scene['scene_id']=='I002':
            scene.update(audio_path=str((OUT/'I002.wav').resolve()),mp3_path=str((OUT/'I002.mp3').resolve()),audio_sha256=sha(OUT/'I002.wav'),duration_s=receipt['production_duration_s'],reading_text='\n'.join(r['reading_text']for r in rows),sentence_times=sentence_times,reading_revision='I002-clarity-v3',source_v1_audio_sha256=None,replaced_v2_audio_sha256=original['audio_sha256'],timing_basis='actual_new_free_I002_audio_with_scaled_native_provider_words',raw_audio_path=str((OUT/'I002_raw.wav').resolve()))
            localwords=copy.deepcopy(words)
        else:
            assert sha(Path(scene['audio_path']))==scene['audio_sha256']
            localwords=[copy.deepcopy(w)for w in old_words if w['scene_id']==scene['scene_id']]
        scene['start_s']=start_s;scene['end_s']=start_s+scene['duration_s'];scene['audio_revision']=REV
        scene['words_path']=rel(OUT/'words_v3.json')
        scene['sentences']=[{**s,'local_start_s':s['start_s'],'local_end_s':s['end_s'],'start_s':start_s+s['start_s'],'end_s':start_s+s['end_s']}for s in scene['sentence_times']]
        scene['captions']=[{'sentence_id':s['sentence_id'],'text':s['text'],'start_s':s['start_s'],'end_s':s['end_s']}for s in scene['sentences']]
        scene['anchors']={'narration_start':scene['sentence_times'][0]['start_s']}
        for w in localwords:
            w['start_s']=start_s+w['local_start_s'];w['end_s']=start_s+w['local_end_s']
        allwords.extend(localwords);scenes.append(scene);paths.append(Path(scene['audio_path']));body_frames+=len(pcm(paths[-1]))//2
    body_data=b''.join(pcm(p)for p in paths);bodyp=OUT/'narration_body_v3.wav';wav(bodyp,body_data)
    last_spoken=scenes[-1]['sentences'][-1]['end_s'];body_end=5+body_frames/44100;outro_start_frame=max(round(body_end*44100),math.ceil((last_spoken+3)*44100));outro_start=outro_start_frame/44100
    scenes.append({'scene_id':'E001','start_s':body_end,'end_s':outro_start,'duration_s':outro_start-body_end,'audio_path':None,'narration_text':'','sentences':[],'sentence_times':[],'captions':[],'anchors':{},'timing_basis':'last_provider_end_plus_3s_existing_tail_counted_once','is_estimate':False})
    contract=copy.deepcopy(old);contract.update(audio_revision=REV,reading_revision='I002-clarity-v3',timing_locked=False,lock_owner='director',status='I002_only_patch_measured_proposal_parent_must_reapply_hook_and_clean_brand_lock',audio_file=str(bodyp.resolve()),audio_file_time_origin_global_s=5.0,full_brand_audio_file=None,audio_body_duration_s=body_frames/44100,last_spoken_end_s=last_spoken,final_audio_tail_already_counted_s=body_end-last_spoken,additional_silence_after_audio_s=outro_start-body_end,total_duration_with_brand_and_hold_s=outro_start+10,scenes=scenes,word_count=len(allwords),changed_scene_ids=['I002'],newly_generated_scene_ids=['I002'],changed_reading_sentence_ids=list(OVERRIDES),timing_delta_s=delta,reading_inputs_path=rel(OUT/'reading_inputs_v3.json'),reading_inputs_sha256=sha(OUT/'reading_inputs_v3.json'),alignment_basis='new_provider_words_for_I002; prior_provider_scaled_sample_cut_maps_for_other25',tts_calls_this_edit=1,paid_api_calls=0,cash_cost_krw=0,parent_relock_required=True,previous_director_lock_audio_sha256=source_lock['audio_sha256'])
    contract['brand_outro'].update(start_s=outro_start,end_s=outro_start+10)
    contract['time_transform']={'I002':'new provider word ticks /10000000 /1.35 + new scene global start','other25':'unchanged local provider/cut times + recomputed global scene start','atempo_factor':1.35,'character_proportional_alignment_used':False}
    save(DIR/'timing_proposals_v3.json',contract);save(OUT/'timing_proposals_v3.json',contract)
    save(OUT/'words_v3.json',{'audio_revision':REV,'words':allwords,'I002_new_provider_boundaries':True,'other25_provider_local_times_unchanged':True})
    previous=read(OUT/'frozen_previous_inputs.json')['files'];assert all(sha(ROOT/p)==digest for p,digest in previous.items()),'Previous source mutated'
    unchanged=[s for s in scenes if s['scene_id']not in ['I002','E001']];assert len(unchanged)==25
    assert all(sha(Path(s['audio_path']))==s['audio_sha256']for s in unchanged)
    assert sum(len(s['sentences'])for s in scenes)==103
    assert [s['sentence_id']for scene in scenes for s in scene['sentences']]==[s['sentence_id']for scene in old['scenes']for s in scene['sentences']]
    assert all(scene['narration_text']==next(s['narration_text']for s in old['scenes']if s['scene_id']==scene['scene_id'])for scene in scenes)
    run_ff(['-i',str(bodyp),'-f','null','-'])
    verification={'status':'I002_patch_audio_and_provider_mapping_passed_actual_listening_unverified','at_utc':stamp(),'new_free_chunks':1,'new_I002_reading_characters':inputs['input_characters'],'new_I002_raw_duration_s':receipt['raw_duration_s'],'old_I002_duration_s':old_duration,'new_I002_atempo135_duration_s':receipt['production_duration_s'],'timing_delta_s':delta,'body_duration_s':body_frames/44100,'proposed_full_duration_s':outro_start+10,'sentences':103,'I002_sentences':7,'I002_provider_word_count':len(words),'full_provider_word_count':len(allwords),'I002_normalized_reading_coverage':1.0,'cached_other_scene_audio_unchanged':25,'frozen_previous_files_unchanged':len(previous),'numeric_values_checked_unchanged':sum(len(r['numeric_values'])for r in rows),'display_sentences_unchanged':True,'body_audio_sha256':sha(bodyp),'patched_I002_audio_sha256':sha(OUT/'I002.wav'),'atempo_factor':FACTOR,'actual_listening_performed':False,'asr_performed_by_narration':False,'single_patch_cycle_complete':True,'no_further_regeneration':True,'paid_api_calls':0,'cash_cost_krw':0}
    save(OUT/'verification.json',verification)
    save(OUT/'handoff.json',{'task_id':'top20-I002-free-pronunciation-clarity-v3','role':'narration','status':verification['status'],'audio_revision':REV,'input_revisions':{'source_v2_timing_sha256':sha(DIR/'timing_proposals_v2.json'),'reading_inputs_sha256':sha(OUT/'reading_inputs_v3.json'),'script_v4_sha256':old['script_sha256']},'outputs':[rel(DIR/'timing_proposals_v3.json'),rel(bodyp),rel(OUT/'I002.wav'),rel(OUT/'I002_raw.wav'),rel(OUT/'I002_provider_boundaries_raw.json'),rel(OUT/'I002_sentence_times_local.json'),rel(OUT/'reading_inputs_v3.json'),rel(OUT/'words_v3.json'),rel(OUT/'verification.json')],'affected_scene_ids':['I002'],'changed_reading_sentence_ids':list(OVERRIDES),'new_length_s':receipt['production_duration_s'],'timing_delta_s':delta,'proposed_full_length_s':outro_start+10,'checks':[{'check':'7 numeric values / 7 provider-mapped sentences / 25 cached audio hashes / prior files immutable / full PCM decode','result':'passed','evidence':'verification.json'},{'check':'patched actual listening / parent ASR','result':'not_performed_by_narration','evidence':None}],'open_issue_ids':['I002_PRONUNCIATION_LISTENING_UNVERIFIED'],'next_role':'director reruns hook-before-brand clean-v7 timing lock and ASR once, then editor/qa','unresolved':'ASR difference not proof of speech error. New native-provider map is exact to reading text, actual sound unlistened. No second regeneration cycle.','cash_cost_krw':0,'new_free_TTS_chunks':1,'new_paid_api_calls':0})
    files=[p for p in OUT.iterdir()if p.is_file()and p.name!='artifact_manifest.json']+[DIR/'timing_proposals_v3.json']
    save(OUT/'artifact_manifest.json',{'files':[{'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size}for p in files]})
    print(json.dumps(verification,ensure_ascii=False),flush=True)


if __name__=='__main__':
    if sys.argv[1:]==['--generate-once']:asyncio.run(generate_once())
    elif sys.argv[1:]==['--assemble-only']:assemble()
    else:raise SystemExit('Use --generate-once OR --assemble-only; no other generation route')
