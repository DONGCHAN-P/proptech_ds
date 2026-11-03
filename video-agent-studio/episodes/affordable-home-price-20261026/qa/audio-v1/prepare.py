"""Offline preparation only. Reuse model/dependency files without copying weights."""
import hashlib,json,os,socket,sys
from pathlib import Path
from datetime import datetime,timezone
sys.dont_write_bytecode=True
QA=Path(__file__).resolve().parent;EP=QA.parents[1];ROOT=EP.parents[2]
sys.path.insert(0,str(QA))
OLD=EP.parent/'housing-choice-networth-20261020/qa/private-production-v1/asr'
SHA='9658fc12dc76f67bb75d00e9c88170b167933ad8482dae1b752e4009d2aaf1a3'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()
def pin(p):return {'path':str(p.resolve()),'sha256':sha(p)}
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
    from checks import compare,numbers
    script=EP/'writer/script_v2.md';ledgerp=EP/'writer/protected_numeric_v2.json';notesp=EP/'writer/pronunciation_notes_v2.json';preparedp=EP/'narration/prepare-v2-r2/prepared.json'
    assert sha(script)==SHA
    ledger,notes,prepared=map(read,[ledgerp,notesp,preparedp]);assert ledger['frozen_script_sha256']==notes['frozen_script_sha256']==prepared['script_sha256']==SHA
    models={}
    for name,folder,manifestp in [('small',OLD/'models/systran-faster-whisper-small',OLD/'model_manifest.json'),('medium',OLD/'models/medium',OLD/'models/medium/model_manifest.json')]:
        m=read(manifestp);assert m['license']=='MIT';files=[]
        for row in m['files']:
            p=folder/row['path'];assert sha(p)==row['sha256'];files.append(pin(p))
        licensep=folder/'UPSTREAM_WHISPER_LICENSE.txt';assert sha(licensep)==m['upstream_license_sha256']
        models[name]={'path':str(folder.resolve()),'repository':m['repository'],'revision':m['revision'],'license':'MIT','manifest':pin(manifestp),'files':files,'license_file':pin(licensep),'weight_sha256':next(x['sha256'] for x in m['files'] if x['path']=='model.bin')}
    chapters=[];all_paragraphs=[]
    for ch in prepared['chapters']:
        paras=[]
        for p in ch['paragraphs']:
            n=next(n for n in notes['scenes'] if n['scene_id']==p['scene_id']);assert p['text']==n['display_text'] and p['spoken_text']==n['spoken_text']
            protected=[v for v in ledger['protected_occurrences'] if v['scene_id']==p['scene_id']]
            for v in protected:assert p['text'][v['display_start']:v['display_end']]==v['display']
            comp=compare(p['text'],p['spoken_text']);assert not comp['numeric_differences'] and not comp['coreterm_differences'],(p['scene_id'],comp)
            row={'scene_id':p['scene_id'],'paragraph':p['paragraph'],'chapter':ch['chapter'],'text':p['text'],'spoken_text':p['spoken_text'],'protected_occurrences':protected,'numbers':numbers(p['text'])};paras.append(row);all_paragraphs.append(row)
        chapters.append({'chapter':ch['chapter'],'title':ch['title'],'paragraphs':paras,'text':'\n'.join(p['text'] for p in paras),'spoken_text':'\n'.join(p['spoken_text'] for p in paras)})
    assert len(chapters)==10 and len(all_paragraphs)==45 and sum(len(p['protected_occurrences']) for p in all_paragraphs)==187
    inputs={name:pin(EP/name) for name in ['writer/script_v2.md','writer/protected_numeric_v2.json','writer/pronunciation_notes_v2.json','narration/prepare-v2-r2/prepared.json']}
    expected={'script_sha256':SHA,'currency':'KRW','chapter_count':10,'paragraph_count':45,'protected_occurrence_count':187,'chapters':chapters,'critical_pairs':ledger['critical_pairs'],'newborn_reset_exact':ledger['newborn_reset_case_exact'],'affordability_exact':ledger['affordability_exact'],'case_numbers_exact':ledger['case_numbers_exact'],'policy_math_recalculated':False,'inputs':inputs}
    dump(QA/'expected.json',expected)
    cfg={'episode_id':EP.name,'script_sha256':SHA,'write_root':str(QA),'shared_deps_readonly':str(OLD/'deps'),'models':models,'inputs':inputs,'expected_sha256':sha(QA/'expected.json'),'production_root':str(EP/'narration/production-injoon-v2'),'main_authorization':str(EP/'narration/main_tts_authorization.json'),'locked_script':str(EP/'director/production-v1/locked_script.json'),'inference':{'device':'cpu','compute_type':'int8','cpu_threads':4,'num_workers':1,'language':'ko','beam_size':5,'condition_on_previous_text':False,'initial_prompt':None,'hotwords':None,'vad_filter':False},'medium_scope':'Only numeric/coreterm discrepancy paragraph from an actual small report; preserve0.4s context, no new full episode medium','actual_listening':False,'continuous_playback':False}
    dump(QA/'config.json',cfg)
    os.environ.update(HF_HUB_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1',DO_NOT_TRACK='1',HF_HOME=str(QA/'cache/hf'),XDG_CACHE_HOME=str(QA/'cache'),TOKENIZERS_PARALLELISM='false')
    def denied(*a,**k):raise RuntimeError('Network forbidden in offline QA')
    socket.socket.connect=socket.socket.connect_ex=socket.create_connection=denied
    sys.path.insert(0,str(OLD/'deps'))
    import faster_whisper,ctranslate2,av,numpy,onnxruntime
    onnxruntime.disable_telemetry_events()
    assert faster_whisper.__version__=='1.2.1' and 'int8' in ctranslate2.get_supported_compute_types('cpu')
    proof={'status':'offline_preparation_verified_no_audio_opened','checked_at':datetime.now(timezone.utc).isoformat(),'script_sha256':SHA,'models_verified_readonly':models,'versions':{'python':sys.version,'faster-whisper':faster_whisper.__version__,'ctranslate2':ctranslate2.__version__,'av':av.__version__,'numpy':numpy.__version__,'onnxruntime':onnxruntime.__version__},'all45_display_spoken_numeric_and_acronym_parity':True,'protected_occurrences':187,'model_weights_downloaded_or_copied':False,'model_loaded_for_inference':False,'audio_files_opened':0,'ASR_runs':0,'network_calls':0,'paid_calls':0,'actual_listening':False,'continuous_playback':False,'config':pin(QA/'config.json'),'expected':pin(QA/'expected.json')}
    dump(QA/'preparation_proof.json',proof)
    print(json.dumps({'status':proof['status'],'chapters':10,'paragraphs':45,'protected_occurrences':187,'versions':proof['versions'],'ASR_runs':0},ensure_ascii=False))
if __name__=='__main__':main()
