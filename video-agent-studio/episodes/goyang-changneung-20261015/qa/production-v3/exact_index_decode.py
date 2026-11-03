from pathlib import Path
import argparse,json,subprocess,hashlib
Q=Path(__file__).resolve().parent;EP=Q.parents[1];ROOT=EP.parents[2]
ap=argparse.ArgumentParser();ap.add_argument('file');ap.add_argument('--tag',default='r2');args=ap.parse_args();movie=Path(args.file);F=ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe'
selected={0,612,613,762,763,764,765,11875,12378,12826,23747,23748,23749,23750,23839,23840,23841,24139};out=Q/f'exact_frames_{args.tag}';out.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before=sha(movie)
cmd=[str(F),'-v','error','-i',str(movie),'-an','-vf','scale=640:360','-fps_mode','passthrough','-c:v','mjpeg','-q:v','2','-f','image2pipe','pipe:1']
proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE);buf=b'';n=0
while chunk:=proc.stdout.read(1024*1024):
 buf+=chunk
 while True:
  start=buf.find(b'\xff\xd8');end=buf.find(b'\xff\xd9',max(start,0))
  if start<0 or end<0:break
  if n in selected:(out/f'frame_{n:06}.jpg').write_bytes(buf[start:end+2])
  n+=1;buf=buf[end+2:]
stderr=proc.stderr.read().decode(errors='replace');code=proc.wait()
report={'file':str(movie),'sha256_before':before,'sha256_after':sha(movie),'decoded_output_frames':n,'exit_code':code,'stderr':stderr,'sample_frames':sorted(selected),'method':'전 구간을 MJPEG image2pipe로 연속 디코드하고 출력 JPEG의 전역 순번을 0부터 직접 계수. 필터 내부 n 미사용. 추출 이미지 640x360. 실제 연속 재생/청취 아님.'}
(Q/f'exact_index_audit_{args.tag}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8');print(json.dumps(report,ensure_ascii=False),flush=True)
