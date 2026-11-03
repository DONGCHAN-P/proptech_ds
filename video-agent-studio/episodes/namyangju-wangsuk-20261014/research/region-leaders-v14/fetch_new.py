import urllib.request,pathlib,json,concurrent.futures
p=pathlib.Path(__file__).parent
urls={'north_b1b2_notice.pdf':'https://www.prugio.com/hb/2025/wangsuk/assets/pdf/%EC%9E%85%EC%A3%BC%EC%9E%90%EB%AA%A8%EC%A7%91%EA%B3%B5%EA%B3%A0%EC%A0%84%EB%AC%B8.pdf','north_b1_lh.html':'https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancInfo.do?panId=0000060927&ccrCnntSysDsCd=02&uppAisTpCd=05&aisTpCd=05&mi=1027'}
def f(z):
 n,u=z
 try:
  b=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=40).read();(p/n).write_bytes(b);return dict(file=n,url=u,bytes=len(b))
 except Exception as e:return dict(file=n,url=u,error=str(e))
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as ex:r=list(ex.map(f,urls.items()))
(p/'downloads.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(r))
