import pathlib,json,numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import gaussian_filter,median_filter
from scipy.stats import theilslopes
EP=pathlib.Path(__file__).resolve().parents[1];ROOT=EP.parents[2]
starts={'monitor':[[463,188],[1111,166],[1109,533],[456,507]],'laptop':[[667,287],[1103,290],[1079,556],[628,523]],'phone':[[817,145],[1007,165],[917,607],[726,573]]}
def line(p,q):
 a=(q[1]-p[1])/(q[0]-p[0]);return np.array([a,p[1]-a*p[0]])
def fit_edge(g,a,b,axis,sign,phone_top=False):
 if axis=='x':a=a[::-1];b=b[::-1]
 guess=line(a,b);ratios=np.r_[np.linspace(.13,.21,8),np.linspace(.80,.87,8)] if phone_top else np.linspace(.17,.83,38)
 pts=[]
 for k in ratios:
  fixed=int(a[0]+(b[0]-a[0])*k);center=round(np.polyval(guess,fixed));lo=center-10;hi=center+11
  vals=np.diff(g[lo:hi,fixed] if axis=='y' else g[fixed,lo:hi]);vary=lo+int(np.argmax(vals*sign))+.5
  pts.append([fixed,vary])
 pts=np.array(pts);robust=theilslopes(pts[:,1],pts[:,0]);co=[robust.slope,float(np.median(pts[:,1]-robust.slope*pts[:,0]))];res=np.abs(np.polyval(co,pts[:,0])-pts[:,1]);keep=res<2.5
 if keep.sum()<6:raise ValueError('Insufficient screen edge points')
 co=np.polyfit(pts[keep,0],pts[keep,1],1);r=float(np.max(np.abs(np.polyval(co,pts[keep,0])-pts[keep,1])))
 return co,r
def cross(h,v):
 a,b=h;c,d=v;y=(a*d+b)/(1-a*c);return [c*y+d,y]
tracks={};report={}
for name,start in starts.items():
 folder=EP/'editor-v2/source_frames'/name/'all';prev=np.array(start,dtype=float);quads=[];residuals=[]
 for i,p in enumerate(sorted(folder.glob('*.png'))):
  g=gaussian_filter(np.array(Image.open(p).convert('L'),dtype=float),.5)
  tl,tr,br,bl=prev
  top,r1=fit_edge(g,tl,tr,'y',1,name=='phone');bottom,r2=fit_edge(g,bl,br,'y',-1)
  try:left,r3=fit_edge(g,tl,bl,'x',1);right,r4=fit_edge(g,tr,br,'x',-1)
  except ValueError as e:raise ValueError(f'{name}/{p.name}: {e}; previous_quad={prev.tolist()}') from e
  q=np.array([cross(top,left),cross(top,right),cross(bottom,right),cross(bottom,left)])
  jump=float(np.max(np.linalg.norm(q-prev,axis=1)))
  if jump>15:raise ValueError(f'{name}/{p.name} tracking jump{jump}; manual correction required')
  prev=q;quads.append(q);residuals.append(max(r1,r2,r3,r4))
 # Three-frame median suppresses subpixel edge-fit noise; no long-window motion smoothing.
 smooth=median_filter(np.array(quads),size=(3,1,1),mode='nearest')
 keys=[]
 for i,q in enumerate(smooth):
  center=q.mean(axis=0);q=q+(center-q)/np.linalg.norm(center-q,axis=1)[:,None]*.85
  keys.append({'time':i/24,'quad':(q*1.5).round(3).tolist()})
  if i in [0,24,48,72,96,119]:
   im=Image.open(folder/f'{i+1:03}.png');d=ImageDraw.Draw(im);d.polygon([tuple(v) for v in q],outline='#00ffff',width=2);im.save(folder.parent/f'actual_track_{i:03}.jpg')
 tracks[name]=keys;report[name]={'source_fps':24,'measured_frames':len(keys),'basis':'every actual source frame, grayscale-to-bezel line fitting;3-frame median;0.85source-pixel inset','max_edge_residual_px':max(residuals),'sample_frames':[0,24,48,72,96,119],'continuous_playback':False}
(ROOT/'video/src/data-insight-v2/tracking.json').write_text(json.dumps(tracks,indent=2),encoding='utf8')
(EP/'editor-v2/tracking_measurements.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report))
