from pathlib import Path
import json,subprocess
from PIL import Image,ImageDraw
E=Path(__file__).resolve().parent;EP=E.parent.parent;R=EP.parents[2];O=EP/'outputs/production-v7-preview';D=O/'encoded_evidence/caption_patch';D.mkdir(exist_ok=True);F=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe';T=json.loads((O/'technical_v7.json').read_text());old=json.loads((O/'caption_patch_before/technical_v7.json').read_text());e=json.loads((O/'caption_patch_before/evidence_manifest.json').read_text());frames=[2539,2540,2607,2628,2714,2715];rows=[]
for f in frames:
 file=D/f'f{f:05}.png';z=subprocess.run(list(map(str,[F,'-v','error','-y','-ss',f/30,'-i',O/'changneung_full_v7_preview.mp4','-frames:v','1',file])),capture_output=True);assert z.returncode==0,z.stderr;rows.append(dict(file=str(file),frame=f,time_s=f/30,source_video_sha256=T['sha256'],unit_id='M001_005'if 2540<=f<2715 else'boundary'))
im=Image.new('RGB',(1920,780),'#ddd');dr=ImageDraw.Draw(im)
for i,r in enumerate(rows):x=i%3*640;y=i//3*390;im.paste(Image.open(r['file']).resize((640,360)),(x,y));dr.text((x+6,y+365),f"f{r['frame']} {r['time_s']:.3f}s",fill='black')
sheet=D/'patch_boundaries.jpg';im.save(sheet,quality=94)
for collection in ['cuts','motions','boundaries']:
 for r in e[collection]:r['source_video_sha256']=old['sha256']
e['cuts']=[r for r in e['cuts']if r['unit_id']!='M001_005'];p=json.loads((O/'project_v7.json').read_text());x=next(x for x in p['visual_intervals']if x.get('unit_id')=='M001_005');e['cuts'].append({**rows[2],'kind':'body','props':x['props'],'unit_id':'M001_005'});e['cuts'].sort(key=lambda r:r['frame']);
# Refresh presentation sheets from inherited pixels plus the one latest state; no unaffected rerender.
for k in range(0,len(e['cuts']),16):
 page=e['cuts'][k:k+16];im=Image.new('RGB',(1920,((len(page)+3)//4)*300),'#ddd');dr=ImageDraw.Draw(im)
 for j,r in enumerate(page):
  xx=j%4*480;yy=j//4*300;im.paste(Image.open(r['file']).resize((480,270)),(xx,yy));dr.text((xx+5,yy+274),f"{r['unit_id']} f{r['frame']} {r['frame']/30:.3f}s",fill='black')
 im.save(O/f'encoded_evidence/cut_contactsheet_{k//16+1:02}.jpg',quality=92)
Image.open(rows[2]['file']).resize((512,288)).save(D/'patch_mobile512.png')
e['source_video_sha256']=T['sha256'];e['caption_patch_actual_samples']=rows;e['caption_patch_sheet']=str(sheet);e['inherited_evidence']={'source_video_sha256':old['sha256'],'source_video':str(O/'caption_patch_before/changneung_full_v7_preview_before_caption_patch.mp4'),'scope':'unchanged semantic states/timeline; local caption only changed; final full stream decode repeated; old pixel samples retained with explicit provenance'};e['scope']='Mixed evidence: unchanged-state samples inherited from r1; six local patch boundary frames extracted from latest MP4; no continuous playback/listening claim';(O/'evidence_manifest.json').write_text(json.dumps(e,ensure_ascii=False,indent=2),encoding='utf-8');(O/'caption_patch_verification.json').write_text(json.dumps({'issue':'QAV7-P01','frames':[2540,2715],'caption':'지도에서 주거와 상업, 공원, 일자리 용지를 구분했습니다.','duration_s':175/30,'source_video_sha256':T['sha256'],'samples':rows,'sheet':str(sheet),'audio_unchanged':True,'duration_unchanged_frames':31426,'local_guard':'caption_patch_guard.json','before_video_sha256':old['sha256'],'technical':'technical_v7.json'},ensure_ascii=False,indent=2),encoding='utf-8');print('CAPTION_PATCH_EVIDENCE_READY '+T['sha256'])
