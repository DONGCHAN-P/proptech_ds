import pathlib,sys,re,json
p=pathlib.Path(__file__).parent;sys.stdout.reconfigure(encoding='utf-8');out={}
for f in p.glob('*notice.txt'):
 s=f.read_text(encoding='utf-8');hits=[]
 for term in ['단지 북측','단지 남측','단지 동측','단지 서측','광역교통','국도47','사릉역','왕숙역','(가칭)왕숙2-1초','왕숙11초']:
  for m in list(re.finditer(re.escape(term),s))[:4]:
   page=re.findall(r'=== PAGE (\d+) ===',s[:m.start()])[-1];hits.append(dict(term=term,page=int(page),text=s[max(0,m.start()-50):m.start()+500]))
 out[f.name]=hits
p.joinpath('environment_sections.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
for k,v in out.items():
 print('\n',k)
 for x in v[:7]:print(x['page'],x['term'],x['text'][:380].replace('\n',' '))
