from pathlib import Path
import subprocess,json,hashlib
EP=Path(__file__).resolve().parents[2];O=EP/'outputs/readability-cta-v15';FOLDER=Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin');F=str(FOLDER/'ffmpeg.exe');P=str(FOLDER/'ffprobe.exe');BASE=EP/'outputs/locator-timeline-v14/namyangju_locator_timeline_full_v14.mp4'
def run(args):subprocess.run([F,'-v','error','-y']+args,check=True)
for i in range(12):run(['-f','lavfi','-i','color=c=0xf6f4ef:s=1740x95:r=30','-i',str(O/f'timeline_bbox_case_{i}.png'),'-filter_complex','[1:v]crop=1740:95:80:759[t];[0:v][t]overlay=0:0','-frames:v','1',str(O/f'timeline_plate_{i}.png')])
detail=[(10290,10678,4),(10678,11026,5),(11026,11672,6),(11672,12003,4),(12003,12289,5),(12289,12694,6),(12694,13485,7),(13485,14104,4),(14104,14214,5),(14214,14533,6),(14533,14793,4),(14793,15126,5),(15126,15758,6)]
closing=[(22156,23234,8),(23234,23920,9),(23920,24487,9),(24487,25243,10),(25243,25936,11)]
reports=[]
for name,start,end,ranges in [('detail',8190,15758,detail),('outside',18648,21636,[(18648,19951,2),(19951,21636,3)]),('closing',21636,27353,closing)]:
 ids=sorted({k for a,b,k in ranges});inputs=['-ss',str(start/30),'-i',str(BASE)]
 for k in ids:inputs+=['-loop','1','-framerate','30','-i',str(O/f'timeline_plate_{k}.png')]
 filters=[];previous='0:v';counter=0
 for a,b,k in ranges:
  counter+=1;label=f'p{counter}';idx=ids.index(k)+1;filters.append(f'[{previous}][{idx}:v]overlay=80:759:enable=between(n\\,{a-start}\\,{b-start-1})[{label}]');previous=label
 if name=='closing':
  inputs+=['-loop','1','-framerate','30','-i',str(O/'source_closing_caption_24030.png')];idx=len(ids)+1;filters.append(f'[{idx}:v]crop=1920:920:0:0[school]');filters.append(f'[{previous}][school]overlay=0:0:enable=between(n\\,{23920-start}\\,{24487-start-1})[final]');previous='final'
 target=O/f'{name}_v15_video.mp4'
 run(inputs+['-filter_complex',';'.join(filters),'-map',f'[{previous}]','-an','-frames:v',str(end-start),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p',str(target)])
 probe=json.loads(subprocess.check_output([P,'-v','error','-show_streams','-of','json',str(target)]));assert int(probe['streams'][0]['nb_frames'])==end-start
 run(['-i',str(target),'-f','null','-'])
 reports.append({'file':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'frames':end-start,'original_frame_range':[start,end],'timeline_changed_ROI':[80,759,1740,95],'timeline_ranges_global':ranges,'school_changed_ROI':[0,0,1920,920] if name=='closing' else None,'school_range_global':[23920,24487] if name=='closing' else None,'whole_decode_passed':True});print(name+' patch/decode ready',flush=True)
(O/'patch_manifest_v15.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
