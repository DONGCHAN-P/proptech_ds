"""Resume missing scenes and preserve raw % WordBoundary events without interpolation."""
import asyncio,hashlib,importlib.util,json,math,shutil,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;EP=HERE.parents[1];ROOT=EP.parents[2]
spec=importlib.util.spec_from_file_location('original_builder',HERE/'build_narration.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
read=m.load;save=m.save;sha=m.digest
planpath=HERE/'prepare-r2/prepared.json';plan=read(planpath)
lock=EP/'director/rebuild-v2/locked_script_r2.json'
auth=EP/'director/rebuild-v2/free_edge_recovery_authorization_r2.json'
old=HERE/'audio-r2';out=HERE/'audio-r2-recovered'
raw_validate=m.validate_events;raw_synth=m.synthesize_scene;merges=[];network=[];cached=[]

def normalize_events(q,events):
    """A separately timed percent sign is speech; extend its preceding word to its real end."""
    if all(m.base.norm(e['text']) for e in events):return raw_validate(q,events)
    original=[dict(e) for e in events];fixed=[]
    for i,e in enumerate(original):
        e=dict(e);e['raw_event_indices']=[i]
        if m.base.norm(e['text']):fixed.append(e);continue
        m.require(e['text']=='%' and fixed and e['offset']>=fixed[-1]['offset'],'Unexpected empty-normalized provider symbol')
        prior=fixed[-1];prior['text']+=e['text'];prior['duration']=max(prior['offset']+prior['duration'],e['offset']+e['duration'])-prior['offset'];prior['raw_event_indices'].append(i)
    m.require(''.join(e['text'] for e in original)==''.join(e['text'] for e in fixed),'Symbol merge text preservation')
    m.require([i for e in fixed for i in e['raw_event_indices']]==list(range(len(original))),'Raw event coverage')
    raw_validate(q,fixed);events[:]=fixed
    merges.append({'scene_id':q['scene_id'],'raw_count':len(original),'aligned_count':len(fixed),'method':'adjacent percent-symbol event joined to preceding word; native start and max actual end; no interpolation','merged_events':[e for e in fixed if len(e['raw_event_indices'])>1]})

async def synthesize(q,folder):
    source=old/q['scene_id']
    if not (source/'original.mp3').is_file():
        m.require(len(network)<16,'Remaining free network call limit');network.append(q['scene_id'])
        result=await raw_synth(q,folder)
        if any(r['scene_id']==q['scene_id'] for r in merges):save(folder/'alignment_WordBoundary.json',result[1])
        return result
    cached.append(q['scene_id']);folder.mkdir(exist_ok=False)
    request=read(source/'request.json');m.require(request['text']==q['spoken_text'] and request['voice']==m.VOICE,'Cache text/voice mismatch')
    for name in ['original.mp3','WordBoundary.json','other_events.json','request.json']:
        shutil.copy2(source/name,folder/name)
    events=read(folder/'WordBoundary.json');normalize_events(q,events)
    save(folder/'alignment_WordBoundary.json',events)
    if (source/'original.wav').is_file():shutil.copy2(source/'original.wav',folder/'original.wav')
    else:m.ffmpeg_convert(folder/'original.mp3',folder/'original.wav',m.HZ)
    values=m.pcm_read(folder/'original.wav');signal=[i for i,v in enumerate(values) if abs(v)>=33]
    m.require(signal and max(map(abs,values))<32767,'Cache PCM silent/clipped')
    native_end=math.ceil(max(e['offset']+e['duration'] for e in events)/1e7*m.HZ)
    m.require(native_end<=len(values)+round(.15*m.HZ),'Cache native end/PCM mismatch')
    return values,events,{'source_pcm_frames':len(values),'signal_start_s':signal[0]/m.HZ,'signal_end_s':(signal[-1]+1)/m.HZ,'first_word_start_s':math.floor(events[0]['offset']/1e7*m.HZ)/m.HZ,'last_word_end_s':native_end/m.HZ,'pcm_peak':max(map(abs,values)),'pcm_preserved':True,'cues':m.align_sentence(q,events)}

def gate(prepared,lockpath,authorization,outpath):
    a=read(auth);l=read(lock)
    m.require(all(Path(x).resolve()==y.resolve() for x,y in [(prepared,planpath),(lockpath,lock),(authorization,auth),(outpath,out)]),'Exact recovery paths')
    m.require(a['approved'] is True and a['max_additional_network_calls']==16 and a['automatic_retries']==0,'Recovery approval')
    m.require(a['script_sha256']==plan['script_sha256']==l['script_sha256'] and l['approved'] and l['claude_approved'],'Exact approved source')
    m.require(a['prepared_sha256']==sha(planpath) and a['lock_sha256']==sha(lock) and a['recovery_code_sha256']==sha(Path(__file__)),'Recovery input pins')
    m.require(plan['pipeline_inputs']==m.pins() and not out.exists(),'Original module preserved and new output')
    for name,digest in plan['inputs'].items():m.require(sha(ROOT/name)==digest,'Prepared inputs changed')
    return plan,{'authorization_path':m.relative(auth),'authorization_sha256':sha(auth),'lock_path':m.relative(lock),'lock_sha256':sha(lock),'prepared_sha256':sha(planpath),'script_sha256':plan['script_sha256'],'recovery_code_sha256':sha(Path(__file__))}

def main():
    if '--test' in sys.argv:
        q=next(q for q in plan['scenes'] if q['scene_id']=='R013');e=read(old/'R013/WordBoundary.json')
        try:raw_validate(q,e)
        except m.BuildError:pass
        else:raise AssertionError('Expected exact provider percent-event reproduction')
        normalize_events(q,e);c=m.align_sentence(q,e)
        assert m.base.compact(''.join(x['text'] for x in c))==m.base.compact(q['text'])
        assert len(e)==52 and len(merges)==1 and len(merges[0]['merged_events'])==2
        print(json.dumps({'test':'actual_R013_percent_events_reproduced_then_fixed','raw_events':54,'aligned_events':52,'interpolation':False}));return
    m.check_gate=gate;m.validate_events=normalize_events;m.synthesize_scene=synthesize
    try:asyncio.run(m.generate(planpath,lock,auth,out))
    finally:
        if (out/'run_receipt.json').exists():
            receipt=read(out/'run_receipt.json');receipt['engine_scene_iterations']=receipt['network_attempts_started'];receipt['network_attempts_started']=len(network);receipt['max_network_attempts']=16;receipt['cache_scene_count']=len(cached);receipt['cached_scene_ids']=cached;receipt['actual_network_scene_ids']=network;receipt['cache_reused']=True
            save(out/'run_receipt.json',receipt)
            save(out/'recovery_receipt.json',{'previous_network_calls':read(old/'run_receipt.json')['network_attempts_started'],'additional_network_calls':len(network),'total_network_calls':read(old/'run_receipt.json')['network_attempts_started']+len(network),'cached_scene_ids':cached,'symbol_merges':merges,'automatic_retries':0,'paid_calls':0,'actual_listening':False})
    print(json.dumps({'status':'recovered_actual_timing_ready','timing':m.relative(out/'final_timing.json'),'additional_network_calls':len(network)}))

if __name__=='__main__':main()
