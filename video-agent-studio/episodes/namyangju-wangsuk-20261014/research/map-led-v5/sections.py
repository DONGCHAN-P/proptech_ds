import pathlib,sys,json
p=pathlib.Path(__file__).parent;sys.stdout.reconfigure(encoding='utf-8')
out={}
for f in p.glob('*notice.txt'):
 s=f.read_text(encoding='utf-8');sections=[]
 for token in ['■ 학교설립 계획','■ 학교설립계획','■ 지구 및 단지 여건','■ 지구및단지','학교설립 계획 및 통학','학교설립계획 및 통학']:
  i=s.find(token)
  if i>=0:sections.append(s[i:i+3300])
 out[f.name]=sections
p.joinpath('school_sections.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(out,ensure_ascii=False)[:18000])
