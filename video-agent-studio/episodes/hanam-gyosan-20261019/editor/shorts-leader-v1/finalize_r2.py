from pathlib import Path
import json,subprocess,re
E=Path(__file__).resolve().parent;EP=E.parents[1];ROOT=EP.parents[2];O=EP/'outputs/shorts-leader-v1'
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
s=(E/'verify.py').read_text(encoding='utf8').replace('gyosan_leader_short_v1.mp4','gyosan_leader_short_v1r2.mp4').replace("out/'technical.json'","out/'technical_r2.json'").replace("out/'render_receipt.json'","out/'render_receipt_r2.json'").replace("out/'audio_comparison.json'","out/'audio_comparison_r2.json'").replace("out/'decode.txt'","out/'decode_r2.txt'").replace("out/f'encoded-{sec:02}.png'","out/f'encoded-r2-{sec:02}.png'")
(E/'verify_r2.py').write_text(s,encoding='utf8');subprocess.run([str(ROOT/'tools/python311/python.exe'),'-X','utf8',str(E/'verify_r2.py')],check=True)
d=json.loads((E/'layout_bounds_r2.json').read_text());els=d['elements'];bad=[x for x in els if x['bbox'][0]<140 or x['bbox'][1]<260 or x['bbox'][2]>840.1 or x['bbox'][3]>1360];over=[]
for i,a in enumerate(els):
 for b in els[i+1:]:
  if a['frame']!=b['frame']:continue
  x=a['bbox'];y=b['bbox']
  if min(x[2],y[2])-max(x[0],y[0])>1 and min(x[3],y[3])-max(x[1],y[1])>1:over.append([a,b])
geo=json.loads((E/'data_r2.json').read_text());visibility=[]
for id in ['C2','B2']:
 f=next(x for x in geo['features'] if x['name']==f'공동주택 ({id})');a=list(map(float,re.findall(r'[-+]?\d*\.?\d+',f['d'])));v=geo['details'][id]['view'];s=1080/v[2];bb=[(min(a[::2])-v[0])*s,435+(min(a[1::2])-v[1])*s,(max(a[::2])-v[0])*s,435+(max(a[1::2])-v[1])*s];mini=[40,660,260,880];overlap=min(bb[2],mini[2])>max(bb[0],mini[0]) and min(bb[3],mini[3])>max(bb[1],mini[1]);visibility.append(dict(block=id,screen_bbox=bb,map_rect=[0,435,1080,920],mini_rect=mini,fully_visible=bb[0]>0 and bb[1]>435 and bb[2]<1080 and bb[3]<920,mini_overlap=overlap))
save(E/'layout_validation_r2.json',dict(profile='youtube_portrait_full_frame_v2',critical_bounds_violations=bad,critical_text_overlaps=over,measured_elements=len(els),target_polygon_visibility=visibility))
r=json.loads((O/'render_receipt_r2.json').read_text());save(E/'handoff_r2.json',dict(status='editor_rendered_pending_independent_qa',output=str(O/'gyosan_leader_short_v1r2.mp4'),sha256=r['sha256'],duration=r['duration'],source_plan=str(E/'clip_plan.json'),technical=str(O/'technical_r2.json'),layout=str(E/'layout_validation_r2.json'),encoded_samples=[str(x) for x in O.glob('encoded-r2-*.png')],paid_api_calls=0,upload_performed=False,actual_listening=False,continuous_playback=False,delta='Only C2/B2 detail view height485 and recentered geographic bounds; locator moved left. Original v1 MP4 preserved.',next_owner='root/independent QA'))
print(json.dumps(dict(bounds=len(bad),overlaps=len(over),target_visibility=visibility,sha256=r['sha256'])))
