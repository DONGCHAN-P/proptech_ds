from pathlib import Path
import json,subprocess,sys,hashlib,shutil,re,math
from PIL import Image,ImageDraw,ImageFont
EP=Path(__file__).resolve().parents[2];ROOT=EP.parents[2];OUT=EP/'outputs/readable-video-v2';P=OUT/'project';C=OUT/'checks'
t=json.loads((P/'timing.json').read_text('utf-8'))
r=json.loads((EP/'outputs/literature-visual-v1/reused_assets.json').read_text('utf-8'))
FF=r['ffmpeg'];PROBE=r['ffprobe'];FINAL=OUT/'regional_literature_readable_v2.mp4'
def dump(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),'utf-8')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(cmd,log):
    with log.open('w',encoding='utf-8') as stream:p=subprocess.run(cmd,stdout=stream,stderr=subprocess.STDOUT)
    if p.returncode:raise RuntimeError(log.read_text('utf-8',errors='replace')[-1600:])
def probe(path):return json.loads(subprocess.check_output([PROBE,'-v','error','-show_format','-show_streams','-of','json',str(path)],text=True,encoding='utf-8'))
def assemble():
    asset=lambda key:ROOT/next(a['actual_file'] for a in r['assets'] if a['asset_id']==key)
    for key in ['channel_brand_intro_clean_v7','channel_brand_outro_clean_v7','existing_channel_bgm']:
        assert digest(asset(key))==next(a['sha256'] for a in r['assets'] if a['asset_id']==key),key
    D=t['duration'];F=t['frames']
    patch=json.loads((C/'household-patch-render.json').read_text('utf-8'));assert patch['exit_code']==0
    st,en,pf=patch['source_start_frame'],patch['source_end_frame'],patch['patch_frames']
    pi=probe(OUT/'household_patch.mp4');assert int(next(s for s in pi['streams'] if s['codec_type']=='video')['nb_frames'])==pf
    graph=f'''[0:v]fps=30,trim=end_frame=150,setpts=PTS-STARTPTS,setsar=1,format=yuv420p[v0];
[1:v]split=2[before][after];
[before]trim=end_frame={st},setpts=PTS-STARTPTS,setsar=1,format=yuv420p[vp];
[4:v]fps=30,trim=end_frame={pf},setpts=PTS-STARTPTS,setsar=1,format=yuv420p[vm];
[after]trim=start_frame={en}:end_frame={F},setpts=PTS-STARTPTS,setsar=1,format=yuv420p[vs];
[vp][vm][vs]concat=n=3:v=1:a=0[v1];
[2:v]fps=30,trim=end_frame=300,setpts=PTS-STARTPTS,setsar=1,format=yuv420p[v2];
[0:a]atrim=end=5,asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo[a0];
[3:a]atrim=end={D},asetpts=PTS-STARTPTS,volume=0.20,afade=t=in:st=0:d=0.35,afade=t=out:st={D-.75}:d=0.75,aformat=sample_rates=48000:channel_layouts=stereo[a1];
[2:a]atrim=end=10,asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo[a2];
[v0][a0][v1][a1][v2][a2]concat=n=3:v=1:a=1[v][a]'''
    gf=C/'assembly.fffilter';gf.write_text(graph,'utf-8')
    cmd=[FF,'-hide_banner','-y','-i',str(asset('channel_brand_intro_clean_v7')),'-i',str(OUT/'body_corrected.mp4'),'-i',str(asset('channel_brand_outro_clean_v7')),'-stream_loop','-1','-i',str(asset('existing_channel_bgm')),'-i',str(OUT/'household_patch.mp4'),'-filter_complex_script',str(gf),'-map','[v]','-map','[a]','-c:v','libx264','-preset','veryfast','-crf','16','-c:a','aac','-b:a','192k','-movflags','+faststart',str(FINAL)]
    run(cmd,C/'assembly.log');info=probe(FINAL);dump(C/'ffprobe.json',info)
    print(json.dumps({'video':str(FINAL),'duration':info['format']['duration'],'bytes':FINAL.stat().st_size,'sha256':digest(FINAL)}))
def balanced_or(parts):
    if len(parts)==1:return parts[0]
    mid=len(parts)//2;return '('+balanced_or(parts[:mid])+'+'+balanced_or(parts[mid:])+')'
def extract():
    directory=C/'encoded';directory.mkdir(exist_ok=True)
    # Inspect all paragraph midpoints plus before/after major cuts and key animations.
    frames={0,149,150,t['frames']+149,t['frames']+150,t['frames']+449}
    for scene in t['scenes']:
        st=round(scene['start']*30)+150
        if st>150:frames.update([st-1,st,st+30])
        for beat in scene['beats']:
            start=round((scene['start']+beat['start'])*30)+150
            frames.add(start+round(min(beat['duration']*.5,7)*30))
    # Household reveal and price-comparison transition: sample both sides.
    for seconds in [38,45,79,83.5,86,90,195,202]:frames.add(round(seconds*30)+150)
    nums=sorted(frames)
    expr=balanced_or([f'eq(n,{n})' for n in nums])
    cmd=[FF,'-hide_banner','-y','-i',str(FINAL),'-vf',f"select='{expr}'",'-fps_mode','vfr',str(directory/'frame-%03d.png')]
    run(cmd,C/'extract.log')
    images=sorted(directory.glob('frame-*.png'));assert len(images)==len(nums),(len(images),len(nums))
    manifest=[{'file':str(p),'frame':n,'pts_seconds':n/30} for p,n in zip(images,nums)]
    dump(C/'encoded_frames.json',manifest)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19)
    for batch_start in range(0,len(images),9):
        subset=images[batch_start:batch_start+9];canvas=Image.new('RGB',(1800,math.ceil(len(subset)/3)*365),'#171717');draw=ImageDraw.Draw(canvas)
        for j,p in enumerate(subset):
            x=(j%3)*600;y=(j//3)*365
            im=Image.open(p).convert('RGB');im.thumbnail((594,334));canvas.paste(im,(x+3,y+28))
            n=nums[batch_start+j];draw.text((x+6,y+3),f'{batch_start+j+1}. frame {n} / {n/30:.3f}s',font=font,fill='white')
        canvas.save(C/f'contact-{batch_start//9+1}.jpg',quality=92)
    print(json.dumps({'encoded_frames':len(images),'contacts':math.ceil(len(images)/9)}))
def verify():
    info=probe(FINAL);v=next(s for s in info['streams'] if s['codec_type']=='video')
    assert (v['width'],v['height'],v['r_frame_rate'])==(1920,1080,'30/1')
    assert int(v['nb_frames'])==t['frames']+450
    assert abs(float(info['format']['duration'])-(t['duration']+15))<.08
    assert any(s['codec_type']=='audio' for s in info['streams'])
    run([FF,'-v','error','-i',str(FINAL),'-f','null','-'],C/'decode.log')
    assert not (C/'decode.log').read_text('utf-8').strip(),'decode errors present'
    expected=''.join(p['text'].replace(' ','') for s in json.loads((OUT/'scene_script.json').read_text('utf-8'))['scenes'] for p in s['paragraphs'])
    actual=''.join(c['text'].replace(' ','') for c in t['captions']);assert actual==expected
    groups=['Chulhee Lee 님','Elliot Kang 님','이준민 님','심승규 님','홍지훈 님','서문규 님','정재엽 님','이효중 님','유건호 님','강명구 님','김선정 님','남진 님']
    unsafely_split=[]
    for scene in t['scenes']:
        for b in scene['beats']:
            cues=[c['text'] for c in t['captions'] if c['beat_id']==b['id']]
            protected=[g for g in groups if g in b['text']]+re.findall(r'\d{4}년\s+(?:\d{1,2}월|\d분기)',b['text'])
            unsafely_split += [(b['id'],g) for g in protected if not any(g in c for c in cues)]
    assert not unsafely_split,unsafely_split
    for a,b in zip(t['captions'],t['captions'][1:]):assert a['end']<=b['start']+.0001
    assert abs(t['captions'][-1]['end']-(t['duration']-3))<.00001
    protected={
      'outputs/literature-video-v1/내레이션_초안.md':'5f40c29d4a3e0ef5255ade11eaa63cb04c8093e2c3d1d0296873126707a26d9b',
      'outputs/literature-visual-v1/previews/literature_visual_review_v1.mp4':'da4490634c89cd371065bc293659e3a974a37a366766dd2902fb6319f76635ee',
      'outputs/household-space-v1/household_space_sample_v1.mp4':'67851a459535ba6f93feba957aa28abfd0af615d20e7af7322d78aa71a38424a',
      'outputs/relocation-space-v1/relocation_space_chapter_v1.mp4':'2409106183dbead4fc7f55723523abadc1ca9a970f6560d7d863b93e0fc36c6c'}
    hashes={key:digest(EP/key)==val for key,val in protected.items()};assert all(hashes.values()),hashes
    result={'video':str(FINAL),'sha256':digest(FINAL),'duration':float(info['format']['duration']),'frames':int(v['nb_frames']),'fps':30,'resolution':[1920,1080],'decoded_all_frames':True,'caption_reconstruction_exact':True,'caption_names_and_date_groups_intact':True,'caption_count':len(t['captions']),'silent_final_body_hold_seconds':3,'original_hashes_unchanged':hashes,'narration_generated':False,'bgm_only':True,'actual_listening':False,'continuous_playback':False,'free_disk_bytes':shutil.disk_usage(ROOT).free}
    dump(C/'verification.json',result);print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':globals()[sys.argv[1]]()
