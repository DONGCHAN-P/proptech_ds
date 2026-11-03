from pathlib import Path
import hashlib,json,subprocess
Q=Path(__file__).resolve().parent
EP=Q.parents[1]
ROOT=EP.parents[2]
O=EP/'outputs/production-v5'
BIN=ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
video=O/'changneung_full_v5r2.mp4'
freeze=O/'source_freeze_v5.json'
sources=json.loads(freeze.read_text(encoding='utf-8-sig'))['source_files']
mismatch=[x['path'] for x in sources if not (ROOT/x['path']).exists() or sha(ROOT/x['path'])!=x['sha256']]
probe=subprocess.run([str(BIN/'ffprobe.exe'),'-v','error','-show_entries','stream=codec_name,codec_type,width,height,r_frame_rate,duration,nb_frames,sample_rate,channels:format=duration,size','-of','json',str(video)],capture_output=True,check=True)
a=subprocess.Popen([str(BIN/'ffmpeg.exe'),'-v','error','-i',str(video),'-vn','-c:a','copy','-f','adts','pipe:1'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
h=hashlib.sha256();count=0
while b:=a.stdout.read(1024*1024):h.update(b);count+=len(b)
stderr=a.stderr.read().decode(errors='replace');code=a.wait()
files=[{'file':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in [video,O/'changneung_full_v5.srt',O/'project_v5.json']]
r={'source_count':len(sources),'source_mismatches':mismatch,'source_freeze_sha256':sha(freeze),'aac_sha256':h.hexdigest(),'aac_bytes':count,'aac_identical':h.hexdigest()=='b6f92ce748b05efd623c265fad0c5fec1c45bc1ee053e639ac85c55784f309eb','aac_exit_code':code,'aac_stderr':stderr,'probe':json.loads(probe.stdout),'primary_files':files}
(Q/'final_input_technical_r2.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(r,ensure_ascii=True),flush=True)
