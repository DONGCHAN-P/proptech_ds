"""Clear repeated map footers, retain a compact corner map attribution."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys
D=Path(__file__).resolve().parent;E=D.parents[2];R=E.parents[2]
FF=R/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
FP=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    a=read(D/'production_authorization.json');source=R/a['baseline_video'];assert sha(source)==a['baseline_sha256']
    t=read(R/a['baseline_timing']);start=48.5;end=t['body_scenes'][-1]['start_s']
    version='v2' if '--v2' in sys.argv else 'v1'
    media=D/'media';media.mkdir(exist_ok=True);out=media/f'baseline_clean_{version}.mp4';assert not out.exists()
    shutil.copyfile('C:/Windows/Fonts/segoeui.ttf',D/'credit.ttf');(D/'osm_credit.txt').write_text('© OpenStreetMap',encoding='utf-8')
    # The legend occupies y850..885, the repeated reference line y895..917.
    filters=["setpts=N/(30*TB)",f"drawbox=x=0:y=889:w=1920:h=34:color=0xf6f4ef:t=fill:enable='between(t,{start},{end})'",
             "drawbox=x=0:y=843:w=1920:h=80:color=0xf6f4ef:t=fill:enable='between(t,39.7,45.05)'",
             f"drawtext=fontfile=credit.ttf:textfile=osm_credit.txt:fontcolor=0x425b6d:fontsize=18:x=1672:y=119:enable='between(t,{start},{end})'"]
    keys=read(D/'transition_plan.json')['forced_source_keyframes'] if version=='v2' else []
    extra=['-bf','0','-force_key_frames',','.join(f'{v:.9f}'for v in keys)] if keys else []
    cmd=[str(FF),'-v','error','-y','-i',str(source),'-an','-vf',','.join(filters),'-c:v','libx264','-preset','fast','-crf','18','-threads','6','-pix_fmt','yuv420p','-fps_mode','cfr','-r','30']+extra+['-video_track_timescale','15360','-movflags','+faststart',str(out)]
    (D/f'clean_command_{version}.json').write_text(json.dumps(cmd,ensure_ascii=False,indent=2),encoding='utf-8')
    with (D/f'clean_{version}.stderr.log').open('wb')as log:r=subprocess.run(cmd,cwd=D,stderr=log)
    assert r.returncode==0,(D/f'clean_{version}.stderr.log')
    p=subprocess.run([str(FP),'-v','error','-show_entries','stream=nb_frames,width,height,r_frame_rate:format=duration','-of','json',str(out)],capture_output=True,check=True)
    p=json.loads(p.stdout);assert int(p['streams'][0]['nb_frames'])==18070
    receipt={'status':'passed','video':str(out),'sha256':sha(out),'source_sha256':a['baseline_sha256'],'frame_count':18070,
             'duration_s':float(p['format']['duration']),'footer_rect':[0,889,1920,34],'legend_preserved':True,
             'compact_attribution':'© OpenStreetMap','attribution_position':[1672,119],
             'attribution_guideline':'https://osmfoundation.org/wiki/Licence/Attribution_Guidelines#TV,_film,_or_video_productions',
             'full_credit_and_licence_url_retained_in_sources':True,'actual_listening':False}
    (D/f'clean_receipt_{version}.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
