from pathlib import Path
import json,os,subprocess,hashlib,argparse,re
D=Path(__file__).resolve().parent;E=D.parents[1];R=E.parents[2];P=E/'editor/top20-split-v4/map-proof-v1'
FF=R/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
FP=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
ENV={**os.environ,'DO_NOT_TRACK':'1','HYPERFRAMES_NO_UPDATE_CHECK':'1','HYPERFRAMES_NO_AUTO_INSTALL':'1','HYPERFRAMES_FFMPEG_PATH':str(FF),'HYPERFRAMES_FFPROBE_PATH':str(FP),'PATH':str(FF.parent)+';'+str(FP.parent)+';'+os.environ['PATH']}
def run(cmd,file):
    with file.open('wb') as out,Path(str(file)+'.stderr.log').open('wb') as err:
        result=subprocess.run([str(x) for x in cmd],cwd=R,env=ENV,stdout=out,stderr=err,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    assert result.returncode==0,file
def main():
    global P
    ap=argparse.ArgumentParser();ap.add_argument('--version',default='v2');args=ap.parse_args();assert re.fullmatch(r'v\d+',args.version)
    P=E/'editor/top20-split-v4'/('map-proof-'+args.version)
    ev=D/'evidence'/('map-proof-'+args.version);ev.mkdir(parents=True,exist_ok=True)
    points='.1,5.8,6.1,8,8.4,13.9,14,16.1,16.4,21.9,22,24.1,24.4,29.9'
    run(['npx.cmd','--no-install','hyperframes','check',P,'--at',points,'--json'],ev/'check.json')
    check=json.loads((ev/'check.json').read_text(encoding='utf-8'));assert check['ok'] and not check.get('browserSkipped')
    output=E/'outputs/top20-split-v4/map-proof'/('map_reading_proof_'+args.version+'.mp4');output.parent.mkdir(parents=True,exist_ok=True);assert not output.exists()
    print('Proof check passed; rendering silent30s',flush=True)
    run(['npx.cmd','--no-install','hyperframes','render',P,'--output',output,'--fps','30','--quality','delivery','--workers','2'],ev/'render.log')
    probe=subprocess.run([str(FP),'-v','error','-show_entries','format=duration,size:stream=codec_type,width,height,r_frame_rate','-of','json',str(output)],capture_output=True);assert probe.returncode==0
    p=json.loads(probe.stdout);assert abs(float(p['format']['duration'])-30)<.04
    run([FF,'-v','error','-xerror','-i',output,'-f','null','-'],ev/'decode.log')
    receipt={'status':'silent_map_proof_rendered','final_two_videos':False,'provisional_timing':True,'output':str(output),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'probe':p,'check_points':14,'full_decode_exit_code':0,'new_narration':False,'paid_calls':0,'actual_continuous_playback':False}
    (D/('map_proof_receipt_'+args.version+'.json')).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(receipt,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
