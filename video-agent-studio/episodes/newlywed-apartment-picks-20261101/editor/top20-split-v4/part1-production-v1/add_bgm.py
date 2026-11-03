"""Reuse channel music quietly, with exact brand silences and canonical carve."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess
H=Path(__file__).resolve().parent;E=H.parents[2];R=E.parents[2]
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
    a=argparse.ArgumentParser();a.add_argument('--project',type=Path,required=True);o=a.parse_args();p=o.project.resolve();p.relative_to(H)
    index=p/'index.html';text=index.read_text(encoding='utf-8');assert 'id="channel-bgm"'not in text
    t=read(E/'director/top20-split-v4/part1-production-v1/locked_timing.json');intro,outro=t['brand_inserts'];b=intro['start_s'];e=b+intro['duration_s'];end=outro['start_s']
    manifest=R/'video-agent-studio/episodes/affordable-home-price-20261026/director/production-v1/media_assets.json'
    ref=next(x for x in read(manifest)['assets']if x['asset_id']=='existing_channel_bgm');music=R/ref['path'];assert sha(music)==ref['sha256']
    ff=R/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe';bed=p/'assets/thinking_music_loop.wav'
    gain=f'if(gte(t,{end}),0,if(lt(t,{b}),min(1,max(0,({b}-t)/0.15)),if(lt(t,{e}),0,min(1,max(0,(t-{e})/0.15)))))'
    filters=['afade=t=in:st=0:d=1.0',f"volume='{gain}':eval=frame",f'afade=t=out:st={end-1.4}:d=1.4']
    cmd=[str(ff),'-v','error','-y','-stream_loop','-1','-i',str(music),'-t',str(t['total_s']),'-af',','.join(filters),'-ar','48000','-ac','2','-c:a','pcm_s16le',str(bed)]
    subprocess.run(cmd,check=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    track=f'<audio id="channel-bgm" class="clip" src="assets/thinking_music_loop.wav" data-start="0" data-duration="{t["total_s"]:.9f}" data-volume="0.045" data-track-index="7" data-track-kind="music"></audio>'
    target='</div><script>window.__timelines';assert target in text
    index.write_text(text.replace(target,track+target),encoding='utf-8')
    carve=Path('C:/Users/e2ken/.agents/skills/hyperframes-audio/scripts/carve.mjs');core=R/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/audio-deps'
    cmd=['node',str(carve),'--comp',str(index),'--core',str(core),'--bed','channel-bgm','--voice','main-narration','--strength','0.8']
    with(p/'carve.log').open('wb')as out,(p/'carve.stderr.log').open('wb')as err:
        run=subprocess.run(cmd,cwd=p,env={**os.environ,'DO_NOT_TRACK':'1','PATH':str(ff.parent)+';'+os.environ['PATH']},stdout=out,stderr=err,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    assert run.returncode==0,p/'carve.stderr.log'
    assert 'data-fx-carve='in index.read_text(encoding='utf-8')
    save(p/'music_credit.json',ref['license'])
    save(p/'mix_receipt.json',{'status':'applied_pending_render_check','music_sha256':sha(music),'bed_sha256':sha(bed),'gain':.045,'carve_strength':.8,'brand_silences':t['brand_inserts'],'actual_listening':False,'new_paid_calls':0})
    print(json.dumps({'status':'music_added_with_voice_carve','project':str(p)}))
if __name__=='__main__':main()
