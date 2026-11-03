import pathlib,json,numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import gaussian_filter
EP=pathlib.Path(__file__).resolve().parents[1];ROOT=EP.parents[2]
folder=EP/'editor-v2/source_frames/monitor';keys=[];metrics=[]
def edge_line(g,axis,fixed_range,guess,sign):
 pts=[]
 for fixed in range(*fixed_range,8):
  center=round(guess(fixed));lo=center-18;hi=center+19
  if axis=='y': vals=np.diff(g[lo:hi,fixed]);vary=lo+int(np.argmax(vals*sign))+.5;pts.append([fixed,vary])
  else: vals=np.diff(g[fixed,lo:hi]);vary=lo+int(np.argmax(vals*sign))+.5;pts.append([fixed,vary])
 a=np.array(pts);fit=np.polyfit(a[:,0],a[:,1],1);res=np.abs(np.polyval(fit,a[:,0])-a[:,1]);keep=res<2
 fit=np.polyfit(a[keep,0],a[keep,1],1)
 return fit,float(np.max(np.abs(np.polyval(fit,a[keep,0])-a[keep,1])))
def intersect(horizontal,vertical):
 a,b=horizontal;c,d=vertical
 y=(a*d+b)/(1-a*c);return [c*y+d,y]
for p in sorted(folder.glob('*.png')):
 g=gaussian_filter(np.array(Image.open(p).convert('L'),dtype=float),.5)
 top,r1=edge_line(g,'y',(505,1085),lambda x:187-(x-459)*20/653,1)
 bottom,r2=edge_line(g,'y',(505,1085),lambda x:505+(x-457)*30/653,-1)
 left,r3=edge_line(g,'x',(220,480),lambda y:459,-1 if False else 1)
 right,r4=edge_line(g,'x',(220,500),lambda y:1110,-1)
 q=np.array([intersect(top,left),intersect(top,right),intersect(bottom,right),intersect(bottom,left)])
 center=q.mean(axis=0);q=q+(center-q)/np.linalg.norm(center-q,axis=1)[:,None]*.65
 t=int(p.stem)/100;quad=(q*1.5).round(3).tolist();keys.append({'time':t,'quad':quad})
 metrics.append({'time':t,'quad_source1280':q.round(3).tolist(),'edge_fit_max_error_source_px':max(r1,r2,r3,r4)})
 im=Image.open(p);draw=ImageDraw.Draw(im);draw.polygon([tuple(v) for v in q],outline='#00ffff',width=2);im.save(folder/f'{p.stem}_tracking.jpg')
track_path=ROOT/'video/src/data-insight-v2/tracking.json'
tracks=json.loads(track_path.read_text(encoding='utf8')) if track_path.exists() else {}
tracks['monitor']=keys;track_path.write_text(json.dumps(tracks,indent=2),encoding='utf8')
(EP/'editor-v2/monitor_tracking_measurement.json').write_text(json.dumps({'basis':'actual API source 1280x720 sampled frames; grayscale screen-to-bezel edge line fitting; inner inset0.65px','samples':metrics},indent=2),encoding='utf8')
print(json.dumps(metrics))
