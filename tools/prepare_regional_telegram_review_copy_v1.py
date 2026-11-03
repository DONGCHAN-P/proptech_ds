"""Keep the 1080p master and make a labelled smaller delivery copy only if needed."""
from pathlib import Path
import argparse,datetime as dt,hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
EP=ROOT/'video-agent-studio/episodes/regional-price-recovery-20261022'
OUT=EP/'outputs/production-v1-jun'
DEST=EP/'director/production-v1/delivery'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb')as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--technical',required=True);args=ap.parse_args()
    tech=read(ROOT/args.technical);master=ROOT/tech['video']['path']
    assert sha(master)==tech['video']['sha256'] and tech['full_decode']=='pass'
    if master.stat().st_size<=48_000_000:
        print(json.dumps({'copy_required':False,'bytes':master.stat().st_size}));return
    DEST.mkdir(parents=True,exist_ok=True)
    dest=DEST/'regional_visual_review_v1_TELEGRAM_720p.mp4'
    assert not dest.exists(),'Preserve existing copies; inspect the receipt instead of repeating'
    assets=read(OUT/'reusable_assets/manifest.json');ff,probe=assets['ffmpeg'],assets['ffprobe']
    cmd=[ff,'-hide_banner','-y','-i',str(master),'-vf','scale=1280:720:flags=lanczos','-c:v','libx264','-preset','fast','-crf','28','-maxrate','330k','-bufsize','660k','-pix_fmt','yuv420p','-c:a','aac','-b:a','64k','-movflags','+faststart',str(dest)]
    with (DEST/'telegram_copy_encode.log').open('w',encoding='utf8')as log:
        proc=subprocess.run(cmd,stdout=log,stderr=log)
    assert proc.returncode==0
    info=json.loads(subprocess.check_output([probe,'-v','error','-show_streams','-show_format','-of','json',str(dest)],text=True,encoding='utf8'))
    video=next(s for s in info['streams']if s['codec_type']=='video')
    assert video['width']==1280 and video['height']==720 and video['r_frame_rate']=='30/1'
    assert int(video['nb_frames'])==tech['video']['frames']
    assert abs(float(info['format']['duration'])-tech['video']['duration'])<.1
    assert dest.stat().st_size<=48_000_000
    decoded=subprocess.run([ff,'-v','error','-i',str(dest),'-f','null','-'],capture_output=True,text=True,encoding='utf8')
    assert decoded.returncode==0 and not decoded.stderr.strip()
    receipt={'at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'path':dest.relative_to(ROOT).as_posix(),
        'sha256':sha(dest),'bytes':dest.stat().st_size,'master_sha256':tech['video']['sha256'],'master_preserved':sha(master)==tech['video']['sha256'],
        'resolution':[1280,720],'fps':30,'frames':tech['video']['frames'],'full_decode':'pass','purpose':'smaller Telegram review copy; native master stays 1080p30',
        'continuous_playback_performed':False,'actual_listening_performed':False}
    (DEST/'telegram_copy_manifest.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(receipt,ensure_ascii=False))
if __name__=='__main__':main()
