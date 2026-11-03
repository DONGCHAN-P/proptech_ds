from pathlib import Path
import subprocess,json
from PIL import Image,ImageDraw
import numpy as np
P=Path(__file__).resolve().parents[2];Q=Path(__file__).parent/'actual';Q.mkdir(exist_ok=True)
ff='C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin/ffmpeg.exe'
frames=[2640,4950,19648,20448,10370,12003,12690,12694,22695,24030,24865,25589]
report=[];board=Image.new('RGB',(1740,12*130),'white');draw=ImageDraw.Draw(board)
for i,f in enumerate(frames):
 target=Q/('timeline_full_'+str(f)+'.png')
 subprocess.run([ff,'-v','error','-y','-ss',str(f/30),'-i',str(P/'outputs/readability-cta-v15/namyangju_readability_cta_full_v15.mp4'),'-frames:v','1',str(target)],check=True)
 im=Image.open(target).convert('RGB');crop=im.crop((80,759,1820,854));a=np.array(crop)
 blue=(a[:,:,2]>160)&(a[:,:,0]<110)&(a[:,:,1]<160)
 yy,xx=np.where(blue)
 report.append({'frame':f,'min_blue_y':int(yy.min()) if len(xx) else None,'max_blue_y':int(yy.max()) if len(xx) else None,'min_blue_x':int(xx.min()) if len(xx) else None,'max_blue_x':int(xx.max()) if len(xx) else None,'blue_touching_crop_edge':bool(np.any(blue[0]) or np.any(blue[-1]) or np.any(blue[:,0]) or np.any(blue[:,-1])),'blue_ink_absent_allowed_for_gray_unknown_only_case':len(xx)==0})
 board.paste(crop,(0,i*130+25));draw.text((5,i*130+5),'case '+str(i)+' frame '+str(f),fill='black')
board.save(Q/'timeline_12cases.png')
(Q/'timeline_12cases.json').write_text(json.dumps({'actual_frames':report,'note':'Blue ink edge test supplements direct glyph/stroke inspection; source font bbox audit has12cases'},indent=2),encoding='utf8')
print(json.dumps(report))
