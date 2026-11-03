from pathlib import Path
from PIL import Image,ImageDraw
import json,re
OWN=Path(__file__).resolve().parent;EP=OWN.parents[2];ROOT=EP.parents[2]
d=json.loads((OWN/'DOM_evidence.json').read_text('utf-8'))
def sheet(rows,name,cols=3,thumb=(640,360)):
 h=thumb[1]+26;canvas=Image.new('RGB',(cols*thumb[0],((len(rows)+cols-1)//cols)*h),'#e7e7e7');draw=ImageDraw.Draw(canvas)
 for i,row in enumerate(rows):
  x,y=(i%cols)*thumb[0],(i//cols)*h
  with Image.open(ROOT/row['frame']) as im:canvas.paste(im.convert('RGB').resize(thumb,Image.Resampling.LANCZOS),(x,y+26))
  draw.text((x+8,y+5),f'{row.get("id",row.get("cue_id"))}  {row["time"]:.3f}s',fill='black')
 canvas.save(OWN/name,quality=94)
for i in range(3):sheet(d['scenes'][i*11:(i+1)*11],f'scenes_contact_{i+1}.jpg')
sheet(d['chapters'],'chapter_cards_contact.jpg')
sheet(d['boundaryChecks'],'ending_boundary_contact.jpg',cols=2)
for i in range(4):sheet(d['captions'][i*39:(i+1)*39],f'captions_contact_{i+1}.jpg',cols=2,thumb=(864,62))
err=[]
for x in d['captions']:
 if re.sub(r'\s+','',x['cueText'])!=re.sub(r'\s+','',x['expectedText']) or x['cueOpacity']<.99:err.append(x['cue_id'])
print(json.dumps({'visible_scene_roots':sum(x['rootVisible'] for x in d['scenes']),'visible_chapter_roots':sum(x['rootVisible'] for x in d['chapters']),'caption_DOM_text_or_visibility_errors':err,'fontFamilies':sorted({r['fontFamily'] for x in d['scenes']+d['captions'] for r in x['rows']}),'font_not_loaded':sum(not r['fontLoaded'] for x in d['scenes']+d['captions'] for r in x['rows'])},ensure_ascii=False))
