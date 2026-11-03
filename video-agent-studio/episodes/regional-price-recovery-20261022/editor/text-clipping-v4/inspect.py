from pathlib import Path
import json,subprocess,hashlib
EP=Path(__file__).resolve().parents[2];ROOT=EP.parents[2];O=EP/'outputs/text-clipping-v4';C=O/'checks';C.mkdir(parents=True,exist_ok=True)
reuse=json.loads((EP/'outputs/literature-visual-v1/reused_assets.json').read_text('utf-8'));video=EP/'outputs/guide-v3/regional_guide_v3.mp4'
for sec in [43.7,44,44.3]:
    subprocess.run([reuse['ffmpeg'],'-v','error','-y','-ss',str(sec),'-i',str(video),'-frames:v','1',str(C/f'before-{sec}s.png')],check=True)
baseline={'video':str(video),'sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'user_report':'44초 차트 상단 글자 잘림, 유사 사례 공통 점검','timing':'unchanged','voice':'on_hold'}
(C/'baseline.json').write_text(json.dumps(baseline,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps(baseline,ensure_ascii=False))
