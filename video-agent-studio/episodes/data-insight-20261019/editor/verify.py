import pathlib,json,subprocess,hashlib
EP=pathlib.Path(__file__).resolve().parents[1]
ROOT=EP.parents[2]
bin=ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc'
out=EP/'outputs/v1/data_insight_30s_v1.mp4'; evidence=EP/'editor/frames';evidence.mkdir(exist_ok=True)
p=subprocess.run([str(bin/'ffprobe.exe'),'-v','error','-count_frames','-show_streams','-show_format','-of','json',str(out)],capture_output=True,text=True,check=True)
probe=json.loads(p.stdout);(EP/'editor/ffprobe.json').write_text(p.stdout,encoding='utf8')
v=next(s for s in probe['streams'] if s['codec_type']=='video');a=next(s for s in probe['streams'] if s['codec_type']=='audio')
assert (v['width'],v['height'],v['avg_frame_rate'],int(v['nb_frames']))==(1920,1080,'30/1',900)
assert int(v['nb_read_frames'])==900
assert abs(float(probe['format']['duration'])-30)<.08
with (EP/'editor/decode.log').open('wb') as log:
 subprocess.run([str(bin/'ffmpeg.exe'),'-v','error','-i',str(out),'-map','0:v:0','-map','0:a:0','-c:v','rawvideo','-c:a','pcm_s16le','-f','null','-'],stdout=log,stderr=subprocess.STDOUT,check=True)
frames=[0,60,119,120,165,209,210,255,299,300,345,389,390,435,479,480,525,569,570,630,689,690,750,809,810,855,899]
for f in frames:
 subprocess.run([str(bin/'ffmpeg.exe'),'-v','error','-y','-ss',str(f/30),'-i',str(out),'-frames:v','1',str(evidence/f'f{f:03}.jpg')],check=True)
result={'status':'technical_pass','duration':probe['format']['duration'],'resolution':[1920,1080],'fps':30,'frames':900,'audio_codec':a['codec_name'],'decode_errors':(EP/'editor/decode.log').stat().st_size,'sampled_frames':frames,'continuous_playback':False,'actual_listening':False,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}
(EP/'editor/technical_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(result,ensure_ascii=False))
