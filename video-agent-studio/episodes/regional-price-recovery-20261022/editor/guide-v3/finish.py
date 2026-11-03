from pathlib import Path
import json,subprocess,hashlib,sys,re,math
from PIL import Image,ImageDraw,ImageFont
EP=Path(__file__).resolve().parents[2];ROOT=EP.parents[2];O=EP/'outputs/guide-v3';P=O/'project';C=O/'checks';FINAL=O/'regional_guide_v3.mp4'
t=json.loads((P/'timing.json').read_text('utf-8'));reuse=json.loads((EP/'outputs/literature-visual-v1/reused_assets.json').read_text('utf-8'));FF=reuse['ffmpeg'];PROBE=reuse['ffprobe']
def dump(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2),'utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(cmd,log):
    with log.open('w',encoding='utf-8') as stream:r=subprocess.run(cmd,stdout=stream,stderr=subprocess.STDOUT)
    if r.returncode:raise RuntimeError(log.read_text('utf-8',errors='replace')[-1500:])
def probe(p):return json.loads(subprocess.check_output([PROBE,'-v','error','-show_format','-show_streams','-of','json',str(p)],text=True,encoding='utf-8'))
def assemble():
    asset=lambda key:ROOT/next(a['actual_file'] for a in reuse['assets'] if a['asset_id']==key)
    for key in ['channel_brand_intro_clean_v7','channel_brand_outro_clean_v7','existing_channel_bgm']:assert sha(asset(key))==next(a['sha256'] for a in reuse['assets'] if a['asset_id']==key)
    D=t['duration'];F=t['frames']
    graph=f'''[0:v]fps=30,trim=end_frame=150,setpts=PTS-STARTPTS,setsar=1,format=yuv420p[v0];
[1:v]fps=30,trim=end_frame={F},setpts=PTS-STARTPTS,setsar=1,format=yuv420p[v1];
[2:v]fps=30,trim=end_frame=300,setpts=PTS-STARTPTS,setsar=1,format=yuv420p[v2];
[0:a]atrim=end=5,asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo[a0];
[3:a]atrim=end={D},asetpts=PTS-STARTPTS,volume=0.20,afade=t=in:st=0:d=0.35,afade=t=out:st={D-.75}:d=0.75,aformat=sample_rates=48000:channel_layouts=stereo[a1];
[2:a]atrim=end=10,asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo[a2];
[v0][a0][v1][a1][v2][a2]concat=n=3:v=1:a=1[v][a]'''
    gf=C/'assembly.fffilter';gf.write_text(graph,'utf-8')
    run([FF,'-hide_banner','-y','-i',str(asset('channel_brand_intro_clean_v7')),'-i',str(O/'body.mp4'),'-i',str(asset('channel_brand_outro_clean_v7')),'-stream_loop','-1','-i',str(asset('existing_channel_bgm')),'-filter_complex_script',str(gf),'-map','[v]','-map','[a]','-c:v','libx264','-preset','veryfast','-crf','16','-c:a','aac','-b:a','192k','-movflags','+faststart',str(FINAL)],C/'assembly.log')
    info=probe(FINAL);dump(C/'ffprobe.json',info);print(json.dumps({'video':str(FINAL),'duration':info['format']['duration'],'sha256':sha(FINAL)}))
def balanced(parts):
    if len(parts)==1:return parts[0]
    m=len(parts)//2;return '('+balanced(parts[:m])+'+'+balanced(parts[m:])+')'
def extract():
    dest=C/'encoded';dest.mkdir(exist_ok=True);frames={0,149,150,t['frames']+149,t['frames']+150,t['frames']+449}
    times=json.loads((C/'snapshot_receipt.json').read_text('utf-8'))['proof_times']
    for x in times:frames.add(round((x+5)*30))
    for s in t['scenes']:
        for cut in [s['start'],s['start']+3.5]:
            k=round((cut+5)*30);frames.update([max(0,k-1),k,k+1])
    for u in t['units']:
        if u['mode']=='population' and ('독립' in u['spoken_text'] or '세 사람이' in u['spoken_text']):
            frames.update([round((u['start']+5)*30),round((u['start']+6.2)*30),round((u['end']+5)*30)-1])
        if u['mode']=='arithmetic' and any(w in u['spoken_text'] for w in ['팔백','이백','천 채']):frames.add(round(((u['start']+u['end'])/2+5)*30))
        if any(w in u['spoken_text'] for w in ['사업체 수','도구변수','이 추정에서는','천 채에서','팔백 채를','이백 채']):
            frames.add(round(((u['start']+u['end'])/2+5)*30))
    last=round((t['captions'][-1]['end']+5)*30);frames.update([last-1,last,last+45])
    nums=sorted(frames);expr=balanced([f'eq(n,{n})' for n in nums])
    run([FF,'-hide_banner','-y','-i',str(FINAL),'-vf',f"select='{expr}'",'-fps_mode','vfr',str(dest/'frame-%03d.png')],C/'extract.log')
    files=sorted(dest.glob('frame-*.png'));assert len(files)==len(nums),(len(files),len(nums))
    manifest=[{'file':str(p),'frame':n,'pts_seconds':n/30} for p,n in zip(files,nums)];dump(C/'encoded_frames.json',manifest)
    qa_targets=[]
    for label,predicate in [
        ('R5_사업체수_두결과대조',lambda u:'사업체 수' in u['spoken_text']),
        ('R3_IV결과',lambda u:u['mode']=='identification' and '이 추정에서는' in u['spoken_text']),
        ('가상_순증계산',lambda u:u['mode']=='arithmetic' and '이백' in u['spoken_text']),
        ('작은_임차공간',lambda u:u['scene_id']=='L003' and '독립' in u['spoken_text']),
        ('실제_59A평면',lambda u:'FP59' in u['asset_ids']),
    ]:
        unit=next((u for u in t['units'] if predicate(u)),None)
        if unit:
            target=(unit['start']+unit['end'])/2+5;shot=min(manifest,key=lambda f:abs(f['pts_seconds']-target))
            qa_targets.append({'label':label,'unit':unit['id'],'spoken_text':unit['spoken_text'],'target_time':target,**shot})
    dump(C/'encoded_qa_packet.json',{'video':str(FINAL),'sha256':sha(FINAL),'targets':qa_targets,'review_scope':'Only these representative actual encoded frames; no continuous playback or actual listening.'})
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
    for batch in range(0,len(files),9):
        part=files[batch:batch+9];im=Image.new('RGB',(1800,math.ceil(len(part)/3)*365),'#171717');draw=ImageDraw.Draw(im)
        for j,p in enumerate(part):
            x=j%3*600;y=j//3*365;shot=Image.open(p).convert('RGB');shot.thumbnail((594,334));im.paste(shot,(x+3,y+28));n=nums[batch+j];draw.text((x+5,y+4),f'{batch+j+1}. frame {n} / {n/30:.3f}s',font=font,fill='white')
        im.save(C/f'contact-{batch//9+1}.jpg',quality=92)
    print(json.dumps({'frames':len(files),'contacts':math.ceil(len(files)/9)}))
def verify():
    info=probe(FINAL);v=next(s for s in info['streams'] if s['codec_type']=='video')
    assert (v['width'],v['height'],v['r_frame_rate'])==(1920,1080,'30/1')
    assert int(v['nb_frames'])==t['frames']+450
    assert abs(float(info['format']['duration'])-t['duration']-15)<.08
    run([FF,'-v','error','-i',str(FINAL),'-f','null','-'],C/'decode.log');assert not (C/'decode.log').read_text('utf-8').strip()
    norm=lambda x:re.sub(r'\s+','',x)
    sem=json.loads((O/'semantic_units.json').read_text('utf-8'));units=[u for s in sem['scenes'] for p in s['paragraphs'] for u in p['units']]
    for s in sem['scenes']:
        for p in s['paragraphs']:assert norm(''.join(u['spoken_text'] for u in p['units']))==norm(p['text'])
    assert len(t['captions'])==len(units)==162
    for c,u in zip(t['captions'],units):assert c['spoken_text']==u['spoken_text'] and c['display_text']==u['display_text']
    for a,b in zip(t['captions'],t['captions'][1:]):assert a['end']<=b['start']+.00001
    assert abs(t['duration']-t['captions'][-1]['end']-3)<.00001
    assets=json.loads((O/'assets.json').read_text('utf-8'));assert len(assets['generated'])==9
    assert len(set(c['sha256'] for c in assets['chapters']))==8
    for a in assets['generated']:assert sha(Path(a['local_file']))==a['sha256']
    across={}
    for r in t['asset_usage']:
        if r['kind']=='body_photo':across.setdefault(r['asset_id'],set()).add(r['scene_id'])
    assert len(across)==5 and all(len(s)==1 for s in across.values())
    for aid in across:
        duration=sum(r['end']-r['start'] for r in t['asset_usage'] if r['kind']=='body_photo' and r['asset_id']==aid);assert duration<=12.00001
    for aid,sid in [('accepted_household_cutaway','L002'),('FP59','L003')]:assert {u['scene_id'] for u in t['units'] if aid in u['asset_ids']}=={sid}
    old={'outputs/readable-video-v2/regional_literature_readable_v2.mp4':'c1e234726f72c85c456e43632fbef5bf8f8220cdada2c30d136c517cc57ead26','outputs/readable-video-v2/대본.md':'b2536411ffc5b348d41c1c3d1f5572d0df5707dbc79479f403eed4f89de12c61','outputs/literature-video-v1/내레이션_초안.md':'5f40c29d4a3e0ef5255ade11eaa63cb04c8093e2c3d1d0296873126707a26d9b'}
    assert all(sha(EP/p)==h for p,h in old.items())
    frozen=json.loads((EP/'director/guide-v3/render_input_manifest.json').read_text('utf-8'))
    assert all(sha(ROOT/p)==h for p,h in frozen.items()),'Render input modified during production'
    result={'video':str(FINAL),'sha256':sha(FINAL),'duration':float(info['format']['duration']),'frames':int(v['nb_frames']),'fps':30,'resolution':[1920,1080],'full_decode':True,'semantic_units':162,'paragraph_reconstruction':30,'display_text_matches_authored_mapping':True,'image_chapters':8,'chapter_unique_hashes':8,'new_generated_images':9,'body_photo_cross_chapter_reuse':False,'body_photo_max_seconds':12,'accepted_household_L002_only':True,'real_floorplan_L003_only':True,'originals_preserved':True,'narration_generated':False,'actual_listening':False,'continuous_playback':False,'timing_provisional':True}
    dump(C/'verification.json',result);print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':globals()[sys.argv[1]]()
