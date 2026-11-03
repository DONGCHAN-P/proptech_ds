import hashlib,json,pathlib,subprocess,sys
ED=pathlib.Path(__file__).resolve().parent;REPO=ED.parents[3];OUT=ED/'render_v2'
FF=REPO/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe';PROBE=FF.with_name('ffprobe.exe')
VIDEO=OUT/'namyangju-wangsuk_v2.mp4'
def save(name,value):(OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
probe=json.loads(subprocess.check_output([str(PROBE),'-v','error','-show_streams','-show_format','-of','json',str(VIDEO)]))
digest=hashlib.sha256()
with VIDEO.open('rb')as f:
    for data in iter(lambda:f.read(1024*1024),b''):digest.update(data)
save('technical_v2.json',probe)
project=json.loads((REPO/'video/src/namyangju-v2/project.json').read_text(encoding='utf-8'))
samples=[]
for c in project['chapters']:
    second=(c['from']+c['frames']/2)/30;name=c['scene_id']+'_encoded_mid.png'
    subprocess.run([str(FF),'-y','-v','error','-ss',str(second),'-i',str(VIDEO),'-frames:v','1',str(OUT/name)],check=True)
    samples.append({'scene_id':c['scene_id'],'second':second,'file':name})
last=(project['durationInFrames']-1)/30
subprocess.run([str(FF),'-y','-v','error','-ss',str(last),'-i',str(VIDEO),'-frames:v','1',str(OUT/'encoded_last_frame.png')],check=True)
report={'sha256':digest.hexdigest(),'bytes':VIDEO.stat().st_size,'expected_frames':project['durationInFrames'],'chapter_samples':samples,'last_frame_second':last,'actual_images_exist':all((OUT/s['file']).is_file()for s in samples),'continuous_playback':False,'audio_listened':False,'independent_62shot_qa':'pending QA agent'}
save('verification_v2.json',report);print(json.dumps({'sha256':report['sha256'],'bytes':report['bytes'],'duration':probe['format']['duration'],'samples':len(samples)},ensure_ascii=False))
