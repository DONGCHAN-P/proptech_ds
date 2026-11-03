"""Measured EDL and global captions only. No render, TTS, common-state edits or upload."""
import hashlib,json,math,sys
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build import EP,ROOT,OUT,read,sha,dump,load_script_lock,resolve_input

TIMING=EP/'narration/production-injoon-v2/final_timing.json'
EXPECTED='67d7e97351b9a6b9ef4ae71410cfab798d1ab120b792ff924ccc3c11051c16a4'
def stamp(t):
    n=round(t*1000);h,n=divmod(n,3600000);m,n=divmod(n,60000);s,ms=divmod(n,1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'

def main():
    lock,script,_=load_script_lock();timing=read(TIMING);handoff=read(EP/'narration/handoff.json');tech=read(EP/'narration/production-injoon-v2/technical_validation.json')
    assert sha(TIMING)==EXPECTED==handoff['final_timing_sha256']==tech['final_timing_sha256']
    assert timing['script_sha256']==handoff['script_sha256']==lock['script_sha256']
    assert tech['status'].startswith('technical_pass') and not handoff['required_technical_errors']
    assert len(timing['chapters'])==10 and sum(len(c['paragraphs']) for c in timing['chapters'])==45
    assets=read(EP/'director/production-v1/media_assets.json')['assets']
    for a in assets:assert sha(resolve_input(a['path']))==a['sha256']
    first=timing['chapters'][0];p=first['paragraphs'][0]
    hook_end=max(p['last_native_word_end_s'],p['last_pcm_signal_end_s']);cut=math.ceil(hook_end*30)/30
    assert first['paragraphs'][1]['offset_s']>cut
    assert not any(c['start_s']<cut<c['end_s'] for c in first['cues'])
    segments=[];offsets=[];global_s=0.0
    def segment(ident,typ,start,end,chapter=None,asset=None):
        nonlocal global_s
        row={'id':ident,'type':typ,'source_start_s':start,'source_end_s':end,'global_start_s':global_s,'global_end_s':global_s+end-start}
        if chapter:row.update(chapter=chapter,file=f'ch{chapter:02}/chapter_versioned.mp4')
        if asset:row['asset']=asset
        segments.append(row);global_s=row['global_end_s']
    segment('opening_hook','chapter',0,cut,1)
    offsets.append({'chapter':1,'local_start_s':0,'local_end_s':cut,'global_offset_s':0})
    segment('clean_brand_intro','brand',0,5,asset=assets[0])
    segment('chapter_1_after_hook','chapter',cut,first['total_seconds'],1)
    offsets.append({'chapter':1,'local_start_s':cut,'local_end_s':first['total_seconds'],'global_offset_s':5.0})
    for c in timing['chapters'][1:]:
        offsets.append({'chapter':c['chapter'],'local_start_s':0,'local_end_s':c['total_seconds'],'global_offset_s':global_s})
        segment(f'chapter_{c["chapter"]}','chapter',0,c['total_seconds'],c['chapter'])
    body_end=global_s;last=timing['chapters'][-1]
    last_voice=offsets[-1]['global_offset_s']+last['last_speech_end_s']
    assert body_end-last_voice>=3
    segment('clean_brand_outro','brand',0,10,asset=assets[1])
    cues=[];srt=[];rounding=0
    for c in timing['chapters']:
        audio=resolve_input(c['audio_file']);assert audio.resolve().is_relative_to((EP/'narration').resolve()) and sha(audio)==c['audio_sha256']
        assert abs(c['total_seconds']*30-round(c['total_seconds']*30))<1e-6
        for cue in c['cues']:
            offset=next(o['global_offset_s'] for o in offsets if o['chapter']==c['chapter'] and o['local_start_s']<=cue['start_s']<o['local_end_s'])
            start,end=cue['start_s']+offset,cue['end_s']+offset
            assert not cues or start>=cues[-1]['global_end_s']
            assert not (start<cut+5 and end>cut)
            rounding=max(rounding,abs(round(start*1000)/1000-start),abs(round(end*1000)/1000-end))
            cues.append({**cue,'chapter':c['chapter'],'global_start_s':start,'global_end_s':end,'global_offset_s':offset})
            srt.append(f'{len(cues)}\n{stamp(start)} --> {stamp(end)}\n{cue["text"]}\n')
    assert len(cues)==150
    (OUT/'captions_measured.srt').write_text('\n'.join(srt),encoding='utf8')
    dump(OUT/'global_captions.json',{'script_sha256':lock['script_sha256'],'timing_sha256':EXPECTED,'cue_count':len(cues),'cues':cues})
    edl={'status':'measured_audio_units','script_sha256':lock['script_sha256'],'timing_sha256':EXPECTED,'fps':30,'hook_cut_s':cut,'hook_cut_basis':'ceil(max(first paragraph native word end, actual PCM signal end) * 30) / 30','hook_native_end_s':p['last_native_word_end_s'],'hook_PCM_signal_end_s':p['last_pcm_signal_end_s'],'intro_video_frames':150,'outro_video_frames':300,'segments':segments,'offset_map':offsets,'body_seconds':sum(c['total_seconds'] for c in timing['chapters']),'total_seconds':global_s,'captions':'captions_measured.srt','execute':False,'caption_hidden_intervals':[{'start_s':cut,'end_s':cut+5,'reason':'clean_brand_intro'},{'start_s':last_voice,'end_s':body_end,'reason':'final_silent_CTA_hold'},{'start_s':body_end,'end_s':global_s,'reason':'clean_brand_outro'}],'voice_and_picture_use_identical_splits':True,'last_voice_global_end_s':last_voice,'outro_gap_after_voice_s':body_end-last_voice,'note':'Measured source assembly plan only; native cue ends unchanged; full render not authorized.'}
    dump(OUT/'assembly_edl.json',edl)
    chapter_rows=[]
    proposal=read(resolve_input(lock['source_proposals']))['scenes']
    for c in timing['chapters']:
        chapter_rows.append({'chapter':c['chapter'],'title':c['title'],'project':f'ch{c["chapter"]:02}','total_seconds':c['total_seconds'],'audio_file':c['audio_file'],'audio_sha256':c['audio_sha256'],'leading_silence_s':c['leading_silence_s'],'last_speech_end_s':c['last_speech_end_s'],'global_start_s':0 if c['chapter']==1 else next(o['global_offset_s'] for o in offsets if o['chapter']==c['chapter']),'scene_ids':[s['scene_id'] for s in proposal if s['chapter']==c['chapter']]})
    dump(OUT/'render_plan.json',{'status':'measured_audio_units_source_integration_in_progress','script_sha256':lock['script_sha256'],'script_content_approved':True,'caption_timing_sha256':EXPECTED,'audio_revision':timing['audio_revision'],'body_seconds':edl['body_seconds'],'film_seconds':edl['total_seconds'],'fps':30,'width':1920,'height':1080,'body_scene_count':45,'cue_count':150,'chapters':chapter_rows,'brand_assembly':{'hook_cut_s':cut,'intro':assets[0],'outro':assets[1],'existing_music':assets[2]},'EDL_sha256':sha(OUT/'assembly_edl.json'),'SRT_sha256':sha(OUT/'captions_measured.srt'),'full_rendered':False,'full_render_allowed_now':False,'pending':['45-scene measured source integration','canonical carve','independent source/audio QA','main full-render authorization']})
    receipt={'status':'measured_EDL_global_captions_ready_source_integration_pending','timing_sha256':EXPECTED,'EDL':'outputs/private-production-v1/assembly_edl.json','EDL_sha256':sha(OUT/'assembly_edl.json'),'SRT':'outputs/private-production-v1/captions_measured.srt','SRT_sha256':sha(OUT/'captions_measured.srt'),'global_captions':'outputs/private-production-v1/global_captions.json','body_seconds':edl['body_seconds'],'film_seconds':edl['total_seconds'],'cue_count':150,'hook_cut_s':cut,'outro_gap_after_voice_s':body_end-last_voice,'maximum_SRT_rounding_error_s':rounding,'actual_listening':False,'full_render_executed':False,'independent_audio_QA':'pending','native_cue_times_modified':False}
    dump(EP/'editor/measured_EDL_handoff.json',receipt);print(json.dumps(receipt))
if __name__=='__main__':main()
