from pathlib import Path
import sys,json,time,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import base_geometry as G
E=P.parent.parent;R=E/'research/monthly-5eok-v1';O=E/'outputs/monthly-5eok-v1';C=O/'cache';C.mkdir(exist_ok=True);a=np.load(R/'monthly_arrays.npz');status=a['status'];catalog=json.loads((R/'complex_catalog.json').read_text(encoding='utf8'));summary=json.loads((R/'monthly_summary.json').read_text(encoding='utf8'));val=json.loads((R/'validation.json').read_text(encoding='utf8'));assert status.shape==(250,8288);xy=[G.pr((c['x_5179'],c['y_5179'])) for c in catalog];assert all(0<=x<G.W and 0<=y<G.H for x,y in xy);S=2
# Static map geometry is cached once; each endpoint has true discrete source statuses.
label_overlay=Image.new('RGBA',(G.W*S,G.H*S),(0,0,0,0));ld=ImageDraw.Draw(label_overlay)
for lab in G.labels:
 x,y=G.pr(lab['native_anchor']);tx=x+lab['offset'][0];ty=y+lab['offset'][1];fo=G.font(35*S,True);box=ld.textbbox((tx*S,ty*S),lab['text'],font=fo,anchor='mm');box=[box[0]-10,box[1]-6,box[2]+10,box[3]+6];ld.line([(x*S,y*S),(tx*S,ty*S)],fill='#7d91a7',width=2);ld.rounded_rectangle(box,radius=12,fill=G.navy);ld.text((tx*S,ty*S),lab['text'],font=fo,anchor='mm',fill=G.white)
records=[];start=time.perf_counter()
for mi,s in enumerate(summary):
 im=G.base.copy();d=ImageDraw.Draw(im);counts={0:0,2:0}
 for st,color,rad in [(2,G.dim,1.55),(0,G.orange,2.3)]:
  for i in np.flatnonzero(status[mi]==st):
   x,y=xy[i];d.ellipse([(x-rad)*S,(y-rad)*S,(x+rad)*S,(y+rad)*S],fill=color);counts[st]+=1
 assert counts[0]==s['map_under'] and counts[2]==s['map_no_trade'];im.paste(label_overlay,(0,0),label_overlay);out=im.resize((G.W,G.H),Image.Resampling.LANCZOS);out.save(C/f'map_{mi:03d}.png',compress_level=1);records.append({'month':s['month'],'under_drawn':counts[0],'no_trade_drawn':counts[2],'over_hidden':s['map_over'],'first_observation_hidden':s['map_not_yet_observed'],'source_counts_match':True})
 if mi%50==0:print('MAP_CACHE '+str(mi)+'/250',flush=True)
# Global styling and axes stay constant; all reported values will come from monthly source rows.
static=Image.new('RGB',(1080,1920),G.navy);d=ImageDraw.Draw(static)
def text(im,txt,x,y,size,bold=False,color=G.white):
 ImageDraw.Draw(im).text((x,y),txt,font=G.font(size,bold),fill=color,anchor='lt')
text(static,'수도권, 5억으로 어디까지?',64,274,54,True);text(static,'84㎡급 · 월중위값 · 연결 8,288 / 제외 884',66,346,30,color=G.muted);text(static,'5억 이하 비율',66,395,28,color=G.muted)
lo,hi=val['chart_axis_percent'];cx0,cx1,cy0,cy1=70,878,435,557
cp=lambda mi,r:(cx0+mi/249*(cx1-cx0),cy1-(r-lo)/(hi-lo)*(cy1-cy0));chart=[cp(i,s['ratio_percent']) for i,s in enumerate(summary)];d.line([(cx0,cy0),(cx1,cy0)],fill='#18283d',width=1);d.line([(cx0,cy1),(cx1,cy1)],fill='#18283d',width=1);d.line(chart,fill='#263a50',width=3)
text(static,str(hi)+'%',66,436,22,color=G.muted);text(static,str(lo)+'%',66,535,22,color=G.muted);text(static,'2006.01',66,570,25,color=G.muted);text(static,'2026.10',780,570,25,color=G.muted)
text(static,'5억 이하',90,1817,25,color=G.muted);text(static,'당월 미거래',320,1817,25,color=G.muted);text(static,'초과 숨김',610,1817,25,color=G.muted);d.ellipse([66,1824,80,1838],fill=G.orange);d.ellipse([296,1824,310,1838],fill=G.dim);text(static,'미연결 884단지 제외 · 최대 계약일 2026.10.10',66,1854,25,color=G.muted);static.save(C/'static.png',compress_level=1)
# Only small transparent data-text panels are cached, never a monthly stop-frame video.
bounds=[]
for mi,s in enumerate(summary):
 panel=Image.new('RGBA',(1080,380),(0,0,0,0));dd=ImageDraw.Draw(panel);items=[('ratio',f"{s['ratio_percent']:.1f}%",710,389,40,True,G.orange),('month',s['month_label'],64,612,82,True,G.white),('counter',f"{s['map_under']:,} / {s['map_observed']:,}",433,623,48,True,G.orange),('counter_label','5억 이하 / 당월 관측 단지',435,681,28,False,G.muted),('partial','2026.10 부분월 · 계약자료 10.10까지' if mi==249 else '연결 표본 · 해당 월 거래 기준',66,724,26,False,G.muted)]
 for name,txt,x,y,size,bold,color in items:
  b=dd.textbbox((x,y-380),txt,font=G.font(size,bold),anchor='lt');assert b[0]>=48 and b[2]<=920 and b[1]>=0 and b[3]<=380,(mi,name,b);dd.text((x,y-380),txt,font=G.font(size,bold),fill=color,anchor='lt');bounds.append({'month':s['month'],'field':name,'bbox':[b[0],b[1]+380,b[2],b[3]+380],'text':txt})
 panel.save(C/f'panel_{mi:03d}.png',compress_level=1)
receipt={'cache_role':'Endpoint state layers and text panels only. Every video frame is composed with point opacity blend and a moving chart cursor/reveal.','month_count':250,'map_layers':250,'source_draw_counts':records,'native_positions_fixed':True,'over_and_not_yet_observed_not_drawn_at_endpoint':True,'chart_axis_percent':[lo,hi],'chart_points':chart,'map_viewport':[0,G.maptop,G.W,G.maptop+G.H],'point_color_under':G.orange,'point_color_no_trade':G.dim,'render_seconds':time.perf_counter()-start,'packet_sha256':hashlib.sha256((E/'research/annual-map-v2/map_packet_v2.json').read_bytes()).hexdigest(),'data_validation_sha256':hashlib.sha256((R/'validation.json').read_bytes()).hexdigest()};(O/'cache_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8');(O/'monthly_text_bounds.json').write_text(json.dumps(bounds,ensure_ascii=False),encoding='utf8');print(json.dumps({'cache_seconds':receipt['render_seconds'],'map_layers':250,'panels':250}),flush=True)
