"""Small actual f32le pipe decode smoke; no generation, mix, encode, or upload."""
import array
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;EP=HERE.parents[1];ROOT=EP.parents[2]
OUT=EP/'outputs/private-production-v1'; FOLDER=HERE/'audio-smoke'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))


def main():
    FOLDER.mkdir(exist_ok=True)
    media=read(EP/'director/two-episode-production-v1/media_assets.json')
    ffmpeg=ROOT/media['ffmpeg'];probe=ROOT/media['ffprobe']
    result={'status':'pending','scope':'0.25s local codec smoke only; no TTS, voice listening, full render or actual mix','sample_rate':48000,'channels':1,'format':'f32le','media_lock_sha256':sha(EP/'director/two-episode-production-v1/media_assets.json'),'checks':[],'external_calls':0}
    for asset in media['assets']:
        p=ROOT/asset['path']
        if sha(p)!=asset['sha256']:raise ValueError('SHA mismatch: '+asset['asset_id'])
        command=[str(probe),'-v','error','-show_entries','format=duration:stream=index,codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels','-of','json',str(p)]
        proc=subprocess.run(command,capture_output=True,check=True)
        info=json.loads(proc.stdout)
        result['checks'].append({'asset_id':asset['asset_id'],'sha256':sha(p),'ffprobe':info})
    samples=[ROOT/next(a['path'] for a in media['assets'] if a['asset_id']=='existing_channel_bgm')]
    sample_voice=EP/'narration/free-tts-v1/samples/injoon-20261026-v1/sample.wav'
    if sample_voice.exists():samples.append(sample_voice)
    for i,p in enumerate(samples):
        command=[str(ffmpeg),'-v','error','-i',str(p),'-vn','-t','0.25','-ac','1','-ar','48000','-f','f32le','pipe:1']
        run=subprocess.run(command,capture_output=True)
        if run.returncode:
            result['checks'].append({'source':str(p.relative_to(ROOT)).replace('\\','/'),'argv':command,'returncode':run.returncode,'stderr':run.stderr.decode('utf8',errors='replace'),'pipe_decode_pass':False})
            result['status']='blocked_missing_f32le_muxer'
            break
        floats=array.array('f');floats.frombytes(run.stdout)
        if len(run.stdout)!=48000 or not all(math.isfinite(v) for v in floats):raise ValueError('Invalid f32le 0.25s pipe output')
        if not any(v!=0 for v in floats):raise ValueError('Unexpected all-zero source window')
        target=FOLDER/f'fixture{i:02d}_0.25s_48k_mono.f32le';target.write_bytes(run.stdout)
        result['checks'].append({'source':str(p.relative_to(ROOT)).replace('\\','/'),'input_sha256':sha(p),'argv':command,'returncode':run.returncode,'stderr':run.stderr.decode('utf8',errors='replace'),'bytes':len(run.stdout),'samples':len(floats),'finite':True,'rms':math.sqrt(sum(v*v for v in floats)/len(floats)),'peak':max(abs(v) for v in floats),'output':str(target.relative_to(EP)).replace('\\','/'),'output_sha256':sha(target)})
    package=OUT/'audio-deps/node_modules/@hyperframes/core/package.json'
    result['core_installed']=package.exists()
    if package.exists():
        metadata=read(package)
        result['core_version']=metadata['version'];result['core_package_sha256']=sha(package)
        if metadata['version']!='0.8.181':raise ValueError('Installed core version differs from 0.8.181')
    result['ffmpeg_sha256']=sha(ffmpeg);result['ffprobe_sha256']=sha(probe)
    result['carve_runtime_tested']=False
    if result['status']=='pending':result['status']='decode_smoke_pass_core_ready' if package.exists() else 'decode_smoke_pass_core_pending'
    (FOLDER/'receipt.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'status':result['status'],'checks':len(result['checks']),'core_version':result.get('core_version'),'carve_executed':False}));return int(result['status'].startswith('blocked'))


if __name__=='__main__':sys.exit(main())
