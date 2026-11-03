import json,subprocess,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
EP=ROOT/'video-agent-studio/episodes/namyangju-wangsuk-20261014'
OUT=EP/'outputs/rail-route-proof-v2'
VIDEO=OUT/'namyangju_rail-route-proof_v2.mp4'
BIN=Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin')
def run(cmd):return subprocess.run([str(x) for x in cmd],capture_output=True,text=True,encoding='utf-8',errors='replace')
probe=run([BIN/'ffprobe.exe','-v','error','-show_format','-show_streams','-of','json',VIDEO]);assert probe.returncode==0,probe.stderr
metadata=json.loads(probe.stdout)
decode=run([BIN/'ffmpeg.exe','-hide_banner','-v','error','-i',VIDEO,'-f','null','NUL']);assert decode.returncode==0,decode.stderr
frames=[]
for seconds in [12,26,37,40.2,40.3,41,46,52,60,60.9,61,71.5]:
    dest=OUT/f'actual_{seconds:05.1f}s.png'
    r=run([BIN/'ffmpeg.exe','-hide_banner','-loglevel','error','-ss',seconds,'-i',VIDEO,'-frames:v','1','-y',dest]);assert r.returncode==0 and dest.exists(),r.stderr
    frames.append(str(dest))
old=json.loads((ROOT/'video/public/namyangju-rail-route-proof-v1/proof_data.json').read_text(encoding='utf-8'))
new=json.loads((ROOT/'video/public/namyangju-rail-route-proof-v2/proof_data.json').read_text(encoding='utf-8'))
new_without_context={k:v for k,v in new.items() if k!='dasanContext'}
assert old==new_without_context,'unrelated original data changed'
report={'metadata':metadata,'bytes':VIDEO.stat().st_size,'sha256':hashlib.sha256(VIDEO.read_bytes()).hexdigest(),'whole_decode_passed':decode.returncode==0 and not decode.stderr.strip(),'decode_stderr':decode.stderr,'actual_encoded_frames':frames,'unchanged_rail_commute_caption_input_data':old==new_without_context,'unchanged_audio_asset':'namyangju-rail-route-proof-v1/original_audio_94_174.wav','changed_clip_interval_s':[40.3,61],'continuous_playback':False,'audio_listened':False,'word_level_caption_alignment':False,'source_segment':{'start_s':94,'end_s':174},'source_kind':'OSM registered neighborhood placement, NOT statutory land-use plan','publication':False,'full_master_modified':False}
(OUT/'technical_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('checked',VIDEO.stat().st_size,'bytes',metadata['format']['duration'],'seconds',len(frames),'actual frames')
