import pathlib,urllib.request,urllib.parse,re,json,sys,concurrent.futures
p=pathlib.Path(__file__).parent;sys.stdout.reconfigure(encoding='utf-8')
base='https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancInfo.do?aisTpCd=05&ccrCnntSysDsCd=02&mi=1027&uppAisTpCd=05&panId='
urls={'changneung_s5.html':base+'0000060803','gyosan_notice.pdf':'https://www.prugio.com/hb/2025/gyosan/assets/pdf/'+urllib.parse.quote('교산푸르지오더퍼스트_입주자모집공고.pdf'),'gyosan_rail_2026.html':'https://www.hanam.go.kr/mayor/selectCvplRceptWebView.do?cvplCode=MINWON5&key=10228&listTy=N&pageIndex=7&pageUnit=10&rceptNo=10639&searchCnd=all','changneung_rail_minutes.html':'https://www.goyangcouncil.go.kr/viewer/minutes.do?uid=14592'}
def fetch(k,u):
 try:
  b=urllib.request.urlopen(u,timeout=45).read();p.joinpath(k).write_bytes(b);print(k,len(b));return dict(file=k,url=u,bytes=len(b))
 except Exception as e:print(k,type(e).__name__);return dict(file=k,url=u,error=type(e).__name__)
with concurrent.futures.ThreadPoolExecutor(max_workers=4)as ex:r=list(ex.map(lambda x:fetch(*x),urls.items()))
s=p.joinpath('changneung_s5.html').read_text(encoding='utf-8')
for fid,name in re.findall(r"fileDownLoad\('([0-9]+)'\);\">([^<]+\.pdf)</a>",s):
 if '모집공고'in name:
  r.append(fetch('changneung_s5_notice.pdf','https://apply.lh.or.kr/lhapply/lhFile.do?fileid='+fid));break
p.joinpath('sources.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
