from pathlib import Path
import json
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parent;E=P.parent.parent;R=E.parents[2];O=E/'outputs/map-preview-v2';cfg=json.loads((R/'config/vertical_video_safe_area.json').read_text(encoding='utf8'));rect=cfg['profiles'][cfg['default_profile']]['critical_rect'];source=Image.open(O/'encoded_last.png').convert('RGB');cases=[]
for w,h in cfg['validation']['phone_viewports_css']+cfg['validation']['tablet_viewports_css']:
 for mode in cfg['validation']['fit_modes']:
  scale=(min if mode=='contain' else max)(w/1080,h/1920);dx=(w-1080*scale)/2;dy=(h-1920*scale)/2;b=[dx+rect['left']*scale,dy+rect['top']*scale,dx+rect['right']*scale,dy+rect['bottom']*scale];ui=[0,.14*h,w-64,.65*h];passed=b[0]>=ui[0] and b[1]>=ui[1] and b[2]<=ui[2] and b[3]<=ui[3];assert passed;row={'viewport':[w,h],'fit':mode,'critical_bbox':b,'modeled_ui_clear_rect':ui,'passed':passed}
  if (w,h) in [(375,812),(393,852),(768,1024)]:
   canvas=Image.new('RGB',(w,h),'#e7e6e2');canvas.paste(source.resize((round(1080*scale),round(1920*scale)),Image.Resampling.LANCZOS),(round(dx),round(dy)));overlay=Image.new('RGBA',(w,h),(0,0,0,0));d=ImageDraw.Draw(overlay);d.rectangle([0,0,w,.14*h],fill=(60,60,60,105));d.rectangle([0,.65*h,w,h],fill=(60,60,60,105));d.rectangle([w-64,.14*h,w,.65*h],fill=(60,60,60,105));d.rectangle(b,outline=(0,140,80,255),width=2);canvas=Image.alpha_composite(canvas.convert('RGBA'),overlay).convert('RGB');f=O/f'modeled_ui_{w}x{h}_{mode}.png';canvas.save(f);row['image']=f.name
  cases.append(row)
(O/'mobile_geometry_models.json').write_text(json.dumps({'cases':cases,'failed':0,'count':len(cases),'coverage':'Modeled overlays only, not actual device playback. Manual zoom/expanded comments/future UI changes not certified.'},indent=2),encoding='utf8');print('MODELED PHONE/TABLET CASES',len(cases),'PASS')
