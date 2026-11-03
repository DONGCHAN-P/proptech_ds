"""Four-paragraph clarity delta. Prepare offline; new exact-plan main approval before TTS."""
import argparse
import asyncio
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import sys

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('v2_runtime_readonly',HERE/'production_v1.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
BASE=HERE/'production-injoon-v2'
BASE_PREPARED=HERE/'prepare-v2-r2/prepared.json'
PREPARED=HERE/'prepare-v3/prepared.json'
MANIFEST=HERE/'prepare-v3/delta_manifest.json'
AUTH=HERE/'main_tts_authorization_v3.json'
OUT=HERE/'production-injoon-v3'
TARGETS=['S014','S019','S024','S030']
VOICE={**r.VOICE,'rate':'-15%'}
FILES=('audio.mp3','audio.wav','native_boundaries.json','request.json','measured.json')
REPLACEMENTS={'DSR':'디 에스 알','DTI':'디 티 아이','5억 103만 원':'오억, 일백삼만 원',
    '4,902만 원':'사천구백 이만 원','10억 2,902만 원':'십억, 이천구백 이만 원'}
MONEY={'5억 103만 원':('오억, 일백삼만 원',501030000),
    '4,902만 원':('사천구백 이만 원',49020000),'10억 2,902만 원':('십억, 이천구백 이만 원',1029020000)}


def text_sha(text):return hashlib.sha256(text.encode('utf8')).hexdigest()


def korean_amount(text):
    """Independent isolated Korean cardinal parser; never parses mixed ASR transcripts."""
    text=re.sub(r'[\s,，]','',text).removesuffix('원')
    digits={s:i for i,s in enumerate('영일이삼사오육칠팔구')};small={'십':10,'백':100,'천':1000};big={'만':10000,'억':100000000,'조':1000000000000}
    total=section=number=0
    for char in text:
        if char in digits:number=digits[char]
        elif char in small:section+=(number or 1)*small[char];number=0
        elif char in big:total+=(section+number or 1)*big[char];section=number=0
        else:raise ValueError('Unsupported isolated numeral')
    return total+section+number


def phonetic_delta(q):
    result=copy.deepcopy(q);text=q['text'];edits=[];diff=[]
    for display,spoken in REPLACEMENTS.items():
        for match in re.finditer(re.escape(display),text):
            a,b=match.span();old=q['spoken_text'][r.position(q,a):r.position(q,b)]
            edits.append((a,b,spoken));diff.append({'display_start':a,'display_end':b,'display':display,
                'spoken_before':old,'spoken_after':spoken,'reason':'letter spacing / phonetic pause only'})
    overrides=[(a,b) for a,b,_ in edits]
    for atom in q['display_mapping']:
        if atom['kind']=='pronunciation' and not any(a<atom['source_end'] and b>atom['source_start'] for a,b in overrides):
            edits.append((atom['source_start'],atom['source_end'],q['spoken_text'][atom['spoken_start']:atom['spoken_end']]))
    atoms=[];pieces=[];cursor=spoken_cursor=0
    for a,b,spoken in sorted(edits):
        assert a>=cursor
        if a>cursor:
            literal=text[cursor:a];pieces.append(literal)
            atoms.append({'source_start':cursor,'source_end':a,'spoken_start':spoken_cursor,'spoken_end':spoken_cursor+len(literal),'kind':'literal'});spoken_cursor+=len(literal)
        pieces.append(spoken);atoms.append({'source_start':a,'source_end':b,'spoken_start':spoken_cursor,
            'spoken_end':spoken_cursor+len(spoken),'kind':'pronunciation','original':text[a:b],'spoken':spoken})
        spoken_cursor+=len(spoken);cursor=b
    if cursor<len(text):
        literal=text[cursor:];pieces.append(literal);atoms.append({'source_start':cursor,'source_end':len(text),
            'spoken_start':spoken_cursor,'spoken_end':spoken_cursor+len(literal),'kind':'literal'})
    result['spoken_text']=''.join(pieces);result['display_mapping']=atoms
    assert result['text']==q['text'] and not re.search(r'\d|DSR|DTI',result['spoken_text'])
    return result,diff


def fixed_align(q,events):
    assert events and all(e['type']=='WordBoundary' for e in events)
    assert r.norm(''.join(e['text'] for e in events))==r.norm(q['spoken_text'])
    intervals=[];cursor=0;previous=-1
    for e in events:
        assert e['duration']>0 and e['offset']>=previous;previous=e['offset']
        size=len(r.norm(e['text']));assert size;intervals.append((cursor,cursor+size));cursor+=size
    result=[]
    for template in q['fixed_cues']:
        a,b=template['source_start'],template['source_end'];sa,sb=r.position(q,a),r.position(q,b)
        left,right=len(r.norm(q['spoken_text'][:sa])),len(r.norm(q['spoken_text'][:sb]))
        touched=[i for i,(x,y) in enumerate(intervals) if x<right and y>left]
        first,last=touched[0],touched[-1]
        if intervals[first][0]!=left or intervals[last][1]!=right:
            raise ValueError('Native event crosses frozen meaning cue; no estimated timing permitted')
        begin=events[first]['offset']/1e7;end=(events[last]['offset']+events[last]['duration'])/1e7
        result.append({**template,'scene_id':q['scene_id'],'paragraph':q['paragraph'],
            'spoken_text':q['spoken_text'][sa:sb],'spoken_start':sa,'spoken_end':sb,
            'start_s':begin,'end_s':end,'native_start_s':begin,'native_end_s':end,
            'first_word_index':first,'last_word_index':last,
            'timing_basis':'actual provider WordBoundary; frozen v2 display meaning units; no interpolation'})
    for a,b in zip(result,result[1:]):a['end_s']=min(a['native_end_s'],b['start_s'])
    assert all(c['end_s']>c['start_s'] for c in result)
    for key,expected in (('text',q['text']),('spoken_text',q['spoken_text'])):
        assert r.compact(''.join(c[key] for c in result))==r.compact(expected)
    assert [i for c in result for i in range(c['first_word_index'],c['last_word_index']+1)]==list(range(len(events)))
    return result


def source_gate():
    evidence=r.p.check_gate(r.EP,r.LOCK,r.SCRIPT_SHA)
    assert Path(evidence['script_path']).resolve()==(r.EP/'outputs/script-final-v2/script_v2.md').resolve()
    return evidence


def verify_pins(plan):
    assert r.sha(BASE/'final_timing.json')==plan['base_final_timing_sha256']
    for item in plan['paragraph_pins']:
        for name,digest in item['files'].items():assert r.sha(BASE/'paragraphs'/item['scene_id']/name)==digest
    for item in plan['chapter_pins']:assert r.sha(BASE/f'chapter_{item["chapter"]:02}.wav')==item['audio_sha256']


def prepare():
    base_plan,base_gate=r.check_gate(BASE_PREPARED)
    old=r.load(BASE/'final_timing.json');plan=copy.deepcopy(base_plan)
    packet_path=r.EP/'qa/audio-v1/v3_delta/target_packet.json';packet=r.load(packet_path)
    assert packet['script_sha256']==r.SCRIPT_SHA and packet['target_paragraphs']==TARGETS
    assert packet['target_count']==4 and packet['unmodified_paragraph_count']==41
    qa_manifest=Path(packet['v2_raw_manifest']['path'])
    assert r.sha(qa_manifest)==packet['v2_raw_manifest']['sha256']
    paragraphs=[];diffs=[];pins=[]
    for ch in plan['chapters']:
        for index,q in enumerate(ch['paragraphs']):
            original=copy.deepcopy(q);folder=BASE/'paragraphs'/q['scene_id'];request=r.load(folder/'request.json')
            assert request['text']==q['text'] and request['spoken_text']==q['spoken_text'] and request['voice']==r.VOICE
            q,edits=phonetic_delta(q) if q['scene_id'] in TARGETS else (q,[])
            fixed=[c for c in old['chapters'][ch['chapter']-1]['cues'] if c['scene_id']==q['scene_id']]
            q['fixed_cues']=[{k:c[k] for k in ('text','display_lines','source_start','source_end')}|{'id':c['id'].split('_',1)[1]} for c in fixed]
            q['meaning_plan']=[{**c,'spoken_text':q['spoken_text'][r.position(q,c['source_start']):r.position(q,c['source_end'])],
                'start_s':None,'end_s':None,'timing_basis':'frozen display unit; new timing unmeasured'} for c in q['fixed_cues']]
            ch['paragraphs'][index]=q;paragraphs.append(q)
            item={'scene_id':q['scene_id'],'chapter':q['chapter'],'reused':q['scene_id'] not in TARGETS,
                'display_sha256':text_sha(q['text']),'spoken_before_sha256':text_sha(original['spoken_text']),
                'spoken_after_sha256':text_sha(q['spoken_text']),'voice_before':r.VOICE,
                'voice_after':VOICE if edits else r.VOICE,'files':{name:r.sha(folder/name) for name in FILES}}
            pins.append(item)
            if edits:diffs.append({'scene_id':q['scene_id'],'chapter':q['chapter'],'display_unchanged':q['text'],
                'spoken_before':original['spoken_text'],'spoken_after':q['spoken_text'],'changes':edits,
                'rate_before':'-5%','rate_after':'-15%','fixed_cue_ids':[c['id'] for c in fixed]})
    assert len(diffs)==4 and sum(len(q['fixed_cues']) for q in paragraphs)==150
    for display,(spoken,value) in MONEY.items():assert korean_amount(spoken)==value
    out=PREPARED.parent;out.mkdir(exist_ok=False)
    plan.update({'status':'v3_delta_prepared_NO_synthesis','script_sha256':r.SCRIPT_SHA,
        'voice':r.VOICE,'voice_overrides':{s:VOICE for s in TARGETS},'generator_sha256':r.sha(__file__),
        'base_prepared_sha256':r.sha(BASE_PREPARED),'base_final_timing_sha256':r.sha(BASE/'final_timing.json'),
        'source_gate':source_gate(),'target_scenes':TARGETS,'paragraph_pins':pins,
        'chapter_pins':[{'chapter':c['chapter'],'audio_sha256':c['audio_sha256'],'json_sha256':r.sha(BASE/f'chapter_{c["chapter"]:02}.json')} for c in old['chapters']],
        'qa_packet':{'path':str(packet_path),'sha256':r.sha(packet_path),'raw_manifest_sha256':r.sha(qa_manifest)},
        'audio_measured':False,'new_audio_created':False,'new_network_calls':0})
    r.save(PREPARED,plan)
    r.save(out/'spoken_diff.json',{'script_sha256':r.SCRIPT_SHA,'scenes':diffs,
        'numeric_validation':[{'display':d,'spoken':s,'parsed_krw':korean_amount(s),'expected_krw':v} for d,(s,v) in MONEY.items()],
        'linguistic_scope':'일백삼 is a formal explicit 103 reading; commas separate 억/만 blocks only. Space before 이만 stays within a single amount, no new arithmetic decomposition.',
        'actual_listening_or_naturalness_verified':False})
    r.save(out/'unchanged41_pins.json',{'paragraphs':[x for x in pins if x['reused']],'count':41})
    r.save(MANIFEST,{'task_id':'narration-v3-pronunciation-clarity-delta','status':'PREPARED_WAITING_EXACT_MAIN_PLAN_INSTRUCTION',
        'script_sha256':r.SCRIPT_SHA,'prepared_sha256':r.sha(PREPARED),'generator_sha256':r.sha(__file__),
        'spoken_diff_sha256':r.sha(out/'spoken_diff.json'),'unchanged41_pins_sha256':r.sha(out/'unchanged41_pins.json'),
        'target_scenes':TARGETS,'new_network_calls_max':4,'unchanged_raw_paragraphs':41,'meaning_cues_frozen':150,
        'display_and_financial_values_unchanged':True,'rebuild_chapters':[4,5,6,7],
        'identical_audio_chapters_expected':[1,2,3,8,9,10],'voice_override':VOICE,
        'preserve_v2_and_root_timing':True,'TTS_calls_performed':0,'cash_cap_krw':0,'paid_fallback':False,
        'source_gate':plan['source_gate'],'qa_packet':plan['qa_packet'],
        'post_generation_required':'all45 raw/source/native/PCM/clip/30fps/CTA checks plus 41pins/6chapterSHA delta; Kant only4 paragraph ASR; no hearing claim'})
    verify_pins(plan)
    return plan


def gate(verify=True):
    plan=r.load(PREPARED);manifest=r.load(MANIFEST)
    if not AUTH.is_file():raise r.p.GateError('Exact v3 plan main instruction absent; NO TTS')
    auth=r.load(AUTH)
    expected={'approved':True,'network_tts_authorized':True,'source':'main_direct_instruction',
        'episode_id':r.EP.name,'script_sha256':r.SCRIPT_SHA,'prepared_sha256':r.sha(PREPARED),
        'generator_sha256':r.sha(__file__),'delta_manifest_sha256':r.sha(MANIFEST),
        'target_scenes':TARGETS,'new_network_calls_max':4,'cash_cap_krw':0,'paid_calls_authorized':False}
    if any(auth.get(k)!=v for k,v in expected.items()) or not auth.get('instruction_reference'):
        raise r.p.GateError('Exact prepared/generator/delta/auth pins or free4-call scope mismatch')
    if plan['generator_sha256']!=r.sha(__file__) or manifest['prepared_sha256']!=r.sha(PREPARED):
        raise r.p.GateError('Prepared v3 generator changed')
    if source_gate()!=plan['source_gate']:raise r.p.GateError('Original approved script/lock/receipts changed')
    if r.sha(BASE_PREPARED)!=plan['base_prepared_sha256']:raise r.p.GateError('Baseline preparation changed')
    if verify:verify_pins(plan)
    return plan,{**plan['source_gate'],'v3_main_instruction_sha256':r.sha(AUTH),
        'v3_prepared_sha256':r.sha(PREPARED),'v3_generator_sha256':r.sha(__file__),'v3_delta_manifest_sha256':r.sha(MANIFEST)}


async def generate():
    plan,evidence=gate();r.dependencies()
    OUT.mkdir(exist_ok=False);(OUT/'paragraphs').mkdir()
    r.save(OUT/'run_inputs.json',{'gate':evidence,'new_paragraphs':4,'reused_paragraphs':41,'automatic_retry':False})
    chapters=[];calls=0;current=None
    try:
        for ch in plan['chapters']:
            records=[]
            for q in ch['paragraphs']:
                current=q['scene_id'];folder=OUT/'paragraphs'/current
                if current in TARGETS:
                    if gate(False)[1]!=evidence:raise r.p.GateError('Gate changed during repair')
                    old_voice,old_align=r.VOICE,r.align
                    try:
                        r.VOICE=VOICE;r.align=fixed_align;calls+=1
                        record=await asyncio.wait_for(r.synthesize(q,folder,evidence),180)
                    finally:r.VOICE=old_voice;r.align=old_align
                else:
                    folder.mkdir();pin=next(x for x in plan['paragraph_pins'] if x['scene_id']==current)
                    for name,digest in pin['files'].items():
                        shutil.copyfile(BASE/'paragraphs'/current/name,folder/name);assert r.sha(folder/name)==digest
                    record=r.load(folder/'measured.json');record['wave_file']=str(folder/'audio.wav')
                r.save(folder/'assembly_record.json',record);records.append(record)
            wave=OUT/f'chapter_{ch["chapter"]:02}.wav'
            if ch['chapter'] in (4,5,6,7):
                result=r.p.assemble_chapter(ch['chapter'],ch['title'],records,r.CONTRACT,wave)
            else:
                shutil.copyfile(BASE/wave.name,wave);result=r.load(BASE/f'chapter_{ch["chapter"]:02}.json')
                result['audio_file']=str(wave.relative_to(r.ROOT)).replace('\\','/')
                for placement,record in zip(result['paragraphs'],records):placement['wave_file']=record['wave_file']
                assert r.sha(wave)==result['audio_sha256']
            r.save(OUT/f'chapter_{ch["chapter"]:02}.json',result);chapters.append(result)
        assert calls==4 and gate(False)[1]==evidence
        old=r.load(BASE/'final_timing.json')
        keys=('id','scene_id','paragraph','text','display_lines','source_start','source_end')
        assert [[{k:c[k] for k in keys} for c in ch['cues']] for ch in chapters]==[[{k:c[k] for k in keys} for c in ch['cues']] for ch in old['chapters']]
        verify_pins(plan)
        r.save(OUT/'final_timing.json',{'script_path':evidence['script_path'],'script_sha256':r.SCRIPT_SHA,
            'voice':r.VOICE,'paragraph_voice_overrides':{s:VOICE for s in TARGETS},'audio_revision':OUT.name,
            'previous_audio_revision':BASE.name,'chapters':chapters,'gate_evidence':evidence,'source_mapping':str(PREPARED),
            'new_paragraphs':4,'reused_paragraphs':41,'actual_listening':False,'ASR_QA_performed':False,
            'paid_api_calls':0,'status':'measured_pending_v3_delta_technical_and_independent_QA',
            'timing_scope':'chapter-local native WordBoundary; original150 display cues frozen'})
    except Exception as error:
        r.save(OUT/'failure.json',{'scene_id':current,'error_type':type(error).__name__,'calls_attempted':calls,
            'http_status':getattr(error,'status',None),'automatic_retry':False,'partial_outputs_preserved':True})
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=('prepare','check-gate','generate'));args=parser.parse_args()
    try:
        if args.action=='prepare':prepare();print(json.dumps({'status':'prepared_NO_synthesis','changed':4,'reused':41,'cues':150}))
        elif args.action=='check-gate':gate();print(json.dumps({'status':'v3_exact_gate_passed'}))
        else:asyncio.run(generate())
    except Exception as error:
        print(json.dumps({'status':'blocked_or_failed_no_retry','error_type':type(error).__name__,
            'reason':str(error) if isinstance(error,(ValueError,r.p.GateError,AssertionError)) else None},ensure_ascii=False));raise SystemExit(2)
