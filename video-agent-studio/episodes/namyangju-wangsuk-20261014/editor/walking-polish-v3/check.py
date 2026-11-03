import json,subprocess,hashlib
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[5]
EP=ROOT/'video-agent-studio/episodes/namyangju-wangsuk-20261014'
OUT=EP/'outputs/rail-route-proof-v3'
VIDEO=OUT/'namyangju_rail-route-proof_v3.mp4'
BIN=Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin')
def run(cmd):return subprocess.run([str(x) for x in cmd],capture_output=True,text=True,encoding='utf-8',errors='replace')
probe=run([BIN/'ffprobe.exe','-v','error','-show_format','-show_streams','-of','json',VIDEO]);assert probe.returncode==0,probe.stderr
metadata=json.loads(probe.stdout)
decode=run([BIN/'ffmpeg.exe','-hide_banner','-v','error','-i',VIDEO,'-f','null','NUL']);assert decode.returncode==0,decode.stderr
frames=[]
for seconds in [26,31.5,31.633,32.9,33,33.133,34.7,37,38.1,39.1,39.233,41,52,68,68.133,70.5,70.633]:
    dest=OUT/f'actual_{seconds:06.3f}s.png'
    r=run([BIN/'ffmpeg.exe','-hide_banner','-loglevel','error','-ss',seconds,'-i',VIDEO,'-frames:v','1','-y',dest]);assert r.returncode==0 and dest.exists(),r.stderr
    frames.append(str(dest))
im=Image.open(OUT/'actual_37.000s.png');crop=im.crop((710,615,826,770));crop.save(OUT/'actual_walker_crop_100pct.png');crop.resize((232,310),Image.Resampling.NEAREST).save(OUT/'actual_walker_crop_200pct.png')
source=(ROOT/'video/src/NamyangjuRailRouteProofV3.tsx').read_text(encoding='utf-8')
oldsource=(ROOT/'video/src/NamyangjuRailRouteProofV2.tsx').read_text(encoding='utf-8')
def section(text,a,b):return text[text.index(a):text.index(b,text.index(a))]
assert section(source,'function Bus(','function Commute(')==section(oldsource,'function Bus(','function Commute(')
assert section(source,'const landColors','function Movie()')==section(oldsource,'const landColors','function Movie()')
report={'metadata':metadata,'bytes':VIDEO.stat().st_size,'sha256':hashlib.sha256(VIDEO.read_bytes()).hexdigest(),'whole_decode_passed':decode.returncode==0 and not decode.stderr.strip(),'decode_stderr':decode.stderr,'actual_encoded_frames':frames,'unmodified_bus_component':True,'unmodified_dasan_component':True,'data_reused_readonly':'namyangju-rail-route-proof-v2/proof_data.json','data_sha256':hashlib.sha256((ROOT/'video/public/namyangju-rail-route-proof-v2/proof_data.json').read_bytes()).hexdigest(),'audio_reused_readonly':'namyangju-rail-route-proof-v1/original_audio_94_174.wav','audio_sha256':hashlib.sha256((ROOT/'video/public/namyangju-rail-route-proof-v1/original_audio_94_174.wav').read_bytes()).hexdigest(),'walking_human_height_px':25.44,'walking_badge_diameter_px':32,'label_avoidance':'commute station label left of unchanged geographic station pin','continuous_playback':False,'audio_listened':False,'word_level_caption_alignment':False,'source_segment':{'start_s':94,'end_s':174},'publication':False,'full_master_modified':False}
(OUT/'technical_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('checked',VIDEO.stat().st_size,'bytes',metadata['format']['duration'],'seconds',len(frames),'actual frames')
