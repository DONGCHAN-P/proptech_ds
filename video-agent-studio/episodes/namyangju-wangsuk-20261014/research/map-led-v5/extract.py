import sys,pathlib,json
p=pathlib.Path(__file__).parent;sys.path.insert(0,str(p/'_pdfdeps'));sys.stdout.reconfigure(encoding='utf-8');import fitz
idx=[]
for f in p.glob('*.pdf'):
 d=fitz.open(f);out=[];hits=[]
 for i,page in enumerate(d):
  t=page.get_text();out.append(f'\n=== PAGE {i+1} ===\n'+t)
  terms=[x for x in ['토지이용','학교','입주예정','개교','교통망','왕숙역','풍양역','왕숙2역','A-24','B-17']if x in t]
  if terms:hits.append(dict(page=i+1,terms=terms))
  if 'pamphlet'in f.stem and i<5:
   page.get_pixmap(matrix=fitz.Matrix(1,1)).save(p/(f.stem+f'_p{i+1}.png'))
 p.joinpath(f.stem+'.txt').write_text(''.join(out),encoding='utf-8');idx.append(dict(file=f.name,pages=len(d),hits=hits))
p.joinpath('pdf_index.json').write_text(json.dumps(idx,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(idx,ensure_ascii=False)[:7000])
