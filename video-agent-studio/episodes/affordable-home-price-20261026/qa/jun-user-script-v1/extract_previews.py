"""실제 MP4 표본과 축소 증거. 연속 재생·청취를 수행하지 않는다."""
from pathlib import Path
from PIL import Image, ImageDraw
import subprocess
import hashlib
import json
from datetime import datetime, timezone

OWN = Path(__file__).resolve().parent
EP = OWN.parents[1]
ROOT = EP.parents[2]
FF = ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
FP = ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
samples = {'S13':[0,1.6,2.9,4.6,6.7,9.5,299/30],
           'S18_S19':[0,2.2,3.3,4.7,179/30,6,181/30,6.7,8.7,10.7,12.5,389/30],
           'S21':[0,1.7,4.2,6.2,8.2,11.5,359/30]}
receipt = {'checked_at_utc':datetime.now(timezone.utc).isoformat(),
           'method':'실제 MP4의 ffprobe·전체 디코드와 독립 추출 정지 프레임. 사람이 확인한 이미지 범위는 findings.json에 기록.',
           'continuous_playback':False,'actual_listening':False,'previews':[]}
for ident,times in samples.items():
    video = EP/f'outputs/jun-user-script-v1/representatives/{ident}_preview_silent_v1.mp4'
    if not video.exists(): continue
    digest = sha(video)
    out = OWN/'frames'/f'{ident}-{digest[:12]}'
    out.mkdir(parents=True,exist_ok=True)
    probe = subprocess.run([str(FP),'-v','error','-show_streams','-show_format','-of','json',str(video)],capture_output=True,text=True,encoding='utf-8')
    assert probe.returncode == 0,probe.stderr
    data = json.loads(probe.stdout)
    decoded = subprocess.run([str(FF),'-v','error','-i',str(video),'-f','null','-'],capture_output=True,text=True,encoding='utf-8')
    assert decoded.returncode == 0,decoded.stderr
    frame_paths = []
    for t in times:
        dest = out/f'f{round(t*30):04}_{t:.3f}s.png'
        result = subprocess.run([str(FF),'-v','error','-y','-ss',str(t),'-i',str(video),'-frames:v','1',str(dest)],capture_output=True,text=True,encoding='utf-8')
        assert result.returncode == 0 and dest.exists(),result.stderr
        with Image.open(dest) as im: assert im.size == (1920,1080)
        frame_paths.append({'time_s':t,'frame_index':round(t*30),'path':dest.relative_to(ROOT).as_posix(),'sha256':sha(dest)})
    sheet = Image.new('RGB',(1280,384*((len(times)+1)//2)),'#e4e4e4')
    draw = ImageDraw.Draw(sheet)
    for i,frame in enumerate(frame_paths):
        with Image.open(ROOT/frame['path']) as im: thumb = im.convert('RGB').resize((640,360),Image.Resampling.LANCZOS)
        x,y = (i%2)*640,(i//2)*384
        sheet.paste(thumb,(x,y+24));draw.text((x+6,y+5),f'{ident} t={frame["time_s"]:.3f}s',fill='black')
    sheet_path = out/'small_640x360_sheet.jpg';sheet.save(sheet_path,quality=94)
    stable = sha(video) == digest
    receipt['previews'].append({'id':ident,'path':video.relative_to(ROOT).as_posix(),'sha256':digest,'bytes':video.stat().st_size,'stable_during_extraction':stable,'probe':data,'full_decode_returncode':decoded.returncode,'frames':frame_paths,'small_sheet':sheet_path.relative_to(ROOT).as_posix(),'small_frame_size':[640,360]})
    assert stable,'Renderer replaced MP4 while QA was extracting'
(OWN/'preview_evidence.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'previews':len(receipt['previews']),'extracted_frames':sum(len(x['frames']) for x in receipt['previews']),'audio_streams':[sum(s['codec_type']=='audio' for s in x['probe']['streams']) for x in receipt['previews']]},ensure_ascii=False))
