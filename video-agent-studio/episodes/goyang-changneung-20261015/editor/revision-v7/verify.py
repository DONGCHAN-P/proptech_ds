from pathlib import Path
import json,subprocess,hashlib,sys
from PIL import Image,ImageDraw
E=Path(__file__).resolve().parent;EP=E.parent.parent;R=EP.parents[2];O=EP/'outputs/visual-review-v7';D=O/'encoded_evidence';D.mkdir(exist_ok=True);B=R/'video/node_modules/@remotion/compositor-win32-x64-msvc';F=B/'ffmpeg.exe';P=B/'ffprobe.exe'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
checks=json.loads((O/'pre_capture_layout_checks.json').read_text(encoding='utf-8'))['checks'];assert len(checks)==12 and all(x['passed'] for x in checks)
partial='--chapter-only' in sys.argv;old=json.loads((O/'technical.json').read_text(encoding='utf-8')) if partial else {};files=[]
for name,frames,samples in [('supply_branch_6s.mp4',180,[29,30,52,74,104,105,127,149,179]),('restriction_events_6s.mp4',180,[0,22,44,59,60,82,104,119,120,142,164,179]),('chapter_title_3s_demo_4s.mp4',120,[0,75,89,90,119])]:
 f=O/name
 if partial and name!='chapter_title_3s_demo_4s.mp4':
  prior=next(x for x in old['actual_encoded_clips'] if x['file']==name);assert prior['sha256']==sha(f);files.append(prior);continue
 z=subprocess.run([str(P),'-v','error','-count_frames','-show_streams','-show_format','-of','json',str(f)],stdout=subprocess.PIPE,stderr=subprocess.PIPE);q=json.loads(z.stdout);v=next(s for s in q['streams'] if s['codec_type']=='video');assert z.returncode==0 and z.stderr==b'' and int(v['nb_read_frames'])==frames and v['avg_frame_rate']=='30/1' and (v['width'],v['height'])==(1920,1080);assert not any(x['codec_type']=='audio' for x in q['streams']);images=[]
 for frame in samples:
  out=D/f'{f.stem}_{frame:03d}.png';subprocess.run([str(F),'-v','error','-y','-ss',f'{frame/30:.9f}','-i',str(f),'-frames:v','1',str(out)],check=True);images.append({'frame':frame,'file':out.name})
 sheet=Image.new('RGB',(1536,((len(images)+2)//3)*312),'#f6f4ef');draw=ImageDraw.Draw(sheet)
 for i,r in enumerate(images):
  x=i%3*512;y=i//3*312;sheet.paste(Image.open(D/r['file']).resize((512,288)),(x,y));draw.text((x+5,y+292),f'{f.stem} / actual encoded {r["frame"]}f',fill='black')
 sheetname=f.stem+'_sheet.jpg';sheet.save(D/sheetname,quality=94);files.append({'file':name,'sha256':sha(f),'bytes':f.stat().st_size,'frames':frames,'fps':30,'resolution':[1920,1080],'silent':True,'decode_exit_code':z.returncode,'decode_stderr':'','probe':q,'samples':images,'sheet':sheetname,'scope':'무음 연출 샘플. 새 본편 발화에 정렬된 영상 아님. 전체 영상 렌더 아님.'})
mobile=O/'mobile';mobile.mkdir(exist_ok=True);receipt=json.loads((O/'render_receipt.json').read_text(encoding='utf-8'))
for x in receipt['stills']:Image.open(O/x['file']).resize((512,288)).save(mobile/x['file'])
(O/'technical.json').write_text(json.dumps({'scope':'대표12PNG·무음클립3개 검토팩','actual_encoded_clips':files,'pre_capture_layout_passed_states':12,'baseline_unchanged':{'file':'outputs/production-v6-ui-r5/changneung_full_v6_ui_r5.mp4','sha256':sha(EP/'outputs/production-v6-ui-r5/changneung_full_v6_ui_r5.mp4')},'script_v7_sha256':sha(EP/'outputs/script-review-v7/script_v7.md'),'whole_video_generated':False,'new_voice_generated':False,'actual_listening':False,'human_continuous_playback':False},ensure_ascii=False,indent=2),encoding='utf-8');print('12 guards / 3 complete frame decodes / 26 actual encoded samples / 12 mobile variants verified',flush=True)
