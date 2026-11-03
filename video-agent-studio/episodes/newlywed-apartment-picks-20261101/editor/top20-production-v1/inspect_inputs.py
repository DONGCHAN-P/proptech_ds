from pathlib import Path
import json,xml.etree.ElementTree as ET
H=Path(__file__).resolve().parent; E=H.parents[1]; R=E.parents[2]
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
m=read(E/'visual/top20-8min-v2/maps/map_assets.json')
root=ET.parse(E/m['assets'][0]['vector_file']).getroot()
print('SVG root',root.attrib)
print('SVG clip rects',[n.attrib for n in root.iter() if n.tag.endswith('rect')])
for node in list(root):
 print('SVG child',node.tag.split('}')[-1], {k:v[:110] for k,v in node.attrib.items()},'children',len(node))
 for c in list(node)[:5]: print('  child',c.tag.split('}')[-1],{k:v[:80] for k,v in c.attrib.items()})
sp=read(E/'writer/top20-8min-v2/scene_proposals_v3.json')
print('scene keys',list(sp['scenes'][0]))
print('asset fields',list(read(E/'visual/top20-8min-v2/photo_assets_v2.json')['assets'][0]))
print('scene order',[(s['scene_id'],s['start_s'],s['end_s']) for s in sp['scenes']])
print('region-specific inputs', [str(p.relative_to(E)) for p in E.rglob('*spec*')][:20])
print('previous evidence', [str(p.relative_to(R)) for p in (R/'video-agent-studio/episodes/affordable-home-price-20261026/qa/jun-quality-v2/evidence').glob('*')][:15])

if __name__=='__main__':
 import subprocess
 from PIL import Image,ImageDraw,ImageFont
 ff=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe'
 movie=R/read(R/'config/current_video.json')['video']
 frames=[]
 for t in [70,190,390]:
  p=H/'evidence'/f'baseline_current_{t}.png'
  if not p.exists():
   r=subprocess.run([str(ff),'-v','error','-ss',str(t),'-i',str(movie),'-frames:v','1',str(p)],capture_output=True)
   print('baseline extraction',t,r.returncode)
  frames.append(p)
 sheet=Image.new('RGB',(960,600),'#f6f4ef')
 for i,p in enumerate(frames):
  im=Image.open(p); im.thumbnail((480,270)); sheet.paste(im,((i%2)*480,(i//2)*300))
 sheet.save(H/'evidence/baseline_current_sheet.jpg')
 photos=read(E/'visual/top20-8min-v2/photo_assets_v2.json')['assets']
 sheet=Image.new('RGB',(1400,1000),'#f6f4ef'); d=ImageDraw.Draw(sheet)
 for i,p in enumerate(photos):
  im=Image.open(Path(p['absolute_file'])); im.thumbnail((280,175)); x=(i%5)*280;y=(i//5)*250
  sheet.paste(im,(x,y)); d.text((x+5,y+180),p['region_id'],fill='black')
 sheet.save(H/'evidence/input_photos_sheet.jpg')
