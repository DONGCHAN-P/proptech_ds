"""Verify the actual three MP4s, decode, extract representative encoded frames."""
import argparse, hashlib, json, subprocess, sys
from pathlib import Path
from PIL import Image, ImageChops, ImageStat, ImageDraw, ImageFont
ED=Path(__file__).resolve().parent;EP=ED.parent.parent;REPO=EP.parents[2]
OUT=EP/'outputs/production-v1-jun';CHECK=OUT/'checks';PREVIEW=OUT/'previews'
def run(cmd):
    p=subprocess.run([str(x) for x in cmd],capture_output=True,text=True,encoding='utf-8',errors='replace')
    if p.returncode: raise RuntimeError(f'{cmd!r}\n{p.stderr[-3000:]}')
    return p.stdout,p.stderr
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--only',choices=['incheon2008-2016recovery']);args=ap.parse_args()
    m=json.loads((OUT/'reusable_assets/manifest.json').read_text(encoding='utf-8-sig'));ff=m['ffmpeg'];probe=m['ffprobe'];reports=[];posters=[]
    version,_=run([ff,'-version']);(CHECK/'ffmpeg_version.txt').write_text(version,encoding='utf-8')
    for name in ['full2006paths','incheon2008-2016recovery','rawmedianvsindex']:
        if args.only and name!=args.only:
            posters.append(CHECK/'encoded_preview_frames'/f'{name}_4s.png');continue
        file=PREVIEW/f'{name}_provisional_v1.mp4'
        if name=='incheon2008-2016recovery' and (PREVIEW/f'{name}_provisional_v2.mp4').is_file():file=PREVIEW/f'{name}_provisional_v2.mp4'
        raw,_=run([probe,'-v','error','-count_frames','-show_streams','-show_format','-of','json',file]);meta=json.loads(raw)
        (CHECK/f'{name}_ffprobe.json').write_text(raw,encoding='utf-8')
        vs=[x for x in meta['streams'] if x['codec_type']=='video'];au=[x for x in meta['streams'] if x['codec_type']=='audio'];assert len(vs)==1 and not au,'Silent preview expected'
        v=vs[0];assert (v['width'],v['height'],v['avg_frame_rate'],int(v['nb_read_frames']))==(1920,1080,'30/1',240)
        assert abs(float(v['duration'])-8)<.034
        _,decode=run([ff,'-v','error','-i',file,'-map','0:v:0','-f','null','-'])
        assert not decode.strip(),decode
        (CHECK/f'{name}_decode.txt').write_text('exit=0\n'+decode,encoding='utf-8')
        frames=[]
        for t in [0,2,4,6,239/30]:
            dest=PREVIEW/f'{name}_encoded_{t:.3f}s.png'
            run([ff,'-y','-v','error','-ss',f'{t:.8f}','-i',file,'-frames:v','1',dest]);assert dest.is_file();frames.append(dest)
            if t==4:posters.append(dest)
        a,b=[Image.open(p).convert('RGB') for p in [frames[1],frames[3]]]
        mean=sum(ImageStat.Stat(ImageChops.difference(a,b)).mean)/3
        assert mean>.01,'No visible motion between 2s and 6s'
        reports.append(dict(file=str(file.relative_to(REPO)),sha256=sha(file),video_duration=v['duration'],container_duration=meta['format']['duration'],resolution=[1920,1080],fps='30/1',decoded_frames=int(v['nb_read_frames']),audio_stream_count=0,decode_exit=0,motion_2s_vs_6s_mean_pixel_difference=mean,representative_frames=[str(x.relative_to(REPO)) for x in frames]))
    sheet=Image.new('RGB',(960,3*580),'#f6f4ef');draw=ImageDraw.Draw(sheet)
    for i,p in enumerate(posters):
        im=Image.open(p).convert('RGB');im.thumbnail((960,540));sheet.paste(im,(0,i*580));draw.text((20,i*580+548),p.stem,fill='#173348')
    sheet.save(PREVIEW/'representative_contactsheet.png')
    receipt=dict(status='technical_preview_checks_passed',scope='incheon v2 only; unchanged other two reuse checks/preview_technical.json' if args.only else '3 silent 8s previews only',prior_technical_checks=str((CHECK/'preview_technical.json').relative_to(REPO)) if args.only else None,actual_listening=False,continuous_playback=False,rendered_files=reports,contactsheet=str((PREVIEW/'representative_contactsheet.png').relative_to(REPO)))
    (CHECK/'media_validation.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(receipt,ensure_ascii=False))
if __name__=='__main__':main()
