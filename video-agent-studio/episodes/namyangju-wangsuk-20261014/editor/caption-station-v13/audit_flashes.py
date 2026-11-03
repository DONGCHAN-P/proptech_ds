from pathlib import Path
import subprocess,json,numpy as np,sys
EP=Path(__file__).resolve().parents[2];O=EP/'outputs/caption-station-v13';B=Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin');full='--full' in sys.argv;final='--final' in sys.argv or full;v=(O/('caption-station_v13_full.mp4' if full else 'caption-station_v13_front.mp4')) if final else EP/'outputs/minimal-v12/minimal_v12_front.mp4'
p=subprocess.Popen([str(B/'ffmpeg.exe'),'-v','error','-i',str(v),'-vf','crop=1760:650:80:190,scale=176:65,format=rgb24','-f','rawvideo','-'],stdout=subprocess.PIPE);frames=[]
while True:
 r=p.stdout.read(176*65*3)
 if len(r)!=176*65*3:break
 frames.append(np.frombuffer(r,dtype=np.uint8).reshape(65,176,3))
assert p.wait()==0 and len(frames)==(26720 if full else 15750)
a=np.stack(frames).astype(np.int16);delta=np.abs(a[1:]-a[:-1]).mean(axis=(1,2,3));cuts=(np.flatnonzero(delta>(1 if final else 6))+1).tolist();short=[];aba=[]
for x,y in zip(cuts,cuts[1:]):
 if y-x<=12:
  before=a[max(0,x-2)];middle=a[(x+y)//2];after=a[min(len(frames)-1,y+1)];enddiff=float(np.abs(before-after).mean());middiff=float(np.abs(before-middle).mean());short.append({'from_frame':x,'end_frame_exclusive':y,'length_frames':y-x,'before_after_difference':enddiff,'middle_difference':middiff})
  if enddiff<3 and middiff>6:aba.append(short[-1])
r={'video':str(v),'frames':len(frames),'roi':[80,190,1760,650],'cut_threshold_mean_rgb':1 if final else 6,'cut_frames':cuts,'short_segments_up_to_12frames':short,'aba_short_flashes':aba,'source_known_boundary_frames':[1898,2498,2588,2678,4942,4950,5484,5642,5892,6214,6977,7474,8190,8703,9202,9704,10290,10678,11026,11672,12003,12289,13485,14104,14214,14533,14793,15126]}
(O/('full_flash_audit.json' if full else 'final_flash_audit.json' if final else 'baseline_flash_audit.json')).write_text(json.dumps(r,indent=2),encoding='utf-8');np.save(EP/'editor/caption-station-v13/mean_frame_delta.npy',delta);print(json.dumps(r))
for n in sorted(set([4940,4941,4942,4943,4948,4949,4950,4951]+[z for q in short for z in [q['from_frame']-1,q['from_frame'],q['end_frame_exclusive']-1,q['end_frame_exclusive']]])):
 subprocess.run([str(B/'ffmpeg.exe'),'-v','error','-ss',str(n/30),'-i',str(v),'-frames:v','1','-y',str(O/f'{"final" if final else "baseline"}_boundary_{n}.png')],check=True)
