"""Independent local AAC/PCM and encoded-frame verification of completed v5."""
from pathlib import Path
import hashlib, json, subprocess, wave
from datetime import datetime, timezone
import numpy as np
from PIL import Image, ImageDraw

HERE=Path(__file__).resolve().parent
EP=HERE.parents[1]
ROOT=EP.parents[2]
DIRECTOR=EP/'director/shorts-ending-fix-v1'
FF=ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
PROBE=ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,data):
    (HERE/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def wav(p):
    with wave.open(str(p),'rb') as w:
        assert w.getnchannels()==1 and w.getsampwidth()==2 and w.getframerate()==44100
        return np.frombuffer(w.readframes(w.getnframes()),dtype='<i2')
def db(x):
    rms=float(np.sqrt(np.mean(np.asarray(x,dtype=float)**2)))
    return round(float(20*np.log10(max(1e-10,rms))),3)
def aac(p):
    return np.frombuffer(subprocess.check_output([str(FF),'-v','error','-xerror','-i',str(p),'-vn','-ac','1','-ar','44100','-c:a','pcm_f32le','-f','f32le','pipe:1']),dtype='<f4')

plan=load(HERE/'input_edit_plan.json')
old_measure=load(HERE/'measurements.json')
records=[]; boundaries=[]; frame_manifest=[]
expected={'promo':'6d05bd6a6cf70b8bbd897423d2092b8f07556ed9e5629e019c62526c3c5cabf8',
          'summary':'06ae5222b598867c07b8ceab91244afc1dfac79f433f38ae3abd7b97466a28c0'}
for p in plan['shorts']:
    sid=p['id']; name=p['name'].replace('_v4','_v5')
    old=EP/'outputs/jun-quality-v2/shorts'/(p['name']+'.mp4')
    new=EP/'outputs/jun-quality-v2/shorts/v5-ending-fix'/(name+'.mp4')
    assert sha(new)==expected[sid]
    pr=json.loads(subprocess.check_output([str(PROBE),'-v','error','-show_format','-show_streams','-of','json',str(new)]))
    save(sid+'_v5_ffprobe.json',pr)
    vs=next(s for s in pr['streams'] if s['codec_type']=='video')
    assert int(vs['nb_frames'])==p['frames'] and (vs['width'],vs['height'])==(1080,1920)
    oldpcm=wav(EP/'editor/jun-quality-v2/shorts'/(p['name']+'_audio.wav'))
    newpcm=wav(DIRECTOR/(name+'_audio.wav'))
    assert len(oldpcm)==len(newpcm)==round(p['duration_s']*44100)
    olddec,newdec=aac(old),aac(new)
    receipt=load(DIRECTOR/(sid+'_audio_fix_receipt.json'))
    fixes={r['scene']:r for r in receipt['sources']}
    for r in p['ranges']:
        fix=fixes[r['scene_id']]; clean=fix['clean_source_out_s']; at=round(r['output_start_s']*44100)
        first=round(r['source_in_s']*44100); stop=round(clean*44100)
        source=wav(Path(r['path']))
        edge=round(.003*44100); n=stop-first
        assert np.array_equal(newpcm[at+edge:at+n-edge],source[first+edge:stop-edge])
        row=dict(short_id=sid,scene_id=r['scene_id'],clean_source_out_s=clean,output_pcm_end_s=(at+n)/44100,
                 original_output_pcm_end_s=(at+round(r['source_out_s']*44100)-first)/44100,
                 source_pcm_preserved_except_3ms_edges=True)
        if r['scene_id']=='S13':
            row.update(action='keep_same_source_continuation',unchanged_pcm_in_entire_slot=bool(np.array_equal(oldpcm[at:at+round(r['output_duration_s']*44100)],newpcm[at:at+round(r['output_duration_s']*44100)])))
            assert row['unchanged_pcm_in_entire_slot']
        else:
            oldend=row['original_output_pcm_end_s']; newend=row['output_pcm_end_s']
            removed=newpcm[at+n:round(oldend*44100)]
            silence=newdec[round((oldend-.045)*44100):round((oldend-.008)*44100)]
            near_clean=newdec[round((newend-.020)*44100):round(newend*44100)]
            removed_aac=newdec[round((newend+.010)*44100):round(oldend*44100)]
            original=next(x for x in old_measure['boundaries'] if x['short_id']==sid and x['scene_id']==r['scene_id'])
            a,b=original['independent_5ms_quiet_span_dbfs_lt_minus55']
            speech_lo=r['output_start_s']+a-r['source_in_s']-.8
            speech_hi=r['output_start_s']+a-r['source_in_s']-.05
            aa=olddec[round(speech_lo*44100):round(speech_hi*44100)]
            bb=newdec[round(speech_lo*44100):round(speech_hi*44100)]
            row.update(action='shorten_source_and_zero_pad_existing_slot',padding_to_old_cut_all_zero=bool(np.all(removed==0)),
                       original_cut_regression_window_s=[oldend-.045,oldend-.008],actual_aac_original_cut_rms_dbfs=db(silence),
                       actual_aac_last20ms_at_clean_cut_rms_dbfs=db(near_clean),actual_aac_removed_region_rms_dbfs=db(removed_aac),
                       last_target_speech_v4_v5_correlation=round(float(np.corrcoef(aa,bb)[0,1]),9),
                       last_target_speech_v4_v5_error_rms_dbfs=db(aa-bb),
                       pass_silence_at_original_cut=db(silence)<-60)
            assert row['padding_to_old_cut_all_zero'] and row['pass_silence_at_original_cut']
        boundaries.append(row)
    srtold=old.with_suffix('.srt'); srtnew=new.with_suffix('.srt')
    assert srtold.read_bytes()==srtnew.read_bytes()
    frame_ids=set()
    for r in p['ranges'][1:]:
        k=round(r['output_start_s']*30); frame_ids.update([k-1,k])
    k=round(p['speech_cut_end_s']*30)
    frame_ids.update([k-1,k,k+1,k+3,k+6,k+10,k+11,p['frames']-1])
    ids=sorted(frame_ids)
    select='+'.join(f'eq(n\\,{f})' for f in ids)
    subprocess.run([str(FF),'-v','error','-xerror','-n','-i',str(new),'-an','-vf','select='+select,'-vsync','0',str(HERE/(sid+'_v5_frame_%02d.png'))],check=True)
    images={f:HERE/(sid+f'_v5_frame_{i+1:02d}.png') for i,f in enumerate(ids)}
    assert all(path.exists() for path in images.values())
    for f,path in images.items():frame_manifest.append(dict(short_id=sid,frame_index=f,pts_s=f/30,path=str(path)))
    # Six frames: three relevant visual boundaries, before and after each.
    sheet=Image.new('RGB',(720,2010),'white'); d=ImageDraw.Draw(sheet)
    for row,r in enumerate([*p['ranges'][1:],dict(output_start_s=p['speech_cut_end_s'])]):
        f=round(r['output_start_s']*30)
        for col,idx in enumerate([f-1,f]):
            im=Image.open(images[idx]);im.thumbnail((360,640));sheet.paste(im,(col*360,row*670+30))
            d.text((col*360+6,row*670+8),f'{sid} f{idx} {idx/30:.3f}s',fill='black')
    sheet.save(HERE/(sid+'_v5_boundaries.jpg'),quality=95)
    sheet=Image.new('RGB',(1500,563),'white');d=ImageDraw.Draw(sheet)
    for i,idx in enumerate([k,k+1,k+3,k+6,k+11]):
        im=Image.open(images[idx]);im.thumbnail((300,533));sheet.paste(im,(i*300,30))
        d.text((i*300+6,8),f'CTA +{(idx-k)/30:.3f}s',fill='black')
    sheet.save(HERE/(sid+'_v5_cta_blend.jpg'),quality=95)
    tail=newdec[round((p['speech_cut_end_s']+.1)*44100):round((p['duration_s']-.1)*44100)]
    records.append(dict(short_id=sid,path=str(new),sha256=sha(new),bytes=new.stat().st_size,frames=p['frames'],duration_s=float(vs['duration']),
                        audio_duration_s=next(s['duration'] for s in pr['streams'] if s['codec_type']=='audio'),
                        srt_sha256=sha(srtnew),srt_byte_identical_to_v4=True,actual_aac_tail_rms_dbfs=db(tail),
                        actual_aac_full_decode_pass=True,video_decode_through_last_frame_pass=True,
                        last_frame_path=str(images[p['frames']-1]),cta_transition_frame_indices=[k,k+1,k+3,k+6,k+10,k+11],
                        cta_transition_interval_s=[p['speech_cut_end_s'],p['speech_cut_end_s']+.35]))
save('v5_measurements.json',dict(created_at_utc=datetime.now(timezone.utc).isoformat(),media=records,boundaries=boundaries,frame_manifest=frame_manifest,
                               actual_listening=False,continuous_playback=False,asr='separate v5_asr.json'))
print(json.dumps(dict(status='v5_signal_and_frames_extracted',boundaries=boundaries,media=records),ensure_ascii=False))
