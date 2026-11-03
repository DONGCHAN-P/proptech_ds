"""Read completed final MP4; save independent frame/decode evidence in QA only."""
import hashlib,json,subprocess,math
from pathlib import Path
from datetime import datetime,timezone
from PIL import Image,ImageDraw,ImageFont
QA=Path(__file__).resolve().parent;EP=QA.parents[1];WORKSPACE=EP.parents[2]
SOURCE=EP/'outputs/private-production-v2';DEST=QA/'encoded-v6/final-v1'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
    assert not DEST.exists()
    receipt_path=EP/'editor/private-production-v2/render_receipt.json';receipt=read(receipt_path)
    video=Path(receipt['final_file']);assert video.is_file() and sha(video)==receipt['final_sha256']
    edl=read(SOURCE/'assembly_edl.json');plan=read(SOURCE/'render_plan.json');shots=read(SOURCE/'snapshot_times.json')['samples']
    provision=read(EP/'director/two-episode-production-v1/ffmpeg_receipt.json');ffmpeg=WORKSPACE/provision['binary'];assert sha(ffmpeg)==provision['binary_sha256']
    DEST.mkdir(parents=True);frames=DEST/'frames';frames.mkdir()
    points=[]
    for shot in shots:
        ch=next(x for x in plan['chapters'] if x['chapter']==shot['chapter']);scene=next(x for x in ch['scenes'] if x['scene_id']==shot['scene_id'])
        for role,seconds in [('representative',shot['representative_s']),('boundary_after_start',shot['after_start_s']),('boundary_before_end',shot['before_end_s']),('boundary_before_start',scene['start_s']-1/30),('boundary_after_end',scene['end_s']+1/30)]:
            local_frame=max(0,min(round(ch['total_seconds']*30)-1,round(seconds*30)));local=local_frame/30
            offset=next(x['global_offset_s'] for x in edl['offset_map'] if x['chapter']==shot['chapter'] and x['local_start_s']<=local<x['local_end_s'])
            points.append(dict(chapter=shot['chapter'],scene_id=shot['scene_id'],role=role,local_frame=local_frame,local_time_s=local,global_frame=round((local+offset)*30)))
    for segment in edl['segments'][1:]:
        for delta,role in [(-1,'join_before'),(1,'join_after')]:points.append(dict(scene_id=segment['id'],role=role,global_frame=round(segment['global_start_s']*30)+delta))
    for segid in ['clean_brand_intro','clean_brand_outro']:
        s=next(x for x in edl['segments'] if x['id']==segid);points.append(dict(scene_id=segid,role='brand_midpoint',global_frame=round((s['global_start_s']+s['global_end_s'])/2*30)))
    last=plan['chapters'][-1];offset=next(x['global_offset_s'] for x in edl['offset_map'] if x['chapter']==10);speech=offset+last['last_speech_end_s']
    for delta in [-.1,.05,1.5,2.95]:points.append(dict(chapter=10,scene_id='last_speech_CTA_hold',role=f'last_speech_offset_{delta}',global_frame=round((speech+delta)*30)))
    points.extend([dict(scene_id='final_edge',role='final_last_frame',global_frame=round(edl['total_seconds']*30)-1),dict(chapter=1,scene_id='s3',role='final_global_44s_regression',global_frame=1320)])
    indices=sorted({x['global_frame'] for x in points});index_map={n:i for i,n in enumerate(indices)}
    select='+'.join(f'eq(n\\,{n})' for n in indices)
    argv=[str(ffmpeg),'-v','error','-nostdin','-threads','2','-i',str(video),'-an','-vf','select='+select,'-fps_mode','vfr','-start_number','0','-y',str(frames/'%05d.png')]
    result=subprocess.run(argv,capture_output=True,text=True,encoding='utf-8',errors='replace');(DEST/'extract.log').write_text(result.stderr,encoding='utf-8');assert result.returncode==0 and not result.stderr.strip(),result.stderr
    assert len(list(frames.glob('*.png')))==len(indices)
    for row in points:
        f=frames/f'{index_map[row["global_frame"]]:05d}.png';row.update(global_time_s=row['global_frame']/30,file=str(f.relative_to(QA)),sha256=sha(f))
    sheets=DEST/'sheets';sheets.mkdir();font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19);sheet_rows=[]
    for ch in range(1,11):
        rows=[x for x in points if x.get('chapter')==ch and x['role']=='representative'];canvas=Image.new('RGB',(1920,math.ceil(len(rows)/2)*568),'white');draw=ImageDraw.Draw(canvas)
        for i,row in enumerate(rows):
            x=(i%2)*960;y=(i//2)*568;draw.text((x+8,y+4),f'ch{ch:02}/{row["scene_id"]} final t={row["global_time_s"]:.6f}',font=font,fill='black')
            with Image.open(QA/row['file']) as im:canvas.paste(im.resize((960,540),Image.Resampling.LANCZOS),(x,y+28))
        target=sheets/f'ch{ch:02}_representatives.jpg';canvas.save(target,quality=95);sheet_rows.append(dict(kind='representatives',chapter=ch,file=str(target.relative_to(QA)),frames=len(rows),scale=.5))
    for ch in range(7,11):
        for scene in next(x for x in plan['chapters'] if x['chapter']==ch)['scenes']:
            sid=scene['scene_id'];canvas=Image.new('RGB',(1920,1136),'white');draw=ImageDraw.Draw(canvas)
            for i,role in enumerate(['boundary_before_start','boundary_after_start','boundary_before_end','boundary_after_end']):
                row=next(x for x in points if x.get('chapter')==ch and x['scene_id']==sid and x['role']==role);x=(i%2)*960;y=(i//2)*568;draw.text((x+8,y+4),f'ch{ch:02}/{sid} {role} t={row["global_time_s"]:.3f}',font=font,fill='black')
                with Image.open(QA/row['file']) as im:canvas.paste(im.resize((960,540),Image.Resampling.LANCZOS),(x,y+28))
            target=sheets/f'ch{ch:02}_{sid}_boundaries.jpg';canvas.save(target,quality=95);sheet_rows.append(dict(kind='boundaries',chapter=ch,scene_id=sid,file=str(target.relative_to(QA)),frames=4,scale=.5))
    decode_argv=[str(ffmpeg),'-v','error','-nostdin','-threads','2','-i',str(video),'-map','0:v:0','-map','0:a:0','-f','null','-']
    result=subprocess.run(decode_argv,capture_output=True,text=True,encoding='utf-8',errors='replace');(DEST/'full_decode.log').write_text(result.stderr,encoding='utf-8');assert result.returncode==0 and not result.stderr.strip(),result.stderr
    assert sha(video)==receipt['final_sha256']
    report=dict(status='final_frames_extracted_full_decode_pass_visual_review_pending',created_at=datetime.now(timezone.utc).isoformat(),script_sha256=plan['script_sha256'],video=str(video),video_sha256=sha(video),render_receipt_sha256=sha(receipt_path),EDL_sha256=sha(SOURCE/'assembly_edl.json'),subtitles_sha256=sha(Path(receipt['captions_file'])),scene_count=len(shots),unique_frame_count=len(indices),sample_records=len(points),samples=points,sheets=sheet_rows,last_speech_global_s=speech,outro_start_s=next(x['global_start_s'] for x in edl['segments'] if x['id']=='clean_brand_outro'),extract_argv=argv,independent_full_decode_argv=decode_argv,independent_full_decode_returncode=result.returncode,decode_stderr='',ffmpeg_sha256=sha(ffmpeg),code_sha256=sha(Path(__file__)),actual_listening=False,continuous_playback=False,actual_visual_inspection=False)
    write(DEST/'input_and_frames.json',report);print(json.dumps(dict(manifest=str(DEST/'input_and_frames.json'),scenes=len(shots),unique_frames=len(indices),decode_returncode=result.returncode)),flush=True)
if __name__=='__main__':main()
