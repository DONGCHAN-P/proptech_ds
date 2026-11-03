from pathlib import Path
import urllib.request, concurrent.futures, json, hashlib, shutil, re, html
P=Path(__file__).parent
R=P/'raw'; R.mkdir(parents=True,exist_ok=True)
urls={
'rail_lh_20260930.pdf':'https://www.xn--3-3u6ey6lv7rsa.kr/kor/ajx_json/UploadMgr/downloadRun.do?qcode=Qm9hcmQsMTY1NSxZ',
's3s4_lh_20260630.pdf':'https://xn--3-3u6ey6lv7rsa.kr/kor/ajx_json/UploadMgr/downloadRun.do?qcode=Qm9hcmQsMTM2NixZ',
'landuse_entry.html':'https://www.xn--3-3u6ey6lv7rsa.kr/kor/CMS/Contents/Contents.do?mCode=MN077',
'transport_plan.html':'https://www.xn--3-3u6ey6lv7rsa.kr/kor/CMS/Contents/Contents.do?mCode=MN101',
'jobs_research_202502.pdf':'https://www.goyang.re.kr/board/free/photo/a81823_202502281035220.pdf',
'rail_lh_20260930.html':'https://www.xn--3-3u6ey6lv7rsa.kr/kor/CMS/Board/Board.do?board_seq=516&mCode=MN024&mgr_seq=12&mode=view',
's3s4_lh_20260703.html':'https://xn--3-3u6ey6lv7rsa.kr/kor/CMS/Board/Board.do?board_seq=466&mCode=MN024&mgr_seq=12&mode=view&page=1',
's5_current.html':'https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancInfo.do?aisTpCd=05&ccrCnntSysDsCd=02&mi=1027&uppAisTpCd=05&panId=0000060803',
'lx_wonheung.html':'https://lx.or.kr/ngyeonggi/sub04.do',
'supply_plan.html':'https://apply.lh.or.kr/lhapply/apply/noti/sp/list.do?mi=201523&sUppAisTpCd=05'
}
def get(item):
 n,u=item
 try:
  b=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=25).read()
  if n.endswith('.pdf') and not b.startswith(b'%PDF'): raise ValueError('not_pdf')
  (R/n).write_bytes(b)
  return {'name':n,'url':u,'local_path':str(R/n),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'download_status':'success','checked_on':'2026-10-15'}
 except Exception as e:return {'name':n,'url':u,'download_status':'failed','error':str(e)[:150]}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex: result=list(ex.map(get,urls.items()))
old=P.parents[1]/'namyangju-wangsuk-20261014/research/outside-comparisons-v6'
for n in ['changneung_s5_notice.pdf','changneung_s5_notice.txt']:
 s=old/n
 if s.exists():
  shutil.copy2(s,R/n); b=(R/n).read_bytes();result.append({'name':n,'local_path':str(R/n),'reuse_source':str(s),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'download_status':'reused_preserved_original','url':'https://apply.lh.or.kr/lhapply/lhFile.do?fileid=60487683'})
for f in R.glob('*.pdf'):
 try:
  import fitz
  d=fitz.open(f); (R/(f.stem+'.txt')).write_text('\n'.join(p.get_text() for p in d),encoding='utf-8')
 except Exception:pass
(P/'download_manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps([{'name':x['name'],'status':x['download_status'],'bytes':x.get('bytes')}for x in result],ensure_ascii=False))
