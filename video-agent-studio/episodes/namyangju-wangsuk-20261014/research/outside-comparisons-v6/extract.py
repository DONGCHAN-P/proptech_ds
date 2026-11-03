import pathlib,sys,json,re,html
p=pathlib.Path(__file__).parent;sys.path.insert(0,str(p.parent/'map-led-v5/_pdfdeps'));sys.stdout.reconfigure(encoding='utf-8');import pymupdf
idx=[]
for f in p.glob('*.pdf'):
 d=pymupdf.open(f);texts=[];hits=[]
 for i,pg in enumerate(d):
  t=pg.get_text();texts.append(f'\n=== PAGE {i+1} ===\n'+t)
  terms=[x for x in ['84A','84B','5층','입주예정','개교','하남검단산','GTX','왕숙','창릉역']if x in t]
  if terms:hits.append(dict(page=i+1,terms=terms))
 p.joinpath(f.stem+'.txt').write_text(''.join(texts),encoding='utf-8');idx.append(dict(file=f.name,pages=len(d),hits=hits))
p.joinpath('pdf_index.json').write_text(json.dumps(idx,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(idx,ensure_ascii=False)[:4000])
