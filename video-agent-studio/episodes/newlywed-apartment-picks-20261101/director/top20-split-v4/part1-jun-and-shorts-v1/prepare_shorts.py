"""Reuse Jun utterances, with actual neighbouring-speech guards and native captions."""
from pathlib import Path
from collections import defaultdict
import copy,hashlib,json,math,subprocess,sys,wave
import numpy as np
D=Path(__file__).resolve().parent;E=D.parents[2];R=E.parents[2];N=E/'narration/top20-split-v4/jun-and-shorts-v1';W=E/'writer/top20-split-v4/jun-and-shorts-v1'
FF=R/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
sys.path.insert(0,str(E/'editor/top20-explain-v3'))
from caption_tools import make_cues
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def pcm(p):
    z=subprocess.run([str(FF),'-v','error','-i',str(p),'-vn','-ar','48000','-ac','2','-f','s16le','-'],capture_output=True,check=True)
    return np.frombuffer(z.stdout,dtype='<i2').reshape(-1,2)
def wav(p,a):
    with wave.open(str(p),'wb')as w:w.setparams((2,2,48000,0,'NONE','none'));w.writeframes(np.asarray(a,dtype='<i2').tobytes())
def ts(v):
    z=round(v*1000);h,z=divmod(z,3600000);m,z=divmod(z,60000);s,z=divmod(z,1000);return f'{h:02d}:{m:02d}:{s:02d},{z:03d}'
def main():
    proposal=read(N/'timing_proposals.json');byid={s['sentence_id']:s for s in proposal['sentences']};chunks={x['asset_id']:x for x in read(N/'scene_chunk_durations.json')['chunks']}
    grouped=defaultdict(list)
    for s in proposal['sentences']:grouped[s['asset_id']].append(s)
    for ss in grouped.values():ss.sort(key=lambda x:x['chunk_local_start_s'])
    arrays={aid:pcm(R/c['wav_path'])for aid,c in chunks.items()};facts=read(D/'shorts_visual_facts.json');byregion={x['region_id']:x for x in facts}
    music=next(a for a in read(R/'video-agent-studio/episodes/affordable-home-price-20261026/director/production-v1/media_assets.json')['assets']if a['asset_id']=='existing_channel_bgm')
    reports=[]
    for filename in ['short01_promo.json','short02_ranks20_16.json','short03_ranks15_11.json']:
        plan=read(W/filename);short=plan['short_id'];out=D/'shorts'/short;out.mkdir(parents=True,exist_ok=True)
        timeline=[];parts=[np.zeros((round(.28*48000),2),dtype=np.int16)];count=len(parts[0]);last_spoken=0;previous_region=None;clips=[]
        def pad(target):
            nonlocal count
            n=round(target*48000)-count
            if n>0:parts.append(np.zeros((n,2),dtype=np.int16));count+=n
        for i,ref in enumerate(plan['sequence']):
            sid=ref['sentence_id'].removeprefix('P01-')if ref['sentence_id'].startswith('P01-SHORTS-CTA')else ref['sentence_id']
            s=copy.deepcopy(byid[sid]);assert ref['exacttext']==s['text'];aid=s['asset_id'];same=grouped[aid];idx=next(k for k,x in enumerate(same)if x['sentence_id']==sid)
            previous=same[idx-1]if idx else None;following=same[idx+1]if idx+1<len(same)else None
            first=s['chunk_local_start_s'];last=s['chunk_local_end_s'];start=max(0,first-.08)
            if previous:start=max(start,previous['chunk_local_end_s']+.10)
            end=min(len(arrays[aid])/48000,last+.30)
            if following:end=min(end,following['chunk_local_start_s']-.12)
            assert start<=first and end>=last+.03,(sid,start,end,first,last)
            region=ref.get('regionid');is_cta=sid.startswith('SHORTS-CTA');changed=region!=previous_region or is_cta
            gap=.58 if changed else .40
            if i:pad(last_spoken+gap-(first-start))
            clip_start=count/48000;lo=round(start*48000);hi=round(end*48000);piece=arrays[aid][lo:hi].copy();parts.append(piece);count+=len(piece)
            offset=clip_start-lo/48000;s['start_s']=offset+first;s['end_s']=offset+last
            for w in s['words']:
                w['start_s']=offset+w['chunk_local_start_s'];w['end_s']=offset+w['chunk_local_end_s'];w['local_start_s']=w['start_s'];w['local_end_s']=w['end_s']
            s.update(region_id=region,screenmessage=ref['screenmessage'],visualpurpose=ref['visualpurpose'],segment_start_s=clip_start,segment_end_s=count/48000,
                     source_clip={'asset_id':aid,'audio_path':chunks[aid]['wav_path'],'audio_sha256':chunks[aid]['wav_sha256'],'start_s':lo/48000,'end_s':hi/48000,
                                  'first_native_s':first,'last_native_s':last,'previous_speech_end_s':previous['chunk_local_end_s']if previous else None,'next_speech_start_s':following['chunk_local_start_s']if following else None})
            timeline.append(s);clips.append({'sentence_id':sid,'target_start_s':clip_start,'duration_s':len(piece)/48000,'source_pcm_sha256':hashlib.sha256(piece.tobytes()).hexdigest(),**s['source_clip']});last_spoken=s['end_s'];previous_region=region
        pad(last_spoken+1.05);total_frames=math.ceil(count/1600);pad(total_frames/30);voice=np.vstack(parts);assert len(voice)==total_frames*1600
        wav(out/'voice.wav',voice);duration=len(voice)/48000;assert duration<180
        bed=out/'music.wav';subprocess.run([str(FF),'-v','error','-y','-stream_loop','-1','-i',str(R/music['path']),'-t',str(duration),'-af',f'volume=0.035,afade=t=in:st=0:d=0.18,afade=t=out:st={duration-.45}:d=0.45','-ar','48000','-ac','2','-c:a','pcm_s16le',str(bed)],check=True)
        mixed=voice.astype(np.int32)+pcm(bed)[:len(voice)].astype(np.int32);assert np.abs(mixed).max()<32767;wav(out/'master_audio.wav',mixed)
        cues=[]
        for s in timeline:
            rows=make_cues(s,s['words'],s['reading_text'],maxchars=22);assert ' '.join(x['text']for x in rows)==s['text'];cues+=rows
        assert all(c['end_s']<=cues[i+1]['start_s']+.0001 for i,c in enumerate(cues[:-1]))
        scenes=[]
        for i,s in enumerate(timeline):
            region=s['region_id'];kind='cta'if s['sentence_id'].startswith('SHORTS-CTA')else 'region'if region else 'hook'
            key=region if region else 'cta'if kind=='cta'else s['sentence_id']
            if scenes and scenes[-1]['key']==key:scenes[-1]['sentences'].append(s)
            else:scenes.append({'scene_id':f"{short}-{len(scenes):02d}",'key':key,'kind':kind,'region_id':region,'start_s':s['segment_start_s']if i else 0,'sentences':[s]})
        for i,scene in enumerate(scenes):
            scene['end_s']=scenes[i+1]['start_s']if i+1<len(scenes)else duration
            if scene['region_id']:scene['visual_facts']=byregion[scene['region_id']]
        lock={'status':'actual_Jun_reuse_locked','revision':'jun-and-shorts-v1','short_id':short,'title':plan['title'],'rankrange':plan.get('rankrange'),
              'scenes':scenes,'sentences':timeline,'captions':cues,'source_clips':clips,'total_s':duration,'total_frames':total_frames,'fps':30,
              'master_audio':str(out/'master_audio.wav'),'master_audio_sha256':sha(out/'master_audio.wav'),'voice_audio':str(out/'voice.wav'),
              'source_plan':str(W/filename),'source_plan_sha256':sha(W/filename),'source_voice_manifest_sha256':sha(N/'narration_manifest.json'),
              'source_visual_facts':str(D/'shorts_visual_facts.json'),'source_visual_facts_sha256':sha(D/'shorts_visual_facts.json'),
              'shared_CTA_generated_once':True,'voice_regeneration_calls':0,'additional_credits':0,
              'vertical_profile':'youtube_portrait_full_frame_v2','voice_tail_included_in_end_hold_s':1.05,
              'actual_listening':False,'continuous_playback':False,'music_credit':music.get('license')}
        save(out/'locked_timing.json',lock);(out/'captions.srt').write_text('\n\n'.join(f"{i+1}\n{ts(c['start_s'])} --> {ts(c['end_s'])}\n{c['text']}"for i,c in enumerate(cues))+'\n',encoding='utf-8')
        reports.append({'short_id':short,'duration_s':duration,'sentences':len(timeline),'captions':len(cues),'regions':[s['region_id']for s in scenes if s['region_id']],
                        'locked_timing':str(out/'locked_timing.json'),'master_audio_sha256':lock['master_audio_sha256'],'peak_pcm':int(np.abs(mixed).max()),'all_complete_utterances_guarded':True})
    save(D/'shorts_media_receipt.json',{'status':'passed','shorts':reports,'new_paid_generation_calls':0,'shared_CTA_generated_once':True,'actual_listening':False})
    print(json.dumps(reports,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
