import json,subprocess,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
EP=ROOT/'video-agent-studio/episodes/namyangju-wangsuk-20261014'
OUT=EP/'outputs/rail-route-proof-v1'
REVISION_B='--revision-b' in sys.argv
VIDEO=OUT/('namyangju_rail-route-proof_v1b.mp4' if REVISION_B else 'namyangju_rail-route-proof_v1.mp4')
BIN=Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin')
def run(cmd):return subprocess.run([str(x) for x in cmd],capture_output=True,text=True,encoding='utf-8',errors='replace')
probe=run([BIN/'ffprobe.exe','-v','error','-show_format','-show_streams','-of','json',VIDEO])
assert probe.returncode==0,probe.stderr
metadata=json.loads(probe.stdout)
decode=run([BIN/'ffmpeg.exe','-hide_banner','-v','error','-i',VIDEO,'-f','null','NUL'])
assert decode.returncode==0,decode.stderr
frames=[]
for seconds in [1,4,4.7,8,8.7,12,18,19,19.7,26,31.5,32.9,34.7,35.4,37,49,64,67,71.5,78]:
    dest=OUT/f'actual_{"b_" if REVISION_B else ""}{seconds:05.1f}s.png'
    r=run([BIN/'ffmpeg.exe','-hide_banner','-loglevel','error','-ss',seconds,'-i',VIDEO,'-frames:v','1','-y',dest])
    assert r.returncode==0 and dest.exists(),r.stderr
    frames.append(str(dest))
report={'metadata':metadata,'bytes':VIDEO.stat().st_size,'sha256':hashlib.sha256(VIDEO.read_bytes()).hexdigest(),'whole_decode_passed':decode.returncode==0 and not decode.stderr.strip(),'decode_stderr':decode.stderr,'actual_encoded_frames':frames,'continuous_playback':False,'audio_listened':False,'word_level_caption_alignment':False,'source_segment':{'start_s':94,'end_s':174},'motion_speed_basis':'explanatory animation, NOT actual travel time','publication':False,'full_master_modified':False}
(OUT/('technical_check_v1b.json' if REVISION_B else 'technical_check.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('checked',VIDEO.stat().st_size,'bytes',metadata['format']['duration'],'seconds',len(frames),'actual frames')
