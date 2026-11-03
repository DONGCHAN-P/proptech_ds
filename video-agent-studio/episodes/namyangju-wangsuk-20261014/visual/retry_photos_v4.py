exec((__import__('pathlib').Path(__file__).parent/'procure_v4.py').read_text('utf-8').split('all=[]')[0])
from PIL import Image,ImageDraw
existing=json.loads((root/'commons_candidates_v4.json').read_text('utf-8'));manifest=json.loads((root/'photos_v4.json').read_text('utf-8'));out=root/'outputs/photos_v4'
chosen=['File:Dasan station platform.jpg','File:남양주다산초등학교Namyangju Dasan Elementary School.jpg','File:20220319 진접역 2번출구.jpg','File:Jinjeop from Jugeumsan.jpg','File:20240910 별내별가람역 1번출구.jpg','File:ROK National Route 6 Wangsuk BR(Westward Dir) 1.jpg']
for n,t in enumerate(chosen,9):
 p=next(p for p in existing if p['title']==t);info=p['imageinfo'][0];m=info['extmetadata'];lic=m.get('LicenseShortName',{}).get('value','');assert lic.startswith(('CC','Public domain')),lic
 filename=f'PHOTO{n:03d}.jpg';req=urllib.request.Request(info['url'],headers={'User-Agent':'NamyangjuEditorialVideo/1.0 (public licensed photo research)'})
 try:
  response=urllib.request.urlopen(req,timeout=25);(out/filename).write_bytes(response.read());manifest.append({'asset_id':f'PHOTO{n:03d}','title':t,'source_url':info['descriptionurl'],'download_url':info['url'],'actual_file':'visual/outputs/photos_v4/'+filename,'dimensions':[info['width'],info['height']],'license':lic,'license_url':m.get('LicenseUrl',{}).get('value'),'author_html':m.get('Artist',{}).get('value'),'photographed':m.get('DateTimeOriginal',{}).get('value'),'description_html':m.get('ImageDescription',{}).get('value'),'rights_metadata':m,'status':'downloaded_license_verified_pending_visual_review'});print(filename,lic)
 except urllib.error.HTTPError as e:
  print('HTTP',e.code,'retry_after',e.headers.get('Retry-After'),'file',t)
  if e.code==429:break
 time.sleep(2)
(root/'photos_v4.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),'utf-8')
imgs=list(out.glob('*.jpg'));sheet=Image.new('RGB',(1200,((len(imgs)+2)//3)*280),'white');d=ImageDraw.Draw(sheet)
for i,p in enumerate(imgs):
 im=Image.open(p);im.thumbnail((390,245));x=i%3*400;y=i//3*280;sheet.paste(im,(x,y));d.text((x+5,y+250),p.name,fill='black')
sheet.save(root/'outputs/photos_contact_v4.jpg')
