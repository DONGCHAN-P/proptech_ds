import pathlib,urllib.request,concurrent.futures,json,re,sys
sys.stdout.reconfigure(encoding='utf-8');p=pathlib.Path(__file__).parent
base='https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancInfo.do?aisTpCd=05&ccrCnntSysDsCd=02&mi=1027&uppAisTpCd=05&panId='
urls={'w1_a2':base.replace('aisTpCd=05','aisTpCd=39').replace('uppAisTpCd=05','uppAisTpCd=39')+'0000060921','w1_a24':base.replace('aisTpCd=05','aisTpCd=39').replace('uppAisTpCd=05','uppAisTpCd=39')+'0000061021','molit_2026':'https://www.molit.go.kr/2026plan/sub5_public.html','nine_2026':'https://www.ggc.go.kr/site/cmt/xb/lwmkr/lawmakerpressrelease/297475','industry_2026':'https://www.nyj.go.kr/industry/contents.do?key=4956'}
def fetch(k,u):
 try:
  b=urllib.request.urlopen(u,timeout=45).read();p.joinpath(k+'.html').write_bytes(b)
  s=b.decode('utf-8','replace');print(k,len(b));return k,u,len(b)
 except Exception as e:print(k,type(e).__name__);return k,u,type(e).__name__
with concurrent.futures.ThreadPoolExecutor(max_workers=4)as ex:res=list(ex.map(lambda x:fetch(*x),urls.items()))
p.joinpath('downloads.json').write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8')
