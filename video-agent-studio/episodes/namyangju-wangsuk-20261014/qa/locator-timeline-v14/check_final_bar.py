import json, subprocess
from pathlib import Path
import numpy as np
p=Path(__file__).resolve().parents[2]
ff='C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin/ffmpeg.exe'
v=p/'outputs/locator-timeline-v14/namyangju_locator_timeline_full_v14.mp4'
r=subprocess.Popen([ff,'-v','error','-i',str(v),'-vf','crop=1600:2:150:930,scale=160:1,format=gray','-f','rawvideo','-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
n=0;bad=[]
while True:
 b=r.stdout.read(160)
 if not b: break
 assert len(b)==160
 if 45<=n<917 or 1067<=n<27353:
  if float(np.frombuffer(b,dtype=np.uint8).mean())<250:bad.append(n)
 n+=1
assert r.wait()==0,r.stderr.read()
out={'decoded_frames':n,'failed_frames':bad,'roi_xywh':[150,930,1600,2],'method':'every encoded frame white bar upper interior mean >=250/255; not text OCR'}
(Path(__file__).parent/'final_corrected_actual/caption_roi.json').write_text(json.dumps(out),encoding='utf8')
print(json.dumps(out))
