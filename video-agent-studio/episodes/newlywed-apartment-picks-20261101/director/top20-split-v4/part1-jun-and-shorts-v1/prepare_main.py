"""Director-owned Jun master, native captions and source-picture conformance anchors."""
from pathlib import Path
from collections import defaultdict
import copy,hashlib,json,math,re,subprocess,sys,wave
import numpy as np
D=Path(__file__).resolve().parent;E=D.parents[2];R=E.parents[2];N=E/'narration/top20-split-v4/jun-and-shorts-v1'
FF=R/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
sys.path.insert(0,str(E/'editor/top20-explain-v3'))
from caption_tools import make_cues,translated_index
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
norm=lambda s:''.join(c for c in s if c.isalnum())
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def pcm(p):
    r=subprocess.run([str(FF),'-v','error','-i',str(p),'-vn','-ar','48000','-ac','2','-f','s16le','-'],capture_output=True,check=True)
    return np.frombuffer(r.stdout,dtype='<i2').reshape(-1,2)
def wav(p,a):
    with wave.open(str(p),'wb')as w:w.setparams((2,2,48000,0,'NONE','none'));w.writeframes(np.asarray(a,dtype='<i2').tobytes())
def main():
    auth=read(D/'production_authorization.json');m=read(N/'narration_manifest.json');ledger=read(N/'generation_ledger.json');proposals=read(N/'timing_proposals.json')
    assert sha(N/'narration_manifest.json')==auth['manifest_sha256']
    assert ledger['actual_credits']<=6500 and ledger['observed_account_delta']==ledger['actual_credits']==2208
    assert proposals['sentence_count']==92 and proposals['word_count']>1000
    chunks=read(N/'scene_chunk_durations.json')['chunks'];mainchunks=[x for x in chunks if x['asset_id']!='SHORTS-CTA'];assert len(mainchunks)==15
    ns=proposals['sentences'];bychunk=defaultdict(list)
    for s in ns:bychunk[s['asset_id']].append(s)
    media=D/'media';media.mkdir(exist_ok=True);parts=[];count=0;origins={};scene_rows=[]
    def append(x):
        nonlocal count
        parts.append(x);count+=len(x)
    def pad_to(t):
        wanted=round(t*48000)
        if wanted>count:append(np.zeros((wanted-count,2),dtype=np.int16))
    pad_to(.8);last_spoken=0
    intro_wave=E/'director/top20-production-v1/locked-audio/intro_clean_v7.wav'
    outro_wave=E/'director/top20-production-v1/locked-audio/outro_clean_v7.wav'
    brand_intro=None
    for i,c in enumerate(mainchunks):
        asset=c['asset_id'];file=R/c['wav_path'];assert sha(file)==c['wav_sha256'];ss=bychunk[asset]
        first=min(x['chunk_local_start_s']for x in ss);last=max(x['chunk_local_end_s']for x in ss)
        if i==1:pad_to(brand_intro['start_s']+5+.08-first)
        elif i>1:pad_to(last_spoken+.70-first)
        origin=count/48000;origins[asset]=origin;x=pcm(file);append(x);last_spoken=origin+last
        scene_rows.append({'scene_id':asset,'asset_id':asset,'start_s':origin,'end_s':count/48000,'audio_path':str(file),'audio_sha256':sha(file),'sentence_ids':c['sentence_ids']})
        if i==0:
            pad_to(max(count/48000,last_spoken+.55));start=count/48000;append(pcm(intro_wave));assert abs(count/48000-start-5)<1e-8
            brand_intro={'start_s':start,'duration_s':5,'end_s':start+5,'source_audio':str(intro_wave),'source_sha256':sha(intro_wave)}
    brandout_start=last_spoken+3;assert count/48000<=brandout_start
    pad_to(brandout_start);append(pcm(outro_wave));assert abs(count/48000-brandout_start-10)<1e-6
    total_frames=math.ceil(count/1600);pad_to(total_frames/30);voice=np.vstack(parts);assert len(voice)==total_frames*1600
    wav(media/'narration_with_brand.wav',voice)
    bm=read(R/'video-agent-studio/episodes/affordable-home-price-20261026/director/production-v1/media_assets.json');music=next(x for x in bm['assets']if x['asset_id']=='existing_channel_bgm');assert sha(R/music['path'])==music['sha256']
    b,e=brand_intro['start_s'],brand_intro['end_s'];outro=brandout_start;dur=total_frames/30
    expression=f'if(lt(t,{b}),min(1,max(0,({b}-t)/0.12)),if(lt(t,{e}),0,if(lt(t,{outro}),min(1,max(0,(t-{e})/0.15)),0)))'
    bed=media/'music_bed.wav';subprocess.run([str(FF),'-v','error','-y','-stream_loop','-1','-i',str(R/music['path']),'-t',str(dur),'-af',f"afade=t=in:st=0:d=0.45,volume='{expression}':eval=frame,volume=0.045,afade=t=out:st={outro-.20}:d=0.20",'-ar','48000','-ac','2','-c:a','pcm_s16le',str(bed)],check=True)
    mixed=voice.astype(np.int32)+pcm(bed)[:len(voice)].astype(np.int32);assert np.abs(mixed).max()<32767
    wav(media/'master_audio.wav',mixed)
    main_sentences=[];captions=[];original={x['sentence_id']:x for x in m['sentences']}
    for s0 in ns:
        if s0['asset_id']=='SHORTS-CTA':continue
        s=copy.deepcopy(s0);offset=origins[s['asset_id']];s['start_s']=offset+s['chunk_local_start_s'];s['end_s']=offset+s['chunk_local_end_s']
        for w in s['words']:
            w['start_s']=offset+w['chunk_local_start_s'];w['end_s']=offset+w['chunk_local_end_s'];w['local_start_s']=w['start_s'];w['local_end_s']=w['end_s'];w['global_start_s']=w['start_s'];w['global_end_s']=w['end_s']
        assert s['text']==original[s['sentence_id']]['text']
        main_sentences.append(s);cs=make_cues(s,s['words'],s['reading_text'],maxchars=42);assert ' '.join(c['text']for c in cs)==s['text'];captions+=cs
    main_sentences.sort(key=lambda x:x['start_s']);assert len(main_sentences)==90
    byid={s['sentence_id']:s for s in main_sentences}
    for scene in scene_rows:scene['sentences']=[byid[sid]for sid in scene['sentence_ids']]
    old=read(E/'director/top20-split-v4/part1-map-clean-v1/locked_timing.json');intro=read(E/'director/top20-split-v4/part1-intro-v3/locked_timing.json')['intro_sentences']
    old_intro=copy.deepcopy(intro)
    for s in old_intro:
        if s['start_s']>=old['insert_at_s']:s['start_s']+=old['insert_duration_s'];s['end_s']+=old['insert_duration_s']
    old_rows=old_intro[:6]+copy.deepcopy(old['criteria_sentences'])+old_intro[6:]+[copy.deepcopy(s)for c in old['body_scenes']for s in c['sentences']]
    for s in old_rows:
        ws=s.get('words',[])
        if ws:
            shift=s['start_s']-min(w['start_s']for w in ws)
            for w in ws:w['start_s']+=shift;w['end_s']+=shift;w['local_start_s']=w['start_s'];w['local_end_s']=w['end_s']
    assert [x['sentence_id']for x in old_rows]==[x['sentence_id']for x in main_sentences]
    align={c['asset_id']:read(R/c['normalized_alignment']['path'])for c in mainchunks}
    candidates=[]
    def anchor(source,target,kind,priority=50,sid=None):candidates.append({'source_s':float(source),'target_s':float(target),'kind':kind,'priority':priority,'sentence_id':sid})
    anchor(0,0,'start',1000);anchor(old['total_s'],dur,'end',1000)
    def new_char_time(s,index):
        raw=[i for i,c in enumerate(s['reading_text'])if c.isalnum()];i=raw[max(0,min(index,len(raw)-1))]+s['chunk_char_start']
        return origins[s['asset_id']]+align[s['asset_id']]['character_start_times_seconds'][i]
    for o in old_rows:
        s=byid[o['sentence_id']];sid=s['sentence_id'];assert norm(o['reading_text'])==norm(s['reading_text'])
        anchor(o['start_s'],s['start_s'],'sentence_start',100,sid);anchor(o['end_s'],s['end_s'],'sentence_end',100,sid)
        cursor=0
        for w in o.get('words',[]):
            token=norm(w.get('provider_text',w.get('reading_text',w['text'])));display=w.get('display_text','')
            if re.search(r'\d',display)or display.endswith(('역','학교','초','중','단지')):
                anchor(w['start_s'],new_char_time(s,cursor),'number_or_place',50,sid)
            cursor+=len(token)
        assert cursor==len(norm(o['reading_text'])),sid
    source_intro=old['brand_intro'];source_outro=old['brand_outro'];brand_outro={'start_s':brandout_start,'duration_s':10,'end_s':brandout_start+10,'source_audio':str(outro_wave),'source_sha256':sha(outro_wave)}
    for source,target,kind in [(source_intro['start_s'],brand_intro['start_s'],'brand_intro_start'),(source_intro['start_s']+5,brand_intro['end_s'],'brand_intro_end'),(source_outro['start_s'],brandout_start,'brand_outro_start'),(source_outro['start_s']+10,brandout_start+10,'brand_outro_end')]:anchor(source,target,kind,1000)
    photos=[]
    for u in old['transition_plan']['photos']:
        source_start=u['final_start_s'];source_end=u['final_end_s'];first=next(s for s in old_rows if s['sentence_id'].startswith(f"P01-R{u['rank']}")and s['sentence_id'].endswith('-01'));newfirst=byid[first['sentence_id']]
        target_start=(byid['P01-INTRO-V3-08']['start_s']-.16)if u['rank']==20 else newfirst['start_s']-.45
        target_end=newfirst['end_s']+.25
        for x,y,kind in [(source_start,target_start,'photo_start'),(source_start+.52,target_start+.52,'photo_enter_end'),(source_end-.55,target_end-.55,'photo_exit_start'),(source_end,target_end,'photo_end')]:anchor(x,y,kind,500,first['sentence_id'])
        photos.append({'rank':u['rank'],'source_start_s':source_start,'source_end_s':source_end,'start_s':target_start,'end_s':target_end})
    unique={}
    for a in candidates:
        k=round(a['source_s'],6)
        if k not in unique or a['priority']>unique[k]['priority']:unique[k]=a
    points=sorted(unique.values(),key=lambda x:x['source_s']);dropped=[]
    while True:
        bad=next((i for i in range(1,len(points))if points[i]['target_s']<=points[i-1]['target_s']+.00001),None)
        if bad is None:break
        k=bad if points[bad]['priority']<=points[bad-1]['priority'] else bad-1
        dropped.append(points.pop(k))
    assert points[0]['source_s']==0 and points[-1]['target_s']==dur
    ratios=[(q['source_s']-p['source_s'])/(q['target_s']-p['target_s'])for p,q in zip(points,points[1:])]
    lock={'status':'actual_Jun_audio_locked','revision':'jun-and-shorts-v1','source_video':m['source_video'],'source_video_sha256':m['source_video_sha256'],
          'source_total_s':old['total_s'],'source_old_sentences':old_rows,'source_brand_intro':source_intro,'source_brand_outro':source_outro,
          'source_to_target_anchors':points,'dropped_conformance_anchors':dropped,'conformance_rate_range':[min(ratios),max(ratios)],
          'main_sentences':main_sentences,'scenes':scene_rows,'captions':captions,'photo_transitions':photos,
          'chunk_origins':origins,'brand_intro':brand_intro,'brand_outro':brand_outro,'last_spoken_end_s':last_spoken,
          'total_s':dur,'total_frames':total_frames,'fps':30,'master_audio':str(media/'master_audio.wav'),'master_audio_sha256':sha(media/'master_audio.wav'),
          'narration_with_brand':str(media/'narration_with_brand.wav'),'native_timing_sha256':sha(N/'timing_proposals.json'),
          'actual_listening':False,'continuous_playback':False,'actual_credits':ledger['actual_credits'],'credit_cap':6500,
          'chunk_gap_policy':'complete source PCM retained; minimum0.70sbetween chunk spoken spans; brandafterhook0.55s/afterbrand0.08s',
          'paid_generation_done':True,'additional_cash_krw':0}
    save(D/'locked_timing.json',lock)
    def ts(x):
        z=round(x*1000);h,z=divmod(z,3600000);m,z=divmod(z,60000);s,z=divmod(z,1000);return f'{h:02d}:{m:02d}:{s:02d},{z:03d}'
    (D/'captions.srt').write_text('\n\n'.join(f"{i+1}\n{ts(c['start_s'])} --> {ts(c['end_s'])}\n{c['text']}"for i,c in enumerate(captions))+'\n',encoding='utf-8')
    report={'status':'locked','total_s':dur,'frames':total_frames,'main_sentences':90,'captions':len(captions),'conformance_points':len(points),'dropped_points':len(dropped),'source_rate_range':[min(ratios),max(ratios)],'master_peak_pcm':int(np.abs(mixed).max()),'actual_credits':ledger['actual_credits'],'raw_chunk_PCMS_uncropped':True,'native_timing_sha256':lock['native_timing_sha256']}
    save(D/'main_media_receipt.json',report);print(json.dumps(report),flush=True)
if __name__=='__main__':main()
