"""Current Jun MP4 evidence: each scene, both sides of joins, longest captions, silent hold.

PNG extraction is not continuous viewing or listening. Main owns final dual media review.
"""
import argparse,json,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build import HERE,EP,ROOT,OUT,read,sha,dump,resolve
def main():
    p=argparse.ArgumentParser();p.add_argument('--extract',action='store_true');args=p.parse_args()
    edl=read(OUT/'assembly_edl.json');plan=read(OUT/'render_plan.json');shots=read(OUT/'snapshot_times.json')['samples'];rows=[]
    def add(ch,scene,role,local):
        local=round(local*30)/30
        off=next(o['global_offset_s'] for o in edl['offset_map'] if o['chapter']==ch and o['local_start_s']<=local<o['local_end_s'])
        frame=round((local+off)*30)
        rows.append({'chapter':ch,'scene_id':scene,'role':role,'local_frame':round(local*30),'global_frame':frame,'global_time_s':frame/30})
    for s in shots:
        for role,key in [('representative','representative_s'),('boundary_after_start','after_start_s'),('boundary_before_end','before_end_s')]:add(s['chapter'],s['scene_id'],role,s[key])
    for ch in plan['chapters']:
        t=read(OUT/ch['project']/'timing.json')
        for c in sorted(t['cues'],key=lambda c:max(len(x) for x in c.get('display_lines',[c['text']])),reverse=True)[:2]:
            add(ch['chapter'],c['id'],'longest_caption',(c['start_s']+c['end_s'])/2)
    for s in edl['segments'][1:]:
        frame=round(s['global_start_s']*30)
        for off,role in [(-1,'join_before'),(0,'join_at'),(1,'join_after')]:rows.append({'scene_id':s['id'],'role':role,'global_frame':frame+off,'global_time_s':(frame+off)/30})
    for t in [.05,1.5,2.95]:
        frame=round((edl['actual_last_speech_global_s']+t)*30)
        rows.append({'scene_id':'final_CTA_hold','role':f'after_last_speech_{t}s','global_frame':frame,'global_time_s':frame/30})
    frames=sorted({r['global_frame'] for r in rows});index={f:i for i,f in enumerate(frames)}
    dest=OUT/'renders/measured-jun-v1/encoded-evidence';dest.mkdir(parents=True,exist_ok=True)
    for r in rows:r['file']=(dest/f'{index[r["global_frame"]]:05d}.png').relative_to(OUT).as_posix()
    report={'status':'frame_plan_ready','fps':30,'script_sha256':plan['script_sha256'],'caption_timing_sha256':plan['caption_timing_sha256'],'EDL_sha256':sha(OUT/'assembly_edl.json'),'samples':rows,'unique_frame_count':len(frames),'actual_frame_inspection':False,'actual_listening':False,'continuous_playback':False}
    dump(OUT/'encoded_frame_plan.json',report)
    if not args.extract:print(json.dumps({'status':report['status'],'frames':len(frames)}));return
    receipt=read(HERE/'render_receipt.json');video=Path(receipt['final_file']);assert sha(video)==receipt['final_sha256']
    provision=read(EP/'director/two-episode-production-v1/ffmpeg_receipt.json');ff=ROOT/provision['binary'];assert sha(ff)==provision['binary_sha256']
    select='+'.join(f'eq(n\\,{f})' for f in frames)
    argv=[str(ff),'-v','error','-nostdin','-threads','2','-i',str(video),'-an','-vf','select='+select,'-fps_mode','vfr','-start_number','0','-n',str(dest/'%05d.png')]
    with (dest/'extract.log').open('w',encoding='utf8') as log:r=subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT)
    assert r.returncode==0 and not (dest/'extract.log').read_text(encoding='utf8').strip(),'Frame extraction failed'
    from PIL import Image,ImageDraw,ImageFont
    for r in rows:
        file=OUT/r['file'];assert file.exists() and file.stat().st_size
        with Image.open(file) as im:assert im.size==(1920,1080)
        r['sha256']=sha(file)
    representatives=[r for r in rows if r['role']=='representative'];sheets=[]
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
    for start in range(0,len(representatives),10):
        sheet=Image.new('RGB',(1280,1950),'white');draw=ImageDraw.Draw(sheet)
        for slot,r in enumerate(representatives[start:start+10]):
            x=(slot%2)*640;y=(slot//2)*390
            with Image.open(OUT/r['file']) as im:sheet.paste(im.convert('RGB').resize((640,360)),(x,y))
            draw.text((x+8,y+363),f'CH{r["chapter"]:02d} / {r["scene_id"]} / {r["global_time_s"]:.3f}s',font=font,fill='#102333')
        file=dest/f'contact_{start//10+1:02d}.jpg';sheet.save(file,quality=94);sheets.append({'file':file.relative_to(OUT).as_posix(),'sha256':sha(file)})
    report.update(status='encoded_frames_extracted_review_pending',final_file=str(video),final_sha256=sha(video),extract_argv=argv,contact_sheets=sheets)
    dump(OUT/'encoded_frame_plan.json',report)
    print(json.dumps({'status':report['status'],'unique_frames':len(frames),'scenes':len(shots)}))
if __name__=='__main__':main()
