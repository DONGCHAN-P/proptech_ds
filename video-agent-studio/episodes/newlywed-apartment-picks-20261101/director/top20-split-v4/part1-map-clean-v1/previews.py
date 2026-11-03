"""User previews from the final encoded video, cut only in verified sentence gaps."""
from pathlib import Path
import math,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from jobs import D,E,FF,read,save,sha,run,probe
def main():
    t=read(D/'locked_timing.json');a=read(D/'assembly_v1.json');src=Path(a['video']);assert sha(src)==a['video_sha256']
    folder=src.parent;work=D/'media/previews-v1';work.mkdir(parents=True,exist_ok=True)
    first=t['body_scenes'][0]['sentences'][0];second=t['body_scenes'][0]['sentences'][1]
    end=math.ceil((first['end_s']+.45)*30)/30;assert end<second['start_s']-.15
    intro=folder/'intro_preview_v1.mp4'
    if intro.exists():assert abs(float(probe(intro)['format']['duration'])-end)<.04
    else:run([FF,'-v','error','-y','-i',src,'-t',f'{end:.9f}','-vf',f'fade=t=out:st={end-.25}:d=0.25','-af',f'afade=t=out:st={end-.25}:d=0.25','-c:v','libx264','-preset','fast','-crf','18','-threads','6','-c:a','aac','-b:a','256k','-movflags','+faststart',intro],D/'evidence/v1/intro_preview.log')
    windows=[(t['insert_at_s'],t['insert_duration_s'],'criteria')]
    for i,u in enumerate(t['transition_plan']['photos']):
        window_end=u['final_end_s']+.10;scene=t['body_scenes'][i]
        assert window_end<scene['sentences'][1]['start_s']-.1
        if i:assert u['final_start_s']>t['body_scenes'][i-1]['sentences'][-1]['end_s']+.05
        windows.append((u['final_start_s'],window_end-u['final_start_s'],f"R{u['rank']}"))
    clips=[]
    for i,(start,length,label)in enumerate(windows):
        dest=work/f'{i:02d}_{label}.mp4';filters=[]
        if i==len(windows)-1:filters=['-vf',f'fade=t=out:st={length-.20}:d=0.20','-af',f'afade=t=out:st={length-.20}:d=0.20']
        if dest.exists():assert abs(float(probe(dest)['format']['duration'])-length)<.05
        else:run([FF,'-v','error','-y','-ss',f'{start:.9f}','-i',src,'-t',f'{length:.9f}']+filters+['-c:v','libx264','-preset','fast','-crf','18','-threads','6','-pix_fmt','yuv420p','-bf','0','-r','30','-c:a','aac','-b:a','192k',dest],D/'evidence/v1'/f'preview_clip_{i:02d}.log')
        clips.append(dest)
    listing=work/'preview.ffconcat';listing.write_text('ffconcat version 1.0\n'+''.join("file '"+p.as_posix()+"'\n"for p in clips),encoding='utf-8')
    changes=folder/'changes_preview_v1.mp4';assert not changes.exists()
    run([FF,'-v','error','-y','-f','concat','-safe','0','-i',listing,'-c','copy','-movflags','+faststart',changes],D/'evidence/v1/preview_concat.log')
    for name,p in [('intro',intro),('changes',changes)]:run([FF,'-v','error','-xerror','-i',p,'-f','null','-'],D/'evidence/v1'/f'{name}_preview_decode.log')
    receipt={'status':'passed','source_video_sha256':a['video_sha256'],
             'intro':{'path':str(intro),'sha256':sha(intro),'duration_s':float(probe(intro)['format']['duration'])},
             'changes':{'path':str(changes),'sha256':sha(changes),'duration_s':float(probe(changes)['format']['duration'])},
             'windows':[{'source_start_s':s,'duration_s':length,'label':label}for s,length,label in windows],
             'all_final_speech_ends_preserved':True,'strict_decode_passed':True,'actual_listening':False,'continuous_playback':False}
    save(D/'previews_v1.json',receipt);print({k:v for k,v in receipt.items()if k!='windows'},flush=True)
if __name__=='__main__':main()
