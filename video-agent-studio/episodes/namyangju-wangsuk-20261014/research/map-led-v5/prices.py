import pathlib,re,sys,html,json
p=pathlib.Path(__file__).parent;sys.stdout.reconfigure(encoding='utf-8');out={}
for f in p.glob('w*.html'):
 s=f.read_text(encoding='utf-8');a=s.find('평균분양가격');s=s[a:a+17000];rows=[]
 for row in re.findall(r'<tr[^>]*>(.*?)</tr>',s,re.S):
  cells=[html.unescape(re.sub('<[^>]+>',' ',c)).strip()for c in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>',row,re.S)]
  cells=[' '.join(c.split())for c in cells]
  if cells:rows.append(cells)
 out[f.stem]=rows[:12]
p.joinpath('price_page_rows.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(out,ensure_ascii=False))
