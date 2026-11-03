import pathlib,json,html
from PIL import Image,ImageDraw,ImageFont
P=pathlib.Path(__file__).parent; E=P.parents[1]
colors={'housing':'#F5C96D','school':'#8ECFDB','education':'#8ECFDB','park':'#A8CE8C','commercial':'#E97E7B','mixed':'#EDA36E','public':'#9B94C2','work':'#728CB8','industry':'#728CB8','water':'#85C6E1'}
colors.update(jobs='#728CB8',commerce='#E97E7B',housing_low='#E8DBB4',road='#D8DBD9',rail='#A9AFB8')
for region in ['north','south']:
 source=E/'research/landuse-v7'/f'w1_{region}_geometry.json'
 if not source.exists():continue
 data=json.loads(source.read_text(encoding='utf-8')); _,_,W,H=data['viewBox']; features=[]
 for row in data['features']:
  xy=row['polygon']; anchor=row.get('anchor',[sum(x for x,y in xy)/len(xy),sum(y for x,y in xy)/len(xy)])
  features.append(dict(id=row['id'],type=row['kind'],label=row['label'],polygon=xy,anchor=anchor))
 cameras={'whole':[0,0,W,H],'a1_a2':[360,160,710,720],'north_jobs':[0,600,1280,1100]} if region=='north' else {'whole':[70,250,1510,1020],'a24_b17':[560,300,580,330],'jobs_station':[100,450,1380,790]}
 out=dict(revision=f'landuse-w1-{region}-v7',dimensions=[W,H],coordinate_system='source-plan-local-pixel; north-up; NOT cadastral/WGS84',source=data,features=features,roads=data.get('roads',[]),cameras=cameras,notes=[data['required_label']])
 P.joinpath(f'w1_{region}_board.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
 im=Image.new('RGB',(W,H),'#F5F3EB'); d=ImageDraw.Draw(im);svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="#F5F3EB"/>']
 for o in features:
  col=colors.get(o['type'],'#9B94C2');d.polygon(o['polygon'],fill=col,outline='white',width=4)
  svg.append(f'<polygon id="{o["id"]}" points="'+' '.join(f'{x},{y}' for x,y in o['polygon'])+f'" fill="{col}" stroke="white" stroke-width="4"/>')
 im.save(P/f'w1_{region}_board_unlabelled.png');P.joinpath(f'w1_{region}_board_unlabelled.svg').write_text(''.join(svg)+'</svg>',encoding='utf-8')
 for o in features:
  if not o['label']:continue
  x,y=o['anchor'];t=o['label'];size=26 if len(t)>9 else 30
  d.text((x,y),t,font=ImageFont.truetype('C:/Windows/Fonts/malgunbd.ttf',size),fill='#203345',anchor='mm')
  svg.append(f'<text x="{x}" y="{y}" text-anchor="middle" dominant-baseline="middle" font-family="Malgun Gothic" font-weight="700" font-size="{size}" fill="#203345">{html.escape(t)}</text>')
 im.save(P/f'w1_{region}_board.png');P.joinpath(f'w1_{region}_board.svg').write_text(''.join(svg)+'</svg>',encoding='utf-8')
 for key,(x,y,w,h) in cameras.items():im.crop((x,y,x+w,y+h)).save(P/f'w1_{region}_preview_{key}.png')
 print(region,len(features),'areas rendered')
