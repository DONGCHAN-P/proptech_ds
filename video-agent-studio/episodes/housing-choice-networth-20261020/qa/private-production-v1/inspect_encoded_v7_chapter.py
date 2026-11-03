"""Extract caption delta evidence only from a chapter with a completed receipt."""
import argparse, hashlib, json, subprocess
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

QA=Path(__file__).resolve().parent
EP=QA.parents[1]
ROOT=EP.parents[2]
SOURCE=EP/'outputs/private-production-v3'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()
def pin(p): return {'path':p.relative_to(EP).as_posix(),'sha256':sha(p)}
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--chapter',type=int,choices=range(1,11),required=True);args=parser.parse_args();n=args.chapter
    video=SOURCE/f'renders/caption-v7/ch{n:02d}.mp4';rp=video.with_suffix('.receipt.json')
    assert rp.is_file(),'No completed chapter receipt; do not inspect in-progress shared MP4'
    receipt=read(rp);video_sha=sha(video);assert video_sha==receipt['output_sha256']
    current=SOURCE/f'ch{n:02d}';assert sha(current/'index.html')==receipt['html_sha256']
    sourcepass=read(QA/'source_v7_pass_receipt.json');sourcepin=next(p for p in sourcepass['current_HTML_pins'] if p['chapter']==n)
    assert sha(current/'index.html')==sourcepin['html_sha256'] and sha(current/'timing.json')==sourcepin['timing_sha256']
    target=QA/f'encoded-v7/ch{n:02d}-{video_sha[:12]}';assert not target.exists(),'Keep existing extraction and review evidence'
    timing=read(EP/'narration/free-tts-v1/caption-v7/final_timing.json')
    assert sha(EP/'narration/free-tts-v1/caption-v7/final_timing.json')==sourcepass['caption_timing_sha256']
    all_cues={c['id']:(ch['chapter'],c) for ch in timing['chapters'] for c in ch['cues']}
    changes=read(EP/'narration/free-tts-v1/caption-v7/change_manifest.json')
    repairs={new for row in changes['v6_to_v7_cue_mapping'] if row['was_short'] for new in row['v7_ids']}
    metrics=read(EP/'editor/private-production-v3/caption_fit_metrics.json')
    assert metrics['caption_timing_sha256']==sourcepass['caption_timing_sha256'] and metrics['failures']==[]
    widest=max(metrics['cues'],key=lambda c:max(l['width'] for l in c['lines']))['cue_id']
    longest=max(all_cues,key=lambda k:max(map(len,all_cues[k][1]['display_lines'])))
    longest_duration=max(all_cues,key=lambda k:all_cues[k][1]['end_s']-all_cues[k][1]['start_s'])
    selected=repairs|{widest,longest,longest_duration,'C01_P001V7Q002','C09_P048V7Q003','C10_P052V7Q003'}
    for chapter,fragment in [(5,'대출잔액에'),(6,'한국 돈으로')]:
        selected.add(next(k for k,(ch,c) in all_cues.items() if ch==chapter and fragment in c['text']))
    stream=next(s for s in receipt['ffprobe']['streams'] if s['codec_type']=='video')
    assert stream['width']==1920 and stream['height']==1080 and stream['r_frame_rate']=='30/1'
    last_frame=int(stream['nb_frames'])-1;points=[]
    for cue_id in selected:
        chapter,c=all_cues[cue_id]
        if chapter==n:points.append({'role':'caption_delta_midpoint','cue_id':cue_id,'text':c['text'],'display_lines':c['display_lines'],'frame':round((c['start_s']+c['end_s'])/2*30)})
    for role,frame in [('chapter_first',0),('chapter_last',last_frame)]:points.append({'role':role,'frame':frame})
    if n==1:points.append({'role':'first44s_regression','frame':1320})
    indices=sorted({min(last_frame,max(0,p['frame'])) for p in points})
    target.mkdir(parents=True);frames=target/'frames';frames.mkdir()
    provision=read(EP/'director/two-episode-production-v1/ffmpeg_receipt.json');ffmpeg=ROOT/provision['binary'];assert sha(ffmpeg)==provision['binary_sha256']
    select='+'.join(f'eq(n\\,{i})' for i in indices)
    argv=[str(ffmpeg),'-v','error','-nostdin','-threads','2','-i',str(video),'-an','-vf','select='+select,'-fps_mode','vfr','-start_number','0','-n',str(frames/'%04d.png')]
    result=subprocess.run(argv,capture_output=True,text=True,encoding='utf-8',errors='replace')
    (target/'extraction.log').write_text(result.stderr,encoding='utf-8');assert result.returncode==0 and not result.stderr.strip()
    assert len(list(frames.glob('*.png')))==len(indices)
    for p in points:
        p['time_s']=p['frame']/30;p['file']=pin(frames/f'{indices.index(p["frame"]):04d}.png')
    ordered=sorted(points,key=lambda p:p['frame']);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
    sheets=[]
    for j in range(0,len(ordered),4):
        group=ordered[j:j+4];sheet=Image.new('RGB',(1920,1120),'white');draw=ImageDraw.Draw(sheet)
        for i,p in enumerate(group):
            x=(i%2)*960;y=(i//2)*560;draw.text((x+8,y+3),f'ch{n:02} {p.get("cue_id",p["role"])} t={p["time_s"]:.3f}',font=font,fill='black')
            with Image.open(EP/p['file']['path']) as img:sheet.paste(img.resize((960,540),Image.Resampling.LANCZOS),(x,y+20))
        fp=target/f'contact_{j//4+1:02d}.jpg';sheet.save(fp,quality=95);sheets.append(pin(fp))
    report={'status':'completed_encoded_chapter_extracted_actual_visual_review_pending','chapter':n,'checked_at':datetime.now(timezone.utc).isoformat(),
      'script_sha256':sourcepass['script_sha256'],'caption_timing_sha256':sourcepass['caption_timing_sha256'],'video':pin(video),'completed_receipt':pin(rp),
      'source_HTML':pin(current/'index.html'),'source_timing':pin(current/'timing.json'),'caption_fit_metrics':pin(EP/'editor/private-production-v3/caption_fit_metrics.json'),
      'video_properties':{k:stream[k] for k in ['codec_name','width','height','r_frame_rate','pix_fmt','nb_frames']},
      'ffmpeg':pin(ffmpeg) if ffmpeg.is_relative_to(EP) else {'path':str(ffmpeg),'sha256':sha(ffmpeg)},'extract_argv':argv,'extract_returncode':result.returncode,
      'points':ordered,'contact_sheets':sheets,'unique_frame_count':len(indices),'actual_visual_inspection':False,
      'decode_scope':'Video stream traversed for select extraction; chapter audio and final whole AV decode not claimed',
      'actual_listening':False,'continuous_playback':False,'final_concat_checked':False,'final_media_approved':False}
    dump(target/'evidence.json',report)
    print(json.dumps({'chapter':n,'video_sha256':video_sha,'unique_frames':len(indices),'sheets':len(sheets),'folder':str(target),'status':report['status']}))

if __name__=='__main__':main()
