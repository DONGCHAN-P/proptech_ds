"""Runway film assets. Explicit USD 3 / 300 credit approval, no auto-retry.
Credentials are read only from workspace .env and never logged.
"""
from pathlib import Path
import base64,json,sys,urllib.request,urllib.error,hashlib,io
from PIL import Image,ImageOps

ROOT=Path(__file__).resolve().parent
WORK=ROOT.parents[2]
OUT=ROOT/'visual';OUT.mkdir(exist_ok=True)
LEDGER=OUT/'generation_ledger.json'
BASE='https://api.dev.runwayml.com/v1'
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
        # No raw response: request echoes could contain base64 or secrets.
        raise SystemExit('Runway HTTP '+str(e.code)+' for '+path)

def save(data):LEDGER.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
ledger=json.loads(LEDGER.read_text(encoding='utf8')) if LEDGER.exists() else dict(approval_id='DI-BUDGET-v1',model='gen4.5',credits_per_second=12,max_credits=300,tasks=[],reserved_credits=0)
specs=[
 ('office','A02.jpg','Cinematic corporate documentary, one continuous natural shot in this exact modern Korean office. A Korean female professional in her early thirties, ivory blouse and charcoal trousers, enters the frame from the left already walking naturally down the foreground aisle toward her workstation. She sets down her shoulder bag beside a chair and glances at a computer screen with a thoughtful expression. Another adult colleague passes in the distant background. Slow subtle camera dolly forward. Preserve the architecture and furniture. Soft realistic morning daylight, premium commercial cinematography, anatomically natural human movement, understated acting, no speech, no titles, no captions, no floating interface.'),
 ('pantry','A04.jpg','Cinematic corporate documentary in this exact office pantry, one continuous shot. A Korean male professional in his thirties wearing a navy shirt enters the foreground from the right carrying a simple ceramic coffee mug. He pauses by the counter and glances down at his phone, then relaxes with a small reassured smile. Natural gentle body movement. Stable slow lateral camera move, realistic soft late afternoon light. Preserve the counter, coffee machines and office architecture. Tasteful premium brand film, normal adult anatomy, no speech, no written overlays, no generated text or interface.'),
 ('team','A11.jpg','Premium cinematic corporate documentary, natural Korean office collaboration in this exact bright lounge. Two adult Korean colleagues, a woman in an ivory blouse and a man in a navy shirt, walk into the frame from opposite sides and meet at the nearest round table. They pause beside the table and share a brief friendly nod and an understated smile while looking at a slim laptop on the table. Natural candid movements, small gestures, slow gentle camera push in. Keep the room architecture, windows and tables coherent. Warm afternoon daylight, realistic human proportions, no speech, no titles or text overlays, no animated mascots.')]
mode=sys.argv[1] if len(sys.argv)>1 else 'poll'
if mode=='balance':
    org=api('/organization')
    safe={k:v for k,v in org.items() if k in ['creditBalance','tier','maxMonthlyCreditSpend','autoBilling']}
    balance_path=OUT/('balance_after.json' if (OUT/'balance_before.json').exists() else 'balance_before.json')
    balance_path.write_text(json.dumps(safe,indent=2),encoding='utf8')
    print(json.dumps({'creditBalance':safe.get('creditBalance'),'maxMonthlyCreditSpend':safe.get('tier',{}).get('maxMonthlyCreditSpend')}));raise SystemExit()
if mode=='submit':
    for name,source,prompt in specs:
        if any(t['name']==name for t in ledger['tasks']):continue
        if ledger['reserved_credits']+60>300:raise SystemExit('Approved budget exhausted')
        im=Image.open(ROOT/'inputs'/source).convert('RGB')
        im=ImageOps.fit(im,(1280,720),method=Image.Resampling.LANCZOS)
        buf=io.BytesIO();im.save(buf,format='JPEG',quality=94)
        im.save(OUT/(name+'_reference.jpg'),quality=94)
        item=dict(name=name,source=source,prompt=prompt,duration=5,model='gen4.5',reserved_credits=60,status='submission_reserved')
        ledger['tasks'].append(item);ledger['reserved_credits']+=60;save(ledger)
        result=api('/image_to_video',dict(model='gen4.5',promptImage='data:image/jpeg;base64,'+base64.b64encode(buf.getvalue()).decode(),promptText=prompt,ratio='1280:720',duration=5))
        item.update(id=result['id'],status='submitted');save(ledger)
        print(name+': submitted '+result['id'],flush=True)
elif mode=='poll':
    for item in ledger['tasks']:
        if not item.get('id') or item['status']=='downloaded':continue
        data=api('/tasks/'+item['id']);item['status']=data.get('status','unknown')
        if item['status']=='SUCCEEDED':
            urls=data.get('output',[])
            if urls:
                with urllib.request.urlopen(urls[0],timeout=120) as r:content=r.read()
                path=OUT/(item['name']+'.mp4');path.write_bytes(content)
                item.update(status='downloaded',file=str(path),bytes=len(content),sha256=hashlib.sha256(content).hexdigest())
        if item['status'] in ['FAILED','CANCELED']:
            item['failure_code']=data.get('failureCode');item['failure']=data.get('failure')
        save(ledger);print(item['name']+': '+item['status'],flush=True)
else:raise SystemExit('Use balance, submit, poll')
