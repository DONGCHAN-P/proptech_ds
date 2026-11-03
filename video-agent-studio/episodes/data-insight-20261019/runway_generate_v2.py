"""Device-use source shots. New v2 approval max300credits; credentials never logged."""
from pathlib import Path
import base64,json,sys,urllib.request,urllib.error,hashlib
ROOT=Path(__file__).resolve().parent
WORK=ROOT.parents[2];OUT=ROOT/'visual-v2';OUT.mkdir(exist_ok=True)
LEDGER=OUT/'generation_ledger.json';BASE='https://api.dev.runwayml.com/v1'
env={}
for line in (WORK/'.env').read_text(encoding='utf-8-sig').splitlines():
 if '=' in line and not line.lstrip().startswith('#'):
  k,v=line.split('=',1);env[k.strip()]=v.strip().strip('\"').strip("'")
key=env.get('RUNWAY_API_KEY') or env.get('RUNWAYML_API_SECRET')
if not key:raise SystemExit('Runway key missing')
headers={'Authorization':'Bearer '+key,'X-Runway-Version':'2024-11-06','Content-Type':'application/json'}
def api(path,payload=None):
 req=urllib.request.Request(BASE+path,data=None if payload is None else json.dumps(payload).encode(),headers=headers,method='GET' if payload is None else 'POST')
 try:
  with urllib.request.urlopen(req,timeout=120) as r:return json.load(r)
 except urllib.error.HTTPError as e:
  try:
   err=json.loads(e.read());safe={'error':err.get('error'),'issues':err.get('issues')}
   # Validation issues only; never dump inputs, headers, base64, or URLs.
   (OUT/'last_http_error.json').write_text(json.dumps(safe,indent=2),encoding='utf8')
  except Exception:pass
  raise SystemExit('Runway HTTP '+str(e.code)+' for '+path)
def save(data):LEDGER.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
ledger=json.loads(LEDGER.read_text(encoding='utf8')) if LEDGER.exists() else dict(approval_id='DI-BUDGET-v2',model='gen4.5',credits_per_second=12,max_credits=300,tasks=[],reserved_credits=0)
common='Premium corporate documentary. LOCKED TRIPOD CAMERA: absolutely no camera movement, zoom, pan or reframing. Preserve initial composition and all four screen corners. Physical display remains uniform dark neutral gray, completely blank, without text or UI. Hands and faces never overlap the screen. Natural adult anatomy, calm subtle movements, no speech or captions. '
specs=[
 ('monitor',common+'The seated woman looks at her desktop computer display and makes a small natural mouse movement with her right hand on the desk. She briefly shifts her fingers over the keyboard, maintaining her working posture and focus. The desktop monitor and desk remain absolutely still; preserve office architecture and lighting. We are observing real work over her shoulder, with the visible empty screen central to the shot.'),
 ('laptop',common+'Two coworkers study the open laptop display together. The seated woman makes a small mouse movement, and the navy-shirted man slightly nods while keeping his seated pose and hands below the screen. They remain looking at the device, do not turn toward the camera. Laptop stays fixed on the table, all four display corners visible and geometrically unchanged. Calm natural collaboration in this exact office lounge.'),
 ('phone',common+'The man quietly reads the phone in his hand. His thumb stays on the OUTSIDE bezel; it never crosses the gray screen. Hold the phone extremely steady with no rotation, translation, tilting or swaying. Only tiny natural movement in his shoulder and breathing. Keep exact evening pantry background. The phone screen and bezel corners are fixed and always unobstructed, camera focus stays on the physical display.')]
mode=sys.argv[1] if len(sys.argv)>1 else 'poll'
if mode=='balance':
 org=api('/organization');safe={'creditBalance':org.get('creditBalance')}
 path=OUT/('balance_after.json' if (OUT/'balance_before.json').exists() else 'balance_before.json');path.write_text(json.dumps(safe,indent=2),encoding='utf8');print(json.dumps(safe))
elif mode=='submit':
 for name,prompt in specs:
  if any(t['name']==name and t.get('id') for t in ledger['tasks']):continue
  assert len(prompt)<=1000,'Prompt exceeds model limit'
  if ledger['reserved_credits']+60>300:raise SystemExit('Budget exhausted')
  image=(OUT/(name+'_reference.jpg')).read_bytes()
  item=dict(name=name,prompt=prompt,duration=5,model='gen4.5',reserved_credits=60,status='submission_reserved',reference=name+'_reference.jpg');ledger['tasks'].append(item);ledger['reserved_credits']+=60;save(ledger)
  result=api('/image_to_video',dict(model='gen4.5',promptImage='data:image/jpeg;base64,'+base64.b64encode(image).decode(),promptText=prompt,ratio='1280:720',duration=5));item.update(id=result['id'],status='submitted');save(ledger);print(name+': submitted '+result['id'],flush=True)
elif mode=='poll':
 for item in ledger['tasks']:
  if not item.get('id') or item['status']=='downloaded':continue
  data=api('/tasks/'+item['id']);item['status']=data.get('status','unknown')
  if item['status']=='SUCCEEDED' and data.get('output'):
   with urllib.request.urlopen(data['output'][0],timeout=120) as r:content=r.read()
   p=OUT/(item['name']+'.mp4');p.write_bytes(content);item.update(status='downloaded',file=str(p),bytes=len(content),sha256=hashlib.sha256(content).hexdigest())
  if item['status'] in ['FAILED','CANCELED']:item['failure_code']=data.get('failureCode')
  save(ledger);print(item['name']+': '+item['status'],flush=True)
else:raise SystemExit('Use balance, submit, poll')
