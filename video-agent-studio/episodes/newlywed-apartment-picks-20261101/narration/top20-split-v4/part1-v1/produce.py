"""PART1 only. Approved free Edge synthesis; no automatic retry or paid fallback.
Adapted helpers from narration/top20-explain-v3/produce.py, not its approval,
source, scene-count, or build assumptions. All writes remain beside this file.
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
EP = OUT.parents[2]
ROOT = EP.parents[2]
REFERENCE = EP / 'narration/top20-explain-v3/produce.py'
DEPS = EP / 'narration/top20-production-v1/deps'
SCRIPT = ROOT / '영상/신혼부부_지역별아파트/2부작_수정안/1편_20-11위_대본_v2.md'
SCENES = EP / 'director/top20-split-v4/part1-production-v1/approved_part1_scene_proposals.json'
APPROVAL = SCENES.with_name('script_approval.json')
AUTH = SCENES.with_name('production_authorization.json')
INTRO = EP / 'director/top20-production-v1/locked-audio/intro_clean_v7.wav'
OUTRO = EP / 'director/top20-production-v1/locked-audio/outro_clean_v7.wav'
FFMPEG = ROOT / 'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
MD_SHA = '9d62f607c352dfbd0dbe7306ff82290607bc10477723ab92ca7851e0379420c2'
SCENE_SHA = 'b20616e6c8b5e128f41bc505ba79875ad90735bee38ecd16d1099739c0c1f951'
VOICE, RATE, FACTOR, SR = 'ko-KR-InJoonNeural', '+0%', 1.35, 44100
REV = 'top20-split-v4-part1-v1-free-edge-injoon-atempo135'
SCRIPT_REV = 'top20-split-v4/part1-script-v2'


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
    result = subprocess.run([str(FFMPEG),'-hide_banner','-loglevel','error']+args,capture_output=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if result.returncode:
        raise RuntimeError('Local ffmpeg failed: '+result.stderr.decode('utf-8',errors='replace')[-700:])


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
    fingerprint = digest(json.dumps({'text_sha256':chunk['sha256'],'voice':VOICE,'rate':RATE,'volume':'+0%','pitch':'+0Hz','boundary':'WordBoundary','edge_tts_version':edge_tts.__version__,'communicate_sha256':sha(DEPS/'edge_tts/communicate.py'),'auto_retry':False},sort_keys=True))
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


def authorization():
    assert sha(SCRIPT) == MD_SHA and sha(SCENES) == SCENE_SHA
    a, approval, doc = read(AUTH), read(APPROVAL), read(SCENES)
    assert a['status'] == approval['status'] == 'approved'
    assert a['decision_id'] == approval['id'] == doc['approval']['decision_id'] == '8c7be2a79904'
    assert a['script_md_sha256'] == MD_SHA and a['scene_json_sha256'] == SCENE_SHA
    assert approval['artifact_revision'] == SCRIPT_REV
    assert any(v['sha256'] == MD_SHA and ROOT/v['path'] == SCRIPT for v in approval['artifacts'])
    ids = [s['scene_id'] for s in doc['scenes']]
    for scope in [a['scope'], approval['scope'], doc['approval']['scope']]:
        assert scope['part'] == 1 and scope['scene_ids'] == ids
        assert scope['cash_cap_krw'] == 0 and scope['voice'] == VOICE
        assert all(scope[k] is False for k in ['paid_generation_authorized','part2_authorized','external_file_export_authorized','upload_authorized'])
    assert all(s['part'] == 1 and s['scene_id'].startswith('P01-') for s in doc['scenes'])
    assert len(ids) == len(set(ids)) == 12
    assert sum(len(s['sentences']) for s in doc['scenes']) == 85
    return {'decision_id':approval['id'],'script_revision':SCRIPT_REV,
            'script_md_path':rel(SCRIPT),'script_md_sha256':MD_SHA,
            'scene_json_path':rel(SCENES),'scene_json_sha256':SCENE_SHA,
            'script_approval_path':rel(APPROVAL),'script_approval_sha256':sha(APPROVAL),
            'production_authorization_path':rel(AUTH),'production_authorization_sha256':sha(AUTH),
            'scope':'PART1 확정 원문만 무료 Edge 합성. 0원. 2편 생성/유료/업로드/파일 반출 없음.',
            'canonical_draft_status_overridden_only_by_approved_part1_receipt':True}


def prepare():
    auth = authorization()
    doc = read(SCENES)
    md = SCRIPT.read_text(encoding='utf-8-sig')
    # Reader MD has plain paragraphs, not the older sentence-ID Markdown format.
    paragraphs = [x.strip() for x in md.split('\n\n') if x.strip() and not x.lstrip().startswith('#')]
    original_rows = [t['text'] for s in doc['scenes'] for t in s['sentences']]
    assert paragraphs[1:] == original_rows, 'reader MD/canonical spoken paragraphs differ'
    rows, chunks, md_cursor = [], [], 0
    for si, scene in enumerate(doc['scenes']):
        local, scene_offset = [], 0
        for ti, t in enumerate(scene['sentences']):
            text = t['text']
            md_start = md.index(text,md_cursor); md_cursor = md_start+len(text)
            reading, transforms, spans = pronounce(text)
            row = {'scene_id':scene['scene_id'],'sentence_id':t['sentence_id'],
                   'original_text':text,'display_text':text,'reading_text':reading,
                   'transformations':transforms,'character_mapping':spans,
                   'display_roundtrip_exact':True,'claim_ids':t.get('claim_ids',[]),
                   'price_role':t.get('price_role'),'statement_type':t.get('statement_type'),
                   'screen_switch_id':t.get('screen_switch_id'),'actual_listening':False,
                   'source_json_path':rel(SCENES),'source_json_pointer':f'/scenes/{si}/sentences/{ti}/text',
                   'scene_display_char_start':scene_offset,'scene_display_char_end':scene_offset+len(text),
                   'reader_md_char_start':md_start,'reader_md_char_end':md_start+len(text)}
            rows.append(row); local.append(row); scene_offset += len(text)+1
        groups = [(scene['scene_id'],local)]
        if scene['scene_id'] == 'P01-INTRO':
            groups = [('P01-INTRO-HOOK',local[:1]),('P01-INTRO-REST',local[1:])]
        for asset_id, selected in groups:
            body = '\n'.join(r['reading_text'] for r in selected)
            path = OUT/'chunks'/(asset_id+'.txt'); write_text(path,body)
            chunks.append({'scene_id':scene['scene_id'],'asset_id':asset_id,
                           'sentence_ids':[r['sentence_id'] for r in selected],
                           'path':rel(path),'sha256':sha(path),'text':body,'characters':len(body)})
    assert len({r['sentence_id'] for r in rows}) == len(rows)
    assert [x for c in chunks for x in c['sentence_ids']] == [r['sentence_id'] for r in rows]
    inputs = {rel(p):sha(p) for p in [SCRIPT,SCENES,APPROVAL,AUTH,INTRO,OUTRO,REFERENCE,DEPS/'edge_tts/communicate.py',FFMPEG,Path(__file__)]}
    save(OUT/'approval_receipt.json',{**auth,'recorded_at':stamp(),'voice':VOICE,'rate':RATE,'atempo':FACTOR})
    save(OUT/'sentences.json',{'script_revision':SCRIPT_REV,'script_sha256':MD_SHA,'sentences':rows})
    save(OUT/'pronunciation_ledger.json',{'source_sha256':MD_SHA,'scene_json_sha256':SCENE_SHA,
         'policy':'원문/표시문을 보존. 발음 변환은 문자 범위·이유·역변환·독립 숫자값 검사와 함께 기록.',
         'reference_code_sha256':sha(REFERENCE),'explicit_name_symbol_rules':SPECIAL,
         'sentences':rows,'transformation_count':sum(len(r['transformations']) for r in rows),
         'numeric_value_count':sum(len(t['independent_values']) for r in rows for t in r['transformations']),
         'actual_pronunciation_listened':False})
    manifest = {'task_id':'part1-narration-v1','created_at':stamp(),'script_revision':SCRIPT_REV,
                'audio_revision':REV,'approval':auth,'input_versions':inputs,'chunks':chunks,
                'sentence_count':len(rows),'scene_count':len(doc['scenes']),'chunk_count':len(chunks),
                'characters':sum(c['characters'] for c in chunks),'provider':'microsoft_edge_consumer_tts',
                'voice':VOICE,'rate':RATE,'postprocess_atempo':FACTOR,'paid_api_calls':0,
                'cash_cost_krw':0,'credentials_loaded':False,'automatic_retry':False,
                'part2_synthesis':False,'ASR_owner':'parent','utf8_roundtrip_checked':True,
                'intro_strategy':'첫 hook 문장과 나머지 INTRO를 독립 합성. 파일을 자르지 않고 hook 전체 뒤 클린브랜드5초 삽입.'}
    save(OUT/'narration_manifest.json',manifest)
    write_text(OUT/'reading_text.txt','\n\n'.join(c['text'] for c in chunks))
    print(json.dumps({k:manifest[k] for k in ['sentence_count','scene_count','chunk_count','characters']},ensure_ascii=False),flush=True)


async def generate():
    authorization()
    manifest = read(OUT/'narration_manifest.json')
    assert manifest['input_versions'][rel(Path(__file__))] == sha(Path(__file__))
    sys.path.insert(0,str(DEPS))
    import edge_tts
    # Each asset has one attempt; the library's automatic 403 retry is bypassed.
    # Sequential requests keep the first failure from starting further requests.
    for chunk in manifest['chunks']:
        try:
            await generate_chunk(chunk,edge_tts)
        except Exception as e:
            save(OUT/'generation_failure.json',{'at':stamp(),'asset_id':chunk['asset_id'],
                 'scene_id':chunk['scene_id'],'error_type':type(e).__name__,
                 'automatic_retry':False,'remaining_chunks_not_started':True})
            raise
    receipts=[read(OUT/'raw'/(c['asset_id']+'.receipt.json')) for c in manifest['chunks']]
    save(OUT/'generation_usage.json',{'at':stamp(),'provider':'microsoft_edge_consumer_tts',
         'voice':VOICE,'edge_tts_version':edge_tts.__version__,'rate':RATE,'postprocess_atempo':FACTOR,
         'complete_assets':len(receipts),'requested_characters':manifest['characters'],
         'failed_requests':0,'automatic_retry':False,'provider_403_retry_disabled':True,
         'paid_api_calls':0,'cash_cost_krw':0,'credentials_loaded':False,
         'receipts':[rel(OUT/'raw'/(c['asset_id']+'.receipt.json')) for c in manifest['chunks']]})
    print(json.dumps({'stage':'generated','assets':len(receipts),'cash_cost_krw':0}),flush=True)


def build():
    auth=authorization(); manifest=read(OUT/'narration_manifest.json')
    rows=read(OUT/'sentences.json')['sentences']; row_by_id={r['sentence_id']:r for r in rows}
    measured=[]
    for c in manifest['chunks']:
        m=align(c,[row_by_id[k] for k in c['sentence_ids']]);m['asset_id']=c['asset_id'];measured.append(m)
    intro,outro=inspect(INTRO),inspect(OUTRO)
    assert intro['duration_s']==5 and outro['duration_s']==10
    position=0;parts=[];words=[];sentences=[];segments=[];intro_start=None
    for m in measured:
        start=position/SR
        segment={'asset_id':m['asset_id'],'scene_id':m['scene_id'],'audio_path':m['audio_path'],
                 'audio_sha256':m['audio_sha256'],'start_s':start,'end_s':(position+m['frames'])/SR,
                 'start_frame':position,'end_frame':position+m['frames'],'duration_s':m['frames']/SR,
                 'raw_audio_path':m['raw_audio_path'],'raw_mp3_path':m['raw_mp3_path'],
                 'provider_boundaries_path':m['provider_boundaries_path'],'full_processed_pcm_preserved':True}
        segments.append(segment)
        for s in m['sentence_times']:
            r=row_by_id[s['sentence_id']]
            sentences.append({**s,'scene_id':m['scene_id'],'asset_id':m['asset_id'],
                              'start_s':start+s['local_start_s'],'end_s':start+s['local_end_s'],
                              'chunk_local_start_s':s['local_start_s'],'chunk_local_end_s':s['local_end_s'],
                              'source_json_pointer':r['source_json_pointer'],
                              'reader_md_char_start':r['reader_md_char_start'],
                              'reader_md_char_end':r['reader_md_char_end'],'audio_revision':REV})
        for w in m['words']:
            r=row_by_id[w['sentence_id']]
            words.append({**w,'asset_id':m['asset_id'],'start_s':start+w['local_start_s'],
                          'end_s':start+w['local_end_s'],'global_start_s':start+w['local_start_s'],
                          'global_end_s':start+w['local_end_s'],
                          'chunk_local_start_s':w['local_start_s'],'chunk_local_end_s':w['local_end_s'],
                          'source_char_start':w['display_char_start'],'source_char_end':w['display_char_end'],
                          'scene_display_char_start':r['scene_display_char_start']+w['display_char_start'],
                          'scene_display_char_end':r['scene_display_char_start']+w['display_char_end'],
                          'reader_md_char_start':r['reader_md_char_start']+w['display_char_start'],
                          'reader_md_char_end':r['reader_md_char_start']+w['display_char_end'],
                          'source_json_pointer':r['source_json_pointer'],'audio_revision':REV})
        parts.append(pcm(Path(m['audio_path'])));position+=m['frames']
        if m['asset_id']=='P01-INTRO-HOOK':
            intro_start=position/SR; parts.append(pcm(INTRO));position+=intro['frames']
    native_end=position/SR; last_word=words[-1]['end_s']
    outro_frame=math.ceil((last_word+3)*SR)
    assert outro_frame>=position,'Existing native final tail exceeds required 3s hold; do not truncate audio'
    extra=outro_frame-position;parts.append(b'\0\0'*extra)
    outro_start=outro_frame/SR;parts.append(pcm(OUTRO));position=outro_frame+outro['frames']
    complete_pcm=b''.join(parts)
    audio_path=OUT/'narration_with_clean_brand.wav';write_wav(audio_path,complete_pcm)
    # Entire individual processed files are copied byte-for-byte, including their tails.
    preservation=[]
    for seg in segments:
        actual=complete_pcm[seg['start_frame']*2:seg['end_frame']*2]
        expected=pcm(Path(seg['audio_path'])); assert actual==expected
        preservation.append({'asset_id':seg['asset_id'],'global_frames':[seg['start_frame'],seg['end_frame']],
                             'pcm_sha256':hashlib.sha256(expected).hexdigest(),'exact_full_pcm_match':True})
    assert complete_pcm[round(intro_start*SR)*2:round((intro_start+5)*SR)*2]==pcm(INTRO)
    assert complete_pcm[outro_frame*2:]==pcm(OUTRO)
    audio_info=inspect(audio_path);ff(['-i',str(audio_path),'-f','null','-'])
    assert audio_info['frames']==position and not audio_info['clip_peak_reached'] and audio_info['rms_pcm']>0
    scenes=[]
    for source_scene in read(SCENES)['scenes']:
        sid=source_scene['scene_id'];segs=[s for s in segments if s['scene_id']==sid]
        start_frame,end_frame=segs[0]['start_frame'],segs[-1]['end_frame']
        start,end=start_frame/SR,end_frame/SR
        ss=[s for s in sentences if s['scene_id']==sid]
        ww=[w for w in words if w['scene_id']==sid]
        for x in ss+ww:
            x['local_start_s']=x['start_s']-start;x['local_end_s']=x['end_s']-start
        path=OUT/'scenes'/(sid+'.wav');write_wav(path,complete_pcm[start_frame*2:end_frame*2])
        scene={'scene_id':sid,'start_s':start,'end_s':end,'duration_s':end-start,
               'audio_revision':REV,'audio_path':str(path),'audio_sha256':sha(path),
               'narration_text':'\n'.join(s['text'] for s in ss),'reading_text':'\n'.join(s['reading_text'] for s in ss),
               'sentences':ss,'sentence_times':[{**s,'start_s':s['local_start_s'],'end_s':s['local_end_s']} for s in ss],
               'captions':[{'sentence_id':s['sentence_id'],'text':s['text'],'start_s':s['start_s'],'end_s':s['end_s']} for s in ss],
               'segments':segs,'internal_gaps':[{'kind':'brand_intro','start_s':intro_start,'end_s':intro_start+5}] if sid=='P01-INTRO' else [],
               'anchors':{'narration_start':ss[0]['start_s']-start},
               'words_path':rel(OUT/'words.json'),'timing_basis':'actual_audio_samples_and_scaled_provider_word_boundaries',
               'alignment_basis':'native_WordBoundary_ticks_divided_by_1.35',
               'confidence':'measured_samples_and_provider_metadata_not_listening_verified',
               'is_estimate':False,'actual_listening':False,'timing_locked':False}
        scenes.append(scene)
    assert len(scenes)==12 and len(sentences)==85
    assert [s['sentence_id'] for s in sentences]==[r['sentence_id'] for r in rows]
    assert all(a['end_s']<=b['start_s']+.000001 for a,b in zip(words,words[1:]))
    for w in words:
        r=row_by_id[w['sentence_id']]
        assert r['display_text'][w['source_char_start']:w['source_char_end']]==w['display_text']
        assert SCRIPT.read_text(encoding='utf-8-sig')[w['reader_md_char_start']:w['reader_md_char_end']]==w['display_text']
    save(OUT/'words.json',{'audio_revision':REV,'script_sha256':MD_SHA,'scene_json_sha256':SCENE_SHA,
         'word_count':len(words),'normalized_reading_coverage':1.0,'units':'seconds',
         'time_semantics':'start_s/end_s and global_* are full-audio global; local_* from scene start including INTRO brand gap; chunk_local_* from independent processed chunk; raw_* from native boundary ticks.',
         'offset_semantics':'Unicode codepoint half-open ranges. source_char/display_char are sentence-local; scene_display offsets use newline-joined original sentences; reader_md offsets use decoded original MD. Explicit transforms can map multiple words to the same protected display span.',
         'character_proportional_alignment_used':False,'actual_listening':False,'words':words})
    brand_intro={**intro,'id':'brand_intro','audio_path':str(INTRO),'start_s':intro_start,'end_s':intro_start+5,
                 'insert_after_sentence_id':'P01-INTRO-V2-01','insert_before_sentence_id':'P01-INTRO-V2-02',
                 'hook_speech_end_s':sentences[0]['end_s'],'hook_tail_retained_s':intro_start-sentences[0]['end_s']}
    brand_outro={**outro,'id':'brand_outro','audio_path':str(OUTRO),'start_s':outro_start,'end_s':position/SR}
    contract={'schema_revision':'top20-narration-contract-v1','task_id':'part1-narration-v1',
              'status':'all_audio_measured_proposal_pending_director_lock_and_independent_QA',
              'script_revision':SCRIPT_REV,'script_sha256':MD_SHA,'scene_json_sha256':SCENE_SHA,
              'approval_receipt':rel(OUT/'approval_receipt.json'),'audio_revision':REV,
              'timing_locked':False,'lock_owner':'director','timing_basis':'actual_audio',
              'is_estimate':False,'duration_is_actual':True,
              'alignment_basis':'native_provider_WordBoundary_ticks_divided_by_1.35',
              'character_proportional_alignment_used':False,'old_timing_fallback_used':False,
              'provider':'microsoft_edge_consumer_tts','voice':VOICE,'edge_rate':RATE,
              'postprocess_atempo_factor':FACTOR,'actual_listening':False,'actual_listening_performed':False,
              'asr_performed':False,'asr_owner':'parent','audio_file':str(audio_path),
              'full_brand_audio_file':str(audio_path),'audio_sha256':sha(audio_path),
              'audio_file_time_origin_global_s':0,'full_brand_audio_file_time_origin_global_s':0,
              'words_file':rel(OUT/'words.json'),'words_file_sha256':sha(OUT/'words.json'),
              'audio_body_duration_s':sum(m['frames'] for m in measured)/SR,'body_audio_is_contiguous':False,
              'body_audio_note':'Full WAV already contains intro once after first hook and outro once. Do not reinsert brand. INTRO scene WAV contains same 5s gap; use per-sentence global times.',
              'last_spoken_end_s':last_word,'last_spoken_end_basis':'native final WordBoundary end /1.35; no listening',
              'native_narration_end_s':native_end,'final_audio_tail_already_counted_s':native_end-last_word,
              'required_hold_from_last_spoken_s':3,'additional_silence_after_audio_s':extra/SR,
              'final_hold':{'start_s':last_word,'end_s':outro_start,'native_tail_s':native_end-last_word,'extra_silence_s':extra/SR},
              'brand_intro':brand_intro,'brand_outro':brand_outro,'brand_audio_included_once':True,
              'total_duration_with_brand_and_hold_s':position/SR,'scenes':scenes,'scene_id_count':12,
              'sentence_count':len(sentences),'word_count':len(words),
              'time_semantics':'scenes.start/end and scenes.sentences.start/end GLOBAL. scenes.sentence_times start/end LOCAL from scene WAV0 incl internal INTRO brand gap. Words start/end GLOBAL; local_* from scene0; chunk_local_* from each processed asset.',
              'changed_scene_ids':[s['scene_id'] for s in scenes],
              'changed_sentence_ids':[r['sentence_id'] for r in rows],'timing_delta_s':None,
              'timing_delta_basis':'new approved PART1 script; no same-script prior actual audio exists',
              'paid_api_calls':0,'cash_cost_krw':0}
    save(OUT/'timing_proposals.json',contract)
    save(OUT/'sentence_times_global.json',{'audio_revision':REV,'time_semantics':'global seconds from full WAV0','sentences':sentences})
    verification={'at':stamp(),'status':'technical_pass_listening_ASR_independent_QA_pending',
                  'approval':auth,'reader_MD_canonical_paragraphs_order_exact':True,
                  'sentence_count':len(sentences),'scene_count':len(scenes),'chunk_count':len(measured),
                  'word_count':len(words),'normalized_provider_reading_coverage':1.0,
                  'every_sentence_has_native_provider_words':True,'display_roundtrip_exact':True,
                  'word_source_offsets_exact':True,'audio':audio_info,'full_decode_passed':True,
                  'full_processed_PCM_preservation':preservation,'audio_truncation_performed':False,
                  'brand_audio_byte_exact_at_single_declared_interval':True,
                  'last_spoken_end_s':last_word,'outro_start_s':outro_start,
                  'outro_minus_provider_last_word_s':outro_start-last_word,
                  'native_tail_already_in_hold_s':native_end-last_word,'extra_silence_s':extra/SR,
                  'target_duration_padding':False,'speed_policy':'+0% then fixed atempo=1.35',
                  'time_transform_accuracy_limit':'Native provider boundaries scaled analytically; atempo phonetic displacement and acoustic speech endpoint are not independently measured.',
                  'metrics':[m['metrics'] for m in measured],
                  'actual_listening':False,'continuous_playback':False,'asr_performed':False,
                  'independent_QA_performed':False,'paid_api_calls':0,'cash_cost_krw':0}
    save(OUT/'verification.json',verification)
    issue_id='PART1_LISTENING_ASR_AND_QA_PENDING'
    save(OUT/('issue_'+issue_id+'.json'),{'issue_id':issue_id,'scene_ids':contract['changed_scene_ids'],
         'problem':'전체 음성의 실제 청취·ASR·독립검수 미수행. atempo 음소 경계 오차 미측정.',
         'evidence':rel(OUT/'verification.json'),'proposal':'총괄이 로컬ASR·청취·독립QA를 이어 수행하고 시간표 확정. 편집은 문장별 global 시점 사용.',
         'impact':'전체 발음·자연스러움 및 마지막 발화 청각 확인 보류. 기술·커버리지 검사를 청취 통과로 확대하지 않음.',
         'next_role':['director','editor','qa']})
    save(OUT/'handoff.json',{'task_id':'part1-narration-v1','role':'narration',
         'status':'technical_narration_complete_pending_parent_QA_and_lock','created_at':stamp(),
         'input_revisions':{'script_revision':SCRIPT_REV,'script_md_sha256':MD_SHA,'scene_json_sha256':SCENE_SHA,
                            'approval_sha256':sha(APPROVAL),'authorization_sha256':sha(AUTH)},
         'outputs':[rel(OUT/p) for p in ['narration_with_clean_brand.wav','timing_proposals.json','words.json',
                    'sentence_times_global.json','sentences.json','pronunciation_ledger.json','verification.json',
                    'approval_receipt.json','generation_usage.json','artifact_manifest.json','completion_receipt.json']],
         'audio_path':rel(audio_path),'audio_sha256':sha(audio_path),'timing_path':rel(OUT/'timing_proposals.json'),
         'words_path':rel(OUT/'words.json'),'new_length_s':position/SR,
         'brand_intervals_s':{'intro':[intro_start,intro_start+5],'outro':[outro_start,position/SR]},
         'last_spoken_end_s':last_word,'changed_scene_ids':contract['changed_scene_ids'],
         'changed_sentence_ids':contract['changed_sentence_ids'],'timing_delta_s':None,
         'timing_delta_note':'새 승인 PART1. 비교 가능한 이전 동일 대본 실측 없음.',
         'validation':'85문장/12장면/13독립chunk; 실제 단어경계 전량 매핑; 원문/숫자/문자오프셋·PCM전량보존·디코드·단일브랜드·발화뒤3초 확인',
         'open_issue_ids':[issue_id],'issue_path':rel(OUT/('issue_'+issue_id+'.json')),
         'schema_note':'v3-compatible scenes[].sentences global start/end,text,reading_text. INTRO internal5s brand gap; scene-local times include gap. words provider_text and global/local times; protected display spans may repeat.',
         'next_role':'director timing lock; editor integration; parent local ASR/listening and independent QA',
         'actual_listening':False,'asr_performed':False,'unverified_scope':'전체 실제 발음·자연스러움·음소 동기',
         'paid_api_calls':0,'cash_cost_krw':0,'raw_retained':True,
         'reproduction':'tools/python311/python.exe -Xutf8 '+rel(OUT/'produce.py')+' prepare / generate / build (separate invocations; verified complete receipts reused; failures never auto-retried)'})
    files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name not in ['artifact_manifest.json','completion_receipt.json','run.log'] and p.suffix!='.tmp')
    save(OUT/'artifact_manifest.json',{'created_at':stamp(),'files':[{'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in files]})
    save(OUT/'completion_receipt.json',{'status':'complete_technical_narration_scope','at':stamp(),
         'code_sha256':sha(Path(__file__)),'artifact_manifest_sha256':sha(OUT/'artifact_manifest.json'),
         'script_md_sha256':MD_SHA,'scene_json_sha256':SCENE_SHA,'audio_sha256':sha(audio_path),
         'sentence_count':85,'scene_count':12,'chunk_count':13,'actual_listening':False,
         'paid_api_calls':0,'cash_cost_krw':0})
    print(json.dumps({'stage':'final','sentences':85,'words':len(words),'duration_s':position/SR,
          'intro_s':[intro_start,intro_start+5],'last_speech_end_s':last_word,
          'outro_s':[outro_start,position/SR],'handoff':rel(OUT/'handoff.json')},ensure_ascii=False),flush=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('step',choices=['prepare','generate','build']);a=p.parse_args()
    if a.step=='prepare': prepare()
    elif a.step=='generate': asyncio.run(generate())
    else: build()


if __name__=='__main__': main()
