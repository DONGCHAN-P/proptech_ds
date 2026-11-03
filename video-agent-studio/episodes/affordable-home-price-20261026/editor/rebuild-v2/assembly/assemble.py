"""Local, frame-exact full-film assembly. Writes only the two assigned roots.

prepare: real PCM/timing -> draft EDL, eight cards and preserved-sample voice stem.
render: exact scene manifest + representative approval -> final CFR EDL/MP4/SRT.
No network, TTS, installer, upload, shared-state or sibling-project writes.
"""
import argparse
import array
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import wave
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
EP = HERE.parents[2]
STUDIO = EP.parents[1]
ROOT = STUDIO.parent
OUT = EP / 'outputs/rebuild-v2/full-film-r2-v1'
FF = STUDIO / 'episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
PROBE = ROOT / 'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
FONT = STUDIO / 'episodes/capital-10eok-map-20261017/visual/map-preview-v1/Pretendard-Bold.ttf'
SCRIPT = EP / 'director/rebuild-v2/frozen-script-v3-r2/scenes_v3_r2.json'
LOCK = EP / 'director/rebuild-v2/locked_script_r2.json'
TIMING = EP / 'narration/rebuild-v2/audio-r2-recovered/final_timing.json'
MEDIA = EP / 'director/production-v1/media_assets.json'
EXPECTED = 'cc1ef7d80225e992e7e5d31faffbfb09a8f90c80fb5352e17c36eb8c90755b12'
FPS, SR = 30, 48000
CHAPTER_ASSETS = [
    EP/'visual/hero-budget-v1.png',
    EP/'visual/rebuild-v2/transaction-costs.png',
    EP/'visual/rebuild-v2/bank-limits.png',
    STUDIO/'episodes/regional-price-recovery-20261022/outputs/guide-v3/project/assets/images/budget.png',
    STUDIO/'assets/chapter-backgrounds/v1/price.png',
    EP/'visual/rebuild-v2/family-policy.png',
    EP/'visual/newborn-home-v1.png',
    STUDIO/'assets/chapter-backgrounds/v1/comparison.png',
]


def owned(p):
    p = Path(p).resolve()
    if not any(p.is_relative_to(r.resolve()) for r in (HERE, OUT)):
        raise ValueError('Write outside exclusive ownership: '+str(p))
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def read(p):
    return json.loads(Path(p).read_text('utf-8-sig'))


def dump(p, obj):
    owned(p).write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', 'utf8')


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()


def pin(p):
    p = Path(p).resolve()
    return dict(path=p.as_posix(), sha256=sha(p), bytes=p.stat().st_size)


def source(p):
    p = Path(p)
    choices = [p] if p.is_absolute() else [ROOT/p, EP/p]
    p = next((f.resolve() for f in choices if f.is_file()), None)
    if not p or not p.is_relative_to(ROOT.resolve()) or p.name == '.env':
        raise ValueError('Missing/workspace-external source: '+str(choices))
    return p


def probe(p, count=False):
    args = [str(PROBE), '-v', 'error']
    if count:
        args += ['-count_frames']
    return json.loads(subprocess.check_output(args+['-show_streams','-show_format','-of','json',str(p)]))


def ceilframe(t):
    return math.ceil(t*FPS-1e-8)


def run(label, argv, inputs=(), outputs=()):
    """Hash-bound resume; failed commands are never retried automatically."""
    path = OUT/'commands'/label
    path.mkdir(parents=True, exist_ok=True)
    receipt = path/'receipt.json'
    refs = [pin(p) for p in inputs]
    signature = hashlib.sha256(json.dumps([argv,refs],sort_keys=True).encode()).hexdigest()
    if receipt.exists():
        old = read(receipt)
        if old.get('signature') == signature and old.get('returncode') == 0 and all(Path(r['path']).exists() and sha(r['path']) == r['sha256'] for r in old['outputs']):
            return old
        raise ValueError('Changed/failed existing step; inspect before new version: '+label)
    for p in outputs:
        if Path(p).exists():
            raise ValueError('Unreceipted existing output: '+str(p))
    dump(path/'argv.json', argv)
    with owned(path/'stdout.log').open('w', encoding='utf8') as log:
        result = subprocess.run(list(map(str,argv)),cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
    evidence = dict(signature=signature,returncode=result.returncode,inputs=refs,outputs=[pin(p) for p in outputs if Path(p).is_file()],log=pin(path/'stdout.log'))
    dump(receipt,evidence)
    if result.returncode:
        raise RuntimeError('Failed '+label+'; '+str(path/'stdout.log'))
    return evidence


def inputs():
    script, timing, lock = read(SCRIPT), read(TIMING), read(LOCK)
    assert sha(SCRIPT) == EXPECTED == timing['script_sha256'] == lock['script_sha256']
    assert lock['approved'] is True and lock['claude_approved'] is True
    assert timing['rate'] == '+0%' and timing['voice'] == 'ko-KR-InJoonNeural'
    assert timing['brand_and_chapter_cards_included'] is False
    assert [s['id'] for s in script['scenes']] == [s['id'] for s in timing['scenes']]
    assert len(script['scenes']) == 34
    media = read(MEDIA)
    assets = {}
    for a in media['assets']:
        f = source(a['path'])
        assert sha(f) == a['sha256'], str(f)
        assets[a['asset_id']] = f
    for s, t in zip(script['scenes'],timing['scenes']):
        assert s['narration'] == t['narration'] and s['chapter'] == t['chapter']
        f = source(t['audio_48k_path'])
        assert sha(f) == t['audio_48k_sha256'], s['id']
        with wave.open(str(f),'rb') as w:
            assert w.getframerate() == SR and w.getsampwidth() == 2
            assert abs(w.getnframes()/SR-t['duration_s']) < 1/SR
        for c in t['cues']:
            assert s['narration'][c['source_start']:c['source_end']] == c['text']
        for b, expected in zip(t['beats'],s['beats']):
            assert b['anchor'] == expected['anchor'] and b['action'] == expected['action']
            assert s['narration'][b['source_start']:b['source_end']] == b['anchor']
    return script,timing,assets


def cards(script):
    from PIL import Image, ImageDraw, ImageFont, ImageOps
    assert len(CHAPTER_ASSETS) == len(set(CHAPTER_ASSETS)) == 8
    font = ImageFont.truetype(str(FONT),72)
    rows, thumbs = [], []
    for c, bg in zip(script['chapters'],CHAPTER_ASSETS):
        cid = c['id']; folder = OUT/'chapters'/f'C{cid:02}'
        folder.mkdir(parents=True,exist_ok=True)
        background = folder/'background.png'
        title = folder/'title.png'
        preview = folder/'preview.png'
        movie = folder/f'chapter_{cid:02}.mp4'
        metadata = folder/'layers.json'
        text = f"{cid}. {c['title']}"
        if not metadata.exists():
            image = ImageOps.fit(Image.open(bg).convert('RGB'),(1920,1080),method=Image.Resampling.LANCZOS)
            image.save(owned(background))
            layer = Image.new('RGBA',(1920,1080))
            draw = ImageDraw.Draw(layer)
            # A separate title layer contains its contrast gradient; the photo stays fixed.
            for x in range(1920):
                draw.line((x,0,x,1079), fill=(13,38,61,round(220*max(0,1-x/1700))))
            box = draw.textbbox((96,444),text,font=font,stroke_width=0)
            assert 72 <= box[0] < box[2] <= 1824 and 72 <= box[1] < box[3] <= 1008
            draw.text((96,444),text,font=font,fill=(246,244,239,255))
            layer.save(owned(title))
            Image.alpha_composite(image.convert('RGBA'),layer).convert('RGB').save(owned(preview))
            dump(metadata,dict(chapter_id=cid,title=text,title_font=pin(FONT),font_size_px=72,title_bbox=list(box),source=pin(bg),background_layer=pin(background),title_layer=pin(title),duration_frames=90,photo_motion='none',material_type='ai_concept',screen_AI_badge=False,actual_location_evidence=False,source_use_count=1))
        row = read(metadata)
        assert row['source']['sha256'] == sha(bg) and row['title'] == text
        run(f'card-{cid:02}',[str(FF),'-hide_banner','-v','warning','-n','-loop','1','-framerate','30','-i',str(background),'-loop','1','-framerate','30','-i',str(title),'-filter_complex','[0:v][1:v]overlay=0:0,format=yuv420p[v]','-map','[v]','-an','-frames:v','90','-c:v','libx264','-preset','fast','-crf','18','-r','30','-video_track_timescale','15360','-movflags','+faststart',str(movie)],inputs=[background,title],outputs=[movie])
        rows.append(dict(chapter_id=cid,source=pin(movie),layers=pin(metadata),asset=pin(bg),title=text))
        thumb = Image.open(preview).convert('RGB'); thumb.thumbnail((480,270)); thumbs.append(thumb)
    sheet = Image.new('RGB',(960,1080))
    for i,im in enumerate(thumbs): sheet.paste(im,((i%2)*480,(i//2)*270))
    sheet.save(owned(OUT/'chapters/contact.png'))
    dump(OUT/'chapter_manifest.json',dict(chapters=rows,distinct_photos=8,total_frames=720))
    return {r['chapter_id']:r for r in rows}


def manifest_rows(path, script):
    if Path(path).resolve().parent.name in ('actual-scenes-r2-v1','actual-scenes-r2-parent-v1'):
        raise ValueError('User excluded v1: blank opening-context defect; use corrected v2 manifest')
    data = read(path)
    assert data['script']['sha256'] == EXPECTED
    assert data['timing']['sha256'] == sha(TIMING)
    rows = data.get('scenes',data.get('renders'))
    if not isinstance(rows,list): raise ValueError('Scene manifest requires scenes/renders array')
    result = {}
    for r in rows:
        sid = r.get('scene_id',r.get('id'))
        if sid in result: raise ValueError('Duplicate scene '+sid)
        if r.get('status') not in (None,'encoded'):
            raise ValueError('Scene not yet encoded: '+str(sid))
        ref = r.get('encoded',r.get('mp4',r.get('file',r.get('output',r.get('path')))))
        if isinstance(ref,dict):
            f = source(ref['path']); expected = ref.get('sha256')
        else:
            f = source(ref); expected = r.get('sha256',r.get('mp4_sha256'))
        if not expected or sha(f) != expected: raise ValueError('Missing/changed scene MP4 SHA '+sid)
        info = probe(f,True)
        v = [x for x in info['streams'] if x['codec_type']=='video']
        assert len(v)==1 and (v[0]['width'],v[0]['height'])==(1920,1080)
        assert v[0]['r_frame_rate']=='30/1' and v[0]['avg_frame_rate']=='30/1'
        project = Path(r.get('project',f.parent))
        if not project.is_absolute(): project = source(project/'index.html').parent
        model = source(r.get('model',r.get('source_json_path',project/'scene.json')))
        html = source(r.get('html',r.get('html_path',project/'index.html')))
        model_data=read(model)
        assert model_data.get('template_only') is False
        assert model_data.get('script_sha256',EXPECTED)==EXPECTED
        result[sid] = dict(source=pin(f),frames=int(v[0]['nb_read_frames']),probe=info,project=str(project.resolve()),model=pin(model),html=pin(html))
    assert set(result) == {s['id'] for s in script['scenes']}
    return result


def edl(script,timing,assets,chapters,actual=None):
    segments,scenes,cues,beats = [],[],[],[]
    cursor=0
    def add(ident,kind,frames,src,**fields):
        nonlocal cursor
        row=dict(id=ident,kind=kind,start_frame=cursor,end_frame=cursor+frames,duration_frames=frames,source_in_frame=0,source_out_frame=frames,source=src,scene_id=None,chapter_id=None,**fields)
        segments.append(row);cursor+=frames
        return row
    seen=set()
    for i,(s,t) in enumerate(zip(script['scenes'],timing['scenes'])):
        sid=s['id'];cid=s['chapter']
        if i==1:
            add('BRAND_INTRO','brand_intro',150,pin(assets['channel_brand_intro_clean_v7']))
        if i>0 and cid not in seen:
            cr=add(f'CHAPTER_{cid:02}','chapter',90,chapters[cid]['source'])
            cr['chapter_id']=cid
            seen.add(cid)
        settled=max(b['start_s']+min(.45,max(.06,b['end_s']-b['start_s'])) for b in t['beats'])
        frames=ceilframe(max(t['duration_s'],settled+1.2))
        if actual:
            frames=actual[sid]['frames']
            assert frames>=ceilframe(t['duration_s']), sid+': encoded scene truncates PCM'
        # Final speech+3 hold is already in the WAV. Preserve every source PCM sample.
        if i==len(timing['scenes'])-1:
            frames=max(ceilframe(t['last_speech_end_s']+3),ceilframe(t['duration_s']))
            assert frames>=ceilframe(settled+1.2), 'Final read hold conflicts with CTA end'
        src=actual[sid]['source'] if actual else None
        row=add(sid,'hook' if i==0 else 'body',frames,src)
        row.update(scene_id=sid,chapter_id=cid,audio_source=pin(source(t['audio_48k_path'])),audio_samples_preserved=round(t['duration_s']*SR),padding_samples=frames*(SR//FPS)-round(t['duration_s']*SR),tail_policy='preserve_all_PCM_then_CFR_pad; no_extra_0.25s',local_duration_s=t['duration_s'],native_gap_after_s=t['gap_after_s'],added_gap_s=0)
        if actual: row['source_out_frame']=min(frames,actual[sid]['frames'])
        scene=dict(scene_id=sid,chapter=cid,start_frame=row['start_frame'],end_frame=row['end_frame'],source_in_frame=0,source_in_s=0,audio_start_frame=row['start_frame'],audio_source=row['audio_source'],last_speech_global_s=row['start_frame']/FPS+t['last_speech_end_s'],local_duration_s=t['duration_s'],tail_policy=row['tail_policy'],project=actual[sid]['project'] if actual else None,model=actual[sid]['model'] if actual else None)
        scenes.append(scene)
        for c in t['cues']:
            r=dict(c)
            r.update(local_start_s=c['start_s'],local_end_s=c['end_s'],start_frame=row['start_frame']+ceilframe(c['start_s']),end_frame=row['start_frame']+ceilframe(c['end_s']))
            r.update(global_start_s=r['start_frame']/FPS,global_end_s=r['end_frame']/FPS)
            assert row['start_frame']<=r['start_frame']<r['end_frame']<=row['end_frame']
            cues.append(r)
        for bi,b in enumerate(t['beats']):
            r=dict(b)
            r.update(scene_id=sid,beat_index=bi,local_start_s=b['start_s'],local_end_s=b['end_s'],global_start_s=row['start_frame']/FPS+b['start_s'],global_end_s=row['start_frame']/FPS+b['end_s'],start_frame=row['start_frame']+ceilframe(b['start_s']),end_frame=row['start_frame']+ceilframe(b['end_s']),provider_timing_basis=b['timing_basis'],timing_basis='native_word_boundary',cue_ids=[c['id'] for c in t['cues'] if c['first_word_index']<=b['last_word_index'] and b['first_word_index']<=c['last_word_index']])
            beats.append(r)
    assert seen==set(range(1,9))
    outro=add('BRAND_OUTRO','brand_outro',300,pin(assets['channel_brand_outro_clean_v7']))
    assert outro['start_frame']==max(ceilframe(scenes[-1]['last_speech_global_s']+3),scenes[-1]['start_frame']+ceilframe(timing['scenes'][-1]['duration_s']))
    result=dict(schema_version='full-film-global-edl-v1',status='actual_manifest_bound' if actual else 'draft_waiting_actual_scene_manifest',clock='global_frames',fps=30,total_frames=cursor,total_seconds=cursor/FPS,script=pin(SCRIPT),script_lock=pin(LOCK),timing=pin(TIMING),segments=segments,scenes=scenes,cues=cues,beats=beats,progressions=[dict(kind=k,scene_id=sid,beat_frames=[b['start_frame'] for b in beats if b['scene_id']==sid],timing_basis='native_word_boundary') for k,sid in [('funding_waterfall','R003'),('ltv_dsr','R006'),('monthly_budget','R030')]],zoom=dict(mode='fixed',max_frames=[]),last_speech_global_s=scenes[-1]['last_speech_global_s'],outro_start_frame=outro['start_frame'],outro_start_s=outro['start_frame']/FPS,gap_policy='natural_PCM_tail_no_extra_0.25s',audio_speed=1.0,actual_listening=False,continuous_playback=False)
    assert len(segments)==44 and len(scenes)==34
    assert segments[0]['start_frame']==0 and all(a['end_frame']==b['start_frame'] for a,b in zip(segments,segments[1:]))
    assert [s['scene_id'] for s in scenes]==[s['id'] for s in script['scenes']]
    return result


def srt(edl,path):
    def stamp(frame):
        ms=round(frame*1000/FPS)
        h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
        return f'{h:02}:{m:02}:{s:02},{ms:03}'
    entries=[]
    for i,c in enumerate(edl['cues'],1):
        entries.append(f"{i}\n{stamp(c['start_frame'])} --> {stamp(c['end_frame'])}\n"+'\n'.join(c['display_lines'])+'\n')
    owned(path).write_text('\n'.join(entries),'utf-8-sig')


def voice_stem(edl,name):
    file=OUT/name
    receipt=OUT/(name+'.json')
    signature=hashlib.sha256(json.dumps([(s['id'],s['duration_frames'],s.get('audio_source')) for s in edl['segments']],sort_keys=True).encode()).hexdigest()
    if receipt.exists():
        old=read(receipt)
        assert old['signature']==signature and sha(file)==old['output']['sha256']
        return file
    if file.exists(): raise ValueError('Unreceipted PCM stem '+str(file))
    refs=[]
    with wave.open(str(owned(file)),'wb') as out:
        out.setparams((1,2,SR,0,'NONE','not compressed'))
        for s in edl['segments']:
            target=s['duration_frames']*(SR//FPS)
            audio=s.get('audio_source')
            if audio:
                p=source(audio['path']); assert sha(p)==audio['sha256']
                with wave.open(str(p),'rb') as w:
                    assert (w.getnchannels(),w.getsampwidth(),w.getframerate())==(1,2,SR)
                    n=w.getnframes(); raw=w.readframes(n)
                assert target>=n
                out.writeframesraw(raw)
                out.writeframesraw(b'\0\0'*(target-n))
                refs.append(dict(scene_id=s['scene_id'],source=audio,source_samples=n,source_PCM_payload_sha256=hashlib.sha256(raw).hexdigest(),global_start_sample=s['start_frame']*(SR//FPS),padding_samples=target-n))
            else: out.writeframesraw(b'\0\0'*target)
    dump(receipt,dict(signature=signature,output=pin(file),sample_rate=SR,channels=1,source_pcm_unmodified=True,samples=edl['total_frames']*(SR//FPS),scenes=refs))
    return file


def prepare():
    script,timing,assets=inputs()
    chapter=cards(script)
    plan=edl(script,timing,assets,chapter)
    dump(OUT/'global_edl_draft.json',plan)
    srt(plan,OUT/'captions_global_draft.srt')
    voice_stem(plan,'voice_preserved_draft.wav')
    dump(HERE/'handoff.json',dict(status='assembly_prepared_waiting_rendered_scene_manifest_and_representative_approval',outputs=[str(OUT/'global_edl_draft.json'),str(OUT/'chapter_manifest.json'),str(OUT/'voice_preserved_draft.wav')],input_versions=dict(script=pin(SCRIPT),timing=pin(TIMING),media=pin(MEDIA)),validation=dict(scene_order_exact=True,all34_PCM_SHA_verified=True,chapter_images_distinct=8,actual_listening=False,continuous_playback=False),unresolved=['Tesla actual scene MP4 manifest','actualvoice representative approval receipt'],affected_scenes=[s['id'] for s in script['scenes']],next_owner='Tesla manifest -> assembly render -> Bohr QA -> director'))
    print(json.dumps(dict(status='prepared',edl=str(OUT/'global_edl_draft.json'),frames=plan['total_frames'],seconds=plan['total_seconds'],cues=len(plan['cues']),beats=len(plan['beats'])),ensure_ascii=False))


def normalized_segments(plan):
    files=[]
    for i,s in enumerate(plan['segments']):
        f=source(s['source']['path']); assert sha(f)==s['source']['sha256']
        target=OUT/'segments'/f'{i:02}_{s["id"]}.mp4';owned(target)
        info=probe(f);v=next(x for x in info['streams'] if x['codec_type']=='video')
        count=s['duration_frames']
        # Canonicalize each independently decoded clip before concatenation.
        # Brand sources decode as full-range yuvj420p/BT.470BG; body is limited
        # yuv420p/BT.709. A single reinitializing filter graph resets frame N.
        vf='tpad=stop_mode=clone:stop_duration=10,scale=1920:1080:in_range=auto:out_range=tv:out_color_matrix=bt709,format=yuv420p,setsar=1,setparams=range=tv:color_primaries=bt709:color_trc=bt709:colorspace=bt709,setpts=N/(30*TB)'
        command=[str(FF),'-hide_banner','-v','warning','-n','-i',str(f),'-map','0:v:0','-an','-vf',vf,'-r','30','-fps_mode','cfr','-enc_time_base','1:30','-c:v','libx264','-preset','veryfast','-crf','18','-bf','0']
        command+=['-frames:v',str(count),'-video_track_timescale','15360','-movflags','+faststart',str(target)]
        run(f'normalize-{i:02}-{s["id"]}',command,[f],[target])
        assert int(next(x for x in probe(target)['streams'] if x['codec_type']=='video')['nb_frames'])==count
        files.append(target)
    concat=OUT/'concat_video.txt'
    owned(concat).write_text('\n'.join("file '"+f.as_posix().replace("'","'\\''")+"'" for f in files)+'\n','utf8')
    picture=OUT/'picture_only.mp4'
    run('picture-concat',[str(FF),'-hide_banner','-v','warning','-n','-f','concat','-safe','0','-i',str(concat),'-map','0:v:0','-an','-c:v','copy','-video_track_timescale','15360','-movflags','+faststart',str(picture)],files+[concat],[picture])
    return picture


def mix(plan,voice,assets):
    """Continuous music clock, spectral room for speech, measured sidechain + fades."""
    duration=plan['total_seconds'];bgm=assets['existing_channel_bgm']
    # Existing brand audio is replaced by the same licensed continuous BGM source;
    # clean brand picture is byte-preserved, and no duplicate soundtrack is mixed.
    recipe=dict(voice_gain=1.0,voice_speed=1.0,source_PCM_preserved=True,music=pin(bgm),music_clock='global continuous loop',music_gain=.085,voice_band_EQ=[dict(hz=250,gain_db=-2,width_oct=1),dict(hz=2000,gain_db=-4,width_oct=1.4),dict(hz=4200,gain_db=-2,width_oct=1)],duck=dict(threshold=.018,ratio=8,attack_ms=20,release_ms=400),fade_in_s=.8,fade_out_s=2,brand_audio_policy='continuous licensed Thinking Music; source brand embedded soundtrack not doubled',loudnorm=dict(I=-17,TP=-1.5,LRA=9),actual_listening=False)
    graph=f'[0:a]aformat=sample_rates=48000:channel_layouts=stereo,asplit=2[voice][key];[1:a]atrim=duration={duration:.12f},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo,equalizer=f=250:t=o:w=1:g=-2,equalizer=f=2000:t=o:w=1.4:g=-4,equalizer=f=4200:t=o:w=1:g=-2,volume=0.085,afade=t=in:st=0:d=0.8,afade=t=out:st={duration-2:.12f}:d=2[bed];[bed][key]sidechaincompress=threshold=0.018:ratio=8:attack=20:release=400[duck];[voice][duck]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.94:level=false:latency=true[mix]'
    premix=OUT/'premix_float.wav'
    run('premix',[str(FF),'-hide_banner','-v','warning','-n','-i',str(voice),'-stream_loop','-1','-i',str(bgm),'-filter_complex',graph,'-map','[mix]','-c:a','pcm_f32le','-ar','48000','-ac','2','-t',str(duration),str(premix)],[voice,bgm],[premix])
    measurement=run('measure-premix',[str(FF),'-hide_banner','-i',str(premix),'-af','loudnorm=I=-17:TP=-1.5:LRA=9:print_format=json','-f','null','-'],[premix])
    log=Path(measurement['log']['path']).read_text('utf8')
    matches=re.findall(r'\{\s*"input_i".*?\}',log,re.S)
    if not matches: raise ValueError('No loudness measurement')
    levels=json.loads(matches[-1]);recipe['premix_loudness']=levels
    filt=f"loudnorm=I=-17:TP=-1.5:LRA=9:measured_I={levels['input_i']}:measured_TP={levels['input_tp']}:measured_LRA={levels['input_lra']}:measured_thresh={levels['input_thresh']}:offset={levels['target_offset']}:linear=true:print_format=json"
    dump(OUT/'audio_recipe.json',recipe)
    return premix,filt


def verify(plan,movie):
    meta=probe(movie);dump(OUT/'probe.json',meta)
    video=next(s for s in meta['streams'] if s['codec_type']=='video');audio=next(s for s in meta['streams'] if s['codec_type']=='audio')
    assert (video['width'],video['height'],video['r_frame_rate'],video['avg_frame_rate'])==(1920,1080,'30/1','30/1')
    assert int(video['nb_frames'])==plan['total_frames']
    assert abs(float(video['duration'])-plan['total_seconds'])<.001
    assert audio['sample_rate']=='48000' and audio['channels']==2
    assert abs(float(audio['duration'])-plan['total_seconds'])<.024
    pts_receipt=run('full-frame-PTS',[str(PROBE),'-v','error','-select_streams','v:0','-show_frames','-show_entries','frame=best_effort_timestamp_time,pkt_duration_time','-of','json',str(movie)],[movie])
    pts=read(pts_receipt['log']['path'])['frames']
    assert len(pts)==plan['total_frames']
    for index,frame in enumerate(pts):
        assert abs(float(frame['best_effort_timestamp_time'])-index/30)<.000001, str(index)
    dump(OUT/'frame_pts_validation.json',dict(status='pass',decoded_frame_count=len(pts),first_PTS=float(pts[0]['best_effort_timestamp_time']),last_PTS=float(pts[-1]['best_effort_timestamp_time']),all_frames_CFR=True,no_PTS_gap_or_overlap=True,frame_duration_s=1/30,source=pts_receipt['log'],movie=pin(movie)))
    decode=run('full-av-decode',[str(FF),'-hide_banner','-v','error','-xerror','-i',str(movie),'-map','0:v:0','-map','0:a:0','-f','null','-'],[movie])
    signal=run('final-av-signal',[str(FF),'-hide_banner','-i',str(movie),'-map','0:a:0','-af','astats=metadata=0:reset=0,ebur128=peak=true','-f','null','-'],[movie])
    log=Path(signal['log']['path']).read_text('utf8')
    lines=log.splitlines();summary='\n'.join(lines[-70:])
    def last_number(pattern):
        found=re.findall(pattern,log)
        return float(found[-1]) if found else None
    metrics=dict(integrated_LUFS=last_number(r'I:\s*([-\d.]+) LUFS'),LRA_LU=last_number(r'LRA:\s*([-\d.]+) LU'),true_peak_dBTP=last_number(r'Peak:\s*([-\d.]+) dBFS'),sample_peak_dBFS=last_number(r'Peak level dB:\s*([-\d.]+)'),RMS_dBFS=last_number(r'RMS level dB:\s*([-\d.]+)'),NaN_samples=last_number(r'Number of NaNs:\s*(\d+)'),Inf_samples=last_number(r'Number of Infs:\s*(\d+)'))
    receipt=dict(status='technical_verified_subjective_review_pending',movie=pin(movie),probe=pin(OUT/'probe.json'),frame_pts_validation=pin(OUT/'frame_pts_validation.json'),total_frames=plan['total_frames'],duration_seconds=plan['total_seconds'],resolution=[1920,1080],fps='30/1',audio_streams=1,audio_sample_rate=48000,audio_channels=2,full_AV_decode_returncode=decode['returncode'],full_AV_decode_log=decode['log'],signal_log=signal['log'],metrics=metrics,signal_summary=summary,actual_listening=False,continuous_playback=False,pronunciation_verified=False,perceived_music_voice_balance_reviewed=False)
    dump(OUT/'av_signal_receipt.json',receipt)
    return receipt


def evidence(plan,actual,args,movie,technical):
    refs={}
    def include(f):
        f=Path(f).resolve()
        if f.is_file(): refs[str(f)]=pin(f)
    music_license=next(v['license'] for v in read(MEDIA)['assets'] if v['asset_id']=='existing_channel_bgm')
    credit_text='\n'.join([music_license['credit'],music_license['url'],music_license['license_url']])+'\n'
    for name in ['credits.txt','description_music_credit.txt','music_credits.txt']:
        owned(OUT/name).write_text(credit_text,'utf8');include(OUT/name)
    for asset in read(MEDIA)['assets']:
        f=source(asset['path']);assert sha(f)==asset['sha256'];include(f)
    for f in [OUT/'audio_recipe.json',OUT/'voice_preserved.wav.json',OUT/'encoded_audio_signal.json']:
        include(f)
    for f in [SCRIPT,LOCK,TIMING,MEDIA,FONT,FF,PROBE,Path(args.scene_manifest),Path(args.representative_approval),HERE/'edl_contract.json',HERE/'extract_samples.py',HERE/'check_encoded_audio.py',Path(__file__),*CHAPTER_ASSETS]:include(f)
    scene_manifest=read(args.scene_manifest)
    for ref in scene_manifest.get('code_inputs',[]):
        f=source(ref['path']);assert sha(f)==ref['sha256'];include(f)
    for key in ['recovery_provenance','timing','script_lock','visual_override']:
        ref=scene_manifest.get(key)
        if ref:
            f=source(ref['path']);assert sha(f)==ref['sha256'];include(f)
    projects=[]
    for sid,r in actual.items():
        projects.append(dict(scene_id=sid,html=r['html'],model=r['model'],allowed_text_shapes=[]))
        include(r['source']['path'])
        for f in Path(r['project']).rglob('*'):
            if f.is_file() and f.suffix.lower() in ('.html','.json','.js','.css','.woff2','.woff','.ttf','.png','.jpg','.jpeg','.svg','.wav'):include(f)
    order={r['scene_id']:i for i,r in enumerate(plan['scenes'])};projects.sort(key=lambda r:order[r['scene_id']])
    for s in plan['segments']:
        if s.get('source'):include(s['source']['path'])
        if s.get('audio_source'):include(s['audio_source']['path'])
    for f in (OUT/'chapters').rglob('*'):
        if f.is_file():include(f)
    dump(OUT/'source_manifest.json',dict(script_sha256=EXPECTED,files=list(refs.values()),scope='actual scene project and assembly dependencies',actual_listening=False))
    receipt=dict(status='rendered_technical_verified_independent_QA_pending',mp4=pin(movie),srt=pin(OUT/'captions_global.srt'),edl=pin(OUT/'global_edl.json'),source_manifest=pin(OUT/'source_manifest.json'),music_credit=pin(OUT/'description_music_credit.txt'),script=pin(SCRIPT),script_lock=pin(LOCK),timing=pin(TIMING),scene_manifest=pin(Path(args.scene_manifest)),representative_approval=pin(Path(args.representative_approval)),audio_recipe=pin(OUT/'audio_recipe.json'),signal_receipt=pin(OUT/'av_signal_receipt.json'),voice_sample_receipt=pin(OUT/'voice_preserved.wav.json'),sampled_frame_index=pin(OUT/'sampled_frames/frame_index.json'),commands=str(OUT/'commands'),render_command=[sys.executable,'-B','-X','utf8',str(Path(__file__)),'render','--scene-manifest',str(Path(args.scene_manifest).resolve()),'--representative-approval',str(Path(args.representative_approval).resolve())],frames=plan['total_frames'],seconds=plan['total_seconds'],actual_listening=False,continuous_playback=False,new_paid_calls=0,network_calls=0,upload_executed=False)
    dump(OUT/'render_receipt.json',receipt)
    packet=dict(status='actual_media_ready_for_independent_QA',evidence_kind='actual_media',scope='full',script_lock=pin(LOCK),script=pin(SCRIPT),mp4=pin(movie),srt=pin(OUT/'captions_global.srt'),edl=pin(OUT/'global_edl.json'),render_receipt=pin(OUT/'render_receipt.json'),source_manifest=pin(OUT/'source_manifest.json'),source_projects=projects)
    dump(OUT/'qa_packet.json',packet)
    lines=['# 전역 배치 가이드','',f"배포 파일: `{movie.name}` · 1920×1080 · 30fps · {plan['total_seconds']:.3f}초",'',f"자막: `captions_global.srt` · {len(plan['cues'])}큐. 전체 컷: `global_edl.json`.",'','모든 전환은 빈 프레임 없는 하드 컷입니다. 본문 원속도 PCM을 전부 보존하고 자연 꼬리와 CFR 패딩만 사용합니다. 자막·출처는 장면 렌더의 별도 레이어이며 배경 줌을 추가하지 않습니다.','', '| 구간 | 추천 시작(초) | 길이(초) | 레이어/자료 유형 |','|---|---:|---:|---|']
    for s in plan['segments']:
        typ='기존 채널 브랜드' if s['kind'].startswith('brand') else '고정 개념 배경 + 별도 72px 제목' if s['kind']=='chapter' else '실제 음성·자료도식·자막·출처'
        lines.append(f"| {s['id']} | {s['start_frame']/30:.3f} | {s['duration_frames']/30:.3f} | {typ} |")
    lines+=['','Thinking Music 출처는 `music_credits.txt`를 사용합니다. 실제 청취·연속 재생·업로드는 수행하지 않았습니다.']
    owned(HERE/'placement_guide.md').write_text('\n'.join(lines)+'\n','utf8')
    dump(HERE/'handoff.json',dict(status=receipt['status'],outputs=[packet['mp4'],packet['srt'],packet['edl'],packet['render_receipt'],pin(OUT/'qa_packet.json')],input_versions=dict(script=pin(SCRIPT),timing=pin(TIMING),scene_manifest=pin(Path(args.scene_manifest))),validation=dict(technical=pin(OUT/'av_signal_receipt.json'),all34_PCM_preserved=True,exact_script_array_order=True,all_cues_shifted=True,all_beats_shifted=True,actual_listening=False,continuous_playback=False),unresolved=['Bohr encoded-media independent review','director actual Claude final media review','subjective listening not performed'],affected_scenes=[s['scene_id'] for s in plan['scenes']],next_owner='Bohr QA + director'))
    print(json.dumps(dict(status=receipt['status'],mp4=receipt['mp4'],srt=receipt['srt'],frames=plan['total_frames'],seconds=plan['total_seconds'],qa_packet=str(OUT/'qa_packet.json')),ensure_ascii=False))


def render(args):
    approval=read(args.representative_approval)
    if approval.get('approved') is not True:
        raise ValueError('Actualvoice representative approved=true receipt required')
    if approval.get('script_sha256') != EXPECTED:
        raise ValueError('Representative approval must bind exact script SHA')
    script,timing,assets=inputs()
    actual=manifest_rows(args.scene_manifest,script)
    # Approval belongs to the encoded representatives from this corrected run.
    approved_reps=approval.get('representative_scene_mp4s',[])
    if {r['scene_id'] for r in approved_reps}!={'R003','R006','R030'}:
        raise ValueError('Representative gate needs exact R003/R006/R030 MP4 hashes')
    for ref in approved_reps:
        if ref['sha256']!=actual[ref['scene_id']]['source']['sha256']:
            raise ValueError('Representative approval belongs to another encoded version')
        f=source(ref['path']);assert sha(f)==ref['sha256']
    for ref in approval.get('review_receipts',[]):
        f=source(ref['path']);assert sha(f)==ref['sha256']
    plan=edl(script,timing,assets,cards(script),actual)
    dump(OUT/'global_edl.json',plan);srt(plan,OUT/'captions_global.srt')
    voice=voice_stem(plan,'voice_preserved.wav')
    picture=normalized_segments(plan)
    premix,normalization=mix(plan,voice,assets)
    movie=OUT/'affordable_home_price_rebuild_r2_v1.mp4'
    run('final-mux',[str(FF),'-hide_banner','-v','info','-n','-i',str(picture),'-i',str(premix),'-map','0:v:0','-map','1:a:0','-c:v','copy','-af',normalization,'-c:a','aac','-b:a','256k','-ar','48000','-ac','2','-t',str(plan['total_seconds']),'-video_track_timescale','15360','-movflags','+faststart',str(movie)],[picture,premix],[movie])
    technical=verify(plan,movie)
    run('check-encoded-audio',[sys.executable,'-B','-X','utf8',str(HERE/'check_encoded_audio.py')],[movie,OUT/'global_edl.json',HERE/'check_encoded_audio.py'],[OUT/'encoded_audio_signal.json'])
    technical['encoded_audio_PCM_signal']=pin(OUT/'encoded_audio_signal.json')
    dump(OUT/'av_signal_receipt.json',technical)
    run('sample-encoded-cuts',[sys.executable,'-B','-X','utf8',str(HERE/'extract_samples.py')],[movie,OUT/'global_edl.json',HERE/'extract_samples.py'],[OUT/'sampled_frames/frame_index.json'])
    evidence(plan,actual,args,movie,technical)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    subs=p.add_subparsers(dest='command',required=True)
    subs.add_parser('prepare')
    r=subs.add_parser('render');r.add_argument('--scene-manifest',required=True);r.add_argument('--representative-approval',required=True)
    args=p.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    if args.command=='prepare':prepare()
    else:render(args)


if __name__=='__main__':
    try:main()
    except Exception as e:
        dump(HERE/'failure_receipt.json',dict(error=type(e).__name__,message=str(e),actual_listening=False,continuous_playback=False))
        raise
