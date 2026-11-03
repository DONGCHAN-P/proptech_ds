"""Local preparation; explicit main instruction plus exact dual-review lock before network."""
import argparse
import array
import asyncio
import copy
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import importlib.util
import inspect
import json
import math
from pathlib import Path
import re
import subprocess
import sys

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
EP=HERE.parent
ROOT=EP.parents[2]
OLD=EP.parent/'housing-choice-networth-20261020/narration/free-tts-v1'
DEPS=OLD/'deps'
SCRIPT_SHA='9658fc12dc76f67bb75d00e9c88170b167933ad8482dae1b752e4009d2aaf1a3'
LOCK=EP/'director/production-v1/locked_script.json'
MAIN_AUTH=HERE/'main_tts_authorization.json'
VOICE={'name':'ko-KR-InJoonNeural','rate':'-5%','pitch':'+0Hz','provider':'edge-tts','version':'7.3.1'}
CONTRACT={'canvas':{'fps':30},'leading_silence':{'chapter_1_s':0.6,'other_chapters_s':3.5},
    'paragraph_gap_s':0.35,'tail_s':{'chapters_1_to_9':1.2,'chapter_10_from_last_spoken_word':3.0},
    'captions':{'font':'Pretendard','font_size_px':40,'line_height_px':50,'text_width_px':1640,
        'text_height_px':124,'safe_width_px':1600,'max_explicit_lines':2,'font_shrink':False},
    'last_speech_basis':'max(last native word end, last PCM sample magnitude >=33); unlistened conservative bound',
    'source':'inherited first-episode audio convention; chapter hold estimates are not measured timing'}
spec=importlib.util.spec_from_file_location('first_episode_pure_helpers',OLD/'production_narration.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)


def load(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def norm(text):return re.sub(r'[\W_]+','',text)
def compact(text):return re.sub(r'\s+','',text)


def save(path,value):
    path=Path(path).resolve()
    if not path.is_relative_to(HERE):raise ValueError('Output outside new episode narration')
    with path.open('x',encoding='utf8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')


def dependencies():
    sys.path.insert(0,str(DEPS))
    import edge_tts
    from edge_tts.communicate import Communicate
    assert edge_tts.__version__==VOICE['version']
    assert 'boundary' in inspect.signature(Communicate).parameters
    ff=ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe'
    assert ff.is_file()
    return {'edge_tts_version':edge_tts.__version__,'shared_deps_readonly':str(DEPS),
        'WordBoundary_parameter_supported':True,'new_episode_WordBoundary_measured':False,
        'python':sys.version.split()[0],'ffmpeg':str(ff),'global_install':False,'network_calls':0,
        'helper_source':str(OLD/'production_narration.py'),'helper_sha256':sha(OLD/'production_narration.py')}


def mapping(scene):
    text,spoken=scene['display_text'],scene['spoken_text'];a=b=0;atoms=[]
    for t in scene['transforms']:
        x,y=t['display_start'],t['display_end'];u,v=t['spoken_start'],t['spoken_end']
        assert a<=x<y and b<=u<v
        assert text[x:y]==t['display'] and spoken[u:v]==t['spoken']
        assert text[a:x]==spoken[b:u],'Unrecorded pronunciation change'
        if x>a:atoms.append({'source_start':a,'source_end':x,'spoken_start':b,'spoken_end':u,'kind':'literal'})
        atoms.append({'source_start':x,'source_end':y,'spoken_start':u,'spoken_end':v,'kind':'pronunciation',
            'original':t['display'],'spoken':t['spoken']})
        a,b=y,v
    assert text[a:]==spoken[b:]
    if a<len(text):atoms.append({'source_start':a,'source_end':len(text),'spoken_start':b,'spoken_end':len(spoken),'kind':'literal'})
    return atoms


def position(q,source_pos):
    return p.spoken_position(q['display_mapping'],source_pos)


def protected_ranges(text,provided):
    ranges=[]
    for item in provided:
        a,b=item['display_start'],item['display_end']
        assert text[a:b]==item['display']
        ranges.append((a,b))
    patterns=[r'\d{4}년\s*\d{1,2}월(?:\s*\d{1,2}일)?',
        r'\d[\d,]*(?:\.\d+)?(?:\s*[조억만천백십]\s*\d[\d,]*)*(?:\s*[조억만천백십])?(?:\s*원|%포인트|%p|pp|%|㎡|개월|년|회|세)',
        r'\b(?:LTV|DSR|DTI)\b']
    for pattern in patterns:ranges.extend((m.start(),m.end()) for m in re.finditer(pattern,text))
    return sorted(set(ranges))


def safe_cut(q,index):
    return not any(a<index<b for a,b in q['protected_ranges'])


def phrase_score(left,right):
    token=left.split()[-1];score=0
    if token.endswith(','):score+=100
    if re.search(r'(면|지만|므로|때문에|면서|어도|아도|이며|으며|하고|이고|했고|려면|보다|뒤|때는|때|따라|대신|함께)$',token):score+=65
    if token in ('연','월','약','한','두','세','네','각각','더','수','그','이','같은','다른','최소','최대') or token.endswith('의'):score-=240
    if re.search(r'(하는|되는|있는|없는|남는|갚는|시키는|움직이는|바뀌는|들어가는|필요한|중요한|가능한|남은|많은|높은|작은|큰|쓸|할|될|살|빼야|갚아야|실거주)$',token):score-=160
    if len(compact(right))<=9 or len(right.split())<=2:score-=220
    return score


def lines(q,a,b):
    text=q['text'][a:b]
    if len(text)<=36:return [text]
    choices=[]
    for match in re.finditer(r'\s+',text):
        x,y=match.start(),match.end();left,right=text[:x],text[y:]
        if max(len(left),len(right))>40 or min(len(compact(left)),len(compact(right)))<10:continue
        if not safe_cut(q,a+x) or not safe_cut(q,a+y):continue
        score=phrase_score(left,right)
        if score<0:continue
        choices.append((score-2*abs(len(left)-len(right)),left,right))
    if choices:
        _,left,right=max(choices);return [left,right]
    return [text] if len(text)<=40 else []


def spans(q,events=None):
    text=q['text'];native_ends=None
    if events is not None:
        assert events and all(e['type']=='WordBoundary' for e in events),'Actual WordBoundary required'
        assert norm(''.join(e['text'] for e in events))==norm(q['spoken_text']),'Native spoken coverage mismatch'
        cursor=0;native_ends={0}
        for e in events:
            assert e['duration']>0 and e['offset']>=0
            cursor+=len(norm(e['text']));native_ends.add(cursor)
    def allowed(index):
        return safe_cut(q,index) and (native_ends is None or len(norm(q['spoken_text'][:position(q,index)])) in native_ends)
    sentence=[];start=0
    for m in re.finditer(r'[.!?。！？](?:\s+|$)',text):
        end=m.start()+1
        if allowed(end):sentence.append((start,end));start=m.end()
    if start<len(text):sentence.append((start,len(text)))
    result=[]
    for start,end in sentence:
        if lines(q,start,end) and len(compact(text[start:end]))>9:
            result.append((start,end));continue
        cuts=[(start,start)]+[(start+m.start(),start+m.end()) for m in re.finditer(r'\s+',text[start:end]) if allowed(start+m.start()) and allowed(start+m.end())]+[(end,end)]
        @lru_cache(None)
        def solve(i):
            best=None
            for j in range(i+1,len(cuts)):
                a,b=cuts[i][1],cuts[j][0];part=text[a:b]
                if len(compact(part))<=9 or not lines(q,a,b):continue
                remaining=solve(j) if j<len(cuts)-1 else (0,[])
                if remaining is None:continue
                score=remaining[0]-180-abs(len(part)-50)/2
                if j<len(cuts)-1:
                    grammar=phrase_score(part,text[cuts[j][1]:end])
                    if grammar<0:continue
                    score+=grammar
                candidate=(score,[(a,b)]+remaining[1])
                if best is None or candidate[0]>best[0]:best=candidate
            return best
        found=solve(0)
        if found is None:raise ValueError('Meaning split requires review: '+q['scene_id']+' '+text[start:end])
        result+=found[1]
    assert compact(''.join(text[a:b] for a,b in result))==compact(text)
    return result


def align(q,events):
    intervals=[];cursor=0;previous=-1
    for event in events:
        assert event['offset']>=previous;previous=event['offset']
        length=len(norm(event['text']));assert length>0
        intervals.append((cursor,cursor+length));cursor+=length
    cues=[]
    for i,(a,b) in enumerate(spans(q,events),1):
        sa,sb=position(q,a),position(q,b)
        x,y=len(norm(q['spoken_text'][:sa])),len(norm(q['spoken_text'][:sb]))
        touched=[j for j,(left,right) in enumerate(intervals) if left<y and right>x]
        first,last=touched[0],touched[-1]
        assert intervals[first][0]==x and intervals[last][1]==y
        begin=events[first]['offset']/1e7;end=(events[last]['offset']+events[last]['duration'])/1e7
        cues.append({'id':q['scene_id']+f'Q{i:03}','scene_id':q['scene_id'],'paragraph':q['paragraph'],
            'text':q['text'][a:b],'spoken_text':q['spoken_text'][sa:sb],'display_lines':lines(q,a,b),
            'start_s':begin,'end_s':end,'native_start_s':begin,'native_end_s':end,
            'source_start':a,'source_end':b,'spoken_start':sa,'spoken_end':sb,
            'first_word_index':first,'last_word_index':last,'timing_basis':'actual provider WordBoundary; semantic grouping; no interpolation'})
    for c,n in zip(cues,cues[1:]):c['end_s']=min(c['native_end_s'],n['start_s'])
    assert all(c['end_s']>c['start_s'] for c in cues)
    for key,expected in (('text',q['text']),('spoken_text',q['spoken_text'])):
        assert compact(''.join(c[key] for c in cues))==compact(expected)
    assert [i for c in cues for i in range(c['first_word_index'],c['last_word_index']+1)]==list(range(len(events)))
    return cues


def prepare(script,out):
    script=Path(script).resolve();out=Path(out).resolve()
    assert script.is_relative_to(EP) and sha(script)==SCRIPT_SHA
    assert out.is_relative_to(HERE)
    props=load(EP/'writer/scene_proposals_v2.json');notes=load(EP/'writer/pronunciation_notes_v2.json');numbers=load(EP/'writer/protected_numeric_v2.json')
    for item in (props,notes,numbers):assert item['frozen_script_sha256']==SCRIPT_SHA
    source=script.read_text(encoding='utf8');headings=list(re.finditer(r'^## (\d+)\. ([^\n]+)\n',source,re.M))
    assert [int(h.group(1)) for h in headings]==list(range(1,11))
    paragraphs=[];chapters=[]
    byscene={s['scene_id']:s for s in notes['scenes']};allscenes=props['scenes']
    for index,h in enumerate(headings):
        a=h.end();b=headings[index+1].start() if index+1<len(headings) else len(source);items=[]
        for match in re.finditer(r'\S[\s\S]*?(?=\n[ \t]*\n|\Z)',source[a:b]):
            text=match.group().rstrip();n=len(paragraphs);scene=allscenes[n]
            assert scene['chapter']==index+1 and scene['display_text']==text
            note=byscene[scene['scene_id']]
            assert note['display_text']==text and note['spoken_text']==scene['spoken_text']
            q={'paragraph':n+1,'paragraph_id':scene['scene_id'],'scene_id':scene['scene_id'],'chapter':index+1,
                'text':text,'spoken_text':scene['spoken_text'],'display_mapping':mapping(note),
                'script_source_start':a+match.start(),'script_source_end':a+match.start()+len(text)}
            protected=[t for t in numbers['protected_occurrences'] if t['scene_id']==scene['scene_id']]
            q['protected_ranges']=protected_ranges(text,protected)
            assert not re.search(r'\d|DSR|LTV|DTI|%|㎡',q['spoken_text'])
            q['meaning_plan']=[{'text':text[x:y],'spoken_text':q['spoken_text'][position(q,x):position(q,y)],
                'display_lines':lines(q,x,y),'source_start':x,'source_end':y,'start_s':None,'end_s':None,
                'timing_basis':'unmeasured local meaning plan; re-evaluate at actual native cuts'} for x,y in spans(q)]
            paragraphs.append(q);items.append(q)
        chapters.append({'chapter':index+1,'title':h.group(2).strip(),'paragraphs':items})
    assert len(paragraphs)==45 and len({q['scene_id'] for q in paragraphs})==45
    assert 'S034R' in {q['scene_id'] for q in paragraphs}
    assert sum(len(q['text']) for q in paragraphs)==6550
    inputs={str(path.relative_to(EP)):sha(path) for path in [script,EP/'writer/scene_proposals_v2.json',EP/'writer/pronunciation_notes_v2.json',EP/'writer/protected_numeric_v2.json',EP/'writer/handoff_v2.json']}
    out.mkdir(parents=True,exist_ok=False)
    (out/'source.md').write_bytes(script.read_bytes())
    save(out/'prepared.json',{'status':'offline_prepared_NOT_synthesized','script_path':str(script.relative_to(EP)),
        'script_sha256':SCRIPT_SHA,'canonical_expected':'outputs/script-final-v2/script_v2.md',
        'voice':VOICE,'chapters':chapters,'paragraph_count':45,'chapter_count':10,'display_characters':6550,
        'inputs':inputs,'pipeline_sha256':sha(__file__),'shared_helper_sha256':sha(OLD/'production_narration.py'),
        'dependencies':dependencies(),'audio_contract':CONTRACT,'audio_measured':False,
        'actual_listening':False,'model_network_TTS_calls':0})
    save(out/'pronunciation_dictionary.json',{'source':'writer/pronunciation_notes_v2.json',
        'script_sha256':SCRIPT_SHA,'dictionary':notes['pronunciation_dictionary'],
        'transforms':{s['scene_id']:s['transforms'] for s in notes['scenes']},
        'protected_occurrences':numbers['protected_occurrences'],'display_and_spoken_exact':True})
    save(out/'timing_plan.json',{'status':'not_measured_not_locked','script_sha256':SCRIPT_SHA,
        'estimated_narration_seconds':props['timing']['estimated_narration_seconds'],
        'estimated_minutes_with_chapter_holds':props['timing']['estimated_narration_plus_chapters_minutes'],
        'chapter_times':[{'chapter':c['chapter'],'audio_file':None,'total_seconds':None,'cues':[]} for c in chapters]})
    return load(out/'prepared.json')


def check_gate(prepared,authorization=MAIN_AUTH):
    plan=load(prepared)
    assert plan['script_sha256']==SCRIPT_SHA and plan['voice']==VOICE
    if not Path(authorization).is_file():raise p.GateError('Main explicit TTS instruction not recorded; local preparation only')
    auth=load(authorization)
    if not (auth.get('approved') is True and auth.get('network_tts_authorized') is True and
            auth.get('episode_id')==EP.name and auth.get('script_sha256')==SCRIPT_SHA and
            auth.get('prepared_sha256')==sha(prepared) and
            auth.get('cash_cap_krw')==0 and auth.get('paid_calls_authorized') is False and
            auth.get('source')=='main_direct_instruction' and auth.get('instruction_reference')):
        raise p.GateError('Main authorization is missing, wrong SHA or not cash0/free-only')
    if not LOCK.is_file() or load(LOCK).get('approved') is not True:raise p.GateError('Approved main locked_script.json absent')
    evidence=p.check_gate(EP,LOCK,SCRIPT_SHA)
    canonical=EP/'outputs/script-final-v2/script_v2.md'
    if Path(evidence['script_path']).resolve()!=canonical.resolve() or sha(canonical)!=SCRIPT_SHA:
        raise p.GateError('Lock must resolve byte-identical canonical v2 script')
    for name,digest in plan['inputs'].items():
        if sha(EP/name)!=digest:raise p.GateError('Prepared input changed: '+name)
    if sha(__file__)!=plan['pipeline_sha256'] or sha(OLD/'production_narration.py')!=plan['shared_helper_sha256']:
        raise p.GateError('Pipeline code changed; prepare a fresh version')
    if plan['audio_contract']!=CONTRACT:raise p.GateError('Audio contract changed')
    if sha(Path(prepared).parent/'source.md')!=SCRIPT_SHA:raise p.GateError('Prepared source changed')
    scenes=load(EP/'writer/scene_proposals_v2.json')['scenes']
    notes=load(EP/'writer/pronunciation_notes_v2.json')['scenes']
    numbers=load(EP/'writer/protected_numeric_v2.json')['protected_occurrences']
    paragraphs=[q for c in plan['chapters'] for q in c['paragraphs']]
    if len(paragraphs)!=45 or len(plan['chapters'])!=10:raise p.GateError('Prepared body structure changed')
    for i,(q,s,n) in enumerate(zip(paragraphs,scenes,notes),1):
        protected=[x for x in numbers if x['scene_id']==s['scene_id']]
        if not (q['paragraph']==i and q['scene_id']==s['scene_id']==n['scene_id'] and
            q['chapter']==s['chapter'] and q['text']==s['display_text']==n['display_text'] and
            q['spoken_text']==s['spoken_text']==n['spoken_text'] and
            q['display_mapping']==mapping(n) and
            q['protected_ranges']==[list(x) for x in protected_ranges(q['text'],protected)]):
            raise p.GateError('Prepared display/spoken/protection differs from frozen writer pair')
    for ref in evidence['receipts'].values():
        receipt=load(EP/ref['path'])
        if receipt.get('critical_issues',[])!=[]:raise p.GateError('Reviewer has unresolved critical issues')
    return plan,{**evidence,'main_instruction_sha256':sha(authorization)}


async def synthesize(q,folder,gate):
    # This is called only after the run gate, then again after every paragraph.
    folder.mkdir(exist_ok=False)
    save(folder/'request.json',{'script_sha256':SCRIPT_SHA,'scene_id':q['scene_id'],'voice':VOICE,
        'text':q['text'],'spoken_text':q['spoken_text'],'gate':gate,'boundary':'WordBoundary'})
    sys.path.insert(0,str(DEPS));import edge_tts
    import edge_tts.communicate
    assert edge_tts.__version__==VOICE['version']
    def reject_retry(error):raise error
    edge_tts.communicate.DRM.handle_client_response_error=staticmethod(reject_retry)
    stream=edge_tts.Communicate(q['spoken_text'],VOICE['name'],rate=VOICE['rate'],pitch=VOICE['pitch'],
        boundary='WordBoundary',connect_timeout=15,receive_timeout=60)
    events=[]
    try:
        with (folder/'audio.mp3').open('xb') as output:
            async for event in stream.stream():
                if event['type']=='audio':output.write(event['data'])
                elif event['type'] in ('WordBoundary','SentenceBoundary'):events.append(event)
    finally:save(folder/'native_boundaries.json',events)
    ff=ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe'
    subprocess.run([str(ff),'-nostdin','-v','error','-i',str(folder/'audio.mp3'),'-ac','1','-ar','24000','-c:a','pcm_s16le',str(folder/'audio.wav')],capture_output=True,check=True)
    raw,frames,signal=p.read_pcm(folder/'audio.wav')
    values=array.array('h',raw)
    assert signal is not None and not any(abs(v)>=32767 for v in values),'Silent or clipped PCM'
    maximum=max((e['offset']+e['duration'])/1e7 for e in events)
    assert maximum<=frames/24000+0.15
    overlaps=[max(0,(a['offset']+a['duration']-b['offset'])/1e7) for a,b in zip(events,events[1:])]
    record={'paragraph':q['paragraph'],'scene_id':q['scene_id'],'wave_file':str(folder/'audio.wav'),
        'audio_sha256':sha(folder/'audio.wav'),'measured_seconds':frames/24000,'last_word_end_s':maximum,
        'pcm_signal_end_s':signal,'word_count':len(events),'cues':align(q,events),
        'native_overlap_preserved':True,'max_native_word_overlap_s':max(overlaps,default=0),
        'pcm_peak_absolute':max(map(abs,values)),'clipped_samples':0,
        'request_sha256':sha(folder/'request.json'),'voice':VOICE,'actual_listening':False}
    save(folder/'measured.json',record);return record


async def generate(prepared,out,authorization=MAIN_AUTH):
    plan,gate=check_gate(prepared,authorization)  # Before mkdir, provider construction, or network.
    dependencies();out=Path(out).resolve()
    assert out.is_relative_to(HERE)
    out.mkdir(parents=True,exist_ok=False);(out/'paragraphs').mkdir()
    save(out/'run_inputs.json',{'prepared_sha256':sha(prepared),'gate':gate,'voice':VOICE,
        'started_utc':datetime.now(timezone.utc).isoformat(),'new_paragraphs':45,'cross_episode_audio_reuse':0})
    chapters=[];current=None
    try:
        for chapter in plan['chapters']:
            records=[]
            for q in chapter['paragraphs']:
                current=q['scene_id'];_,now=check_gate(prepared,authorization)
                if now!=gate:raise p.GateError('Lock/authorization changed during run')
                records.append(await asyncio.wait_for(synthesize(q,out/'paragraphs'/current,gate),180))
            result=p.assemble_chapter(chapter['chapter'],chapter['title'],records,CONTRACT,out/f'chapter_{chapter["chapter"]:02}.wav')
            assert result['pcm_frames']%800==0
            if chapter['chapter']==10:assert result['tail_from_last_spoken_s']>=3
            save(out/f'chapter_{chapter["chapter"]:02}.json',result);chapters.append(result)
        _,now=check_gate(prepared,authorization)
        if now!=gate:raise p.GateError('Final gate changed')
        save(out/'final_timing.json',{'script_path':gate['script_path'],'script_sha256':SCRIPT_SHA,
            'voice':VOICE,'audio_revision':out.name,'chapters':chapters,'gate_evidence':gate,
            'actual_listening':False,'ASR_QA_performed':False,'paid_api_calls':0,
            'status':'measured_pending_independent_audio_and_render_QA','source_mapping':str(prepared),
            'timing_scope':'chapter-local native WordBoundary; editor adds brand/chapter global anchors'})
    except Exception as error:
        save(out/'failure.json',{'scene_id':current,'error_type':type(error).__name__,
            'http_status':getattr(error,'status',None),'automatic_retry':False,
            'partial_outputs_preserved':True,'resume_requires_main_diagnosis_and_instruction':True})
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='action',required=True)
    a=sub.add_parser('prepare');a.add_argument('--script',required=True);a.add_argument('--out',required=True)
    for name in ('check-gate','generate'):
        a=sub.add_parser(name);a.add_argument('--prepared',required=True);a.add_argument('--authorization',default=str(MAIN_AUTH))
        if name=='generate':a.add_argument('--out',required=True)
    args=parser.parse_args()
    try:
        if args.action=='prepare':
            result=prepare(args.script,args.out);print(json.dumps({'status':result['status'],'paragraphs':45,'display_characters':6550}))
        elif args.action=='check-gate':
            _,result=check_gate(args.prepared,args.authorization);print(json.dumps({'status':'gate_passed','script_sha256':result['script_sha256']}))
        else:asyncio.run(generate(args.prepared,args.out,args.authorization))
    except Exception as error:
        print(json.dumps({'status':'blocked_or_failed_NO_automatic_retry','error_type':type(error).__name__,
            'reason':str(error) if isinstance(error,(ValueError,p.GateError,AssertionError)) else None},ensure_ascii=False));return 2
    return 0


if __name__=='__main__':raise SystemExit(main())
