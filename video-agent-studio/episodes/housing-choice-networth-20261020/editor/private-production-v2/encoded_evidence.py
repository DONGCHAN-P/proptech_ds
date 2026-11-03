"""Prepare all 50 scene representative/boundary times; optionally extract final MP4 frames."""
import argparse,hashlib,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;EP=HERE.parents[1];ROOT=EP.parents[2]
OUT=EP/'outputs/private-production-v2';DEST=OUT/'renders/measured-v6'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,r):p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--extract',action='store_true');args=parser.parse_args()
    edl=read(OUT/'assembly_edl.json');plan=read(OUT/'render_plan.json');shots=read(OUT/'snapshot_times.json')['samples']
    evidence=[]
    for shot in shots:
        for role,key in [('representative','representative_s'),('boundary_after_start','after_start_s'),('boundary_before_end','before_end_s')]:
            local_frame=round(shot[key]*30);local=local_frame/30
            offset=next(o['global_offset_s'] for o in edl['offset_map'] if o['chapter']==shot['chapter'] and o['local_start_s']<=local<o['local_end_s'])
            frame=round((local+offset)*30)
            evidence.append({'chapter':shot['chapter'],'scene_id':shot['scene_id'],'role':role,'local_frame':local_frame,'global_frame':frame,'global_time_s':frame/30})
    for segment in edl['segments'][1:]:
        frame=round(segment['global_start_s']*30)
        for off,role in [(-1,'join_before'),(1,'join_after')]:
            evidence.append({'scene_id':segment['id'],'role':role,'global_frame':frame+off,'global_time_s':(frame+off)/30})
    targeted=read(EP/'outputs/private-production-v1/preview_fixes/handoff.json')['frames']+read(OUT/'preview_delta/handoff.json')['frames']
    for shot in targeted:
        local_frame=round(shot['time_s']*30);local=local_frame/30
        offset=next(o['global_offset_s'] for o in edl['offset_map'] if o['chapter']==shot['chapter'] and o['local_start_s']<=local<o['local_end_s'])
        frame=round((local+offset)*30)
        evidence.append({'chapter':shot['chapter'],'scene_id':shot['scene_id'],'role':'targeted_verified_cue','cue_id':shot['cue_id'],'cue_text':shot['cue_text'],'global_frame':frame,'global_time_s':frame/30})
    last=plan['chapters'][-1];offset=next(o['global_offset_s'] for o in edl['offset_map'] if o['chapter']==10)
    for off in [.05,1.5,2.95]:
        frame=round((offset+last['last_speech_end_s']+off)*30)
        evidence.append({'chapter':10,'scene_id':'final_CTA_hold','role':f'after_last_speech_{off}s','global_frame':frame,'global_time_s':frame/30})
    frames=sorted(set(r['global_frame'] for r in evidence));indices={f:i for i,f in enumerate(frames)}
    directory=DEST/'encoded-evidence';directory.mkdir(parents=True,exist_ok=True)
    for row in evidence:row['file']=str((directory/f'{indices[row["global_frame"]]:05d}.png').relative_to(OUT)).replace('\\','/')
    report={'status':'final_encoded_frame_plan_ready','script_sha256':plan['script_sha256'],'EDL_sha256':sha(OUT/'assembly_edl.json'),
            'fps':30,'duration_s':edl['total_seconds'],'scene_count':len(shots),'scene_samples':len(shots)*3,'unique_frame_count':len(frames),'samples':evidence,
            'actual_frame_inspection':False,'actual_listening':False,'continuous_playback':False}
    dump(OUT/'encoded_frame_plan.json',report)
    if not args.extract:print(json.dumps({k:v for k,v in report.items() if k!='samples'}));return
    receipt=read(HERE/'render_receipt.json');video=Path(receipt['final_file'])
    if receipt['final_sha256']!=sha(video):raise ValueError('Final MP4 SHA differs from technical receipt')
    provision=read(EP/'director/two-episode-production-v1/ffmpeg_receipt.json');ffmpeg=ROOT/provision['binary']
    if sha(ffmpeg)!=provision['binary_sha256']:raise ValueError('FFmpeg lock mismatch')
    select='+'.join(f'eq(n\\,{f})' for f in frames)
    argv=[str(ffmpeg),'-v','error','-nostdin','-threads','2','-i',str(video),'-an','-vf','select='+select,'-fps_mode','vfr','-start_number','0','-y',str(directory/'%05d.png')]
    result=subprocess.run(argv,capture_output=True,text=True,encoding='utf8',errors='replace')
    (directory/'extract.log').write_text(result.stderr,encoding='utf8')
    if result.returncode or result.stderr.strip():raise ValueError('Final frame extraction failed')
    for row in evidence:
        p=OUT/row['file']
        if not p.is_file() or not p.stat().st_size:raise ValueError('Missing requested final frame')
        row['sha256']=sha(p)
    report.update(status='final_encoded_frames_extracted_independent_review_pending',final_file=str(video),final_sha256=sha(video),ffmpeg_sha256=sha(ffmpeg),extract_argv=argv)
    from PIL import Image,ImageDraw,ImageFont
    representatives=[r for r in evidence if r['role']=='representative']
    report['contact_sheets']=[]
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
    for page,start in enumerate(range(0,len(representatives),10),1):
        sheet=Image.new('RGB',(1280,1950),'#ffffff');draw=ImageDraw.Draw(sheet)
        for slot,row in enumerate(representatives[start:start+10]):
            x=(slot%2)*640;y=(slot//2)*390
            with Image.open(OUT/row['file']) as frame:sheet.paste(frame.convert('RGB').resize((640,360)),(x,y))
            label=f'CH{row["chapter"]:02d} / {row["scene_id"]} / {row["global_time_s"]:.3f}s'
            draw.text((x+8,y+363),label,font=font,fill='#102333')
        target=directory/f'contact_{page:02d}.jpg';sheet.save(target,quality=94)
        report['contact_sheets'].append({'file':str(target.relative_to(OUT)).replace('\\','/'),'sha256':sha(target),'scope':'overview only; full-resolution PNGs retained for glyph and numerical inspection'})
    report['evidence_script_sha256']=sha(Path(__file__))
    dump(OUT/'encoded_frame_plan.json',report)
    print(json.dumps({'status':report['status'],'scene_count':len(shots),'unique_frame_count':len(frames),'manifest':str(OUT/'encoded_frame_plan.json')}))
if __name__=='__main__':main()
