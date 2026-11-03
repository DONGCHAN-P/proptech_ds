"""Refresh established review links with the current Jun voice and complete sentences."""
from pathlib import Path
import argparse,hashlib,json,math,subprocess
D=Path(__file__).resolve().parent;E=D.parents[2];R=E.parents[2]
FF=R/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(cmd,log):
    log.parent.mkdir(parents=True,exist_ok=True)
    with log.open('wb')as f:subprocess.run(list(map(str,cmd)),stderr=f,stdout=f,check=True)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--video',type=Path,required=True);ap.add_argument('--revision',default='v1');a=ap.parse_args();assert a.revision.isalnum();src=a.video.resolve();src.relative_to(E/'outputs/top20-split-v4/jun-and-shorts-v1')
    t=read(D/'locked_timing.json');byid={x['sentence_id']:x for x in t['main_sentences']};first=byid['P01-R20-V2-01'];second=byid['P01-R20-V2-02']
    end=min(math.ceil((first['end_s']+.45)*30)/30,math.floor((second['start_s']-.12)*30)/30);assert end>first['end_s']+.15
    work=D/'media/previews'/a.revision;work.mkdir(parents=True,exist_ok=True);folder=E/'outputs/top20-split-v4/jun-and-shorts-v1/previews';folder.mkdir(parents=True,exist_ok=True)
    intro=folder/f'intro_Jun_{a.revision}.mp4';assert not intro.exists();fade=min(.20,end-first['end_s']-.04)
    run([FF,'-v','error','-y','-i',src,'-t',f'{end:.9f}','-vf',f'fade=t=out:st={end-fade}:d={fade}','-af',f'afade=t=out:st={end-fade}:d={fade}','-c:v','libx264','-preset','fast','-crf','18','-threads','4','-c:a','aac','-b:a','256k','-movflags','+faststart',intro],work/'intro.log')
    criterion=[x for x in t['main_sentences']if x['asset_id']=='INTRO-CRITERIA'];windows=[(criterion[0]['start_s']-.10,criterion[-1]['end_s']+.25,'criteria')]
    for u in t['photo_transitions']:
        nxt=next(x for x in t['main_sentences']if x['sentence_id']==f"P01-R{u['rank']}-V2-02")
        clipend=min(u['end_s']+.08,nxt['start_s']-.12);assert clipend>byid[f"P01-R{u['rank']}-V2-01"]['end_s']+.12
        windows.append((u['start_s'],clipend,f"R{u['rank']}"))
    files=[]
    for i,(start,stop,label)in enumerate(windows):
        dest=work/f'clip_{i:02d}.mp4';length=stop-start;filters=[]
        if i==len(windows)-1:filters=['-vf',f'fade=t=out:st={length-.14}:d=0.14','-af',f'afade=t=out:st={length-.14}:d=0.14']
        run([FF,'-v','error','-y','-ss',f'{start:.9f}','-i',src,'-t',f'{length:.9f}']+filters+['-c:v','libx264','-preset','fast','-crf','18','-threads','4','-pix_fmt','yuv420p','-bf','0','-r','30','-c:a','aac','-b:a','192k',dest],work/f'clip_{i:02d}.log');files.append(dest)
    listing=work/'concat.txt';listing.write_text('ffconcat version 1.0\n'+''.join("file '"+p.as_posix()+"'\n"for p in files),encoding='utf-8');changes=folder/f'changes_Jun_{a.revision}.mp4';assert not changes.exists()
    run([FF,'-v','error','-y','-f','concat','-safe','0','-i',listing,'-c','copy','-movflags','+faststart',changes],work/'join.log')
    for p in [intro,changes]:run([FF,'-v','error','-xerror','-i',p,'-f','null','-'],work/(p.stem+'_decode.log'))
    report={'status':'passed','source_video_sha256':sha(src),'intro':{'path':str(intro),'sha256':sha(intro),'duration_s':end},'changes':{'path':str(changes),'sha256':sha(changes)},'complete_sentence_guards':True,'actual_listening':False,'continuous_playback':False}
    target=D/'previews.json'
    if target.exists():
        old=read(target);archived=D/f"previews_{old['source_video_sha256'][:12]}.json"
        if not archived.exists():archived.write_bytes(target.read_bytes())
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':'Jun_previews_ready','intro_s':end,'source_sha256':report['source_video_sha256']}),flush=True)
if __name__=='__main__':main()
