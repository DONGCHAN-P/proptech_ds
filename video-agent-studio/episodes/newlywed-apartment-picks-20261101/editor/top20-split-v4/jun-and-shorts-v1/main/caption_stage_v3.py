"""Show the white rail only in the actual native-caption cue union; reuse v1 picture/AAC/lock."""
from pathlib import Path
import hashlib
import json
import math
import os
import subprocess
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent))
import conform as c

P=c.HERE/'jun-v3'
PROJECT=P/'project'
OUTPUT=c.OUTPUT/'part1_Jun_conform_jun-v3.mp4'


def body_windows(d):
    windows=[]
    for cue in sorted(d['captions'],key=lambda row:row['start_s']):
        start,end=float(cue['start_s']),float(cue['end_s'])
        if not 0 <= start < end:
            raise ValueError('Invalid native caption cue')
        if windows and start <= windows[-1][1]+1e-8:
            windows[-1]=(windows[-1][0],max(windows[-1][1],end))
        else:
            windows.append((start,end))
    return windows


def background_windows(d):
    intro=d['brand_intro']
    return [(0.,intro['start_s']),
            (intro['start_s']+intro['duration_s'],d['brand_outro']['start_s'])]


def enable(windows):
    return '+'.join(f'between(n,{math.ceil(a*c.FPS-1e-7)},{math.ceil(b*c.FPS-1e-7)-1})'for a,b in windows)


def build():
    from PIL import Image
    d=c.read(c.LOCK)
    previous=c.read(c.HERE/'jun-v1/render_receipt.json')
    if c.sha(c.LOCK)!=previous['lock_sha256']:
        raise ValueError('Parent lock changed; this revision must reuse the same lock')
    picture=Path(previous['picture'])
    if c.sha(picture)!=previous['picture_sha256'] or c.sha(previous['video'])!=previous['video_sha256']:
        raise ValueError('v1 cached inputs changed')
    audio=Path(d['master_audio'])
    if c.sha(audio)!=previous['master_audio_sha256']:
        raise ValueError('Parent master changed')
    info={'audio':audio,'mask_windows':body_windows(d)}
    # The shared emitter owns editable text/font geometry; only its box windows
    # change here. An additional opaque flat rail covers baked source boxes too.
    c.emit_project(d,info,PROJECT)
    dest=c.owned(PROJECT/'assets/conformed_picture.mp4')
    if not dest.exists():
        os.link(picture,dest)
    if not os.path.samefile(dest,picture):
        raise ValueError('Must reuse the existing conformed picture, never reconform')
    flat=c.owned(PROJECT/'assets/flat_caption_rail.png')
    Image.new('RGB',(c.WIDTH,c.HEIGHT-c.RAIL_Y),'#f6f4ef').save(flat)
    index=(PROJECT/'index.html').read_text(encoding='utf-8')
    index=index.replace('data-track-index=\'3\'','data-track-index=\'4\'')
    index=index.replace('data-track-index=\'2\'','data-track-index=\'3\'')
    index=index.replace('data-track-index=\'1\'','data-track-index=\'2\'')
    index=index.replace('old-caption-mask-','caption-box-')
    clears=[]
    for i,(a,b)in enumerate(background_windows(d)):
        clears.append(f"<img id='baked-caption-clear-{i}' class='clip rail' src='assets/flat_caption_rail.png' data-start='{a:.9f}' data-duration='{b-a:.9f}' data-track-index='1'/>")
    index=index.replace('</video>','</video>\n'+'\n'.join(clears),1)
    c.write(PROJECT/'index.html',index)
    c.save(PROJECT/'background_windows.json',background_windows(d))
    c.save(PROJECT/'caption_box_windows.json',body_windows(d))
    c.save(P/'input_manifest.json',{'revision':'jun-v3_native_caption_cue_union_only',
        'lock':str(c.LOCK),'lock_sha256':previous['lock_sha256'],
        'cached_picture':str(picture),'cached_picture_sha256':previous['picture_sha256'],
        'cached_picture_reused_same_file':os.path.samefile(picture,dest),
        'AAC_source_video':previous['video'],'AAC_source_video_sha256':previous['video_sha256'],
        'master_audio':str(audio),'master_audio_sha256':previous['master_audio_sha256'],
        'opaque_clear_windows':background_windows(d),'white_box_windows':body_windows(d),'native_caption_count':len(d['captions']),'merged_box_window_count':len(body_windows(d)),
        'guide_basis':'latest user/parent instruction: hide rail in every inactive native-caption interval, overriding body cue-gap default',
        'source_to_target_anchors_changed':False,'native_cues_changed':False,
        'TTS_or_paid_calls':0,'reconform_performed':False,
        'caption_stage_code_sha256':c.sha(__file__),'shared_emitter_sha256':c.sha(c.HERE/'conform.py')})
    return d,previous


def render():
    d,previous=build()
    if OUTPUT.exists():
        raise FileExistsError('Preserve existing v3 output')
    filters=(f"[0:v][2:v]overlay=x=0:y={c.RAIL_Y}:enable='{enable(background_windows(d))}'[clear];"
             f"[clear][3:v]overlay=x=0:y={c.RAIL_Y}:enable='{enable(body_windows(d))}'[box];"
             '[box]ass=filename=captions.ass:fontsdir=assets/fonts[delivery]')
    command=[str(c.FF),'-v','warning','-nostdin','-i',previous['picture'],
             '-i',previous['video'],'-loop','1','-framerate','30','-i','assets/flat_caption_rail.png',
             '-loop','1','-framerate','30','-i','assets/caption_rail.png',
             '-filter_complex_threads','2','-filter_complex',filters,
             '-map','[delivery]','-map','1:a:0','-c:v','libx264','-preset','fast','-crf','16',
             '-threads','6','-pix_fmt','yuv420p','-r','30','-c:a','copy',
             '-frames:v',str(d['total_frames']),'-t',f'{d["total_s"]:.9f}',
             '-video_track_timescale','15360','-movflags','+faststart',str(OUTPUT)]
    c.save(P/'render_command.json',{'command':command,'cwd':str(PROJECT),
        'route':'cached conformed picture -> caption stage only; AAC stream copy',
        'anchor_retiming':False,'source_frame_decode_or_reconform':False})
    started=time.monotonic()
    with c.owned(P/'encode.stderr.log').open('wb')as log:
        r=subprocess.run(command,cwd=PROJECT,stdout=subprocess.DEVNULL,stderr=log,creationflags=c.NO_WINDOW)
    if r.returncode:
        raise RuntimeError('Caption-stage encode failed; see encode.stderr.log')
    probe=c.probe(OUTPUT)
    v=next(s for s in probe['streams']if s['codec_type']=='video')
    if (v['width'],v['height'],v['r_frame_rate'],int(v['nb_frames']))!=(1920,1080,'30/1',20452):
        raise ValueError('v3 media specification changed')
    decode=[str(c.FF),'-v','error','-xerror','-i',str(OUTPUT),'-map','0:v:0','-map','0:a:0','-f','null','-']
    with c.owned(P/'decode.stderr.log').open('wb')as log:
        subprocess.run(decode,stderr=log,stdout=subprocess.DEVNULL,check=True,creationflags=c.NO_WINDOW)
    hashes=[]
    for path in [previous['video'],OUTPUT]:
        z=subprocess.run([str(c.FF),'-v','error','-i',str(path),'-map','0:a:0','-c','copy','-f','hash','-hash','sha256','-'],capture_output=True,check=True,creationflags=c.NO_WINDOW)
        hashes.append(z.stdout.decode().strip())
    if hashes[0]!=hashes[1]:
        raise ValueError('AAC packet payload changed')
    if c.sha(previous['video'])!=previous['video_sha256'] or c.sha(c.LOCK)!=previous['lock_sha256']:
        raise ValueError('v1 or parent lock changed during caption-only revision')
    receipt={'status':'encoded_strict_decode_passed','video':str(OUTPUT),
        'video_sha256':c.sha(OUTPUT),'probe':probe,'duration_s':d['total_s'],'frames':d['total_frames'],
        'elapsed_s':round(time.monotonic()-started,3),'lock_sha256':previous['lock_sha256'],
        'previous_video_sha256':previous['video_sha256'],'cached_picture_sha256':previous['picture_sha256'],
        'master_audio_sha256':previous['master_audio_sha256'],'audio_packet_hash_v1':hashes[0],
        'audio_packet_hash_v3':hashes[1],'audio_stream_copied_bit_identically':True,
        'reconform_performed':False,'anchors_changed':False,'native_cues_changed':False,
        'white_box_policy':'actual native-caption cue union only','merged_box_window_count':len(body_windows(d)),'crop_or_scale':False,'new_paid_calls':0,'actual_listening':False,'continuous_playback':False}
    c.save(P/'render_receipt.json',receipt)
    print(json.dumps({'status':receipt['status'],'video':str(OUTPUT),'sha256':receipt['video_sha256'],
                      'AAC_bit_identical':True,'elapsed_s':receipt['elapsed_s']},ensure_ascii=False),flush=True)


if __name__=='__main__':
    render()
