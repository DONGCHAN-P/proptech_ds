"""Inspect real encoded preview streams, decode them and extract review evidence."""
from pathlib import Path
import datetime as dt
import argparse
import hashlib
import json
import subprocess
from PIL import Image, ImageOps, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
EP=ROOT/'video-agent-studio/episodes/regional-price-recovery-20261022'
OUT=EP/'outputs/production-v1-jun'
parser=argparse.ArgumentParser()
parser.add_argument('--revision',choices=['v2','v3'],default='v2')
args=parser.parse_args()
PRE=OUT/'previews';EVID=OUT/f'checks/encoded_preview_frames_{args.revision}';EVID.mkdir(parents=True,exist_ok=True)
manifest=json.loads((OUT/'reusable_assets/manifest.json').read_text(encoding='utf8'))
ff=manifest['ffmpeg'];probe=manifest['ffprobe']
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
names=['full2006paths','incheon2008-2016recovery','rawmedianvsindex']
handoff_path=EP/'editor/production-v1/handoff.json'
selected=json.loads(handoff_path.read_text(encoding='utf8'))['selected_previews']
sources={}
for name in names:
    item=next(item for item in selected if Path(item['path']).name.startswith(name+'_provisional_'))
    p=ROOT/item['path'];assert sha(p)==item['sha256']
    sources[name]=p
results=[];frames=[]
for name in names:
    p=sources[name];assert p.is_file(),p
    m=json.loads(subprocess.check_output([probe,'-v','error','-show_format','-show_streams','-of','json',str(p)],text=True,encoding='utf8'))
    v=next(s for s in m['streams'] if s['codec_type']=='video')
    duration=float(m['format']['duration'])
    assert abs(duration-8)<0.1 and (v['width'],v['height'])==(1920,1080) and v['r_frame_rate']=='30/1'
    assert not any(s['codec_type']=='audio' for s in m['streams']), 'These are explicitly silent prototypes'
    subprocess.run([ff,'-v','error','-i',str(p),'-f','null','-'],check=True)
    hashes=[]
    for sec in [2,4,7]:
        target=EVID/f'{name}_{sec}s.png'
        subprocess.run([ff,'-v','error','-y','-ss',str(sec),'-i',str(p),'-frames:v','1',str(target)],check=True)
        digest=sha(target);hashes.append(digest)
        frames.append({'clip':name,'at_seconds':sec,'path':target.relative_to(ROOT).as_posix(),'sha256':digest,'review':'pending_static_visual_review'})
    assert len(set(hashes))>1,'No sampled motion differences: '+name
    results.append({'clip':name,'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size,
                    'duration':duration,'resolution':[1920,1080],'fps':'30/1','audio_streams':0,'full_decode':'pass','sampled_unique_frames':len(set(hashes))})
concat=PRE/f'preview_concat_{args.revision}.txt'
concat.write_text('\n'.join("file '"+sources[n].name+"'" for n in names)+'\n',encoding='utf8')
combined=PRE/f'지역별회복_모션시안_{args.revision}_무음.mp4'
subprocess.run([ff,'-v','error','-y','-f','concat','-safe','0','-i',str(concat),'-c','copy','-movflags','+faststart',str(combined)],check=True)
subprocess.run([ff,'-v','error','-i',str(combined),'-f','null','-'],check=True)
sheet=Image.new('RGB',(1440,870),'#f6f4ef');draw=ImageDraw.Draw(sheet)
for i,item in enumerate(frames):
    img=Image.open(ROOT/item['path']).convert('RGB').resize((480,270))
    x=(i%3)*480;y=(i//3)*290
    sheet.paste(img,(x,y+20));draw.text((x+8,y+3),f'{item["clip"]} / {item["at_seconds"]}s',fill='#173348')
sheetpath=EVID/'contact_sheet.png';sheet.save(sheetpath)
record={'checked_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'status':'technical_decode_pass_visual_review_pending',
        'selection_source':handoff_path.relative_to(ROOT).as_posix(),'selection_handoff_sha256':sha(handoff_path),
        'provisional':True,'timing_locked':False,'actual_voice_generated':False,'continuous_playback':False,'actual_listening':False,
        'clips':results,'frames':frames,'contact_sheet':sheetpath.relative_to(ROOT).as_posix(),
        'combined_preview':{'path':combined.relative_to(ROOT).as_posix(),'sha256':sha(combined),'bytes':combined.stat().st_size},
        'sample_review_scope':'3timesper8secondclip; static encoded frames, not continuous playback'}
(OUT/f'checks/preview_technical_{args.revision}.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'clips':3,'decode':'pass','encoded_frames':len(frames),'combined_preview':str(combined),'bytes':combined.stat().st_size,'visual_review':'pending'},ensure_ascii=False))
