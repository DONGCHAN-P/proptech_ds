from pathlib import Path
import concurrent.futures, hashlib, json, subprocess, math
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
EP = HERE.parents[2]
ROOT = EP.parents[2]
SRC = EP / 'editor/jun-user-script-v1/full-film-v1'
VIDEO = EP / 'outputs/jun-user-script-v1/full-film-v1/affordable_price_jun_user_script_v2.mp4'
FF = ROOT / 'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
PROBE = ROOT / 'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''):h.update(chunk)
    return h.hexdigest()

def save(name, value):
    (HERE/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def tc(t):
    return f'{int(t)//60:02}:{t%60:06.3f}'

def main():
    sch=json.loads((SRC/'schedule.json').read_text(encoding='utf-8-sig'))
    inputs=[]
    for p in [VIDEO, SRC/'assemble.py', SRC/'build_visuals.py', SRC/'schedule.json']:
        inputs.append({'path':str(p), 'bytes':p.stat().st_size, 'sha256':sha(p)})
    save('input_manifest.json',inputs)
    r=subprocess.run([str(PROBE),'-v','error','-show_entries','format=duration,size:stream=index,codec_name,codec_type,width,height,r_frame_rate,duration,sample_rate,channels','-of','json',str(VIDEO)],capture_output=True,check=True)
    save('stream_metadata.json',json.loads(r.stdout))
    samples=[]
    for p in sch['placements']:
        if p['kind']!='scene':continue
        s=p['scene']; sid=p['id']
        local=min(s['beats'][-1]['start_s']+.70,p['duration']-.20)
        samples.append({'scene_id':sid,'role':'fully_built','time_s':round(math.ceil((p['start']+local)*30-1e-6)/30,6)})
        if sid in ['S03','S04','S08','S11','S12','S18','S20','S21','S22','S24','S30']:
            pre=min(max(s['beats'][0]['start_s']-.25,.3),5.0)
            samples.append({'scene_id':sid,'role':'pre_first_beat','time_s':round(math.ceil((p['start']+pre)*30-1e-6)/30,6)})
    extras=[('S04','arrow_pre',83.70),('S04','arrow_settled',84.40),('S18','cap_pre_total',399.0),('S22','pre_first_row',520.80),('S26','scene_open',592.166667),('S12','pre_last_beat',276.8)]
    samples += [{'scene_id':s,'role':r,'time_s':t} for s,r,t in extras]
    for x in samples:
        x['timecode']=tc(x['time_s']);x['file']=f'{x["scene_id"]}_{x["role"]}_{x["time_s"]:010.3f}.jpg'
    def extract(x):
        r=subprocess.run([str(FF),'-v','error','-threads','1','-ss',str(x['time_s']),'-i',str(VIDEO),'-frames:v','1','-q:v','2','-y',str(HERE/x['file'])],capture_output=True)
        if r.returncode:raise RuntimeError(r.stderr.decode('utf-8','replace'))
        with Image.open(HERE/x['file']) as im:x['size']=list(im.size)
        x['bytes']=(HERE/x['file']).stat().st_size
        return x
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:samples=list(ex.map(extract,samples))
    save('frame_manifest.json',samples)
    font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',20)
    groups=[('full', [x for x in samples if x['role']=='fully_built']),('holds',[x for x in samples if x['role']!='fully_built'])]
    for prefix,rows in groups:
        for page in range(math.ceil(len(rows)/9)):
            subset=rows[page*9:(page+1)*9];nrows=math.ceil(len(subset)/3)
            sheet=Image.new('RGB',(1920,nrows*390),'#172b38');draw=ImageDraw.Draw(sheet)
            for i,x in enumerate(subset):
                left=(i%3)*640;top=(i//3)*390
                with Image.open(HERE/x['file']) as im:sheet.paste(im.resize((640,360)),(left,top+30))
                draw.text((left+8,top+4),f'{x["scene_id"]} {x["timecode"]} {x["role"]}',font=font,fill='white')
            sheet.save(HERE/f'contact_{prefix}_{page+1:02}.jpg',quality=94)
    print(json.dumps({'frames':len(samples),'contact_sheets':sum(math.ceil(len(a)/9) for _,a in groups),'evidence':str(HERE),'input_sha256':inputs[0]['sha256']}))

if __name__=='__main__':main()
