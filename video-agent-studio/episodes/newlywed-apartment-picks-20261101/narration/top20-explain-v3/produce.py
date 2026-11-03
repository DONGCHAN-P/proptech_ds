"""Approved v6 only: free Edge once, frozen raw words, local 1.35x audio.

All writes stay beside this script. No credentials, paid providers, ASR or uploads.
"""
from __future__ import annotations

import argparse
import asyncio
import audioop
import datetime as dt
from decimal import Decimal
import hashlib
import html
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import wave

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
EP = OUT.parents[1]
ROOT = OUT.parents[4]
OLD = EP / 'narration/top20-production-v1'
SCRIPT = EP / 'writer/top20-explain-v3/script_v6.md'
SCENES = EP / 'writer/top20-explain-v3/scene_proposals_v6.json'
APPROVAL = EP / 'director/top20-explain-v3/script_approval.json'
AUTH = EP / 'director/top20-explain-v3/production_authorization.json'
EDITOR = EP / 'editor/top20-explain-v3/input_contract.json'
OLD_LOCK = EP / 'director/top20-enhance-v2/locked_timing.json'
INTRO = EP / 'director/top20-production-v1/locked-audio/intro_clean_v7.wav'
OUTRO = EP / 'director/top20-production-v1/locked-audio/outro_clean_v7.wav'
FFMPEG = ROOT / 'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
MD_SHA = '4259f50a9c5cadbadd864d838559a16f85e07316818ddcb31ce40939fbccac38'
SCENE_SHA = '8beec59448e180617327f17913aaa25277b3152769a1815cbdc493351003803e'
VOICE, RATE, FACTOR, SR = 'ko-KR-InJoonNeural', '+0%', 1.35, 44100
REV = 'top20-explain-v3-v6-free-edge-injoon-atempo135'
DIGITS = '영일이삼사오육칠팔구'
NATIVE = {1:'한',2:'두',3:'세',4:'네',5:'다섯',6:'여섯',7:'일곱',8:'여덟',9:'아홉',10:'열',11:'열한',12:'열두',13:'열세',14:'열네',15:'열다섯',16:'열여섯',17:'열일곱',18:'열여덟',19:'열아홉',20:'스무',22:'스물두',35:'서른다섯',53:'쉰세'}
NATIVE_DECODE = {'한':1,'두':2,'세':3,'네':4,'다섯':5,'여섯':6,'일곱':7,'여덟':8,'아홉':9,'열':10,'열한':11,'열두':12,'열세':13,'열네':14,'열다섯':15,'열여섯':16,'열일곱':17,'열여덟':18,'열아홉':19,'스무':20,'스물두':22,'서른다섯':35,'쉰세':53}


def stamp(): return dt.datetime.now(dt.timezone.utc).isoformat()
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p): return p.resolve().relative_to(ROOT).as_posix()
def digest(text): return hashlib.sha256(text.encode('utf-8')).hexdigest()


def save(p, data):
    p.resolve().relative_to(OUT)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + '.tmp')
    tmp.write_bytes((json.dumps(data, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))
    tmp.replace(p)


def write_text(p, text):
    p.resolve().relative_to(OUT)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(text.encode('utf-8'))
    assert p.read_text(encoding='utf-8') == text


def sino(n):
    # Value generator follows the existing prepare.py pronounce() number policy.
    if n == 0: return '영'
    pieces = []
    for value, label in [(100000000,'억'),(10000,'만')]:
        if n >= value:
            top, n = divmod(n, value)
            pieces.append(sino(top)+label)
    small = ''
    for value, label in [(1000,'천'),(100,'백'),(10,'십'),(1,'')]:
        top, n = divmod(n,value)
        if top: small += ('' if top == 1 and value > 1 else DIGITS[top])+label
    if small: pieces.append(small)
    return ' '.join(pieces)


def decode_number(text):
    """Separate parser, used against produced readings, not the generator."""
    text = text.replace(' ','')
    if text in NATIVE_DECODE: return NATIVE_DECODE[text]
    total, block, digit = 0, 0, 0
    for c in text:
        if c in DIGITS: digit = DIGITS.index(c)
        elif c in '십백천':
            block += (digit or 1)*{'십':10,'백':100,'천':1000}[c]
            digit = 0
        elif c in '만억':
            total += (block+digit or 1)*{'만':10000,'억':100000000}[c]
            block, digit = 0, 0
        else: raise ValueError(('unknown number phoneme',c))
    return total+block+digit


def number_reading(source, native=False):
    plain = source.replace(',','')
    if '.' in plain:
        whole, frac = plain.split('.')
        spoken = sino(int(whole))+' 점 '+' '.join(DIGITS[int(c)] for c in frac)
        decoded = Decimal(decode_number(spoken.split(' 점 ')[0]))+Decimal('0.'+''.join(str(DIGITS.index(c)) for c in spoken.split(' 점 ')[1].replace(' ','')))
    else:
        value = int(plain)
        spoken = NATIVE.get(value, sino(value)) if native else sino(value)
        decoded = Decimal(decode_number(spoken))
    assert decoded == Decimal(plain)
    return spoken, str(Decimal(plain)), str(decoded)


SPECIAL = {
    '10월':'시월',
    'Y CITY(와이시티)':'와이시티', 'Y CITY':'와이시티',
    'GTX-A':'지티엑스 에이', 'G밸리':'지밸리', 'G타워':'지타워',
    'e편한':'이편한', '중위값':'중윗값',
    '잠실2·3단지':'잠실 이 단지와 삼 단지',
    '제2·3판교테크노밸리':'제이 판교테크노밸리와 제삼 판교테크노밸리',
    '83~85㎡':'팔십삼에서 팔십오 제곱미터',
    '㎡':'제곱미터', '·':', ', '(':' ', ')':' ', '~':'에서 ', '%':'퍼센트',
}
TOKEN = re.compile('|'.join(re.escape(s) for s in sorted(SPECIAL,key=len,reverse=True))+r'|\d[\d,]*(?:\.\d+)?억(?:\d[\d,]*(?:\.\d+)?만)?원|\d[\d,]*(?:\.\d+)?만원|\d[\d,]*(?:\.\d+)?')


def pronounce(original):
    parts, transforms, spans, cursor, spoken_pos = [], [], [], 0, 0
    for m in TOKEN.finditer(original):
        unchanged = original[cursor:m.start()]
        if unchanged:
            parts.append(unchanged)
            spans.append({'source_start':cursor,'source_end':m.start(),'reading_start':spoken_pos,'reading_end':spoken_pos+len(unchanged),'kind':'identity'})
            spoken_pos += len(unchanged)
        surface = m[0]
        values = []
        if surface in SPECIAL:
            replacement = SPECIAL[surface]
            reason = 'explicit_name_or_symbol_pronunciation'
            if surface == '10월':
                # Standard Korean calendar allomorph; independent lexical month table.
                values = [{'source_value':'10','decoded_value':str({'시월':10}[replacement]),'unit':'calendar_month'}]
                reason = 'standard_calendar_month_allomorph_10_to_siwol'
            elif surface == '잠실2·3단지': values = [{'source_value':'2','decoded_value':str(decode_number('이'))},{'source_value':'3','decoded_value':str(decode_number('삼'))}]
            elif surface.startswith('제2·3'): values = [{'source_value':'2','decoded_value':str(decode_number('이'))},{'source_value':'3','decoded_value':str(decode_number('삼'))}]
            elif surface == '83~85㎡': values = [{'source_value':'83','decoded_value':str(decode_number('팔십삼'))},{'source_value':'85','decoded_value':str(decode_number('팔십오'))}]
        elif surface.endswith('원'):
            match = re.fullmatch(r'(?:(\d[\d,]*(?:\.\d+)?)억)?(?:(\d[\d,]*(?:\.\d+)?)만)?원',surface)
            assert match
            eok, man = (Decimal(x.replace(',','')) if x else Decimal(0) for x in match.groups())
            source_value = eok*100000000+man*10000
            spoken_parts = []
            if eok: spoken_parts.append(sino(int(eok))+' 억')
            if man: spoken_parts.append(sino(int(man))+' 만')
            replacement = ' '.join(spoken_parts)+' 원'
            decoded = decode_number(replacement.removesuffix(' 원'))
            assert source_value == Decimal(decoded)
            values = [{'source_value':str(source_value),'decoded_value':str(decoded),'unit':'KRW'}]
            reason = 'whole_money_expression_value_preserved'
        else:
            native = original[m.end():].startswith(('건','개'))
            replacement, value, decoded = number_reading(surface,native)
            # Explicit spacing aids Korean number/counter separation.
            if m.end() < len(original) and (original[m.end()].isalnum()): replacement += ' '
            values = [{'source_value':value,'decoded_value':decoded,'unit':'number'}]
            reason = 'numeric_counter_or_identifier_value_preserved'
        assert all(Decimal(v['source_value']) == Decimal(v['decoded_value']) for v in values)
        transform = {'source_start':m.start(),'source_end':m.end(),'source_text':surface,'spoken_start':spoken_pos,'spoken_end':spoken_pos+len(replacement),'spoken_text':replacement,'reason':reason,'independent_values':values,'value_preserved':True}
        transforms.append(transform)
        spans.append({'source_start':m.start(),'source_end':m.end(),'reading_start':spoken_pos,'reading_end':spoken_pos+len(replacement),'kind':'explicit_transform'})
        parts.append(replacement)
        spoken_pos += len(replacement)
        cursor = m.end()
    if cursor < len(original):
        parts.append(original[cursor:])
        spans.append({'source_start':cursor,'source_end':len(original),'reading_start':spoken_pos,'reading_end':spoken_pos+len(original)-cursor,'kind':'identity'})
    reading = ''.join(parts)
    restored = reading
    for t in reversed(transforms):
        assert restored[t['spoken_start']:t['spoken_end']] == t['spoken_text']
        restored = restored[:t['spoken_start']]+t['source_text']+restored[t['spoken_end']:]
    assert restored == original, 'original display roundtrip failed'
    assert not re.search(r'[0-9A-Za-z㎡·~%()]',reading), reading
    assert '?' not in reading, 'unexpected question-mark corruption'
    return reading, transforms, spans


def inspect(p):
    with wave.open(str(p),'rb') as w:
        rate, channels, width, count = w.getframerate(),w.getnchannels(),w.getsampwidth(),w.getnframes()
        assert (rate,channels,width) == (SR,1,2)
        pcm = w.readframes(count)
    assert len(pcm) == count*2
    peak, rms = audioop.max(pcm,2), audioop.rms(pcm,2)
    hop = 441
    frames = [audioop.rms(pcm[i:i+hop*2],2) for i in range(0,len(pcm),hop*2)]
    silent = [v < 184 for v in frames]  # -45 dBFS, 10ms windows
    leading = next((i for i,x in enumerate(silent) if not x),len(silent))*.01
    trailing = next((i for i,x in enumerate(reversed(silent)) if not x),len(silent))*.01
    longest, run = 0, 0
    for x in silent:
        run = run+1 if x else 0
        longest = max(longest,run)
    return {'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size,'frames':count,'duration_s':count/SR,'sample_rate':rate,'channels':channels,'sample_width_bytes':width,'peak_pcm':peak,'peak_dbfs':20*math.log10(peak/32768) if peak else None,'rms_pcm':rms,'rms_dbfs':20*math.log10(rms/32768) if rms else None,'leading_silence_s':round(leading,3),'trailing_silence_s':round(trailing,3),'max_silent_run_s':round(longest*.01,3),'silent_window_fraction':sum(silent)/len(silent),'silence_threshold_dbfs':-45,'silence_window_s':.01,'clip_peak_reached':peak>=32767}


def ff(args):
    result = subprocess.run([str(FFMPEG),'-hide_banner','-loglevel','error']+args,capture_output=True)
    if result.returncode:
        raise RuntimeError('Local ffmpeg failed: '+result.stderr.decode('utf-8',errors='replace')[-700:])


def authorization():
    assert sha(SCRIPT) == MD_SHA and sha(SCENES) == SCENE_SHA
    for p in [APPROVAL,AUTH]:
        a = read(p)
        assert a['script_md_sha256'] == MD_SHA and a['scene_json_sha256'] == SCENE_SHA
        assert a['text'] == '이대로 진행해줘' and a['cash_cap_krw'] == 0 and a['paid_generation_authorized'] is False
    return {'script_md_sha256':MD_SHA,'scene_json_sha256':SCENE_SHA,'script_approval_path':rel(APPROVAL),'script_approval_sha256':sha(APPROVAL),'production_authorization_path':rel(AUTH),'production_authorization_sha256':sha(AUTH),'approval_overrides_draft_narration_ready':True,'canonical_source_unchanged':True}


def prepare():
    auth = authorization()
    doc = read(SCENES)
    rows, chunks = [], []
    md_rows = re.findall(r'^\*\*\[([^\]]+)\]\*\* (.+)$',SCRIPT.read_text(encoding='utf-8-sig'),re.M)
    source_rows = [(t['sentence_id'],t['text']) for s in doc['scenes'] for t in s['sentences']]
    assert md_rows == source_rows and len(source_rows) == 133
    assert sum(bool(s.get('region_id')) for s in doc['scenes']) == 20
    for scene in doc['scenes']:
        local = []
        for t in scene['sentences']:
            reading, transforms, spans = pronounce(t['text'])
            row = {'scene_id':scene['scene_id'],'sentence_id':t['sentence_id'],'original_text':t['text'],'display_text':t['text'],'reading_text':reading,'writer_reading_reference':t.get('reading_text'),'transformations':transforms,'character_mapping':spans,'display_roundtrip_exact':True,'claim_ids':t.get('claim_ids',[]),'price_role':t.get('price_role'),'statement_type':t.get('statement_type'),'screen_switch_id':t.get('screen_switch_id'),'actual_listening':False}
            rows.append(row)
            local.append(row)
        if not local: continue
        body = '\n'.join(r['reading_text'] for r in local)
        path = OUT/'chunks'/(scene['scene_id']+'.txt')
        write_text(path,body)
        asset_id = scene['scene_id']+('-month-v2' if any('10월' in r['display_text'] for r in local) else '')
        chunks.append({'scene_id':scene['scene_id'],'asset_id':asset_id,'path':rel(path),'sha256':sha(path),'text':body,'characters':len(body),'sentence_ids':[r['sentence_id'] for r in local]})
    inputs = {rel(p):sha(p) for p in [SCRIPT,SCENES,APPROVAL,AUTH,EDITOR,OLD_LOCK,INTRO,OUTRO,OLD/'prepare.py',OLD/'generate_free.py',OLD/'build_audio_contract.py',OLD/'build_sentence_cut_v2.py',OLD/'deps/edge_tts/communicate.py',FFMPEG]}
    save(OUT/'approval_receipt.json',{**auth,'recorded_at':stamp(),'scope':'확정 v6 원문 전체 무료 Edge TTS; paid0 cash0; 완료/업로드 승인 별도','voice':VOICE,'rate':RATE,'atempo':FACTOR,'original_narration_ready':doc['narration_ready'],'script_gate_draft_flags_unchanged':True})
    save(OUT/'sentences.json',{'script_revision':'v6','script_sha256':MD_SHA,'sentences':rows})
    save(OUT/'pronunciation_ledger.json',{'source_sha256':MD_SHA,'scene_json_sha256':SCENE_SHA,'policy':'발음 변환만 별도 기록; source/display 원문 복원 및 독립 숫자값 확인. 원고 수정 없음.','reference_prepare_sha256':sha(OLD/'prepare.py'),'explicit_name_symbol_rules':SPECIAL,'sentences':[{k:r[k] for k in ['scene_id','sentence_id','display_text','reading_text','transformations','character_mapping','display_roundtrip_exact']} for r in rows],'transformation_count':sum(len(r['transformations']) for r in rows),'numeric_value_count':sum(len(t['independent_values']) for r in rows for t in r['transformations']),'actual_pronunciation_listened':False})
    manifest = {'task_id':'TOP20-explain-v3-narration','created_at':stamp(),'script_revision':'v6','audio_revision':REV,'approval':auth,'input_versions':inputs,'chunks':chunks,'sentence_count':len(rows),'region_count':20,'spoken_scene_count':len(chunks),'characters':sum(c['characters'] for c in chunks),'provider':'microsoft_edge_consumer_tts','voice':VOICE,'rate':RATE,'postprocess_atempo':FACTOR,'paid_api_calls':0,'cash_cost_krw':0,'credentials_loaded':False,'automatic_retry':False,'old_timing_fallback':False,'ASR_owner':'parent/independent QA; do not duplicate','utf8_roundtrip_checked':True}
    save(OUT/'narration_manifest.json',manifest)
    write_text(OUT/'reading_text.txt','\n\n'.join(c['text'] for c in chunks))
    print(json.dumps({k:manifest[k] for k in ['sentence_count','region_count','spoken_scene_count','characters','utf8_roundtrip_checked']},ensure_ascii=False),flush=True)


def norm(text): return ''.join(c for c in html.unescape(text) if c.isalnum())


async def stream_no_retry(comm):
    """Same installed stream contract, deliberately omit its automatic 403 retry."""
    assert not comm.state['stream_was_called']
    comm.state['stream_was_called'] = True
    for comm.state['partial_text'] in comm.texts:
        comm.state['chunk_audio_bytes'] = 0
        async for event in comm._Communicate__stream():
            yield event


async def generate_chunk(chunk, edge_tts):
    sid = chunk['scene_id']
    asset_id = chunk.get('asset_id',sid)
    raw = OUT/'raw'; raw.mkdir(exist_ok=True)
    receipt_path = raw/(asset_id+'.receipt.json')
    fingerprint = digest(json.dumps({'text_sha256':chunk['sha256'],'voice':VOICE,'rate':RATE,'volume':'+0%','pitch':'+0Hz','boundary':'WordBoundary','edge_tts_version':edge_tts.__version__,'communicate_sha256':sha(OLD/'deps/edge_tts/communicate.py'),'auto_retry':False},sort_keys=True))
    if receipt_path.exists():
        old = read(receipt_path)
        assert old['status']=='complete' and old['generation_input_sha256']==fingerprint, 'Existing failed/incomplete/different attempt; no automatic retry: '+sid
        assert all(sha(ROOT/v['path'])==v['sha256'] for v in old['outputs'].values())
        return old
    body = (ROOT/chunk['path']).read_text(encoding='utf-8')
    assert body == chunk['text'] and digest(body)==chunk['sha256']
    receipt = {'scene_id':sid,'status':'in_progress','started_at':stamp(),'input_sha256':chunk['sha256'],'generation_input_sha256':fingerprint,'voice':VOICE,'rate':RATE,'edge_tts_version':edge_tts.__version__,'characters':len(body),'automatic_retry':False,'provider_403_retry_disabled':True,'paid_api_calls':0,'cash_cost_krw':0,'credentials_loaded':False}
    save(receipt_path,receipt)
    mp3, metadata, wav = raw/(asset_id+'.mp3'),raw/(asset_id+'.boundaries.json'),raw/(asset_id+'.wav')
    boundaries = []
    try:
        comm = edge_tts.Communicate(body,VOICE,rate=RATE,volume='+0%',pitch='+0Hz',boundary='WordBoundary',connect_timeout=15,receive_timeout=35)
        with mp3.open('wb') as f:
            async for event in stream_no_retry(comm):
                if event['type']=='audio': f.write(event['data'])
                elif event['type'] in ['WordBoundary','SentenceBoundary']: boundaries.append({k:v for k,v in event.items() if k!='data'})
        save(metadata,{'scene_id':sid,'units':'100ns ticks','boundaries':boundaries})
        assert mp3.stat().st_size>1000 and boundaries
        ff(['-i',str(mp3),'-ac','1','-ar',str(SR),'-c:a','pcm_s16le','-y',str(wav)])
        info = inspect(wav)
        assert info['rms_pcm']>0 and not info['clip_peak_reached']
        receipt.update(status='complete',completed_at=stamp(),duration_s=info['duration_s'],boundary_count=len(boundaries),outputs={key:{'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size} for key,p in [('mp3',mp3),('metadata',metadata),('wav',wav)]},actual_listening=False)
        save(receipt_path,receipt)
        return receipt
    except Exception as e:
        save(metadata,{'scene_id':sid,'units':'100ns ticks','boundaries':boundaries,'incomplete':True})
        receipt.update(status='failed',completed_at=stamp(),error_type=type(e).__name__,os_error=getattr(e,'errno',None),http_status=getattr(e,'status',None),safe_reason='무료 Edge 연결/합성/로컬 디코드 실패. 자동 재시도 없음.',bytes_received=mp3.stat().st_size if mp3.exists() else 0)
        save(receipt_path,receipt)
        print(json.dumps({'scene_id':sid,'status':'failed','error_type':type(e).__name__,'http_status':getattr(e,'status',None)},ensure_ascii=False),flush=True)
        raise


async def generate(which):
    authorization()
    manifest = read(OUT/'narration_manifest.json')
    sys.path.insert(0,str(OLD/'deps'))
    import edge_tts
    selected = manifest['chunks'][:3] if which=='first3' else manifest['chunks'][3:]
    # First scenes are sequential for a stable early handoff; later two at a time.
    for offset in range(0,len(selected),1 if which=='first3' else 2):
        batch = selected[offset:offset+(1 if which=='first3' else 2)]
        results = await asyncio.gather(*(generate_chunk(c,edge_tts) for c in batch),return_exceptions=True)
        failures = [type(r).__name__ for r in results if isinstance(r,BaseException)]
        if failures:
            save(OUT/'generation_failure.json',{'at':stamp(),'scene_ids':[c['scene_id'] for c in batch],'errors':failures,'automatic_retry':False,'remaining_scenes_not_started':True})
            raise RuntimeError('Stopped at failed batch; no retry: '+str(failures))
    print(json.dumps({'stage':which,'completed_scenes':len(selected),'paid_api_calls':0,'cash_cost_krw':0},ensure_ascii=False),flush=True)


def pcm(p):
    with wave.open(str(p),'rb') as w:
        assert (w.getnchannels(),w.getframerate(),w.getsampwidth())==(1,SR,2)
        return w.readframes(w.getnframes())


def write_wav(p,data):
    p.resolve().relative_to(OUT);p.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(p),'wb') as w:
        w.setparams((1,2,SR,0,'NONE','not compressed'));w.writeframes(data)


def source_range(row, start, end):
    spans = [s for s in row['character_mapping'] if s['reading_start']<end and s['reading_end']>start]
    assert spans
    bounds = []
    for s in spans:
        if s['kind']=='identity': bounds.append((s['source_start']+max(start-s['reading_start'],0),s['source_start']+min(end-s['reading_start'],s['reading_end']-s['reading_start'])))
        else: bounds.append((s['source_start'],s['source_end']))
    lo, hi = min(x[0] for x in bounds),max(x[1] for x in bounds)
    return lo,hi,row['display_text'][lo:hi]


def align(chunk,rows):
    sid = chunk['scene_id']
    asset_id = chunk.get('asset_id',sid)
    receipt = read(OUT/'raw'/(asset_id+'.receipt.json'))
    assert receipt['status']=='complete' and receipt['input_sha256']==chunk['sha256']
    assert all(sha(ROOT/v['path'])==v['sha256'] for v in receipt['outputs'].values())
    expected, cursor, words = norm(chunk['text']),0,[]
    # Provider normalized offsets are mapped back through exact reading/display spans.
    reading_positions = [i for i,c in enumerate(chunk['text']) if c.isalnum()]
    sentence_ranges, at, reading_at = [],0,0
    for r in rows:
        size = len(norm(r['reading_text']))
        sentence_ranges.append((at,at+size,reading_at,r))
        at += size; reading_at += len(r['reading_text'])+1
    for b in read(ROOT/receipt['outputs']['metadata']['path'])['boundaries']:
        assert b['type']=='WordBoundary'
        token = norm(b['text'])
        if not token: continue
        assert expected[cursor:cursor+len(token)]==token,(sid,b['text'],expected[cursor:cursor+30])
        end = cursor+len(token)
        found = [(a,z,p,r) for a,z,p,r in sentence_ranges if a<=cursor<z]
        assert len(found)==1
        a,z,p,row = found[0]
        assert end<=z, 'provider token crosses sentence'
        rs,re_ = reading_positions[cursor]-p,reading_positions[end-1]+1-p
        ds,de,display = source_range(row,rs,re_)
        raw_start,raw_end = b['offset']/1e7,(b['offset']+b['duration'])/1e7
        assert 0<=raw_start<raw_end<=receipt['duration_s']+.03
        assert not words or raw_start>=words[-1]['raw_end_s']-.000001
        words.append({'scene_id':sid,'sentence_id':row['sentence_id'],'text':html.unescape(b['text']),'provider_text':b['text'],'reading_text':row['reading_text'][rs:re_],'display_text':display,'reading_char_start':rs,'reading_char_end':re_,'display_char_start':ds,'display_char_end':de,'normalized_char_start':cursor,'normalized_char_end':end,'raw_start_s':raw_start,'raw_end_s':raw_end,'local_start_s':raw_start/FACTOR,'local_end_s':raw_end/FACTOR,'timing_basis':'provider_word_boundary_divided_by_1.35','display_span_policy':'transformed multiword values may map multiple provider tokens to the same protected display span'})
        cursor=end
    assert cursor==len(expected), (sid,'incomplete word coverage')
    out = OUT/'processed'/(asset_id+'.wav')
    out.parent.mkdir(exist_ok=True)
    build_receipt = out.with_suffix('.receipt.json')
    build_input = digest(json.dumps({'raw_wav_sha256':sha(ROOT/receipt['outputs']['wav']['path']),'ffmpeg_sha256':sha(FFMPEG),'factor':FACTOR,'sr':SR,'channels':1,'width':2},sort_keys=True))
    if build_receipt.exists():
        old=read(build_receipt)
        assert old['input_sha256']==build_input and sha(out)==old['output_sha256']
    else:
        ff(['-i',str(ROOT/receipt['outputs']['wav']['path']),'-af','atempo=1.35','-ac','1','-ar',str(SR),'-c:a','pcm_s16le','-y',str(out)])
        save(build_receipt,{'input_sha256':build_input,'output_sha256':sha(out),'factor':FACTOR})
    info=inspect(out);raw_info=inspect(ROOT/receipt['outputs']['wav']['path'])
    assert info['rms_pcm']>0 and not info['clip_peak_reached']
    assert max(w['local_end_s'] for w in words)<=info['duration_s']+.04
    sentence_times=[]
    for row in rows:
        matched=[w for w in words if w['sentence_id']==row['sentence_id']]
        assert norm(''.join(w['text'] for w in matched))==norm(row['reading_text'])
        sentence_times.append({'sentence_id':row['sentence_id'],'text':row['display_text'],'display_text':row['display_text'],'reading_text':row['reading_text'],'start_s':matched[0]['local_start_s'],'end_s':matched[-1]['local_end_s'],'local_start_s':matched[0]['local_start_s'],'local_end_s':matched[-1]['local_end_s'],'raw_start_s':matched[0]['raw_start_s'],'raw_end_s':matched[-1]['raw_end_s'],'word_count':len(matched),'price_role':row['price_role'],'statement_type':row['statement_type'],'screen_switch_id':row['screen_switch_id'],'timing_basis':'actual_provider_first_last_word_boundary_scaled_by_1.35','confidence':'provider_metadata_scaled_not_listening_verified'})
    syllables=sum('가'<=c<='힣' for c in chunk['text'])
    spoken_span=words[-1]['local_end_s']-words[0]['local_start_s']
    metrics={'scene_id':sid,'raw_audio':raw_info,'processed_audio':info,'normalized_reading_coverage':1.0,'word_count':len(words),'sentence_count':len(rows),'hangul_syllables':syllables,'syllables_per_total_s':syllables/info['duration_s'],'syllables_per_provider_speech_span_s':syllables/spoken_span,'max_sentence_syllables_per_span_s':max(sum('가'<=c<='힣' for c in s['reading_text'])/(s['end_s']-s['start_s']) for s in sentence_times),'tempo_sample_delta_from_ideal_s':info['duration_s']-raw_info['duration_s']/FACTOR,'provider_final_word_to_decoded_end_s':info['duration_s']-words[-1]['local_end_s'],'intelligibility_verdict':'unverified; rate/signal/coverage are measured proxies, not listening or ASR','actual_listening':False}
    save(OUT/'processed'/(asset_id+'.metrics.json'),metrics)
    return {'scene_id':sid,'audio_path':str(out),'audio_sha256':sha(out),'raw_audio_path':str(ROOT/receipt['outputs']['wav']['path']),'raw_mp3_path':str(ROOT/receipt['outputs']['mp3']['path']),'provider_boundaries_path':receipt['outputs']['metadata']['path'],'duration_s':info['duration_s'],'frames':info['frames'],'narration_text':'\n'.join(r['display_text'] for r in rows),'reading_text':chunk['text'],'sentence_times':sentence_times,'words':words,'metrics':metrics}


def build(partial=False):
    auth=authorization();manifest=read(OUT/'narration_manifest.json');rows=read(OUT/'sentences.json')['sentences']
    chosen=manifest['chunks'][:3] if partial else manifest['chunks']
    intro,outro=inspect(INTRO),inspect(OUTRO)
    assert intro['duration_s']==5 and outro['duration_s']==10
    old_lock=read(OLD_LOCK)
    brand_sources=old_lock['brand_visuals']
    assert len(brand_sources)==2
    for b in brand_sources: assert sha(ROOT/b['path'])==b['sha256']
    measured=[align(c,[r for r in rows if r['scene_id']==c['scene_id']]) for c in chosen]
    position=0;scenes=[];words=[];parts=[];body_frames=0
    intro_start=None
    for m in measured:
        start=position/SR
        duration=m['frames']/SR
        scene={k:v for k,v in m.items() if k not in ['words','metrics','frames']}
        scene.update(start_s=start,end_s=start+duration,duration_s=duration,audio_revision=REV,timing_basis='actual_audio',alignment_basis='new_provider_word_boundaries_scaled_by_1.35',confidence='measured_samples_and_provider_metadata_not_listening_verified',is_estimate=False,actual_listening=False,actual_listening_performed=False,timing_locked=False)
        scene['sentences']=[{**s,'start_s':start+s['local_start_s'],'end_s':start+s['local_end_s']} for s in m['sentence_times']]
        scene['captions']=[{'sentence_id':s['sentence_id'],'text':s['text'],'start_s':s['start_s'],'end_s':s['end_s']} for s in scene['sentences']]
        scene['anchors']={'narration_start':m['sentence_times'][0]['start_s']}
        scene['words_path']=rel(OUT/('partial_words.json' if partial else 'words.json'))
        for word in m['words']: words.append({**word,'start_s':start+word['local_start_s'],'end_s':start+word['local_end_s'],'audio_revision':REV})
        scenes.append(scene);parts.append(pcm(Path(m['audio_path'])));body_frames+=m['frames'];position+=m['frames']
        if m['scene_id']=='O001':
            intro_start=position/SR
            parts.append(pcm(INTRO));position+=intro['frames']
    full_end=position/SR;last_word=words[-1]['end_s']
    suffix='partial_' if partial else ''
    audio_path=OUT/('partial_first3_with_clean_intro_v6.wav' if partial else 'narration_with_clean_brand_v6.wav')
    if not partial:
        assert len(rows)==133 and len(measured)==25
        outro_frame=math.ceil((last_word+3)*SR)
        assert outro_frame>=position, 'Raw final tail exceeds 3-second hold; do not append duplicate silence'
        extra=outro_frame-position
        parts.append(b'\0\0'*extra)
        outro_start=outro_frame/SR
        scenes.append({'scene_id':'E001','start_s':full_end,'end_s':outro_start,'duration_s':outro_start-full_end,'audio_path':None,'narration_text':'','reading_text':'','sentences':[],'sentence_times':[],'captions':[],'anchors':{},'timing_basis':'actual_provider_last_word_end_plus_3s_existing_tail_counted_once','confidence':'provider_metadata_not_listening_verified','audio_revision':REV,'is_estimate':False,'actual_listening':False})
        parts.append(pcm(OUTRO));position=outro_frame+outro['frames']
    else: outro_start=None;extra=None
    write_wav(audio_path,b''.join(parts))
    audio_info=inspect(audio_path)
    ff(['-i',str(audio_path),'-f','null','-'])
    assert audio_info['frames']==position and not audio_info['clip_peak_reached'] and audio_info['rms_pcm']>0
    word_path=OUT/(suffix+'words.json')
    save(word_path,{'audio_revision':REV,'script_sha256':MD_SHA,'scene_json_sha256':SCENE_SHA,'word_count':len(words),'normalized_reading_coverage':1.0,'units':'seconds','time_semantics':'start/end global from full audio0; local_start/end from decoded processed scene WAV0; raw_start/end from raw provider ticks /1e7','alignment_basis':'raw provider WordBoundary ticks divided by1.35; measured processed sample counts determine scene starts','character_proportional_alignment_used':False,'atempo_phoneme_sync_error_s':None,'actual_listening':False,'words':words})
    brand_visuals=[]
    for b in brand_sources:
        start=intro_start if b['id']=='brand_intro' else outro_start
        brand_visuals.append({**b,'start_s':start,'end_s':None if start is None else start+b['duration_s'],'inherited_from':rel(OLD_LOCK)})
    contract={'schema_revision':'top20-narration-contract-v1','task_id':'TOP20-explain-v3-narration','status':'partial_first3_measured_ready' if partial else 'all_audio_measured_proposal_pending_director_lock_and_independent_QA','script_revision':'v6','script_sha256':MD_SHA,'scene_json_sha256':SCENE_SHA,'approval_receipt':rel(OUT/'approval_receipt.json'),'audio_revision':REV,'timing_locked':False,'lock_owner':'director','timing_basis':'actual_audio','is_estimate':False,'duration_is_actual':True,'alignment_basis':'new_native_provider_word_boundaries_scaled_by_1.35','character_proportional_alignment_used':False,'old_timing_fallback_used':False,'provider':'microsoft_edge_consumer_tts','voice':VOICE,'edge_rate':RATE,'postprocess_atempo_factor':FACTOR,'actual_listening':False,'actual_listening_performed':False,'asr_performed':False,'asr_owner':'parent/independent QA, no duplicate ASR by narration','audio_file':str(audio_path),'full_brand_audio_file':str(audio_path),'audio_sha256':sha(audio_path),'audio_file_time_origin_global_s':0,'full_brand_audio_file_time_origin_global_s':0,'words_file':rel(word_path),'words_file_sha256':sha(word_path),'audio_body_duration_s':body_frames/SR,'body_audio_is_contiguous':False,'body_audio_note':'O001, clean intro5s, O002 onward. All scenes have individual WAVs.','last_spoken_end_s':last_word,'last_spoken_end_basis':'actual provider last WordBoundary /1.35; not actual listening','final_audio_tail_already_counted_s':full_end-last_word,'required_hold_from_last_spoken_s':3,'additional_silence_after_audio_s':extra/SR if extra is not None else None,'brand_intro':{**intro,'audio_path':str(INTRO),'path':brand_sources[0]['path'],'start_s':intro_start,'end_s':intro_start+5},'brand_outro':{**outro,'audio_path':str(OUTRO),'path':brand_sources[1]['path'],'start_s':outro_start,'end_s':None if outro_start is None else outro_start+10},'brand_visuals':brand_visuals,'clean_brand_source':'existing approved clean v7; intro after O001; no brand narration','total_duration_with_brand_and_hold_s':position/SR,'scenes':scenes,'scene_id_count':len(scenes),'sentence_count':sum(len(s['sentence_times']) for s in scenes),'word_count':len(words),'time_semantics':'scene start/end and scenes.sentences/words start/end global seconds; sentence_times start/end/local_start/local_end scene-local seconds; brand inserts5s after O001.','changed_scene_ids':[m['scene_id'] for m in measured],'changed_sentence_ids':[r['sentence_id'] for r in rows if r['scene_id'] in {m['scene_id'] for m in measured}],'timing_delta_s':None,'timing_delta_basis':'new approved v6 full reading; no old timing fallback or equivalent same-script baseline','paid_api_calls':0,'cash_cost_krw':0}
    timing_path=OUT/(suffix+'timing_proposals.json');save(timing_path,contract)
    validation={'at':stamp(),'status':'technical_checks_passed_listening_and_independent_QA_pending','input_sha_verified':auth,'script_MD_scene_sentence_order_exact':True,'sentence_count':contract['sentence_count'],'region_count':20 if not partial else 1,'word_count':len(words),'normalized_provider_reading_coverage':1.0,'every_sentence_has_native_provider_words':True,'display_roundtrip_exact':True,'audio':audio_info,'full_decode_passed':True,'audio_clipping_detected':False,'last_spoken_end_s':last_word,'outro_start_s':outro_start,'outro_minus_provider_last_word_s':outro_start-last_word if outro_start is not None else None,'extra_silence_after_audio_s':contract['additional_silence_after_audio_s'],'target_duration_enforced':False,'speed_policy':'approved +0% followed by fixed atempo1.35; no target-length padding','time_transform_accuracy_limit':'provider word times are analytically scaled; atempo internal phonetic displacement has not been independently measured','metrics':[m['metrics'] for m in measured],'actual_listening':False,'asr_performed':False,'asr_deferred_to':'parent/independent QA per latest instruction','paid_api_calls':0,'cash_cost_krw':0}
    verification_path=OUT/(suffix+'verification.json');save(verification_path,validation)
    handoff={'task_id':'TOP20-explain-v3-narration','role':'narration','status':contract['status'],'created_at':stamp(),'input_revisions':{'script_revision':'v6','script_md_sha256':MD_SHA,'scene_json_sha256':SCENE_SHA,'approval_sha256':sha(APPROVAL),'authorization_sha256':sha(AUTH),'manifest_sha256':sha(OUT/'narration_manifest.json')},'outputs':[rel(p) for p in [audio_path,timing_path,word_path,verification_path,OUT/'pronunciation_ledger.json',OUT/'approval_receipt.json']],'audio_path':rel(audio_path),'audio_sha256':sha(audio_path),'timing_path':rel(timing_path),'words_path':rel(word_path),'words_sha256':sha(word_path),'new_length_s':position/SR,'affected_scene_ids':[s['scene_id'] for s in scenes],'changed_sentence_ids':contract['changed_sentence_ids'],'timing_delta_s':None,'timing_delta_note':'new v6 whole reading; compare only against approved lock after director integration','checks':[{'check':'exact SHA, UTF8 roundtrip, display restoration, numeric independent values, native wordcoverage, decoded PCM peak/RMS/silence','result':'passed','evidence':rel(verification_path)},{'check':'actual listening / ASR / independent QA / timing lock','result':'pending_other_roles','evidence':None}],'open_issue_ids':[] if partial else ['AUDIO_V6_LISTENING_AND_INDEPENDENT_QA_PENDING'],'next_role':'director locks timing; editor integrates; parent/independent QA does local ASR/listening','actual_listening':False,'unverified_scope':'all actual sound pronunciation/naturalness and atempo phonetic sync; ASR not run here','paid_api_calls':0,'cash_cost_krw':0,'reproduction':'tools/python311/python.exe -X utf8 '+rel(OUT/'produce.py')+' prepare; generate-first3; build-first3; generate-rest; build-final (each is a separate subcommand; complete same-input provider receipts reuse verified files, failed receipts never auto retry)'}
    handoff_path=OUT/('partial_handoff.json' if partial else 'handoff.json');save(handoff_path,handoff)
    if not partial:
        save(OUT/'issue_AUDIO_V6_LISTENING_AND_INDEPENDENT_QA_PENDING.json',{'issue_id':'AUDIO_V6_LISTENING_AND_INDEPENDENT_QA_PENDING','scene_ids':[m['scene_id'] for m in measured],'problem':'실제 청취·독립QA 미수행. atempo 후 음소 경계 오차는 미측정.','evidence':rel(verification_path),'proposal':'parent/독립QA가 캐시 로컬ASR와 실제청취 후 판단; 총괄 timing lock, editor 최종 통합.','impact':'생성/신호/wordcoverage 완료. 자연스러움·발음·최종 영상 승인으로 확대하지 않음.','next_role':['director','editor','qa']})
        files=[p for p in OUT.rglob('*') if p.is_file() and p.name not in ['artifact_manifest.json','completion_receipt.json'] and p.suffix!='.tmp']
        artifacts=[{'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(files)]
        save(OUT/'artifact_manifest.json',{'created_at':stamp(),'files':artifacts})
        save(OUT/'completion_receipt.json',{'status':'complete_technical_narration_scope','at':stamp(),'input_sha256':digest(json.dumps(manifest['input_versions'],sort_keys=True)),'code_sha256':sha(Path(__file__)),'artifact_manifest_sha256':sha(OUT/'artifact_manifest.json'),'script_md_sha256':MD_SHA,'scene_json_sha256':SCENE_SHA,'audio_sha256':sha(audio_path),'sentence_count':133,'spoken_scene_count':25,'actual_listening':False,'paid_api_calls':0,'cash_cost_krw':0})
    print(json.dumps({'stage':'partial' if partial else 'final','sentences':contract['sentence_count'],'words':len(words),'duration_s':position/SR,'intro_start_s':intro_start,'last_word_end_s':last_word,'outro_start_s':outro_start,'handoff':rel(handoff_path)},ensure_ascii=False),flush=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('step',choices=['prepare','generate-first3','build-first3','generate-rest','build-final']);a=p.parse_args()
    if a.step=='prepare': prepare()
    elif a.step.startswith('generate-'): asyncio.run(generate('first3' if a.step.endswith('first3') else 'rest'))
    else: build(a.step.endswith('first3'))


if __name__=='__main__': main()
