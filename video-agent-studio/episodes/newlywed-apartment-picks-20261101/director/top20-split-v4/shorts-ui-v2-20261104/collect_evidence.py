"""Extract final encoded frames and signal checks; sampled review is not playback/listening."""
from pathlib import Path
import argparse,hashlib,json,subprocess,wave
import numpy as np
from PIL import Image,ImageDraw,ImageFont
D=Path(__file__).resolve().parent;E=D.parents[2];R=E.parents[2]
FF=R/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
FP=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
Q=E/'qa/top20-split-v4/shorts-ui-v2-20261104/encoded'
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--video',type=Path,required=True);ap.add_argument('--id',required=True);ap.add_argument('--lock',type=Path,required=True);a=ap.parse_args();video=a.video.resolve();video.relative_to(E/'outputs/top20-split-v4/shorts-ui-v2-20261104')
    t=read(a.lock);portrait=not a.id.startswith('main');rows=t['sentences']if portrait else t['main_sentences'];points=[]
    def add(time,purpose):
        time=max(0,min(t['total_s']-.034,float(time)));points.append({'time_s':time,'purpose':purpose})
    if portrait:
        add(0, 'first_frame')
        for scene in t['scenes']:
            s=scene['start_s'];end=scene['end_s'];
            for delta in [-.10,0,.10,.30,.60]:add(s+delta,'boundary_'+scene['kind']);
            add(s+.08,scene['kind']+'_first');add((s+end)/2,scene['kind']+'_mid');add(end-.10,scene['kind']+'_last')
            if scene['kind']=='region'and len(scene['sentences'])>1:
                add(scene['sentences'][1]['start_s']+.7,scene['region_id']+'_price');add(s+.95,scene['region_id']+'_hero')
        for c in sorted(t['captions'],key=lambda x:len(x['text']),reverse=True)[:5]:add((c['start_s']+c['end_s'])/2,'long_caption')
        last=rows[-1]['end_s'];add(last-.12,'last_utterance');add(last+.55,'last_hold');add(t['total_s']-.05,'last_frame')
    else:
        for v in [0.1,.8,2.5,t['brand_intro']['start_s']-.034,t['brand_intro']['start_s']+.034,t['brand_intro']['start_s']+2.5,t['brand_intro']['end_s']+.10]:add(v,'opening_brand')
        for scene in t['scenes']:
            add(scene['start_s']+.7,scene['scene_id']+'_start')
            for c in sorted([c for c in t['captions']if c['sentence_id']in scene['sentence_ids']],key=lambda x:len(x['text']),reverse=True)[:1]:add((c['start_s']+c['end_s'])/2,scene['scene_id']+'_long_caption')
        for u in t['photo_transitions']:
            for v,suffix in [(u['start_s']-.04,'before'),(u['start_s']+.3,'entry'),(u['start_s']+1.1,'hero'),(u['end_s']-.25,'exit'),(u['end_s']+.12,'map')]:add(v,f"R{u['rank']}_{suffix}")
        for s in rows:
            if s['sentence_id'].startswith('P01-R')and ('중위값은'in s['text']or'준공된 집단은'in s['text']or'단지 수는'in s['text']):add(s['end_s']-.15,'price_complete_'+s['sentence_id'])
        for v in [t['last_spoken_end_s']-.15,t['last_spoken_end_s']+.8,t['brand_outro']['start_s']-.04,t['brand_outro']['start_s']+.04,t['brand_outro']['start_s']+5,t['total_s']-.05]:add(v,'ending')
    folder=Q/a.id;folder.mkdir(parents=True,exist_ok=True);seen=set();frames=[]
    for p in points:
        key=round(p['time_s']*30)
        if key in seen:continue
        seen.add(key);f=folder/f"frame_{len(frames):03d}.jpg";subprocess.run([str(FF),'-v','error','-y','-ss',f"{p['time_s']:.9f}",'-i',str(video),'-frames:v','1','-q:v','2',str(f)],check=True,capture_output=True);frames.append(dict(p,file=str(f),sha256=sha(f)))
    contacts=[];font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18);cw,ch=(270,480)if portrait else(480,270);cols=4 if portrait else 3
    for k in range(0,len(frames),12):
        sheet=Image.new('RGB',(cw*cols,(ch+28)*3 if portrait else(ch+28)*4),'#e7e9ea');draw=ImageDraw.Draw(sheet)
        for i,p in enumerate(frames[k:k+12]):
            pic=Image.open(p['file']);pic.thumbnail((cw,ch));x=i%cols*cw;y=i//cols*(ch+28);sheet.paste(pic,(x,y));draw.text((x+4,y+ch+3),f"{p['time_s']:.2f}s {p['purpose'][:17]}",font=font,fill='#173348')
        dest=folder/f'contact_{k//12+1:02d}.jpg';sheet.save(dest,quality=94);contacts.append(str(dest))
    ui=[]
    if portrait:
        for i,p in enumerate([x for x in frames if x['purpose']=='long_caption'][:3]):
            im=Image.open(p['file']).convert('RGBA');overlay=Image.new('RGBA',im.size);dr=ImageDraw.Draw(overlay);dr.rectangle([0,0,1080,240],fill=(12,22,33,195));dr.rectangle([900,240,1080,1400],fill=(12,22,33,155));dr.rectangle([0,1400,1080,1920],fill=(12,22,33,210));im=Image.alpha_composite(im,overlay);dest=folder/f'UI_mock_{i:02d}.jpg';im.convert('RGB').save(dest,quality=94);ui.append(str(dest))
    p=subprocess.run([str(FP),'-v','error','-show_entries','stream=codec_type,codec_name,width,height,r_frame_rate,nb_frames,sample_rate,channels:format=duration,size','-of','json',str(video)],capture_output=True,check=True);probe=json.loads(p.stdout);v=next(x for x in probe['streams']if x['codec_type']=='video')
    assert int(v['nb_frames'])==t['total_frames']and v['r_frame_rate']=='30/1';assert abs(float(probe['format']['duration'])-t['total_s'])<.04
    assert(v['width'],v['height'])==((1080,1920)if portrait else(1920,1080))
    raw=subprocess.run([str(FF),'-v','error','-i',str(video),'-vn','-ar','48000','-ac','2','-f','s16le','-'],capture_output=True,check=True);decoded=np.frombuffer(raw.stdout,dtype='<i2').reshape(-1,2)
    with wave.open(t['master_audio'],'rb')as w:assert w.getframerate()==48000;master=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').reshape(-1,2)
    windows=[]
    selected=rows if portrait else[rows[0],rows[5],rows[6]]+[s for s in rows if s['sentence_id'].endswith('-01')]+rows[-2:]
    for s in selected:
        start=s['start_s']+.05;end=min(s['end_s'],start+.6);lo=round(start*48000);hi=round(end*48000)
        if hi-lo<4800:continue
        x=master[lo:hi].astype(float).ravel();y=decoded[lo:hi].astype(float).ravel();corr=float(np.corrcoef(x,y)[0,1]);assert corr>.97,(s['sentence_id'],corr);windows.append({'sentence_id':s['sentence_id'],'start_s':start,'correlation':corr})
    report={'status':'passed','id':a.id,'video':str(video),'video_sha256':sha(video),'lock_sha256':sha(a.lock),'probe':probe,'frames':frames,'contacts':contacts,'UI_mockups':ui,'audio_windows':windows,'minimum_audio_correlation':min(x['correlation']for x in windows),'peak_pcm':int(np.abs(decoded.astype(np.int32)).max()),'sample_count':len(frames),'actual_listening':False,'continuous_playback':False,'scope':'Final encoded sampled frames + modeled YouTube overlay + native master signal comparison; not continuous viewing or hearing'}
    save(folder/'encoded_manifest.json',report);print(json.dumps({'status':'encoded_evidence_ready','id':a.id,'frames':len(frames),'audio_windows':len(windows),'minimum_audio_correlation':report['minimum_audio_correlation'],'folder':str(folder)}),flush=True)
if __name__=='__main__':main()
