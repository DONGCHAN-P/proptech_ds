from pathlib import Path
import sys
sys.path.insert(0,str(Path('video-agent-studio/episodes/namyangju-wangsuk-20261014/research/map-led-v5/_pdfdeps').resolve()))
import requests,fitz,json,hashlib
root=Path(__file__).parent
urls={
'a2_corrected.pdf':'https://www.prugio.com/hb/2025/gyosan/assets/pdf/%28%EC%A0%95%EC%A0%95%29250424_%EA%B5%90%EC%82%B0%ED%91%B8%EB%A5%B4%EC%A7%80%EC%98%A4%EB%8D%94%ED%8D%BC%EC%8A%A4%ED%8A%B8_%EC%9E%85%EC%A3%BC%EC%9E%90%EB%AA%A8%EC%A7%91%EA%B3%B5%EA%B3%A0.pdf',
'huic_esg.pdf':'https://www.huic.co.kr/DATA/download/www/cts312_file02.pdf',
'rail_20260922.html':'https://www.hanam.go.kr/mayor/selectCvplRceptWebView.do?cvplCode=MINWON5&key=10229&listTy=N&pageIndex=7&pageUnit=10&rceptNo=10639&searchCnd=all',
'plan_web.html':'https://www.xn--3-3u6ey6lv7rsa.kr/kor/CMS/Contents/Contents.do?mCode=MN053',
'council_20260722.html':'https://council.hanam.go.kr/minutes/svc/web/cms/mnts/SvcMntsViewer.php?mode=spkr1&schSn=3211&spkrCd=MBR9010'
}
manifest=[]
for name,url in urls.items():
 try:
  r=requests.get(url,timeout=40);r.raise_for_status();p=root/name;p.write_bytes(r.content)
  item={'file':name,'url':url,'bytes':len(r.content),'sha256':hashlib.sha256(r.content).hexdigest()}
  if name.endswith('.pdf'):
   doc=fitz.open(p);item['pages']=len(doc)
   (root/(p.stem+'.txt')).write_text('\n'.join(f'=== PAGE {i+1} ===\n'+pg.get_text() for i,pg in enumerate(doc)),encoding='utf-8')
   if name=='huic_esg.pdf':
    for i,pg in enumerate(doc):
     if '토지이용' in pg.get_text():pg.get_pixmap(matrix=fitz.Matrix(2,2)).save(root/f'huic_plan_p{i+1}.png')
   if name=='a2_corrected.pdf':
    for i in [6,7,8,46]:
     if i<len(doc):doc[i].get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(root/f'a2_p{i+1}.png')
  manifest.append(item)
 except Exception as e:manifest.append({'file':name,'url':url,'error':str(e)})
(root/'download_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(manifest,ensure_ascii=False,indent=2))
