"""Independently validate all31 Jun source cuts and all84 Shorts caption mappings."""
import pathlib,json,hashlib,subprocess,wave,math
from datetime import datetime,timezone
Q=pathlib.Path(__file__).resolve().parent;E=Q.parents[2];R=E.parents[2];D=E/'director/top20-split-v4/part1-jun-and-shorts-v1';N=E/'narration/top20-split-v4/jun-and-shorts-v1'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(s):return ''.join(c for c in s if c.isalnum())
def wav(p):
    with wave.open(str(p),'rb') as w:return dict(rate=w.getframerate(),channels=w.getnchannels(),width=w.getsampwidth(),frames=w.getnframes()),w.readframes(w.getnframes())
FF=R/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe';t=read(N/'timing_proposals.json');sources={s['sentence_id']:s for s in t['sentences']};grouped={}
for s in t['sentences']:grouped.setdefault(s['asset_id'],[]).append(s)
cache={};reports=[];failures=[];total_clips=total_cues=0
for name in ['SHORT01-PROMO','SHORT02-R20-R16','SHORT03-R15-R11']:
    path=D/'shorts'/name/'locked_timing.json';lock=read(path);fmt,voice=wav(pathlib.Path(lock['voice_audio']));rows=[];caption_rows=[]
    assert fmt['rate']==48000 and fmt['channels']==2 and fmt['width']==2 and fmt['frames']==lock['total_frames']*1600
    for i,(clip,target) in enumerate(zip(lock['source_clips'],lock['sentences'])):
        sid=clip['sentence_id'];s=sources[sid];asset=s['asset_id'];same=grouped[asset];j=next(k for k,x in enumerate(same) if x['sentence_id']==sid);previous=same[j-1] if j else None;following=same[j+1] if j+1<len(same) else None
        if asset not in cache:
            p=R/s['wav_path'];r=subprocess.run([str(FF),'-v','error','-xerror','-i',str(p),'-ar','48000','-ac','2','-c:a','pcm_s16le','-f','s16le','-'],capture_output=True);assert r.returncode==0;cache[asset]=r.stdout
        source=cache[asset];duration=len(source)/4/48000;first=s['chunk_local_start_s'];last=s['chunk_local_end_s'];a=max(0,first-.08,previous['chunk_local_end_s']+.10 if previous else 0);b=min(duration,last+.30,following['chunk_local_start_s']-.12 if following else duration)
        lo=round(a*48000);hi=round(b*48000);pcm=source[lo*4:hi*4];dest=round(clip['target_start_s']*48000);actual=voice[dest*4:dest*4+len(pcm)]
        guard=abs(clip['start_s']-lo/48000)<1e-8 and abs(clip['end_s']-hi/48000)<1e-8 and a<=first+1e-8 and b>=last+.03-1e-8 and (not previous or a>=previous['chunk_local_end_s']+.10-1/48000) and (not following or b<=following['chunk_local_start_s']-.12+1/48000)
        exact=pcm==actual and hashlib.sha256(pcm).hexdigest()==clip['source_pcm_sha256'];offset=clip['target_start_s']-lo/48000
        timing=abs(target['start_s']-offset-first)<1e-7 and abs(target['end_s']-offset-last)<1e-7 and target['text']==s['text'] and target['reading_text']==s['reading_text']
        gap=None
        if i:
            gap=target['start_s']-lock['sentences'][i-1]['end_s'];changed=target.get('region_id')!=lock['sentences'][i-1].get('region_id') or sid.startswith('SHORTS-CTA');timing &= gap>=(.58 if changed else .40)-1/48000
        rows.append(dict(sentence_id=sid,source_start_s=lo/48000,source_end_s=hi/48000,first_native_s=first,last_native_s=last,previous_native_end_s=previous['chunk_local_end_s'] if previous else None,next_native_start_s=following['chunk_local_start_s'] if following else None,target_start_s=clip['target_start_s'],target_spoken_start_s=target['start_s'],target_spoken_end_s=target['end_s'],spoken_gap_s=gap,guard_passed=bool(guard),raw_clip_PCM_exact=exact,target_native_time_exact=bool(timing)))
        if not (guard and exact and timing):failures.append(dict(short_id=name,sentence_id=sid,guard=guard,PCM=exact,timing=timing))
        gs=[c for c in lock['captions'] if c['sentence_id']==sid];bounds=[];pos=0
        join=norm(''.join(c['text'] for c in gs))==norm(s['text']);protected_ok=True;word_anchors={round(x[k]+offset,7) for x in s['words'] for k in ['chunk_local_start_s','chunk_local_end_s']}
        time_ok=all(target['start_s']-1e-6<=c['start_s']<c['end_s']<=target['end_s']+1e-6 and all(any(abs(c[k]-x)<1e-6 for x in word_anchors) for k in ['start_s','end_s']) for c in gs)
        for c in gs:
            n=len(norm(c['text']));join &= c['display_normalized_range']==[pos,pos+n];pos+=n;bounds.append(pos)
        for p in s['protected_numeric_spans']:
            aa=len(norm(s['text'][:p['display_char_start']]));bb=len(norm(s['text'][:p['display_char_end']]));protected_ok &= all(not aa<x<bb for x in bounds[:-1])
        caption_rows.append(dict(sentence_id=sid,cues=len(gs),text_rejoins_exact=join,protected_numeric_unit_not_split=protected_ok,native_word_boundary_times=time_ok))
        if not (join and protected_ok and time_ok):failures.append(dict(short_id=name,sentence_id=sid,caption_join=join,numeric_protection=protected_ok,native_boundary=time_ok))
    total_clips+=len(rows);total_cues+=len(lock['captions']);tail=lock['total_s']-lock['sentences'][-1]['end_s'];assert tail>=1.05-1/48000 and tail<1.05+1/30+1/48000
    assert all(x['end_s']<=y['start_s']+1e-6 for x,y in zip(lock['captions'],lock['captions'][1:]))
    reports.append(dict(short_id=name,lock_sha256=sha(path),duration_s=lock['total_s'],sentences=len(rows),cues=len(lock['captions']),last_native_end_s=lock['sentences'][-1]['end_s'],end_hold_s=tail,master_audio_sha256=sha(pathlib.Path(lock['master_audio'])),voice_PCM_frames=fmt['frames'],clips=rows,captions=caption_rows))
main=read(D/'locked_timing.json');anchors=main['source_to_target_anchors'];main_meta=dict(duration_s=main['total_s'],frames=main['total_frames'],captions=len(main['captions']),sentences=len(main['main_sentences']),anchors=len(anchors),dropped=len(main['dropped_conformance_anchors']),brand_intro=main['brand_intro'],brand_outro=main['brand_outro'],outro_gap_s=main['brand_outro']['start_s']-main['last_spoken_end_s'],master_audio_sha256=main['master_audio_sha256'])
assert main_meta['outro_gap_s']==3 and main_meta['frames']==20452 and main_meta['sentences']==90 and main_meta['captions']==181 and main_meta['anchors']==389 and main_meta['dropped']==0
report=dict(status='passed_all31_cuts_and84_caption_cues' if not failures else 'required_correction',checked_at=datetime.now(timezone.utc).isoformat(),clips_checked=total_clips,cues_checked=total_cues,shorts=reports,main_lock_summary=main_meta,failed_checks=failures,coverage=dict(native_source_guards=True,actual_complete_clip_PCM_equality=True,subtitle_rejoin_and_number_unit_boundaries=True,actual_listening=False,actual_hearing=False,continuous_playback=False,final_MP4=False),limitations='Cuts are guarded against provider native adjacent speech, not acoustically forced-aligned listening. Master mix/naturalness and encoded Shorts still require final media evidence.')
(Q/'shorts_cut_caption_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status=report['status'],clips=total_clips,cues=total_cues,failed=failures,durations=[x['duration_s'] for x in reports]),ensure_ascii=False))
