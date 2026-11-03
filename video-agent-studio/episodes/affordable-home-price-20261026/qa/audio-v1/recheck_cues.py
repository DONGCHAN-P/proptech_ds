"""One bounded diagnostic pass for remaining coreterm/numeric ambiguities.

Native cue context only, fixed offline medium, no prompts or hotwords. These
are additional contexts of the same model, not another independent model.
"""
import hashlib,sys
from pathlib import Path
sys.dont_write_bytecode=True
QA=Path(__file__).resolve().parent
sys.path.insert(0,str(QA))
import run_asr as r
from prepare import read,dump,pin,sha
from checks import compare

TARGETS={4:['C04_S014Q003'],5:['C05_S019Q003'],6:['C06_S024Q004'],7:['C07_S030Q004','C07_S031Q002','C07_S031Q003'],8:['C08_S032Q001','C08_S036Q003']}

if __name__=='__main__':
    cfg=read(QA/'config.json');r.gate(cfg);model,fw,np,versions=r.runtime(cfg,'medium')
    for n,ids in TARGETS.items():
        jp=Path(cfg['production_root'])/f'chapter_{n:02}.json';ch=read(jp);wp=r.resolve(ch['audio_file']);assert sha(wp)==ch['audio_sha256']
        audio=fw.audio.decode_audio(str(wp),sampling_rate=16000)
        for cid in ids:
            cue=next(c for c in ch['cues'] if c['id']==cid)
            existing=list((QA/'runs').glob(f'ch{n:02}-medium-*/*/comparison.json'))
            prior=next(p for p in existing if read(p)['scene_id']==cue['scene_id'])
            assert read(prior)['unresolved_requires_manual_evidence_review']
            lo=max(0,cue['native_start_s']-.4);hi=min(len(audio)/16000,cue['native_end_s']+.4)
            clip=audio[round(lo*16000):round(hi*16000)]
            assert len(clip)>1600 and np.max(np.abs(clip))>.01
            rows,info=r.transcribe(model,clip)
            text=''.join(s['text'] for s in rows).strip();comp=compare(cue['spoken_text'],text)
            dest=QA/'cue_rechecks'/cid;dest.mkdir(parents=True,exist_ok=True)
            dump(dest/'review.json',{'cue_id':cid,'chapter':n,'scene_id':cue['scene_id'],'source_audio':pin(wp),'chapter_json':pin(jp),'prior_paragraph_comparison':pin(prior),'native_cue':cue,'clip_start_s':lo,'clip_end_s':hi,'context_each_side_s':.4,'decoded_clip_samples':len(clip),'decoded_float32_clip_sha256':hashlib.sha256(clip.tobytes()).hexdigest(),'medium_transcript':text,'comparison':comp,'segments':rows,'info':info,'model':cfg['models']['medium'],'versions':versions,'reference_as_prompt':False,'hotwords':None,'actual_listening':False,'is_additional_context_of_same_medium_model':True})
            assert sha(wp)==ch['audio_sha256']
            print({'cue':cid,'transcript':text,'numeric_diffs':comp['numeric_differences'],'term_diffs':comp['coreterm_differences']},flush=True)
