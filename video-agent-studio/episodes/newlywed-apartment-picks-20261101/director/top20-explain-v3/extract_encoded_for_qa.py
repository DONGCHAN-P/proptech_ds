"""Extract the independent QA plan from the exact final MP4; no source regeneration."""
from pathlib import Path
import hashlib,json,math,subprocess,time
D=Path(__file__).resolve().parent;E=D.parents[1];R=E.parents[2]
FF=R/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
V=E/'outputs/top20-explain-v3/main/top20_v6_free_v1.mp4'
Q=E/'qa/top20-explain-v3/production'
OUT=D/'evidence/encoded_qa';OUT.mkdir(parents=True,exist_ok=True)
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
    h=hashlib.sha256(V.read_bytes()).hexdigest()
    assert h=='80b7cd14b0fa15de21a696796b2a996f0fa47e29ad02ab067ab8ca20448220d1'
    plan=read(Q/'mp4_review_plan.json');samples=plan['samples']
    indexes=sorted({min(22108,max(0,round(s['time_s']*30))) for s in samples})
    mapping=[]
    for i,n in enumerate(indexes):
        mapping.append({'file':f'frame-{i:04d}.png','frame_index':n,'actual_time_s':n/30,'requests':[s for s in samples if min(22108,max(0,round(s['time_s']*30)))==n]})
    save(OUT/'extraction_started.json',{'video_sha256':h,'requested_samples':len(samples),'unique_frames':len(indexes),'mapping':mapping})
    expression='+'.join(f'eq(n,{i})' for i in indexes)
    command=[str(FF),'-v','error','-n','-i',str(V),'-vf',f"select='{expression}'",'-fps_mode','vfr','-start_number','0','-compression_level','2',str(OUT/'frame-%04d.png')]
    t=time.monotonic()
    with (OUT/'extract.stderr.log').open('wb') as log:
        result=subprocess.run(command,stdout=subprocess.DEVNULL,stderr=log)
    assert result.returncode==0
    assert len(list(OUT.glob('frame-*.png')))==len(indexes)
    save(OUT/'manifest.json',{'status':'extracted_from_final_MP4','video':str(V),'video_sha256':h,'requested_samples':len(samples),'unique_frames':len(indexes),'width':1920,'height':1080,'elapsed_s':time.monotonic()-t,'mapping':mapping,'actual_listening_performed':False,'continuous_playback_performed':False})
    print(json.dumps({'status':'extracted','samples':len(samples),'unique_frames':len(indexes),'path':str(OUT)},ensure_ascii=False),flush=True)
    result=subprocess.run([str(FF),'-v','info','-i',str(V),'-vn','-af','volumedetect','-f','null','-'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    assert result.returncode==0
    (OUT/'encoded_audio_volumedetect.log').write_bytes(result.stderr)
    print('Encoded audio signal analysis completed',flush=True)

if __name__=='__main__':main()
