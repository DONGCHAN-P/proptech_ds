import pathlib,urllib.request,re,concurrent.futures,json,sys
sys.stdout.reconfigure(encoding='utf-8');p=pathlib.Path(__file__).parent
files=[]
for f in p.glob('w*.html'):
 s=f.read_text(encoding='utf-8')
 for id,name in re.findall(r"fileDownLoad\('([0-9]+)'\);\">([^<]+\.pdf)</a>",s):
  if '팸플릿' in name or '모집공고' in name:files.append((f.stem,id,name))
def get(x):
 k,id,name=x;u='https://apply.lh.or.kr/lhapply/lhFile.do?fileid='+id
 try:
  b=urllib.request.urlopen(u,timeout=80).read();fn=k+'_'+('pamphlet'if'팸플릿'in name else'notice')+'.pdf';p.joinpath(fn).write_bytes(b);return dict(file=fn,url=u,original_name=name,bytes=len(b),valid_pdf=b.startswith(b'%PDF'))
 except Exception as e:return dict(url=u,error=type(e).__name__)
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as ex:r=list(ex.map(get,files))
p.joinpath('pdf_downloads.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(r,ensure_ascii=True))
