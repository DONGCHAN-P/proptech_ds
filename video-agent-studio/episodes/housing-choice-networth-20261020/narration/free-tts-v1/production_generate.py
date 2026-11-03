"""Prepare offline; generate body only after the two-review exact-SHA lock passes."""
import argparse
import asyncio
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess
import sys
import traceback

SIDE=Path(__file__).resolve().parent
sys.path.insert(0,str(SIDE))
import production_narration as p

EP=SIDE.parents[1]
ROOT=SIDE.parents[4]
CONTRACT=EP/'director/two-episode-production-v1/media_contract.json'
LOCK=EP/'director/two-episode-production-v1/locked_script.json'
VOICE={'name':'ko-KR-InJoonNeural','rate':'-5%','pitch':'+0Hz','provider':'edge-tts','version':'7.3.1'}


def stop_automatic_retry(error):
    raise error


def configure_no_retry():
    sys.path.insert(0,str(SIDE/'deps'))
    import edge_tts.communicate
    # Pinned 7.3.1 would otherwise retry HTTP403 after clock correction.
    edge_tts.communicate.DRM.handle_client_response_error=staticmethod(stop_automatic_retry)


def workspace_relative(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def save(path,data):
    with Path(path).open('x',encoding='utf8') as out:
        json.dump(data,out,ensure_ascii=False,indent=2);out.write('\n')


def owned(path):
    path=Path(path).resolve()
    if not path.is_relative_to(SIDE):
        raise ValueError('쓰기 범위는 narration/free-tts-v1 내부입니다.')
    return path


def prepare(script_path,out):
    script=p.reference(EP,script_path)
    chapters=p.parse_script(script.read_text(encoding='utf-8-sig'))
    out=owned(out);out.mkdir(parents=True,exist_ok=False)
    tokens=sorted({match.group() for chapter in chapters for paragraph in chapter['paragraphs']
                   for match in p.TOKEN.finditer(paragraph['text'])})
    dictionary={'revision':'korean-finance-readings-v1','aliases':p.ALIASES,'overrides':p.OVERRIDES,
        'observed_entries':{token:p.reading(token) for token in tokens},
        'rules':{'money':'한자 수사+금액 단위; 원문 숫자/단위 한 덩어리 보호',
                 'decimal':'정수 한자 수사, 점 이하 각 자리 영/일/이… 유지',
                 'year':'2006년=이천육 년; 2016년=이천십육 년',
                 'percent':'퍼센트; 4.0%는 영을 생략하지 않음'},
        'actual_listening':'pending_QA; original display text preserved'}
    save(out/'pronunciation_dictionary.json',dictionary)
    with (out/'source.md').open('xb') as target:
        target.write(script.read_bytes())
    plan={'status':'prepared_not_synthesized','script_path':str(script.relative_to(EP)),
        'script_sha256':p.digest(script),'media_contract_sha256':p.digest(CONTRACT),
        'phonetics_code_sha256':p.digest(SIDE/'production_narration.py'),
        'dictionary_sha256':p.digest(out/'pronunciation_dictionary.json'),
        'voice':VOICE,'paragraph_count':54,'chapter_count':10,'chapters':chapters,
        'full_synthesis_gate':str(LOCK.relative_to(EP)),'measured_audio_created':False}
    save(out/'prepared.json',plan)
    pending={'status':'pending_locked_script_and_actual_audio','script_path':plan['script_path'],
        'script_sha256':plan['script_sha256'],'voice':VOICE,'audio_revision':None,
        'chapters':[{'chapter':c['chapter'],'title':c['title'],'audio_file':None,
            'total_seconds':None,'last_speech_end_s':None,'paragraph_count':len(c['paragraphs']),
            'cues':[]} for c in chapters]}
    save(out/'final_timing.plan.json',pending)
    return plan


def gate_for_plan(prepared_path):
    prepared_path=Path(prepared_path).resolve()
    plan=p.load(prepared_path)
    gate=p.check_gate(EP,LOCK,plan['script_sha256'])
    if p.digest(CONTRACT)!=plan['media_contract_sha256']:
        raise p.GateError('미디어 계약 변경: 오프라인 준비부터 다시 수행해야 합니다.')
    if plan['voice']!=VOICE or p.digest(SIDE/'production_narration.py')!=plan['phonetics_code_sha256']:
        raise p.GateError('음성/발음 코드 변경: 준비본 무효')
    if p.digest(prepared_path.with_name('pronunciation_dictionary.json'))!=plan['dictionary_sha256']:
        raise p.GateError('발음 사전 변경: 준비본 무효')
    actual=p.parse_script(Path(gate['script_path']).read_text(encoding='utf-8-sig'))
    if actual!=plan['chapters']:
        raise p.GateError('준비본 원문/낭독 대조가 잠근 실제 대본과 다릅니다.')
    return plan,gate


async def paragraph_audio(paragraph,folder,script_sha,gate_sha):
    folder.mkdir(exist_ok=False)
    request={'script_sha256':script_sha,'voice':VOICE,'paragraph':paragraph['paragraph'],
        'text':paragraph['text'],'spoken_text':paragraph['spoken_text'],
        'lock_sha256':gate_sha,'boundary':'WordBoundary'}
    save(folder/'request.json',request)
    sys.path.insert(0,str(SIDE/'deps'))
    import edge_tts
    if edge_tts.__version__!=VOICE['version']:
        raise ValueError('검증한 edge-tts 버전이 아닙니다.')
    configure_no_retry()
    events=[]
    stream=edge_tts.Communicate(paragraph['spoken_text'],VOICE['name'],rate=VOICE['rate'],
        pitch=VOICE['pitch'],boundary='WordBoundary',connect_timeout=15,receive_timeout=60)
    try:
        with (folder/'audio.mp3').open('xb') as audio:
            async for event in stream.stream():
                if event['type']=='audio':
                    audio.write(event['data'])
                elif event['type'] in ('WordBoundary','SentenceBoundary'):
                    events.append(event)
    finally:
        save(folder/'native_boundaries.json',events)
    ffdir=ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc'
    subprocess.run([str(ffdir/'ffmpeg.exe'),'-nostdin','-v','error','-i',str(folder/'audio.mp3'),
        '-ac','1','-ar',str(p.RATE),'-c:a','pcm_s16le',str(folder/'audio.wav')],capture_output=True,check=True)
    _,frames,signal_end=p.read_pcm(folder/'audio.wav')
    cues=p.word_cues(paragraph['text'],paragraph['spoken_text'],paragraph['display_mapping'],events,paragraph['paragraph'])
    last_end=(events[-1]['offset']+events[-1]['duration'])/1e7
    if signal_end is None or max((e['offset']+e['duration'])/1e7 for e in events)>frames/p.RATE+0.15:
        raise ValueError('무음 또는 단어 경계/실측 길이 불일치')
    overlaps=[max(0,(a['offset']+a['duration']-b['offset'])/1e7) for a,b in zip(events,events[1:])]
    record={'status':'generated_measured_not_listened','script_sha256':script_sha,
        'paragraph':paragraph['paragraph'],'wave_file':str(folder/'audio.wav'),
        'audio_sha256':p.digest(folder/'audio.wav'),'request_sha256':p.digest(folder/'request.json'),
        'measured_seconds':frames/p.RATE,'last_word_end_s':last_end,
        'pcm_signal_end_s':signal_end,'max_native_word_overlap_s':max(overlaps,default=0),
        'word_count':len(events),'cues':cues}
    save(folder/'measured.json',record)
    return record


def cached_paragraph(folder,paragraph,script_sha):
    record=p.load(folder/'measured.json');request=p.load(folder/'request.json')
    if record['script_sha256']!=script_sha or request['spoken_text']!=paragraph['spoken_text'] or request['voice']!=VOICE:
        raise p.GateError('재사용 문단의 대본/낭독/음성 설정 불일치')
    if p.digest(folder/'request.json')!=record['request_sha256'] or p.digest(folder/'audio.wav')!=record['audio_sha256']:
        raise p.GateError('재사용 문단 SHA 불일치')
    return record


async def generate(prepared_path,out,resume=False,cache_only=False):
    plan,gate=gate_for_plan(prepared_path)  # Must precede mkdir, imports and ALL network.
    out=owned(out)
    final=SIDE/'final_timing.json'
    if final.exists():
        raise p.GateError('기존 final_timing 보존: 새 버전 인계/보존 절차를 먼저 수행해야 합니다.')
    if resume:
        previous=p.load(out/'run_inputs.json')
        if previous['prepared_sha256']!=p.digest(prepared_path):
            raise p.GateError('재개 입력 준비본이 다릅니다.')
        if cache_only and len(list((out/'paragraphs').glob('*/measured.json')))!=54:
            raise p.GateError('로컬 저장 재개에는 이미 실측된 54문단이 모두 필요합니다.')
    else:
        out.mkdir(parents=True,exist_ok=False)
        save(out/'run_inputs.json',{'prepared_sha256':p.digest(prepared_path),'gate':gate,'voice':VOICE,
            'contract_sha256':p.digest(CONTRACT),'at':datetime.now(timezone.utc).isoformat()})
    (out/'paragraphs').mkdir(exist_ok=True)
    contract=p.load(CONTRACT);chapters=[];current_paragraph=None;stage='start'
    try:
        for chapter in plan['chapters']:
            records=[]
            for paragraph in chapter['paragraphs']:
                current_paragraph=paragraph['paragraph_id'];stage='gate_check'
                _,current=gate_for_plan(prepared_path)
                if current['lock_sha256']!=gate['lock_sha256']:
                    raise p.GateError('합성 도중 잠금 파일 변경: 자동 진행 금지')
                folder=out/'paragraphs'/paragraph['paragraph_id']
                stage='paragraph_synthesis_or_cache'
                if resume and folder.exists():
                    record=cached_paragraph(folder,paragraph,plan['script_sha256'])
                else:
                    if cache_only:
                        raise p.GateError('로컬 재개에서 새 합성은 금지됩니다.')
                    record=await asyncio.wait_for(paragraph_audio(paragraph,folder,
                        plan['script_sha256'],gate['lock_sha256']),timeout=180)
                records.append(record)
            wav=out/f'chapter_{chapter["chapter"]:02}.wav'
            report=out/f'chapter_{chapter["chapter"]:02}.json'
            stage='chapter_pcm_assembly'
            if resume and report.exists():
                result=p.load(report)
                if p.digest(wav)!=result['audio_sha256']:
                    raise p.GateError('기존 장 WAV 무결성 실패')
            else:
                result=p.assemble_chapter(chapter['chapter'],chapter['title'],records,contract,wav)
                save(report,result)
            chapters.append(result)
            print(json.dumps({'chapter_completed':chapter['chapter'],'measured_seconds':result['total_seconds'],
                'cue_count':len(result['cues'])},ensure_ascii=False),flush=True)
        _,current=gate_for_plan(prepared_path)
        if current['lock_sha256']!=gate['lock_sha256']:
            raise p.GateError('최종 잠금 변경')
        stage='final_manifest'
        timing={'script_path':str(Path(gate['script_path']).relative_to(ROOT)).replace('\\','/'),
            'script_sha256':plan['script_sha256'],'voice':VOICE,'audio_revision':out.name,
            'chapters':chapters,'gate_evidence':gate,'media_contract_sha256':p.digest(CONTRACT),
            'status':'generated_measured_pending_listening_and_full_media_QA',
            'source_mapping':workspace_relative(prepared_path),
            'continuous_playback':False,'actual_listening':False,'paid_api_calls':0,
            'timing_scope':'per-chapter local time; editor applies brand intro/outro global offset map'}
        save(out/'final_timing.json',timing)
        save(final,timing)
        print(json.dumps({'status':timing['status'],'chapters':len(chapters),
            'total_seconds':sum(c['total_seconds'] for c in chapters),'out':str(out)},ensure_ascii=False))
    except Exception as exc:
        failure=out/('failure_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.json')
        save(failure,{'status':'failed','error_type':type(exc).__name__,
            'http_status':getattr(exc,'status',None),'no_automatic_retry':True,
            'partial_outputs_preserved':True,'completed_chapters':len(chapters),
            'current_paragraph':current_paragraph,'stage':stage,
            'local_reason':str(exc) if isinstance(exc,(p.GateError,ValueError)) else None,
            'trace_locations':[{'file':Path(f.filename).name,'line':f.lineno,'function':f.name}
                               for f in traceback.extract_tb(exc.__traceback__)]})
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='action',required=True)
    a=commands.add_parser('prepare');a.add_argument('--script',required=True);a.add_argument('--out',required=True)
    for action in ('check-gate','generate','finalize-existing'):
        a=commands.add_parser(action);a.add_argument('--prepared',required=True)
        if action in ('generate','finalize-existing'):
            a.add_argument('--out',required=True)
        if action=='generate':
            a.add_argument('--resume',action='store_true')
    args=parser.parse_args()
    try:
        if args.action=='prepare':
            plan=prepare(args.script,args.out)
            print(json.dumps({'status':plan['status'],'chapters':10,'paragraphs':54,'script_sha256':plan['script_sha256']},ensure_ascii=False))
        elif args.action=='check-gate':
            _,gate=gate_for_plan(args.prepared)
            print(json.dumps({'status':'gate_passed','script_sha256':gate['script_sha256']},ensure_ascii=False))
        elif args.action=='finalize-existing':
            asyncio.run(generate(args.prepared,args.out,resume=True,cache_only=True))
        else:
            asyncio.run(generate(args.prepared,args.out,args.resume))
    except p.GateError as exc:
        print(json.dumps({'status':'blocked_no_body_synthesis','reason':str(exc)},ensure_ascii=False))
        return 2
    except Exception as exc:
        print(json.dumps({'status':'failed','error_type':type(exc).__name__,'no_automatic_retry':True},ensure_ascii=False))
        return 1
    return 0


if __name__=='__main__':
    raise SystemExit(main())
