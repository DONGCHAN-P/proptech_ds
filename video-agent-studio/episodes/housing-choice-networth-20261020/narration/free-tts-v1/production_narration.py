"""Pure production contracts: approval gate, Korean readings, word cues and PCM assembly."""
import array
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import wave

SIDE = Path(__file__).resolve().parent
ROOT = SIDE.parents[4]
RATE = 24000
ALIASES = {'S&P500':'에스 앤드 피 오백','S&P':'에스 앤드 피','ETF':'이 티 에프'}
OVERRIDES = {'2억5천만원':'이억 오천만 원','1.21배':'일 점 이일 배',
             '2건':'두 건','30단지':'서른 단지'}
TOKEN = re.compile(r'S&P500|S&P|ETF|\d[\d,]*(?:\.\d+)?(?:[조억만천백십]\d*)*원|\d[\d,]*(?:\.\d+)?(?:개월|분기|단지|건|년|%|배)|\d[\d,]*(?:\.\d+)?')


class GateError(RuntimeError):
    pass


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def reference(root, value):
    path = Path(value)
    if not path.is_absolute():
        candidate = root / path
        if not candidate.exists() and str(path).replace('\\','/').startswith('video-agent-studio/'):
            candidate = root.parents[2] / path
        path = candidate
    path = path.resolve()
    if not path.is_relative_to(root.resolve()):
        raise GateError('승인 입력 경로가 episode 밖입니다.')
    return path


def validate_content_receipt(receipt, expected_sha):
    hashes = [receipt[k] for k in ('script_sha256','artifact_sha256','checked_sha256') if k in receipt]
    if not hashes or any(value != expected_sha for value in hashes):
        raise GateError('검수 영수증의 실제 대본 SHA가 다릅니다.')
    if receipt.get('approved') is not True or receipt.get('required_issues') != []:
        raise GateError('내용 검수 미통과 또는 필수 이슈가 있습니다.')
    if receipt.get('is_error') or receipt.get('exit_code',0) != 0:
        raise GateError('실패한 검수 실행은 승인으로 사용할 수 없습니다.')
    scope = str(receipt.get('approval_scope',receipt.get('review_scope',''))).lower()
    if scope and not any(token in scope for token in ('script','content','대본')):
        raise GateError('내용 검수 범위의 영수증이 아닙니다.')


def check_gate(episode_root, lock_path, prepared_sha):
    root = Path(episode_root).resolve()
    lock_path = Path(lock_path).resolve()
    if not lock_path.is_relative_to(root) or not lock_path.is_file():
        raise GateError('locked_script.json 미도착: 본문 합성 금지')
    lock = load(lock_path)
    try:
        script = reference(root,lock['script_path'])
        expected = lock['script_sha256']
        if expected != prepared_sha or digest(script) != expected:
            raise GateError('잠금/준비본/실제 대본 SHA가 일치하지 않습니다.')
        paths=[]; receipts={}
        for name in ('codex','claude'):
            ref = lock[name+'_receipt']
            receipt_path=reference(root,ref['path'] if isinstance(ref,dict) else ref)
            if receipt_path in paths:
                raise GateError('Codex와 Claude는 서로 다른 검수 영수증이 필요합니다.')
            if isinstance(ref,dict) and ref.get('sha256') != digest(receipt_path):
                raise GateError('잠금 파일에 고정된 검수 영수증 SHA가 다릅니다.')
            pinned=lock.get('review_receipt_sha256')
            if pinned is not None:
                key=ref['path'] if isinstance(ref,dict) else ref
                if pinned.get(key)!=digest(receipt_path):
                    raise GateError('review_receipt_sha256의 실제 영수증 SHA가 다릅니다.')
            receipt=load(receipt_path)
            identity=' '.join(str(receipt.get(k,'')) for k in
                ('reviewer','agent','role','model_requested')).lower()
            accepted=('codex','video_qa','gpt') if name=='codex' else ('claude','opus','sonnet','haiku')
            if not any(marker in identity for marker in accepted):
                raise GateError(name+' 검수자/실행 모델 식별 근거가 없습니다.')
            if any(previous['sha256']==digest(receipt_path) for previous in receipts.values()):
                raise GateError('동일 영수증 복사본으로 양측 검수를 대체할 수 없습니다.')
            if 'required_issues' not in receipt:
                review_path=receipt_path.with_name('review.json')
                review=load(review_path)
                validate_content_receipt(review,expected)
                receipt={**receipt,'required_issues':review['required_issues']}
            validate_content_receipt(receipt,expected)
            paths.append(receipt_path)
            receipts[name]={'path':str(receipt_path.relative_to(root)),'sha256':digest(receipt_path)}
    except (KeyError,OSError,TypeError,json.JSONDecodeError) as exc:
        raise GateError('잠금/검수 입력 불완전: '+type(exc).__name__) from None
    if lock.get('approved') is False:
        raise GateError('총괄 잠금이 승인되지 않았습니다.')
    for key in ('codex_content_pass','claude_content_pass','free_tts_authorized'):
        if key in lock and lock[key] is not True:
            raise GateError('잠금 파일의 '+key+'가 승인되지 않았습니다.')
    if lock.get('paid_tts_authorized') is True:
        raise GateError('현재 작업은 무료 TTS 현금0원 범위만 허용됩니다.')
    return {'script_path':str(script),'script_sha256':expected,
            'lock_sha256':digest(lock_path),'receipts':receipts}


def sino(value):
    number=int(str(value).replace(',',''))
    if number==0:
        return '영'
    if number>=10000:
        groups=[]
        for magnitude,unit in ((10**12,'조'),(10**8,'억'),(10000,'만')):
            quotient,number=divmod(number,magnitude)
            if quotient:
                groups.append(sino(quotient)+unit)
        return ''.join(groups)+(sino(number) if number else '')
    result=''
    for magnitude,unit in ((1000,'천'),(100,'백'),(10,'십'),(1,'')):
        quotient,number=divmod(number,magnitude)
        if quotient:
            result+=('' if quotient==1 and magnitude>1 else '영일이삼사오육칠팔구'[quotient])+unit
    return result


def reading(token):
    if token in ALIASES:
        return ALIASES[token]
    if token in OVERRIDES:
        return OVERRIDES[token]
    if token.endswith('원'):
        body=token[:-1]
        body=re.sub(r'\d[\d,]*(?:\.\d+)?',
            lambda m: '' if m.group()=='1' and body[m.end():m.end()+1] in ('천','백','십') else number_reading(m.group()),body)
        return body+' 원'
    match=re.fullmatch(r'([\d,]+(?:\.\d+)?)(개월|분기|단지|건|년|%|배)?',token)
    if not match:
        raise ValueError('지원하지 않는 숫자 표기: '+token)
    number,unit=match.groups()
    return number_reading(number)+(' '+{'%':'퍼센트'}.get(unit,unit) if unit else '')


def number_reading(number):
    integer,point,fraction=number.replace(',','').partition('.')
    return sino(integer)+(' 점 '+''.join('영일이삼사오육칠팔구'[int(d)] for d in fraction) if point else '')


def pronounce(text):
    pieces=[];mapping=[];cursor=0;spoken_cursor=0
    for match in TOKEN.finditer(text):
        if match.start()>cursor:
            literal=text[cursor:match.start()]
            mapping.append({'source_start':cursor,'source_end':match.start(),'spoken_start':spoken_cursor,
                            'spoken_end':spoken_cursor+len(literal),'original':literal,'spoken':literal,'kind':'literal'})
            pieces.append(literal);spoken_cursor+=len(literal)
        value=reading(match.group())
        mapping.append({'source_start':match.start(),'source_end':match.end(),'spoken_start':spoken_cursor,
                        'spoken_end':spoken_cursor+len(value),'original':match.group(),'spoken':value,'kind':'pronunciation'})
        pieces.append(value);spoken_cursor+=len(value);cursor=match.end()
    if cursor<len(text):
        literal=text[cursor:]
        mapping.append({'source_start':cursor,'source_end':len(text),'spoken_start':spoken_cursor,
                        'spoken_end':spoken_cursor+len(literal),'original':literal,'spoken':literal,'kind':'literal'})
        pieces.append(literal)
    result=''.join(pieces)
    if re.search(r'\d',result):
        raise ValueError('낭독문에 미변환 숫자가 남았습니다.')
    return result,mapping


def parse_script(text):
    headings=list(re.finditer(r'^## (\d+)\. ([^\n]+)\n',text,re.M))
    if [int(m.group(1)) for m in headings]!=list(range(1,11)):
        raise ValueError('낭독 대본은 번호가 있는 10장이어야 합니다.')
    chapters=[];global_paragraph=0
    for i,heading in enumerate(headings):
        start=heading.end();end=headings[i+1].start() if i+1<len(headings) else len(text)
        body=text[start:end];paragraphs=[]
        for local,match in enumerate(re.finditer(r'\S[\s\S]*?(?=\n[ \t]*\n|\Z)',body),1):
            original=match.group().rstrip()
            if original.startswith('#'):
                raise ValueError('본문 안의 Markdown 제목을 낭독할 수 없습니다.')
            global_paragraph+=1
            spoken,mapping=pronounce(original)
            paragraphs.append({'paragraph':global_paragraph,'chapter_paragraph':local,
                'paragraph_id':f'C{i+1:02}P{local:02}',
                'text':original,'spoken_text':spoken,'display_mapping':mapping,
                'source_start':start+match.start(),'source_end':start+match.start()+len(original)})
        chapters.append({'chapter':i+1,'title':heading.group(2).strip(),'paragraphs':paragraphs})
    if global_paragraph!=54:
        raise ValueError(f'확인된 후보의 54문단과 다릅니다: {global_paragraph}')
    return chapters


def norm(text):
    return re.sub(r'[\W_]+','',text)


def spoken_position(mapping,position):
    for atom in mapping:
        if position==atom['source_start']:
            return atom['spoken_start']
        if position==atom['source_end']:
            return atom['spoken_end']
        if atom['source_start']<position<atom['source_end']:
            if atom['kind']!='literal':
                raise ValueError('숫자/단위/고유명사 치환 안에서 cue를 나눌 수 없습니다.')
            return atom['spoken_start']+position-atom['source_start']
    raise ValueError('원문-낭독 위치 연결 실패')


def meaning_spans(text):
    tokens=list(re.finditer(r'\S+',text));spans=[];start=None;end=None
    for token in tokens:
        if start is None:
            start=token.start()
        if end is not None and token.end()-start>36 and end-start>=12:
            previous=text[start:end].split()[-1]
            if previous not in ('연','월','약','최소','최대','제','한','두','세','네','다섯','여섯','일곱','여덟','아홉','열','서른'):
                spans.append([start,end]);start=token.start()
        end=token.end()
        if re.search(r'[.!?。！？]$',token.group()) or (token.group().endswith(',') and end-start>=14):
            spans.append([start,end]);start=None;end=None
    if start is not None:
        spans.append([start,end])
    return spans


def word_cues(text,spoken,mapping,events,paragraph):
    if not events or any(e['type']!='WordBoundary' for e in events):
        raise ValueError('문단 합성에는 실제 WordBoundary가 필요합니다.')
    if norm(''.join(e['text'] for e in events))!=norm(spoken):
        raise ValueError('단어 메타데이터와 낭독문 전체가 일치하지 않습니다. 추정 정렬 금지')
    intervals=[];cursor=0;previous=-1
    for event in events:
        if event['duration']<=0 or event['offset']<0 or event['offset']<previous:
            raise ValueError('단어 경계 길이/순서 오류')
        length=len(norm(event['text']))
        intervals.append((cursor,cursor+length));cursor+=length;previous=event['offset']
    groups=[]
    for start,end in meaning_spans(text):
        a,b=spoken_position(mapping,start),spoken_position(mapping,end)
        left,right=len(norm(spoken[:a])),len(norm(spoken[:b]))
        touched=[i for i,(x,y) in enumerate(intervals) if x<right and y>left]
        if not touched:
            raise ValueError('의미구에 실제 단어 경계가 없습니다.')
        if groups and groups[-1][3]>=touched[0]:
            groups[-1][1]=end;groups[-1][3]=touched[-1]
        else:
            groups.append([start,end,touched[0],touched[-1]])
    cues=[]
    for i,(start,end,first,last) in enumerate(groups,1):
        a,b=spoken_position(mapping,start),spoken_position(mapping,end)
        beginning=events[first]['offset']/1e7
        ending=(events[last]['offset']+events[last]['duration'])/1e7
        cues.append({'id':f'P{paragraph:03}Q{i:03}','paragraph':paragraph,'text':text[start:end],
            'spoken_text':spoken[a:b],'start_s':beginning,'end_s':ending,
            'native_start_s':beginning,'native_end_s':ending,'source_start':start,'source_end':end,
            'first_word_index':first,'last_word_index':last,'timing_basis':'actual provider WordBoundary; phrase grouping only'})
    for current,following in zip(cues,cues[1:]):
        current['end_s']=min(current['end_s'],following['start_s'])
        if current['end_s']<=current['start_s']:
            raise ValueError('겹침 정리 후 cue 길이 0: 재검수 필요')
    if norm(''.join(c['text'] for c in cues))!=norm(text):
        raise ValueError('표시 cue의 원문 누락')
    return cues


def read_pcm(path):
    with wave.open(str(path),'rb') as source:
        if (source.getnchannels(),source.getsampwidth(),source.getframerate())!=(1,2,RATE):
            raise ValueError('문단 WAV는 PCM16 mono 24000Hz가 필요합니다.')
        frames=source.getnframes();pcm=source.readframes(frames)
    values=array.array('h',pcm)
    if not values:
        raise ValueError('빈 PCM')
    last=next((i for i in range(len(values)-1,-1,-1) if abs(values[i])>=33),None)
    return pcm,frames,(last+1)/RATE if last is not None else None


def assemble_chapter(chapter,title,records,contract,output_wave):
    leading=contract['leading_silence']['chapter_1_s' if chapter==1 else 'other_chapters_s']
    pcm=bytearray(b'\0\0'*round(leading*RATE));cues=[];paragraphs=[];native_end=0;signal_end=0
    for index,record in enumerate(records):
        offset=len(pcm)/(2*RATE)
        raw,frames,local_signal=read_pcm(record['wave_file'])
        if local_signal is None:
            raise ValueError('문단이 무음입니다.')
        if record['last_word_end_s']>frames/RATE+0.15:
            raise ValueError('단어 경계가 파일 길이를 벗어났습니다.')
        native_end=offset+record['last_word_end_s'];signal_end=offset+local_signal
        for cue in record['cues']:
            row=copy.deepcopy(cue)
            for key in ('start_s','end_s','native_start_s','native_end_s'):
                if key in row:
                    row[key]=round(row[key]+offset,9)
            row['id']=f'C{chapter:02}_'+row['id'];cues.append(row)
        paragraphs.append({'paragraph':record['paragraph'],'offset_s':offset,'measured_seconds':frames/RATE,
            'wave_file':record['wave_file'],'last_native_word_end_s':native_end,'last_pcm_signal_end_s':signal_end})
        pcm.extend(raw)
        if index<len(records)-1:
            pcm.extend(b'\0\0'*round(contract['paragraph_gap_s']*RATE))
    last_spoken=max(native_end,signal_end)
    tail=contract['tail_s']['chapters_1_to_9' if chapter<10 else 'chapter_10_from_last_spoken_word']
    target=max(len(pcm)/(2*RATE),last_spoken+tail)
    fps=contract['canvas']['fps']
    if RATE%fps:
        raise ValueError('PCM/영상 프레임 간격 불일치')
    frame_samples=RATE//fps
    target_frames=math.ceil(target*RATE/frame_samples-1e-8)*frame_samples
    pcm.extend(b'\0\0'*(target_frames-len(pcm)//2))
    output_wave=Path(output_wave)
    with output_wave.open('xb') as stream:
        with wave.open(stream,'wb') as out:
            out.setparams((1,2,RATE,0,'NONE','not compressed'));out.writeframes(pcm)
    _,measured_frames,chapter_signal_end=read_pcm(output_wave)
    return {'chapter':chapter,'title':title,'audio_file':str(output_wave.relative_to(ROOT)).replace('\\','/'),
        'total_seconds':measured_frames/RATE,'pcm_frames':measured_frames,
        'last_speech_end_s':last_spoken,'last_speech_end_basis':'max(last provider word end, last PCM sample >= -60dBFS); documented unlistened estimate',
        'last_native_word_end_s':native_end,'last_pcm_signal_end_s':chapter_signal_end,
        'leading_silence_s':leading,'paragraph_gap_s':contract['paragraph_gap_s'],
        'tail_from_last_spoken_s':measured_frames/RATE-last_spoken,'cues':cues,'paragraphs':paragraphs,
        'audio_sha256':digest(output_wave),'listening':'not_performed'}
