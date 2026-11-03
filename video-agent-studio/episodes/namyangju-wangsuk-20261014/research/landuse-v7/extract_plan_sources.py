import sys,json,pathlib,hashlib
p=pathlib.Path(__file__).parent
src=p.parent/'map-led-v5'
sys.path.insert(0,str(src/'_pdfdeps'))
import fitz
out=p/'source_assets';out.mkdir(parents=True,exist_ok=True)
index=[]
for name in ['w1_a1','w1_a2','w1_a24','w1_b17','w2_a3']:
 f=src/(name+'_pamphlet.pdf');doc=fitz.open(f)
 for i,page in enumerate(doc):
  if '토지이용계획' not in page.get_text() or i>6:continue
  base=name+f'_p{i+1}'
  page.get_pixmap(matrix=fitz.Matrix(3,3)).save(out/(base+'_300pct.png'))
  (out/(base+'_text.json')).write_text(json.dumps(page.get_text('dict',flags=0),ensure_ascii=False,indent=2),encoding='utf-8')
  paths=[]
  for d in page.get_drawings():
   paths.append({k:([list(v) if hasattr(v,'__len__') and not isinstance(v,(str,dict)) else v for v in val] if k=='items' else list(val) if isinstance(val,(fitz.Rect,fitz.Point)) else val) for k,val in d.items()})
  # Rendering paths need recursive serialization of Point/Rect/Quad.
  def ser(x):
   if isinstance(x,(fitz.Rect,fitz.Point,fitz.Quad)):return list(x)
   if isinstance(x,(list,tuple)):return [ser(v) for v in x]
   if isinstance(x,dict):return {k:ser(v) for k,v in x.items()}
   return x
  (out/(base+'_drawing_paths.json')).write_text(json.dumps(ser(page.get_drawings()),ensure_ascii=False,default=list),encoding='utf-8')
  (out/(base+'_reference.svg')).write_text(page.get_svg_image(),encoding='utf-8')
  index.append(dict(asset_id=base,source_file=str(f),source_page=i+1,page_size=list(page.rect),source_sha256=hashlib.sha256(f.read_bytes()).hexdigest(),vector_paths=len(page.get_drawings()),render=base+'_300pct.png',geometry=base+'_drawing_paths.json',usage='research_reference_only_until_specific_reuse_basis_confirmed',geometry_accuracy='published_schematic_not_cadastral_or_georegistered'))
(p/'source_assets.json').write_text(json.dumps(index,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(index,ensure_ascii=False))
