from pathlib import Path
import argparse,json,subprocess,hashlib
P=Path(__file__).resolve().parent;E=P.parent.parent;O=E/'outputs/map-preview-v2';ap=argparse.ArgumentParser();ap.add_argument('--ffmpeg-bin',required=True);a=ap.parse_args();B=Path(a.ffmpeg_bin);F=str(B/'ffmpeg.exe');receipt=json.loads((O/'preview_receipt.json').read_text(encoding='utf-8'));assert receipt['preview_only'] and len(receipt['actual_data_frames'])==3
rows=['ffconcat version 1.0']
for x in receipt['actual_data_frames']:rows += ["file '"+(O/x['file']).resolve().as_posix()+"'",'option framerate 30','duration 2.000000000000']
rows += ["file '"+(O/receipt['actual_data_frames'][-1]['file']).resolve().as_posix()+"'",'option framerate 30'];listing=P/'style_preview.ffconcat';listing.write_text('\n'.join(rows)+'\n',encoding='utf-8');out=O/'style_preview_6s.mp4'
subprocess.run([F,'-v','error','-y','-f','concat','-safe','0','-i',str(listing),'-an','-vf','fps=30,format=yuv420p','-frames:v','180','-c:v','libx264','-preset','fast','-crf','18','-metadata:s:v:0','rotate=0','-movflags','+faststart',str(out)],check=True)
probe=json.loads(subprocess.check_output([str(B/'ffprobe.exe'),'-v','error','-show_streams','-show_format','-of','json',str(out)]));v=next(s for s in probe['streams'] if s['codec_type']=='video');assert (v['width'],v['height'],v['avg_frame_rate'],int(v['nb_frames']))==(1080,1920,'30/1',180);assert not any(s['codec_type']=='audio' for s in probe['streams']);subprocess.run([F,'-v','error','-i',str(out),'-f','null','-'],check=True)
(O/'technical_preview.json').write_text(json.dumps({'file':out.name,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'bytes':out.stat().st_size,'probe':probe,'decode_exit_code':0,'preview_only':True,'external_transmission_allowed':False,'full_video':False,'actual_listening':False,'continuous_playback':False},ensure_ascii=False,indent=2),encoding='utf-8');print('6초 로컬 시안만 출력 완료')

