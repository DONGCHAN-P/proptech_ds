import json,urllib.request,urllib.parse,hashlib
from pathlib import Path
out=Path('video-agent-studio/episodes/goyang-changneung-20261015/visual/photo-v3');out.mkdir(parents=True,exist_ok=True)
titles=['File:Wonheung Station 20150304 160820.jpg','File:Wonheung Station 20150304 155831.jpg']
query=urllib.parse.urlencode({'action':'query','format':'json','titles':'|'.join(titles),'prop':'imageinfo','iiprop':'url|extmetadata','iiurlwidth':1600})
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'RealestateReco/1.0 (video photo source attribution research)'}),timeout=35) as r:return r.read()
data=json.loads(get('https://commons.wikimedia.org/w/api.php?'+query))
(out/'commons_metadata.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
assets=[]
for i,p in enumerate(data['query']['pages'].values()):
    info=p.get('imageinfo',[{}])[0];meta=info.get('extmetadata',{});license=meta.get('LicenseShortName',{}).get('value','')
    assert license.startswith('CC BY') or license in ['Public domain','CC0'],license
    url=info.get('thumburl') or info['url'];b=get(url);target=out/f'wonheung_{i+1}.jpg';target.write_bytes(b)
    assets.append({'file':str(target),'title':p['title'],'source':info.get('descriptionurl'),'url':url,'license':license,'metadata':meta,'sha256':hashlib.sha256(b).hexdigest(),'status':'downloaded_pending_visual_verification','historical_photo_not_2026_current':True})
(out/'assets.json').write_text(json.dumps(assets,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps([{'file':x['file'],'license':x['license']} for x in assets]))
