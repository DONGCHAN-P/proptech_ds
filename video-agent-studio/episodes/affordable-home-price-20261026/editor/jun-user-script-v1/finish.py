"""Technical receipts, encoded preview evidence and a stream-copy review reel."""
import hashlib,json,os,re,subprocess,sys
from pathlib import Path
from PIL import Image,ImageChops
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build import HERE,EP,ROOT,OUT,PROJECT,read,sha,dump,write,PLAN,MANIFEST,CAPTIONS,CALC,BASE
FF=ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
PROBE=ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
CLI=Path('C:/Users/e2ken/AppData/Roaming/npm/node_modules/hyperframes/bin/hyperframes.mjs')
env=dict(os.environ,DO_NOT_TRACK='1',HYPERFRAMES_NO_UPDATE_CHECK='1',HYPERFRAMES_NO_AUTO_INSTALL='1')
def run(args,log=None):
    p=subprocess.run([str(x) for x in args],capture_output=True,env=env)
    if log:write(log,(p.stdout+p.stderr).decode('utf8','replace'))
    return p
def frame(src,t,dst):
    dst.parent.mkdir(parents=True,exist_ok=True)
    p=run([FF,'-v','error','-y','-ss',str(t),'-i',src,'-frames:v','1',dst]);assert p.returncode==0 and dst.is_file(),p.stderr
    return dst
def header(p):
    im=Image.open(p).convert('RGB');result={}
    for name,(x0,x1) in {'brand':(80,450),'preview_status':(1400,1840)}.items():
        pts=[(x,y) for y in range(90) for x in range(x0,x1) if all(c<190 for c in im.getpixel((x,y)))]
        bbox=None if not pts else [min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts)+1,max(y for x,y in pts)+1]
        result[name]={'ink_bbox':bbox,'top_clearance_pass':bbox is not None and bbox[1]>=20}
    return result
def media(p):
    probe=run([PROBE,'-v','error','-show_format','-show_streams','-of','json',p]);assert probe.returncode==0
    d=json.loads(probe.stdout);dec=run([FF,'-v','error','-i',p,'-f','null','-'],HERE/'checks'/f'{p.stem}_decode.log')
    pts=run([PROBE,'-v','error','-select_streams','v:0','-show_entries','frame=best_effort_timestamp_time','-of','csv=p=0',p])
    ts=[float(x.split(',')[0]) for x in pts.stdout.decode().splitlines() if re.match(r'^\d+\.\d+',x)]
    v=next(x for x in d['streams'] if x['codec_type']=='video')
    result={'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size,'duration_s':float(d['format']['duration']),'width':v['width'],'height':v['height'],'fps':v['r_frame_rate'],'time_base':v['time_base'],'codec':v['codec_name'],'pix_fmt':v['pix_fmt'],'audio_streams':sum(x['codec_type']=='audio' for x in d['streams']),'decode_returncode':dec.returncode,'decode_stderr_empty':not dec.stderr.strip(),'decoded_video_frames':len(ts),'pts_monotonic':all(a<b for a,b in zip(ts,ts[1:])),'pts_step_30fps':all(abs((b-a)-1/30)<.000002 for a,b in zip(ts,ts[1:]))}
    assert result['width']==1920 and result['height']==1080 and result['fps']=='30/1' and result['audio_streams']==0 and result['decode_returncode']==0 and result['pts_monotonic'] and result['pts_step_30fps'],result
    return result
def parse_cli(p):
    s=p.read_text(encoding='utf8',errors='replace');start=s.find('\n{\n');return json.JSONDecoder().raw_decode(s[start+1:])[0]
def main():
    current=[('S13','S13_preview_silent_v1.mp4',[1.6,4.6,9.5]),('S18_S19','S18_S19_preview_silent_v2.mp4',[2.2,6.7,10.7]),('S21','S21_preview_silent_v2.mp4',[1.7,6.2,11.5])]
    streams=[];headers={};pngs=[]
    for id,name,times in current:
        f=OUT/name;assert f.is_file(),f
        streams.append(media(f))
        frames=[frame(f,t,OUT/'encoded_frames'/f'{id}_{t:g}s.png') for t in times]
        pngs.append(frames);target=OUT/f'{id}_representative_v1.png';Image.open(frames[-1]).save(target)
        Image.open(frames[-1]).resize((640,360),Image.Resampling.LANCZOS).save(OUT/f'{id}_small_640x360.png')
        headers[id]=[{ 'time_s':t,'frame':str(p),'checks':header(p)} for t,p in zip(times,frames)]
    dump(OUT/'header_bounds_receipt.json',{'scope':'actual encoded pixels; top ink bounding boxes, not source coordinates','frames':headers})
    assert all(v['top_clearance_pass'] for h in headers.values() for s in h for v in s['checks'].values()),'Header fix failed: inspect header_bounds_receipt.json before concat'
    # Successful render checks are separate from the CLI's unwritable global history.
    checks={}
    for id,_,_ in current:
        log=HERE/'checks'/f'{id}_final_check.log';p=run(['node',CLI,'check',PROJECT/id,'--at','0,1.7,4.6,6.7,9.5','--json'],log)
        d=parse_cli(log);assert d['ok'] is True and not d.get('browserSkipped'),id
        checks[id]={'process_exit_code':p.returncode,'payload_ok':d['ok'],'layout_samples':d['layout']['samples'],'contrast_checked':d['contrast'].get('checked'),'global_history_write_warning':'EPERM' in log.read_text(encoding='utf8'),'log':str(log)}
    # Codec, time base, format and dimensions must match before stream copy.
    assert len({tuple(s[k] for k in ['codec','time_base','pix_fmt','width','height','fps']) for s in streams})==1
    concat_list=OUT/'concat_current.txt';write(concat_list,''.join("file '"+(OUT/n).as_posix()+"'\n" for _,n,_ in current))
    combined=OUT/'representative_preview_silent_v1.mp4';assert not combined.exists(),'Preserve existing combined preview; choose a new version'
    p=run([FF,'-v','error','-f','concat','-safe','0','-i',concat_list,'-c','copy','-movflags','+faststart',combined],HERE/'checks/concat.log');assert p.returncode==0
    cm=media(combined);assert abs(cm['duration_s']-35)<.04 and cm['decoded_video_frames']==1050
    boundaries=[]
    for t in [0,9.966667,10,10.033333,22.966667,23,23.033333,34.966667]:
        fp=frame(combined,t,OUT/'combined_boundaries'/f'{t:g}s.png');boundaries.append(str(fp))
    sheet=Image.new('RGB',(1920,1080),'#f6f4ef')
    for col,frames in enumerate(pngs):
        for row,f in enumerate(frames):sheet.paste(Image.open(f).resize((640,360),Image.Resampling.LANCZOS),(col*640,row*360))
    sheet.save(OUT/'contact_sheet.png')
    final=Image.new('RGB',(1920,360),'#f6f4ef')
    for i,(id,_,_) in enumerate(current):final.paste(Image.open(OUT/f'{id}_small_640x360.png'),(i*640,0))
    final.save(OUT/'three_representatives_small.png')
    baseline=BASE.parent/'renders/measured-jun-v1/housing_choice_jun_v1.mp4'
    bframes=[]
    for t in [270,320,400]:bframes.append(frame(baseline,t,OUT/'style_reference'/f'public_Jun_{t}s.png'))
    bs=Image.new('RGB',(1920,360),'#f6f4ef')
    for i,p in enumerate(bframes):bs.paste(Image.open(p).resize((640,360),Image.Resampling.LANCZOS),(i*640,0))
    bs.save(OUT/'style_reference/public_Jun_contact.png')
    dump(OUT/'qa_receipt.json',{'status':'technical_checks_passed_visual_review_required','media':streams+[cm],'cli_checks':checks,'header_bounds_receipt':str(OUT/'header_bounds_receipt.json'),'combined_boundary_frames':boundaries,'source_caption_display_lines':'verbatim from narration/caption_plan.json; selected cues for preview only','actual_listening':False,'continuous_playback':False,'audio_sync_verified':False,'native_browser_custom_audit':'launch timed out; CLI browser checks completed instead','independent_QA':'parent Euler agent owns separate review; not claimed here'})
    dump(HERE/'current_deliverables.json',{'clips':[str(OUT/n) for _,n,_ in current],'combined':str(combined),'pngs':[str(OUT/f'{id}_representative_v1.png') for id,_,_ in current],'contact_sheet':str(OUT/'contact_sheet.png')})
    print(json.dumps({'technical_receipt':str(OUT/'qa_receipt.json'),'combined_duration_s':cm['duration_s'],'header_checks':'passed','current_clips':[n for _,n,_ in current]}))
if __name__=='__main__':main()
