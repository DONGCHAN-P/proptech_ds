"""Extract only completed chapter 1-3 encoded-video QA evidence into the QA folder."""
import hashlib,json,subprocess
from datetime import datetime,timezone
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

QA=Path(__file__).resolve().parent
EP=QA.parents[1]
WORKSPACE=EP.parents[2]
SOURCE=EP/'outputs/private-production-v2'
DEST=QA/'encoded-v6/ch01-03-v1'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    assert not DEST.exists(),'Preserve existing evidence; choose a new version'
    plan=read(SOURCE/'render_plan.json')
    shots=read(SOURCE/'snapshot_times.json')['samples']
    edl=read(SOURCE/'assembly_edl.json')
    provision=read(EP/'director/two-episode-production-v1/ffmpeg_receipt.json')
    ffmpeg=WORKSPACE/provision['binary']
    assert sha(ffmpeg)==provision['binary_sha256']
    DEST.mkdir(parents=True)
    chapters=[];samples=[];scenes=[]
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
    for number in [1,2,3]:
        video=SOURCE/f'renders/measured-v6/ch{number:02}.mp4'
        receipt_path=video.with_suffix('.receipt.json')
        receipt=read(receipt_path)
        assert video.is_file() and sha(video)==receipt['output_sha256']
        assert receipt['reused_completed_render'] and sha(Path(receipt['reuse_source']))==receipt['output_sha256']
        chapter=next(x for x in plan['chapters'] if x['chapter']==number)
        video_stream=next(x for x in receipt['ffprobe']['streams'] if x['codec_type']=='video')
        assert video_stream['r_frame_rate']=='30/1'
        last_frame=int(video_stream['nb_frames'])-1
        timing=read(SOURCE/f'ch{number:02}/timing.json')
        points=[]
        for shot in [x for x in shots if x['chapter']==number]:
            scene=next(x for x in chapter['scenes'] if x['scene_id']==shot['scene_id'])
            for role,seconds in [('representative',shot['representative_s']),
                ('boundary_after_start',shot['after_start_s']),('boundary_before_end',shot['before_end_s']),
                ('boundary_before_start',scene['start_s']-1/30),('boundary_after_end',scene['end_s']+1/30)]:
                points.append(dict(scene_id=shot['scene_id'],role=role,requested_time_s=seconds,
                    local_frame=max(0,min(last_frame,round(seconds*30)))))
            scenes.append(dict(chapter=number,**scene))
        points.extend([dict(scene_id='chapter_edge',role='file_first_frame',requested_time_s=0,local_frame=0),
                       dict(scene_id='chapter_edge',role='file_last_frame',requested_time_s=last_frame/30,local_frame=last_frame)])
        if number in [2,3]:points.append(dict(scene_id='chapter_card',role='chapter_card',requested_time_s=1.5,local_frame=45))
        if number==1:points.append(dict(scene_id='s3',role='first44s_regression',requested_time_s=44.,local_frame=1320))
        indices=sorted({x['local_frame'] for x in points})
        folder=DEST/f'ch{number:02}';folder.mkdir()
        select='+'.join(f'eq(n\\,{n})' for n in indices)
        argv=[str(ffmpeg),'-v','error','-nostdin','-threads','2','-i',str(video),'-an',
              '-vf','select='+select,'-fps_mode','vfr','-start_number','0','-y',str(folder/'%05d.png')]
        result=subprocess.run(argv,capture_output=True,text=True,encoding='utf-8',errors='replace')
        (folder/'extract.log').write_text(result.stderr,encoding='utf-8')
        assert result.returncode==0 and not result.stderr.strip(),result.stderr
        assert len(list(folder.glob('*.png')))==len(indices)
        for row in points:
            frame=row['local_frame'];file=folder/f'{indices.index(frame):05d}.png';assert file.is_file()
            local=frame/30
            offset=next(x['global_offset_s'] for x in edl['offset_map'] if x['chapter']==number and x['local_start_s']<=local<x['local_end_s'])
            active=[x for x in timing['cues'] if x['start_s']<=local<=x['end_s']]
            samples.append(dict(chapter=number,**row,sample_time_s=local,file=str(file.relative_to(QA)),
                sha256=sha(file),source_MP4_sha256=receipt['output_sha256'],
                expected_cue_ids=[x['id'] for x in active],expected_caption_text=' '.join(x['text'] for x in active),
                planned_final_global_frame=round((local+offset)*30),planned_final_global_time_s=round((local+offset)*30)/30))
        chapters.append(dict(chapter=number,file=str(video),sha256=sha(video),bytes=video.stat().st_size,
            receipt_sha256=sha(receipt_path),reused_MP4_SHA_matches_v5=True,input_fingerprint_count=len(receipt['input_file_sha256']),
            video_properties_from_producer_receipt={k:video_stream[k] for k in ['codec_name','width','height','r_frame_rate','pix_fmt','nb_frames']},
            video_stream_selected_frame_extraction_returncode=result.returncode,full_audio_video_decode_check_performed=False,
            extract_argv=argv,unique_PNGs=len(indices)))
        print(json.dumps(dict(chapter=number,unique_encoded_frames=len(indices),scene_count=len(chapter['scenes']))),flush=True)
    sheets=DEST/'boundary_sheets';sheets.mkdir()
    for scene in scenes:
        ch=scene['chapter'];sid=scene['scene_id']
        roles=['boundary_before_start','boundary_after_start','boundary_before_end','boundary_after_end']
        sheet=Image.new('RGB',(1920,1120),'white');draw=ImageDraw.Draw(sheet)
        for i,role in enumerate(roles):
            row=next(x for x in samples if x['chapter']==ch and x['scene_id']==sid and x['role']==role)
            x=(i%2)*960;y=(i//2)*560
            draw.text((x+8,y+5),f'ch{ch:02}/{sid} {role}  t={row["sample_time_s"]:.6f}  n={row["local_frame"]}',font=font,fill='black')
            with Image.open(QA/row['file']) as image:sheet.paste(image.resize((960,540),Image.Resampling.LANCZOS),(x,y+20))
        target=sheets/f'ch{ch:02}_{sid}.jpg';sheet.save(target,quality=95)
        scene['boundary_sheet']=str(target.relative_to(QA));scene['boundary_sheet_scale']=.5
    report=dict(status='encoded_frames_extracted_visual_inspection_pending',created_at=datetime.now(timezone.utc).isoformat(),
        script_sha256=plan['script_sha256'],plan_sha256=sha(SOURCE/'render_plan.json'),
        snapshot_times_sha256=sha(SOURCE/'snapshot_times.json'),EDL_sha256=sha(SOURCE/'assembly_edl.json'),
        ffmpeg_sha256=sha(ffmpeg),extractor_sha256=sha(Path(__file__)),chapters=chapters,scenes=scenes,samples=samples,
        scene_count=len(scenes),unique_frame_count=sum(x['unique_PNGs'] for x in chapters),sample_records=len(samples),
        actual_visual_inspection=False,actual_listening=False,continuous_playback=False,final_concat_checked=False)
    write(DEST/'input_and_frames.json',report)
    print(json.dumps(dict(output=str(DEST),scene_count=len(scenes),unique_frames=report['unique_frame_count'],sample_records=len(samples))),flush=True)

if __name__=='__main__':main()
