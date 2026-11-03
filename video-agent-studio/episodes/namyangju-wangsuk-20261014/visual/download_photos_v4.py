exec((__import__('pathlib').Path(__file__).parent/'procure_v4.py').read_text('utf-8').split('all=[]')[0])
existing=json.loads((root/'commons_candidates_v4.json').read_text('utf-8'))
for q in ['Wangsuk','Byeollae Byeolgaram','Namyangju Dasan city']:
 try:
  d=get({'action':'query','format':'json','generator':'search','gsrsearch':q,'gsrnamespace':6,'gsrlimit':6,'prop':'imageinfo','iiprop':'url|size|extmetadata'})
  found=list(d.get('query',{}).get('pages',{}).values());existing.extend(found);print(q,[p['title'] for p in found])
 except Exception as e:print(q,str(e)[:100])
 time.sleep(1)
(root/'commons_candidates_v4.json').write_text(json.dumps(existing,ensure_ascii=False,indent=2),'utf-8')
chosen=['File:20240921 8호선 별내역 승강장.jpg','File:Byeollae-Y.JPG','File:Byeollae-station.jpg','File:Dasan station.jpg','File:Dasan station platform.jpg','File:남양주다산초등학교Namyangju Dasan Elementary School.jpg','File:20220319 진접역 2번출구.jpg','File:Jinjeop from Jugeumsan.jpg']
out=root/'outputs/photos_v4';out.mkdir(exist_ok=True);manifest=[]
for n,p in enumerate([next(p for p in existing if p['title']==t) for t in chosen],1):
 info=p['imageinfo'][0];m=info['extmetadata'];license=m.get('LicenseShortName',{}).get('value','');assert license.startswith(('CC','Public domain')),license
 filename=f'PHOTO{n:03d}.jpg';req=urllib.request.Request(info['url'],headers={'User-Agent':'NamyangjuEditorialVideo/1.0 (public licensed photo research)'})
 try:
  (out/filename).write_bytes(urllib.request.urlopen(req,timeout=30).read())
  manifest.append({'asset_id':f'PHOTO{n:03d}','title':p['title'],'source_url':info['descriptionurl'],'download_url':info['url'],'actual_file':'visual/outputs/photos_v4/'+filename,'dimensions':[info['width'],info['height']],'license':license,'license_url':m.get('LicenseUrl',{}).get('value'),'author_html':m.get('Artist',{}).get('value'),'photographed':m.get('DateTimeOriginal',{}).get('value'),'description_html':m.get('ImageDescription',{}).get('value'),'rights_metadata':m,'status':'downloaded_license_verified_pending_visual_review'})
  print(filename,license)
 except Exception as e:print('downloadfailed',p['title'],str(e)[:150])
(root/'photos_v4.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),'utf-8')
