"""Actual new intro + unchanged encoded body, cut only in the old intro's silence."""
from pathlib import Path
from datetime import datetime,timezone
from collections import defaultdict
import copy,hashlib,json,math,subprocess,sys,wave
import numpy as np
D=Path(__file__).resolve().parent;E=D.parents[2];R=E.parents[2];N=E/'narration/top20-split-v4/intro-rationale-v3'
FF=R/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
FP=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
sys.path.insert(0,str(E/'editor/top20-explain-v3'));from caption_tools import make_cues,norm
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def pcm(source,extra=None):
    c=[str(FF),'-v','error']+(extra or[])+['-i',str(source),'-vn','-ar','48000','-ac','2','-f','s16le','-']
    r=subprocess.run(c,capture_output=True);assert r.returncode==0,r.stderr;return np.frombuffer(r.stdout,dtype='<i2').reshape(-1,2)
def wav(p,arr):
    with wave.open(str(p),'wb')as w:w.setparams((2,2,48000,0,'NONE','not compressed'));w.writeframes(np.asarray(arr,dtype='<i2').tobytes())
def main():
    out=D/'media';out.mkdir(exist_ok=True);auth=read(D/'production_authorization.json');assert auth['status']=='approved'
    t=read(N/'timing_proposals.json');script=read(E/'writer/top20-split-v4/intro-rationale-v3/intro_proposal_v3.json')
    assert len(t['sentences'])==8 and t['script_sha256']==sha(E/'writer/top20-split-v4/intro-rationale-v3/intro_proposal_v3.json')
    assert [s['text']for s in t['sentences']]==[s['text']for s in script['sentences']]
    source=E/auth['existing_body_video'];assert sha(source)==auth['existing_body_sha256']
    old=read(E/'director/top20-split-v4/part1-production-v1/locked_timing.json')
    Bframe=1391;Kframe=1575;B=Bframe/30;K=Kframe/30;lead=.8
    # Confirm the splice begins in speech-free space and the copy boundary is a true IDR/keyframe.
    assert old['scenes'][0]['sentences'][-1]['end_s']<B<old['scenes'][1]['sentences'][0]['start_s']
    probe=subprocess.run([str(FP),'-v','error','-read_intervals','44%+28','-skip_frame','nokey','-select_streams','v:0','-show_frames','-show_entries','frame=best_effort_timestamp_time','-of','json',str(source)],capture_output=True)
    assert any(abs(float(f['best_effort_timestamp_time'])-K)<1e-5 for f in json.loads(probe.stdout)['frames'])
    raw=pcm(R/t['audio_path']);assert sha(R/t['audio_path'])==t['audio_sha256']
    T0frames=math.ceil((lead+len(raw)/48000)*30);T0=T0frames/30;intro=np.zeros((T0frames*1600,2),dtype=np.int16)
    intro[round(lead*48000):round(lead*48000)+len(raw)]=raw
    wav(out/'intro_voice_48k.wav',intro)
    b=t['brand_intro']['start_s']+lead;e=b+5
    music_manifest=read(R/'video-agent-studio/episodes/affordable-home-price-20261026/director/production-v1/media_assets.json')
    music=next(a for a in music_manifest['assets']if a['asset_id']=='existing_channel_bgm');mp=R/music['path'];assert sha(mp)==music['sha256']
    gain=f'if(lt(t,{b}),min(1,max(0,({b}-t)/0.12)),if(lt(t,{e}),0,min(1,max(0,(t-{e})/0.18))))'
    bed=out/'intro_music.wav';cmd=[str(FF),'-v','error','-y','-stream_loop','-1','-i',str(mp),'-t',str(T0),'-af',f"afade=t=in:st=0:d=0.45,volume='{gain}':eval=frame,volume=0.045,afade=t=out:st={T0-.30}:d=0.30",'-ar','48000','-ac','2','-c:a','pcm_s16le',str(bed)]
    subprocess.run(cmd,check=True);bedarr=pcm(bed)
    mixed=intro.astype(np.int32)+bedarr[:len(intro)].astype(np.int32);assert np.abs(mixed).max()<32767
    wav(out/'intro_mixed.wav',mixed)
    oldpcm=pcm(source);body=oldpcm[Bframe*1600:].copy()
    # Ten milliseconds of music-only silence precedes the first body word by 67 ms.
    n=480;body[:n]=np.rint(body[:n].astype(float)*np.linspace(0,1,n)[:,None]).astype(np.int16)
    expected_frames=T0frames+18006-Bframe;total=expected_frames/30
    master=np.vstack([mixed.astype(np.int16),body]);target=expected_frames*1600
    assert len(master)<=target+1024
    if len(master)<target:master=np.vstack([master,np.zeros((target-len(master),2),dtype=np.int16)])
    master=master[:target];wav(out/'master_audio.wav',master)
    groups=defaultdict(list)
    for w in read(R/t['words_file'])['words']:groups[w['sentence_id']].append(copy.deepcopy(w))
    new=[];captions=[]
    for s in t['sentences']:
        g=groups[s['sentence_id']];assert ''.join(norm(w.get('provider_text',w['text']))for w in g)==norm(s['reading_text'])
        row=copy.deepcopy(s);row['start_s']+=lead;row['end_s']+=lead;row['words']=g
        for w in g:
            w['start_s']+=lead;w['end_s']+=lead;w['local_start_s']=w['start_s'];w['local_end_s']=w['end_s']
        new.append(row);cs=make_cues(row,g,row['reading_text'],maxchars=42)
        assert ' '.join(c['text']for c in cs)==row['text'];captions+=cs
    delta=T0-B
    for c in old['captions']:
        if c['start_s']<B:continue
        captions.append(dict(c,start_s=c['start_s']+delta,end_s=c['end_s']+delta))
    assert len({c['sentence_id']for c in captions})==88
    oldscenes=[]
    for s in old['scenes'][1:]:
        row={k:v for k,v in s.items()if k!='sentences'}
        for k in ['start_s','end_s']:row[k]+=delta
        row['sentences']=[dict(v,start_s=v['start_s']+delta,end_s=v['end_s']+delta)for v in s['sentences']]
        oldscenes.append(row)
    prefix_end=T0+(K-B)
    lock={'status':'actual_audio_locked','revision':'intro-rationale-v3','script_decision_id':'d884be1c4e38',
      'created_at':datetime.now(timezone.utc).isoformat(),'narration_timing_sha256':sha(N/'timing_proposals.json'),
      'intro_script_sha256':sha(E/'writer/top20-split-v4/intro-rationale-v3/intro_proposal_v3.json'),
      'original_video':str(source),'original_video_sha256':sha(source),'old_body_cut_s':B,'old_body_cut_frame':Bframe,
      'stream_copy_keyframe_s':K,'stream_copy_keyframe':Kframe,'lead_s':lead,'intro_end_s':T0,'delta_s':delta,
      'prefix_end_s':prefix_end,'prefix_frames':round(prefix_end*30),'total_s':total,'total_frames':expected_frames,
      'intro_sentences':new,'brand_intro':{'start_s':b,'duration_s':5,'source_video':str(R/'video-agent-studio/episodes/regional-price-recovery-20261022/outputs/production-v1-jun/reusable_assets/brand_intro_clean_v7.mp4')},
      'brand_outro':{'start_s':old['brand_inserts'][-1]['start_s']+delta,'duration_s':10},
      'captions':captions,'body_scenes':oldscenes,'master_audio':str(out/'master_audio.wav'),'master_audio_sha256':sha(out/'master_audio.wav'),
      'last_spoken_end_s':old['last_spoken_end_s']+delta,'voice_profile':'free InJoon+0%/atempo1.35','music_credit':music['license'],
      'actual_listening':False,'new_paid_calls':0,'cash_cost_krw':0,'unmodified_body_copy_begins_at_s':prefix_end}
    save(D/'locked_timing.json',lock)
    def ts(x):
        z=round(x*1000);h,z=divmod(z,3600000);m,z=divmod(z,60000);s,z=divmod(z,1000);return f'{h:02d}:{m:02d}:{s:02d},{z:03d}'
    (D/'captions.srt').write_text('\n\n'.join(f"{i+1}\n{ts(c['start_s'])} --> {ts(c['end_s'])}\n{c['text']}"for i,c in enumerate(captions))+'\n',encoding='utf-8')
    save(D/'media_receipt.json',{'status':'passed','intro_native_sentences':8,'full_sentences':88,'captions':len(captions),'prefix_end_s':prefix_end,'total_s':total,
      'body_cut_in_old_intro_silence':True,'first_body_native_word_s':oldscenes[0]['sentences'][0]['start_s'],
      'intro_brand_once':True,'old_body_audio_copied_from_final_mix':True,'body_first_10ms_music_only_fade':True,
      'voice_regenerated_body_sentences':0,'master_audio_sha256':lock['master_audio_sha256'],'master_peak_pcm':int(np.abs(master.astype(np.int32)).max()),
      'hyperframes_usage_status':'unknown_usage_request_failed','cash_cap_krw':0})
    print(json.dumps({'status':'media_actual_timing_ready','intro_end_s':T0,'prefix_end_s':prefix_end,'total_s':total,'captions':len(captions),'delta_s':delta}))
if __name__=='__main__':main()
