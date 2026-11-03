"""Exact two-paragraph v6 repair; all reuse and root publication are gate checked."""
import argparse
import asyncio
import copy
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import re
import shutil
import sys
import traceback

SIDE=Path(__file__).resolve().parent
sys.path.insert(0,str(SIDE))
import production_narration as p
import production_generate as g

OLD_SHA='babeb15213477f3f6dcb8e8ab958e1a4ccc691c53c1fca6ca9ceae99cc5f269b'
NEW_SHA='0368c9e08b8a2447ed429d9e78ab9a8238b2d823c27467362174600876a797b7'
BASE=SIDE/'production-injoon-v5'
OUT=SIDE/'production-injoon-v6'
PREP=SIDE/'prepare-v6/prepared.json'


def flatten(plan):
    return [row for chapter in plan['chapters'] for row in chapter['paragraphs']]


def compare_plans(old,new,changes):
    if old['script_sha256']!=OLD_SHA or new['script_sha256']!=NEW_SHA:
        raise ValueError('v5/v6 대본 SHA가 지정값과 다릅니다.')
    if changes['previous_sha256']!=OLD_SHA or changes['script_sha256']!=NEW_SHA:
        raise ValueError('changes.json 입력 SHA 불일치')
    if old['voice']!=new['voice'] or new['voice']!=g.VOICE:
        raise ValueError('음성/속도/모델 변경은 이번 수정 범위가 아닙니다.')
    a,b=flatten(old),flatten(new)
    if len(a)!=54 or len(b)!=54 or [(c['chapter'],c['title']) for c in old['chapters']]!=[(c['chapter'],c['title']) for c in new['chapters']]:
        raise ValueError('54문단/10장 구조 변경')
    declared={}
    for change in changes['changes']:
        match=re.fullmatch(r'C(\d+)_P(\d+)',change['paragraph_id'])
        if not match or int(match.group(1))!=change['chapter']:
            raise ValueError('변경 문단 ID 불일치')
        declared[int(match.group(2))]=change
    if set(declared)!={23,27}:
        raise ValueError('이번 수정은 전역 문단23·27만 허용됩니다.')
    changed=[];reuse=[]
    for before,after in zip(a,b):
        if before['paragraph_id']!=after['paragraph_id'] or before['paragraph']!=after['paragraph']:
            raise ValueError('문단 순서 변경')
        number=after['paragraph']
        if number in declared:
            change=declared[number]
            if before['text'].count(change['before'])!=1 or before['text'].replace(change['before'],change['after'])!=after['text']:
                raise ValueError('정확한 before/after 두 문장 범위를 넘었습니다.')
            if int(after['paragraph_id'][1:3])!=change['chapter']:
                raise ValueError('장/문단 연결 불일치')
            changed.append(after['paragraph_id'])
        else:
            if any(before[key]!=after[key] for key in ('text','spoken_text','display_mapping')):
                raise ValueError('변경 승인 밖 52문단의 원문/발음층 변경')
            reuse.append(after['paragraph_id'])
        if p.TOKEN.findall(before['text'])!=p.TOKEN.findall(after['text']):
            raise ValueError('숫자/금액/명칭 토큰 변경')
    return {'changed_ids':changed,'reused_ids':reuse,'reused_count':len(reuse),'changed_chapters':[5,6]}


def assert_reusable(paragraph,request,measured,voice):
    if request['script_sha256']!=OLD_SHA or measured['script_sha256']!=OLD_SHA:
        raise ValueError('재사용 음성의 생성 원본이 v5가 아닙니다.')
    if request['text']!=paragraph['text'] or request['spoken_text']!=paragraph['spoken_text'] or request['voice']!=voice:
        raise ValueError('재사용 원문/읽기표기/voice 조건 불일치')
    if request['paragraph']!=paragraph['paragraph'] or measured['paragraph']!=paragraph['paragraph']:
        raise ValueError('재사용 문단 번호 불일치')


def publish_versioned(root,expected_root_sha,timing):
    root=Path(root);current=root/'final_timing.json'
    if p.digest(current)!=expected_root_sha:
        raise ValueError('루트 타임맵이 준비 이후 변경되어 덮어쓸 수 없습니다.')
    original=current.read_bytes();archive=root/'final_timing.v5.json'
    if archive.exists():
        if archive.read_bytes()!=original:raise ValueError('기존 v5 아카이브 불일치')
    else:
        with archive.open('xb') as stream:stream.write(original)
    g.save(root/'final_timing.v6.json',timing)
    temporary=root/'final_timing.pending-v6.json'
    with temporary.open('xb') as stream:stream.write((root/'final_timing.v6.json').read_bytes())
    os.replace(temporary,current)


def offline():
    old=p.load(SIDE/'prepare-v5/prepared.json');new=p.load(PREP)
    changes=p.load(g.EP/'outputs/script-final-v6/changes.json')
    comparison=compare_plans(old,new,changes)
    final=p.load(BASE/'final_timing.json');technical=p.load(BASE/'technical_validation.json')
    if final['script_sha256']!=OLD_SHA or final['voice']!=new['voice']:
        raise ValueError('기준 v5 타임맵/음성 설정 불일치')
    root_sha=p.digest(SIDE/'final_timing.json')
    if p.digest(BASE/'final_timing.json')!=root_sha:
        raise ValueError('루트 타임맵은 기준 v5와 같아야 합니다.')
    fingerprints={row['paragraph_id']:row for row in technical['source_audio']}
    reuse=[]
    for paragraph in flatten(new):
        identifier=paragraph['paragraph_id'];folder=BASE/'paragraphs'/identifier
        measured=p.load(folder/'measured.json');request=p.load(folder/'request.json')
        fp=fingerprints[identifier]
        for filename,key in [('audio.mp3','mp3_sha256'),('audio.wav','wav_sha256'),('native_boundaries.json','native_boundaries_sha256')]:
            if p.digest(folder/filename)!=fp[key]:raise ValueError('v5 원본 지문 불일치')
        if p.digest(folder/'request.json')!=measured['request_sha256']:raise ValueError('v5 요청 지문 불일치')
        if identifier in comparison['reused_ids']:
            assert_reusable(paragraph,request,measured,new['voice'])
            reuse.append({'paragraph_id':identifier,'paragraph':paragraph['paragraph'],
                'source_script_sha256':OLD_SHA,'target_script_sha256':NEW_SHA,
                'display_spoken_voice_equal':True,'file_sha256':{f:p.digest(folder/f) for f in ('request.json','audio.mp3','audio.wav','native_boundaries.json','measured.json')}})
    result={'status':'offline_delta_verified_not_synthesized','comparison':comparison,
        'old_script_sha256':OLD_SHA,'new_script_sha256':NEW_SHA,'root_v5_sha256':root_sha,
        'old_final_timing_sha256':p.digest(BASE/'final_timing.json'),
        'prepared_sha256':p.digest(PREP),'contract_sha256':p.digest(g.CONTRACT),
        'reuse':reuse,'v5_file_sha256':{str(f.relative_to(BASE)):p.digest(f) for f in BASE.rglob('*') if f.is_file()},
        'new_spoken_paragraphs':[row for row in flatten(new) if row['paragraph_id'] in comparison['changed_ids']],
        'planned_new_tts_calls':2,'planned_reused_paragraphs':52,'planned_rebuilt_chapters':[5,6]}
    g.save(PREP.with_name('repair_manifest.json'),result)
    return result


def validate_manifest():
    manifest=p.load(PREP.with_name('repair_manifest.json'))
    plan,gate=g.gate_for_plan(PREP)
    if plan['script_sha256']!=NEW_SHA or p.digest(PREP)!=manifest['prepared_sha256']:
        raise p.GateError('v6 잠금/준비/수정 매니페스트 불일치')
    if p.digest(g.CONTRACT)!=manifest['contract_sha256'] or p.digest(SIDE/'final_timing.json')!=manifest['root_v5_sha256']:
        raise p.GateError('계약 또는 기준 루트 v5 타임맵 변경')
    for name,sha in manifest['v5_file_sha256'].items():
        if p.digest(BASE/name)!=sha:raise p.GateError('v5 보존 입력 변경: '+name)
    return manifest,plan,gate


def link_immutable(source,destination):
    source=Path(source).resolve();destination=Path(destination)
    if destination.exists():raise ValueError('기존 v6 파일 덮어쓰기 금지')
    try:os.link(source,destination);method='hardlink'
    except OSError:
        with source.open('rb') as src,destination.open('xb') as dst:shutil.copyfileobj(src,dst)
        method='copy'
    if p.digest(source)!=p.digest(destination):raise ValueError('재사용 사본 SHA 불일치')
    return method


def reuse_paragraph(paragraph,entry):
    source=BASE/'paragraphs'/paragraph['paragraph_id'];target=OUT/'paragraphs'/paragraph['paragraph_id']
    target.mkdir(exist_ok=False)
    request=p.load(source/'request.json');measured=p.load(source/'measured.json')
    assert_reusable(paragraph,request,measured,g.VOICE)
    methods={}
    for filename in ('request.json','audio.mp3','audio.wav','native_boundaries.json'):
        if p.digest(source/filename)!=entry['file_sha256'][filename]:raise ValueError('오프라인 검증 이후 원본 변경')
        methods[filename]=link_immutable(source/filename,target/filename)
    record=copy.deepcopy(measured)
    record.update(wave_file=str(target/'audio.wav'),reuse_status='exact_v5_content_voice_and_audio_reuse',
        applicable_script_sha256=NEW_SHA,source_script_sha256=OLD_SHA,
        source_measured_sha256=p.digest(source/'measured.json'),source_folder=str(source),reuse_methods=methods)
    g.save(target/'measured.json',record)
    g.save(target/'reuse_evidence.json',entry)
    return record


async def generate():
    manifest,plan,gate=validate_manifest()  # No mkdir or network before actual v6 gate.
    OUT.mkdir(exist_ok=False);(OUT/'paragraphs').mkdir()
    g.save(OUT/'run_inputs.json',{'gate':gate,'manifest_sha256':p.digest(PREP.with_name('repair_manifest.json')),
        'prepared_sha256':p.digest(PREP),'task_id':'narration-v6-two-paragraph-repair','new_tts_call_limit':2,
        'voice':g.VOICE,'at':datetime.now(timezone.utc).isoformat()})
    previous=p.load(BASE/'final_timing.json');entries={x['paragraph_id']:x for x in manifest['reuse']}
    records={};new_calls=0;reused=0;stage='start';current=None
    try:
        for paragraph in flatten(plan):
            current=paragraph['paragraph_id']
            if current in entries:
                stage='verified_local_reuse';record=reuse_paragraph(paragraph,entries[current]);reused+=1
            else:
                stage='v6_gate_before_new_synthesis'
                _,now=g.gate_for_plan(PREP)
                if now['lock_sha256']!=gate['lock_sha256']:raise p.GateError('수정 합성 도중 잠금 변경')
                if current not in manifest['comparison']['changed_ids'] or new_calls>=2:raise ValueError('두 문단 합성 범위를 벗어남')
                stage='new_synthesis';new_calls+=1
                record=await asyncio.wait_for(g.paragraph_audio(paragraph,OUT/'paragraphs'/current,NEW_SHA,gate['lock_sha256']),timeout=180)
                print(json.dumps({'new_paragraph_completed':current,'seconds':record['measured_seconds'],'word_events':record['word_count']},ensure_ascii=False),flush=True)
            records[current]=record
        if (new_calls,reused)!=(2,52):raise ValueError('실제 생성/재사용 수 불일치')
        chapters=[];chapter_changes=[];contract=p.load(g.CONTRACT)
        for source,old in zip(plan['chapters'],previous['chapters']):
            number=source['chapter'];wav=OUT/f'chapter_{number:02}.wav';stage='chapter_assembly'
            if number in (5,6):
                result=p.assemble_chapter(number,source['title'],[records[x['paragraph_id']] for x in source['paragraphs']],contract,wav)
            else:
                link_immutable(g.ROOT/old['audio_file'],wav)
                result=copy.deepcopy(old);result['audio_file']=g.workspace_relative(wav)
                for position,paragraph in zip(result['paragraphs'],source['paragraphs']):
                    position['wave_file']=records[paragraph['paragraph_id']]['wave_file']
                if p.digest(wav)!=old['audio_sha256']:raise ValueError('유지 대상 장 WAV SHA 변경')
            g.save(OUT/f'chapter_{number:02}.json',result);chapters.append(result)
            chapter_changes.append({'chapter':number,'rebuilt':number in (5,6),'previous_seconds':old['total_seconds'],
                'new_seconds':result['total_seconds'],'delta_seconds':round(result['total_seconds']-old['total_seconds'],9),
                'previous_audio_sha256':old['audio_sha256'],'new_audio_sha256':result['audio_sha256'],
                'same_audio_sha256':old['audio_sha256']==result['audio_sha256'],
                'previous_cues':len(old['cues']),'new_cues':len(result['cues'])})
        _,now=g.gate_for_plan(PREP)
        if now['lock_sha256']!=gate['lock_sha256']:raise p.GateError('최종 게시 전 잠금 변경')
        timing={'script_path':g.workspace_relative(gate['script_path']),'script_sha256':NEW_SHA,'voice':g.VOICE,
            'audio_revision':OUT.name,'chapters':chapters,'gate_evidence':gate,'media_contract_sha256':p.digest(g.CONTRACT),
            'source_mapping':g.workspace_relative(PREP),'status':'two_paragraph_repair_generated_measured_pending_narrow_ASR_QA',
            'previous_audio_revision':BASE.name,'reused_paragraphs':52,'newly_synthesized_paragraphs':2,
            'rebuilt_chapters':[5,6],'actual_listening':False,'ASR_QA_performed':False,'paid_api_calls':0,
            'timing_scope':'per-chapter local time; editor applies one brand global offset map'}
        stage='versioned_root_publication'
        g.save(OUT/'final_timing.json',timing)
        publish_versioned(SIDE,manifest['root_v5_sha256'],timing)
        summary={'task_id':'narration-v6-two-paragraph-repair','status':'generated_pending_technical_verification',
            'script_sha256':NEW_SHA,'new_tts_calls':new_calls,'reused_paragraphs':reused,'chapter_changes':chapter_changes,
            'previous_total_seconds':sum(x['total_seconds'] for x in previous['chapters']),
            'total_seconds':sum(x['total_seconds'] for x in chapters),'previous_cues':sum(len(x['cues']) for x in previous['chapters']),
            'new_cues':sum(len(x['cues']) for x in chapters),'paid_api_calls':0,'automatic_retries':0}
        g.save(OUT/'repair_summary.json',summary)
        packet={'task_id':'narration-v6-two-paragraph-repair','script_sha256':NEW_SHA,'next_owner':'QA Kant',
            'actual_listening_by_narration':False,'paragraphs':[]}
        for paragraph in flatten(plan):
            if paragraph['paragraph_id'] not in manifest['comparison']['changed_ids']:continue
            folder=OUT/'paragraphs'/paragraph['paragraph_id'];chapter=int(paragraph['paragraph_id'][1:3])
            packet['paragraphs'].append({'paragraph_id':f'C{chapter:02}_P{paragraph["paragraph"]:03}',
                'runtime_id':paragraph['paragraph_id'],'paragraph':paragraph['paragraph'],'chapter':chapter,
                'text':paragraph['text'],'spoken_text':paragraph['spoken_text'],
                'audio_file':g.workspace_relative(folder/'audio.wav'),'mp3_file':g.workspace_relative(folder/'audio.mp3'),
                'native_boundaries':g.workspace_relative(folder/'native_boundaries.json'),
                'audio_sha256':records[paragraph['paragraph_id']]['audio_sha256'],
                'measured_seconds':records[paragraph['paragraph_id']]['measured_seconds']})
        g.save(OUT/'qa_repair_packet.json',packet)
        print(json.dumps({k:summary[k] for k in ('status','new_tts_calls','reused_paragraphs','total_seconds','new_cues')},ensure_ascii=False))
    except Exception as exc:
        g.save(OUT/'failure.json',{'error_type':type(exc).__name__,'http_status':getattr(exc,'status',None),
            'paragraph':current,'stage':stage,'new_tts_invocations_started':new_calls,'reused':reused,
            'automatic_retry':False,'preserve_all_outputs':True,
            'local_reason':str(exc) if isinstance(exc,(ValueError,p.GateError)) else None,
            'trace':[{'file':Path(x.filename).name,'line':x.lineno,'function':x.name} for x in traceback.extract_tb(exc.__traceback__)]})
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['prepare-reuse','generate','check-gate'])
    args=parser.parse_args()
    try:
        if args.action=='prepare-reuse':
            result=offline();print(json.dumps(result['comparison'],ensure_ascii=False))
        elif args.action=='check-gate':
            _,_,gate=validate_manifest();print(json.dumps({'status':'gate_passed','script_sha256':gate['script_sha256']},ensure_ascii=False))
        else:asyncio.run(generate())
    except p.GateError as exc:
        print(json.dumps({'status':'blocked_no_synthesis','reason':str(exc)},ensure_ascii=False));return 2
    except Exception as exc:
        print(json.dumps({'status':'failed','error_type':type(exc).__name__,'automatic_retry':False},ensure_ascii=False));return 1
    return 0


if __name__=='__main__':raise SystemExit(main())
