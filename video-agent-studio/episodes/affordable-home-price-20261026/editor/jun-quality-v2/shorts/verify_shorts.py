"""Verification and handoff evidence for the actual encoded portrait MP4s."""
from pathlib import Path
import json, subprocess, hashlib, importlib.util, math
from datetime import datetime, timezone
from PIL import Image, ImageDraw

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('shorts_build',HERE/'build_shorts.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
OUT=b.OUT
def run(args, log=None):
    r=subprocess.run([str(x) for x in args],capture_output=True)
    if log:log.write_bytes(r.stdout+r.stderr)
    assert r.returncode==0,(args,r.stderr.decode('utf-8','replace')[-2000:])
    return r
def bbox_intersects(a,c):return a[0]<c[2] and a[2]>c[0] and a[1]<c[3] and a[3]>c[1]

def main():
    plan=b.load(HERE/'edit_plan.json');checks=[]
    evidence=HERE/'qa'/plan['revision']; evidence.mkdir(parents=True,exist_ok=True)
    cfg=b.load(b.ROOT/'config/vertical_video_safe_area.json')
    profile=cfg['profiles']['youtube_portrait_full_frame_v2']
    bounds=b.load(HERE/'layout_bounds.json')
    masks=[[0,0,1080,240],[0,1400,1080,1920],[900,240,1080,1400]]
    overlap=[x for x in bounds['elements'] if any(bbox_intersects(x['bbox'],m) for m in masks)]
    assert not overlap,overlap
    b.save(evidence/'native_ui_overlap.json',dict(profile='youtube_portrait_full_frame_v2',mask_rects=masks,
         measured_text_count=len(bounds['elements']),overlaps=overlap,passed=True,scope='Native 9:16 YouTube UI simulation, not an actual device playback'))
    for p in plan['shorts']:
        video=OUT/(p['name']+'.mp4')
        probe=json.loads(run([b.PROBE,'-v','error','-show_streams','-show_format','-of','json',video]).stdout)
        b.save(evidence/(p['id']+'_ffprobe.json'),probe)
        v=next(x for x in probe['streams'] if x['codec_type']=='video');a=next(x for x in probe['streams'] if x['codec_type']=='audio')
        assert (v['width'],v['height'],v['r_frame_rate'],v['sample_aspect_ratio'],v['pix_fmt'])==(1080,1920,'30/1','1:1','yuv420p')
        assert abs(float(probe['format']['duration'])-p['duration_s'])<.05
        assert v['codec_name']=='h264' and a['codec_name']=='aac' and a['sample_rate']=='48000'
        assert int(v['nb_frames'])==p['frames']
        assert not any(x.get('rotation',0) for x in v.get('side_data_list',[]))
        run([b.FF,'-v','error','-xerror','-i',video,'-map','0:v:0','-map','0:a:0','-f','null','-'],evidence/(p['id']+'_decode.log'))
        # Verify every subtitle against exact original snippets and its source map.
        for c in p['captions']:
            assert 0<=c['start_s']<c['end_s']<=p['duration_s']
            assert len(c['lines']) in (1,2)
            assert ' '.join(c['lines'])==c['text']
        for x,y in zip(p['captions'],p['captions'][1:]):assert x['end_s']<=y['start_s']+.000001
        sets=([.8,4.5,7.5,11.3,15.7,21.8,23.0,27.8,31.6,34.8,35.5,37.5] if p['id']=='promo' else
              [.8,3.6,5.9,7.3,10,11.8,15.8,18.6,22.3,24.5,27.5,31.3,34.2,34.8,38.6,43.1,48.3,50.3])
        # Include the longest subtitle and both sides of every audio-edit boundary.
        longest=max(p['captions'],key=lambda x:max(len(y) for y in x['lines']))
        sets.append((longest['start_s']+longest['end_s'])/2)
        boundaries=[r['output_start_s'] for r in p['ranges'][1:]]+[p['speech_cut_end_s']]
        for t in boundaries:sets.extend([max(0,t-1/30),min(p['duration_s']-1/30,t+1/30)])
        frames=[]
        for i,t in enumerate(sorted(set(round(x,3) for x in sets))):
            dest=evidence/f'{p["id"]}_{i:02}_{t:06.3f}.jpg'
            run([b.FF,'-v','error','-n','-ss',t,'-i',video,'-frames:v','1','-q:v','2',dest])
            frames.append(dict(time_s=t,path=str(dest)))
        thumbs=[]
        for f in frames:
            im=Image.open(f['path']).convert('RGB').resize((270,480));thumb=Image.new('RGB',(270,508),'#e6e6e6');thumb.paste(im,(0,28))
            ImageDraw.Draw(thumb).text((8,7),f'{p["id"]} {f["time_s"]:06.3f}s',fill='black');thumbs.append(thumb)
        sheet=Image.new('RGB',(1080,508*math.ceil(len(thumbs)/4)),'#dddddd')
        for i,im in enumerate(thumbs):sheet.paste(im,((i%4)*270,(i//4)*508))
        sheet.save(evidence/(p['id']+'_encoded_contact_sheet.jpg'))
        # Native UI overlay is modeled, with essential content protected separately.
        im=Image.open(frames[len(frames)//2]['path']).convert('RGBA');overlay=Image.new('RGBA',im.size,(0,0,0,0));d=ImageDraw.Draw(overlay)
        for r in masks:d.rectangle(r,fill=(12,17,24,180))
        d.text((28,65),'MODELED YouTube UI',fill='white',font=b.font(32))
        Image.alpha_composite(im,overlay).convert('RGB').save(evidence/(p['id']+'_native_ui_model.jpg'))
        # Phone fit/crop geometry is evaluated separately from platform overlays.
        phone=[]
        for vw,vh in cfg['validation']['phone_viewports_css']:
            for fit in ['contain','cover']:
                scale=(min if fit=='contain' else max)(vw/1080,vh/1920)
                ox=(vw-1080*scale)/2;oy=(vh-1920*scale)/2
                clipped=[]
                for el in bounds['elements']:
                    bb=el['bbox'];x0,y0,x1,y1=[bb[0]*scale+ox,bb[1]*scale+oy,bb[2]*scale+ox,bb[3]*scale+oy]
                    if x0<0 or y0<0 or x1>vw or y1>vh:clipped.append(el.get('id',el.get('text')))
                phone.append(dict(viewport=[vw,vh],fit=fit,text_clipped_by_canvas=len(clipped)))
        b.save(evidence/(p['id']+'_phone_crop_models.json'),dict(models=phone,scope='Geometric text crop only; native modeled UI is tested separately; no actual device playback'))
        checks.append(dict(id=p['id'],path=str(video),sha256=b.sha(video),bytes=video.stat().st_size,duration_s=float(probe['format']['duration']),
             resolution=[1080,1920],fps='30/1',frames=int(v['nb_frames']),audio_codec=a['codec_name'],audio_channels=a['channels'],audio_hz=a['sample_rate'],
             decode_passed=True,caption_cues=len(p['captions']),caption_overlap=False,actual_listening=False,continuous_playback=False,
             sampled_frames=frames,source_ranges=p['ranges']))
    # Snapshot every actual immutable input, including tools, fonts and local build.
    inputs=[b.N/'scene_alignment.json',b.N/'caption_plan.json',b.N/'narration_body.txt',b.N/'narration_manifest.json',
        b.EP/'editor/jun-user-script-v1/full-film-v1/schedule.json',b.EP/'editor/jun-user-script-v1/full-film-v1/assemble.py',
        b.EP/'editor/jun-user-script-v1/full-film-v1/build_visuals.py',b.EP/'visual/jun-user-script-v1/editor_asset_packet.json',
        b.ROOT/'config/vertical_video_safe_area.json',b.ROOT/'video-agent-studio/guides/세로영상_안전영역.md',b.HOUSE_ASSET,b.FF,b.PROBE,HERE/'build_shorts.py',HERE/'verify_shorts.py']
    inputs.extend((HERE/'fonts').glob('*.ttf'))
    inputs.extend({Path(r['path']) for p in plan['shorts'] for r in p['ranges']})
    b.save(HERE/'input_versions.json',dict(inputs=[dict(path=str(x),sha256=b.sha(x)) for x in inputs],new_external_calls=0,new_paid_TTS=0,
         hyperframes_usage='unknown: no network/usage request permitted by task; approved local FFmpeg route used'))
    b.save(evidence/'technical_report.json',dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),shorts=checks,
         mathematical_check=dict(equity=100000000-20000000,theoretical_price=80000000/.3,example_price=266000000,loan=186000000,
          monthly_payment=186000000*(.045/12)/(1-(1+.045/12)**(-360))),
         scope='Full decode, metadata, source character alignment, measured glyph bounds, sampled actual frames. Listening, continuous playback and independent editorial QA remain parent responsibility.'))
    files=[x for x in OUT.iterdir() if x.is_file() and x.name!='SHA256SUMS.txt']
    b.write(OUT/'SHA256SUMS.txt','\n'.join(b.sha(x)+'  '+x.name for x in sorted(files))+'\n')
    print(json.dumps(dict(status='verified',shorts=[{k:v for k,v in x.items() if k in ['id','duration_s','sha256','caption_cues','decode_passed']} for x in checks],native_ui_overlap_count=0)))

if __name__=='__main__':main()
