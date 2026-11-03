"""Plan encoded evidence without rendering; --extract reads only a decoded final MP4."""
import argparse,json,math,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True;sys.path.insert(0,str(Path(__file__).resolve().parent))
from render_pipeline import HERE,EP,ROOT,OUT,DEFAULT_RUN,read,sha,dump,dest_of,tools

def frame_plan(run):
    edl=read(OUT/'assembly_edl.json');plan=read(OUT/'render_plan.json');shots=read(OUT/'snapshot_times.json')['samples'];captions=read(OUT/'global_captions.json')['cues'];bbox=read(HERE/'bbox_measured_v4.json');total=round(edl['total_seconds']*30);samples=[]
    assert len(shots)==45 and len(captions)==150 and len(edl['segments'])-1==12
    def add(frame,role,scene_id,chapter=None,local=None,cue_id=None):
        assert 0<=frame<total
        row={'chapter':chapter,'scene_id':scene_id,'global_frame':frame,'global_time_s':frame/30,'role':role}
        if local is not None:row['chapter_local_time_s']=local
        if cue_id:row['cue_id']=cue_id
        samples.append(row);return row
    def local(ch,t,role,sid,cue_id=None):
        local_frame=round(t*30);t=local_frame/30;o=next(o for o in edl['offset_map'] if o['chapter']==ch and o['local_start_s']-1e-9<=t<o['local_end_s']-1e-9)
        return add(round((t+o['global_offset_s'])*30),role,sid,ch,t,cue_id)
    for shot in shots:
        for role,key in [('representative','representative_s'),('scene_after_start','after_start_s'),('scene_before_end','before_end_s')]:local(shot['chapter'],shot[key],role,shot['scene_id'])
    for ch in plan['chapters'][1:]:local(ch['chapter'],ch['leading_silence_s']/2,'chapter_title',f'CH{ch["chapter"]:02}_TITLE')
    for seg in edl['segments'][1:]:
        frame=round(seg['global_start_s']*30)
        for offset,role in [(-1,'assembly_join_before'),(0,'assembly_join_first_after')]:add(frame+offset,role,seg['id'],seg.get('chapter'))
    add(0,'film_first_frame','opening_hook',1);add(total-1,'film_last_frame','clean_brand_outro')
    last=plan['chapters'][-1];offset=edl['offset_map'][-1]['global_offset_s']
    for delta in [.05,1.5,2.95]:add(round((offset+last['last_speech_end_s']+delta)*30),'CTA_caption_blank_hold','S044',10)
    # Actual measured source line widths choose the dense caption cases, not guessed strings.
    widths=[]
    for cue in captions:
        mid=(cue['start_s']+cue['end_s'])/2;chapter=next(c for c in bbox['chapters'] if c['chapter']==cue['chapter']);near=min(chapter['times'],key=lambda r:abs(r['time_s']-mid));assert abs(near['time_s']-mid)<1e-7
        widths.append((near['max_caption_width_px'],cue))
    widths.sort(key=lambda x:x[0],reverse=True)
    for width,cue in widths[:5]:
        row=local(cue['chapter'],(cue['start_s']+cue['end_s'])/2,'longest_caption_measured_width',cue['scene_id'],cue['id']);row.update(source_width_px=width,caption_text=cue['text'])
    targets=[c for c in captions if c['scene_id'] in ['S031','S040']]
    for cue in targets:local(cue['chapter'],(cue['start_s']+cue['end_s'])/2,'focus_fix_native_cue',cue['scene_id'],cue['id'])
    # Preserve exact post-brand first frame and pre-native blank caption checks.
    cut=round(edl['hook_cut_s']*30);add(cut+150,'brand_resume_S002_caption_blank','S002',1,cut/30)
    first=next(c for c in captions if c['scene_id']=='S002');local(1,first['start_s']-.07,'before_S002_native_caption_blank','S002')
    critical=[]
    for sid in ['S001','S008','S014','S016','S019','S024','S025','S028','S032','S034R']:
        row=next(r for r in samples if r['scene_id']==sid and r['role']=='representative');critical.append({**row,'review_role':'critical_'+sid})
    for cueid in ['C07_S031Q002','C07_S031Q003','C09_S040Q003','C09_S040Q004']:
        critical.append({**next(r for r in samples if r.get('cue_id')==cueid and r['role']=='focus_fix_native_cue'),'review_role':'critical_focus_'+cueid})
    critical.append({**next(r for r in samples if r['role']=='brand_resume_S002_caption_blank'),'review_role':'critical_brand_resume'})
    critical.append({**next(r for r in samples if r['role']=='longest_caption_measured_width'),'review_role':'critical_longest_caption'})
    assert len(critical)==16
    for row in critical:row.update(sample_role=row['role'],role=row['review_role'])
    frames=sorted({r['global_frame'] for r in samples});index={f:i for i,f in enumerate(frames)};directory=dest_of(run)/'encoded-evidence'
    for row in samples+critical:row['file']=(directory/f'{index[row["global_frame"]]:05}.png').relative_to(OUT).as_posix()
    return {'status':'encoded_frame_plan_ready_not_extracted','run_id':run,'script_sha256':plan['script_sha256'],'timing_sha256':edl['timing_sha256'],'EDL_sha256':sha(OUT/'assembly_edl.json'),'SRT_sha256':sha(OUT/'captions_measured.srt'),'fps':30,'duration_s':edl['total_seconds'],'total_video_frames':total,'scene_count':45,'native_caption_count':150,'assembly_joins':12,'unique_frame_count':len(frames),'samples':samples,'critical_frames':critical,'actual_frame_inspection':False,'actual_listening':False,'continuous_playback':False,'encoded_frame_files_exist':False}

def contacts(report,directory):
    from PIL import Image,ImageDraw,ImageFont
    reps=[r for r in report['samples'] if r['role']=='representative'];font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
    sheets=[]
    for page,start in enumerate(range(0,len(reps),10),1):
        group=reps[start:start+10];sheet=Image.new('RGB',(1280,390*math.ceil(len(group)/2)),'white');draw=ImageDraw.Draw(sheet)
        for i,row in enumerate(group):
            x=i%2*640;y=i//2*390
            with Image.open(OUT/row['file']) as im:sheet.paste(im.convert('RGB').resize((640,360)),(x,y))
            draw.text((x+8,y+363),f'CH{row["chapter"]:02} / {row["scene_id"]} / {row["global_time_s"]:.3f}s',font=font,fill='#173348')
        file=directory/f'contact_{page:02}.png';sheet.save(file);sheets.append({'file':file.relative_to(OUT).as_posix(),'sha256':sha(file),'role':'encoded_scene_contact_sheet'})
    sheet=Image.new('RGB',(1920,2160),'white');draw=ImageDraw.Draw(sheet);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16)
    for i,row in enumerate(reps):
        x=i%5*384;y=i//5*240
        with Image.open(OUT/row['file']) as im:sheet.paste(im.convert('RGB').resize((384,216)),(x,y))
        draw.text((x+4,y+218),f'CH{row["chapter"]:02}/{row["scene_id"]} {row["global_time_s"]:.2f}s',font=small,fill='#173348')
    file=directory/'contact_overview.png';sheet.save(file);return sheets,{'file':file.relative_to(OUT).as_posix(),'sha256':sha(file),'role':'45_scene_encoded_overview_only'}

def extract(report):
    receipt=read(HERE/'render_receipt.json');video=Path(receipt['final_file']);assert receipt['decode_returncode']==0 and receipt['status']=='rendered_technical_pass_independent_media_review_pending'
    assert sha(video)==receipt['final_sha256'] and receipt['captions_sha256']==report['SRT_sha256']
    assert receipt['expected_duration_s']==report['duration_s']
    dest=dest_of(report['run_id']);assert video.parent==dest.resolve()
    directory=dest/'encoded-evidence';directory.mkdir(parents=True,exist_ok=True);frames=sorted({r['global_frame'] for r in report['samples']})
    checkpoint=directory/'extraction_checkpoint.json';identity={'final_sha256':receipt['final_sha256'],'frames':frames}
    if checkpoint.exists():assert read(checkpoint)==identity,'Never overwrite evidence for a different film'
    else:dump(checkpoint,identity)
    _,_,ffmpeg,_=tools();selection='+'.join(f'eq(n\\,{frame})' for frame in frames)
    argv=[str(ffmpeg),'-v','error','-xerror','-nostdin','-threads','2','-i',str(video),'-an','-vf','select='+selection,'-fps_mode','vfr','-start_number','0','-y',str(directory/'%05d.png')]
    p=subprocess.run(argv,capture_output=True,text=True,encoding='utf8',errors='replace');(directory/'extract.log').write_text(p.stderr,encoding='utf8');assert p.returncode==0 and not p.stderr.strip(),'Encoded extraction failed'
    from PIL import Image
    for row in report['samples']+report['critical_frames']:
        file=OUT/row['file'];assert file.is_file() and file.stat().st_size
        with Image.open(file) as im:assert im.size==(1920,1080)
        row['sha256']=sha(file)
    sheets,overview=contacts(report,directory)
    report.update(status='final_encoded_frames_extracted_independent_media_review_pending',final_file=str(video),final_sha256=receipt['final_sha256'],render_receipt_sha256=sha(HERE/'render_receipt.json'),encoded_frame_files_exist=True,extract_argv=argv,extract_returncode=p.returncode,extract_log_sha256=sha(directory/'extract.log'),ffmpeg_sha256=sha(ffmpeg),contact_sheets=sheets,contact_overview=overview,evidence_script_sha256=sha(Path(__file__)))
    manifest={'status':'actual_encoded_frames_ready_for_review','final_file':str(video),'final_sha256':receipt['final_sha256'],'frames':report['critical_frames'],'contact_overview':overview,'scope':'16 fullres critical frames plus overview; all45 representatives, scene/chapter boundaries,12 assembly joins,longest captions,CTA in encoded_frame_plan.json. Sampled evidence is not continuous viewing/listening.'}
    dump(OUT/'encoded_critical_frames.json',manifest)
    images=[OUT/overview['file']]+[OUT/r['file'] for r in report['critical_frames']]
    dump(HERE/'encoded_review_image_list.json',list(dict.fromkeys(p.relative_to(ROOT).as_posix() for p in images)))
    return report

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-id',default=DEFAULT_RUN);parser.add_argument('--extract',action='store_true');args=parser.parse_args()
    if args.extract:
        report=read(OUT/'encoded_frame_plan.prepared.json');assert report['run_id']==args.run_id
        report=extract(report)
    else:
        report=frame_plan(args.run_id);dump(OUT/'encoded_frame_plan.prepared.json',report)
    dump(OUT/'encoded_frame_plan.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ['samples','critical_frames','extract_argv']},ensure_ascii=False))
if __name__=='__main__':main()
